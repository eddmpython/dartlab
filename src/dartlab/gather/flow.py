"""수급 fallback facade — 한국 전용 (naver)."""

from __future__ import annotations

import logging

from .domains import FLOW_FALLBACK, load_domain
from .types import GatherError

log = logging.getLogger(__name__)


async def fetch(
    stock_code: str,
    *,
    market: str = "KR",
    client=None,
) -> list[dict] | None:
    """수급 시계열 — fallback 체인 (async). KR만 지원."""
    if market != "KR":
        return None

    for domain_name in FLOW_FALLBACK:
        try:
            module = load_domain(domain_name)
            result = await module.fetch_flow(stock_code, client)
            if result:
                return result
        except (GatherError, ImportError, OSError) as exc:
            log.debug("flow fallback %s 실패: %s", domain_name, exc)
            continue
    return None
