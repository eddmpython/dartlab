"""시장 OHLCV 접근 공용 헬퍼.

L2 엔진들이 가격 데이터와 벤치마크를 함께 써야 할 때 직접 서로를 import하지
않도록 L1.5 synth에 둔다.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from dartlab.core.logger import logSafe

if TYPE_CHECKING:
    import polars as pl

log = logging.getLogger(__name__)


def fetchOhlcv(stockCode: str, **kwargs: Any) -> "pl.DataFrame | None":
    """gather("price")로 OHLCV 수집, 실패 시 None."""
    try:
        from dartlab.gather.entry import GatherEntry

        g = GatherEntry()
        return g("price", stockCode, **kwargs)
    except (ImportError, ValueError, TypeError, RuntimeError):
        log.warning("OHLCV fetch 실패: %s", logSafe(stockCode))
        return None


def fetchBenchmark(market: str = "KR", **kwargs: Any) -> "pl.DataFrame | None":
    """벤치마크 OHLCV 수집. KR은 시장 지수, US는 S&P500 계열."""
    try:
        from dartlab.synth.benchmarkData import fetchBenchmarkOhlcv

        stockCode = kwargs.pop("stockCode", None)
        benchmark = kwargs.pop("benchmark", None)
        benchmarkMode = kwargs.pop("benchmarkMode", "market")
        return fetchBenchmarkOhlcv(
            stockCode,
            market=market,
            benchmark=benchmark,
            benchmarkMode=benchmarkMode,
            **kwargs,
        )
    except (ImportError, ValueError, TypeError, RuntimeError):
        log.warning("벤치마크 fetch 실패: %s", logSafe(market))
        return None
