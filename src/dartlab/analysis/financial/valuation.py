"""가치평가 축 -- facade. 본체는 `_valuationInputs` / `_valuationDcf` / `_valuationOther`.

calc 함수 9개: DCF, DDM, 상대가치, RIM, 목표주가, 역내재성장률, 민감도, 종합합성, 플래그.
모든 함수는 ``(company) -> dict | None`` 시그니처.
"""

from __future__ import annotations

from dartlab.analysis.financial._valuationDcf import (
    calcDcf,
    calcDdm,
    calcRelativeValuation,
    calcSensitivity,
)

# 분리된 깊이 (BC re-export)
from dartlab.analysis.financial._valuationDeep import (  # noqa: E402, F401
    _classifyCompanyType,
    calcPriceTarget,
    calcValuationFlags,
    calcValuationSynthesis,
)
from dartlab.analysis.financial._valuationInputs import (
    _IG_TO_SECTOR_KEY,
    _fetchPriceContext,
    _getSectorParams,
    _getSeriesAndShares,
    _resolveSectorKey,
)
from dartlab.analysis.financial._valuationOther import (
    _HOLDING_SUBS,
    calcNavValuation,
    calcResidualIncome,
    calcReverseImplied,
)
from dartlab.analysis.valuation.pricetarget import computePriceTarget

__all__ = [
    "_HOLDING_SUBS",
    "_IG_TO_SECTOR_KEY",
    "_classifyCompanyType",
    "_fetchPriceContext",
    "_getSectorParams",
    "_getSeriesAndShares",
    "_resolveSectorKey",
    "calcDcf",
    "calcDdm",
    "calcNavValuation",
    "calcPriceTarget",
    "calcRelativeValuation",
    "calcResidualIncome",
    "calcReverseImplied",
    "calcSensitivity",
    "calcValuationFlags",
    "calcValuationSynthesis",
    "computePriceTarget",
]
