"""macro/corporate/historicalContext 결과 타입 — 8 dataclass.

macro/corporate/historicalContext.py 가 1115 줄 god module 이라 types 분리.
identity 보존을 위해 historicalContext.py 가 본 모듈에서 re-export 한다.

타입:
- HYSpikeHistory — HY 스프레드 급등 → 침체 통계
- YCInversionHistory — 수익률곡선 역전 → 침체 통계
- URBounceHistory — 실업률 저점 반등 → 침체 통계
- SimultaneousWarnings — 동시 경고등 판정
- BullishSignals — 호황/회복 신호
- HYCompressionHistory — HY 스프레드 급락 → 확장 통계
- HistoricalEvent — 유사 역사적 사건
- HistoricalContext — 종합 역사적 맥락
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HYSpikeHistory:
    """HY 스프레드 급등 → 침체 통계."""

    totalSpikes: int
    recessionWithin12m: int
    recessionRate12m: float
    nearestMatch: str | None
    nearestMatchDelta: float | None
    nearestMatchOutcome: str | None
    currentDelta: float | None
    description: str


@dataclass(frozen=True)
class YCInversionHistory:
    """Yield Curve 역전 → 침체 통계."""

    totalInversions: int
    avgLeadMonths: float | None
    medianLeadMonths: float | None
    rangeLeadMonths: tuple[int, int] | None
    currentInversionStart: str | None
    currentDurationMonths: int | None
    description: str


@dataclass(frozen=True)
class URBounceHistory:
    """실업률 저점 반등 → 침체 통계."""

    totalBounces: int
    recessionWithin12m: int
    recessionRate12m: float
    currentBounce: float | None
    description: str


@dataclass(frozen=True)
class SimultaneousWarnings:
    """동시 경고등 판정."""

    activeFlags: list[str]
    flagCount: int
    historicalOccurrences: int
    recessionRate18m: float
    similarPeriods: list[dict]
    description: str


@dataclass(frozen=True)
class BullishSignals:
    """호황/회복 신호 — 위기의 반대."""

    activeSignals: list[str]
    signalCount: int
    historicalOccurrences: int
    avgExpansionMonths: float | None
    similarPeriods: list[dict]
    description: str


@dataclass(frozen=True)
class HYCompressionHistory:
    """HY 스프레드 급락 (신용 완화) → 확장 통계."""

    totalCompressions: int
    avgExpansionMonths: float | None
    currentDelta: float | None
    description: str


@dataclass(frozen=True)
class HistoricalEvent:
    """현재와 유사한 역사적 사건."""

    eventName: str
    eventDate: str
    similarity: str
    context: str
    outcome: str


@dataclass(frozen=True)
class HistoricalContext:
    """종합 역사적 맥락 — 위기 + 호황 양방향."""

    hySpike: HYSpikeHistory | None = None
    yieldCurveInversion: YCInversionHistory | None = None
    unemploymentBounce: URBounceHistory | None = None
    cpiAcceleration: dict | None = None
    simultaneousWarnings: SimultaneousWarnings | None = None
    bullishSignals: BullishSignals | None = None
    hyCompression: HYCompressionHistory | None = None
    historicalEvents: list[HistoricalEvent] | None = None
    suggestedScenario: str | None = None
    suggestedScenarioReason: str | None = None
    riskLevel: str | None = None
    riskLabel: str | None = None
    opportunityLevel: str | None = None
    opportunityLabel: str | None = None
    description: str = ""
    status: str = "unavailable"
    observedInputs: int = 0
    totalInputs: int = 8


__all__ = [
    "BullishSignals",
    "HYCompressionHistory",
    "HYSpikeHistory",
    "HistoricalContext",
    "HistoricalEvent",
    "SimultaneousWarnings",
    "URBounceHistory",
    "YCInversionHistory",
]
