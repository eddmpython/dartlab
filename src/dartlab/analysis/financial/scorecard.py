"""2-5 종합 평가 -- 8영역 스코어카드, Piotroski, 종합 플래그."""

from __future__ import annotations

_GRADE_MAP = {
    "performance": "성장성",
    "profitability": "수익성",
    "health": "안정성",
    "cashflow": "현금흐름",
}


def _sectorRelativeScore(company, value: float, metric: str) -> int:
    """섹터 분포 기준 상대 점수 (0~4).

    Q3 초과 → 4(A), 중앙값~Q3 → 3(B), Q1~중앙값 → 2(C),
    Q1 미만이면서 양수 → 1(D), 음수 → 0(F).
    벤치마크가 없으면 절대 기준 fallback.
    """
    try:
        from dartlab.analysis.financial.insight.benchmark import getBenchmark

        sector = company.sector
        if sector is not None:
            bm = getBenchmark(sector.sector)
            median = getattr(bm, f"{metric}Median", None)
            q1 = getattr(bm, f"{metric}Q1", None)
            q3 = getattr(bm, f"{metric}Q3", None)
            if median is not None and q1 is not None and q3 is not None:
                if value >= q3:
                    return 4
                if value >= median:
                    return 3
                if value >= q1:
                    return 2
                if value > 0:
                    return 1
                return 0
    except (ValueError, KeyError, AttributeError):
        pass
    # fallback: 절대 기준
    if value > 0.15 if metric == "tat" else value > 10:
        return 3
    if value > 0:
        return 1
    return 0


def calcScorecard(company, *, basePeriod: str | None = None) -> dict | None:
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
    eqGrade = _calcEarningsQualityGrade(company, basePeriod=basePeriod)
    if eqGrade:
        items.append({"area": "이익품질", "grade": eqGrade})

    # 투자효율
    invGrade = _calcInvestmentGrade(company, basePeriod=basePeriod)
    if invGrade:
        items.append({"area": "투자효율", "grade": invGrade})

    # 재무정합성
    csGrade = _calcCrossStatementGrade(company, basePeriod=basePeriod)
    if csGrade:
        items.append({"area": "재무정합성", "grade": csGrade})

    if not items:
        return None

    return {"items": items, "profile": getattr(insights, "profile", "") if insights else ""}


def _calcEfficiencyGrade(company) -> str | None:
    """총자산회전율 추세로 효율성 등급 산출 — 섹터 상대 등급.

    업종별 TAT 분포(중앙값/사분위)를 기준으로 상대 위치 판정.
    추세 개선 시 +1 보너스.
    """
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

    # 섹터 상대 등급 (0~4)
    score = _sectorRelativeScore(company, latest, "tat")

    # 추세 개선 보너스 (+1)
    if improving:
        score = min(4, score + 1)

    return ["F", "D", "C", "B", "A"][score]


def _calcEarningsQualityGrade(company, *, basePeriod: str | None = None) -> str | None:
    """이익품질 등급 — 발생액비율 + M-Score 기반."""
    try:
        from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis, calcBeneishTimeline

        accrual = calcAccrualAnalysis(company, basePeriod=basePeriod)
        beneish = calcBeneishTimeline(company, basePeriod=basePeriod)

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


def _calcInvestmentGrade(company, *, basePeriod: str | None = None) -> str | None:
    """투자효율 등급 -- ROIC 섹터 상대 등급."""
    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

        result = calcRoicTimeline(company, basePeriod=basePeriod)
        if result is None or not result["history"]:
            return None

        h0 = result["history"][0]
        roic = h0.get("roic")
        if roic is None:
            return None

        # 섹터 상대 등급 (0~4)
        score = _sectorRelativeScore(company, roic, "roic")

        return ["F", "D", "C", "B", "A"][score]
    except (ImportError, AttributeError, TypeError, ValueError, KeyError):
        return None


def _calcCrossStatementGrade(company, *, basePeriod: str | None = None) -> str | None:
    """재무정합성 등급 — anomalyScore 기반."""
    try:
        from dartlab.analysis.financial.crossStatement import calcAnomalyScore

        result = calcAnomalyScore(company, basePeriod=basePeriod)
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


def calcPiotroskiDetail(company, *, basePeriod: str | None = None) -> dict | None:
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


def calcSummaryFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """전체 경고/기회 요약 -- 8영역 플래그 수집."""
    flags: list[str] = []

    from dartlab.analysis.financial.efficiency import calcEfficiencyFlags
    from dartlab.analysis.financial.growthAnalysis import calcGrowthFlags
    from dartlab.analysis.financial.profitability import calcProfitabilityFlags
    from dartlab.analysis.financial.stability import calcStabilityFlags

    flags.extend(calcProfitabilityFlags(company, basePeriod=basePeriod))
    flags.extend(calcGrowthFlags(company, basePeriod=basePeriod))
    flags.extend(calcStabilityFlags(company, basePeriod=basePeriod))
    flags.extend(calcEfficiencyFlags(company, basePeriod=basePeriod))

    # 새 영역 플래그
    try:
        from dartlab.analysis.financial.earningsQuality import calcEarningsQualityFlags

        flags.extend(calcEarningsQualityFlags(company, basePeriod=basePeriod))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.financial.investmentAnalysis import calcInvestmentFlags

        flags.extend(calcInvestmentFlags(company, basePeriod=basePeriod))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.financial.crossStatement import calcCrossStatementFlags

        flags.extend(calcCrossStatementFlags(company, basePeriod=basePeriod))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.financial.costStructure import calcCostStructureFlags

        flags.extend(calcCostStructureFlags(company, basePeriod=basePeriod))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.financial.capitalAllocation import calcCapitalAllocationFlags

        flags.extend(calcCapitalAllocationFlags(company, basePeriod=basePeriod))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    try:
        from dartlab.analysis.financial.taxAnalysis import calcTaxFlags

        flags.extend(calcTaxFlags(company, basePeriod=basePeriod))
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    return flags
