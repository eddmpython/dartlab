"""내부자 거래 facade -- KR(DART)."""

from __future__ import annotations

import logging

from .types import InsiderTrade, MajorHolder

log = logging.getLogger(__name__)


async def fetchInsiderTrading(
    stockCode: str,
    *,
    market: str = "KR",
    **_kwargs,
) -> list[InsiderTrade]:
    """내부자(임원/주요주주) 거래 내역 -- KR만 지원."""
    if market != "KR":
        return []
    try:
        from .domains.dartApi import fetchInsiderTrading as _dartInsider

        return await _dartInsider(stockCode)
    except (ImportError, OSError) as exc:
        log.warning("insider KR 실패 (%s): %s", stockCode, exc)
        return []


async def fetchMajorShareholders(
    stockCode: str,
    *,
    market: str = "KR",
    **_kwargs,
) -> list[MajorHolder]:
    """5% 이상 대량보유 변동 -- KR(DART)."""
    if market != "KR":
        return []
    try:
        from .domains.dartApi import fetchMajorShareholders as _dartMajor

        return await _dartMajor(stockCode)
    except (ImportError, OSError) as exc:
        log.warning("majorShareholders 실패 (%s): %s", stockCode, exc)
        return []
