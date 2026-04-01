"""7축 신용평가 정량 지표 산출.

모든 지표를 company.select() / company.notes / company.show()에서
직접 산출한다. 다른 analysis calc 함수를 호출하지 않는다.
"""

from __future__ import annotations


def _div(a, b, pct: bool = False) -> float | None:
    """안전한 나눗셈. pct=True이면 ×100."""
    if a is None or b is None or b == 0:
        return None
    result = a / abs(b)
    if pct:
        result *= 100
    return round(result, 2)


def _cv(values: list) -> float | None:
    """변동계수(CV) = 표준편차/|평균| × 100."""
    nums = [v for v in values if v is not None]
    if len(nums) < 3:
        return None
    mean = sum(nums) / len(nums)
    if mean == 0:
        return None
    variance = sum((x - mean) ** 2 for x in nums) / len(nums)
    return round((variance**0.5) / abs(mean) * 100, 2)


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    """SelectResult → ({계정명: {period: val}}, periods)."""
    if selectResult is None:
        return None
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _annualCols(periods: list[str], basePeriod: str | None, maxYears: int = 8) -> list[str]:
    from dartlab.analysis.financial._helpers import annualColsFromPeriods

    return annualColsFromPeriods(periods, basePeriod, maxYears)


def _getRatios(company):
    try:
        return company.finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


# ═══════════════════════════════════════════════════════════
# 7축 지표 산출
# ═══════════════════════════════════════════════════════════


