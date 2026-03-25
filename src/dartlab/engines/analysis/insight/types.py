"""인사이트 엔진 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Flag:
    """리스크/기회 플래그."""

    level: str
    category: str
    text: str


@dataclass
class InsightResult:
    """단일 영역 분석 결과."""

    grade: str
    summary: str
    details: list[str] = field(default_factory=list)
    risks: list[Flag] = field(default_factory=list)
    opportunities: list[Flag] = field(default_factory=list)


@dataclass
class Anomaly:
    """이상치 탐지 결과."""

    severity: str
    category: str
    text: str
    value: Optional[float] = None


@dataclass
class ModelScore:
    """개별 부실 모델 결과 — 원시 값 + 판정 + 근거."""

    name: str  # "Ohlson O-Score"
    rawValue: float  # -5.23
    displayValue: str  # "P(부도) 0.5%" 또는 "Z'' = 6.42"
    zone: str  # "safe" / "gray" / "distress"
    interpretation: str  # "부도 확률 극히 낮음."
    reference: str  # "Ohlson (1980), 9변수 로지스틱"

    def __repr__(self) -> str:
        return f"{self.name:<20s} {self.displayValue:<16s} {self.zone:<10s} {self.interpretation}"


@dataclass
class DistressAxis:
    """스코어카드 단일 축 — 점수 + 구성 모델 상세."""

    name: str  # "정량 분석"
    score: float  # 0~100
    weight: float  # 0.40
    models: list[ModelScore] = field(default_factory=list)
    summary: str = ""

    def __repr__(self) -> str:
        pct = int(self.weight * 100)
        header = f"[{self.name}] {self.score:.1f}/100 (가중 {pct}%)"
        if not self.models:
            return f"{header}\n  {self.summary}"
        lines = [header]
        for m in self.models:
            lines.append(f"  {m}")
        return "\n".join(lines)


@dataclass
class AuditDataForAnomaly:
    """감사 탐지기 입력 DTO.

    pipeline이 Company에서 추출하여 anomaly에 전달.
    각 필드는 연도별 시계열 (최신이 마지막).
    """

    auditors: list[str | None] = field(default_factory=list)  # 감사인명 시계열
    opinions: list[str | None] = field(default_factory=list)  # 감사의견 시계열
    fees: list[float | None] = field(default_factory=list)  # 감사보수 시계열 (백만원)
    kamCounts: list[int | None] = field(default_factory=list)  # KAM 건수 시계열
    hasGoingConcern: bool = False  # 계속기업 불확실성 여부 (최신기)
    hasInternalControlWeakness: bool = False  # 내부통제 취약점 여부 (최신기)


@dataclass
class MarketDataForDistress:
    """시장 기반 부실 분석 입력 데이터.

    gather 엔진에서 수집한 시장 데이터를 pipeline에 전달하기 위한 DTO.
    pipeline이 직접 gather를 호출하지 않고, 호출자가 준비하여 전달.
    """

    marketCap: float  # 시가총액 (원)
    dailyReturns: list[float]  # 일별 수익률 (최소 60일 권장)
    riskFreeRate: float = 0.035  # 무위험이자율 (3.5%)


@dataclass
class DistressResult:
    """부실 예측 종합 스코어카드.

    5축 가중 평균 (100점 만점, 0=안전 100=위험):
    - 정량 분석 (30%): O-Score, Z''-Score, Z-Score  [Merton 있을 때, 없으면 40%]
    - 시장 기반 (20%): Merton D2D + PD               [Merton 없으면 0%]
    - 이익 품질 (15%): Beneish M-Score, Sloan Accrual, Piotroski F-Score  [없으면 20%]
    - 추세 분석 (25%): 연속적자, ICR<1, CCC 확대 등    [없으면 30%]
    - 감사 위험 (10%): 비적정 의견 등

    Merton 미제공 시 기존 4축(40/20/30/10) 그대로 동작 (하위호환 100%).
    금융업(isFinancial=True) → Merton 무시 (은행 부채 구조적 왜곡).

    레벨: safe(<15), watch(<30), warning(<50), danger(<70), critical(>=70)
    신용등급: AAA~D (S&P PD 매핑)
    """

    # 종합 판정
    level: str  # safe/watch/warning/danger/critical
    overall: float  # 0~100
    creditGrade: str  # AAA~D
    creditDescription: str  # "투자적격 최상위" 등

    # 축 상세 (4축 또는 5축)
    axes: list[DistressAxis] = field(default_factory=list)

    # 유동성 경보
    cashRunwayMonths: Optional[float] = None
    liquidityAlert: Optional[str] = None

    # 핵심 위험 요인
    riskFactors: list[str] = field(default_factory=list)

    # 메타
    modelCount: int = 0
    dataQuality: str = "충분"

    def __repr__(self) -> str:
        lines = [
            "=== 부실 예측 스코어카드 ===",
            f"종합: {self.level} ({self.overall:.1f}/100) | 신용등급: {self.creditGrade} ({self.creditDescription})",
            "",
        ]
        for axis in self.axes:
            lines.append(repr(axis))
            lines.append("")

        if self.liquidityAlert:
            runway = f"{self.cashRunwayMonths:.0f}개월" if self.cashRunwayMonths and self.cashRunwayMonths < 900 else ""
            lines.append(f"유동성: {self.liquidityAlert} {runway}".strip())

        if self.riskFactors:
            lines.append("위험 요인:")
            for rf in self.riskFactors:
                lines.append(f"  - {rf}")
        else:
            lines.append("위험 요인: 없음")

        lines.append(f"모델 {self.modelCount}개 사용, 데이터 품질: {self.dataQuality}")
        return "\n".join(lines)


@dataclass
class AnalysisResult:
    """종합 분석 결과."""

    corpName: str
    stockCode: str
    isFinancial: bool

    performance: InsightResult
    profitability: InsightResult
    health: InsightResult
    cashflow: InsightResult
    governance: InsightResult
    risk: InsightResult
    opportunity: InsightResult

    predictability: Optional[InsightResult] = None
    uncertainty: Optional[InsightResult] = None
    coreEarnings: Optional[InsightResult] = None

    anomalies: list[Anomaly] = field(default_factory=list)
    distress: Optional[DistressResult] = None
    summary: str = ""
    profile: str = ""

    def grades(self) -> dict[str, str]:
        """10영역 등급 dict 반환."""
        result = {
            "performance": self.performance.grade,
            "profitability": self.profitability.grade,
            "health": self.health.grade,
            "cashflow": self.cashflow.grade,
            "governance": self.governance.grade,
            "risk": self.risk.grade,
            "opportunity": self.opportunity.grade,
        }
        if self.predictability:
            result["predictability"] = self.predictability.grade
        if self.uncertainty:
            result["uncertainty"] = self.uncertainty.grade
        if self.coreEarnings:
            result["coreEarnings"] = self.coreEarnings.grade
        return result

    def __repr__(self):
        g = self.grades()
        gradeStr = " ".join(f"{k[:4]}={v}" for k, v in g.items())
        anomalyStr = f" anomalies={len(self.anomalies)}" if self.anomalies else ""
        return f"AnalysisResult({self.corpName}, {gradeStr}{anomalyStr})"
