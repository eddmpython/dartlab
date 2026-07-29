"""데이터 로딩 및 공통 유틸."""

import json
import os
import socket
import sys
import time
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path

import polars as pl

import dartlab.core.dataLoaderIndex as dataLoaderIndex
from dartlab.core.dataConfig import (
    DATA_RELEASES,
    hfBaseUrl,
    repoFor,
    resolveDataCategory,
)

DataIndexError = dataLoaderIndex.DataIndexError

_IS_PYODIDE = sys.platform == "emscripten"

# Phase D — _LOAD_CACHE 폐기.
# 이전 정책: 같은 (stockCode, category, …) 조합 결과를 LRU(max 8) 캐시.
# 폐기 이유:
#   1. BoundedCache (`Company._cache`) 가 이미 _financeStmt_* / _sections 등 결과 캐시.
#   2. Phase A 의 IPC mirror + Phase D 의 mmap path 가 disk 재읽기를 ms 단위로 단축.
#   3. _LOAD_CACHE 는 *원본 parquet → DataFrame* 을 영구 heap 점유 — BoundedCache 와 이중.
#   4. *_finance_* pinned 가 BoundedCache 안 in-memory 재사용을 *이미* 잡음.
# 폐기 효과: heap 점유 ↓ (8 × DataFrame × ~수백MB = 수 GB 잠재 회수).
# 잔존: `_clearLoadCache` 는 호환 위해 no-op stub 으로 유지 (memory.py 가 EMERGENCY 시 호출).
_LOAD_CACHE: "OrderedDict[tuple, pl.DataFrame]" = OrderedDict()  # 항상 empty — backward-compat alias
_LOAD_CACHE_MAX = 0  # backward-compat 상수 — 폐기 신호


def _clearLoadCache() -> None:
    """[deprecated] _LOAD_CACHE 가 폐기됨. backward-compat no-op."""
    _LOAD_CACHE.clear()  # 안전 — 항상 empty


def readParquetSafe(path, *, columns: list[str] | None = None) -> pl.DataFrame:
    """polars read_parquet with pyarrow fallback (pyodide WASM 호환).

    polars WASM wheel 은 read_parquet 이 비활성(PyLazyFrame.new_from_parquet 부재)
    이므로 pyarrow 로 우회한 뒤 arrowToPolars 로 변환한다. read_table 이 아니라 저수준
    ParquetFile.read 를 쓴다(read_table 은 첫 호출에 pyarrow.dataset + pandas 를 lazy import 해
    브라우저 첫 데이터 로드에 수 초를 먹는다. 단일 파일 읽기라 dataset 스캐너 불요, table 은 동일).
    일반 환경에서는 pl.read_parquet 그대로 사용(byte-identical).

    Args:
        path: 단일 parquet 경로(str/Path/bytes) 또는 경로 리스트(여러 파일 수직 concat).
        columns: 열 프로젝션. None 이면 전체 열.
    """
    if not _IS_PYODIDE:
        return pl.read_parquet(path, columns=columns)
    import pyarrow as pa

    from dartlab.core.dataLoaderPyodide import PyodideParquetError, readParquetFrame

    paths = list(path) if isinstance(path, (list, tuple)) else [path]
    frames: list[pl.DataFrame] = []
    for p in paths:
        try:
            frames.append(readParquetFrame(p, columns=columns))
        except MemoryError:
            raise
        except (OSError, pa.ArrowInvalid) as exc:
            raise PyodideParquetError("읽기", "<bytes>" if isinstance(p, bytes) else p, exc) from exc
        except pa.ArrowException:
            raise
    return frames[0] if len(frames) == 1 else pl.concat(frames, how="vertical_relaxed")


if not _IS_PYODIDE:
    from urllib.error import URLError
    from urllib.parse import urlsplit
    from urllib.request import Request, urlopen, urlretrieve


def _getDataRoot() -> Path:
    from dartlab import config

    return Path(config.dataDir)


