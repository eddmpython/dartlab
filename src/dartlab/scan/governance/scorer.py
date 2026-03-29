"""거버넌스 종합 등급 산출 (5축 = 100점).

배점: 지분(20) + 사외(25) + 보수(15) + 감사(25) + 분산(15)
"""

from __future__ import annotations


def score_ownership(pct: float | None) -> float:
    """최대주주 지분율 점수 (0~20). 30~50%가 최적."""
    if pct is None:
        return 10.0
    if 30 <= pct <= 50:
        return 20.0
    if 20 <= pct < 30 or 50 < pct <= 60:
        return 16.0
    if 10 <= pct < 20 or 60 < pct <= 70:
        return 12.0
    if pct < 10:
        return 4.0
    return 8.0  # 70%+


def score_outside_ratio(
    ratio: float | None,
    *,
    resign: int = 0,
    concurrent: int = 0,
) -> float:
    """사외이사 비율 점수 (0~25). 중도사임/겸직 페널티 포함."""
    if ratio is None:
        return 12.5

    if ratio >= 40:
        base = 25.0
    elif ratio >= 30:
        base = 22.0
    elif ratio >= 20:
        base = 18.0
    elif ratio >= 10:
        base = 14.0
    elif ratio > 0:
        base = 8.0
    else:
        base = 3.0

    penalty = 0.0
    if resign > 0:
        penalty += min(resign * 3, 6)
    if concurrent > 0:
        penalty += min(concurrent * 2, 4)

    return max(base - penalty, 0.0)


def score_pay_ratio(ratio: float | None) -> float:
    """pay ratio 점수 (0~15). 낮을수록 좋음."""
    if ratio is None:
        return 7.5
    if ratio <= 2:
        return 15.0
    if ratio <= 3:
        return 13.0
    if ratio <= 5:
        return 11.0
    if ratio <= 10:
        return 8.0
    if ratio <= 20:
        return 4.0
    return 1.0


def score_audit(opinion: str | None) -> float:
    """감사의견 점수 (0~25)."""
    if opinion is None or opinion == "":
        return 12.5
    if opinion == "적정의견":
        return 25.0
    if opinion == "한정의견":
        return 5.0
    return 0.0  # 부적정의견, 의견거절


def score_minority(pct: float | None) -> float:
    """소액주주 지분율 점수 (0~15). 높을수록 분산 양호."""
    if pct is None:
        return 7.5
    if pct >= 60:
        return 15.0
    if pct >= 50:
        return 13.0
    if pct >= 40:
        return 11.0
    if pct >= 30:
        return 8.0
    if pct >= 20:
        return 5.0
    return 2.0


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
