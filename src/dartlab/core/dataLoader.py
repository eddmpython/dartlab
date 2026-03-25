"""데이터 로딩 및 공통 유틸."""

import inspect
import json
import re
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen, urlretrieve

import polars as pl

from dartlab.core.dataConfig import (
    DATA_RELEASES,
    HF_REPO,
    hfBaseUrl,
)


def _getDataRoot() -> Path:
    from dartlab import config

    return Path(config.dataDir)


_DOWNLOAD_TIMEOUT = 30
_MAX_RETRIES = 3
_EDGAR_UNIVERSE_TTL_HOURS = 24
_EDGAR_DOCS_FRESHNESS_TTL_HOURS = 24
_SEC_HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}
_LISTED_EXCHANGES = {"Nasdaq", "NYSE", "CBOE"}

PERIOD_KINDS = {
    "y": ["annual"],
    "q": ["Q1", "semi", "Q3", "annual"],
    "h": ["semi", "annual"],
}

_EXPLICIT_DOWNLOAD_ONLY_CATEGORIES = {"edgarDocs"}


@contextmanager
def _socketTimeout(seconds: int = _DOWNLOAD_TIMEOUT):
    """소켓 글로벌 타임아웃을 임시 설정하고 복원."""
    oldTimeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(seconds)
        yield
    finally:
        socket.setdefaulttimeout(oldTimeout)


def _dataDir(category: str = "docs") -> Path:
    return _getDataRoot() / DATA_RELEASES[category]["dir"]


