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
    """SelectResult → ({계정명: {period: val}}, periods).

    analysis._helpers.toDict 와 동일 로직을 자체 구현.
    cross-dependency 방지: credit ↛ analysis.
    """
    if selectResult is None:
        return None

    df = selectResult.df
    from dartlab.core.show import isPeriodColumn

    periods = sorted([c for c in df.columns if isPeriodColumn(c)], reverse=True)
    if not periods:
        return None

    labelCol = "계정명" if "계정명" in df.columns else (df.columns[0] if df.columns else None)
    if labelCol is None:
        return None

    # EDGAR bridge: snakeId → 한국어 라벨 (양 provider 호환)
    needsBridge = labelCol != "계정명" and "계정명" not in df.columns
    krLabels: dict[str, str] | None = None
    if needsBridge:
        from dartlab.core.finance.labels import get_korean_labels

        krLabels = get_korean_labels()

    data: dict[str, dict] = {}
    for row in df.iter_rows(named=True):
        label = str(row.get(labelCol, ""))
        key = krLabels.get(label, label) if krLabels else label
        data[key] = {c: row.get(c) for c in periods}
    return (data, periods) if data else None


def _annualCols(periods: list[str], basePeriod: str | None, maxYears: int = 8) -> list[str]:
    """기간 목록에서 연간 컬럼 추출 — basePeriod 이하만.

    analysis._helpers.annualColsFromPeriods 와 동일 로직을 자체 구현.
    cross-dependency 방지: credit ↛ analysis.
    """
    cols = sorted([c for c in periods if "Q" not in c], reverse=True)
    if not cols:
        cols = sorted([c for c in periods if c.endswith("Q4")], reverse=True)
    if basePeriod is not None:
        limit = basePeriod + "Q5" if "Q" not in basePeriod else basePeriod
        cols = [c for c in cols if (c + "Q5" if "Q" not in c else c) <= limit]
    return cols[:maxYears]


def _isQuarterlyFallback(cols: list[str]) -> bool:
    """Q4 fallback 컬럼인지 판별."""
    return bool(cols) and "Q" in cols[0]


def _ttmSum(flowData: dict, qCol: str, allPeriods: list[str]) -> float | None:
    """Q4 컬럼 기준 최근 4분기 합산(TTM).

    qCol이 "2025Q4"이면 2025Q4+Q3+Q2+Q1 합산.
    분기 데이터가 부족하면 가용 분기만 연환산.
    """
    year = qCol[:4]
    quarters = [f"{year}Q{q}" for q in (4, 3, 2, 1)]
    vals = [flowData.get(q) for q in quarters if q in allPeriods]
    valid = [v for v in vals if v is not None]
    if not valid:
        return None
    if len(valid) >= 3:
        # 3~4분기 있으면 4분기로 연환산
        return sum(valid) / len(valid) * 4
    # 2분기 이하면 단순 합산 (부정확하지만 0보다 나음)
    return sum(valid) / len(valid) * 4


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

    cfResult = company.select("CF", ["영업활동현금흐름", "유형자산의취득", "4.금융비용", "금융비용"])
    cfParsed = _toDict(cfResult)
    cfData: dict = {}
    if cfParsed is not None:
        cfData, _ = cfParsed

    yCols = _annualCols(bsPeriods, basePeriod, 9)
    if len(yCols) < 2:
        return None

    # Q4 fallback 감지 — IS/CF 플로우 변수에 TTM 합산 필요
    _quarterlyMode = _isQuarterlyFallback(yCols)
    _allPeriods = set(bsPeriods)

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
    # CF 이자비용 fallback (IS에 이자비용/금융비용이 없는 기업용)
    cfFinCost = cfData.get("4.금융비용", {}) or cfData.get("금융비용", {})

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

        # IS/CF 플로우 변수: Q4 fallback이면 TTM 합산
        if _quarterlyMode:
            revenue = _ttmSum(rev, col, _allPeriods)
            opIncome = _ttmSum(oi, col, _allPeriods)
            netIncome = _ttmSum(ni, col, _allPeriods)
            depreciation = _ttmSum(dep, col, _allPeriods)
            ocfVal = _ttmSum(ocf, col, _allPeriods)
            capexVal = _ttmSum(capex, col, _allPeriods)
            ie = (
                _ttmSum(intCost, col, _allPeriods)
                or _ttmSum(finCost, col, _allPeriods)
                or _ttmSum(cfFinCost, col, _allPeriods)
            )
        else:
            revenue = rev.get(col)
            opIncome = oi.get(col)
            netIncome = ni.get(col)
            depreciation = dep.get(col)
            ocfVal = ocf.get(col)
            capexVal = capex.get(col)
            ie = intCost.get(col) or finCost.get(col) or cfFinCost.get(col)
        if capexVal is not None:
            capexVal = abs(capexVal)

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

    # ── 기업 프로필 + 부문 구성 + 업종 순위 ──
    profile = _fetchProfile(company)
    segmentComposition = _fetchSegmentComposition(company)
    rank = _fetchRank(company)

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
        "profile": profile,
        "segmentComposition": segmentComposition,
        "rank": rank,
    }


