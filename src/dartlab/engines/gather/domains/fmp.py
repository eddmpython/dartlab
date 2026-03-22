"""Financial Modeling Prep — API 키 기반 보조 소스.

무료 플랜: 250 req/day. API 키 없으면 자동 skip (다음 fallback으로).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from ..market_config import resolve_ticker
from ..types import GatherError, PriceSnapshot

log = logging.getLogger(__name__)

_BASE = "https://financialmodelingprep.com/api/v3"


def _get_api_key() -> str | None:
    return os.environ.get("FMP_API_KEY")


def fetch_price(stock_code: str, client, *, market: str = "US") -> PriceSnapshot | None:
    """현재가 — /quote/{ticker}."""
    key = _get_api_key()
    if not key:
        return None  # 키 없으면 skip

    ticker = resolve_ticker(stock_code, market, "fmp")

    try:
        resp = client.get(
            f"{_BASE}/quote/{ticker}",
            params={"apikey": key},
        )
    except GatherError:
        return None

    try:
        data = resp.json()
    except ValueError:
        return None

    if not data or not isinstance(data, list) or len(data) == 0:
        return None

    q = data[0]
    current = q.get("price", 0.0)
    if not current:
        return None

    return PriceSnapshot(
        current=current,
        change=q.get("change", 0.0),
        change_pct=q.get("changesPercentage", 0.0),
        high_52w=q.get("yearHigh", 0.0),
        low_52w=q.get("yearLow", 0.0),
        volume=q.get("volume", 0),
        market_cap=q.get("marketCap", 0.0),
        per=q.get("pe") if q.get("pe") else None,
        pbr=None,
        dividend_yield=None,
        source="fmp",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        currency=q.get("currency", "USD"),
        exchange=q.get("exchange", ""),
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
    """히스토리 OHLCV — /historical-price-full/{ticker}.

    Returns:
        [{"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]
    """
    key = _get_api_key()
    if not key:
        return []

    ticker = resolve_ticker(stock_code, market, "fmp")

    try:
        resp = client.get(
            f"{_BASE}/historical-price-full/{ticker}",
            params={"apikey": key, "from": start, "to": end},
        )
    except GatherError:
        return []

    try:
        data = resp.json()
    except ValueError:
        return []

    historical = data.get("historical", [])
    if not historical:
        return []

    rows = []
    for h in reversed(historical):  # FMP는 최신→과거 순 → 역순
        rows.append({
            "date": h.get("date", ""),
            "open": h.get("open", 0.0),
            "high": h.get("high", 0.0),
            "low": h.get("low", 0.0),
            "close": h.get("close", 0.0),
            "volume": h.get("volume", 0),
        })

    return rows
