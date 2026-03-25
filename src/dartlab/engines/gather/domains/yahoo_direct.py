"""Yahoo Finance v8 REST 직접 호출 — crumb/cookie 불필요.

chart API(``query1.finance.yahoo.com/v8/finance/chart/``)를 사용하여
yfinance 의존 없이 전세계 60+ 거래소 현재가 + 히스토리를 수집한다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..market_config import resolve_ticker
from ..types import ConsensusData, GatherError, PriceSnapshot, RevenueConsensus

log = logging.getLogger(__name__)

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"


async def fetch_price(stock_code: str, client, *, market: str = "US") -> PriceSnapshot | None:
    """현재가 스냅샷 — Yahoo v8 chart API (range=1d)."""
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    try:
        resp = await client.get(
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


async def fetch_history(
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
        resp = await client.get(
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
        rows.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "open": opens[i] if i < len(opens) and opens[i] is not None else 0.0,
                "high": highs[i] if i < len(highs) and highs[i] is not None else 0.0,
                "low": lows[i] if i < len(lows) and lows[i] is not None else 0.0,
                "close": closes[i],
                "volume": volumes[i] if i < len(volumes) and volumes[i] is not None else 0,
            }
        )

    return rows


# ══════════════════════════════════════
# Yahoo quoteSummary — Revenue Consensus
# ══════════════════════════════════════

_SUMMARY_URL = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"


async def fetch_consensus(
    stock_code: str,
    client,
    *,
    market: str = "US",
) -> ConsensusData | None:
    """Yahoo quoteSummary → 컨센서스 (목표가, 애널리스트 수, 추천 점수)."""
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    try:
        resp = await client.get(
            _SUMMARY_URL.format(ticker=ticker),
            params={"modules": "financialData"},
        )
    except GatherError:
        return None

    try:
        data = resp.json()
    except ValueError:
        return None

    quote_summary = data.get("quoteSummary", {}).get("result")
    if not quote_summary:
        return None

    fin = quote_summary[0].get("financialData", {})
    target = fin.get("targetMeanPrice", {}).get("raw", 0)
    if not target or target <= 0:
        return None

    analyst_count = fin.get("numberOfAnalystOpinions", {}).get("raw", 0)
    recomm = fin.get("recommendationMean", {}).get("raw", 0)
    # Yahoo recommendationMean: 1=strong buy, 5=sell → buy_ratio 변환
    buy_ratio = max(0.0, (5.0 - recomm) / 4.0) if recomm > 0 else 0.0
    high = fin.get("targetHighPrice", {}).get("raw", 0)
    low = fin.get("targetLowPrice", {}).get("raw", 0)

    return ConsensusData(
        target_price=target,
        analyst_count=analyst_count,
        buy_ratio=round(buy_ratio, 2),
        high=high or target,
        low=low or target,
        source="yahoo_direct",
    )


async def fetch_revenue_consensus(
    stock_code: str,
    client,
    *,
    market: str = "US",
) -> list[RevenueConsensus]:
    """Yahoo quoteSummary에서 매출/이익 컨센서스 추출.

    modules: earningsTrend (연도별 revenue estimate), financialData (실적).

    Returns:
        RevenueConsensus 리스트 (actual + estimate).
    """
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    try:
        resp = await client.get(
            _SUMMARY_URL.format(ticker=ticker),
            params={"modules": "earningsTrend,financialData"},
        )
    except GatherError:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

    quote_summary = data.get("quoteSummary", {}).get("result")
    if not quote_summary:
        return []

    result_data = quote_summary[0] if quote_summary else {}
    items: list[RevenueConsensus] = []

    # earningsTrend: 분기/연간 estimates
    earnings_trend = result_data.get("earningsTrend", {}).get("trend", [])
    for trend in earnings_trend:
        period = trend.get("period", "")
        # 연간만 ("+1y", "+2y", "0y" 등)
        if "y" not in period:
            continue

        end_date = trend.get("endDate", "")
        # endDate → fiscal year 추출
        fy = 0
        if end_date:
            try:
                fy = int(end_date[:4])
            except (ValueError, IndexError):
                pass
        if fy == 0:
            continue

        revenue_est_raw = trend.get("revenueEstimate", {})
        revenue_avg = revenue_est_raw.get("avg", {}).get("raw", 0)

        earnings_est_raw = trend.get("earningsEstimate", {})
        eps_avg = earnings_est_raw.get("avg", {}).get("raw")

        if revenue_avg <= 0:
            continue

        # Yahoo는 USD 단위 → 억원 변환하지 않음 (EDGAR는 원화가 아님)
        # source에 "yahoo_consensus"를 마킹하여 통화 구분
        source = "yahoo_consensus" if period.startswith("+") else "yahoo_actual"

        items.append(
            RevenueConsensus(
                fiscal_year=fy,
                revenue_est=revenue_avg,  # USD 기준 (원화 아님)
                operating_profit_est=None,
                net_income_est=None,
                eps_est=eps_avg,
                per_est=None,
                source=source,
            )
        )

    # financialData: 현재 실적 (totalRevenue)
    fin_data = result_data.get("financialData", {})
    total_revenue = fin_data.get("totalRevenue", {}).get("raw", 0)
    if total_revenue > 0 and not any(i.source == "yahoo_actual" for i in items):
        # fiscal year 추정: 가장 최근 완료 연도
        current_year = datetime.now(timezone.utc).year
        items.append(
            RevenueConsensus(
                fiscal_year=current_year - 1,
                revenue_est=total_revenue,
                source="yahoo_actual",
            )
        )

    return items


# ══════════════════════════════════════
# 배당/분할 이벤트
# ══════════════════════════════════════


async def fetchDividends(
    stock_code: str,
    client,
    *,
    market: str = "KR",
    years: int = 10,
) -> list[dict]:
    """배당 이력 — Yahoo v8 chart API (events=div)."""
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    now = int(datetime.now(timezone.utc).timestamp())
    period1 = now - years * 365 * 86400

    try:
        resp = await client.get(
            _CHART_URL.format(ticker=ticker),
            params={
                "period1": str(period1),
                "period2": str(now),
                "interval": "1d",
                "events": "div",
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

    events = result[0].get("events", {}).get("dividends", {})
    rows = []
    for ts, ev in sorted(events.items(), key=lambda x: int(x[0])):
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        rows.append({"date": dt.strftime("%Y-%m-%d"), "amount": ev.get("amount", 0.0)})
    return rows


async def fetchSplits(
    stock_code: str,
    client,
    *,
    market: str = "KR",
    years: int = 20,
) -> list[dict]:
    """분할 이력 — Yahoo v8 chart API (events=split)."""
    ticker = resolve_ticker(stock_code, market, "yahoo_direct")
    now = int(datetime.now(timezone.utc).timestamp())
    period1 = now - years * 365 * 86400

    try:
        resp = await client.get(
            _CHART_URL.format(ticker=ticker),
            params={
                "period1": str(period1),
                "period2": str(now),
                "interval": "1d",
                "events": "split",
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

    events = result[0].get("events", {}).get("splits", {})
    rows = []
    for ts, ev in sorted(events.items(), key=lambda x: int(x[0])):
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        rows.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "numerator": ev.get("numerator", 1),
                "denominator": ev.get("denominator", 1),
            }
        )
    return rows
