"""주가 fallback facade — 시장별 동적 fallback + circuit breaker + health tracking."""

from __future__ import annotations

import copy
import logging
import time

from .cache import GatherCache
from .domains import get_price_fallback, load_domain
from .market_config import get_market_config
from .resilience import circuit_breaker, health_tracker
from .types import GatherError, PriceSnapshot

log = logging.getLogger(__name__)

# 모듈 레벨 stale cache (price.py 단독 사용 시)
_stale_cache = GatherCache(max_entries=100)


def fetch(
    stock_code: str,
    *,
    market: str = "KR",
    client=None,
) -> PriceSnapshot | None:
    """주가 — 시장별 fallback 체인 + circuit breaker + health scoring.

    1. health score로 fallback 순서 재정렬
    2. circuit open인 소스 skip
    3. 성공/실패를 circuit breaker + health tracker에 기록
    4. 전부 실패 시 stale cache에서 반환 시도
    """
    config = get_market_config(market)
    chain = get_price_fallback(market)
    chain = health_tracker.reorder(chain)

    for source_name in chain:
        if circuit_breaker.is_open(source_name):
            log.debug("price skip %s (circuit open)", source_name)
            continue

        t0 = time.monotonic()
        try:
            module = load_domain(source_name)
            if hasattr(module, "fetch_price"):
                result = module.fetch_price(stock_code, client, market=market)
            else:
                continue

            latency = time.monotonic() - t0

            if result:
                result.currency = config.currency
                result.market = market
                circuit_breaker.record_success(source_name)
                health_tracker.record(source_name, success=True, latency=latency)
                # stale cache에도 저장 (fallback용)
                _stale_cache.put_typed(stock_code, "price", result)
                return result

            # None 반환 = 데이터 없음 (에러는 아님)
            health_tracker.record(source_name, success=True, latency=latency)

        except (GatherError, ImportError, OSError) as exc:
            latency = time.monotonic() - t0
            circuit_breaker.record_failure(source_name)
            health_tracker.record(source_name, success=False, latency=latency)
            log.debug("price fallback %s 실패: %s", source_name, exc)
            continue

    # 모든 소스 실패 → stale cache 시도
    stale = _stale_cache.get_typed(stock_code, "price", allow_stale=True)
    if stale is not None and isinstance(stale, PriceSnapshot):
        stale_copy = copy.copy(stale)
        stale_copy.is_stale = True
        log.info("price %s: stale cache 반환", stock_code)
        return stale_copy

    return None
