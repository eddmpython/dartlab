"""수급 fallback facade — naver 순서로 시도."""

from __future__ import annotations

import logging

from .domains import FLOW_FALLBACK, load_domain
from .types import FlowData, GatherError

log = logging.getLogger(__name__)


def fetch(
    stock_code: str,
    *,
    client=None,
) -> FlowData | None:
    """수급 — fallback 체인."""
    for domain_name in FLOW_FALLBACK:
        try:
            module = load_domain(domain_name)
            result = module.fetch_flow(stock_code, client)
            if result:
                return result
        except (GatherError, ImportError, OSError) as exc:
            log.debug("flow fallback %s 실패: %s", domain_name, exc)
            continue
    return None
