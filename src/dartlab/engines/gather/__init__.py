"""Gather 엔진 — 통합 멀티소스 수집.

Usage::

    from dartlab.engines.gather import Gather

    g = Gather()
    g.price("005930")              # PriceSnapshot (fallback)
    g.consensus("005930")          # ConsensusData
    g.flow("005930")               # FlowData

    snap = g.collect("005930")     # 전체 병렬 수집 → GatherSnapshot
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from . import consensus as _consensus
from . import flow as _flow
from . import history as _history
from . import price as _price
from .cache import GatherCache
from .domains import get_price_fallback, load_domain
from .http import GatherHttpClient
from .market_config import get_market_config
from .types import (
    ConsensusData,
    FlowData,
    GatherResult,
    GatherSnapshot,
    MarketSnapshot,
    PeerData,
    PriceSnapshot,
    RevenueConsensus,
    SourceUnavailableError,
)

log = logging.getLogger(__name__)


class Gather:
    """통합 멀티소스 수집 엔진.

    - 개별 조회: price(), consensus(), flow() — fallback 체인
    - 전체 수집: collect() — 도메인별 병렬 호출
    - 캐시: TTL 기반 데이터 유형별 자동 만료
    """

    def __init__(self, client: GatherHttpClient | None = None) -> None:
        self._client = client or GatherHttpClient()
        self._cache = GatherCache()
        self._owns_client = client is None

    # ── 개별 조회 (fallback 체인) ──

    def price(self, stock_code: str, *, market: str = "KR") -> PriceSnapshot | None:
        """주가 — naver → yahoo fallback."""
        cached = self._cache.get_typed(stock_code, "price")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = _price.fetch(stock_code, market=market, client=self._client)
        if result:
            self._cache.put_typed(stock_code, "price", result)
        return result

    def consensus(self, stock_code: str) -> ConsensusData | None:
        """컨센서스 — naver fallback."""
        cached = self._cache.get_typed(stock_code, "consensus")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = _consensus.fetch(stock_code, client=self._client)
        if result:
            self._cache.put_typed(stock_code, "consensus", result)
        return result

    def flow(self, stock_code: str) -> FlowData | None:
        """수급 — naver fallback."""
        cached = self._cache.get_typed(stock_code, "flow")
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = _flow.fetch(stock_code, client=self._client)
        if result:
            self._cache.put_typed(stock_code, "flow", result)
        return result

    def revenue_consensus(self, stock_code: str) -> list[RevenueConsensus]:
        """매출/이익 컨센서스 — 네이버 finance/annual API."""
        cached = self._cache.get_typed(stock_code, "revenue_consensus")
        if cached is not None:
            return cached  # type: ignore[return-value]
        try:
            module = load_domain("naver")
            result = module.fetch_revenue_consensus(stock_code, self._client)
        except (SourceUnavailableError, ImportError, OSError) as exc:
            log.debug("revenue_consensus 실패 (%s): %s", stock_code, exc)
            result = []
        if result:
            self._cache.put_typed(stock_code, "revenue_consensus", result)
        return result

    def history(
        self,
        stock_code: str,
        *,
        start: str,
        end: str,
        market: str = "KR",
    ) -> list[dict]:
        """히스토리 OHLCV — fallback 체인 (yahoo_direct → fmp → yahoo).

        Args:
            start: "2024-01-01"
            end: "2024-12-31"

        Returns:
            [{"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]
        """
        cache_key = f"{stock_code}:history:{start}:{end}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]
        result = _history.fetch(
            stock_code, start=start, end=end, market=market, client=self._client,
        )
        if result:
            from .cache import TTL_HISTORY

            self._cache.put(cache_key, result, TTL_HISTORY)
        return result

    # ── 전체 병렬 수집 ──

    def collect(self, stock_code: str, *, market: str = "KR") -> GatherSnapshot:
        """모든 도메인에서 병렬 수집 → GatherSnapshot.

        각 도메인(naver, yahoo)을 ThreadPoolExecutor로 동시 호출.
        개별 도메인 실패는 격리 — 나머지 결과로 스냅샷 생성.
        """
        cached = self._cache.get_typed(stock_code, "snapshot")
        if cached is not None:
            return cached  # type: ignore[return-value]

        config = get_market_config(market)
        # collect는 모든 가용 도메인에서 병렬 수집
        domains = list(dict.fromkeys(config.fallback_chain))  # 순서 유지 중복 제거

        results: dict[str, GatherResult] = {}
        with ThreadPoolExecutor(max_workers=len(domains)) as executor:
            futures = {executor.submit(self._fetch_domain, name, stock_code, market): name for name in domains}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except (SourceUnavailableError, TimeoutError, OSError) as exc:
                    log.warning("도메인 %s 수집 실패: %s", name, exc)
                    results[name] = GatherResult(domain=name, error=str(exc))

        snapshot = GatherSnapshot(
            stock_code=stock_code,
            results=results,
            collected_at=datetime.now(timezone.utc).isoformat(),
        )

        self._cache.put_typed(stock_code, "snapshot", snapshot)
        return snapshot

    def _fetch_domain(self, domain_name: str, stock_code: str, market: str) -> GatherResult:
        """단일 도메인에서 모든 데이터 수집."""
        module = load_domain(domain_name)
        # fetch_all이 있는 도메인 (naver, yahoo)
        if hasattr(module, "fetch_all"):
            if domain_name == "naver":
                return module.fetch_all(stock_code, self._client)
            return module.fetch_all(stock_code, self._client, market=market)
        # fetch_price만 있는 도메인 (yahoo_direct, fmp)
        price = None
        if hasattr(module, "fetch_price"):
            price = module.fetch_price(stock_code, self._client, market=market)
        return GatherResult(domain=domain_name, price=price)

    def invalidate(self, stock_code: str) -> None:
        """특정 종목의 캐시 무효화."""
        self._cache.invalidate(stock_code)

    def close(self) -> None:
        """리소스 정리."""
        if self._owns_client:
            self._client.close()

    def __repr__(self) -> str:
        return f"Gather(cache={self._cache})"


__all__ = [
    "Gather",
    "GatherSnapshot",
    "MarketSnapshot",
    "PeerData",
    "PriceSnapshot",
    "ConsensusData",
    "FlowData",
    "GatherResult",
    "RevenueConsensus",
]
