"""주가 fallback facade — 시장별 동적 fallback + circuit breaker + health tracking (async)."""

from __future__ import annotations

import copy
import logging
import time
from typing import Awaitable, Callable, cast

from ..domains import getPriceFallback, loadDomain
from ..infra.cache import GatherCache
from ..infra.consolidation import checkDiff as _checkConsolidation
from ..infra.resilience import circuitBreaker, healthTracker
from ..infra.telemetry import emitGatherFallback
from ..marketConfig import getMarketConfig
from ..types import (
    CircuitOpenError,
    GatherError,
    PriceSnapshot,
    SourceAttemptsExhaustedError,
    SourceUnavailableError,
)

log = logging.getLogger(__name__)

# 모듈 레벨 stale cache (price.py 단독 사용 시)
_staleCache = GatherCache(maxEntries=100)


async def fetch(
    stockCode: str,
    *,
    market: str = "KR",
    client=None,
    limit: int | None = None,
    consolidate: bool = False,
) -> PriceSnapshot | None:
    """주가 — 시장별 fallback 체인 + circuit breaker + health scoring (async).

    1. health score로 fallback 순서 재정렬
    2. circuit open인 소스 skip
    3. 성공/실패를 circuit breaker + health tracker에 기록
    4. 전부 실패 시 stale cache에서 반환 시도

    Capabilities:
        - market-aware fallback chain + 동적 health scoring
        - circuit breaker open 시 skip
        - stale cache 안전망 (마지막 성공값 보존)

    AIContext:
        - mixin.price 의 backend — gather price axis 의 진짜 source-level 진입점

    Guide:
        Naver(KR)/Yahoo(US)/FMP/FDR 등 fallback chain. health 가 가장 좋은
        source 부터 시도 (recency 가중).

    When:
        gather.price() 의 PriceSnapshot 호출 chain 진입 시.

    How:
        chain reorder → 각 source 시도 → 성공 시 record → 실패 시 stale.

    Requires:
        네트워크 (다중 fallback source).

    Parameters
    ----------
    stock_code : str
        종목코드/티커 (예: "005930", "AAPL").
    market : str
        시장 코드 ("KR", "US", "JP" 등). 기본 "KR".
    client : httpx.AsyncClient | None
        HTTP 클라이언트. None이면 GatherHttpClient 자동 생성.
    limit : int | None
        단건 스냅샷 반환 함수라 무시된다. 인터페이스 호환 목적으로만 존재.
    consolidate : bool
        True 면 primary 성공 후 chain 의 다음 alive source 도 시도해서
        ``infra.consolidation.checkDiff`` 로 drift 측정. breached 시 logger.warning
        + ``data/qualityIncidents/priceConsolidation.parquet`` 박제. default False
        (호출량 2 배 증가하므로 명시 호출 시만).

    Returns
    -------
    PriceSnapshot | None
        주가 스냅샷. 주요 필드:

        - current : float — 현재가 (원 또는 해당 통화)
        - change : float — 전일 대비 변동 (원)
        - change_pct : float — 전일 대비 변동률 (%)
        - high_52w : float — 52주 최고가 (원)
        - low_52w : float — 52주 최저가 (원)
        - volume : int — 거래량 (주)
        - market_cap : float — 시가총액 (억원)
        - per : float | None — PER (배)
        - pbr : float | None — PBR (배)
        - dividend_yield : float | None — 배당수익률 (%)
        - currency : str — 통화 코드 ("KRW", "USD" 등)
        - is_stale : bool — stale cache 반환 여부

        하나 이상의 source가 정상 무데이터를 반환하면 None.

    Raises
    ------
    ValueError
        종목코드와 시장 입력 계약 위반.
    SourceAttemptsExhaustedError
        모든 fallback source가 실패하고 stale cache도 없는 경우.

    Example
    -------
    >>> snap = await fetch("005930", market="KR")

    See Also:
        ``dartlab.gather.infra.resilience.CircuitBreaker``.
        ``dartlab.gather.domains.fallback.healthTracker``.
    """
    config = getMarketConfig(market)
    from ..infra.cache import buildCacheSlot

    cacheSlot = buildCacheSlot("price", market=market)
    chain = getPriceFallback(market)
    chain = healthTracker.reorder(chain)

    # client=None이면 자체 생성
    if client is None:
        from ..infra.http import GatherHttpClient

        client = GatherHttpClient()

    attempts: list[tuple[str, Exception]] = []
    hadSuccessfulResponse = False

    for i, source_name in enumerate(chain):
        if circuitBreaker.isOpen(source_name):
            log.debug("price skip %s (circuit open)", source_name)
            attempts.append((source_name, CircuitOpenError(f"{source_name} circuit breaker가 열려 있습니다")))
            continue

        t0 = time.monotonic()
        try:
            module = loadDomain(source_name)
            fetchPrice = getattr(module, "fetchPrice", None)
            if not callable(fetchPrice):
                raise SourceUnavailableError(f"{source_name}에 fetchPrice 구현이 없습니다")

            fetchPriceFn = cast(Callable[..., Awaitable[PriceSnapshot | None]], fetchPrice)
            result = await fetchPriceFn(stockCode, client, market=market)

            latency = time.monotonic() - t0
            hadSuccessfulResponse = True

            if result is not None:
                if not isinstance(result, PriceSnapshot):
                    raise TypeError(
                        f"{source_name}.fetchPrice가 PriceSnapshot이 아닌 {type(result).__name__}을 반환했습니다"
                    )
                result.currency = config.currency
                result.market = market
                circuitBreaker.recordSuccess(source_name)
                healthTracker.record(source_name, success=True, latency=latency)
                # stale cache에도 저장 (fallback용)
                _staleCache.putTyped(stockCode, cacheSlot, result)

                # Sprint 1 PR3 — 정확도 drift 감지 (consolidate=True 시만)
                if consolidate:
                    await _verifyConsolidation(stockCode, market, result, chain, i, client)

                return result

            # None 반환 = 데이터 없음 (에러는 아님)
            healthTracker.record(source_name, success=True, latency=latency)

        except ValueError:
            raise
        except Exception as exc:
            latency = time.monotonic() - t0
            circuitBreaker.recordFailure(source_name)
            healthTracker.record(source_name, success=False, latency=latency)
            log.debug("price fallback %s 실패: %s", source_name, exc)
            attempts.append((source_name, exc))
            # fallback 신호 — 다음 source 가 chain 에 존재할 때만 (A 트랙 O2)
            if i + 1 < len(chain):
                emitGatherFallback("price", primary=source_name, fallback=chain[i + 1])
            continue

    # 모든 소스 실패 → stale cache 시도
    stale = _staleCache.getTyped(stockCode, cacheSlot, allowStale=True)
    if stale is not None and isinstance(stale, PriceSnapshot):
        stale_copy = copy.copy(stale)
        stale_copy.is_stale = True
        log.info("price %s: stale cache 반환", stockCode)
        return stale_copy

    if hadSuccessfulResponse:
        return None
    raise SourceAttemptsExhaustedError("price", attempts)