_DOWNLOAD_TIMEOUT = 30
_MAX_RETRIES = 3
_EDGAR_UNIVERSE_TTL_HOURS = 24
_DART_FRESHNESS_TTL_HOURS = 12  # 일일 HF 수집 주기(03:00 KST)에 맞춰 12h — 최대 stale 윈도우 반감
_KRX_FRESHNESS_TTL_HOURS = 1  # 장마감 후 일별 갱신 데이터라 stale 허용폭을 짧게 둔다

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


def _dataDir(category: str = "panel") -> Path:
    category = resolveDataCategory(category)
    return _getDataRoot() / DATA_RELEASES[category]["dir"]


def _downloadWithRetry(url: str, dest: Path) -> None:
    """URL → dest 다운로드. 최대 3회 재시도 (2초, 4초 대기)."""
    from dartlab.core.dataLoaderFreshness import downloadWithRetry

    downloadWithRetry(url, dest, maxRetries=_MAX_RETRIES, socketTimeout=_socketTimeout, urlretrieve=urlretrieve)


def _checkRemoteFreshness(stockCode: str, localPath: Path, category: str = "panel") -> bool | None:
    """로컬 파일이 원격보다 오래됐는지 HTTP HEAD로 확인.

    검증 2단계:
    1. ETag 비교 (HF의 content hash) — 다르면 stale
    2. Content-Length 비교 (HF가 알려준 파일 크기) — 다르면 stale
       → ETag만 같고 실제 내용/크기가 다른 손상 케이스 방어

    Returns: True=stale, False=fresh, None=판단불가(네트워크 오류 등).

    핵심 안전 규칙:
    - .etag 사이드카 파일은 **다운로드 성공 직후에만 작성**해야 한다 (_saveEtag).
    - 여기서 etag 파일이 없는 상태는 "이전에 다운로드 받은 적이 없거나, 외부 경로로
      복사된 stale 파일"이다. 어느 쪽이든 fresh로 판정하면 안 된다.
    - 과거 버그: etag 없으면 현재 HF ETag를 저장 + return False(fresh) → parquet은
      옛날 그대로인데 .etag만 새로 만들어져서 영구적으로 stale 데이터가 고정됨.
    - 수정: etag 없으면 stale(True) 반환하여 다운로드를 강제. _saveEtag가 다운로드
      성공 직후 etag를 기록한다.
    """
    from dartlab.core.dataLoaderFreshness import checkRemoteFreshness

    category = resolveDataCategory(category)
    return checkRemoteFreshness(
        stockCode,
        localPath,
        category,
        hfBaseUrl=hfBaseUrl,
        fetchRemoteEtagAndSize=_fetchRemoteEtagAndSize,
    )


def _saveEtag(stockCode: str, dest: Path, category: str = "panel") -> None:
    """다운로드 성공 후 HF ETag를 사이드카 파일에 저장."""
    from dartlab.core.dataLoaderFreshness import saveEtag

    category = resolveDataCategory(category)
    saveEtag(stockCode, dest, category, hfBaseUrl=hfBaseUrl, fetchRemoteEtag=_fetchRemoteEtag)


def _fetchRemoteEtag(url: str) -> str:
    """HTTP HEAD로 원격 ETag 조회. 없으면 빈 문자열."""
    etag, _, _ = _fetchRemoteHeaders(url)
    return etag


def _fetchRemoteHeaders(url: str) -> tuple[str, str | None, str | None]:
    """검증된 HTTPS HEAD 응답에서 freshness header를 한 번 읽는다."""
    parsedUrl = urlsplit(url)
    if parsedUrl.scheme != "https" or not parsedUrl.hostname:
        raise ValueError(f"remote metadata URL must use HTTPS: {url!r}")
    req = Request(url, method="HEAD")
    token = os.environ.get("HF_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    # urlsplit 검사로 HTTPS와 netloc이 확인된 Request만 연다.
    with _socketTimeout(10), urlopen(req) as resp:  # nosec B310
        etag = resp.headers.get("ETag", "").strip('" ')
        linkedSize = resp.headers.get("X-Linked-Size")
        contentLength = resp.headers.get("Content-Length")
    return etag, linkedSize, contentLength


def _remoteSize(linkedSize: str | None, contentLength: str | None) -> int:
    for header, value in (("X-Linked-Size", linkedSize), ("Content-Length", contentLength)):
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"invalid remote {header}: {value!r}")
        normalized = value.strip()
        if not normalized:
            continue
        if not normalized.isascii() or not normalized.isdecimal():
            raise ValueError(f"invalid remote {header}: {value!r}")
        return int(normalized)
    return 0


