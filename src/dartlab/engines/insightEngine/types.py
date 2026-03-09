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
