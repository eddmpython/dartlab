"""네이버 글로벌 주식 — US/글로벌 주가 fallback (Yahoo 다음 2순위).

네이버 웹 스크래핑 (api.stock.naver.com). 공식 API 아님.
Reuters Code 체계: NASDAQ → .O, NYSE → 접미사 없음.

사용 시 주의:
    - **호출 간 2~4초 강제 딜레이** — 서버 보호 (asyncio.Lock으로 경쟁 방지)
    - Reuters Code 캐싱: 종목당 첫 호출만 5개 suffix 시도, 이후 캐시 히트
    - dayCandle 110개 하드 제한 → **endTime 페이징**으로 최대 1100일 수집
    - Yahoo v8 실패(429 rate limit) 시 이 모듈이 자동으로 이어받음

fallback 위치:
    yahoo_chart(1순위) → **naver_global(2순위)** → fmp(3순위)

데이터 범위:
    - dayCandle: 최대 ~1100일 (페이징 10회 × 110개)
    - weekCandle: ~2년
    - monthCandle: ~9년
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone

from ..types import PriceSnapshot, SourceUnavailableError

log = logging.getLogger(__name__)

_API_BASE = "https://api.stock.naver.com"

# Reuters Code 접미사 후보 (순서대로 시도)
_SUFFIXES = ["", ".O", ".N", ".K", ".A"]

# 서버 보호: 호출 간 2~4초 강제 딜레이 (모듈 전역)
_MIN_DELAY = 2.0
_MAX_DELAY = 4.0
_lastCallTime: float = 0.0
_throttleLock = asyncio.Lock()

# Reuters Code 캐시 — 종목당 5번 suffix 시도를 1번으로 줄임
_REUTERS_CACHE: dict[str, str | None] = {}


async def _throttle() -> None:
    """마지막 호출 이후 2~4초 대기 (Lock으로 경쟁 상태 방지).

    Returns
    -------
    None
        대기 완료 후 반환. _lastCallTime 갱신.
    """
    global _lastCallTime
    async with _throttleLock:
        now = time.monotonic()
        elapsed = now - _lastCallTime
        delay = random.uniform(_MIN_DELAY, _MAX_DELAY)
        if elapsed < delay:
            wait = delay - elapsed
            await asyncio.sleep(wait)
        _lastCallTime = time.monotonic()


def _cleanNumber(val) -> float | None:
    """문자열/숫자 → float 변환. 콤마 제거 포함.

    Parameters
    ----------
    val
        변환할 값. str, int, float 또는 None.

    Returns
    -------
    float | None
        변환된 숫자. None이거나 변환 불가 시 None.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(",", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parsePriceNumber(value: object, field: str) -> float | None:
    """Naver global price 숫자의 정상 결측과 schema 손상을 구분한다."""
    if isinstance(value, bool):
        raise SourceUnavailableError(f"Naver global price {field} 값이 bool입니다")
    token = str(value).replace(",", "").strip() if value is not None else ""
    if token in ("", "N/A", "-"):
        return None
    parsed = _cleanNumber(value)
    if parsed is None:
        raise SourceUnavailableError(f"Naver global price {field} 값을 해석할 수 없습니다: {value!r}")
    return parsed


async def _resolveReutersCode(ticker: str, client, *, raiseOnFailure: bool = False) -> str | None:
    """ticker → 네이버 Reuters Code (캐시 우선).

    Parameters
    ----------
    ticker : str
        종목 심볼 (예: "AAPL", "MSFT").
    client
        비동기 HTTP 클라이언트.

    Returns
    -------
    str | None
        매핑된 Reuters Code (예: "AAPL.O"). 실패 시 None.
    """
    if ticker in _REUTERS_CACHE:
        return _REUTERS_CACHE[ticker]

    failures: list[Exception] = []
    for suffix in _SUFFIXES:
        await _throttle()
        code = f"{ticker}{suffix}"
        url = f"{_API_BASE}/stock/{code}/basic"
        try:
            resp = await client.get(url, headers={"Accept": "application/json"})
            data = resp.json()
            if not isinstance(data, dict):
                raise SourceUnavailableError("Naver global Reuters 응답 schema가 객체가 아닙니다")
            if data.get("stockName") and not data.get("code", "").startswith("Stock"):
                _REUTERS_CACHE[ticker] = code
                return code
        except (SourceUnavailableError, ValueError, KeyError) as exc:
            failures.append(exc)
            continue

    if failures and raiseOnFailure:
        raise SourceUnavailableError(f"Naver global Reuters code 확인 실패: {ticker}") from failures[-1]
    if failures:
        return None
    _REUTERS_CACHE[ticker] = None
    return None


async def fetchPrice(
    stockCode: str,
    client,
    *,
    market: str = "US",
    limit: int | None = None,
) -> PriceSnapshot | None:
    """네이버 글로벌 → 현재가 스냅샷.

    Capabilities: US/Global Naver api.stock.naver.com → PriceSnapshot.
    AIContext: US gather.price fallback chain — Yahoo 첫 시도, naverGlobal 보조.
    Guide: 한국어 라벨로 표시되는 글로벌 종목 (한국 사용자 친화).
    When: Yahoo 실패 시 fallback / Naver 사용자 표시 형식 선호 시.
    How: api.stock.naver.com integration JSON → PriceSnapshot.

    Parameters
    ----------
    stock_code : str
        종목 심볼 (예: ``"AAPL"``, ``"MSFT"``).
    client
        비동기 HTTP 클라이언트.
    market : str
        시장 코드. 기본값 ``"US"``.
    limit : int | None
        단건 PriceSnapshot 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    PriceSnapshot | None
        current : float — 현재가 (USD)
        change : float — 전일 대비 변동 (USD)
        change_pct : float — 전일 대비 변동률 (%)
        volume : int — 누적 거래량 (주)
        market_cap : float — 시가총액 (USD)
        source : str — ``"naver_global"``
        유효한 응답에서 Reuters 매핑 또는 현재가가 없으면 None.

    Raises
    ------
    ValueError
        종목코드가 비어 있는 경우.
    SourceUnavailableError
        Reuters 확인, 요청, JSON, schema 또는 숫자 파싱 실패.

    Example
    -------
    >>> snap = await fetchPrice("AAPL", client, market="US")

    Requires
    --------
    네트워크 (``api.stock.naver.com``) + Reuters Code 매핑 가능. 호출 간 2~4 초 throttle
    (asyncio.Lock 으로 경쟁 방지). 비공식 API — 차단 가능성 있음.

    See Also
    --------
    sources/price.fetch : 호출 체인 (Yahoo → naverGlobal → fmp).
    yahooChart.fetchPrice : primary US source.
    fmp.fetchPrice : 다음 fallback.
    """
    del limit
    if not stockCode or not stockCode.strip():
        raise ValueError("Naver global price 종목코드가 비어 있습니다")
    code = await _resolveReutersCode(stockCode, client, raiseOnFailure=True)
    if not code:
        return None

    await _throttle()
    url = f"{_API_BASE}/stock/{code}/basic"
    try:
        resp = await client.get(url, headers={"Accept": "application/json"})
        data = resp.json()
    except Exception as exc:
        raise SourceUnavailableError(f"Naver global price 요청 실패: {stockCode}") from exc
    if not isinstance(data, dict):
        raise SourceUnavailableError("Naver global price 응답 schema가 객체가 아닙니다")

    current = _parsePriceNumber(data.get("closePrice"), "closePrice")
    if not current:
        return None

    change = _parsePriceNumber(data.get("compareToPreviousClosePrice"), "compareToPreviousClosePrice") or 0.0
    change_pct = _parsePriceNumber(data.get("fluctuationsRatio"), "fluctuationsRatio") or 0.0
    volume = int(_parsePriceNumber(data.get("accumulatedTradingVolume"), "accumulatedTradingVolume") or 0)

    # 시가총액 (억 달러 → 달러)
    marketCap = 0.0
    market_cap_raw = data.get("marketValue")
    if market_cap_raw:
        mc = _parsePriceNumber(market_cap_raw, "marketValue")
        if mc:
            marketCap = mc  # 네이버 API가 원단위로 줄 수 있음

    # 52주 고저, PER 등은 별도 API 필요 — 기본값
    exchange_name = ""
    ex_type = data.get("stockExchangeType", {})
    if not isinstance(ex_type, dict):
        raise SourceUnavailableError("Naver global price stockExchangeType이 객체가 아닙니다")
    exchange_name = str(ex_type.get("name") or "")

    return PriceSnapshot(
        current=current,
        change=change,
        change_pct=change_pct,
        high_52w=0.0,
        low_52w=0.0,
        volume=volume,
        marketCap=marketCap,
        per=None,
        pbr=None,
        dividend_yield=None,
        source="naver_global",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        currency="USD",
        exchange=exchange_name,
        market=market,
    )


async def fetchHistory(
    stockCode: str,
    client,
    *,
    start: str = "",
    end: str = "",
    market: str = "US",
    limit: int | None = None,
    **kwargs,
) -> list[dict]:
    """네이버 글로벌 → OHLCV 히스토리.

    Capabilities: US/Global Naver chart API → 일/주/월 OHLCV list[dict].
    AIContext: US gather.history fallback (FMP 보조 + 한국 사용자 표시).
    Guide: chart API 110개 하드 제한 — 기간 따라 dayCandle/weekCandle/monthCandle 자동.
    When: US 종목의 한국어 라벨 OHLCV 필요 시.
    How: api.stock.naver.com chart → periodType 자동 선택 → list[dict].

    네이버 글로벌 chart API는 periodType별 110개 하드 제한.
    요청 기간에 따라 자동 선택:
      - 1년 이내: dayCandle (약 110 거래일 = 6개월)
      - 1~2년: weekCandle (약 110주 = 2년)
      - 2년 이상: monthCandle (약 110개월 = 9년)
    start 미지정이면 dayCandle (하위호환).

    Parameters
    ----------
    stock_code : str
        종목 심볼 (예: ``"AAPL"``, ``"MSFT"``).
    client
        비동기 HTTP 클라이언트.
    start : str
        시작일 (YYYY-MM-DD). 빈 문자열이면 필터 없음.
    end : str
        종료일 (YYYY-MM-DD). 빈 문자열이면 필터 없음.
    market : str
        시장 코드. 기본값 ``"US"``.
    limit : int | None
        반환 행수 상한 (가장 최근 N건). None이면 [start, end] 전체.

    Returns
    -------
    list[dict]
        OHLCV 행 목록 (날짜 오름차순, 중복 제거). 각 dict 키:

        - date : str — 거래일 (YYYY-MM-DD)
        - open : float — 시가 (USD)
        - high : float — 고가 (USD)
        - low : float — 저가 (USD)
        - close : float — 종가 (USD)
        - volume : int — 거래량 (주)

        정상 응답에서 Reuters code 또는 가격 데이터가 없으면 빈 리스트.

    Raises
    ------
    SourceUnavailableError
        Reuters code 확인, 네트워크, 응답 형식 또는 행 파싱에 실패한 경우.

    Example
    -------
    >>> rows = await fetchHistory("AAPL", client, start="2024-01-01")

    Requires
    --------
    네트워크 + Reuters Code 매핑 + 호출 간 2~4 초 throttle. dayCandle 110 일 하드 제한 —
    endTime 페이징 (최대 10 회 = 1100 일).

    See Also
    --------
    sources/history.fetch : 호출 체인 (Yahoo primary → naverGlobal fallback).
    yahooChart.fetchHistory · fdr.fetchHistory · fmp.fetchHistory : 동행 source.
    """
    code = await _resolveReutersCode(stockCode, client, raiseOnFailure=True)
    if not code:
        return []

    # 요청 기간 길이로 periodType 자동 선택
    period_type = "dayCandle"
    if start:
        from datetime import date
        from datetime import datetime as _dt

        start_dt = _dt.strptime(start, "%Y-%m-%d").date()
        end_dt = _dt.strptime(end, "%Y-%m-%d").date() if end else date.today()
        span_days = (end_dt - start_dt).days
        if span_days > 730:
            period_type = "monthCandle"
        elif span_days > 365:
            period_type = "weekCandle"

    # 페이징: dayCandle 110개 제한 → endTime으로 이전 데이터 반복 요청
    all_rows: list[dict] = []
    end_time = ""  # 빈 문자열 = 최신부터
    max_pages = 10 if period_type == "dayCandle" else 3

    for _page in range(max_pages):
        await _throttle()
        url = f"{_API_BASE}/chart/foreign/item/{code}?periodType={period_type}&count=500"
        if end_time:
            url += f"&endTime={end_time}"
        try:
            resp = await client.get(url, headers={"Accept": "application/json"})
            data = resp.json()
        except (SourceUnavailableError, ValueError) as exc:
            raise SourceUnavailableError(f"Naver global history 요청 실패: {stockCode}") from exc

        if not isinstance(data, dict):
            raise SourceUnavailableError("Naver global history 응답 schema가 객체가 아닙니다")
        if "priceInfos" not in data:
            raise SourceUnavailableError("Naver global history 응답에 priceInfos가 없습니다")
        infos = data["priceInfos"]
        if not isinstance(infos, list):
            raise SourceUnavailableError("Naver global history priceInfos가 배열이 아닙니다")
        if not infos:
            break

        page_rows: list[dict] = []
        for p in infos:
            if not isinstance(p, dict):
                raise SourceUnavailableError("Naver global history 행이 객체가 아닙니다")
            rawDate = str(p.get("localDate") or "")
            if len(rawDate) != 8 or not rawDate.isdigit():
                raise SourceUnavailableError(f"Naver global history 거래일이 올바르지 않습니다: {rawDate!r}")
            requiredFields = ("openPrice", "highPrice", "lowPrice", "closePrice", "accumulatedTradingVolume")
            if any(field not in p or p[field] is None for field in requiredFields):
                raise SourceUnavailableError(f"Naver global history {rawDate} 행에 OHLCV가 누락되었습니다")
            dateStr = f"{rawDate[:4]}-{rawDate[4:6]}-{rawDate[6:8]}"
            numericValues = {field: _cleanNumber(p[field]) for field in requiredFields}
            if any(value is None for value in numericValues.values()):
                raise SourceUnavailableError(f"Naver global history {rawDate} 행의 OHLCV를 해석할 수 없습니다")
            page_rows.append(
                {
                    "date": dateStr,
                    "open": numericValues["openPrice"],
                    "high": numericValues["highPrice"],
                    "low": numericValues["lowPrice"],
                    "close": numericValues["closePrice"],
                    "volume": int(numericValues["accumulatedTradingVolume"] or 0),
                }
            )

        all_rows.extend(page_rows)

        # start 날짜 이전 데이터까지 도달했으면 중단
        if start and page_rows and page_rows[0]["date"] <= start:
            break

        # 다음 페이지: 현재 페이지의 가장 오래된 날짜를 endTime으로
        oldest = infos[0].get("localDate", "")
        if not oldest or oldest == end_time:
            break  # 더 이상 이전 데이터 없음
        end_time = oldest

    # 중복 제거 + 정렬
    seen: set[str] = set()
    unique_rows: list[dict] = []
    for r in all_rows:
        if r["date"] not in seen:
            seen.add(r["date"])
            unique_rows.append(r)
    unique_rows.sort(key=lambda r: r["date"])

    # 날짜 범위 필터
    if start:
        unique_rows = [r for r in unique_rows if r["date"] >= start]
    if end:
        unique_rows = [r for r in unique_rows if r["date"] <= end]

    if limit is not None and limit > 0:
        return unique_rows[-limit:]
    return unique_rows
