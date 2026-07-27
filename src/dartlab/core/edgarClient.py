"""EDGAR/SEC fetch seam — DI Protocol (정공법 B).

gather 가 모든 EDGAR network fetch 를 전담(ETL Extract). providers 의 build/read
코드가 client 가 필요하면 본 core seam 으로 접근 — providers↛gather 단방향 유지.
``gather/edgar/client.py`` 의 ``EdgarFetchProvider`` 구현이 import 시점에 register.

``EdgarApiError`` + ``DEFAULT_*`` URL/User-Agent 는 build·fetch 양쪽이 쓰는 공유
식별자/상수라 core 에 정의 (gather raise/fetch, providers except/URL 조립). 본 모듈의
``EdgarClient`` 는 wrapper class — 소비자 호출부(``EdgarClient(...)``)와
``EdgarClient.getJson`` monkeypatch 표면을 유지하면서 실제 HTTP 구현은 gather provider 에 위임.

CredentialProvider/LoaderProvider/DartFetchProvider 와 동일 패턴.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import polars as pl

from dartlab.core.pluginDiscovery import discoverOnce

DEFAULT_USER_AGENT = "DartLab eddmpython@gmail.com"
DEFAULT_BASE_URL = "https://data.sec.gov"
DEFAULT_SEC_URL = "https://www.sec.gov"

# 정기공시 form 종류 — fetch(filter)·build·read 공유 상수.
SUPPORTED_REGULAR_FORMS = ("10-K", "10-Q", "20-F", "40-F")

# companyfacts normalize(gather facts.companyFactsToRows) → parquet(providers saver) 공유 schema.
EDGAR_COMPANYFACTS_SCHEMA = {
    "cik": pl.Utf8,
    "entityName": pl.Utf8,
    "namespace": pl.Utf8,
    "tag": pl.Utf8,
    "label": pl.Utf8,
    "unit": pl.Utf8,
    "val": pl.Float64,
    "fy": pl.Int32,
    "fp": pl.Utf8,
    "form": pl.Utf8,
    "filed": pl.Date,
    "frame": pl.Utf8,
    "start": pl.Date,
    "end": pl.Date,
    "accn": pl.Utf8,
}


class EdgarApiError(RuntimeError):
    """SEC API 호출 오류 (공유 infra 예외 — gather raise, providers except)."""


@runtime_checkable
class EdgarFetchProvider(Protocol):
    """EDGAR fetch+normalize 추상화 — providers build/read 가 gather/edgar 출력을 얻는 seam.

    EDGAR 는 SEC API fetch 와 JSON→DataFrame normalize 가 밀결합(companyFactsToRows 등)이라
    gather/edgar 가 Extract+normalize 를 전담한다. providers 의 parquet-build·accessor 가
    normalize 결과를 쓰려면 ``call(module, func, ...)`` 로 gather/edgar 서브모듈에 위임.
    """

    def makeClient(self, **kwargs: Any) -> Any:
        """SEC HTTP 클라이언트 인스턴스 생성 (userAgent/email/minInterval/timeout/maxRetries)."""
        ...

    def call(self, module: str, func: str, *args: Any, **kwargs: Any) -> Any:
        """gather/edgar.<module>.<func> 위임 호출 (fetch+normalize 출력)."""
        ...


_PROVIDER: EdgarFetchProvider | None = None

_KNOWN_PROVIDER_MODULES: tuple[str, ...] = ("dartlab.gather.edgar.client",)


def _discover() -> None:
    """알려진 EdgarFetchProvider 모듈을 한 번만 lazy import . register 트리거.

    한 번만 도는 규칙은 `core.pluginDiscovery` 가 갖는다. 예전에는 이 열세 줄이
    core 안에 열한 벌 복사돼 있었다.
    """
    discoverOnce(__name__, _KNOWN_PROVIDER_MODULES)


def registerEdgarFetchProvider(provider: EdgarFetchProvider) -> None:
    """EdgarFetchProvider 등록 — gather/edgar/client 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getEdgarFetchProvider() -> EdgarFetchProvider | None:
    """현재 등록된 EdgarFetchProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER


def _provider() -> EdgarFetchProvider:
    provider = getEdgarFetchProvider()
    if provider is None:
        raise RuntimeError("EdgarFetchProvider 미등록 — dartlab.gather.edgar.client import 실패 (gather 미설치/오류)")
    return provider


class EdgarClient:
    """SEC EDGAR 클라이언트 wrapper — gather EdgarFetchProvider 위임.

    Requires: ``dartlab.gather.edgar.client`` (EdgarFetchProvider 등록). SEC public API
        는 키 불요, User-Agent 필수(_buildUserAgent 자동).
    Raises: RuntimeError — EdgarFetchProvider 미등록.
    Example:
        >>> from dartlab.core.edgarClient import EdgarClient  # doctest: +SKIP
        >>> client = EdgarClient()
    """

    def __init__(
        self,
        *,
        userAgent: str | None = None,
        email: str | None = None,
        minInterval: float = 0.2,
        timeout: float = 30.0,
        maxRetries: int = 3,
    ) -> None:
        self._client = _provider().makeClient(
            userAgent=userAgent,
            email=email,
            minInterval=minInterval,
            timeout=timeout,
            maxRetries=maxRetries,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def getJson(self, url: str) -> dict[str, Any]:
        """SEC JSON endpoint 호출 — 실제 구현은 등록된 gather client 에 위임."""
        return self._client.getJson(url)


# ── gather/edgar fetch+normalize 위임 delegate (providers 소비자 호환 seam) ──
# 소비자는 import 경로만 본 모듈로 교체. 실제 구현은 gather/edgar 서브모듈.


def _call(module: str, func: str, *args: Any, **kwargs: Any) -> Any:
    return _provider().call(module, func, *args, **kwargs)


def getSubmissionsJson(*args: Any, **kwargs: Any) -> Any:
    """SEC submissions JSON fetch — gather/edgar 위임. Requires: gather.edgar. Raises: EdgarApiError. Example: >>> getSubmissionsJson("0000320193")  # doctest: +SKIP"""
    return _call("submissions", "getSubmissionsJson", *args, **kwargs)


