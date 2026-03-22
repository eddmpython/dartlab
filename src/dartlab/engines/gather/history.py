"""히스토리 fallback facade — yahoo_direct → fmp → yahoo 순서 (async)."""

from __future__ import annotations

import asyncio
import logging

from .domains import HISTORY_FALLBACK, load_domain
from .resilience import circuit_breaker
from .types import GatherError

log = logging.getLogger(__name__)


async def fetch(
    stock_code: str,
    *,
    start: str,
    end: str,
    market: str = "KR",
    client=None,
) -> list[dict]:
    """히스토리 OHLCV — fallback 체인 (async).

    Args:
        start: "2024-01-01"
        end: "2024-12-31"

    Returns:
        [{"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]
    """
    chain = list(HISTORY_FALLBACK)
    # fmp도 히스토리 지원 — fallback에 추가 (중복 방지)
    if "fmp" not in chain:
        chain.append("fmp")

    for source_name in chain:
        if circuit_breaker.is_open(source_name):
            continue

        try:
            module = load_domain(source_name)

            if source_name == "yahoo":
                # yfinance 기반 — 동기, client 인자 없음, pl.DataFrame 반환
                if hasattr(module, "fetch_history"):
                    result = await asyncio.to_thread(
                        module.fetch_history,
                        stock_code,
                        start=start,
                        end=end,
                        market=market,
                    )
                    if result is not None and len(result) > 0:
                        # pl.DataFrame → list[dict] 변환
                        if hasattr(result, "to_dicts"):
                            return result.to_dicts()
                        return result
            elif hasattr(module, "fetch_history"):
                result = await module.fetch_history(
                    stock_code, client, start=start, end=end, market=market,
                )
                if result:
                    return result

        except (GatherError, ImportError, OSError) as exc:
            log.debug("history fallback %s 실패: %s", source_name, exc)
            continue

    return []
