"""2-5 종합 평가 -- 8영역 스코어카드, Piotroski, 종합 플래그."""

from __future__ import annotations

from dartlab.core.memory import memoizedCalc

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


@memoizedCalc
def calcScorecard(company, *, basePeriod: str | None = None) -> dict | None:
    """8영역 등급 요약.

    기존 5영역(수익성/성장성/안정성/효율성/현금흐름)
    + 이익품질/투자효율/재무정합성.

    Capabilities:
        - 8 영역 grade 산출 + 종합 profile 라벨.

    Guide:
        insights.grades + 별도 4 종 헬퍼 등급을 한 dict 로 합성.

    When:
        "한 화면에 종합 등급" 요약 카드가 필요할 때.

    How:
        analyzeFinancial → grades → 헬퍼 4 등급 보강 → items list.

    Requires:
        company.stockCode + analyzeFinancial 가능 (insights pipeline).

    Raises:
        없음 (None 반환).

    Example:
        >>> calcScorecard(c)
        {"items": [{"area": "수익성", "grade": "A"}, ...], "profile": "premium"}

    See Also:
        - calcSummaryFlags : 등급 ↦ 문장 요약
        - calcPiotroskiDetail : 9 점 표 세부

    AIContext:
        AI 답변 "종합 평가" 헤더 카드 색상/라벨 결정에 사용.

    Returns
    -------
    dict
        items : list[dict] — 영역별 등급
            area : str — 영역명
            grade : str — 등급 ("A" | "B" | "C" | "D" | "F")
        profile : str — 종합 프로필 ("premium" | "average" | "weak")
    """
    # insights — analyze() 직접 호출 (c.insights 는 P3 에서 제거됨)
    insights = None
    cacheKey = "_insights_analyze"
    cache = getattr(company, "_cache", None)
    cacheHit = False
    if cache is not None:
        lookup = getattr(cache, "lookup", None)
        if callable(lookup):
            cacheHit, insights = lookup(cacheKey)
        elif cacheKey in cache:
            cacheHit, insights = True, cache[cacheKey]
    if not cacheHit:
        try:
            from dartlab.analysis.financial.insight.pipeline import analyzeFinancial

            insights = analyzeFinancial(company.stockCode, company=company)
            if cache is not None:
                cache[cacheKey] = insights
        except (ImportError, ValueError, KeyError, AttributeError, TypeError, RuntimeError, OSError):
            insights = None

    # 금융업 판별
    sector = getattr(company, "sector", None)
    isFinancial = False
    if sector:
        sectorVal = getattr(sector, "sector", None)
        if sectorVal and hasattr(sectorVal, "value") and sectorVal.value == "금융":
            isFinancial = True

    items = []
    if insights is not None:
        grades = insights.grades()
        if grades:
            for eng, kor in _GRADE_MAP.items():
                grade = grades.get(eng)
                if grade:
                    # 금융업: 안정성/효율성은 제조업 기준 부적합 → 등급 미표시
                    if isFinancial and kor in ("안정성", "효율성"):
                        continue
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
        result = company._ratioSeries()
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


@memoizedCalc
def calcPiotroskiDetail(company, *, basePeriod: str | None = None) -> dict | None:
    """Piotroski F-Score 9개 항목 상세.

    Capabilities:
        - Piotroski 9 신호 component 별 pass/fail + 총점.

    Guide:
        F-Score 0~9 — 8 이상 quality, 2 이하 distressed 신호.

    When:
        "건전성 9 칸 체크리스트" 카드 출력 시.

    How:
        company._buildFinanceSeries(Y) → calcPiotroski → 라벨 매핑.

    Requires:
        annual finance series 가용해야 동작.

    Raises:
        없음 (예외 시 None).

    Example:
        >>> calcPiotroskiDetail(c)["total"]
        7

    See Also:
        - calcScorecard : 8 영역 등급 묶음
        - research.scoring.calcPiotroski : 원본 계산

    AIContext:
        AI 답변 "F-Score 7/9" 칸 차트 데이터로 사용.

    Returns
    -------
    dict
        total : int — 총점 (점, 0~9)
        interpretation : str — 해석 문구
        items : list[dict] — 9개 신호별 결과
            signal : str — 신호명
            pass : bool — 충족 여부
    """
    try:
        annual = company._buildFinanceSeries(freq="Y")
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


