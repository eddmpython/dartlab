"""종합 요약 텍스트 + 프로필 분류."""

from __future__ import annotations

from typing import Optional

from dartlab.engines.insight.types import Anomaly, InsightResult

GRADE_SCORE = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0, "N": None}


def _josa(word: str, withBatchim: str, withoutBatchim: str) -> str:
    if not word:
        return word + withBatchim
    lastChar = ord(word[-1])
    if 0xAC00 <= lastChar <= 0xD7A3:
        hasBatchim = (lastChar - 0xAC00) % 28 != 0
        return word + (withBatchim if hasBatchim else withoutBatchim)
    return word + withBatchim


def _eunNeun(word: str) -> str:
    return _josa(word, "은", "는")


def _iGa(word: str) -> str:
    return _josa(word, "이", "가")


def _avgGrade(grades: dict[str, str]) -> float:
    scores = [GRADE_SCORE[g] for g in grades.values() if GRADE_SCORE.get(g) is not None]
    if not scores:
        return 0
    return sum(scores) / len(scores)


def classifyProfile(grades: dict[str, str]) -> str:
    """등급 조합으로 기업 프로필 분류."""
    avgScore = _avgGrade(grades)
    perf = grades.get("performance", "C")
    profit = grades.get("profitability", "C")
    health = grades.get("health", "C")
    risk = grades.get("risk", "C")
    opp = grades.get("opportunity", "C")

    if avgScore >= 3.0 and risk in ("A", "B"):
        return "premium"
    if perf in ("A", "B") and profit in ("A", "B") and opp in ("A", "B"):
        return "growth"
    if health in ("A", "B") and risk in ("A", "B") and profit in ("A", "B"):
        return "stable"
    if risk in ("D", "F") or health == "F":
        return "caution"
    if avgScore < 1.5:
        return "distress"
    return "mixed"


def _getStrengths(insights: dict[str, InsightResult]) -> list[str]:
    strengths = []
    mapping = {
        "performance": "실적",
        "profitability": "수익성",
        "health": "재무건전성",
        "cashflow": "현금흐름",
        "governance": "지배구조",
    }
    for key, label in mapping.items():
        if key in insights and insights[key].grade == "A":
            strengths.append(label)
    return strengths


def _getWeaknesses(insights: dict[str, InsightResult]) -> list[str]:
    weaknesses = []
    mapping = {
        "performance": "실적",
        "profitability": "수익성",
        "health": "재무건전성",
        "cashflow": "현금흐름",
        "governance": "지배구조",
    }
    for key, label in mapping.items():
        if key in insights and insights[key].grade == "F":
            weaknesses.append(label)
    return weaknesses


def _getKeyMetric(insights: dict[str, InsightResult]) -> Optional[str]:
    for key in ("performance", "profitability"):
        if key in insights:
            for detail in insights[key].details:
                for keyword in ("성장", "이익률", "ROE"):
                    if keyword in detail:
                        return detail
    return None


def generateSummary(
    corpName: str,
    insights: dict[str, InsightResult],
    anomalies: list[Anomaly],
    profile: str,
) -> str:
    """한국어 종합 요약 생성."""
    strengths = _getStrengths(insights)
    weaknesses = _getWeaknesses(insights)
    keyMetric = _getKeyMetric(insights)

    parts: list[str] = []
    nameEunNeun = _eunNeun(corpName)

    if profile == "premium":
        if strengths:
            parts.append(f"{nameEunNeun} {', '.join(strengths)} 등 전반적으로 우수한 재무 상태를 보이는 우량 기업입니다.")
        else:
            parts.append(f"{nameEunNeun} 전반적으로 우수한 재무 상태를 보이는 우량 기업입니다.")

    elif profile == "growth":
        parts.append(f"{nameEunNeun} 성장성과 수익성이 돋보이는 기업입니다.")

    elif profile == "stable":
        parts.append(f"{nameEunNeun} 안정적인 재무구조를 갖춘 기업입니다.")

    elif profile == "caution":
        if weaknesses:
            parts.append(f"{nameEunNeun} {', '.join(weaknesses)} 측면에서 주의가 필요합니다.")
        else:
            grades = {k: v.grade for k, v in insights.items()}
            riskGrade = grades.get("risk", "C")
            if riskGrade in ("D", "F"):
                parts.append(f"{nameEunNeun} 재무 리스크 요인이 존재하여 주의가 필요합니다.")
            else:
                parts.append(f"{nameEunNeun} 일부 재무 지표에서 주의가 필요합니다.")

    elif profile == "distress":
        parts.append(f"{nameEunNeun} 여러 재무 지표에서 개선이 시급한 상황입니다.")

    else:
        if strengths and weaknesses:
            parts.append(f"{nameEunNeun} {', '.join(strengths)} 양호하나 {', '.join(weaknesses)}에서 약점을 보입니다.")
        elif strengths:
            if len(strengths) == 1:
                parts.append(f"{nameEunNeun} {_iGa(strengths[0])} 양호한 기업입니다.")
            else:
                front = ", ".join(strengths[:-1])
                parts.append(f"{nameEunNeun} {front}, {_iGa(strengths[-1])} 양호한 기업입니다.")
        else:
            parts.append(f"{nameEunNeun} 전반적으로 보통 수준의 재무 상태를 보입니다.")

    if keyMetric:
        parts.append(keyMetric + ".")

    dangerAnomalies = [a for a in anomalies if a.severity == "danger"]
    if dangerAnomalies:
        topAnomaly = dangerAnomalies[0].text.split("—")[0].strip()
        parts.append(f"다만 {topAnomaly} 점에 유의해야 합니다.")
    elif len(anomalies) >= 3:
        parts.append(f"이상 신호 {len(anomalies)}건이 감지되어 모니터링이 필요합니다.")

    return " ".join(parts)
