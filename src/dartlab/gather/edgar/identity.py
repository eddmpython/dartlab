"""EDGAR issuer identity 해석."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.core.dataLoader import loadEdgarListedUniverse
from dartlab.core.edgarClient import DEFAULT_SEC_URL, EdgarClient

_TICKERS_URL = f"{DEFAULT_SEC_URL}/files/company_tickers.json"


def _tickersPath() -> Path:
    from dartlab.core.dataLoader import _getDataRoot

    return _getDataRoot() / "edgar" / "tickers.parquet"


def loadTickers(
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
) -> pl.DataFrame:
    """SEC company_tickers 를 다운로드하고 로컬 캐시된 DataFrame 으로 반환.

    Args:
        client: EdgarClient 인스턴스.
        refresh: 캐시 무시 + 강제 재다운로드.

    Returns:
        ``ticker/cik/title`` 컬럼 + listed/exchange/is_otc 옵션 DataFrame.

    Raises:
        EdgarApiError: SEC API 호출 실패.
        OSError: 캐시 파일 쓰기 실패.

    Example:
        >>> loadTickers().head()

    SeeAlso:
        - ``loadTickers`` / ``resolveIssuer`` / ``searchIssuers`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - SEC company_tickers.json 다운로드 + 정규화 + 검색 (ticker / CIK / 회사명 lookup).

    Guide:
        - "ticker / CIK 변환" → 본 모듈.

    AIContext:
        internal identity — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 일 1 회 이상 SEC tickers fetch 시도 → 24 h 캐시 활용.
            - User-Agent 미설정 → 403.
        OutputSchema:
            - pl.DataFrame [cik, ticker, title, exchange] 또는 dict.
        Prerequisites:
            - 인터넷 (cache 부재 시) + SEC EDGAR public API.
        Freshness:
            - SEC company_tickers 갱신 (일 단위).
        Dataflow:
            - SEC company_tickers → loadTickers parquet → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) identity.
    """
    path = _tickersPath()
    if path.exists() and not refresh:
        return pl.read_parquet(path)
    if sys.platform == "emscripten" and not refresh:
        try:
            from dartlab.core.dataLoader import loadData

            return loadData("tickers", "edgarTickers")
        except Exception:
            pass

    api = client or EdgarClient()
    payload = api.getJson(_TICKERS_URL)
    rows: list[dict[str, Any]] = []
    for record in payload.values():
        rows.append(
            {
                "ticker": str(record.get("ticker") or "").upper().strip(),
                "cik": str(record.get("cik_str") or "").zfill(10),
                "title": str(record.get("title") or "").strip(),
            }
        )

    df = pl.DataFrame(rows).filter(pl.col("ticker") != "")

    try:
        listed = loadEdgarListedUniverse()
        if not listed.is_empty():
            listedSlim = listed.select(
                [col for col in ("ticker", "exchange", "is_exchange_listed", "is_otc") if col in listed.columns]
            )
            df = df.join(listedSlim, on="ticker", how="left")
    except (FileNotFoundError, OSError, RuntimeError):
        pass

    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    return df


def resolveIssuer(
    query: str,
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """티커 또는 CIK 를 기업 identity dict 로 해석.

    Args:
        query: ticker 또는 CIK 문자열.
        client: EdgarClient 인스턴스.
        refresh: 캐시 무시.

    Returns:
        ``{ticker, cik, title, exchange, is_exchange_listed, is_otc}`` dict.

    Raises:
        ValueError: query 빈 문자열 또는 매칭 없음.

    Example:
        >>> resolveIssuer("AAPL")

    SeeAlso:
        - ``loadTickers`` / ``resolveIssuer`` / ``searchIssuers`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - SEC company_tickers.json 다운로드 + 정규화 + 검색 (ticker / CIK / 회사명 lookup).

    Guide:
        - "ticker / CIK 변환" → 본 모듈.

    AIContext:
        internal identity — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 일 1 회 이상 SEC tickers fetch 시도 → 24 h 캐시 활용.
            - User-Agent 미설정 → 403.
        OutputSchema:
            - pl.DataFrame [cik, ticker, title, exchange] 또는 dict.
        Prerequisites:
            - 인터넷 (cache 부재 시) + SEC EDGAR public API.
        Freshness:
            - SEC company_tickers 갱신 (일 단위).
        Dataflow:
            - SEC company_tickers → loadTickers parquet → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) identity.
    """
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


def searchIssuers(
    query: str,
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
    limit: int | None = None,
) -> pl.DataFrame:
    """티커/CIK/회사명으로 SEC 등록 기업을 검색하여 DataFrame 반환.

    Args:
        query: 검색어.
        client: EdgarClient (재사용 시).
        refresh: True 면 ticker 캐시 재다운로드.
        limit: 최대 행 수. None 이면 무제한.

    Returns:
        매칭 DataFrame.

    Raises:
        없음.

    Example:
        >>> searchIssuers("apple", limit=10)

    SeeAlso:
        - ``loadTickers`` / ``resolveIssuer`` / ``searchIssuers`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - SEC company_tickers.json 다운로드 + 정규화 + 검색 (ticker / CIK / 회사명 lookup).

    Guide:
        - "ticker / CIK 변환" → 본 모듈.

    AIContext:
        internal identity — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 일 1 회 이상 SEC tickers fetch 시도 → 24 h 캐시 활용.
            - User-Agent 미설정 → 403.
        OutputSchema:
            - pl.DataFrame [cik, ticker, title, exchange] 또는 dict.
        Prerequisites:
            - 인터넷 (cache 부재 시) + SEC EDGAR public API.
        Freshness:
            - SEC company_tickers 갱신 (일 단위).
        Dataflow:
            - SEC company_tickers → loadTickers parquet → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) identity.
    """
    if not query or not str(query).strip():
        return pl.DataFrame(schema={"ticker": pl.Utf8, "cik": pl.Utf8, "title": pl.Utf8})

    df = loadTickers(client, refresh=refresh)
    text = str(query).strip()
    upper = text.upper()

    if text.isdigit():
        result = df.filter(pl.col("cik").str.contains(text))
    else:
        result = df.filter(
            pl.col("ticker").str.contains(upper, literal=True)
            | pl.col("title").str.to_uppercase().str.contains(upper, literal=True)
        ).sort(["ticker", "cik"])

    if limit is not None:
        result = result.head(limit)
    return result


def iterIssuers(
    query: str,
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
    limit: int | None = None,
):
    """``searchIssuers`` 의 iterator pair (룰 10).

    Args:
        query: 검색어.
        client: EdgarClient (재사용 시).
        refresh: True 면 ticker 캐시 재다운로드.
        limit: 최대 행 수. None 이면 무제한.

    Yields:
        issuer row dict.

    Raises:
        없음.

    Example:
        >>> for row in iterIssuers("apple", limit=10):
        ...     print(row["ticker"])

    SeeAlso:
        - ``loadTickers`` / ``resolveIssuer`` / ``searchIssuers`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - SEC company_tickers.json 다운로드 + 정규화 + 검색 (ticker / CIK / 회사명 lookup).

    Guide:
        - "ticker / CIK 변환" → 본 모듈.

    AIContext:
        internal identity — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - 일 1 회 이상 SEC tickers fetch 시도 → 24 h 캐시 활용.
            - User-Agent 미설정 → 403.
        OutputSchema:
            - pl.DataFrame [cik, ticker, title, exchange] 또는 dict.
        Prerequisites:
            - 인터넷 (cache 부재 시) + SEC EDGAR public API.
        Freshness:
            - SEC company_tickers 갱신 (일 단위).
        Dataflow:
            - SEC company_tickers → loadTickers parquet → 본 함수.
        TargetMarkets:
            - US (SEC EDGAR) identity.
    """
    df = searchIssuers(query, client, refresh=refresh, limit=limit)
    yield from df.iter_rows(named=True)