def _fetchRemoteEtagAndSize(url: str) -> tuple[str, int]:
    """HTTP HEAD로 원격 ETag + Content-Length 동시 조회.

    HF는 LFS 파일에 대해 X-Linked-Size 헤더로 실제 파일 크기를 제공.
    일반 파일은 Content-Length. 둘 중 하나라도 있으면 사용.
    """
    etag, linkedSize, contentLength = _fetchRemoteHeaders(url)
    size = _remoteSize(linkedSize, contentLength)
    return etag, size


def _download(stockCode: str, dest: Path, category: str = "panel") -> None:
    """HuggingFace 데이터셋에서 단건 다운로드."""
    category = resolveDataCategory(category)
    hfUrl = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    _downloadWithRetry(hfUrl, dest)
    _saveEtag(stockCode, dest, category)


_STALE_WARN_DAYS = 7  # 로컬 데이터가 7일 이상 갱신 안 됐을 때 사용자에게 경고
_staleWarnedPaths: set[str] = set()  # 세션당 경로별 1회만 경고


def _maybeWarnStale(path: Path) -> None:
    """로컬 데이터가 매우 오래됐으면(7일+) 한 번 경고. 같은 세션에서 같은 경로는 중복 안 함."""
    from dartlab.core.dataLoaderFreshness import maybeWarnStale

    maybeWarnStale(path, warnedPaths=_staleWarnedPaths, staleWarnDays=_STALE_WARN_DAYS)


def _shouldRefreshDart(path: Path, refresh: str) -> bool:
    """DART 카테고리 로컬 파일의 갱신 필요 여부 판단."""
    from dartlab.core.dataLoaderFreshness import shouldRefreshDart

    return shouldRefreshDart(
        path,
        refresh,
        staleWarnDays=_STALE_WARN_DAYS,
        dartFreshnessTtlHours=_DART_FRESHNESS_TTL_HOURS,
        warnStale=_maybeWarnStale,
    )


def _shouldRefreshHfCategory(path: Path, category: str, refresh: str) -> bool:
    """HF 공개 parquet 카테고리별 freshness 정책."""
    from dartlab.core.dataLoaderFreshness import shouldRefreshHfCategory

    return shouldRefreshHfCategory(
        path,
        category,
        refresh,
        krxFreshnessTtlHours=_KRX_FRESHNESS_TTL_HOURS,
        shouldRefreshDartFunc=_shouldRefreshDart,
    )


def _refreshFromHf(stockCode: str, path: Path, category: str) -> None:
    """ETag 비교 후 HF가 최신이면 다운로드로 갱신. 실패 시 기존 파일 유지."""
    from dartlab.core.dataLoaderFreshness import refreshFromHf

    category = resolveDataCategory(category)
    refreshFromHf(
        stockCode,
        path,
        category,
        dataReleases=DATA_RELEASES,
        hfBaseUrl=hfBaseUrl,
        checkRemoteFreshness=_checkRemoteFreshness,
        downloadWithRetry=_downloadWithRetry,
        saveEtag=_saveEtag,
    )


