"""데이터 로딩 및 공통 유틸."""

import inspect
import json
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen, urlretrieve

import polars as pl

from dartlab.core.dataConfig import (
    DATA_RELEASES,
    releaseApiUrl,
    releaseBaseUrl,
    shardAllTags,
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


def _dataDir(category: str = "docs") -> Path:
    return _getDataRoot() / DATA_RELEASES[category]["dir"]


def _downloadWithRetry(url: str, dest: Path) -> None:
    """URL → dest 다운로드. 최대 3회 재시도 (2초, 4초 대기)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    lastErr = None
    for attempt in range(_MAX_RETRIES):
        old_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(_DOWNLOAD_TIMEOUT)
            urlretrieve(url, dest)
            return
        except (URLError, socket.timeout, OSError) as e:
            lastErr = e
            if dest.exists():
                dest.unlink()
            if attempt < _MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
        finally:
            socket.setdefaulttimeout(old_timeout)
    raise lastErr


def _download(stockCode: str, dest: Path, category: str = "docs") -> None:
    url = f"{releaseBaseUrl(category, stockCode=stockCode)}/{stockCode}.parquet"
    _downloadWithRetry(url, dest)


def loadData(
    stockCode: str,
    category: str = "docs",
    *,
    sinceYear: int | None = None,
    asOf: str | None = None,
    refresh: str = "auto",
) -> pl.DataFrame:
    """종목코드 → DataFrame. 로컬에 없으면 릴리즈에서 자동 다운로드."""
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
        label = DATA_RELEASES[category]["label"]
        print(f"[dartlab] {stockCode}.parquet ({label}) 로컬에 없음 → GitHub Release에서 다운로드...")
        try:
            _download(stockCode, path, category)
            print(f"[dartlab] 저장 완료: {path}")
        except (URLError, socket.timeout, OSError) as e:
            if path.exists():
                path.unlink()
            raise RuntimeError(
                f"데이터 다운로드 실패 ({stockCode}): {e}\n"
                f"  해결 방법:\n"
                f"  1. 네트워크 연결 확인\n"
                f"  2. `dartlab download {stockCode}` 명령으로 수동 다운로드\n"
                f"  3. GitHub Releases 페이지에서 직접 다운로드 후 {dataDir}/ 에 배치"
            ) from e
        except ValueError:
            if path.exists():
                path.unlink()
            raise
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
    from dartlab.engines.edgar.docs.fetch import fetchEdgarDocs

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
        label = DATA_RELEASES["edgarDocs"]["label"]
        print(f"[dartlab] {stockCode}.parquet ({label}) 로컬에 없음 → GitHub Release에서 다운로드...")
        try:
            _download(stockCode, path, "edgarDocs")
            print(f"[dartlab] 저장 완료: {path}")
        except (URLError, socket.timeout, OSError):
            if path.exists():
                path.unlink()
            print("[dartlab] GitHub Release에 없거나 다운로드 실패 → SEC EDGAR API 직접 수집으로 전환")
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


def _fetchAssets(tag: str) -> list[dict]:
    """릴리즈 태그에서 에셋 목록 + updated_at 조회."""
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(_DOWNLOAD_TIMEOUT)
        with urlopen(releaseApiUrl(tag=tag)) as resp:
            data = json.loads(resp.read())
    finally:
        socket.setdefaulttimeout(old_timeout)
    return [a for a in data["assets"] if a["name"].endswith(".parquet")]


def _isOutdated(localPath: Path, remoteUpdatedAt: str) -> bool:
    """로컬 파일이 원격보다 오래됐는지 확인."""
    if not localPath.exists():
        return True
    localMtime = datetime.fromtimestamp(localPath.stat().st_mtime, tz=timezone.utc)
    remoteTime = datetime.fromisoformat(remoteUpdatedAt.replace("Z", "+00:00"))
    return localMtime < remoteTime


def downloadAll(category: str = "docs", *, forceUpdate: bool = False) -> None:
    """GitHub Release의 전체 parquet을 한번에 다운로드.

    Args:
        category: "docs", "finance", "report".
        forceUpdate: True면 로컬 파일이 있어도 원격 업데이트 일자가 더 최신이면 재다운로드.
    """
    if category in _EXPLICIT_DOWNLOAD_ONLY_CATEGORIES:
        raise ValueError(
            f"{category}는 전체 다운로드를 지원하지 않음. "
            f"용량이 크므로 개별 종목 loadData(..., category='{category}') 또는 전용 샘플만 사용하세요."
        )

    from alive_progress import alive_bar

    dataDir = _dataDir(category)
    dataDir.mkdir(parents=True, exist_ok=True)
    label = DATA_RELEASES[category]["label"]

    conf = DATA_RELEASES[category]
    if "shards" in conf:
        tags = shardAllTags(category)
    else:
        tags = [conf["tag"]]

    allAssets: list[dict] = []
    print(f"[dartlab] {label} — GitHub Release 에셋 목록 조회 중... ({len(tags)}개 태그)")
    for tag in tags:
        assets = _fetchAssets(tag)
        allAssets.extend(assets)
        print(f"  {tag}: {len(assets)}개")

    toDownload = []
    skipped = 0
    for asset in allAssets:
        dest = dataDir / asset["name"]
        if forceUpdate and _isOutdated(dest, asset["updated_at"]):
            toDownload.append(asset)
        elif not dest.exists():
            toDownload.append(asset)
        else:
            skipped += 1

    if not toDownload:
        print(f"[dartlab] 전체 {len(allAssets)}종목 이미 최신 ({dataDir})")
        return

    action = "다운로드 (신규+업데이트)" if forceUpdate else "신규 다운로드"
    print(f"[dartlab] {action}: {len(toDownload)}종목 (스킵: {skipped})")

    failed = 0
    with alive_bar(len(toDownload), title="다운로드") as bar:
        for asset in toDownload:
            dest = dataDir / asset["name"]
            try:
                _downloadWithRetry(asset["browser_download_url"], dest)
            except (URLError, socket.timeout, OSError) as e:
                print(f"\n[dartlab] {asset['name']} 다운로드 실패 (3회 재시도 후): {e}")
                if dest.exists():
                    dest.unlink()
                failed += 1
            bar()

    if failed:
        print(f"[dartlab] 완료 → {dataDir} (실패: {failed}건)")
    else:
        print(f"[dartlab] 완료 → {dataDir}")


def download(stockCode: str) -> None:
    """특정 종목의 docs + finance 데이터를 모두 다운로드."""
    for category in DATA_RELEASES:
        if category in _EXPLICIT_DOWNLOAD_ONLY_CATEGORIES:
            continue
        dataDir = _dataDir(category)
        dest = dataDir / f"{stockCode}.parquet"
        label = DATA_RELEASES[category]["label"]
        if dest.exists():
            print(f"[dartlab] {stockCode} ({label}) 이미 존재")
            continue
        print(f"[dartlab] {stockCode} ({label}) 다운로드 중...")
        try:
            _download(stockCode, dest, category)
            print(f"[dartlab] 저장 완료: {dest}")
        except (URLError, socket.timeout, OSError) as e:
            if dest.exists():
                dest.unlink()
            print(f"[dartlab] {stockCode} ({label}) 다운로드 실패 (3회 재시도 후): {e}")


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
            records.append({
                "stockCode": code,
                "corpName": name,
                "rows": df.height,
                "yearFrom": years[0] if years else None,
                "yearTo": years[-1] if years else None,
                "nDocs": nDocs,
            })
            bar()

    return pl.DataFrame(records)


def updateEdgarListedUniverse(*, force: bool = False) -> Path:
    """SEC exchange ticker 원본으로 listed universe 캐시 갱신."""
    path = _getDataRoot() / "edgar" / "listedUniverse.parquet"
    if not force and path.exists() and not _isLocalCacheExpired(path, _EDGAR_UNIVERSE_TTL_HOURS):
        return path

    print("[dartlab] SEC listed universe 갱신 중...")
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
        records.append({
            "cik": str(cik).zfill(10),
            "ticker": tickerStr,
            "title": str(name or "").strip(),
            "exchange": exchangeStr,
            "is_exchange_listed": exchangeStr in _LISTED_EXCHANGES,
            "is_otc": exchangeStr == "OTC",
        })

    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(records).write_parquet(path)
    print(f"[dartlab] 저장 완료: {path}")
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
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(_DOWNLOAD_TIMEOUT)
        request = Request(url, headers=_SEC_HEADERS)
        with urlopen(request) as resp:
            return json.loads(resp.read())
    finally:
        socket.setdefaulttimeout(old_timeout)


def _isEdgarDocsCheckExpired(path: Path) -> bool:
    if not path.exists():
        return True
    ageSeconds = time.time() - path.stat().st_mtime
    return ageSeconds > _EDGAR_DOCS_FRESHNESS_TTL_HOURS * 3600


def _getLatestRegularEdgarFiling(stockCode: str, *, sinceYear: int) -> dict[str, str] | None:
    from dartlab.engines.edgar.docs.fetch import _findFilings, _getSubmissions, _resolveTickerMeta

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
    from dartlab.engines.edgar.docs.fetch import fetchEdgarDocs

    try:
        _callFetchEdgarDocs(
            fetchEdgarDocs,
            stockCode,
            path,
            sinceYear=sinceYear,
            sourceMode=sourceMode,
        )
    except Exception:
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
    from dartlab.engines.edgar.docs.fetch import (
        FILING_TIMEOUT_SECONDS,
        _collectFilingRows,
        _findFilings,
        _getSubmissions,
        _resolveTickerMeta,
    )

    currentDf = pl.read_parquet(path)
    existingAccessions = set(currentDf["accession_no"].drop_nulls().to_list()) if "accession_no" in currentDf.columns else set()
    meta = _resolveTickerMeta(stockCode.upper())
    filings = _findFilings(_getSubmissions(meta["cik"]), sinceYear)
    newFilings = [filing for filing in filings if filing["accessionNumber"] not in existingAccessions]
    if not newFilings:
        return

    rows: list[dict] = []
    skipped: list[str] = []
    _collectFilingRows(rows, newFilings, meta, stockCode.upper(), None, FILING_TIMEOUT_SECONDS, skipped)
    if not rows:
        return
    newDf = pl.DataFrame(rows)
    merged = pl.concat([currentDf, newDf], how="vertical_relaxed")
    merged.write_parquet(path)


def _normalizeLoadedFrame(df: pl.DataFrame, category: str) -> pl.DataFrame:
    if category == "docs":
        return _normalizeDartDocs(df)
    if category == "edgarDocs":
        return _normalizeEdgarDocs(df)
    return df


def _normalizeDartDocs(df: pl.DataFrame) -> pl.DataFrame:
    exprs: list[pl.Expr] = []

    if "source" not in df.columns:
        exprs.append(pl.lit("dart").alias("source"))
    if "entity_id" not in df.columns and "stock_code" in df.columns:
        exprs.append(pl.col("stock_code").alias("entity_id"))
    if "doc_id" not in df.columns and "rcept_no" in df.columns:
        exprs.append(pl.col("rcept_no").alias("doc_id"))
    if "doc_date" not in df.columns and "rcept_date" in df.columns:
        exprs.append(pl.col("rcept_date").alias("doc_date"))
    if "doc_url" not in df.columns and "section_url" in df.columns:
        exprs.append(pl.col("section_url").alias("doc_url"))
    if "period_key" not in df.columns and "report_type" in df.columns:
        from dartlab.core.reportSelector import parsePeriodKey

        exprs.append(
            pl.col("report_type")
            .map_elements(parsePeriodKey, return_dtype=pl.Utf8)
            .alias("period_key")
        )

    if exprs:
        return df.with_columns(exprs)
    return df


def _normalizeEdgarDocs(df: pl.DataFrame) -> pl.DataFrame:
    exprs: list[pl.Expr] = []

    if "report_type" not in df.columns and "form_type" in df.columns:
        exprs.append(
            pl.struct([col for col in ("form_type", "period_end", "year") if col in df.columns])
            .map_elements(_edgarReportTypeFromRow, return_dtype=pl.Utf8)
            .alias("report_type")
        )

    if "source" not in df.columns:
        exprs.append(pl.lit("edgar").alias("source"))
    if "entity_id" not in df.columns and "ticker" in df.columns:
        exprs.append(pl.col("ticker").alias("entity_id"))
    if "doc_id" not in df.columns and "accession_no" in df.columns:
        exprs.append(pl.col("accession_no").alias("doc_id"))
    if "doc_date" not in df.columns and "filing_date" in df.columns:
        exprs.append(pl.col("filing_date").alias("doc_date"))
    if "doc_url" not in df.columns and "filing_url" in df.columns:
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
        enriched.append({
            "accession_no": accession,
            "form_type": formType,
            "filing_date": filingDate,
            "period_end": periodEndStr,
            "year": str(filing.get("year") or ""),
            "sort_key": sortKey,
        })

    enriched.sort(key=lambda row: (row["sort_key"], row["filing_date"], row["accession_no"]))
    periodMap: dict[str, str | None] = {}

    annualIdx = [
        i for i, row in enumerate(enriched)
        if row["form_type"] in annualForms and row["period_end"]
    ]

    for idx in annualIdx:
        annual = enriched[idx]
        periodMap[annual["accession_no"]] = annual["period_end"][:4]

    for pos in range(1, len(annualIdx)):
        prevAnnual = annualIdx[pos - 1]
        curAnnual = annualIdx[pos]
        fy = enriched[curAnnual]["period_end"][:4]
        qRows = [
            row for row in enriched[prevAnnual + 1:curAnnual]
            if row["form_type"] == "10-Q"
        ]
        for qNum, row in enumerate(qRows[:3], start=1):
            periodMap[row["accession_no"]] = f"{fy}Q{qNum}"

    if annualIdx:
        lastAnnual = annualIdx[-1]
        lastFy = int(enriched[lastAnnual]["period_end"][:4])
        qRows = [
            row for row in enriched[lastAnnual + 1:]
            if row["form_type"] == "10-Q"
        ]
        for qNum, row in enumerate(qRows[:3], start=1):
            periodMap[row["accession_no"]] = f"{lastFy + 1}Q{qNum}"

    if not annualIdx:
        for row in enriched:
            if row["form_type"] in annualForms and row["year"]:
                periodMap[row["accession_no"]] = row["year"]

    return periodMap