# ═══════════════════════════════════════════════════════════
# notes / sections / scan 데이터 수집
# ═══════════════════════════════════════════════════════════


_SECTOR_KR = {
    "ENERGY": "에너지",
    "MATERIALS": "소재",
    "INDUSTRIALS": "산업재",
    "CONSUMER_DISC": "경기관련소비재",
    "CONSUMER_STAPLES": "필수소비재",
    "HEALTHCARE": "건강관리",
    "FINANCIALS": "금융",
    "IT": "IT",
    "COMMUNICATION": "커뮤니케이션서비스",
    "UTILITIES": "유틸리티",
    "REAL_ESTATE": "부동산",
}


def _fetchProfile(company) -> dict | None:
    """기업 프로필 (업종, 주요제품) 수집.

    Company.sector + dartlab.listing() 직접 접근.
    cross-dependency 방지: credit ↛ analysis.
    """
    parts: dict[str, str] = {}
    try:
        sectorInfo = company.sector
        if sectorInfo:
            sectorKr = _SECTOR_KR.get(sectorInfo.sector.name, sectorInfo.sector.name)
            groupKr = sectorInfo.industryGroup.value
            parts["sector"] = f"섹터: {sectorKr} > {groupKr}"
    except (ValueError, KeyError, AttributeError):
        pass

    try:
        import dartlab

        listing = dartlab.listing()
        stockCode = getattr(company, "stockCode", "")
        if stockCode:
            row = listing.filter(listing["종목코드"] == stockCode)
            if not row.is_empty() and "주요제품" in row.columns:
                products = row["주요제품"][0]
                if products:
                    parts["products"] = f"주요제품: {products}"
    except (ImportError, ValueError, KeyError):
        pass

    return parts if parts else None


def _fetchSegmentComposition(company) -> dict | None:
    """부문별 매출/이익 구성 수집.

    company.notes.segments 직접 접근.
    cross-dependency 방지: credit ↛ analysis.
    """
    try:
        accessor = getattr(company, "_notesAccessor", None) or getattr(company, "notes", None)
        if accessor is None:
            return None
        df = getattr(accessor, "segments", None)
        if df is None or not hasattr(df, "to_dicts"):
            return None
        rows = df.to_dicts()
        if not rows:
            return None

        # segments DataFrame에서 부문별 매출 추출
        segments = []
        for row in rows:
            name = None
            revenue = None
            for k, v in row.items():
                if isinstance(v, str) and name is None:
                    name = v
                if isinstance(v, (int, float)) and v > 0:
                    if any(term in str(k) for term in ["매출", "수익", "revenue"]):
                        revenue = v
                        break
            if name and revenue and revenue > 0:
                segments.append({"name": name, "revenue": revenue})

        if not segments:
            return None

        segments.sort(key=lambda x: x["revenue"], reverse=True)
        totalRev = sum(s["revenue"] for s in segments)
        if totalRev == 0:
            return None

        return {"segments": segments, "totalRevenue": totalRev}
    except (AttributeError, FileNotFoundError, ValueError, KeyError, TypeError):
        return None


def _fetchRank(company) -> dict | None:
    """업종 내 순위 수집. scan 데이터 없으면 None (스냅샷 빌드 시도 안 함)."""
    try:
        from dartlab.scan.rank import _SNAPSHOT, _cacheDir

        # 캐시된 스냅샷이 있을 때만 사용 (빌드 시도 X — 수분 소요)
        if _SNAPSHOT is None:
            cachePath = _cacheDir() / "rank_snapshot.parquet"
            if not cachePath.exists():
                return None

        from dartlab.scan.rank import getRankOrBuild

        stockCode = getattr(company, "stockCode", "")
        if not stockCode:
            return None
        rank = getRankOrBuild(stockCode, verbose=False)
        if rank is None:
            return None
        return {
            "revenueRank": rank.revenueRank,
            "revenueTotal": rank.revenueTotal,
            "revenueRankInSector": rank.revenueRankInSector,
            "revenueSectorTotal": rank.revenueSectorTotal,
            "sizeClass": rank.sizeClass,
            "sector": rank.sector,
            "industryGroup": rank.industryGroup,
        }
    except (ImportError, AttributeError, ValueError, KeyError, OSError, TypeError):
        return None


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


# ═══════════════════════════════════════════════════════════
# Track B: 금융업 전용 지표 산출
# ═══════════════════════════════════════════════════════════