def mergeSubmissionFilings(*args: Any, **kwargs: Any) -> Any:
    """submissions filing 배열 병합(paginated) — gather/edgar 위임. Requires: gather.edgar. Raises: EdgarApiError. Example: >>> mergeSubmissionFilings(sub)  # doctest: +SKIP"""
    return _call("submissions", "mergeSubmissionFilings", *args, **kwargs)


def findRegularFilings(*args: Any, **kwargs: Any) -> Any:
    """정기공시 filing 필터/정규화 — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> findRegularFilings(sub)  # doctest: +SKIP"""
    return _call("submissions", "findRegularFilings", *args, **kwargs)


def filingsFrame(*args: Any, **kwargs: Any) -> Any:
    """filing list → DataFrame — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> filingsFrame(sub)  # doctest: +SKIP"""
    return _call("submissions", "filingsFrame", *args, **kwargs)


def getCompanyFactsJson(*args: Any, **kwargs: Any) -> Any:
    """SEC companyfacts JSON fetch — gather/edgar 위임. Requires: gather.edgar. Raises: EdgarApiError. Example: >>> getCompanyFactsJson("0000320193")  # doctest: +SKIP"""
    return _call("facts", "getCompanyFactsJson", *args, **kwargs)


def getCompanyConceptJson(*args: Any, **kwargs: Any) -> Any:
    """SEC companyconcept JSON fetch — gather/edgar 위임. Requires: gather.edgar. Raises: EdgarApiError. Example: >>> getCompanyConceptJson(...)  # doctest: +SKIP"""
    return _call("facts", "getCompanyConceptJson", *args, **kwargs)


def getFrameJson(*args: Any, **kwargs: Any) -> Any:
    """SEC frames JSON fetch — gather/edgar 위임. Requires: gather.edgar. Raises: EdgarApiError. Example: >>> getFrameJson(...)  # doctest: +SKIP"""
    return _call("facts", "getFrameJson", *args, **kwargs)


def companyFactsToRows(*args: Any, **kwargs: Any) -> Any:
    """companyfacts JSON → flat DataFrame normalize — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> companyFactsToRows(payload)  # doctest: +SKIP"""
    return _call("facts", "companyFactsToRows", *args, **kwargs)


