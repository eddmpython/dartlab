"""하위호환 re-export — 실제 구현은 engines.common.finance.ratios."""

from dartlab.engines.common.finance.ratios import (
    RatioResult,
    RatioSeriesResult,
    calcRatios,
    calcRatioSeries,
)

__all__ = ["RatioResult", "RatioSeriesResult", "calcRatios", "calcRatioSeries"]
