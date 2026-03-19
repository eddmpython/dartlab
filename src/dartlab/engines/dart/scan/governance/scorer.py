"""거버넌스 종합 등급 산출 (4축 × 25점 = 100점)."""

from __future__ import annotations


def score_ownership(pct: float | None) -> float:
    """최대주주 지분율 점수 (0~25). 30~50%가 최적."""
    if pct is None:
        return 12.5
    if 30 <= pct <= 50:
        return 25.0
    if 20 <= pct < 30 or 50 < pct <= 60:
        return 20.0
    if 10 <= pct < 20 or 60 < pct <= 70:
        return 15.0
    if pct < 10:
        return 5.0
    return 10.0  # 70%+


def score_outside_ratio(ratio: float | None) -> float:
    """사외이사 비율 점수 (0~25)."""
    if ratio is None:
        return 12.5
    if ratio >= 40:
        return 25.0
    if ratio >= 30:
        return 22.0
    if ratio >= 20:
        return 18.0
    if ratio >= 10:
        return 14.0
    if ratio > 0:
        return 8.0
    return 3.0


def score_pay_ratio(ratio: float | None) -> float:
    """pay ratio 점수 (0~25). 낮을수록 좋음."""
    if ratio is None:
        return 12.5
    if ratio <= 2:
        return 25.0
    if ratio <= 3:
        return 22.0
    if ratio <= 5:
        return 18.0
    if ratio <= 10:
        return 14.0
    if ratio <= 20:
        return 8.0
    return 3.0


def score_audit(opinion: str | None) -> float:
    """감사의견 점수 (0~25)."""
    if opinion is None or opinion == "":
        return 12.5
    if opinion == "적정의견":
        return 25.0
    if opinion == "한정의견":
        return 5.0
    return 0.0  # 부적정의견, 의견거절


def grade(score: float) -> str:
    """총점 → A~E 등급."""
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "E"