def loadTickers(*args: Any, **kwargs: Any) -> Any:
    """SEC company_tickers fetch+캐시 — gather/edgar 위임. Requires: gather.edgar. Raises: EdgarApiError. Example: >>> loadTickers()  # doctest: +SKIP"""
    return _call("identity", "loadTickers", *args, **kwargs)


def resolveIssuer(*args: Any, **kwargs: Any) -> Any:
    """ticker/CIK → issuer dict. ``loadTickers`` seam 을 사용해 monkeypatch 가능한 표면 유지."""
    query = args[0] if args else kwargs.pop("query")
    client = args[1] if len(args) > 1 else kwargs.pop("client", None)
    refresh = bool(kwargs.pop("refresh", False))
    if kwargs:
        raise TypeError(f"unexpected keyword arguments: {', '.join(kwargs)}")
    if not query or not str(query).strip():
        raise ValueError("tickerOrCik가 비어 있음")

    text = str(query).strip()
    normalized = text.upper()
    cikQuery = text.zfill(10) if text.isdigit() else ""

    df = loadTickers(client, refresh=refresh)
    row = None
    if cikQuery:
        match = df.filter(pl.col("cik") == cikQuery)
        if match.height > 0:
            row = match.row(0, named=True)
    else:
        match = df.filter(pl.col("ticker") == normalized)
        if match.height > 0:
            row = match.row(0, named=True)
    if row is None:
        raise ValueError(f"{query}에 해당하는 CIK를 찾을 수 없음")
    return {
        "ticker": str(row.get("ticker") or normalized),
        "cik": str(row.get("cik") or "").zfill(10),
        "title": str(row.get("title") or normalized),
        "exchange": row.get("exchange"),
        "is_exchange_listed": row.get("is_exchange_listed"),
        "is_otc": row.get("is_otc"),
    }


def searchIssuers(*args: Any, **kwargs: Any) -> Any:
    """issuer 검색 DataFrame — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> searchIssuers("apple")  # doctest: +SKIP"""
    return _call("identity", "searchIssuers", *args, **kwargs)


def iterIssuers(*args: Any, **kwargs: Any) -> Any:
    """issuer 검색 iterator — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> list(iterIssuers("apple"))  # doctest: +SKIP"""
    return _call("identity", "iterIssuers", *args, **kwargs)


def fetchEdgarDocs(*args: Any, **kwargs: Any) -> Any:
    """EDGAR 공시 HTML fetch+파싱 → docs parquet — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: ValueError/httpx. Example: >>> fetchEdgarDocs("AAPL", path)  # doctest: +SKIP"""
    return _call("docs.fetch", "fetchEdgarDocs", *args, **kwargs)


def htmlToText(*args: Any, **kwargs: Any) -> Any:
    """filing HTML → text normalize — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> htmlToText(html)  # doctest: +SKIP"""
    return _call("docs.fetchHtmlParse", "_htmlToText", *args, **kwargs)


def saveDocs(*args: Any, **kwargs: Any) -> Any:
    """EDGAR docs fetch+검증+저장 — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx/OSError. Example: >>> saveDocs("AAPL")  # doctest: +SKIP"""
    return _call("saver", "saveDocs", *args, **kwargs)


def saveFinance(*args: Any, **kwargs: Any) -> Any:
    """EDGAR companyfacts fetch+normalize+저장 — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx/OSError. Example: >>> saveFinance("0000320193")  # doctest: +SKIP"""
    return _call("saver", "saveFinance", *args, **kwargs)


def downloadCompanyfactsBulk(*args: Any, **kwargs: Any) -> Any:
    """SEC companyfacts.zip bulk download — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx/OSError. Example: >>> downloadCompanyfactsBulk()  # doctest: +SKIP"""
    return _call("bulk", "downloadCompanyfactsBulk", *args, **kwargs)


def extractCompanyfactsZip(*args: Any, **kwargs: Any) -> Any:
    """companyfacts.zip stream → (cik, json) — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> extractCompanyfactsZip(path)  # doctest: +SKIP"""
    return _call("bulk", "extractCompanyfactsZip", *args, **kwargs)


def ensureFinanceParquet(*args: Any, **kwargs: Any) -> Any:
    """EDGAR finance parquet 보장(bulk) — gather/edgar 위임. Requires: gather.edgar. Raises: OSError. Example: >>> ensureFinanceParquet("0000320193")  # doctest: +SKIP"""
    return _call("bulk", "ensureFinanceParquet", *args, **kwargs)


