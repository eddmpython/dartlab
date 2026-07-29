"""Yahoo Finance v8 Chart API — 해외 주가 OHLCV 직접 크롤링.

FDR(FinanceDataReader)과 동일한 Yahoo v8 비공식 엔드포인트를 사용한다.
API 키 불필요. 브라우저 User-Agent 위장. 수정주가(adjclose) 지원.

사용 시 주의:
    - Yahoo v8은 **비공식 API** — 언제든 차단/변경 가능
    - rate limit 발생 시 429 응답 → http.py가 지수 백오프 재시도 (최대 3회)
    - 재시도 실패 시 **naver_global → fmp 자동 fallback**
    - 일봉 기준 최대 ~10년 데이터 수집 가능 (FDR과 동등)

fallback 체인 (해외 전 시장 공통):
    yahoo_chart(1순위) → naver_global(2순위) → fmp(3순위)

지원 시장:
    US(접미사 없음), JP(.T), HK(.HK), UK(.L), DE(.DE),
    CN_SH(.SS), CN_SZ(.SZ), IN(.NS)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from ..types import PriceSnapshot, SourceUnavailableError

log = logging.getLogger(__name__)

_BASE_URL = "https://query2.finance.yahoo.com/v8/finance/chart"

# Yahoo 거래소 접미사 매핑 (Sprint 3 PR2 — 8→15 시장 확장)
_EXCHANGE_SUFFIX: dict[str, str] = {
    "US": "",
    "JP": ".T",
    "HK": ".HK",
    "UK": ".L",
    "DE": ".DE",
    "CN_SH": ".SS",
    "CN_SZ": ".SZ",
    "IN": ".NS",
    # Sprint 3 PR2 — 7 신규 거래소 (Yahoo 일봉 커버리지 검증 완료)
    "CA": ".TO",  # Toronto Stock Exchange
    "AU": ".AX",  # Australian Securities Exchange
    "BR": ".SA",  # B3 (Brasil Bolsa Balcão)
    "ZA": ".JO",  # Johannesburg Stock Exchange
    "MX": ".MX",  # Bolsa Mexicana de Valores
    "SG": ".SI",  # Singapore Exchange
    "TH": ".BK",  # Stock Exchange of Thailand
}


def _buildSymbol(stockCode: str, market: str) -> str:
    """종목코드 + 시장 → Yahoo 심볼.

    Parameters
    ----------
    stock_code : str
        종목 심볼 (예: "AAPL", "7203").
    market : str
        시장 코드 (예: "US", "JP").

    Returns
    -------
    str
        Yahoo 심볼 (예: "AAPL", "7203.T").
    """
    suffix = _EXCHANGE_SUFFIX.get(market, "")
    return f"{stockCode}{suffix}"


async def fetchPrice(
    stockCode: str,
    client,
    *,
    market: str = "US",
    limit: int | None = None,
) -> PriceSnapshot | None:
    """Yahoo v8 Chart API → 현재가 스냅샷.

    Capabilities: US Yahoo v8 chart API → PriceSnapshot (5일 chunk → latest).
    AIContext: US gather.price primary source — chain 첫 시도.
    Guide: 무인증 v8 — rate limit 10rpm. crumb 불필요.
    When: gather("price", ticker, market="US") 진입 시 chain 우선순위 최상.
    How: query2.finance.yahoo.com/v8/chart 최근 5일 → regularMarketPrice.

    최근 5거래일 데이터를 요청하여 최신 regularMarketPrice를 추출한다.
    429 rate limit 시 http.py가 자동 재시도하며, 3회 실패 시 None 반환 →
    fallback 체인에서 naver_global이 이어받는다.

    Parameters
    ----------
    stock_code : str
        종목 심볼 (예: "AAPL", "MSFT", "7203").
        시장별 거래소 접미사는 _build_symbol()이 자동 부착.
    client
        비동기 HTTP 클라이언트 (GatherHttpClient).
    market : str
        시장 코드 ("US", "JP", "HK", "UK", "DE", "CN", "IN"). 기본 "US".
    limit : int | None
        단건 PriceSnapshot 반환 함수라 무시된다. 인터페이스 호환 목적.

    Returns
    -------
    PriceSnapshot | None
        current : float — 현재가 (해당 통화 단위)
        change : float — 전일 대비 변동
        change_pct : float — 전일 대비 변동률 (%)
        volume : int — 거래량 (주)
        currency : str — 통화 (USD/JPY/HKD 등, Yahoo 응답 기준)
        source : str — "yahoo_chart"
        API 실패 또는 데이터 없으면 None → fallback 체인 진행.

    Raises
    ------
    없음
        Yahoo v8 API 내부 예외 (SourceUnavailableError/ValueError/OSError) 는 흡수.

    Example
    -------
    >>> snap = await fetchPrice("AAPL", client, market="US")

    Requires
    --------
    네트워크 (``query2.finance.yahoo.com/v8/finance/chart``). 무인증 비공식 API.
    rate limit 시 http.py 가 지수 backoff 자동 재시도 (최대 3 회).

    See Also
    --------
    sources/price.fetch : 호출 체인 (US primary).
    naverGlobal.fetchPrice · fmp.fetchPrice : fallback source.
    fetchHistory : 일별 OHLCV 동행 endpoint.
    """
    del limit
    symbol = _buildSymbol(stockCode, market)
    url = f"{_BASE_URL}/{symbol}"
    params = {
        "interval": "1d",
        "range": "5d",
        "includeAdjustedClose": "true",
    }

    try:
        resp = await client.get(url, params=params)
        data = resp.json()
    except (SourceUnavailableError, ValueError, OSError) as exc:
        log.debug("yahoo_chart price 실패 (%s): %s", stockCode, exc)
        return None

    result = data.get("chart", {}).get("result")
    if not result:
        return None

    meta = result[0].get("meta", {})
    current = meta.get("regularMarketPrice")
    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

    if not current:
        return None

    change = round(current - prev_close, 4) if prev_close else 0.0
    change_pct = round((change / prev_close) * 100, 2) if prev_close and prev_close != 0 else 0.0
    volume = meta.get("regularMarketVolume", 0)

    return PriceSnapshot(
        current=float(current),
        change=float(change),
        change_pct=float(change_pct),
        high_52w=0.0,
        low_52w=0.0,
        volume=int(volume),
        marketCap=0.0,
        per=None,
        pbr=None,
        dividend_yield=None,
        source="yahoo_chart",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        currency=meta.get("currency", "USD"),
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
    """Yahoo v8 Chart API → OHLCV 히스토리 (수정주가).

    Capabilities: US Yahoo v8 chart 일별 OHLCV + adjclose list[dict].
    AIContext: US gather.history primary source — chain 첫 시도.
    Guide: adjclose 우선 (수정주가). 429 시 http.py 백오프 재시도.
    When: US 종목 장기 OHLCV 필요 시.
    How: query2.finance.yahoo.com/v8/chart period1/period2 → list[dict].

    일봉 기준 최대 ~10년 데이터 수집 가능. adjclose(수정주가) 우선 사용.
    429 rate limit 시 http.py가 지수 백오프 재시도 (최대 3회).
    재시도 실패 → 빈 리스트 반환 → fallback 체인에서 naver_global이 이어받음.

    Parameters
    ----------
    stock_code : str
        종목 심볼 (예: "AAPL", "7203"). 거래소 접미사 자동 부착.
    client
        비동기 HTTP 클라이언트 (GatherHttpClient).
    start : str
        시작일 ("YYYY-MM-DD"). 빈 문자열이면 최근 1년.
    end : str
        종료일 ("YYYY-MM-DD"). 빈 문자열이면 오늘.
    market : str
        시장 코드 ("US", "JP", "HK" 등). 기본 "US".
    limit : int | None
        반환 행수 상한 (가장 최근 N일). None이면 [start, end] 전체.

    Returns
    -------
    list[dict]
        날짜 오름차순 OHLCV 행 목록. 각 dict:
            date : str — 거래일 ("YYYY-MM-DD")
            open : float — 시가 (해당 통화)
            high : float — 고가
            low : float — 저가
            close : float — 종가 (수정주가, 액면분할/배당 반영)
            volume : int — 거래량 (주)
        정상 응답에 데이터가 없으면 빈 리스트.

    Notes
    -----
    Yahoo v8 API는 비공식이므로 차단 위험이 있다.
    dartlab은 yahoo_chart → naver_global → fmp 3단계 fallback으로
    어느 한 소스가 실패해도 데이터 수집을 보장한다.

    Raises
    ------
    SourceUnavailableError
        네트워크, JSON, 응답 schema 또는 OHLCV 행 파싱에 실패한 경우.

    Example
    -------
    >>> rows = await fetchHistory("AAPL", client, start="2024-01-01")

    Requires
    --------
    네트워크 + Yahoo v8 chart 가용 (비공식). 일봉 최대 ~10 년. adjclose 우선 사용.

    See Also
    --------
    sources/history.fetch : 호출 체인 (US primary).
    naverGlobal.fetchHistory · fdr.fetchHistory · fmp.fetchHistory : fallback.
    fetchPrice : 단일 시점 동행 endpoint.
    """
    from datetime import datetime as _dt

    symbol = _buildSymbol(stockCode, market)

    # Unix timestamp 변환
    if start:
        period1 = int(_dt.strptime(start, "%Y-%m-%d").timestamp())
    else:
        period1 = int((_dt.now().timestamp()) - 365 * 86400)

    if end:
        period2 = int(_dt.strptime(end, "%Y-%m-%d").timestamp())
    else:
        period2 = int(time.time())

    url = f"{_BASE_URL}/{symbol}"
    params = {
        "period1": str(period1),
        "period2": str(period2),
        "interval": "1d",
        "includeAdjustedClose": "true",
    }

    try:
        resp = await client.get(url, params=params)
        data = resp.json()
    except (SourceUnavailableError, ValueError, OSError) as exc:
        raise SourceUnavailableError(f"Yahoo history 요청 실패: {stockCode}") from exc

    if not isinstance(data, dict):
        raise SourceUnavailableError("Yahoo history 응답 schema가 객체가 아닙니다")
    chart = data.get("chart")
    if not isinstance(chart, dict):
        raise SourceUnavailableError("Yahoo history 응답에 chart 객체가 없습니다")
    providerError = chart.get("error")
    if providerError:
        raise SourceUnavailableError(f"Yahoo history API 오류: {providerError}")
    result = chart.get("result")
    if result is None or result == []:
        return []
    if not isinstance(result, list) or not isinstance(result[0], dict):
        raise SourceUnavailableError("Yahoo history result schema가 올바르지 않습니다")

    timestamps = result[0].get("timestamp", [])
    indicators = result[0].get("indicators")
    if not isinstance(timestamps, list):
        raise SourceUnavailableError("Yahoo history timestamp가 배열이 아닙니다")
    if not timestamps:
        return []
    if not isinstance(indicators, dict):
        raise SourceUnavailableError("Yahoo history indicators가 객체가 아닙니다")
    quoteData = indicators.get("quote")
    if not isinstance(quoteData, list) or not quoteData or not isinstance(quoteData[0], dict):
        raise SourceUnavailableError("Yahoo history quote schema가 올바르지 않습니다")
    quotes = quoteData[0]
    adj_close_data = indicators.get("adjclose", [])
    if not isinstance(adj_close_data, list):
        raise SourceUnavailableError("Yahoo history adjclose가 배열이 아닙니다")
    if adj_close_data and not isinstance(adj_close_data[0], dict):
        raise SourceUnavailableError("Yahoo history adjclose 행이 객체가 아닙니다")
    adj_closes = adj_close_data[0].get("adjclose", []) if adj_close_data else []

    requiredQuoteFields = ("open", "high", "low", "close", "volume")
    missingQuoteFields = [field for field in requiredQuoteFields if field not in quotes]
    if missingQuoteFields:
        missing = ", ".join(missingQuoteFields)
        raise SourceUnavailableError(f"Yahoo history quote에 필수 series가 없습니다: {missing}")
    opens = quotes["open"]
    highs = quotes["high"]
    lows = quotes["low"]
    closes = quotes["close"]
    volumes = quotes["volume"]
    series = {
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "adjclose": adj_closes,
    }
    if any(not isinstance(values, list) for values in series.values()):
        raise SourceUnavailableError("Yahoo history OHLCV series가 배열이 아닙니다")

    rows: list[dict] = []
    try:
        for i, ts in enumerate(timestamps):
            if ts is None:
                continue

            dt_str = _dt.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

            o = opens[i] if i < len(opens) and opens[i] is not None else None
            h = highs[i] if i < len(highs) and highs[i] is not None else None
            lo = lows[i] if i < len(lows) and lows[i] is not None else None
            # 수정주가 우선, 없으면 종가
            c = (
                adj_closes[i]
                if i < len(adj_closes) and adj_closes[i] is not None
                else (closes[i] if i < len(closes) else None)
            )
            v = volumes[i] if i < len(volumes) and volumes[i] is not None else 0

            if o is None or c is None:
                continue

            rows.append(
                {
                    "date": dt_str,
                    "open": round(float(o), 4),
                    "high": round(float(h), 4) if h else round(float(o), 4),
                    "low": round(float(lo), 4) if lo else round(float(o), 4),
                    "close": round(float(c), 4),
                    "volume": int(v),
                }
            )
    except (IndexError, TypeError, ValueError, OSError, OverflowError) as exc:
        raise SourceUnavailableError("Yahoo history OHLCV 행을 해석할 수 없습니다") from exc

    if limit is not None and limit > 0:
        return rows[-limit:]
    return rows
