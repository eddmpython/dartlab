"""ratios 호환 re-export.

새 SSOT 는 ``dartlab.core.ratios`` 다. 기존
``dartlab.analysis.financial.ratios`` import 경로 보존 + L1 ↛ L2 lazy upper
회피 (providers/edgar/accessor + providers/dart/builder).
"""

from __future__ import annotations

from dartlab.core.ratios import (  # noqa: F401
    RATIO_CATEGORIES,
    RatioResult,
    RatioSeriesResult,
    _detectArchetype,
    _safeDiv,
    _safePct,
    _safePctPositive,
    _yoy,
    calcRatios,
    calcRatioSeries,
    toSeriesDict,
    yoyPct,
)
