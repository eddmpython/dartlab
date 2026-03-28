"""순주주환원 분류 — 환원형 / 중립 / 희석형."""

from __future__ import annotations


def classify_return(
    has_dividend: bool,
    has_buyback: bool,
    recent_increase: bool,
) -> tuple[str, bool]:
    """순주주환원 방향 분류.

    Returns:
        (분류, 모순형여부)
        분류: "적극환원" / "환원형" / "중립" / "희석형"
        모순형: 배당하면서 최근 증자
    """
    return_score = 0
    if has_dividend:
        return_score += 1
    if has_buyback:
        return_score += 1
    if recent_increase:
        return_score -= 1

    if return_score >= 2:
        category = "적극환원"
    elif return_score >= 1:
        category = "환원형"
    elif return_score == 0:
        category = "중립"
    else:
        category = "희석형"

    contradiction = has_dividend and recent_increase
    return category, contradiction
