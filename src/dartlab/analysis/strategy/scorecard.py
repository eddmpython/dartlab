"""2-5 종합 평가 -- 스코어카드, Piotroski, 종합 플래그."""

from __future__ import annotations

_GRADE_MAP = {
    "performance": "성장성",
    "profitability": "수익성",
    "health": "안정성",
    "cashflow": "현금흐름",
}


def calcScorecard(company) -> dict | None:
    """5영역(수익성/성장성/안정성/효율성/현금흐름) 등급 요약."""
    insights = getattr(company, "insights", None)
    if insights is None:
        return None

    grades = insights.grades()
    if not grades:
        return None

    # 10영역 → 5영역 매핑 (review 2부 관점)
    items = []
    for eng, kor in _GRADE_MAP.items():
        grade = grades.get(eng)
        if grade:
            items.append({"area": kor, "grade": grade})

    # 효율성은 ratioSeries 기반으로 직접 판정
    effGrade = _calcEfficiencyGrade(company)
    if effGrade:
        items.append({"area": "효율성", "grade": effGrade})

    if not items:
        return None

    return {"items": items, "profile": getattr(insights, "profile", "")}


def _calcEfficiencyGrade(company) -> str | None:
    """총자산회전율 추세로 효율성 등급 산출."""
    try:
        result = company.finance.ratioSeries
        if result is None:
            return None
    except (ValueError, KeyError, AttributeError):
        return None

    data, _years = result
    tat = data.get("RATIO", {}).get("totalAssetTurnover", [])
    recent = [v for v in tat[-3:] if v is not None]
    if not recent:
        return None

    latest = recent[-1]
    improving = len(recent) >= 2 and recent[-1] >= recent[-2]

    if latest >= 1.0 and improving:
        return "A"
    if latest >= 0.7:
        return "B"
    if latest >= 0.4:
        return "C"
    if latest >= 0.2:
        return "D"
    return "F"


def calcPiotroskiDetail(company) -> dict | None:
    """Piotroski F-Score 9개 항목 상세."""
    try:
        annual = company.annual
        if annual is None:
            return None
    except (ValueError, KeyError, AttributeError):
        return None

    aSeries, _aYears = annual
    from dartlab.analysis.financial.research.scoring import calcPiotroski

    score = calcPiotroski(aSeries)

    labels = {
        "roaPositive": "ROA 양수",
        "ocfPositive": "영업CF 양수",
        "roaIncreasing": "ROA 개선",
        "cfGtNi": "CF > 순이익",
        "debtDecreasing": "장기부채 감소",
        "currentRatioUp": "유동비율 개선",
        "noNewShares": "주식 미발행",
        "grossMarginUp": "매출총이익률 개선",
        "assetTurnoverUp": "자산회전율 개선",
    }
    items = [{"signal": labels.get(k, k), "pass": v} for k, v in score.components.items()]

    return {
        "total": score.total,
        "interpretation": score.interpretation,
        "items": items,
    }


def calcSummaryFlags(company) -> list[str]:
    """전체 경고/기회 요약 -- 다른 영역 플래그 수집."""
    flags: list[str] = []

    from dartlab.analysis.strategy.efficiency import calcEfficiencyFlags
    from dartlab.analysis.strategy.growthAnalysis import calcGrowthFlags
    from dartlab.analysis.strategy.profitability import calcProfitabilityFlags
    from dartlab.analysis.strategy.stability import calcStabilityFlags

    flags.extend(calcProfitabilityFlags(company))
    flags.extend(calcGrowthFlags(company))
    flags.extend(calcStabilityFlags(company))
    flags.extend(calcEfficiencyFlags(company))

    return flags