def repairLocalCache(category: str = "finance", *, dryRun: bool = False) -> dict[str, int]:
    """로컬 dart 캐시 전수 무결성 검사 + 손상된 파일 자동 재다운로드.

    과거 ETag 사이드카 first-write 버그(_checkRemoteFreshness가 etag 없을 때
    현재 HF ETag를 그냥 저장하고 fresh 판정)로 인해 영구 stale로 굳어진 로컬
    parquet들을 전부 회복하기 위한 일괄 도구.

    검사 절차:
    1. 카테고리 폴더의 모든 *.parquet 순회
    2. 각각 _checkRemoteFreshness로 stale 판단 (ETag + Content-Length 2단계)
    3. stale이면 새 코드로 다운로드 (dryRun=True면 통계만)

    Args:
        category: "finance", "report", "panel" 중 하나.
        dryRun: True면 다운로드 안 하고 통계만 반환

    Returns:
        {"checked": N, "stale": N, "repaired": N, "failed": N, "fresh": N}
    """
    category = resolveDataCategory(category)
    dataDir = _dataDir(category)
    if not dataDir.exists():
        return {"checked": 0, "stale": 0, "repaired": 0, "failed": 0, "fresh": 0}

    stats = {"checked": 0, "stale": 0, "repaired": 0, "failed": 0, "fresh": 0}
    for parquet in sorted(dataDir.glob("*.parquet")):
        stockCode = parquet.stem
        stats["checked"] += 1
        stale = _checkRemoteFreshness(stockCode, parquet, category)
        if stale is None:
            stats["failed"] += 1
            continue
        if not stale:
            stats["fresh"] += 1
            continue
        stats["stale"] += 1
        if dryRun:
            continue
        try:
            _refreshFromHf(stockCode, parquet, category)
            stats["repaired"] += 1
        except (URLError, socket.timeout, OSError):
            stats["failed"] += 1
    return stats


