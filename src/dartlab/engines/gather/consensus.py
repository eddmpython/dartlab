"""컨센서스 fallback facade — naver 순서로 시도."""

from __future__ import annotations

import logging

from .domains import CONSENSUS_FALLBACK, load_domain
from .types import ConsensusData, GatherError

log = logging.getLogger(__name__)


def fetch(
    stock_code: str,
    *,
    client=None,
) -> ConsensusData | None:
    """컨센서스 — fallback 체인."""
    for domain_name in CONSENSUS_FALLBACK:
        try:
            module = load_domain(domain_name)
            result = module.fetch_consensus(stock_code, client)
            if result:
                return result
        except (GatherError, ImportError, OSError) as exc:
            log.debug("consensus fallback %s 실패: %s", domain_name, exc)
            continue
    return None