def calcAllMetrics(company, *, basePeriod: str | None = None) -> dict | None:
    """7축 모든 지표를 한 번에 산출.

    company.select()로 원본 데이터를 직접 가져오고,
    notes/sections에서 추가 정보를 보강한다.
    """
    # ── 원본 데이터 수집 ──
    bsResult = company.select(
        "BS",
        [
            "자산총계",
            "부채총계",
            "자본총계",
            "유동자산",
            "유동부채",
            "비유동부채",
            "현금및현금성자산",
            "단기차입금",
            "장기차입금",
            "사채",
            "재고자산",
            "이익잉여금",
        ],
    )
    bsParsed = _toDict(bsResult)
    if bsParsed is None:
        return None
    bsData, bsPeriods = bsParsed

    isResult = company.select(
        "IS",
        [
            "매출액",
            "영업이익",
            "당기순이익",
            "금융비용",
            "이자비용",
            "감가상각비",
            "매출총이익",
        ],
    )
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None
    isData, _ = isParsed

    cfResult = company.select("CF", ["영업활동현금흐름", "유형자산의취득"])
    cfParsed = _toDict(cfResult)
    cfData: dict = {}
    if cfParsed is not None:
        cfData, _ = cfParsed

    yCols = _annualCols(bsPeriods, basePeriod, 9)
    if len(yCols) < 2:
        return None

    # 행 추출
    ta = bsData.get("자산총계", {})
    tl = bsData.get("부채총계", {})
    eq = bsData.get("자본총계", {})
    ca = bsData.get("유동자산", {})
    cl = bsData.get("유동부채", {})
    ncl = bsData.get("비유동부채", {})
    cash = bsData.get("현금및현금성자산", {})
    stb = bsData.get("단기차입금", {})
    ltb = bsData.get("장기차입금", {})
    bonds = bsData.get("사채", {})
    re = bsData.get("이익잉여금", {})

    rev = isData.get("매출액", {})
    oi = isData.get("영업이익", {})
    ni = isData.get("당기순이익", {})
    finCost = isData.get("금융비용", {})
    intCost = isData.get("이자비용", {})
    dep = isData.get("감가상각비", {})
    gp = isData.get("매출총이익", {})

    ocf = cfData.get("영업활동현금흐름", {})
    capex = cfData.get("유형자산의취득", {})

    # ── notes 데이터 수집 ──
    borrowingsDetail = _fetchNotes(company, "borrowings")
    provisionsDetail = _fetchNotes(company, "provisions")
    segmentsDetail = _fetchNotes(company, "segments")

    # ── 연도별 지표 산출 ──
    history = []
    opMargins = []
    revenues = []

    for col in yCols[:-1]:
        totalAssets = ta.get(col)
        totalDebt = tl.get(col)
        equity = eq.get(col)
        curAssets = ca.get(col)
        curLiab = cl.get(col)
        cashVal = cash.get(col)

        stBorrow = stb.get(col) or 0
        ltBorrow = ltb.get(col) or 0
        bondsVal = bonds.get(col) or 0
        totalBorrowing = stBorrow + ltBorrow + bondsVal

        revenue = rev.get(col)
        opIncome = oi.get(col)
        netIncome = ni.get(col)
        depreciation = dep.get(col)
        ocfVal = ocf.get(col)
        capexVal = capex.get(col)
        if capexVal is not None:
            capexVal = abs(capexVal)

        # 이자비용 (우선순위: IS이자비용 → IS금융비용)
        ie = intCost.get(col) or finCost.get(col)

        # EBITDA
        ebitda = (opIncome + (depreciation or 0)) if opIncome is not None else None

        # FFO (간이) = NI + 감가상각, fallback OCF
        ffo = None
        if netIncome is not None and depreciation is not None:
            ffo = netIncome + depreciation
        elif ocfVal is not None:
            ffo = ocfVal

        # FCF
        fcf = (ocfVal - capexVal) if ocfVal is not None and capexVal is not None else None

        # 순차입금
        netDebt = totalBorrowing - (cashVal or 0) if totalBorrowing > 0 else 0

        # ── 축 1: 채무상환능력 ──
        ffoToDebt = _div(ffo, totalBorrowing, pct=True) if totalBorrowing > 0 else (999.0 if ffo and ffo > 0 else None)
        debtToEbitda = _div(totalBorrowing, ebitda) if totalBorrowing > 0 else (0.0 if ebitda and ebitda > 0 else None)
        focfToDebt = _div(fcf, totalBorrowing, pct=True) if totalBorrowing > 0 else (999.0 if fcf and fcf > 0 else None)
        ebitdaInterest = _div(ebitda, ie) if ie and ie > 0 else (999.0 if ebitda and ebitda > 0 else None)

        # ── 축 2: 자본 구조 ──
        debtRatio = _div(totalDebt, equity, pct=True) if equity and equity > 0 else None
        borrowingDep = _div(totalBorrowing, totalAssets, pct=True) if totalAssets and totalAssets > 0 else None
        netDebtEbitda = _div(netDebt, ebitda) if ebitda and ebitda > 0 else None

        # ── 축 3: 유동성 ──
        currentRatio = _div(curAssets, curLiab, pct=True) if curLiab and curLiab > 0 else None
        cashRatio = _div(cashVal, curLiab, pct=True) if curLiab and curLiab > 0 else None
        stDebtRatio = _div(stBorrow, totalBorrowing, pct=True) if totalBorrowing > 0 else None

        # ── 축 4: 현금흐름 ──
        ocfToSales = _div(ocfVal, revenue, pct=True) if revenue and revenue > 0 else None
        fcfToSales = _div(fcf, revenue, pct=True) if revenue and revenue > 0 else None
        ocfToDebt = _div(ocfVal, totalBorrowing, pct=True) if totalBorrowing > 0 else None

        # 축 5용 수집
        opMargin = _div(opIncome, revenue, pct=True) if revenue and revenue > 0 else None
        opMargins.append(opMargin)
        revenues.append(revenue)

        history.append(
            {
                "period": col,
                # 원본
                "totalAssets": totalAssets,
                "totalBorrowing": totalBorrowing if totalBorrowing > 0 else None,
                "ebitda": ebitda,
                "ffo": ffo,
                "ocf": ocfVal,
                "fcf": fcf,
                "netDebt": netDebt,
                "revenue": revenue,
                "operatingIncome": opIncome,
                # 축 1: 채무상환
                "ffoToDebt": ffoToDebt,
                "debtToEbitda": debtToEbitda,
                "focfToDebt": focfToDebt,
                "ebitdaInterestCoverage": ebitdaInterest,
                # 축 2: 자본구조
                "debtRatio": debtRatio,
                "borrowingDependency": borrowingDep,
                "netDebtToEbitda": netDebtEbitda,
                # 축 3: 유동성
                "currentRatio": currentRatio,
                "cashRatio": cashRatio,
                "shortTermDebtRatio": stDebtRatio,
                # 축 4: 현금흐름
                "ocfToSales": ocfToSales,
                "fcfToSales": fcfToSales,
                "ocfToDebt": ocfToDebt,
            }
        )

    if not history:
        return None

    # ── 축 5: 사업 안정성 (전체 기간 대상) ──
    opMarginCV = _cv(opMargins)
    revenueCV = _cv(revenues)
    latestRevenue = revenues[0] if revenues else None
    avgMargin = None
    validMargins = [m for m in opMargins if m is not None]
    if validMargins:
        avgMargin = round(sum(validMargins) / len(validMargins), 2)

    # segments HHI (부문 다각화도)
    segmentHHI = _calcSegmentHHI(segmentsDetail)

    # ── 축 6: 재무 신뢰성 (ratios에서 참조) ──
    ratios = _getRatios(company)
    reliabilityData = {}
    if ratios:
        reliabilityData = {
            "beneishMScore": ratios.beneishMScore,
            "sloanAccrualRatio": ratios.sloanAccrualRatio,
            "ohlsonProbability": ratios.ohlsonProbability,
            "altmanZScore": ratios.altmanZScore,
            "altmanZppScore": ratios.altmanZppScore,
            "piotroskiFScore": ratios.piotroskiFScore,
        }

    # ── 축 7: 공시 리스크 (scan 참조) ──
    disclosureRisk = _fetchDisclosureRisk(company)

    # ── 감사의견 ──
    auditOpinion = _fetchAuditOpinion(company)

    return {
        "history": history,
        "businessStability": {
            "opMarginCV": opMarginCV,
            "revenueCV": revenueCV,
            "latestRevenue": latestRevenue,
            "avgMargin": avgMargin,
            "segmentHHI": segmentHHI,
        },
        "reliability": reliabilityData,
        "disclosureRisk": disclosureRisk,
        "auditOpinion": auditOpinion,
        "borrowingsDetail": borrowingsDetail,
        "provisionsDetail": provisionsDetail,
        "segmentsDetail": segmentsDetail,
    }