def loadData(
    stockCode: str,
    category: str = "panel",
    *,
    sinceYear: int | None = None,
    asOf: str | None = None,
    refresh: str = "auto",
    columns: list[str] | None = None,
    predicate: pl.Expr | None = None,
) -> pl.DataFrame:
    """종목코드 → DataFrame. 로컬에 없으면 릴리즈에서 자동 다운로드.

    Phase D 에서 `_LOAD_CACHE` 폐기 — 매 호출 disk 재로드. cache 역할은
    BoundedCache (accessor 결과) + IPC mmap (`.arrow` mirror, OS page cache
    위임) 가 분담. `refresh="force"` 는 ETag 기반 HF refresh 만 강제.

    ``predicate`` 는 polars expression — 전달 시 ``scan_parquet().filter(
    predicate).collect(streaming)`` 으로 predicate pushdown 활성 (Phase A
    의 row group sort 가 skipping 동행). caller (single-statement fast path)
    가 ``pl.col("sj_div").is_in([...])`` 형식으로 디스크 디코드량 축소.
    """
    category = resolveDataCategory(category)
    effectiveSinceYear = 2009 if category == "edgarDocs" and sinceYear is None else sinceYear
    if _IS_PYODIDE:
        return _loadDataPyodide(
            stockCode,
            category,
            sinceYear=effectiveSinceYear,
            asOf=asOf,
            refresh=refresh,
            columns=columns,
            predicate=predicate,
        )
    from dartlab.core.memory import checkMemoryAndGc

    dataDir = _dataDir(category)
    path = dataDir / f"{stockCode}.parquet"

    # KRX daily bulk data is updated after market close. In long-lived server
    # processes, the in-memory LRU must not pin yesterday's parquet after the
    # short KRX freshness TTL expires.
    krxShouldRefresh: bool | None = None
    if (
        category in {"krxPrices", "krxIndices", "govPrices", "govPriceCompany", "govIndices", "govIndexPerIndex"}
        and refresh == "auto"
    ):
        krxShouldRefresh = _shouldRefreshHfCategory(path, category, refresh)

    checkMemoryAndGc(f"loadData({stockCode},{category})")
    if category == "edgarDocs":
        # registry dispatch (정공법 B — DIP). providers/edgar 가 EdgarDocsLoader 등록.
        from dartlab.core.loaders import getLoader

        loader = getLoader("edgarDocs")
        if loader is None:
            raise RuntimeError("edgarDocs LoaderProvider 미등록 — providers.edgar 모듈 로드 실패")
        loader.ensure(
            stockCode,
            path,
            sinceYear=effectiveSinceYear or 2009,
            asOf=asOf,
            refresh=refresh,
        )
    else:
        shouldRefresh = (
            krxShouldRefresh if krxShouldRefresh is not None else _shouldRefreshHfCategory(path, category, refresh)
        )
        _ensureLocalParquet(stockCode, path, category, shouldRefresh=shouldRefresh)
    # Phase D — .arrow IPC mirror 가 옆에 있고 더 새것이면 mmap 경로 우선 (OS page cache 위임).
    # Phase A 가 빌드한 mirror 파일. mmap path 는 useLazy 와 무관 — predicate 도 lazy filter.
    ipcPath = path.with_suffix(".arrow")
    useIpcMmap = not _IS_PYODIDE and ipcPath.exists() and ipcPath.stat().st_mtime >= path.stat().st_mtime

    # lazy scan: sinceYear · columns · predicate 중 하나라도 있으면 scan_parquet 경로
    yearColCandidates = ("year", "bsns_year")
    useLazy = sinceYear is not None or columns is not None or predicate is not None
    if useIpcMmap and (useLazy or True):
        # IPC mmap — 결과 buffer 가 mmap pages 백킹, RSS 기여 = touched pages.
        # predicate / sinceYear / columns 도 동일하게 적용 (lazy 가능).
        lf = pl.scan_ipc(str(ipcPath), memory_map=True)
        schemaNames = lf.collect_schema().names()
        if sinceYear is not None:
            for colName in yearColCandidates:
                if colName in schemaNames:
                    yearCol = pl.col(colName)
                    if str(lf.collect_schema()[colName]) == "String":
                        yearCol = yearCol.cast(pl.Int32, strict=False)
                    lf = lf.filter(yearCol >= sinceYear)
                    break
        if predicate is not None:
            lf = lf.filter(predicate)
        if columns:
            available = [c for c in columns if c in schemaNames]
            if available:
                lf = lf.select(available)
        df = lf.collect(engine="streaming") if useLazy else pl.read_ipc(str(ipcPath), memory_map=True)
        return _normalizeLoadedFrame(df, category)

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
        # caller predicate (single-statement fast path 등) — row group skipping 활성화
        if predicate is not None:
            lf = lf.filter(predicate)
        # 컬럼 프로젝션
        if columns:
            available = [c for c in columns if c in schemaNames]
            if available:
                lf = lf.select(available)
        # M2: streaming engine 명시 — filter + select 만 있는 단순 chain 은 호환 + O(batch) 메모리
        df = lf.collect(engine="streaming")
    else:
        df = pl.read_parquet(str(path))
    return _normalizeLoadedFrame(df, category)


def _ensureLocalParquet(stockCode: str, path: Path, category: str, *, shouldRefresh: bool) -> None:
    """카테고리별 로컬 parquet 보장 (최초 로드 + refresh 통합 라우터).

    - ``edgar`` → SEC 벌크 (companyfacts.zip) 자동 다운로드·변환, HF 미러링 없음
    - 그 외 → HF 다운로드 + ETag 기반 증분 갱신
    """
    if category == "edgar":
        # registry dispatch (정공법 B — DIP). providers/edgar 가 EdgarBulkLoader 등록.
        from dartlab.core.loaders import getLoader

        loader = getLoader("edgar")
        if loader is None:
            raise RuntimeError("edgar LoaderProvider 미등록 — providers.edgar 모듈 로드 실패")
        loader.ensure(stockCode, path, refresh=shouldRefresh)
        return

    if not path.exists():
        _downloadFromHf(stockCode, path, category)
        return

    if shouldRefresh:
        _refreshFromHf(stockCode, path, category)


