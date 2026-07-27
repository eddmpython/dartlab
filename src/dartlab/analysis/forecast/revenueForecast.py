"""매출 예측 (Revenue Forecast) — facade. 본체는 `_revenueForecastTypes` / `_revenueForecastCore`.

설계 원칙 (Engine-First, AI-Augmented):
- 엔진이 재현 가능하고 투명한 기본 예측을 생성
- ai_context 필드로 AI가 세계 지식으로 보정할 수 있는 브릿지 제공
- 결과 스키마는 도메인(DART/EDGAR/EDINET) 불문 동일
- 3-시나리오 출력 (Base/Bull/Bear)으로 불확실성 정량화
- CompanyDataBundle로 L1 데이터를 L0에 전달 (L0→L1 import 금지)

외부 의존성: gather 엔진 (optional — 없으면 시계열 only).
"""

from __future__ import annotations

from dartlab.analysis.forecast._revenueForecastCore import (
    _BACKLOG_WEIGHT,
    _ROIC_WEIGHT,
    _SEGMENT_WEIGHT,
    forecastRevenue,
)
from dartlab.analysis.forecast._revenueForecastLifecycle import (
    _classifyLifecycle,
    _computeWeights,
    _fetchConsensusRevenue,
    _fundamentalGrowth,
    _lifecycleWeightAdjustments,
)
from dartlab.analysis.forecast._revenueForecastOverlay import (
    _MAX_ANNUAL_ADJ,
    _MAX_TOTAL_ADJ,
    applyAiOverlay,
)
from dartlab.analysis.forecast._revenueForecastTypes import (
    BacklogSignal,
    CompanyDataBundle,
    RevenueForecastAIOverlay,
    RevenueForecastResult,
    SegmentForecast,
)

__all__ = [
    "_BACKLOG_WEIGHT",
    "_MAX_ANNUAL_ADJ",
    "_MAX_TOTAL_ADJ",
    "_ROIC_WEIGHT",
    "_SEGMENT_WEIGHT",
    "BacklogSignal",
    "CompanyDataBundle",
    "RevenueForecastAIOverlay",
    "RevenueForecastResult",
    "SegmentForecast",
    "_classifyLifecycle",
    "_computeWeights",
    "_fetchConsensusRevenue",
    "_fundamentalGrowth",
    "_lifecycleWeightAdjustments",
    "applyAiOverlay",
    "forecastRevenue",
]