async def _verifyConsolidation(
    stockCode: str,
    market: str,
    primary: PriceSnapshot,
    chain: list[str],
    primaryIdx: int,
    client,
) -> None:
    """primary 성공 후 다음 alive source 도 시도 → checkDiff 박제.

    Sig: ``_verifyConsolidation(stockCode, market, primary, chain, primaryIdx, client) -> None``

    Capabilities: chain 내 primary 이후 첫 alive source 호출 + diff 측정 + breached 시 archive.
    AIContext: ``fetch(consolidate=True)`` 의 후속 hook — 사용자 직접 호출 금지.
    Guide: 두 번째 source 실패는 silent (drift 측정 못 한 것은 incident 아님).
    When: primary 성공 + consolidate=True.
    How: chain[primaryIdx+1:] 순회 → circuit open skip → loadDomain → fetchPrice → checkDiff.

    Args:
        stockCode: 종목 코드.
        market: 시장 코드.
        primary: 1순위 응답 (이미 currency/market 채워짐).
        chain: reorder 된 fallback chain.
        primaryIdx: chain 안 primary 의 인덱스.
        client: GatherHttpClient (재사용).

    Returns:
        None — incident 박제는 ``infra.consolidation`` 가 처리.

    Raises:
        없음 — 모든 예외 흡수 (관찰성 hook 이지 본 fetch 흐름 차단 금지).

    Example:
        내부 헬퍼. 직접 호출 안 함.

    See Also:
        ``infra.consolidation.checkDiff`` — diff 측정 + archive.
    """
    config = getMarketConfig(market)
    for source_name in chain[primaryIdx + 1 :]:
        if circuitBreaker.isOpen(source_name):
            continue
        try:
            module = loadDomain(source_name)
            fetchPrice = getattr(module, "fetchPrice", None)
            if not callable(fetchPrice):
                continue
            fetchPriceFn = cast(Callable[..., Awaitable[PriceSnapshot | None]], fetchPrice)
            secondary = await fetchPriceFn(stockCode, client, market=market)
            if secondary is None:
                continue
            secondary.currency = config.currency
            secondary.market = market
            _checkConsolidation(primary, secondary)
            return
        except (GatherError, ImportError, OSError, ValueError) as exc:
            log.debug("consolidation secondary %s 실패 (silent): %s", source_name, exc)
            continue
