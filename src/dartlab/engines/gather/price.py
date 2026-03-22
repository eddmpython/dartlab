"""주가 fallback facade — naver → yahoo 순서로 시도."""

from __future__ import annotations

import logging

from .domains import PRICE_FALLBACK, load_domain
from .types import GatherError, PriceSnapshot

log = logging.getLogger(__name__)


def fetch(
    stock_code: str,
    *,
    market: str = "KR",
    client=None,
) -> PriceSnapshot | None:
    """주가 — fallback 체인.

    KR: naver → yahoo
    US: yahoo
    """
    chain = PRICE_FALLBACK if market == "KR" else ["yahoo"]

    for domain_name in chain:
        try:
            module = load_domain(domain_name)
            if domain_name == "yahoo":
                result = module.fetch_price(stock_code, client, market=market)
            else:
                result = module.fetch_price(stock_code, client)
            if result:
                return result
        except (GatherError, ImportError, OSError) as exc:
            log.debug("price fallback %s 실패: %s", domain_name, exc)
            continue
    return None