def convertBulkToParquets(*args: Any, **kwargs: Any) -> Any:
    """companyfacts.zip → per-CIK parquet 변환(bulk) — gather/edgar 위임. Requires: gather.edgar. Raises: OSError. Example: >>> convertBulkToParquets()  # doctest: +SKIP"""
    return _call("bulk", "convertBulkToParquets", *args, **kwargs)


def downloadQuarterlyDataset(*args: Any, **kwargs: Any) -> Any:
    """SEC 분기 financial-statement-data-sets zip download — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx/OSError. Example: >>> downloadQuarterlyDataset(2024, 3)  # doctest: +SKIP"""
    return _call("datasetBulk", "downloadQuarterlyDataset", *args, **kwargs)


def discoverLatestQuarter(*args: Any, **kwargs: Any) -> Any:
    """SEC 공개 최신 분기 HEAD 탐색 — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: 없음. Example: >>> discoverLatestQuarter()  # doctest: +SKIP"""
    return _call("datasetBulk", "discoverLatestQuarter", *args, **kwargs)


def updateListedUniverse(*args: Any, **kwargs: Any) -> Any:
    """SEC listed universe(company_tickers_exchange) fetch+캐시 갱신 — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: URLError. Example: >>> updateListedUniverse(force=True)  # doctest: +SKIP"""
    return _call("universe", "updateListedUniverse", *args, **kwargs)


def openEdgar(*args: Any, **kwargs: Any) -> Any:
    """OpenEdgar 파사드 인스턴스 생성 — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> openEdgar()("AAPL").filings()  # doctest: +SKIP"""
    return _call("edgar", "OpenEdgar", *args, **kwargs)


def downloadFilingSource(*args: Any, **kwargs: Any) -> Any:
    """단일 공시 원문 source 다운로드 — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx. Example: >>> downloadFilingSource(url)  # doctest: +SKIP"""
    return _call("docs.fetch", "_downloadFilingSource", *args, **kwargs)


def findFilings(*args: Any, **kwargs: Any) -> Any:
    """submissions → 정기공시 filing 추출 — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> findFilings(sub, sinceYear=2024)  # doctest: +SKIP"""
    return _call("docs.fetch", "_findFilings", *args, **kwargs)


def getSubmissions(*args: Any, **kwargs: Any) -> Any:
    """submissions JSON fetch(docs flow) — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx. Example: >>> getSubmissions(cik)  # doctest: +SKIP"""
    return _call("docs.fetch", "_getSubmissions", *args, **kwargs)


def resolveTickerMeta(*args: Any, **kwargs: Any) -> Any:
    """ticker → cik/이름 메타 resolve(docs flow) — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> resolveTickerMeta("AAPL")  # doctest: +SKIP"""
    return _call("docs.fetch", "_resolveTickerMeta", *args, **kwargs)


def collectFilingRows(*args: Any, **kwargs: Any) -> Any:
    """공시 목록 → docs row 수집 — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx. Example: >>> collectFilingRows(filings)  # doctest: +SKIP"""
    return _call("docs.fetch", "_collectFilingRows", *args, **kwargs)


def makeProgress(*args: Any, **kwargs: Any) -> Any:
    """docs fetch 진행 콜백 생성 — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> makeProgress(total)  # doctest: +SKIP"""
    return _call("docs.fetch", "_makeProgress", *args, **kwargs)


def filingTimeoutSeconds(*args: Any, **kwargs: Any) -> Any:
    """공시 fetch 타임아웃(초) 상수 — gather/edgar 위임. Requires: gather.edgar. Raises: 없음. Example: >>> filingTimeoutSeconds()  # doctest: +SKIP"""
    return _call("docs.fetch", "filingTimeoutSeconds", *args, **kwargs)


def batchCollectEdgar(*args: Any, **kwargs: Any) -> Any:
    """EDGAR 티커 배치 수집(finance/docs) — gather/edgar 위임. Requires: gather.edgar + 인터넷. Raises: httpx. Example: >>> batchCollectEdgar(["AAPL"], categories=["finance"])  # doctest: +SKIP"""
    return _call("batch", "batchCollectEdgar", *args, **kwargs)