def _downloadFromHf(stockCode: str, path: Path, category: str) -> None:
    """HF 최초 다운로드 + 안내 + 예외 처리 단일 블록."""
    from dartlab.core.messaging import emit
    from dartlab.core.messaging import format as gfmt

    category = resolveDataCategory(category)
    label = DATA_RELEASES[category]["label"]
    emit("download:start", stockCode=stockCode, label=label)
    try:
        _download(stockCode, path, category)
    except (URLError, socket.timeout, OSError) as e:
        if path.exists():
            path.unlink()
        raise RuntimeError(gfmt("error:download_failed", stockCode=stockCode, label=label, error=str(e))) from e
    except ValueError:
        if path.exists():
            path.unlink()
        raise

    size = path.stat().st_size
    sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
    emit("download:done_short", sizeStr=sizeStr)


def download(stockCode: str) -> None:
    """특정 종목의 등록된 공개 parquet 데이터를 다운로드."""
    from dartlab.core.messaging import emit

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


def buildIndex(category: str = "panel") -> pl.DataFrame:
    """로컬 parquet를 projection 집계해 종목 인덱스를 생성한다.

    Returns:
        고정 스키마 DataFrame
        ``(stockCode, corpName, rows, yearFrom, yearTo, nDocs)``.
        원본에 회사명 컬럼이 없으면 ``corpName``은 null이며, 로컬 파일이 없으면
        같은 스키마의 빈 DataFrame이다.

    Raises:
        DataIndexError: parquet가 손상됐거나 projection 집계에 실패한 경우.
        KeyError: 등록되지 않은 데이터 카테고리인 경우.
    """
    category = resolveDataCategory(category)
    dataDir = _dataDir(category)
    files = sorted(dataDir.glob("*.parquet"))
    if not files:
        return dataLoaderIndex.buildDataIndex(files, category, pyodide=_IS_PYODIDE)

    from rich.progress import Progress

    from dartlab.core.logger import getConsole

    with Progress(console=getConsole()) as progress:
        task = progress.add_task("종목 스캔", total=len(files))
        return dataLoaderIndex.buildDataIndex(
            files,
            category,
            pyodide=_IS_PYODIDE,
            onProgress=lambda: progress.advance(task),
        )


def updateEdgarListedUniverse(*, force: bool = False) -> Path:
    """SEC exchange ticker 원본으로 listed universe 캐시 갱신 — fetch 는 gather 위임.

    수집 일원화: SEC ``company_tickers_exchange.json`` Extract 는 gather/edgar/universe
    가 전담. core 는 갱신 트리거 + 캐시 parquet read(``loadEdgarListedUniverse``)만.
    """
    from dartlab.core.edgarClient import updateListedUniverse

    return updateListedUniverse(force=force)


def loadEdgarListedUniverse(
    *,
    forceUpdate: bool = False,
    localOnly: bool = False,
) -> pl.DataFrame:
    """현재 상장 universe 캐시를 갱신 정책에 맞춰 로드한다.

    Args:
        forceUpdate: SEC 원본을 강제로 다시 확인한다.
        localOnly: 기존 parquet만 읽고 network와 파일 갱신을 금지한다.

    Returns:
        CIK, ticker, 회사명, 거래소를 가진 현재 상장 universe.

    Raises:
        ValueError: ``forceUpdate``와 ``localOnly``를 동시에 요청한 경우.
        FileNotFoundError: local-only cache가 존재하지 않는 경우.

    Example:
        ``snapshot = loadEdgarListedUniverse(localOnly=True)``.
    """
    if forceUpdate and localOnly:
        raise ValueError("forceUpdate와 localOnly는 함께 사용할 수 없습니다")
    path = (
        _getDataRoot() / "edgar" / "listedUniverse.parquet"
        if localOnly
        else updateEdgarListedUniverse(force=forceUpdate)
    )
    if localOnly and not path.is_file():
        raise FileNotFoundError("EDGAR listed universe local snapshot이 없습니다")
    return pl.read_parquet(path)


def loadEdgarTargetUniverse(
    tier: str = "all",
    *,
    localOnly: bool = False,
) -> pl.DataFrame:
    """tier별 EDGAR 상장사 목록 반환.

    Parameters
    ----------
    tier : str
        "all" — Nasdaq + NYSE + CBOE (OTC 제외)
        "nasdaq" — Nasdaq만
        "nyse" — NYSE만
        "sp500" — S&P 500 구성 종목 (정적 목록 교차)

    Returns
    -------
    pl.DataFrame
        cik, ticker, title, exchange 컬럼.
    """
    from dartlab.core.dataLoaderUniverse import loadEdgarTargetUniverse as _impl

    return _impl(
        loadEdgarListedUniverse(localOnly=localOnly),
        tier,
        _loadSp500Tickers(),
    )


