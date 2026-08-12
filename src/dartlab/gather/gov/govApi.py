"""공공데이터포털 금융위원회_주식시세정보 raw fetch.

두 진입:
    fetchGovStock — 종목 하나 전체이력 (likeSrtnCd, 차트 SSOT).
    fetchGovBydd  — 하루치 전종목 (basDt, 일별 sync SSOT).
둘 다 raw gov 컬럼 DataFrame 반환. `normalizeGovFrame` 가 회사 schema 로 정규화
(회사별 parquet 표준 컬럼).

라이선스: 공공누리/KOGL — 비상업 + 출처표시 재배포 가능.
인증키(`DATA_GO_KR_KEY`, 디코딩 키)는 환경변수 자동 read 없음 — 명시 전달만.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
import polars as pl

log = logging.getLogger(__name__)

_GOV_ENDPOINT = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
_GOV_INDEX_ENDPOINT = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"
_GOV_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_GOV_BACKOFF_SECONDS = (2, 5, 10, 20)

# gov 응답 컬럼 → 회사 표준 schema.
GOV_TO_STD = {
    "basDt": "date",
    "srtnCd": "stockCode",
    "itmsNm": "name",
    "mrktCtg": "market",
    "mkp": "open",
    "hipr": "high",
    "lopr": "low",
    "clpr": "close",
    "vs": "priceChange",
    "fltRt": "fluctuationRate",
    "trqu": "volume",
    "trPrc": "tradedValue",
    "mrktTotAmt": "marketCap",
    "lstgStCnt": "listedShares",
}

# 응답이 전부 string → 수치 컬럼 명시 cast (SSOT).
_GOV_NUM = ("clpr", "vs", "fltRt", "mkp", "hipr", "lopr", "trqu", "trPrc", "lstgStCnt", "mrktTotAmt")
_NUM_STD = (
    "open",
    "high",
    "low",
    "close",
    "priceChange",
    "fluctuationRate",
    "volume",
    "tradedValue",
    "marketCap",
    "listedShares",
)

# gov getStockPriceInfo 응답 → KRX 전종목 raw schema (date 샤드 = 랜딩 전종목 스캔이 직독).
# ISU_CD = srtnCd 6자리 단축코드 (krx/prices·hfBulk·랜딩 duckdb·company/recent 전부 6자리 공통 포맷);
# SECT_TP_NM 은 gov 미제공 → 빈 컬럼 유지(15-col parity).
GOV_TO_KRXRAW = {
    "basDt": "BAS_DD",
    "itmsNm": "ISU_NM",
    "mrktCtg": "MKT_NM",
    "mkp": "TDD_OPNPRC",
    "hipr": "TDD_HGPRC",
    "lopr": "TDD_LWPRC",
    "clpr": "TDD_CLSPRC",
    "vs": "CMPPREVDD_PRC",
    "fltRt": "FLUC_RT",
    "trqu": "ACC_TRDVOL",
    "trPrc": "ACC_TRDVAL",
    "mrktTotAmt": "MKTCAP",
    "lstgStCnt": "LIST_SHRS",
}
# KRX raw dtype 정합 — 원화 가격·거래량·시총·주식수 = Int64, 등락률만 Float64.
_KRXRAW_INT = (
    "TDD_OPNPRC",
    "TDD_HGPRC",
    "TDD_LWPRC",
    "TDD_CLSPRC",
    "CMPPREVDD_PRC",
    "ACC_TRDVOL",
    "ACC_TRDVAL",
    "MKTCAP",
    "LIST_SHRS",
)
_KRXRAW_FLOAT = ("FLUC_RT",)
_KRXRAW_COLS = (
    "BAS_DD",
    "ISU_CD",
    "ISU_NM",
    "MKT_NM",
    "SECT_TP_NM",
    "TDD_CLSPRC",
    "CMPPREVDD_PRC",
    "FLUC_RT",
    "TDD_OPNPRC",
    "TDD_HGPRC",
    "TDD_LWPRC",
    "ACC_TRDVOL",
    "ACC_TRDVAL",
    "MKTCAP",
    "LIST_SHRS",
)

# gov getStockMarketIndex 응답 → KRX 지수 raw schema (13-col, krxIndex Data Contract).
# idxCsf 는 rename 하지 않고 MARKET_GROUP / IDX_CLSS 파생에만 쓴다.
GOV_IDX_TO_KRX = {
    "basDt": "BAS_DD",
    "idxNm": "IDX_NM",
    "clpr": "CLSPRC_IDX",
    "mkp": "OPNPRC_IDX",
    "hipr": "HGPRC_IDX",
    "lopr": "LWPRC_IDX",
    "vs": "CMPPREVDD_IDX",
    "fltRt": "FLUC_RT",
    "trqu": "ACC_TRDVOL",
    "trPrc": "ACC_TRDVAL",
    "lstgMrktTotAmt": "MKTCAP",
}
_GOV_IDX_NUM = ("clpr", "vs", "fltRt", "mkp", "hipr", "lopr", "trqu", "trPrc", "lstgMrktTotAmt", "epyItmsCnt")
_IDX_FLOAT = ("CLSPRC_IDX", "OPNPRC_IDX", "HGPRC_IDX", "LWPRC_IDX", "CMPPREVDD_IDX", "FLUC_RT")
_IDX_INT = ("ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP")
_KRXIDX_COLS = (
    "BAS_DD",
    "MARKET_GROUP",
    "IDX_CLSS",
    "IDX_NM",
    "CLSPRC_IDX",
    "OPNPRC_IDX",
    "HGPRC_IDX",
    "LWPRC_IDX",
    "CMPPREVDD_IDX",
    "FLUC_RT",
    "ACC_TRDVOL",
    "ACC_TRDVAL",
    "MKTCAP",
)


def _marketGroupFromIdxCsf(idxCsf: str | None) -> str:
    """gov idxCsf(지수 시리즈 분류) → KRX MARKET_GROUP 토큰.

    idxCsf 4종 = {KOSPI시리즈, KOSDAQ시리즈, KRX시리즈, 테마지수}. 테마지수는
    전용 KRX 엔드포인트가 없어 KRX 시장군에 귀속(기존 gov/indices raw parity). 미지의
    신규 idxCsf 도 'KRX' 로 fallback(행 유실 방지).
    """
    s = str(idxCsf or "")
    if s.startswith("KOSPI"):
        return "KOSPI"
    if s.startswith("KOSDAQ"):
        return "KOSDAQ"
    return "KRX"


def _parseItems(data: dict) -> list[dict]:
    """gov JSON 응답 → item dict 리스트 (단일 item 도 리스트화, 빈 응답 [])."""
    body = (data or {}).get("response", {}).get("body", {}) or {}
    items = (body.get("items") or {}).get("item")
    if not items:
        return []
    return items if isinstance(items, list) else [items]


def _totalCount(data: dict) -> int:
    body = (data or {}).get("response", {}).get("body", {}) or {}
    raw = body.get("totalCount")
    if raw is None:
        raise ValueError("gov 응답에 totalCount가 없습니다")
    try:
        total = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"gov 응답 totalCount가 정수가 아닙니다: {raw!r}") from exc
    if total < 0:
        raise ValueError(f"gov 응답 totalCount가 음수입니다: {total}")
    return total


def _validatePaging(numOfRows: int, maxPages: int) -> None:
    if isinstance(numOfRows, bool) or not isinstance(numOfRows, int) or numOfRows <= 0:
        raise ValueError("numOfRows는 양의 정수여야 합니다")
    if isinstance(maxPages, bool) or not isinstance(maxPages, int) or maxPages <= 0:
        raise ValueError("maxPages는 양의 정수여야 합니다")


def _assertPageComplete(*, totalCount: int, fetchedPages: int, numOfRows: int, maxPages: int) -> None:
    if fetchedPages * numOfRows < totalCount:
        raise RuntimeError(
            "gov 페이지 상한으로 응답이 잘렸습니다: "
            f"totalCount={totalCount}, fetchedPages={fetchedPages}, "
            f"numOfRows={numOfRows}, maxPages={maxPages}"
        )


def _rawFrame(rows: list[dict]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame()
    df = pl.DataFrame(rows)
    casts = [pl.col(c).cast(pl.Float64, strict=False) for c in _GOV_NUM if c in df.columns]
    return df.with_columns(casts) if casts else df


def _retryAttempts() -> int:
    try:
        return max(1, int(os.environ.get("DARTLAB_GOV_RETRY_ATTEMPTS", "4")))
    except ValueError:
        return 4


def _retryWait(exc: Exception, attempt: int) -> float:
    response = getattr(exc, "response", None)
    retryAfter = response.headers.get("Retry-After") if response is not None else None
    wait: float | None = None
    if retryAfter:
        try:
            wait = max(0.0, float(retryAfter))
        except ValueError as exc:
            log.warning("gov Retry-After 초 파싱 실패: %s", exc)
            try:
                parsed = parsedate_to_datetime(retryAfter)
                wait = max(0.0, (parsed - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError) as dateExc:
                log.warning("gov Retry-After 날짜 파싱 실패: %s", dateExc)
                wait = None
    if wait is None:
        wait = float(_GOV_BACKOFF_SECONDS[min(attempt, len(_GOV_BACKOFF_SECONDS) - 1)])
    try:
        maximum = max(0.0, float(os.environ.get("DARTLAB_GOV_RETRY_MAX_SINGLE_WAIT_SECONDS", "60")))
    except ValueError as exc:
        log.warning("DARTLAB_GOV_RETRY_MAX_SINGLE_WAIT_SECONDS 파싱 실패: %s", exc)
        maximum = 60.0
    return min(wait, maximum)


def _isRetryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _GOV_RETRYABLE_STATUS
    return False


def _get(params: dict, *, apiKey: str, client: httpx.Client | None, endpoint: str = _GOV_ENDPOINT) -> dict:
    """단일 gov 호출을 transient 재시도 후 JSON으로 반환한다."""
    query = {"serviceKey": apiKey, "resultType": "json", **params}
    own = client is None
    cl = client or httpx.Client(timeout=30.0)
    try:
        attempts = _retryAttempts()
        for attempt in range(attempts):
            try:
                resp = cl.get(endpoint, params=query)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                if not _isRetryable(exc) or attempt == attempts - 1:
                    raise
                wait = _retryWait(exc, attempt)
                status = getattr(getattr(exc, "response", None), "status_code", None) or type(exc).__name__
                log.warning("gov API %s, %.1f초 후 재시도 (%d/%d)", status, wait, attempt + 1, attempts - 1)
                time.sleep(wait)
    finally:
        if own:
            cl.close()
    raise RuntimeError("unreachable")


def fetchGovStock(
    code: str,
    *,
    apiKey: str,
    numOfRows: int = 4000,
    maxPages: int = 8,
    client: httpx.Client | None = None,
) -> pl.DataFrame:
    """종목 하나 전체이력 raw fetch (likeSrtnCd, 페이지 루프).

    Capabilities: 한 종목 전체 일별 OHLCV+시총+거래대금 raw (gov 원본 컬럼, 2020~).
    AIContext: 차트 회사별 parquet 의 source — likeSrtnCd 는 LIKE 라 srtnCd 정확매칭만 채택.
    Guide: 프론트 /__gov 가 종목 클릭 시 호출 → company/{code} 캐시 채움(사용자 직접 호출 X).
    When: 온디맨드 캐시 미스 시 (gov 라이브 단일 종목 fetch).
    How: likeSrtnCd 페이지 루프 → srtnCd 정확매칭 dedup → _rawFrame 수치 cast.
    Requires: 인터넷 + 공공데이터포털 디코딩 키 (sto 권한).
    SeeAlso: normalizeGovFrame · buildGovData.produceStock (캐시 채움 caller).

    Args:
        code: 종목코드 6자리.
        apiKey: 공공데이터포털 디코딩 인증키 (명시 필수).
        numOfRows: 페이지당 행수. maxPages: 최대 페이지 (이력 상한 가드).
        client: 재사용 httpx.Client (None 이면 자동 생성/종료).

    Returns:
        pl.DataFrame: gov raw 컬럼 (basDt/srtnCd/clpr/mkp/... 수치 cast). 빈 = 데이터 없음.

    Raises:
        ValueError: apiKey 빈 문자열.
        httpx.HTTPStatusError: gov 응답 4xx/5xx.

    Example:
        >>> df = fetchGovStock("005930", apiKey=key)  # 1578행(2020~)
    """
    if not apiKey:
        raise ValueError("apiKey 필수 — 공공데이터포털 호출에는 디코딩 인증키가 필요합니다")
    _validatePaging(numOfRows, maxPages)
    code = str(code).strip()
    rows: list[dict] = []
    seen: set[str] = set()
    totalCount = 0
    fetchedPages = 0
    for page in range(1, maxPages + 1):
        data = _get({"numOfRows": numOfRows, "pageNo": page, "likeSrtnCd": code}, apiKey=apiKey, client=client)
        items = _parseItems(data)
        totalCount = _totalCount(data)
        if not items:
            break
        fetchedPages = page
        for r in items:
            if str(r.get("srtnCd")) != code:
                continue
            key = str(r.get("basDt"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)
        if page * numOfRows >= totalCount:
            break
    _assertPageComplete(
        totalCount=totalCount,
        fetchedPages=fetchedPages,
        numOfRows=numOfRows,
        maxPages=maxPages,
    )
    return _rawFrame(rows)


def fetchGovBydd(
    basDt: str,
    *,
    apiKey: str,
    numOfRows: int = 4000,
    maxPages: int = 4,
    client: httpx.Client | None = None,
) -> pl.DataFrame:
    """하루치 전종목 raw fetch (basDt, 페이지 루프).

    Capabilities: 그날 전 시장(~2877종목) OHLCV+시총 raw — 일별 sync 의 증분 source.
    AIContext: buildGovData 가 매일 어제 basDt 1콜로 전종목 증분 수집.
    Guide: 운영자 cron(buildGovData --daily)만 호출 → date/{year} 전종목 횡단 갱신.
    When: 매일 장마감 후 어제 basDt 1콜 (엔진 scan/quant 전시장 데이터).
    How: basDt 페이지 루프 → 전종목 누적 → _rawFrame 수치 cast.
    Requires: 인터넷 + 공공데이터포털 디코딩 키 (sto 권한).
    SeeAlso: normalizeGovToKrxRaw (date 샤드 schema) · buildGovData.daily.

    Args:
        basDt: 기준일자 YYYYMMDD.
        apiKey: 공공데이터포털 디코딩 인증키 (명시 필수).
        numOfRows / maxPages / client: fetchGovStock 와 동일 규약.

    Returns:
        pl.DataFrame: 그날 전종목 gov raw 컬럼. 휴장일/미확정일은 빈 DataFrame.

    Raises:
        ValueError: apiKey 빈 문자열.
        httpx.HTTPStatusError: gov 응답 4xx/5xx.

    Example:
        >>> df = fetchGovBydd("20260609", apiKey=key)  # ~2877행
    """
    if not apiKey:
        raise ValueError("apiKey 필수 — 공공데이터포털 호출에는 디코딩 인증키가 필요합니다")
    _validatePaging(numOfRows, maxPages)
    basDt = str(basDt).replace("-", "").strip()
    rows: list[dict] = []
    totalCount = 0
    fetchedPages = 0
    for page in range(1, maxPages + 1):
        data = _get({"numOfRows": numOfRows, "pageNo": page, "basDt": basDt}, apiKey=apiKey, client=client)
        items = _parseItems(data)
        totalCount = _totalCount(data)
        if not items:
            break
        fetchedPages = page
        rows.extend(items)
        if page * numOfRows >= totalCount:
            break
    _assertPageComplete(
        totalCount=totalCount,
        fetchedPages=fetchedPages,
        numOfRows=numOfRows,
        maxPages=maxPages,
    )
    return _rawFrame(rows)


def normalizeGovFrame(df: pl.DataFrame) -> pl.DataFrame:
    """raw gov DataFrame → 회사 표준 schema.

    Capabilities: gov 원본 컬럼을 date/stockCode/name/market/OHLC/.../marketCap 으로 rename+cast.
    AIContext: 회사별 parquet (gov/prices/company/{code}.parquet) 의 최종 schema 보장.
    Guide: produceStock 이 fetchGovStock 결과를 이 함수로 정규화 후 company 캐시에 저장.
    When: 종목별 캐시 채움 직전 (gov raw → 회사 표준 schema).
    How: GOV_TO_STD rename → 수치 Float64 cast → 6자리 stockCode 필터 → 정렬.
    Requires: polars (네트워크 불필요 — 순수 변환).
    SeeAlso: fetchGovStock (입력) · normalizeGovToKrxRaw (전종목 date 샤드용 변형).

    Args:
        df: fetchGovStock/fetchGovBydd 의 raw gov DataFrame.

    Returns:
        pl.DataFrame: date(str)·stockCode(str)·name·market·open·high·low·close·priceChange·
            fluctuationRate·volume·tradedValue·marketCap·listedShares. (stockCode+date 정렬)

    Raises:
        없음 — 빈/컬럼 누락 입력은 빈/부분 DataFrame 으로 그대로 반환 (예외 미발생).

    Example:
        >>> std = normalizeGovFrame(fetchGovStock("005930", apiKey=key))
    """
    if df.is_empty():
        return df
    rename = {k: v for k, v in GOV_TO_STD.items() if k in df.columns}
    out = df.rename(rename)
    casts = [pl.col(c).cast(pl.Float64, strict=False) for c in _NUM_STD if c in out.columns]
    if "date" in out.columns:
        casts.append(pl.col("date").cast(pl.Utf8))
    if "stockCode" in out.columns:
        casts.append(pl.col("stockCode").cast(pl.Utf8))
    out = out.with_columns(casts)
    keep = [v for v in GOV_TO_STD.values() if v in out.columns]
    out = out.select(keep)
    if "stockCode" in out.columns and "date" in out.columns:
        out = out.filter(pl.col("stockCode").str.len_chars() == 6).sort(["stockCode", "date"])
    return out


def normalizeGovToKrxRaw(df: pl.DataFrame) -> pl.DataFrame:
    """raw gov(전종목 bydd) DataFrame → KRX 전종목 raw schema (date 샤드용).

    Capabilities: gov 원본 컬럼을 BAS_DD/ISU_CD/TDD_* 등 15-col KRX raw 로 rename+cast.
    AIContext: gov/prices/date/{year}.parquet(랜딩 전종목 스캔 직독)의 schema 보장 —
        ISU_CD 는 srtnCd 6자리 단축코드(예: "005930"). hfBulk.loadFiltered(ISU_CD==code)·
        랜딩 duckdb(WHERE ISU_CD='005930')·company/recent 전부 6자리로 필터하므로 접두 없이
        krx/prices·전 역사와 동질 (접두 'A' 부여 시 최신 구간이 전 소비자에서 누락됨).
    Guide: daily 가 fetchGovBydd 결과를 이 함수로 KRX raw 화 후 date 샤드에 upsert.
    When: 전종목 date 샤드 갱신 직전 (gov bydd → KRX 15-col raw).
    How: GOV_TO_KRXRAW rename → ISU_CD=srtnCd 6자리 zfill → Int/Float cast → SECT_TP_NM 빈 컬럼 → 정렬.
    Requires: polars (네트워크 불필요 — 순수 변환).
    SeeAlso: fetchGovBydd (입력) · buildGovData._appendYearlyRaw (date 샤드 caller).

    Args:
        df: fetchGovBydd 의 raw gov DataFrame (basDt/srtnCd/clpr/...).

    Returns:
        pl.DataFrame: 15-col KRX raw (BAS_DD·ISU_CD=srtnCd 6자리·ISU_NM·MKT_NM·SECT_TP_NM(빈)·
            TDD_*·CMPPREVDD_PRC·FLUC_RT·ACC_TRDVOL·ACC_TRDVAL·MKTCAP·LIST_SHRS). BAS_DD+ISU_CD 정렬.

    Raises:
        없음 — 빈/컬럼 누락 입력은 빈 DataFrame 으로 반환.

    Example:
        >>> raw = normalizeGovToKrxRaw(fetchGovBydd("20260609", apiKey=key))  # ~2877행
    """
    if df.is_empty() or "srtnCd" not in df.columns:
        return pl.DataFrame()
    rename = {k: v for k, v in GOV_TO_KRXRAW.items() if k in df.columns}
    out = df.rename(rename).with_columns(
        pl.col("srtnCd").cast(pl.Utf8).str.zfill(6).alias("ISU_CD"),
        *[pl.col(c).cast(pl.Int64, strict=False) for c in _KRXRAW_INT if c in rename.values()],
        *[pl.col(c).cast(pl.Float64, strict=False) for c in _KRXRAW_FLOAT if c in rename.values()],
    )
    if "BAS_DD" in out.columns:
        out = out.with_columns(pl.col("BAS_DD").cast(pl.Utf8))
    if "SECT_TP_NM" not in out.columns:
        out = out.with_columns(pl.lit(None, dtype=pl.Utf8).alias("SECT_TP_NM"))
    out = out.filter(pl.col("ISU_CD").str.len_chars() == 6)  # 단축코드 6자리 (krx·gov·전 소비자 공통)
    keep = [c for c in _KRXRAW_COLS if c in out.columns]
    return out.select(keep).sort(["BAS_DD", "ISU_CD"])


def fetchGovIndex(
    basDt: str,
    *,
    apiKey: str,
    numOfRows: int = 1000,
    maxPages: int = 2,
    client: httpx.Client | None = None,
) -> pl.DataFrame:
    """하루치 전 지수 raw fetch (getStockMarketIndex, basDt, 페이지 루프).

    Capabilities: 그날 전 시장군 지수(~163종) OHLC+등락+거래대금+시총 raw (gov 원본 컬럼).
    AIContext: buildGovData 가 매일 어제 basDt 1콜로 전지수 증분 수집(주가 fetchGovBydd 미러).
    Guide: 운영자 cron(buildGovData --daily-index)만 호출 → date/{year} 전지수 횡단 갱신.
    When: 매일 장마감 후 어제 basDt 1콜 (benchmarkMap/macro 벤치마크).
    How: getStockMarketIndex basDt 페이지 루프 → 누적 → _GOV_IDX_NUM Float64 cast.
    Requires: 인터넷 + 공공데이터포털 디코딩 키 (지수시세 권한 신청 필요).
    SeeAlso: normalizeGovIndexFrame (KRX 지수 schema) · buildGovData.dailyIndex.

    Args:
        basDt: 기준일자 YYYYMMDD.
        apiKey: 공공데이터포털 디코딩 인증키 (명시 필수).
        numOfRows / maxPages / client: fetchGovBydd 와 동일 규약 (지수는 163종 → 1페이지 충분).

    Returns:
        pl.DataFrame: 그날 전지수 gov raw 컬럼 (basDt/idxNm/idxCsf/clpr/...). 휴장일은 빈 DataFrame.

    Raises:
        ValueError: apiKey 빈 문자열.
        httpx.HTTPStatusError: gov 응답 4xx/5xx.

    Example:
        >>> df = fetchGovIndex("20260609", apiKey=key)  # ~163행
    """
    if not apiKey:
        raise ValueError("apiKey 필수 — 공공데이터포털 호출에는 디코딩 인증키가 필요합니다")
    _validatePaging(numOfRows, maxPages)
    basDt = str(basDt).replace("-", "").strip()
    rows: list[dict] = []
    totalCount = 0
    fetchedPages = 0
    for page in range(1, maxPages + 1):
        data = _get(
            {"numOfRows": numOfRows, "pageNo": page, "basDt": basDt},
            apiKey=apiKey,
            client=client,
            endpoint=_GOV_INDEX_ENDPOINT,
        )
        items = _parseItems(data)
        totalCount = _totalCount(data)
        if not items:
            break
        fetchedPages = page
        rows.extend(items)
        if page * numOfRows >= totalCount:
            break
    _assertPageComplete(
        totalCount=totalCount,
        fetchedPages=fetchedPages,
        numOfRows=numOfRows,
        maxPages=maxPages,
    )
    if not rows:
        return pl.DataFrame()
    df = pl.DataFrame(rows)
    casts = [pl.col(c).cast(pl.Float64, strict=False) for c in _GOV_IDX_NUM if c in df.columns]
    return df.with_columns(casts) if casts else df


def normalizeGovIndexFrame(df: pl.DataFrame) -> pl.DataFrame:
    """raw gov 지수 DataFrame → KRX 지수 raw schema (13-col, krxIndex Data Contract).

    Capabilities: gov 지수 컬럼을 BAS_DD/MARKET_GROUP/IDX_CLSS/IDX_NM/CLSPRC_IDX/... 로 변환.
    AIContext: gov/indices/date·index 파생의 단일 SSOT — MARKET_GROUP·IDX_CLSS 는 idxCsf 접두 파생.
    Guide: dailyIndex 가 fetchGovIndex 결과를 이 함수로 KRX 지수 schema 화 후 date 샤드에 upsert.
    When: 전지수 date 샤드 갱신 직전 (gov 지수 → KRX 13-col).
    How: GOV_IDX_TO_KRX rename → _marketGroupFromIdxCsf 로 MARKET_GROUP/IDX_CLSS 파생 → cast → 정렬.
    Requires: polars (네트워크 불필요 — 순수 변환).
    SeeAlso: fetchGovIndex (입력) · buildGovData._appendYearlyIndex (date 샤드 caller).

    Args:
        df: fetchGovIndex 의 raw gov 지수 DataFrame.

    Returns:
        pl.DataFrame: 13-col KRX 지수 raw (BAS_DD·MARKET_GROUP·IDX_CLSS·IDX_NM·CLSPRC_IDX·
            OPNPRC_IDX·HGPRC_IDX·LWPRC_IDX·CMPPREVDD_IDX·FLUC_RT·ACC_TRDVOL·ACC_TRDVAL·MKTCAP).
            BAS_DD+MARKET_GROUP+IDX_CLSS+IDX_NM 정렬.

    Raises:
        없음 — 빈/컬럼 누락 입력은 빈 DataFrame 으로 반환.

    Example:
        >>> idx = normalizeGovIndexFrame(fetchGovIndex("20260609", apiKey=key))
    """
    if df.is_empty() or "idxCsf" not in df.columns:
        return pl.DataFrame()
    market = pl.col("idxCsf").map_elements(_marketGroupFromIdxCsf, return_dtype=pl.Utf8)
    rename = {k: v for k, v in GOV_IDX_TO_KRX.items() if k in df.columns}
    out = df.rename(rename).with_columns(
        market.alias("MARKET_GROUP"),
        market.alias("IDX_CLSS"),
        *[pl.col(c).cast(pl.Float64, strict=False) for c in _IDX_FLOAT if c in rename.values()],
        *[pl.col(c).cast(pl.Int64, strict=False) for c in _IDX_INT if c in rename.values()],
    )
    if "BAS_DD" in out.columns:
        out = out.with_columns(pl.col("BAS_DD").cast(pl.Utf8))
    keep = [c for c in _KRXIDX_COLS if c in out.columns]
    return out.select(keep).sort(["BAS_DD", "MARKET_GROUP", "IDX_CLSS", "IDX_NM"])
