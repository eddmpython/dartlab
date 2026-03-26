"""재무 숫자 데이터 엔진.

OpenDART 재무제표 parquet에서 시계열을 추출하고,
표준계정 매핑 → 피벗 → 비율 계산까지 처리한다.
"""

from dartlab.providers.dart.finance.extract import getAnnualValues, getLatest, getRevenueGrowth3Y, getTTM
from dartlab.providers.dart.finance.mapper import AccountMapper
from dartlab.providers.dart.finance.pivot import (
    buildAnnual,
    buildCumulative,
    buildSceAnnual,
    buildSceMatrix,
    buildTimeseries,
)
from dartlab.providers.dart.finance.ratios import calcRatios, calcRatioSeries, toSeriesDict
from dartlab.providers.dart.finance.scanAccount import scanAccount, scanRatio, scanRatioList

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
    "scanAccount",
    "scanRatio",
    "scanRatioList",
]