# ═══════════════════════════════════════════════════════════
# notes / sections / scan 데이터 수집
# ═══════════════════════════════════════════════════════════


def _fetchNotes(company, key: str) -> list[dict] | None:
    """notes에서 DataFrame을 dict 리스트로 안전하게 추출."""
    try:
        accessor = getattr(company, "_notesAccessor", None) or getattr(company, "notes", None)
        if accessor is None:
            return None
        df = getattr(accessor, key, None)
        if df is not None and hasattr(df, "to_dicts"):
            return df.to_dicts()
    except (AttributeError, FileNotFoundError, ValueError, KeyError):
        pass
    return None


def _calcSegmentHHI(segmentsData: list[dict] | None) -> float | None:
    """부문별 매출에서 HHI(허핀달-허쉬만 지수) 계산.

    HHI = Σ(부문매출비중²) × 10000
    HHI < 1500: 다각화, 1500-2500: 보통, > 2500: 집중
    """
    if not segmentsData:
        return None

    # segments DataFrame에서 매출 추출
    revenues = []
    for row in segmentsData:
        # 매출액 또는 영업수익 컬럼 탐색
        for k, v in row.items():
            if isinstance(v, (int, float)) and v > 0:
                if any(term in str(k) for term in ["매출", "수익", "revenue"]):
                    revenues.append(v)
                    break

    if len(revenues) < 2:
        return None

    total = sum(revenues)
    if total <= 0:
        return None

    hhi = sum((r / total * 100) ** 2 for r in revenues)
    return round(hhi, 0)


def _fetchDisclosureRisk(company) -> dict | None:
    """scan.disclosureRisk에서 기업별 리스크 신호 추출."""
    try:
        from dartlab.scan.disclosureRisk import disclosureRisk

        result = disclosureRisk(company)
        if result is not None and hasattr(result, "to_dicts"):
            rows = result.to_dicts()
            if rows:
                return rows[0]
    except (ImportError, AttributeError, ValueError, KeyError, TypeError):
        pass
    return None


def _fetchAuditOpinion(company) -> str | None:
    """감사의견 추출 — 적정/한정/부적정/의견거절."""
    try:
        from dartlab.scan.governance.scorer import _extractAuditOpinion

        return _extractAuditOpinion(company)
    except (ImportError, AttributeError):
        pass

    # fallback: scan governance에서
    try:
        gov = getattr(company, "governance", None)
        if gov is not None and callable(gov):
            result = gov()
            if result is not None and hasattr(result, "to_dicts"):
                rows = result.to_dicts()
                if rows:
                    return rows[0].get("auditOpinion")
    except (AttributeError, ValueError, KeyError, TypeError):
        pass
    return None