def _loadSp500Tickers() -> list[str] | None:
    """정적 S&P 500 ticker 목록 로드 (edgarTickers.json fallback)."""
    from dartlab.core.dataLoaderUniverse import loadSp500Tickers

    return loadSp500Tickers(Path(__file__).resolve().parents[3])


def extractCorpName(df: pl.DataFrame) -> str | None:
    """DataFrame에서 기업명 추출."""
    for col in ("corp_name", "company_name"):
        if col in df.columns:
            names = [name for name in df[col].unique().to_list() if name]
            if names:
                return names[0]
    return None


def yearsDesc(df: pl.DataFrame | None, *, limit: int | None = None) -> list:
    """DataFrame 'year' 컬럼 → 내림차순 고유 연도 list (빈/결측 시 []).

    빈 회사 (loadData 빈 결과 — year 컬럼 부재) 에서 ``sorted(df["year"]...)`` 가
    ColumnNotFoundError 로 크래시하는 것을 차단하는 docs/finance accessor 공통 가드.

    Args:
        df: loadData 결과 DataFrame (None/empty 허용).
        limit: 반환 연도 최대 개수. None=전체.

    Returns:
        내림차순 정렬된 고유 연도 list. df None/empty/year 부재 시 빈 list.

    Raises:
        없음 — 빈 입력을 빈 list 로 흡수.

    Example:
        >>> yearsDesc(loadData("005930"))[:2]  # doctest: +SKIP
        [2024, 2023]
    """
    if df is None or df.is_empty() or "year" not in df.columns:
        return []
    ordered = sorted(df["year"].unique().to_list(), reverse=True)
    return ordered[:limit] if limit is not None else ordered


def _isLocalCacheExpired(path: Path, ttlHours: int) -> bool:
    if not path.exists():
        return True
    ageSeconds = time.time() - path.stat().st_mtime
    return ageSeconds > ttlHours * 3600


# ── 로드 결과 표준화 ───────────────────────────────────────────────


def _normalizeLoadedFrame(df: pl.DataFrame, category: str) -> pl.DataFrame:
    from dartlab.core.dataLoaderNormalize import normalizeLoadedFrame

    return normalizeLoadedFrame(df, category)


# ── Pyodide (emscripten) 전용 경로 ──────────────────────────────────


def _loadDataPyodide(
    stockCode: str,
    category: str,
    *,
    sinceYear: int | None = None,
    asOf: str | None = None,
    refresh: str = "auto",
    columns: list[str] | None = None,
    predicate: pl.Expr | None = None,
) -> pl.DataFrame:
    """Pyodide 환경: pre-fetched FS 파일 → pyarrow → polars.

    JS 측에서 HF parquet을 fetch → pyodide FS에 미리 기록.
    Python은 로컬 파일처럼 pyarrow로 읽는다.
    polars WASM wheel은 read_parquet 비활성이므로 pyarrow 경유.
    """
    from dartlab.core.dataLoaderPyodide import loadDataPyodide

    return loadDataPyodide(
        stockCode,
        category,
        sinceYear=sinceYear,
        asOf=asOf,
        refresh=refresh,
        columns=columns,
        predicate=predicate,
    )


def _pyodideFetchToFS(stockCode: str, category: str, dirPath: str, path: Path) -> None:
    """Pyodide: HF에서 parquet을 fetch하여 FS에 저장.

    여러 pyodide 환경(브라우저/xlwings lite/JupyterLite/Node)을 지원하기 위해
    3가지 방법을 순차 시도한다.
    """
    from dartlab.core.dataLoaderPyodide import pyodideFetchToFS

    pyodideFetchToFS(stockCode, category, dirPath, path)
