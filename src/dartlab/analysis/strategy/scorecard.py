"""2-5 종합 평가 -- 8영역 스코어카드, Piotroski, 종합 플래그."""

from __future__ import annotations

_GRADE_MAP = {
    "performance": "성장성",
    "profitability": "수익성",
    "health": "안정성",
    "cashflow": "현금흐름",
}


def calcScorecard(company) -> dict | None:
    """8영역 등급 요약.

    기존 5영역(수익성/성장성/안정성/효율성/현금흐름)
    + 이익품질/투자효율/재무정합성.
    """
    insights = getattr(company, "insights", None)

    items = []
    if insights is not None:
        grades = insights.grades()
        if grades:
            for eng, kor in _GRADE_MAP.items():
                grade = grades.get(eng)
                if grade:
                    items.append({"area": kor, "grade": grade})

    # 효율성은 ratioSeries 기반으로 직접 판정
    effGrade = _calcEfficiencyGrade(company)
    if effGrade:
        items.append({"area": "효율성", "grade": effGrade})

    # 이익품질
    eqGrade = _calcEarningsQualityGrade(company)
    if eqGrade:
        items.append({"area": "이익품질", "grade": eqGrade})

    # 투자효율
    invGrade = _calcInvestmentGrade(company)
    if invGrade:
        items.append({"area": "투자효율", "grade": invGrade})

    # 재무정합성
    csGrade = _calcCrossStatementGrade(company)
    if csGrade:
        items.append({"area": "재무정합성", "grade": csGrade})

    if not items:
        return None

    return {"items": items, "profile": getattr(insights, "profile", "") if insights else ""}


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


def _calcEarningsQualityGrade(company) -> str | None:
    """이익품질 등급 — 발생액비율 + M-Score 기반."""
    try:
        from dartlab.analysis.strategy.earningsQuality import calcAccrualAnalysis, calcBeneishTimeline

        accrual = calcAccrualAnalysis(company)
        beneish = calcBeneishTimeline(company)

        score = 0  # 0~100 (높을수록 좋음)
        count = 0

        if accrual and accrual["history"]:
            sar = accrual["history"][0].get("sloanAccrualRatio")
            if sar is not None:
                # 낮은 발생액 = 좋음
                if abs(sar) < 0.05:
                    score += 100
                elif abs(sar) < 0.10:
                    score += 70
                elif abs(sar) < 0.15:
                    score += 40
                else:
                    score += 10
                count += 1

            ocfNi = accrual["history"][0].get("ocfToNi")
            if ocfNi is not None:
                if ocfNi > 100:
                    score += 100
                elif ocfNi > 70:
                    score += 80
                elif ocfNi > 40:
                    score += 50
                else:
                    score += 20
                count += 1

        if beneish and beneish["history"]:
            ms = beneish["history"][0].get("mScore")
            if ms is not None:
                if ms < -2.22:
                    score += 100
                elif ms < -1.78:
                    score += 60
                else:
                    score += 20
                count += 1

        if count == 0:
            return None
        avg = score / count
        if avg >= 80:
            return "A"
        if avg >= 60:
            return "B"
        if avg >= 40:
            return "C"
        if avg >= 20:
            return "D"
        return "F"
    except (ImportError, AttributeError, TypeError, ValueError):
        return None


def _calcInvestmentGrade(company) -> str | None:
    """투자효율 등급 — ROIC-WACC Spread 기반."""
    try:
        from dartlab.analysis.strategy.investmentAnalysis import calcRoicTimeline

        result = calcRoicTimeline(company)
        if result is None or not result["history"]:
            return None

        h0 = result["history"][0]
        spread = h0.get("spread")
        if spread is None:
            return None

        if spread > 5:
            return "A"
        if spread > 2:
            return "B"
        if spread > 0:
            return "C"
        if spread > -3:
            return "D"
        return "F"
    except (ImportError, AttributeError, TypeError, ValueError):
        return None


def _calcCrossStatementGrade(company) -> str | None:
    """재무정합성 등급 — anomalyScore 기반."""
    try:
        from dartlab.analysis.strategy.crossStatement import calcAnomalyScore

        result = calcAnomalyScore(company)
        if result is None or not result["history"]:
            return None

        h0 = result["history"][0]
        anomalyScore = h0.get("score", 0)

        # 낮을수록 좋음
        if anomalyScore < 15:
            return "A"
        if anomalyScore < 30:
            return "B"
        if anomalyScore < 50:
            return "C"
        if anomalyScore < 70:
            return "D"
        return "F"
    except (ImportError, AttributeError, TypeError, ValueError):
        return None


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
    """전체 경고/기회 요약 -- 8영역 플래그 수집."""
    flags: list[str] = []

    from dartlab.analysis.strategy.efficiency import calcEfficiencyFlags
    from dartlab.analysis.strategy.growthAnalysis import calcGrowthFlags
    from dartlab.analysis.strategy.profitability import calcProfitabilityFlags
    from dartlab.analysis.strategy.stability import calcStabilityFlags

    flags.extend(calcProfitabilityFlags(company))
    flags.extend(calcGrowthFlags(company))
    flags.extend(calcStabilityFlags(company))
    flags.extend(calcEfficiencyFlags(company))

    # 새 영역 플래그
    try:
        from dartlab.analysis.strategy.earningsQuality import calcEarningsQualityFlags

        flags.extend(calcEarningsQualityFlags(company))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.strategy.investmentAnalysis import calcInvestmentFlags

        flags.extend(calcInvestmentFlags(company))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.strategy.crossStatement import calcCrossStatementFlags

        flags.extend(calcCrossStatementFlags(company))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.strategy.costStructure import calcCostStructureFlags

        flags.extend(calcCostStructureFlags(company))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.strategy.capitalAllocation import calcCapitalAllocationFlags

        flags.extend(calcCapitalAllocationFlags(company))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.strategy.taxAnalysis import calcTaxFlags

        flags.extend(calcTaxFlags(company))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    return flags
