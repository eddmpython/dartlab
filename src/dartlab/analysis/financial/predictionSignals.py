"""6-2 예측신호 -- 이 회사의 실적은 어디로 향하는가.

다중 소스 예측 신호를 구조화된 데이터로 제공한다.
forecast 엔진(점 추정)과 달리, 방향성과 신뢰도에 집중한다.

학술 근거:
- Sloan 1996: 현금흐름 구성요소가 발생액보다 지속성 높음
- Cao & You 2024 (G&D Award): 횡단면 재무비율 → ML 이익 예측
- M Competition: 단순 앙상블이 복잡한 가중치를 이김
- M6: 방향 정확도가 점 정확도보다 투자에 유의미
"""

from __future__ import annotations

from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get

import logging
import math

from dartlab.analysis.financial._predictionMath import (
    _calcLagCorrelation,
    _fitOLS,
    _invertMatrix,
    _pearsonCorrelation,
    _quickCorr,
)
from dartlab.analysis.financial._predictionProbability import (
    _DIRECTION_SCORES,
    _bayesUpdate,
    _calibrate,
    _clamp,
)
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

log = logging.getLogger(__name__)

_MAX_YEARS = 8

# ── 업종별 모멘텀 사전확률 + 매크로 매핑 (JSON 단일 진실의 원천) ──
import json
from pathlib import Path as _Path

_SECTOR_DATA = json.loads(
    (
        _Path(__file__).resolve().parents[2]
        / "providers"
        / "mappers"
        / "mapperData"
        / "parserMappings"
        / "sectorPriors.json"
    ).read_text(encoding="utf-8")
)
_INDUSTRY_PRIOR: dict[str, float] = _SECTOR_DATA.get("priors", {})
_DEFAULT_PRIOR: float = _SECTOR_DATA.get("_metadata", {}).get("defaultPrior", 0.721)
_SECTOR_MACRO_MAP: dict[str, list[dict]] = _SECTOR_DATA.get("sectorMacroMap", {})
_sensitivity = _SECTOR_DATA.get("sectorSensitivity", {})
_RATE_SENSITIVE_SECTORS = set(_sensitivity.get("rate", []))
_FX_SENSITIVE_SECTORS = set(_sensitivity.get("fx", []))
_COMMODITY_SECTORS = set(_sensitivity.get("commodity", []))


# ── 공통 헬퍼 ──


from dartlab.analysis.financial._constants import (
    FX_SENSITIVITY_HIGH,
    FX_SENSITIVITY_MODERATE,
    TREND_RSQUARED_HIGH,
    TREND_RSQUARED_MEDIUM,
)
from dartlab.analysis.financial._predictionSynthesis import (
    calcPredictionFlags,
    calcPredictionSynthesis,
)
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.calc import safeDiv as _safe


def _getStockCode(company) -> str | None:
    """Company 객체에서 종목코드 추출."""
    return getattr(company, "stockCode", None)


def _getSectorKey(company) -> str | None:
    """업종 키 추출 (scenario.py와 동일 경로)."""
    try:
        from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY

        sectorInfo = company.sector
        if sectorInfo is not None:
            igName = sectorInfo.industryGroup.name
            return _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError, ImportError):
        pass
    return None


# ══════════════════════════════════════


# 분리된 신호 (BC re-export)
from dartlab.analysis.financial._signalsCorporate import (  # noqa: E402, F401
    calcAnnouncementTiming,
    calcDisclosureDelta,
    calcInventoryDivergence,
    calcSupplyChainSignal,
)
from dartlab.analysis.financial._signalsDirection import (  # noqa: E402, F401
    calcConsensusDirection,
    calcFlowDirection,
    calcRevenueDirection,
)
from dartlab.analysis.financial._signalsEarnings import calcEarningsMomentum  # noqa: E402, F401
from dartlab.analysis.financial._signalsEvent import calcEventImpact  # noqa: E402, F401
from dartlab.analysis.financial._signalsMacro import (  # noqa: E402, F401
    calcMacroRegression,
    calcMacroSensitivity,
    calcStructuralBreak,
)
from dartlab.analysis.financial._signalsPeer import calcPeerPrediction  # noqa: E402, F401
