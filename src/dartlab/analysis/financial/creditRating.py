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


def _isHolding(company) -> bool:
    """지주사 여부."""
    try:
        name = getattr(company, "corpName", "") or ""
        if any(k in name for k in ("지주", "홀딩스", "Holdings")):
            return True
    except (AttributeError, ImportError):
        pass
    return False


def _getSectorEnum(name: str):
    """Sector enum 값을 이름으로 조회."""
    try:
        from dartlab.core.sector.types import Sector
        return getattr(Sector, name, None)
    except ImportError:
        return None


def _getIndustryGroup(company):
    """company.sector에서 IndustryGroup enum 추출."""
    try:
        si = getattr(company, "sector", None)
        if si is not None:
            return si.industryGroup
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


def _isCaptiveFinance(company, totalBorrowing: float, ebitda: float | None) -> bool:
    """캡티브 금융 복합기업 감지.

    비금융업인데 Debt/EBITDA > 15이고 차입금의존도 > 25%이면
    금융자회사 연결 효과로 판단. 현대차/삼성/SK 등.
    """
    if _isFinancial(company):
        return False
    if ebitda is None or ebitda <= 0 or totalBorrowing <= 0:
        return False
    debtEbitda = totalBorrowing / ebitda
    return debtEbitda > 15


def _calcBusinessRisk(company, metrics: dict) -> dict | None:
    """사업위험 정량화 — 매출 안정성 + 이익 안정성 + 규모.

    신평사의 사업위험 중 정량화 가능한 부분:
    - 매출 변동성 (CV) → 낮을수록 안정
    - 이익 변동성 (CV) → 낮을수록 안정
    - 매출 규모 (절대값) → 클수록 안정
    - 영업이익률 수준 → 높을수록 강한 경쟁력
    """
    history = metrics.get("history", [])
    if len(history) < 3:
        return None

    stabilityMetrics = metrics.get("stabilityMetrics", {})
    revenueCV = stabilityMetrics.get("revenueCV")
    opMarginCV = stabilityMetrics.get("operatingMarginCV")

    # 매출 규모 (최신, 조 단위 환산)
    latestRevenue = None
    try:
        ratios = getRatios(company)
        if ratios and ratios.revenueTTM:
            latestRevenue = ratios.revenueTTM
    except (AttributeError, ValueError):
        pass

    # 평균 영업이익률
    margins = []
    for h in history:
        ocfSales = h.get("ocfToSales")
        if ocfSales is not None:
            margins.append(ocfSales)

    avgMargin = sum(margins) / len(margins) if margins else None

    # 사업위험 점수 산출 (0-100, 높을수록 위험)
    scores = []

    # 매출 안정성 (CV 기반)
    if revenueCV is not None:
        if revenueCV < 5:
            scores.append(("매출안정성", 0.0))
        elif revenueCV < 15:
            scores.append(("매출안정성", (revenueCV - 5) * 2))
        elif revenueCV < 30:
            scores.append(("매출안정성", 20 + (revenueCV - 15) * 2))
        else:
            scores.append(("매출안정성", min(60, 50 + (revenueCV - 30))))

    # 이익 안정성
    if opMarginCV is not None:
        if opMarginCV < 10:
            scores.append(("이익안정성", 0.0))
        elif opMarginCV < 30:
            scores.append(("이익안정성", (opMarginCV - 10) * 1.5))
        elif opMarginCV < 60:
            scores.append(("이익안정성", 30 + (opMarginCV - 30)))
        else:
            scores.append(("이익안정성", min(60, 60)))

    # 규모 (매출 기준)
    if latestRevenue is not None:
        revTril = latestRevenue / 1e12  # 조 단위
        if revTril > 50:
            scores.append(("규모", 0.0))
        elif revTril > 10:
            scores.append(("규모", 5.0))
        elif revTril > 1:
            scores.append(("규모", 15.0))
        elif revTril > 0.1:
            scores.append(("규모", 30.0))
        else:
            scores.append(("규모", 45.0))

    # 영업이익률 수준
    if avgMargin is not None:
        if avgMargin > 20:
            scores.append(("마진수준", 0.0))
        elif avgMargin > 10:
            scores.append(("마진수준", 5.0))
        elif avgMargin > 5:
            scores.append(("마진수준", 15.0))
        elif avgMargin > 0:
            scores.append(("마진수준", 30.0))
        else:
            scores.append(("마진수준", 50.0))

    if not scores:
        return None

    from dartlab.core.finance.creditScorecard import axisScore

    score = axisScore(scores)
    return {
        "score": score,
        "metrics": scores,
        "revenueCV": revenueCV,
        "opMarginCV": opMarginCV,
    }


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
    industryGroup = _getIndustryGroup(company)
    thresholds = getThresholds(sector, industryGroup)
    sectorLabel = getSectorLabel(sector)

    # ── 캡티브 금융 복합기업 감지 ──
    # 비금융업인데 금융자회사 연결로 차입금/부채 과대계상된 경우
    # Debt/EBITDA, 차입금의존도 등 레버리지 지표를 완화 처리
    isCaptive = _isCaptiveFinance(
        company,
        latest.get("totalBorrowing") or 0,
        latest.get("ebitda"),
    )

    if isCaptive:
        # 캡티브 금융: 부채 관련 지표를 유틸리티 기준으로 완화
        from dartlab.core.finance.sectorThresholds import getThresholds as _getT
        from dartlab.core.sector.types import Sector as _S

        thresholds = _getT(_S.UTILITIES)
        sectorLabel = f"{sectorLabel} (캡티브금융조정)"

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
    # 연속 정규화: 이진 판정(0/70)이 아닌 선형 보간으로 과대평가 방지
    ratios = getRatios(company)
    distressScores: list[tuple[str, float | None]] = []
    if ratios is not None:
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
        # Springate: 연속 정규화 (이전: 0/70 이진)
        if ratios.springateSScore is not None:
            s = ratios.springateSScore
            if s > 1.5:
                sNorm = 0.0
            elif s > 0.862:
                sNorm = (1 - (s - 0.862) / 0.638) * 30
            elif s > 0.5:
                sNorm = 30 + (1 - (s - 0.5) / 0.362) * 30
            else:
                sNorm = min(80, 60 + (0.5 - s) * 40)
            distressScores.append(("Springate S", round(sNorm, 1)))
        # Zmijewski: 연속 정규화 (이전: 0/70 이진)
        if ratios.zmijewskiXScore is not None:
            x = ratios.zmijewskiXScore
            if x < -3.0:
                zNorm = 0.0
            elif x < 0:
                zNorm = (x + 3.0) / 3.0 * 25
            elif x < 1.0:
                zNorm = 25 + x * 25
            else:
                zNorm = min(80, 50 + (x - 1.0) * 15)
            distressScores.append(("Zmijewski X", round(zNorm, 1)))

    distressScore = axisScore(distressScores) if distressScores else None

    # ── 축 5: 이익품질·추세 (10%) ──
    # 신용등급 맥락: 이익품질은 보조 축이므로 점수 상한을 50으로 제한
    qualityScores: list[tuple[str, float | None]] = []
    if ratios is not None:
        from dartlab.analysis.financial.insight.distress import (
            _normalizeBeneish,
            _normalizeFScore,
            _normalizeSloan,
        )

        if ratios.beneishMScore is not None:
            # Beneish: 신용등급용 완화 (M < -2.22이면 0, 조작 구간만 경고)
            m = ratios.beneishMScore
            if m < -2.22:
                bScore = 0.0
            elif m < -1.78:
                bScore = 20.0
            else:
                bScore = 45.0
            qualityScores.append(("Beneish M", bScore))
        if ratios.sloanAccrualRatio is not None:
            # Sloan: 완화 (|ratio| < 15%는 정상)
            absR = abs(ratios.sloanAccrualRatio)
            if absR > 25:
                slScore = 45.0
            elif absR > 15:
                slScore = 20.0
            else:
                slScore = max(0, absR * 0.8)
            qualityScores.append(("Sloan Accrual", round(slScore, 1)))
        if ratios.piotroskiFScore is not None:
            # Piotroski: 완화 (F>=5이면 안전, F<=2만 경고)
            f = ratios.piotroskiFScore
            if f >= 7:
                fScore = 0.0
            elif f >= 5:
                fScore = 10.0
            elif f >= 3:
                fScore = 25.0
            else:
                fScore = 45.0
            qualityScores.append(("Piotroski F", fScore))

    # 이익 변동성 (CV 기반) — 완화
    stabilityMetrics = metrics.get("stabilityMetrics", {})
    opMarginCV = stabilityMetrics.get("operatingMarginCV")
    if opMarginCV is not None:
        # CV 80% 이상 → 45점, CV 20% 이하 → 0점 (이전: CV*1.4로 과대)
        cvScore = min(45, max(0, (opMarginCV - 20) * 0.75))
        qualityScores.append(("이익변동성", round(cvScore, 2)))

    qualityScore = axisScore(qualityScores) if qualityScores else None

    # ── 축 6: 사업위험 (10%) ──
    bizRisk = _calcBusinessRisk(company, metrics)
    bizRiskScore = bizRisk["score"] if bizRisk else None

    # ── 6축 가중평균 ──
    # 업종별 가중치 조정:
    # - 금융업: 레버리지/유동성 강화, 부실모델 축소 (은행 부채구조 왜곡)
    # - 에너지/소재/자동차: 부실모델 축소 (사이클 업종 Z-Score 구조적 저평가)
    # - 캡티브금융: 부실모델 대폭 축소
    isFinancialCo = _isFinancial(company)
    isCyclical = sector in (
        _getSectorEnum("ENERGY"), _getSectorEnum("MATERIALS"),
    ) if sector else False
    isHolding = _isHolding(company)

    if isFinancialCo:
        distressWeight, repayWeight, leverageWeight = 0.05, 0.30, 0.20
    elif isCaptive:
        distressWeight, repayWeight, leverageWeight = 0.05, 0.25, 0.15
    elif isCyclical:
        distressWeight, repayWeight, leverageWeight = 0.05, 0.30, 0.20
    elif isHolding:
        distressWeight, repayWeight, leverageWeight = 0.05, 0.25, 0.20
    else:
        distressWeight, repayWeight, leverageWeight = 0.10, 0.30, 0.20

    bizWeight = max(0.10, 1.0 - repayWeight - leverageWeight - 0.15 - distressWeight - 0.10)

    axes = [
        {"name": "채무상환능력", "score": repaymentScore, "weight": repayWeight},
        {"name": "레버리지", "score": leverageScore, "weight": leverageWeight},
        {"name": "유동성·만기", "score": liquidityScore, "weight": 0.15},
        {"name": "부실모델 앙상블", "score": distressScore, "weight": distressWeight},
        {"name": "이익품질", "score": qualityScore, "weight": 0.10},
        {"name": "사업위험", "score": bizRiskScore, "weight": bizWeight},
    ]

    currentScore = weightedScore(axes)

    # ── 시계열 안정성 보정 (3개년 가중 이동평균) ──
    # 등급의 급변동을 방지: 최신 60% + 과거1 25% + 과거2 15%
    historicalScores = []
    for h in metrics["history"][1:3]:  # 과거 2개 기간
        pScores = []
        for metricKey, threshKey in [
            ("ffoToDebt", "ffo_to_debt"),
            ("debtToEbitda", "debt_to_ebitda"),
            ("ebitdaInterestCoverage", "ebitda_interest_coverage"),
            ("debtRatio", "debt_ratio"),
            ("currentRatio", "current_ratio"),
        ]:
            s = scoreMetric(h.get(metricKey), thresholds[threshKey])
            if s is not None:
                pScores.append(s)
        if pScores:
            historicalScores.append(round(sum(pScores) / len(pScores), 2))

    if len(historicalScores) >= 2:
        overall = currentScore * 0.60 + historicalScores[0] * 0.25 + historicalScores[1] * 0.15
    elif len(historicalScores) == 1:
        overall = currentScore * 0.70 + historicalScores[0] * 0.30
    else:
        overall = currentScore

    overall = round(overall, 2)
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

    bizRiskMetrics = bizRisk["metrics"] if bizRisk else []
    axesDetail = [
        _formatAxis("채무상환능력", repaymentScore, axes[0]["weight"], repayment_scores),
        _formatAxis("레버리지", leverageScore, axes[1]["weight"], leverage_scores),
        _formatAxis("유동성·만기", liquidityScore, axes[2]["weight"], liquidity_scores),
        _formatAxis("부실모델 앙상블", distressScore, axes[3]["weight"], distressScores),
        _formatAxis("이익품질", qualityScore, axes[4]["weight"], qualityScores),
        _formatAxis("사업위험", bizRiskScore, axes[5]["weight"], bizRiskMetrics),
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
        "captiveFinance": isCaptive,
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
