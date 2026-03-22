"""ESG 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EsgPillar:
    """E/S/G 개별 pillar 결과."""

    name: str  # "E", "S", "G"
    label: str  # "환경", "사회", "지배구조"
    score: float  # 0~100
    grade: str  # A~E
    metrics: dict  # 개별 메트릭 값
    details: list[str]  # 상세 분석 문장


@dataclass
class EsgResult:
    """ESG 종합 결과."""

    stockCode: str
    corpName: str | None

    environment: EsgPillar
    social: EsgPillar
    governance: EsgPillar

    totalScore: float  # 가중 평균 (E 30%, S 30%, G 40%)
    totalGrade: str

    @property
    def grades(self) -> dict[str, str]:
        return {
            "E": self.environment.grade,
            "S": self.social.grade,
            "G": self.governance.grade,
            "total": self.totalGrade,
        }


def _grade_from_score(score: float) -> str:
    """점수 → 등급."""
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "E"
