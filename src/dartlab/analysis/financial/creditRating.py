"""3-6 신용평가 — 제도권 수준 신용등급 산출.

16개 정량 지표를 5축 가중평균으로 종합하여 20단계 신용등급(AAA~D)을 부여한다.
업종별 차등 기준표를 적용하여 같은 지표라도 업종에 따라 다르게 평가한다.

stability.py가 "추세 관찰"이라면, creditRating.py는 "등급 부여".
stability는 원인, creditRating은 결론이다.

학술 근거:
- Moody's Corporate Rating Methodology (2024): 스코어카드 선형 보간
- S&P Corporate Methodology (2024): 정량/정성 혼합
- KIS/KR/NICE 공개 방법론: 업종별 차등 기준
- Altman (1968), Ohlson (1980), Campbell et al. (2008)
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    MAX_RATIO_YEARS,
    annualColsFromPeriods,
    fetchNotesDetail,
    getRatios,
    getRatioSeries,
    toDict,
    toDictBySnakeId,
)
from dartlab.analysis.financial._memoize import memoized_calc

_MAX_YEARS = MAX_RATIO_YEARS


def _safe_div(a, b) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return round(a / abs(b) * 100, 2)


def _safe_ratio(a, b) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return round(a / abs(b), 2)


def _cv(values: list) -> float | None:
    """변동계수(Coefficient of Variation) — 표준편차/평균."""
    nums = [v for v in values if v is not None]
    if len(nums) < 3:
        return None
    mean = sum(nums) / len(nums)
    if mean == 0:
        return None
    variance = sum((x - mean) ** 2 for x in nums) / len(nums)
    std = variance**0.5
    return round(std / abs(mean) * 100, 2)


def _getSector(company):
    """company.sector에서 Sector enum 추출."""
    try:
        si = getattr(company, "sector", None)
        if si is not None:
            return si.sector
    except (AttributeError, ImportError):
        pass
    return None


def _isFinancial(company) -> bool:
    """금융업 여부."""
    try:
        sector = _getSector(company)
        if sector is not None:
            from dartlab.core.sector.types import Sector

            return sector == Sector.FINANCIALS
    except (AttributeError, ImportError):
        pass
    return False


# ═══════════════════════════════════════════════════════════
# calc 1: 신용평가 핵심 지표 시계열
# ═══════════════════════════════════════════════════════════


@memoized_calc
def calcCreditMetrics(company, *, basePeriod: str | None = None) -> dict | None:
    """신용평가 핵심 지표 16개를 5개년 시계열로 산출.

    4축 16개 지표:
    - 채무상환(4): FFO/총차입금, Debt/EBITDA, FOCF/Debt, EBITDA/이자비용
    - 레버리지(3): 부채비율, 차입금의존도, 순차입금/EBITDA
    - 유동성(3): 유동비율, 현금비율, 단기차입금비중
    - 현금흐름(3): OCF/매출, FCF/매출, OCF/총차입금
    - 이익안정성(3): 영업이익률CV, 매출변동계수, DOL
    """
    # BS 데이터
    bsResult = company.select(
        "BS",
        [
            "자산총계", "부채총계", "자본총계",
            "유동자산", "유동부채",
            "현금및현금성자산",
            "단기차입금", "장기차입금", "사채",
            "재고자산",
        ],
    )
    bsParsed = toDict(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed

    # IS 데이터
    isResult = company.select(
        "IS",
        ["매출액", "영업이익", "당기순이익", "금융비용", "이자비용", "감가상각비"],
    )
    isParsed = toDict(isResult)
    if isParsed is None:
        return None
    isData, _ = isParsed

    # CF 데이터
    cfResult = company.select(
        "CF",
        ["영업활동현금흐름", "투자활동현금흐름", "유형자산의취득"],
    )
    cfParsed = toDict(cfResult)
    cfData: dict = {}
    if cfParsed is not None:
        cfData, _ = cfParsed

    # CF snakeId fallback
    cfSnakeResult = company.select("CF", ["interest_paid", "capex"])
    cfSnakeParsed = toDictBySnakeId(cfSnakeResult)
    cfSnakeData: dict = {}
    if cfSnakeParsed is not None:
        cfSnakeData, _ = cfSnakeParsed

    # 행 추출
    ta = bsData.get("자산총계", {})
    tl = bsData.get("부채총계", {})
    eq = bsData.get("자본총계", {})
    ca = bsData.get("유동자산", {})
    cl = bsData.get("유동부채", {})
    cash = bsData.get("현금및현금성자산", {})
    stBorrow = bsData.get("단기차입금", {})
    ltBorrow = bsData.get("장기차입금", {})
    bonds = bsData.get("사채", {})
    inventory = bsData.get("재고자산", {})

    revenue = isData.get("매출액", {})
    opIncome = isData.get("영업이익", {})
    netIncome = isData.get("당기순이익", {})
    finCost = isData.get("금융비용", {})
    intCost = isData.get("이자비용", {})
    depreciation = isData.get("감가상각비", {})

    ocf = cfData.get("영업활동현금흐름", {})
    icf = cfData.get("투자활동현금흐름", {})
    capexRow = cfData.get("유형자산의취득", {})

    intPaid = cfSnakeData.get("interest_paid", {})
    capexSnake = cfSnakeData.get("capex", {})

    yCols = annualColsFromPeriods(bsPeriods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    opMargins = []

    for col in yCols[:-1]:
        # 기초 데이터
        totalAssets = ta.get(col)
        totalDebt = tl.get(col)
        equity = eq.get(col)
        curAssets = ca.get(col)
        curLiab = cl.get(col)
        cashVal = cash.get(col)
        inv = inventory.get(col)

        stb = stBorrow.get(col) or 0
        ltb = ltBorrow.get(col) or 0
        bnd = bonds.get(col) or 0
        totalBorrowing = stb + ltb + bnd

        rev = revenue.get(col)
        oi = opIncome.get(col)
        ni = netIncome.get(col)
        dep = depreciation.get(col)
        ocfVal = ocf.get(col)

        # 이자비용 (우선순위: IS이자비용 → CF이자지급 → IS금융비용)
        ie = intCost.get(col)
        if not ie:
            cfInt = intPaid.get(col)
            if cfInt:
                ie = abs(cfInt)
        if not ie:
            ie = finCost.get(col)

        # EBITDA 추정
        ebitda = None
        if oi is not None:
            ebitda = oi + (dep or 0)

        # FFO (Funds From Operations) = NI + 감가상각 (간이)
        # 감가상각 미제공 시 OCF를 FFO 대체 (보수적 근사)
        ffo = None
        if ni is not None and dep is not None:
            ffo = ni + dep
        elif ocfVal is not None:
            ffo = ocfVal  # fallback: OCF ≈ FFO

        # CAPEX
        capex = capexRow.get(col)
        if capex is None:
            capex = capexSnake.get(col)
        if capex is not None:
            capex = abs(capex)

        # FCF = OCF - CAPEX
        fcf = None
        if ocfVal is not None and capex is not None:
            fcf = ocfVal - capex

        # FOCF = FCF (Free Operating Cash Flow)
        focf = fcf

        # 순차입금
        netDebt = totalBorrowing - (cashVal or 0) if totalBorrowing > 0 else 0

        # ── 채무상환 지표 ──
        ffo_to_debt = _safe_div(ffo, totalBorrowing) if totalBorrowing > 0 else (999.0 if ffo and ffo > 0 else None)
        debt_to_ebitda = _safe_ratio(totalBorrowing, ebitda) if totalBorrowing > 0 else (0.0 if ebitda and ebitda > 0 else None)
        focf_to_debt = _safe_div(focf, totalBorrowing) if totalBorrowing > 0 else (999.0 if focf and focf > 0 else None)
        ebitda_interest = _safe_ratio(ebitda, ie) if ie and ie > 0 else (999.0 if ebitda and ebitda > 0 else None)

        # ── 레버리지 지표 ──
        debt_ratio = _safe_div(totalDebt, equity) if equity and equity > 0 else None
        borrowing_dep = _safe_div(totalBorrowing, totalAssets) if totalAssets and totalAssets > 0 else None
        net_debt_ebitda = _safe_ratio(netDebt, ebitda) if ebitda and ebitda > 0 else None

        # ── 유동성 지표 ──
        current_ratio = _safe_div(curAssets, curLiab) if curLiab and curLiab > 0 else None
        cash_ratio = _safe_div(cashVal, curLiab) if curLiab and curLiab > 0 else None
        st_debt_ratio = _safe_div(stb, totalBorrowing) if totalBorrowing > 0 else None

        # ── 현금흐름 지표 ──
        ocf_to_sales = _safe_div(ocfVal, rev) if rev and rev > 0 else None
        fcf_to_sales = _safe_div(fcf, rev) if rev and rev > 0 else None
        ocf_to_debt = _safe_div(ocfVal, totalBorrowing) if totalBorrowing > 0 else None

        # ── 이익안정성 (후처리에서 계산) ──
        opMargin = _safe_div(oi, rev) if rev and rev > 0 else None
        opMargins.append(opMargin)

        history.append({
            "period": col,
            # 원본
            "totalAssets": totalAssets,
            "totalBorrowing": totalBorrowing if totalBorrowing > 0 else None,
            "ebitda": ebitda,
            "ffo": ffo,
            "ocf": ocfVal,
            "fcf": fcf,
            # 채무상환
            "ffoToDebt": ffo_to_debt,
            "debtToEbitda": debt_to_ebitda,
            "focfToDebt": focf_to_debt,
            "ebitdaInterestCoverage": ebitda_interest,
            # 레버리지
            "debtRatio": debt_ratio,
            "borrowingDependency": borrowing_dep,
            "netDebtToEbitda": net_debt_ebitda,
            # 유동성
            "currentRatio": current_ratio,
            "cashRatio": cash_ratio,
            "shortTermDebtRatio": st_debt_ratio,
            # 현금흐름
            "ocfToSales": ocf_to_sales,
            "fcfToSales": fcf_to_sales,
            "ocfToDebt": ocf_to_debt,
        })

    if not history:
        return None

    # 이익안정성 지표 — 전체 기간 대상
    opMarginCV = _cv(opMargins)
    revValues = [revenue.get(col) for col in yCols[:-1]]
    revenueCV = _cv(revValues)

    result: dict = {
        "history": history,
        "stabilityMetrics": {
            "operatingMarginCV": opMarginCV,
            "revenueCV": revenueCV,
        },
    }

    # notes enrichment
    notesDetail = fetchNotesDetail(company, ["borrowings", "provisions"])
    if notesDetail:
        result["notesDetail"] = notesDetail

    return result


# ═══════════════════════════════════════════════════════════
# calc 2: 신용등급 종합 산출
# ═══════════════════════════════════════════════════════════


@memoized_calc
def calcCreditScore(company, *, basePeriod: str | None = None) -> dict | None:
    """신용등급 종합 산출 — 5축 가중평균 → 업종 조정 → 20단계 등급.

    5축 (100점 만점, 0=안전 100=위험):
    - 채무상환능력 (35%): FFO/Debt, Debt/EBITDA, FOCF/Debt, EBITDA/Interest
    - 레버리지 (25%): 부채비율, 차입금의존도, 순차입금/EBITDA
    - 유동성·만기 (15%): 유동비율, 현금비율, 단기차입금비중
    - 부실모델 앙상블 (15%): Altman, Ohlson, Zmijewski, Springate
    - 이익품질·추세 (10%): Beneish, Sloan, Piotroski, 이익변동성
    """
    from dartlab.core.finance.creditScorecard import (
        axisScore,
        cashFlowGrade,
        creditOutlook,
        gradeCategory,
        isInvestmentGrade,
        mapTo20Grade,
        scoreMetric,
        weightedScore,
    )
    from dartlab.core.finance.sectorThresholds import getSectorLabel, getThresholds

    metrics = calcCreditMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    latest = metrics["history"][0]  # 최신 기간
    sector = _getSector(company)
    thresholds = getThresholds(sector)
    sectorLabel = getSectorLabel(sector)

    # ── 축 1: 채무상환능력 (35%) ──
    repayment_scores = [
        ("FFO/총차입금", scoreMetric(latest.get("ffoToDebt"), thresholds["ffo_to_debt"])),
        ("Debt/EBITDA", scoreMetric(latest.get("debtToEbitda"), thresholds["debt_to_ebitda"])),
        ("FOCF/Debt", scoreMetric(latest.get("focfToDebt"), thresholds["focf_to_debt"])),
        ("EBITDA/이자비용", scoreMetric(latest.get("ebitdaInterestCoverage"), thresholds["ebitda_interest_coverage"])),
    ]
    repaymentScore = axisScore(repayment_scores)

    # ── 축 2: 레버리지 (25%) ──
    leverage_scores = [
        ("부채비율", scoreMetric(latest.get("debtRatio"), thresholds["debt_ratio"])),
        ("차입금의존도", scoreMetric(latest.get("borrowingDependency"), thresholds["borrowing_dependency"])),
        ("순차입금/EBITDA", scoreMetric(latest.get("netDebtToEbitda"), thresholds["net_debt_to_ebitda"])),
    ]
    leverageScore = axisScore(leverage_scores)

    # ── 축 3: 유동성·만기 (15%) ──
    liquidity_scores = [
        ("유동비율", scoreMetric(latest.get("currentRatio"), thresholds["current_ratio"])),
        ("현금비율", scoreMetric(latest.get("cashRatio"), thresholds["cash_ratio"])),
        ("단기차입금비중", scoreMetric(latest.get("shortTermDebtRatio"), thresholds["short_term_debt_ratio"])),
    ]
    liquidityScore = axisScore(liquidity_scores)

    # ── 축 4: 부실모델 앙상블 (15%) ──
    ratios = getRatios(company)
    distressScores: list[tuple[str, float | None]] = []
    if ratios is not None:
        # 기존 ratios에서 이미 계산된 부실 모델 활용
        from dartlab.analysis.financial.insight.distress import (
            _normalizeOhlson,
            _normalizeZ,
            _normalizeZpp,
        )

        if ratios.ohlsonProbability is not None:
            distressScores.append(("Ohlson O-Score", _normalizeOhlson(ratios.ohlsonProbability)))
        if ratios.altmanZppScore is not None:
            distressScores.append(("Altman Z''", _normalizeZpp(ratios.altmanZppScore)))
        if ratios.altmanZScore is not None:
            distressScores.append(("Altman Z", _normalizeZ(ratios.altmanZScore)))
        if ratios.springateSScore is not None:
            sNorm = 0.0 if ratios.springateSScore > 0.862 else 70.0
            distressScores.append(("Springate S", sNorm))
        if ratios.zmijewskiXScore is not None:
            zNorm = 0.0 if ratios.zmijewskiXScore < 0 else 70.0
            distressScores.append(("Zmijewski X", zNorm))

    distressScore = axisScore(distressScores) if distressScores else None

    # ── 축 5: 이익품질·추세 (10%) ──
    qualityScores: list[tuple[str, float | None]] = []
    if ratios is not None:
        from dartlab.analysis.financial.insight.distress import (
            _normalizeBeneish,
            _normalizeFScore,
            _normalizeSloan,
        )

        if ratios.beneishMScore is not None:
            qualityScores.append(("Beneish M", _normalizeBeneish(ratios.beneishMScore)))
        if ratios.sloanAccrualRatio is not None:
            qualityScores.append(("Sloan Accrual", _normalizeSloan(ratios.sloanAccrualRatio)))
        if ratios.piotroskiFScore is not None:
            qualityScores.append(("Piotroski F", _normalizeFScore(ratios.piotroskiFScore)))

    # 이익 변동성 (CV 기반)
    stabilityMetrics = metrics.get("stabilityMetrics", {})
    opMarginCV = stabilityMetrics.get("operatingMarginCV")
    if opMarginCV is not None:
        # CV 50% 이상 → 위험 70점, CV 10% 이하 → 안전 5점
        cvScore = min(70, max(5, opMarginCV * 1.4))
        qualityScores.append(("이익변동성", round(cvScore, 2)))

    qualityScore = axisScore(qualityScores) if qualityScores else None

    # ── 5축 가중평균 ──
    isFinancialCo = _isFinancial(company)
    axes = [
        {"name": "채무상환능력", "score": repaymentScore, "weight": 0.30 if isFinancialCo else 0.35},
        {"name": "레버리지", "score": leverageScore, "weight": 0.20 if isFinancialCo else 0.25},
        {"name": "유동성·만기", "score": liquidityScore, "weight": 0.20 if isFinancialCo else 0.15},
        {"name": "부실모델 앙상블", "score": distressScore, "weight": 0.20 if isFinancialCo else 0.15},
        {"name": "이익품질·추세", "score": qualityScore, "weight": 0.10},
    ]

    overall = weightedScore(axes)
    grade, gradeDesc, pdEstimate = mapTo20Grade(overall)

    # ── 현금흐름등급 ──
    ocfToSales = latest.get("ocfToSales")
    fcfPositive = latest.get("fcf") is not None and latest.get("fcf", 0) > 0
    ocfToDebt = latest.get("ocfToDebt")
    # OCF 추세 안정성 (3기 연속 양수)
    ocfTrendStable = all(
        h.get("ocf") is not None and h.get("ocf", 0) > 0
        for h in metrics["history"][:3]
    ) if len(metrics["history"]) >= 3 else None

    eCR = cashFlowGrade(ocfToSales, fcfPositive, ocfToDebt, ocfTrendStable)

    # ── 등급 시계열 (역산) ──
    scoreHistory = []
    for h in metrics["history"]:
        periodScores = []
        for metricKey, threshKey in [
            ("ffoToDebt", "ffo_to_debt"),
            ("debtToEbitda", "debt_to_ebitda"),
            ("ebitdaInterestCoverage", "ebitda_interest_coverage"),
            ("debtRatio", "debt_ratio"),
            ("currentRatio", "current_ratio"),
        ]:
            s = scoreMetric(h.get(metricKey), thresholds[threshKey])
            if s is not None:
                periodScores.append(s)
        if periodScores:
            scoreHistory.append(round(sum(periodScores) / len(periodScores), 2))

    outlook = creditOutlook(scoreHistory)

    # ── 축 상세 (출력용) ──
    def _formatAxis(name, score, weight, metricScores):
        return {
            "name": name,
            "score": score,
            "weight": round(weight * 100),
            "metrics": [
                {"name": n, "score": s}
                for n, s in metricScores
                if s is not None
            ],
        }

    axesDetail = [
        _formatAxis("채무상환능력", repaymentScore, axes[0]["weight"], repayment_scores),
        _formatAxis("레버리지", leverageScore, axes[1]["weight"], leverage_scores),
        _formatAxis("유동성·만기", liquidityScore, axes[2]["weight"], liquidity_scores),
        _formatAxis("부실모델 앙상블", distressScore, axes[3]["weight"], distressScores),
        _formatAxis("이익품질·추세", qualityScore, axes[4]["weight"], qualityScores),
    ]

    return {
        "grade": grade,
        "gradeDescription": gradeDesc,
        "gradeCategory": gradeCategory(grade),
        "investmentGrade": isInvestmentGrade(grade),
        "score": overall,
        "pdEstimate": pdEstimate,
        "eCR": eCR,
        "outlook": outlook,
        "sector": sectorLabel,
        "axes": axesDetail,
        "latestPeriod": latest.get("period"),
        "qualitativeSlots": {
            "marketPosition": None,
            "competitiveAdvantage": None,
            "managementQuality": None,
            "groupSupport": None,
        },
    }


# ═══════════════════════════════════════════════════════════
# calc 3: 신용등급 시계열
# ═══════════════════════════════════════════════════════════


@memoized_calc
def calcCreditHistory(company, *, basePeriod: str | None = None) -> dict | None:
    """신용등급 시계열 — 5개년 등급 변화 추적.

    매년 핵심 지표 기반 등급을 역산하여 등급 궤적을 보여준다.
    """
    from dartlab.core.finance.creditScorecard import mapTo20Grade, scoreMetric
    from dartlab.core.finance.sectorThresholds import getThresholds

    metrics = calcCreditMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    sector = _getSector(company)
    thresholds = getThresholds(sector)

    history = []
    for h in metrics["history"]:
        # 핵심 5개 지표로 간이 점수 역산
        scores = []
        for metricKey, threshKey in [
            ("ffoToDebt", "ffo_to_debt"),
            ("debtToEbitda", "debt_to_ebitda"),
            ("ebitdaInterestCoverage", "ebitda_interest_coverage"),
            ("debtRatio", "debt_ratio"),
            ("borrowingDependency", "borrowing_dependency"),
            ("currentRatio", "current_ratio"),
            ("cashRatio", "cash_ratio"),
            ("ocfToDebt", "focf_to_debt"),
        ]:
            s = scoreMetric(h.get(metricKey), thresholds[threshKey])
            if s is not None:
                scores.append(s)

        if not scores:
            continue

        periodScore = round(sum(scores) / len(scores), 2)
        grade, desc, pd = mapTo20Grade(periodScore)
        history.append({
            "period": h["period"],
            "score": periodScore,
            "grade": grade,
            "pdEstimate": pd,
        })

    if not history:
        return None

    # 등급 변동 분석
    grades = [h["grade"] for h in history]
    stable = len(set(grades)) <= 2  # 2개 이하 등급 = 안정적

    return {
        "history": history,
        "stable": stable,
        "latestGrade": history[0]["grade"] if history else None,
        "oldestGrade": history[-1]["grade"] if history else None,
    }


# ═══════════════════════════════════════════════════════════
# calc 4: 현금흐름등급 (eCR)
# ═══════════════════════════════════════════════════════════


@memoized_calc
def calcCashFlowGrade(company, *, basePeriod: str | None = None) -> dict | None:
    """현금흐름등급(eCR) — 현금흐름창출능력 별도 평가.

    한국 신평사 현금흐름 등급 체계 대응.
    eCR-1(최상) ~ eCR-6(최하).
    """
    from dartlab.core.finance.creditScorecard import cashFlowGrade

    metrics = calcCreditMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    history = []
    for h in metrics["history"]:
        ocfToSales = h.get("ocfToSales")
        fcfPositive = h.get("fcf") is not None and h.get("fcf", 0) > 0
        ocfToDebt = h.get("ocfToDebt")

        eCR = cashFlowGrade(ocfToSales, fcfPositive, ocfToDebt)
        history.append({
            "period": h["period"],
            "eCR": eCR,
            "ocfToSales": ocfToSales,
            "fcfPositive": fcfPositive,
            "ocfToDebt": ocfToDebt,
        })

    return {"history": history} if history else None


# ═══════════════════════════════════════════════════════════
# calc 5: 업종 내 신용 순위
# ═══════════════════════════════════════════════════════════


@memoized_calc
def calcCreditPeerPosition(company, *, basePeriod: str | None = None) -> dict | None:
    """업종 내 신용 순위 — 핵심 지표별 백분위.

    scan 데이터를 활용하여 동종업계 대비 위치를 산출한다.
    scan 데이터 미보유 시 None 반환.
    """
    metrics = calcCreditMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    latest = metrics["history"][0]

    # scan 데이터에서 동종업계 비교 — 가용한 경우만
    peerData = None
    try:
        from dartlab.scan.debt.scanner import scan_icr

        icrData = scan_icr(company)
        if icrData is not None:
            peerData = icrData
    except (ImportError, AttributeError, ValueError, KeyError):
        pass

    return {
        "latestPeriod": latest.get("period"),
        "metrics": {
            "debtRatio": latest.get("debtRatio"),
            "ebitdaInterestCoverage": latest.get("ebitdaInterestCoverage"),
            "ffoToDebt": latest.get("ffoToDebt"),
            "currentRatio": latest.get("currentRatio"),
        },
        "peerAvailable": peerData is not None,
    }


# ═══════════════════════════════════════════════════════════
# calc 6: 신용 경고/개선 플래그
# ═══════════════════════════════════════════════════════════


@memoized_calc
def calcCreditFlags(company, *, basePeriod: str | None = None) -> dict | None:
    """신용 경고(warning) / 개선(opportunity) 플래그.

    등급 하방 압력 또는 상방 기회 신호를 구체적으로 제시한다.
    """
    metrics = calcCreditMetrics(company, basePeriod=basePeriod)
    if metrics is None or not metrics.get("history"):
        return None

    latest = metrics["history"][0]
    flags: list[dict] = []

    # ── 경고 플래그 ──
    icr = latest.get("ebitdaInterestCoverage")
    if icr is not None and icr < 1.5 and not _isFinancial(company):
        flags.append({
            "type": "warning",
            "signal": "이자보상배율 1.5배 미달",
            "detail": f"EBITDA/이자비용 = {icr}배. 이자 지급 능력 부족.",
            "impact": "등급 하방 압력 1~2 notch",
        })

    debtRatio = latest.get("debtRatio")
    if debtRatio is not None and debtRatio > 300 and not _isFinancial(company):
        flags.append({
            "type": "warning",
            "signal": "부채비율 300% 초과",
            "detail": f"부채비율 {debtRatio:.0f}%. 과도한 레버리지.",
            "impact": "등급 하방 압력",
        })

    stDebtRatio = latest.get("shortTermDebtRatio")
    if stDebtRatio is not None and stDebtRatio > 60:
        flags.append({
            "type": "warning",
            "signal": "단기차입금 비중 60% 초과",
            "detail": f"단기차입금 비중 {stDebtRatio:.0f}%. 차환 리스크 높음.",
            "impact": "유동성 위험",
        })

    ocf = latest.get("ocf")
    if ocf is not None and ocf < 0:
        flags.append({
            "type": "warning",
            "signal": "영업현금흐름 적자",
            "detail": "본업에서 현금이 유출되고 있음.",
            "impact": "등급 하방 압력 2+ notch",
        })

    # OCF 3기 연속 감소
    if len(metrics["history"]) >= 3:
        ocfs = [h.get("ocf") for h in metrics["history"][:3]]
        if all(o is not None for o in ocfs):
            if ocfs[0] < ocfs[1] < ocfs[2]:
                flags.append({
                    "type": "warning",
                    "signal": "영업CF 3기 연속 감소",
                    "detail": "현금흐름 악화 추세.",
                    "impact": "등급 전망 부정적",
                })

    # Debt/EBITDA 과다
    debtEbitda = latest.get("debtToEbitda")
    if debtEbitda is not None and debtEbitda > 5 and not _isFinancial(company):
        flags.append({
            "type": "warning",
            "signal": "Debt/EBITDA 5배 초과",
            "detail": f"총차입금/EBITDA = {debtEbitda}배. 부채 감당 능력 부족.",
            "impact": "B급 이하 위험",
        })

    # ── 개선 플래그 ──
    if icr is not None and icr > 10:
        flags.append({
            "type": "opportunity",
            "signal": "이자보상배율 10배 초과",
            "detail": f"EBITDA/이자비용 = {icr}배. 충분한 이자 지급 여력.",
            "impact": "등급 상방 기회",
        })

    ffoDebt = latest.get("ffoToDebt")
    if ffoDebt is not None and ffoDebt > 40:
        flags.append({
            "type": "opportunity",
            "signal": "FFO/총차입금 40% 초과",
            "detail": f"FFO/Debt = {ffoDebt:.0f}%. 우수한 부채상환 능력.",
            "impact": "등급 상방 기회",
        })

    currentRatio = latest.get("currentRatio")
    if currentRatio is not None and currentRatio > 200:
        flags.append({
            "type": "opportunity",
            "signal": "유동비율 200% 초과",
            "detail": f"유동비율 {currentRatio:.0f}%. 단기 유동성 매우 우수.",
            "impact": "유동성 안전",
        })

    # 부채 3기 연속 감소
    if len(metrics["history"]) >= 3:
        debts = [h.get("debtRatio") for h in metrics["history"][:3]]
        if all(d is not None for d in debts):
            if debts[0] < debts[1] < debts[2]:
                flags.append({
                    "type": "opportunity",
                    "signal": "부채비율 3기 연속 감소",
                    "detail": "레버리지 개선 추세.",
                    "impact": "등급 전망 긍정적",
                })

    return {"flags": flags} if flags else {"flags": []}
