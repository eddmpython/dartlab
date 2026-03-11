"""재무 숫자 데이터 엔진.

OpenDART 재무제표 parquet에서 시계열을 추출하고,
표준계정 매핑 → 피벗 → 비율 계산까지 처리한다.
"""

from dartlab.engines.dart.finance.extract import getAnnualValues, getLatest, getRevenueGrowth3Y, getTTM
from dartlab.engines.dart.finance.mapper import AccountMapper
from dartlab.engines.dart.finance.pivot import (
    buildAnnual,
    buildCumulative,
    buildSceAnnual,
    buildSceMatrix,
    buildTimeseries,
)
from dartlab.engines.dart.finance.ratios import calcRatios, calcRatioSeries, toSeriesDict

__all__ = [
    "buildTimeseries",
    "buildAnnual",
    "buildCumulative",
    "buildSceMatrix",
    "buildSceAnnual",
    "getTTM",
    "getLatest",
    "getAnnualValues",
    "getRevenueGrowth3Y",
    "calcRatios",
    "calcRatioSeries",
    "toSeriesDict",
    "AccountMapper",
]
