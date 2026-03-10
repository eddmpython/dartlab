"""소스 독립적 재무 유틸리티.

시계열 dict에서 값을 추출하고 비율을 계산한다.
DART, EDGAR 등 어떤 L1 소스의 결과든 동일한 dict 구조면 동작.
"""

from dartlab.engines.common.finance.extract import (
    getTTM,
    getLatest,
    getAnnualValues,
    getRevenueGrowth3Y,
)
from dartlab.engines.common.finance.ratios import (
    calcRatios,
    calcRatioSeries,
    toSeriesDict,
    RATIO_CATEGORIES,
    RatioResult,
    RatioSeriesResult,
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
]
