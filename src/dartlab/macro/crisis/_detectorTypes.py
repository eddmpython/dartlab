"""macro/crisis/detectors 결과 타입 — 9 dataclass.

macro/crisis/detectors.py 가 999 줄 god module 이라 types 분리.
identity 보존을 위해 detectors.py 가 본 모듈에서 re-export 한다.

타입:
- CreditGapResult — Credit-to-GDP Gap (BIS Basel III)
- GHSResult — Greenwood-Hanson-Shleifer 금융위기 예측 점수
- RecessionDashboard — 침체 확률 종합 대시보드
- MinskyPhaseResult — Minsky 금융 불안정 5단계
- KooRecessionResult — Koo Balance Sheet Recession
- FisherDeflationResult — Fisher 부채-디플레이션
- KRHousingStressResult — 한국 부동산-금융 스트레스
- DalioPhaseResult — Dalio 부채사이클 단계
- DalioPolicyLeverResult — Dalio 정책 4 레버 소진도
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreditGapResult:
    """Credit-to-GDP Gap (BIS 방법)."""

    gap: float | None
    trend: float | None
    actual: float | None
    zone: str | None
    zoneLabel: str
    ccybBuffer: float | None
    description: str
    status: str = "usable"
    observedInputs: int = 1
    totalInputs: int = 1


@dataclass(frozen=True)
class GHSResult:
    """GHS 금융위기 예측 점수 (Greenwood-Hanson-Shleifer 2022).

    regime 확장 (Dalio): 같은 GHS 점수라도 실질금리에 따라
    deflationary (실질금리 높음 + 신용 수축) vs inflationary
    (실질금리 음수 + 신용 확장) 위기 성격이 다르다.
    """

    score: float
    zone: str
    zoneLabel: str
    components: dict[str, float]
    crisisProb: float
    description: str
    regime: str | None = None
    regimeLabel: str | None = None


@dataclass(frozen=True)
class RecessionDashboard:
    """침체 확률 종합 대시보드."""

    composite: float | None
    zone: str | None
    zoneLabel: str
    components: dict[str, float | None]
    historicalMatch: str | None
    description: str
    historicalFacts: dict | None = None
    status: str = "usable"
    observedInputs: int = 0
    totalInputs: int = 5


@dataclass(frozen=True)
class MinskyPhaseResult:
    """Minsky 금융 불안정 순환 5단계 판별."""

    phase: str | None
    phaseLabel: str | None
    confidence: str
    signals: list[str]
    description: str
    status: str = "usable"
    observedInputs: int = 0
    totalInputs: int = 6


@dataclass(frozen=True)
class KooRecessionResult:
    """Koo Balance Sheet Recession 감지."""

    privateSurplus: float
    policyRate: float
    isBSR: bool
    description: str


@dataclass(frozen=True)
class FisherDeflationResult:
    """Fisher 부채 디플레이션 위험 평가."""

    dsr: float
    nplRate: float | None
    cpiYoy: float
    risk: str
    riskLabel: str
    description: str


@dataclass(frozen=True)
class KRHousingStressResult:
    """한국 부동산-금융 스트레스 지표."""

    housePriceYoy: float
    householdDebtYoy: float | None
    stress: str
    stressLabel: str
    description: str


@dataclass(frozen=True)
class DalioPhaseResult:
    """Dalio 부채사이클 단계 (Big Debt Crises Part 1).

    subPhase 와 regimeVariant 는 phase 에 따라 선택적으로 채워진다:
    - subPhase: beautifulDeleveraging 상태에서만 4단계 (austerity/defaultRestructuring/
      moneyPrinting/wealthTransfer) 세분화
    - regimeVariant: deflationary | inflationary — 환율/기축통화/외화부채 기반
    """

    phase: str | None
    phaseLabel: str | None
    signals: list[str]
    description: str
    subPhase: str | None = None
    subPhaseLabel: str | None = None
    regimeVariant: str | None = None
    regimeVariantLabel: str | None = None
    status: str = "usable"
    observedInputs: int = 0
    totalInputs: int = 4


@dataclass(frozen=True)
class DalioPolicyLeverResult:
    """Dalio 정책 4 레버 소진도."""

    monetary: str
    fiscal: str
    credit: str
    fx: str
    exhaustionScore: int | None
    signals: list[str]
    status: str = "usable"
    observedInputs: int = 0
    totalInputs: int = 4


__all__ = [
    "CreditGapResult",
    "DalioPhaseResult",
    "DalioPolicyLeverResult",
    "FisherDeflationResult",
    "GHSResult",
    "KRHousingStressResult",
    "KooRecessionResult",
    "MinskyPhaseResult",
    "RecessionDashboard",
]
