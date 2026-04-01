"""7-1 기술적 분석 — quant 엔진을 analysis 축으로 래핑.

주가 OHLCV → 25개 기술적 지표 + 9개 신호 + 종합 판단.
gather("price")로 데이터를 가져와 quant 모듈에 위임.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._memoize import memoized_calc


def _fetchOHLCV(company) -> Any:
    """Company에서 주가 OHLCV 가져오기."""
    try:
        return company.gather("price")
    except (AttributeError, TypeError, ValueError):
        return None


@memoized_calc
def calcTechnicalVerdict(company, *, basePeriod: str | None = None) -> dict | None:
    """종합 기술적 판단 — 강세/중립/약세 + RSI/ADX/SMA/BB."""
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or (hasattr(ohlcv, "is_empty") and ohlcv.is_empty()):
        return None

    from dartlab.quant.analyzer import technicalVerdict

    return technicalVerdict(ohlcv)


@memoized_calc
def calcTechnicalIndicators(company, *, basePeriod: str | None = None) -> dict | None:
    """25개 기술적 지표 전체."""
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or (hasattr(ohlcv, "is_empty") and ohlcv.is_empty()):
        return None

    from dartlab.quant.analyzer import enrichWithIndicators

    df = enrichWithIndicators(ohlcv)
    return {"dataframe": df, "rows": df.shape[0], "columns": df.columns}


@memoized_calc
def calcBeta(company, *, basePeriod: str | None = None) -> dict | None:
    """시장 베타 + CAPM 기대수익률."""
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or (hasattr(ohlcv, "is_empty") and ohlcv.is_empty()):
        return None

    from dartlab.quant.analyzer import _calcBeta, _fetchBenchmark

    market = _fetchBenchmark()
    if market is None or market.is_empty():
        return None

    return _calcBeta(ohlcv, market)
