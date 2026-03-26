"""소스 독립적 재무 유틸리티.

시계열 dict에서 값을 추출하고 비율을 계산한다.
DART, EDGAR 등 어떤 L1 소스의 결과든 동일한 dict 구조면 동작.
"""

from dartlab.core.finance.currency import (
    convertValue,
    getExchangeRate,
)
from dartlab.core.finance.extract import (
    getAnnualValues,
    getLatest,
    getRevenueGrowth3Y,
    getTTM,
)
from dartlab.core.finance.merton import (
    MertonResult,
    calcEquityVolatility,
    solveMerton,
)
from dartlab.core.finance.ratios import (
    RATIO_CATEGORIES,
    RatioResult,
    RatioSeriesResult,
    calcRatios,
    calcRatioSeries,
    toSeriesDict,
    yoy_pct,
)

__all__ = [
    "getTTM",
    "getLatest",
    "getAnnualValues",
    "getRevenueGrowth3Y",
    "calcRatios",
    "calcRatioSeries",
    "toSeriesDict",
    "RATIO_CATEGORIES",
    "RatioResult",
    "RatioSeriesResult",
    "yoy_pct",
    # merton (structural model)
    "MertonResult",
    "calcEquityVolatility",
    "solveMerton",
    # currency
    "getExchangeRate",
    "convertValue",
]