def calcFinancialMetrics(company, *, basePeriod: str | None = None) -> dict | None:
    """금융업(은행/보험/증권) 전용 5축 지표 산출.

    일반기업용 D/EBITDA, FFO/Debt 대신
    자본비율, ROA, NIM 대리, 충당금 비율 등 금융업 핵심 지표 사용.
    """
    bsResult = company.select(
        "BS",
        ["자산총계", "부채총계", "자본총계", "유동자산", "유동부채", "현금및현금성자산"],
    )
    bsParsed = _toDict(bsResult)
    if bsParsed is None:
        return None
    bsData, bsPeriods = bsParsed

    isResult = company.select(
        "IS",
        ["이자수익", "금융이익", "금융비용", "4.금융비용", "당기순이익", "대손상각비", "영업이익"],
    )
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None
    isData, _ = isParsed

    cfResult = company.select("CF", ["영업활동현금흐름", "4.금융비용", "금융비용"])
    cfParsed = _toDict(cfResult)
    cfData = cfParsed[0] if cfParsed else {}

    yCols = _annualCols(bsPeriods, basePeriod, 9)
    if len(yCols) < 2:
        return None

    _qMode = _isQuarterlyFallback(yCols)
    _allP = set(bsPeriods)

    # 금융업: 금융이익(순영업수익)을 우선. 이자수익은 부수 항목일 수 있음
    intIncome = isData.get("금융이익", {}) or isData.get("이자수익", {})
    intExpense = isData.get("금융비용", {}) or isData.get("4.금융비용", {})
    ni = isData.get("당기순이익", {})
    provision = isData.get("대손상각비", {})
    oi = isData.get("영업이익", {})
    ta = bsData.get("자산총계", {})
    eq = bsData.get("자본총계", {})
    cash = bsData.get("현금및현금성자산", {})
    ca = bsData.get("유동자산", {})
    cl = bsData.get("유동부채", {})
    ocf = cfData.get("영업활동현금흐름", {})
    cfFinCost = cfData.get("4.금융비용", {}) or cfData.get("금융비용", {})

    history = []
    roaList = []
    revList = []

    for col in yCols[:-1]:
        totalAssets = ta.get(col)
        equity = eq.get(col)
        cashVal = cash.get(col)
        curAssets = ca.get(col)
        curLiab = cl.get(col)

        if _qMode:
            intInc = _ttmSum(intIncome, col, _allP)
            intExp = _ttmSum(intExpense, col, _allP) or _ttmSum(cfFinCost, col, _allP)
            netIncome = _ttmSum(ni, col, _allP)
            provCharge = _ttmSum(provision, col, _allP)
            opIncome = _ttmSum(oi, col, _allP)
            ocfVal = _ttmSum(ocf, col, _allP)
        else:
            intInc = intIncome.get(col)
            intExp = intExpense.get(col) or cfFinCost.get(col)
            netIncome = ni.get(col)
            provCharge = provision.get(col)
            opIncome = oi.get(col)
            ocfVal = ocf.get(col)

        if totalAssets is None or totalAssets == 0:
            continue

        # 축1: 자본적정성
        equityRatio = _div(equity, totalAssets, pct=True)

        # 축2: 수익성
        roa = _div(netIncome, totalAssets, pct=True)
        # NIM 대리: 이자수익/자산 (금융비용 차감 방식은 계정 불일치로 불안정)
        nim = _div(intInc, totalAssets, pct=True) if intInc else None

        # 축3: 자산건전성
        provRatio = _div(abs(provCharge) if provCharge else None, totalAssets, pct=True)

        # 축4: 유동성
        cashToAsset = _div(cashVal, totalAssets, pct=True)
        currentRatio = _div(curAssets, curLiab, pct=True) if curLiab and curLiab > 0 else None

        roaList.append(roa)
        revList.append(opIncome)

        history.append({
            "period": col,
            "totalAssets": totalAssets,
            "equity": equity,
            "netIncome": netIncome,
            "operatingIncome": opIncome,
            "ocf": ocfVal,
            # 축1
            "equityRatio": equityRatio,
            # 축2
            "roa": roa,
            "nimProxy": nim,
            # 축3
            "provisionRatio": provRatio,
            # 축4
            "cashToAsset": cashToAsset,
            "currentRatio": currentRatio,
        })

    if not history:
        return None

    # 축5: 사업안정성 (기존 로직 재사용)
    bizStability = {
        "revenueCV": _cv([r for r in revList if r is not None]),
        "roaCV": _cv([r for r in roaList if r is not None]),
        "totalAssets": history[0].get("totalAssets"),
    }

    return {
        "history": history,
        "businessStability": bizStability,
        "track": "B",
    }
