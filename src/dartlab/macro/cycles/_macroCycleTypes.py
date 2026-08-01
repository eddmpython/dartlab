"""macroCycle 결과 타입 — 11 dataclass + PHASE_LABELS.

macro/cycles/macroCycle.py 가 1182 줄 god module 이라 types 분리.
identity 보존을 위해 macroCycle.py 가 본 모듈에서 re-export 한다.

타입:
- CyclePhase — 4국면 판별 결과
- TransitionSignal — 사이클 전환 시퀀스 신호
- RateDecomposition — 장기금리 3요소 분해 (DKW 근사)
- GoldDrivers — 금 가격 3요인
- FxDrivers — 환율 3요인 분해
- MarketValuation — 시장 레벨 밸류에이션 (Buffett Indicator)
- VixRegime — VIX 구간 판정
- AssetSignal — 개별 자산 신호
- MultipleBand — 멀티플 정규분포 밴드
- CopperGoldSignal — 구리/금 비율 경기 선행
- RealRateRegimeResult — 실질금리 + BEI 4분면 분해
"""

from __future__ import annotations

from dataclasses import dataclass, field

PHASE_LABELS = {
    "contraction": "침체",
    "recovery": "회복",
    "expansion": "확장",
    "slowdown": "둔화",
}


@dataclass(frozen=True)
class CyclePhase:
    """경제 사이클 판별 결과."""

    phase: str | None
    label: str
    confidence: str
    signals: tuple[str, ...]
    sectorStrategy: dict[str, str] = field(default_factory=dict)
    status: str = "observed"
    observedInputs: int = 0
    totalInputs: int = 8

    def __repr__(self) -> str:
        return f"{self.label} ({self.confidence}) — {', '.join(self.signals[:3])}"


@dataclass(frozen=True)
class TransitionSignal:
    """사이클 전환 시퀀스 감지 결과."""

    fromPhase: str
    toPhase: str
    progress: int
    triggered: tuple[str, ...]
    pending: tuple[str, ...]
    sequenceOrder: tuple[tuple[str, str | None], ...] = ()
    orderValid: bool | None = None

    def __repr__(self) -> str:
        order_mark = "" if self.orderValid is None else (" ✓순서" if self.orderValid else " ✗역전")
        return f"{PHASE_LABELS.get(self.fromPhase, self.fromPhase)}→{PHASE_LABELS.get(self.toPhase, self.toPhase)} {self.progress}%{order_mark}"


@dataclass(frozen=True)
class RateDecomposition:
    """장기금리 3요소 분해 (DKW 근사)."""

    nominal: float
    expectedInflation: float
    realRate: float
    termPremium: float


@dataclass(frozen=True)
class GoldDrivers:
    """금 가격 3요인 해석."""

    realRateEffect: str
    dollarEffect: str
    safeHavenEffect: str
    dominant: str


@dataclass(frozen=True)
class FxDrivers:
    """환율 3요인 분해 해석."""

    rateDiffEffect: str
    tradeEffect: str
    riskEffect: str
    dominant: str
    divergence: str | None


@dataclass(frozen=True)
class MarketValuation:
    """시장 레벨 밸류에이션."""

    buffettIndicator: float
    zone: str
    zoneLabel: str
    description: str


@dataclass(frozen=True)
class VixRegime:
    """VIX 구간 판정."""

    level: float
    zone: str
    zoneLabel: str
    buySignal: int


@dataclass(frozen=True)
class AssetSignal:
    """개별 자산의 현재 신호."""

    asset: str
    label: str
    level: float | None
    change: float | None
    interpretation: str
    implication: str


@dataclass(frozen=True)
class MultipleBand:
    """멀티플 정규분포 밴드."""

    metric: str
    current: float
    mean: float
    std: float
    percentile: float
    zone: str
    zLabel: str


@dataclass(frozen=True)
class CopperGoldSignal:
    """구리/금 비율 경기 선행 신호."""

    ratio: float
    direction: str
    directionLabel: str
    implication: str
    description: str


@dataclass(frozen=True)
class RealRateRegimeResult:
    """실질금리 + 기대인플레이션 분해 결과."""

    realRate: float
    bei: float
    regime: str
    regimeLabel: str
    description: str


__all__ = [
    "AssetSignal",
    "CopperGoldSignal",
    "CyclePhase",
    "FxDrivers",
    "GoldDrivers",
    "MarketValuation",
    "MultipleBand",
    "PHASE_LABELS",
    "RateDecomposition",
    "RealRateRegimeResult",
    "TransitionSignal",
    "VixRegime",
]
