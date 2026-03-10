"""하위호환 re-export — 실제 구현은 engines.common.finance.ratios."""

from dartlab.engines.common.finance.ratios import (
    RatioResult,
    RatioSeriesResult,
    calcRatios,
    calcRatioSeries,
    toSeriesDict,
    RATIO_CATEGORIES,
)

__all__ = ["RatioResult", "RatioSeriesResult", "calcRatios", "calcRatioSeries", "toSeriesDict", "RATIO_CATEGORIES"]
