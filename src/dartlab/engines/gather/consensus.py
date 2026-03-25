"""컨센서스 fallback facade — 시장별 다중 소스."""

from __future__ import annotations

import logging

from .domains import CONSENSUS_FALLBACK, load_domain
from .resilience import circuit_breaker as _cb
from .types import ConsensusData, GatherError

log = logging.getLogger(__name__)


async def fetch(
    stock_code: str,
    *,
    market: str = "KR",
    client=None,
) -> ConsensusData | None:
    """컨센서스 — fallback 체인 (async).

    KR: naver → yahoo_direct
    US/기타: yahoo_direct → naver
    """
    if market == "KR":
        chain = CONSENSUS_FALLBACK  # ["naver", "yahoo_direct"]
    else:
        chain = ["yahoo_direct"]  # US는 naver 불가

    for domain_name in chain:
        if _cb.is_open(domain_name):
            log.debug("consensus skip %s (circuit open)", domain_name)
            continue
        try:
            module = load_domain(domain_name)
            if not hasattr(module, "fetch_consensus"):
                continue
            if domain_name == "naver":
                result = await module.fetch_consensus(stock_code, client)
            else:
                result = await module.fetch_consensus(stock_code, client, market=market)
            if result:
                _cb.record_success(domain_name)
                return result
        except (GatherError, ImportError, OSError, AttributeError) as exc:
            _cb.record_failure(domain_name)
            log.debug("consensus fallback %s 실패: %s", domain_name, exc)
            continue
    return None
