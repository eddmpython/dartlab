"""Yahoo Finance v8 REST 직접 호출 — crumb/cookie 불필요.

chart API(``query1.finance.yahoo.com/v8/finance/chart/``)를 사용하여
yfinance 의존 없이 전세계 60+ 거래소 현재가 + 히스토리를 수집한다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..market_config import resolve_ticker
from ..types import GatherError, PriceSnapshot

log = logging.getLogger(__name__)

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"


def fetch_price(stock_code: str, client, *, market: str = "US") -> PriceSnapshot | None:
    """현재가 스냅샷 — Yahoo v8 chart API (range=1d)."""
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    try:
        resp = client.get(
            _CHART_URL.format(ticker=ticker),
            params={"range": "1d", "interval": "1d", "includePrePost": "false"},
        )
    except GatherError:
        return None

    try:
        data = resp.json()
    except ValueError:
        return None

    result = data.get("chart", {}).get("result")
    if not result:
        return None

    quote = result[0]
    meta = quote.get("meta", {})
    indicators = quote.get("indicators", {}).get("quote", [{}])[0]

    current = meta.get("regularMarketPrice", 0.0)
    prev_close = meta.get("chartPreviousClose", 0.0) or meta.get("previousClose", 0.0)

    if not current:
        return None

    change = current - prev_close if prev_close else 0.0
    change_pct = (change / prev_close * 100) if prev_close else 0.0

    # 52주 고/저 — indicators에서 추출
    highs = indicators.get("high", [])
    lows = indicators.get("low", [])
    volumes = indicators.get("volume", [])

    return PriceSnapshot(
        current=current,
        change=change,
        change_pct=change_pct,
        high_52w=meta.get("fiftyTwoWeekHigh", 0.0),
        low_52w=meta.get("fiftyTwoWeekLow", 0.0),
        volume=volumes[-1] if volumes and volumes[-1] else 0,
        market_cap=0.0,
        per=None,
        pbr=None,
        dividend_yield=None,
        source="yahoo_direct",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        currency=meta.get("currency", "USD"),
        exchange=meta.get("exchangeName", ""),
        market=market,
    )


def fetch_history(
    stock_code: str,
    client,
    *,
    start: str,
    end: str,
    market: str = "US",
) -> list[dict]:
    """히스토리 OHLCV — Yahoo v8 chart API (period1/period2).

    Args:
        start: "2024-01-01" 형식
        end: "2024-12-31" 형식

    Returns:
        [{"date": "2024-01-02", "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]
    """
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    period1 = int(datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    period2 = int(datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())

    try:
        resp = client.get(
            _CHART_URL.format(ticker=ticker),
            params={
                "period1": str(period1),
                "period2": str(period2),
                "interval": "1d",
                "includePrePost": "false",
            },
        )
    except GatherError:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

    result = data.get("chart", {}).get("result")
    if not result:
        return []

    quote = result[0]
    timestamps = quote.get("timestamp", [])
    indicators = quote.get("indicators", {}).get("quote", [{}])[0]

    opens = indicators.get("open", [])
    highs = indicators.get("high", [])
    lows = indicators.get("low", [])
    closes = indicators.get("close", [])
    volumes = indicators.get("volume", [])

    rows = []
    for i, ts in enumerate(timestamps):
        if i >= len(closes) or closes[i] is None:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        rows.append({
            "date": dt.strftime("%Y-%m-%d"),
            "open": opens[i] if i < len(opens) and opens[i] is not None else 0.0,
            "high": highs[i] if i < len(highs) and highs[i] is not None else 0.0,
            "low": lows[i] if i < len(lows) and lows[i] is not None else 0.0,
            "close": closes[i],
            "volume": volumes[i] if i < len(volumes) and volumes[i] is not None else 0,
        })

    return rows
