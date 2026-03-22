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
class DistressResult:
    """부실 예측 종합 스코어카드.

    4축 가중 평균 (100점 만점, 0=안전 100=위험):
    - 정량 분석 (40%): O-Score, Z''-Score, Z-Score
    - 이익 품질 (20%): Beneish M-Score, Sloan Accrual, Piotroski F-Score
    - 추세 분석 (30%): 연속적자, ICR<1, CCC 확대 등
    - 감사 위험 (10%): 비적정 의견 등

    레벨: safe(<15), watch(<30), warning(<50), danger(<70), critical(>=70)
    신용등급: AAA~D (S&P PD 매핑)
    """

    # 종합 판정
    level: str  # safe/watch/warning/danger/critical
    overall: float  # 0~100
    creditGrade: str  # AAA~D
    creditDescription: str  # "투자적격 최상위" 등

    # 4축 상세
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

    anomalies: list[Anomaly] = field(default_factory=list)
    distress: Optional[DistressResult] = None
    summary: str = ""
    profile: str = ""

    def grades(self) -> dict[str, str]:
        """7영역 등급 dict 반환."""
        return {
            "performance": self.performance.grade,
            "profitability": self.profitability.grade,
            "health": self.health.grade,
            "cashflow": self.cashflow.grade,
            "governance": self.governance.grade,
            "risk": self.risk.grade,
            "opportunity": self.opportunity.grade,
        }

    def __repr__(self):
        g = self.grades()
        gradeStr = " ".join(f"{k[:4]}={v}" for k, v in g.items())
        anomalyStr = f" anomalies={len(self.anomalies)}" if self.anomalies else ""
        return f"AnalysisResult({self.corpName}, {gradeStr}{anomalyStr})"