def _downloadWithRetry(url: str, dest: Path) -> None:
    """URL → dest 다운로드. 최대 3회 재시도 (2초, 4초 대기)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    lastErr = None
    for attempt in range(_MAX_RETRIES):
        try:
            with _socketTimeout():
                urlretrieve(url, dest)
            return
        except (URLError, socket.timeout, OSError) as e:
            lastErr = e
            if dest.exists():
                dest.unlink()
            if attempt < _MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
    raise lastErr


def _checkRemoteFreshness(stockCode: str, localPath: Path, category: str = "docs") -> bool | None:
    """로컬 파일이 원격보다 오래됐는지 HTTP HEAD ETag로 확인.

    HF는 Last-Modified 대신 ETag(content hash)를 제공한다.
    로컬 .etag 사이드카 파일에 마지막 다운로드 시 ETag를 저장해두고 비교.

    Returns: True=stale, False=fresh, None=판단불가(네트워크 오류 등).
    """
    hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    etagPath = localPath.with_suffix(".parquet.etag")
    try:
        remoteEtag = _fetchRemoteEtag(hfUrl)
        if not remoteEtag:
            return None
        if etagPath.exists():
            localEtag = etagPath.read_text(encoding="utf-8").strip()
            return remoteEtag != localEtag
        # etag 파일 없음 → 최초이므로 현재 ETag 저장 + fresh 취급
        etagPath.write_text(remoteEtag, encoding="utf-8")
        return False
    except (URLError, socket.timeout, OSError, ValueError):
        return None


def _saveEtag(stockCode: str, dest: Path, category: str = "docs") -> None:
    """다운로드 성공 후 HF ETag를 사이드카 파일에 저장."""
    hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    etagPath = dest.with_suffix(".parquet.etag")
    try:
        etag = _fetchRemoteEtag(hfUrl)
        if etag:
            etagPath.write_text(etag, encoding="utf-8")
    except (URLError, socket.timeout, OSError):
        pass


def _fetchRemoteEtag(url: str) -> str:
    """HTTP HEAD로 원격 ETag 조회. 없으면 빈 문자열."""
    req = Request(url, method="HEAD")
    with _socketTimeout(10):
        resp = urlopen(req)
    return resp.headers.get("ETag", "").strip('" ')


def _download(stockCode: str, dest: Path, category: str = "docs") -> None:
    """HuggingFace 데이터셋에서 단건 다운로드."""
    hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    _downloadWithRetry(hfUrl, dest)
    _saveEtag(stockCode, dest, category)


def loadData(
    stockCode: str,
    category: str = "docs",
    *,
    sinceYear: int | None = None,
    asOf: str | None = None,
    refresh: str = "auto",
    columns: list[str] | None = None,
) -> pl.DataFrame:
    """종목코드 → DataFrame. 로컬에 없으면 릴리즈에서 자동 다운로드."""
    from dartlab.core.memory import check_memory_and_gc

    check_memory_and_gc(f"loadData({stockCode},{category})")
    dataDir = _dataDir(category)
    path = dataDir / f"{stockCode}.parquet"
    effectiveSinceYear = sinceYear
    if category == "edgarDocs" and effectiveSinceYear is None:
        effectiveSinceYear = 2009
    if category == "edgarDocs":
        _ensureEdgarDocs(
            stockCode,
            path,
            sinceYear=effectiveSinceYear or 2009,
            asOf=asOf,
            refresh=refresh,
        )
    elif not path.exists():
        from dartlab.core.guidance import emit
        from dartlab.core.guidance import format as gfmt

        label = DATA_RELEASES[category]["label"]
        emit("download:start", stockCode=stockCode, label=label)
        try:
            _download(stockCode, path, category)
            size = path.stat().st_size
            sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
            emit("download:done_short", sizeStr=sizeStr)
        except (URLError, socket.timeout, OSError) as e:
            if path.exists():
                path.unlink()
            key = "error:download_failed"
            raise RuntimeError(gfmt(key, stockCode=stockCode, label=label, error=str(e))) from e
        except ValueError:
            if path.exists():
                path.unlink()
            raise
    # lazy scan: sinceYear 필터 또는 컬럼 프로젝션이 있으면 scan_parquet 사용
    yearColCandidates = ("year", "bsns_year")
    useLazy = sinceYear is not None or columns is not None
    if useLazy:
        lf = pl.scan_parquet(str(path))
        schemaNames = lf.collect_schema().names()
        # sinceYear 필터 (year 또는 bsns_year 컬럼)
        if sinceYear is not None:
            for colName in yearColCandidates:
                if colName in schemaNames:
                    yearCol = pl.col(colName)
                    if str(lf.collect_schema()[colName]) == "String":
                        yearCol = yearCol.cast(pl.Int32, strict=False)
                    lf = lf.filter(yearCol >= sinceYear)
                    break
        # 컬럼 프로젝션
        if columns:
            available = [c for c in columns if c in schemaNames]
            if available:
                lf = lf.select(available)
        df = lf.collect()
    else:
        df = pl.read_parquet(str(path))
    return _normalizeLoadedFrame(df, category)


def _ensureEdgarDocs(
    stockCode: str,
    path: Path,
    *,
    sinceYear: int,
    asOf: str | None,
    refresh: str,
) -> None:
    if refresh not in {"auto", "force_check", "force_rebuild", "local_only"}:
        raise ValueError(f"지원하지 않는 refresh 정책: {refresh}")

    if refresh == "local_only":
        if not path.exists():
            raise FileNotFoundError(f"로컬 EDGAR docs 없음: {path}")
        return

    if refresh == "force_rebuild":
        _rebuildEdgarDocs(stockCode, path, sinceYear=sinceYear, sourceMode="sec_api_rebuild")
        return

    if not path.exists():
        from dartlab.core.guidance import emit

        label = DATA_RELEASES["edgarDocs"]["label"]
        emit("download:start", stockCode=stockCode, label=label)
        try:
            _download(stockCode, path, "edgarDocs")
            size = path.stat().st_size
            sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
            emit("download:done_short", sizeStr=sizeStr)
        except (URLError, socket.timeout, OSError):
            if path.exists():
                path.unlink()
            emit("edgar:fallback")
            _rebuildEdgarDocs(stockCode, path, sinceYear=sinceYear, sourceMode="sec_api")
        return

    if refresh == "auto" and not _isEdgarDocsCheckExpired(path):
        return

    latestRemote = _getLatestRegularEdgarFiling(stockCode, sinceYear=sinceYear)
    if latestRemote is None:
        return
    localState = _getLocalEdgarDocsState(path)
    if localState is not None and _isEdgarDocsFresh(localState, latestRemote, asOf=asOf):
        return
    _incrementalUpdateEdgarDocs(stockCode, path, sinceYear=sinceYear, latestRemote=latestRemote)


_HF_MAX_RETRIES = 3


def downloadAll(category: str = "docs", *, forceUpdate: bool = False) -> None:
    """HuggingFace 데이터셋에서 카테고리 전체 parquet을 다운로드.

    huggingface_hub의 snapshot_download를 사용하여 resume/병렬 다운로드를 지원한다.
    중간에 끊겨도 이어받기가 가능하며, 이미 받은 파일은 자동 skip.

    Args:
        category: "docs", "finance", "report" 등.
        forceUpdate: True면 로컬 캐시 무시하고 원격 최신 파일로 갱신.

    Examples::

        import dartlab
        dartlab.downloadAll("finance")              # 재무 전체 (~600MB)
        dartlab.downloadAll("docs")                 # 공시 전체 (~8GB)
        dartlab.downloadAll("finance", forceUpdate=True)  # 강제 갱신
    """
    if category in _EXPLICIT_DOWNLOAD_ONLY_CATEGORIES:
        raise ValueError(
            f"{category}는 전체 다운로드를 지원하지 않음. 개별 종목 loadData(..., category='{category}')를 사용하세요."
        )

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise ImportError(
            "downloadAll()은 huggingface_hub가 필요합니다.\n"
            "  pip install dartlab[hf]\n"
            "또는 개별 종목은 dartlab.Company('005930')으로 자동 다운로드됩니다."
        ) from exc

    import os

    dataDir = _dataDir(category)
    dataDir.mkdir(parents=True, exist_ok=True)
    label = DATA_RELEASES[category]["label"]
    hfDir = DATA_RELEASES[category]["dir"]

    from dartlab.core.guidance import emit

    emit("download_all:hf_start", label=label, repo=HF_REPO, dir=hfDir)

    # rate limit 방지: 동시 다운로드 workers를 보수적으로 설정
    if "HF_HUB_DOWNLOAD_WORKERS" not in os.environ:
        os.environ["HF_HUB_DOWNLOAD_WORKERS"] = "4"

    localDir = _getDataRoot()
    lastErr = None
    for attempt in range(_HF_MAX_RETRIES):
        try:
            snapshot_download(
                repo_id=HF_REPO,
                repo_type="dataset",
                local_dir=str(localDir),
                allow_patterns=f"{hfDir}/*.parquet",
                force_download=forceUpdate if attempt == 0 else False,
            )
            break
        except (OSError, ConnectionError, TimeoutError) as exc:
            lastErr = exc
            emit("download_all:hf_retry", attempt=attempt + 1, error=str(exc))
            if attempt < _HF_MAX_RETRIES - 1:
                time.sleep(2 ** (attempt + 1))
    else:
        raise RuntimeError(
            f"{label} 다운로드 실패 ({_HF_MAX_RETRIES}회 재시도 후). "
            f"네트워크를 확인하거나 HF 토큰을 설정하세요: huggingface-cli login\n"
            f"마지막 에러: {lastErr}"
        )

    count = len(list(dataDir.glob("*.parquet")))
    emit("download_all:hf_done", label=label, count=count, dataDir=str(dataDir))


def download(stockCode: str) -> None:
    """특정 종목의 docs + finance + report 데이터를 모두 다운로드."""
    from dartlab.core.guidance import emit

    for category in DATA_RELEASES:
        if category in _EXPLICIT_DOWNLOAD_ONLY_CATEGORIES:
            continue
        dataDir = _dataDir(category)
        dest = dataDir / f"{stockCode}.parquet"
        label = DATA_RELEASES[category]["label"]
        if dest.exists():
            emit("download:exists", stockCode=stockCode, label=label)
            continue
        emit("download:progress", stockCode=stockCode, label=label)
        try:
            _download(stockCode, dest, category)
            size = dest.stat().st_size
            sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
            emit("download:done", label=label, sizeStr=sizeStr)
        except (URLError, socket.timeout, OSError) as e:
            if dest.exists():
                dest.unlink()
            emit("download:failed_single", stockCode=stockCode, label=label, error=str(e))


DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="

EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_LISTED_UNIVERSE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"


def buildIndex(category: str = "docs") -> pl.DataFrame:
    """로컬 parquet 전체를 스캔해서 종목 인덱스 생성.

    Returns:
        DataFrame (stockCode, corpName, rows, yearFrom, yearTo, nDocs)
        로컬에 파일이 없으면 빈 DataFrame.
    """
    dataDir = _dataDir(category)
    files = sorted(dataDir.glob("*.parquet"))
    if not files:
        return pl.DataFrame(
            schema={
                "stockCode": pl.Utf8,
                "corpName": pl.Utf8,
                "rows": pl.Int64,
                "yearFrom": pl.Utf8,
                "yearTo": pl.Utf8,
                "nDocs": pl.Int64,
            }
        )

    from alive_progress import alive_bar

    records = []
    with alive_bar(len(files), title="종목 스캔") as bar:
        for f in files:
            df = _normalizeLoadedFrame(pl.read_parquet(str(f)), category)
            code = f.stem
            name = extractCorpName(df)
            years = sorted(df["year"].unique().to_list())
            docIdCol = _docIdColumn(df)
            nDocs = df[docIdCol].n_unique() if docIdCol else 0
            records.append(
                {
                    "stockCode": code,
                    "corpName": name,
                    "rows": df.height,
                    "yearFrom": years[0] if years else None,
                    "yearTo": years[-1] if years else None,
                    "nDocs": nDocs,
                }
            )
            bar()

    return pl.DataFrame(records)


def updateEdgarListedUniverse(*, force: bool = False) -> Path:
    """SEC exchange ticker 원본으로 listed universe 캐시 갱신."""
    path = _getDataRoot() / "edgar" / "listedUniverse.parquet"
    if not force and path.exists() and not _isLocalCacheExpired(path, _EDGAR_UNIVERSE_TTL_HOURS):
        return path

    from dartlab.core.guidance import emit

    emit("edgar:universe_update")
    data = _fetchJson(EDGAR_LISTED_UNIVERSE_URL)

    records = []
    for row in data.get("data", []):
        if len(row) < 4:
            continue
        cik, name, ticker, exchange = row[:4]
        tickerStr = str(ticker or "").upper().strip()
        exchangeStr = str(exchange or "").strip()
        if not tickerStr:
            continue
        records.append(
            {
                "cik": str(cik).zfill(10),
                "ticker": tickerStr,
                "title": str(name or "").strip(),
                "exchange": exchangeStr,
                "is_exchange_listed": exchangeStr in _LISTED_EXCHANGES,
                "is_otc": exchangeStr == "OTC",
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(records).write_parquet(path)
    emit("edgar:universe_save", path=str(path))
    return path


def loadEdgarListedUniverse(*, forceUpdate: bool = False) -> pl.DataFrame:
    """현재 상장 universe 캐시 로드. 필요 시 SEC 원본에서 갱신."""
    path = updateEdgarListedUniverse(force=forceUpdate)
    return pl.read_parquet(path)


def extractCorpName(df: pl.DataFrame) -> str | None:
    """DataFrame에서 기업명 추출."""
    for col in ("corp_name", "company_name"):
        if col in df.columns:
            names = [name for name in df[col].unique().to_list() if name]
            if names:
                return names[0]
    return None


def _docIdColumn(df: pl.DataFrame) -> str | None:
    for col in ("rcept_no", "accession_no"):
        if col in df.columns:
            return col
    return None


def _isLocalCacheExpired(path: Path, ttlHours: int) -> bool:
    if not path.exists():
        return True
    ageSeconds = time.time() - path.stat().st_mtime
    return ageSeconds > ttlHours * 3600


def _fetchJson(url: str) -> dict:
    with _socketTimeout():
        request = Request(url, headers=_SEC_HEADERS)
        with urlopen(request) as resp:
            return json.loads(resp.read())


def _isEdgarDocsCheckExpired(path: Path) -> bool:
    if not path.exists():
        return True
    ageSeconds = time.time() - path.stat().st_mtime
    return ageSeconds > _EDGAR_DOCS_FRESHNESS_TTL_HOURS * 3600


def _getLatestRegularEdgarFiling(stockCode: str, *, sinceYear: int) -> dict[str, str] | None:
    from dartlab.engines.company.edgar.docs.fetch import _findFilings, _getSubmissions, _resolveTickerMeta

    meta = _resolveTickerMeta(stockCode.upper())
    submissions = _getSubmissions(meta["cik"])
    filings = _findFilings(submissions, sinceYear)
    if not filings:
        return None
    latest = filings[-1]
    return {
        "ticker": stockCode.upper(),
        "cik": meta["cik"],
        "filing_date": latest["filingDate"],
        "accession_no": latest["accessionNumber"],
        "form_type": latest["formType"],
    }


def _getLocalEdgarDocsState(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    df = pl.read_parquet(path, columns=["filing_date", "accession_no"])
    if df.is_empty():
        return None
    latestDate = df["filing_date"].drop_nulls().max()
    latestAccession = ""
    if latestDate is not None:
        latestRows = df.filter(pl.col("filing_date") == latestDate)
        if latestRows.height and "accession_no" in latestRows.columns:
            latestAccession = str(latestRows["accession_no"][0] or "")
    return {
        "latest_filing_date": str(latestDate or ""),
        "latest_accession_no": latestAccession,
    }


def _isEdgarDocsFresh(localState: dict[str, str], latestRemote: dict[str, str], *, asOf: str | None) -> bool:
    latestAccession = str(localState.get("latest_accession_no") or "")
    latestDate = str(localState.get("latest_filing_date") or "")
    if asOf is not None and latestDate:
        return latestDate >= asOf
    if latestDate and latestDate > latestRemote["filing_date"]:
        return True
    if latestDate and latestDate == latestRemote["filing_date"]:
        return latestAccession == latestRemote["accession_no"] or bool(latestAccession)
    if latestAccession:
        return latestAccession == latestRemote["accession_no"]
    return latestDate == latestRemote["filing_date"]


def _callFetchEdgarDocs(
    fetchFn,
    stockCode: str,
    path: Path,
    *,
    sinceYear: int,
    sourceMode: str,
) -> None:
    kwargs = {"sinceYear": sinceYear}
    try:
        signature = inspect.signature(fetchFn)
    except (TypeError, ValueError):
        signature = None

    if signature is None or "sourceMode" in signature.parameters:
        kwargs["sourceMode"] = sourceMode
    if signature is None or "strictQuality" in signature.parameters:
        kwargs["strictQuality"] = False

    fetchFn(stockCode, path, **kwargs)


def _rebuildEdgarDocs(stockCode: str, path: Path, *, sinceYear: int, sourceMode: str) -> None:
    from dartlab.engines.company.edgar.docs.fetch import fetchEdgarDocs

    try:
        _callFetchEdgarDocs(
            fetchEdgarDocs,
            stockCode,
            path,
            sinceYear=sinceYear,
            sourceMode=sourceMode,
        )
    except (URLError, OSError, ValueError):
        if path.exists():
            path.unlink()
        raise


def _incrementalUpdateEdgarDocs(
    stockCode: str,
    path: Path,
    *,
    sinceYear: int,
    latestRemote: dict[str, str],
) -> None:
    from dartlab.core.guidance import emit
    from dartlab.engines.company.edgar.docs.fetch import (
        FILING_TIMEOUT_SECONDS,
        _collectFilingRows,
        _findFilings,
        _getSubmissions,
        _resolveTickerMeta,
    )

    currentDf = pl.read_parquet(path)
    existingAccessions = (
        set(currentDf["accession_no"].drop_nulls().to_list()) if "accession_no" in currentDf.columns else set()
    )
    meta = _resolveTickerMeta(stockCode.upper())
    filings = _findFilings(_getSubmissions(meta["cik"]), sinceYear)
    newFilings = [filing for filing in filings if filing["accessionNumber"] not in existingAccessions]
    if not newFilings:
        emit("edgar:no_new", ticker=stockCode.upper())
        return

    emit("edgar:incremental_start", ticker=stockCode.upper(), newCount=len(newFilings))

    from alive_progress import alive_bar

    rows: list[dict] = []
    skipped: list[str] = []
    with alive_bar(
        len(newFilings),
        title=f"EDGAR 증분 | {stockCode.upper()}",
        bar="smooth",
        spinner="dots_waves",
        force_tty=True,
    ) as bar:
        _collectFilingRows(rows, newFilings, meta, stockCode.upper(), bar, FILING_TIMEOUT_SECONDS, skipped)

    if not rows:
        return
    newDf = pl.DataFrame(rows)
    merged = pl.concat([currentDf, newDf], how="vertical_relaxed")
    merged.write_parquet(path)
    emit("edgar:incremental_done", ticker=stockCode.upper(), newRows=len(rows))


# ── 메모리 최적화: Categorical + 다운캐스트 ──────────────

# 반복 빈도 높은 문자열 컬럼 → Categorical (정수 인덱스로 90%+ 절감)
_CATEGORICAL_COLS = frozenset(
    {
        "source",  # dart/edgar (== 비교만 사용)
        "account_id",  # XBRL 계정 ID (수백 종류, 수만 행, == 비교만)
        "blockType",  # text/table/heading 등 (== 비교만)
        "form_type",  # 10-K/10-Q 등 (== 비교만)
        # 제외: report_type, section_title, sj_div, topic → .str 연산 사용
    }
)

# 작은 정수 컬럼 → Int32 (Int64 대비 50% 절감 + CPU 캐시 친화)
_DOWNCAST_INT_COLS = frozenset(
    {
        "year",
        "section_order",
        "bsns_year",
    }
)


def _optimizeMemory(df: pl.DataFrame) -> pl.DataFrame:
    """Categorical 전환 + Int 다운캐스트로 메모리 절감."""
    exprs: list[pl.Expr] = []
    schema = df.schema
    for col, dtype in schema.items():
        if col in _CATEGORICAL_COLS and dtype == pl.Utf8:
            exprs.append(pl.col(col).cast(pl.Categorical))
        elif col in _DOWNCAST_INT_COLS and dtype == pl.Int64:
            exprs.append(pl.col(col).cast(pl.Int32))
    if exprs:
        return df.with_columns(exprs)
    return df


def _normalizeLoadedFrame(df: pl.DataFrame, category: str) -> pl.DataFrame:
    if category == "docs":
        df = _normalizeDartDocs(df)
    elif category == "edgarDocs":
        df = _normalizeEdgarDocs(df)
    return _optimizeMemory(df)


def _normalizeDartDocs(df: pl.DataFrame) -> pl.DataFrame:
    cols = set(df.columns)
    exprs: list[pl.Expr] = []

    if "source" not in cols:
        exprs.append(pl.lit("dart").alias("source"))
    if "entity_id" not in cols and "stock_code" in cols:
        exprs.append(pl.col("stock_code").alias("entity_id"))
    if "doc_id" not in cols and "rcept_no" in cols:
        exprs.append(pl.col("rcept_no").alias("doc_id"))
    if "doc_date" not in cols and "rcept_date" in cols:
        exprs.append(pl.col("rcept_date").alias("doc_date"))
    if "doc_url" not in cols and "section_url" in cols:
        exprs.append(pl.col("section_url").alias("doc_url"))
    if "period_key" not in cols and "report_type" in cols:
        from dartlab.core.reportSelector import parsePeriodKey

        exprs.append(pl.col("report_type").map_elements(parsePeriodKey, return_dtype=pl.Utf8).alias("period_key"))

    if exprs:
        return df.with_columns(exprs)
    return df


def _normalizeEdgarDocs(df: pl.DataFrame) -> pl.DataFrame:
    cols = set(df.columns)
    exprs: list[pl.Expr] = []

    if "report_type" not in cols and "form_type" in cols:
        exprs.append(
            pl.struct([col for col in ("form_type", "period_end", "year") if col in cols])
            .map_elements(_edgarReportTypeFromRow, return_dtype=pl.Utf8)
            .alias("report_type")
        )

    if "source" not in cols:
        exprs.append(pl.lit("edgar").alias("source"))
    if "entity_id" not in cols and "ticker" in cols:
        exprs.append(pl.col("ticker").alias("entity_id"))
    if "doc_id" not in cols and "accession_no" in cols:
        exprs.append(pl.col("accession_no").alias("doc_id"))
    if "doc_date" not in cols and "filing_date" in cols:
        exprs.append(pl.col("filing_date").alias("doc_date"))
    if "doc_url" not in cols and "filing_url" in cols:
        exprs.append(pl.col("filing_url").alias("doc_url"))

    result = df.with_columns(exprs) if exprs else df
    return _applyEdgarPeriodKeys(result)


def _edgarReportTypeFromRow(row: dict) -> str | None:
    formType = row.get("form_type")
    periodEnd = row.get("period_end")
    year = row.get("year")
    if not formType:
        return None
    if not periodEnd:
        if formType in ("10-K", "20-F", "40-F") and year:
            return f"{formType} ({year}.12)"
        return str(formType)

    match = re.match(r"(\d{4})-(\d{2})", str(periodEnd))
    if not match:
        return str(formType)
    year, month = match.groups()
    return f"{formType} ({year}.{month})"


def _applyEdgarPeriodKeys(df: pl.DataFrame) -> pl.DataFrame:
    if "accession_no" not in df.columns or "form_type" not in df.columns:
        return df

    cols = [col for col in ("accession_no", "form_type", "filing_date", "period_end", "year") if col in df.columns]
    filingDf = df.select(cols).unique(subset=["accession_no"]).sort(["filing_date", "accession_no"])
    filings = filingDf.to_dicts()
    periodMap = _inferEdgarPeriodKeyMap(filings)
    if not periodMap:
        return df

    return df.with_columns(
        pl.col("accession_no")
        .map_elements(lambda accession: periodMap.get(str(accession)), return_dtype=pl.Utf8)
        .alias("period_key")
    )


def _inferEdgarPeriodKeyMap(filings: list[dict]) -> dict[str, str | None]:
    annualForms = {"10-K", "20-F", "40-F"}
    enriched = []
    for filing in filings:
        accession = str(filing.get("accession_no") or "")
        formType = str(filing.get("form_type") or "")
        filingDate = str(filing.get("filing_date") or "")
        periodEnd = filing.get("period_end")
        periodEndStr = str(periodEnd) if periodEnd else ""
        sortKey = periodEndStr or filingDate
        enriched.append(
            {
                "accession_no": accession,
                "form_type": formType,
                "filing_date": filingDate,
                "period_end": periodEndStr,
                "year": str(filing.get("year") or ""),
                "sort_key": sortKey,
            }
        )

    enriched.sort(key=lambda row: (row["sort_key"], row["filing_date"], row["accession_no"]))
    periodMap: dict[str, str | None] = {}

    annualIdx = [i for i, row in enumerate(enriched) if row["form_type"] in annualForms and row["period_end"]]

    for idx in annualIdx:
        annual = enriched[idx]
        periodMap[annual["accession_no"]] = annual["period_end"][:4]

    for pos in range(1, len(annualIdx)):
        prevAnnual = annualIdx[pos - 1]
        curAnnual = annualIdx[pos]
        fy = enriched[curAnnual]["period_end"][:4]
        qRows = [row for row in enriched[prevAnnual + 1 : curAnnual] if row["form_type"] == "10-Q"]
        for qNum, row in enumerate(qRows[:3], start=1):
            periodMap[row["accession_no"]] = f"{fy}Q{qNum}"

    if annualIdx:
        lastAnnual = annualIdx[-1]
        lastFy = int(enriched[lastAnnual]["period_end"][:4])
        qRows = [row for row in enriched[lastAnnual + 1 :] if row["form_type"] == "10-Q"]
        for qNum, row in enumerate(qRows[:3], start=1):
            periodMap[row["accession_no"]] = f"{lastFy + 1}Q{qNum}"

    if not annualIdx:
        for row in enriched:
            if row["form_type"] in annualForms and row["year"]:
                periodMap[row["accession_no"]] = row["year"]

    return periodMap
