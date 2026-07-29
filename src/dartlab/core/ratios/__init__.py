"""DART? EDGAR ?? ???? ?? ??."""

from dartlab.core.ratioCategories import RATIO_CATEGORIES as RATIO_CATEGORIES
from dartlab.core.ratios.common import (
    _detectArchetype as _detectArchetype,
)
from dartlab.core.ratios.common import (
    _safeDiv as _safeDiv,
)
from dartlab.core.ratios.common import (
    _safePct as _safePct,
)
from dartlab.core.ratios.common import (
    _safePctPositive as _safePctPositive,
)
from dartlab.core.ratios.common import (
    _safeRound as _safeRound,
)
from dartlab.core.ratios.common import (
    _yoy as _yoy,
)
from dartlab.core.ratios.common import (
    yoyPct as yoyPct,
)
from dartlab.core.ratios.models import RatioResult as RatioResult
from dartlab.core.ratios.models import RatioSeriesResult as RatioSeriesResult
from dartlab.core.ratios.point import _calcProfitability as _calcProfitability
from dartlab.core.ratios.point import _calcStability as _calcStability
from dartlab.core.ratios.point import calcRatios as calcRatios
from dartlab.core.ratios.series import calcRatioSeries as calcRatioSeries
from dartlab.core.ratios.series import toSeriesDict as toSeriesDict

__all__ = [
    "RATIO_CATEGORIES",
    "RatioResult",
    "RatioSeriesResult",
    "calcRatios",
    "calcRatioSeries",
    "toSeriesDict",
    "yoyPct",
]