@memoizedCalc
def calcPiotroskiTimeline(company, *, basePeriod: str | None = None) -> dict | None:
    """Piotroski F-Score 시계열 — 매 annual period 0~9 점.

    Capabilities:
        - 기존 calcPiotroski (단일 시점) 의 시계열 wrapper.
        - 각 평가 시점 i 에서 series 의 [:i+1] 슬라이스로 calcPiotroski 호출.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 3 키
              (period, score, breakdown: dict[str, bool] — 9 components).

    Example:
        >>> r = calcPiotroskiTimeline(Company("005930"))
        >>> r["history"][-1]
        {"period": "2024", "score": 7, "breakdown": {"roaPositive": True, ...}}

    Guide:
        score ≥ 7 = strong, 4~6 = moderate, ≤ 3 = weak (Piotroski 2000).
        시계열 추세 ↑ = 펀더멘털 개선, ↓ = 악화 신호.

    Requires:
        annual 시계열 ≥ 2 년 (i ≥ 1 부터 평가).

    SeeAlso:
        - calcPiotroskiDetail : 단일 시점 9 신호 상세
        - research._scoringDescriptive.calcPiotroski : 원본 계산

    AIContext:
        시계열 추세 + 최근 점수 함께 인용. 단일 점수만 인용 금지.
    """
    try:
        annual = company._buildFinanceSeries(freq="Y")
    except (ValueError, KeyError, AttributeError):
        return None
    if annual is None:
        return None
    aSeries, aYears = annual
    if not aYears or len(aYears) < 2:
        return None

    from dartlab.analysis.financial.research._scoringDescriptive import calcPiotroski

    history: list[dict] = []
    nYears = len(aYears)
    # i ∈ [1, n-1]: i=0 은 비교 prev 없어 skip. 매 i 에서 series 를 [:i+1] 로 슬라이스 후 calcPiotroski 호출
    # (calcPiotroski 가 _latest / _latestTwo 로 마지막 2 점만 보므로 동일 결과).
    for i in range(1, nYears):
        sliced: dict = {}
        for sheet, accs in aSeries.items():
            if not isinstance(accs, dict):
                continue
            sliced[sheet] = {}
            for acc, vals in accs.items():
                if isinstance(vals, list):
                    sliced[sheet][acc] = vals[: i + 1]
        try:
            score = calcPiotroski(sliced)
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        history.append(
            {
                "period": str(aYears[i]),
                "score": score.total,
                "breakdown": dict(score.components),
            }
        )

    return {"history": history} if history else None


@memoizedCalc
def calcSummaryFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """전체 경고/기회 요약 -- 8영역 플래그 수집.

    Capabilities:
        - 8 영역 flag 함수 결과를 단일 리스트로 합성.

    Guide:
        도메인별 calc*Flags 호출 → 하나의 인사이트 리스트.

    When:
        대시보드 상단 "주요 신호" 카드 1 회 출력 시.

    How:
        profitability/growth/stability/efficiency/eq/inv/cs flags 모음.

    Requires:
        하위 flag 함수들이 import 가능.

    Raises:
        없음 (개별 영역 실패는 try/except 흡수).

    Example:
        >>> calcSummaryFlags(c)
        ["영업이익률 3기 연속 하락 ...", ...]

    See Also:
        - calcScorecard : 등급 dict
        - 도메인별 calc*Flags

    AIContext:
        AI 답변 "이번 분기 주목 신호" 카드의 원천 텍스트.

    Returns
    -------
    list[str]
        경고/기회 메시지 목록
    """
    flags: list[str] = []

    from dartlab.analysis.financial.efficiency import calcEfficiencyFlags
    from dartlab.analysis.financial.growthAnalysis import calcGrowthFlags
    from dartlab.analysis.financial.profitability import calcProfitabilityFlags
    from dartlab.analysis.financial.stability import calcStabilityFlags

    flags.extend(calcProfitabilityFlags(company, basePeriod=basePeriod))
    flags.extend(calcGrowthFlags(company, basePeriod=basePeriod))

    # calcStabilityFlags, calcEarningsQualityFlags: dict 반환 → flags 키 추출
    stabResult = calcStabilityFlags(company, basePeriod=basePeriod)
    if isinstance(stabResult, dict):
        flags.extend(stabResult.get("flags", []))
    elif isinstance(stabResult, list):
        flags.extend(stabResult)

    flags.extend(calcEfficiencyFlags(company, basePeriod=basePeriod))

    # 새 영역 플래그
    try:
        from dartlab.analysis.financial.earningsQuality import calcEarningsQualityFlags

        eqResult = calcEarningsQualityFlags(company, basePeriod=basePeriod)
        if isinstance(eqResult, dict):
            flags.extend(eqResult.get("flags", []))
        elif isinstance(eqResult, list):
            flags.extend(eqResult)
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
