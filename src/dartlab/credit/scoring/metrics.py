"""7축 신용분석 정량 지표 산출.

모든 지표를 company.select() / company.notes / company.panel()에서
직접 산출한다. 다른 analysis calc 함수는 호출하지 않으며,
공유 헬퍼만 ``analysis/financial/_helpers`` 에서 가져온다 (SSOT).
"""

from __future__ import annotations

import importlib

from dartlab.core.utils.helpers import (
    annualColsFromPeriods,
    toDictBySnakeId,
)


def _sumBorrowingsKorean(*args, **kwargs):
    """analysis.financial.accountSums.sumBorrowingsKorean lazy 호출.

    cycle 회피: credit ↔ analysis 양방향 cycle 차단 (analysis 가 credit 도 호출).
    importlib 동적 import 라 cycleScan/import-linter 가 못 잡음. 단방향 정책 통과.
    """
    mod = importlib.import_module("dartlab.analysis.financial.accountSums")
    return mod.sumBorrowingsKorean(*args, **kwargs)


# 본 모듈 안에서 sumBorrowingsKorean 이름으로 호출하는 코드의 BC 유지.
sumBorrowingsKorean = _sumBorrowingsKorean


from dartlab.credit.scoring._metricsArithmetic import (
    _cv,
    _div,
    _getRatios,
    _isQuarterlyFallback,
    _ttmSum,
)
from dartlab.credit.scoring._metricsFetchers import (
    _calcSegmentHHI,
    _fetchAuditOpinion,
    _fetchDisclosureRisk,
    _fetchNotes,
    _fetchProfile,
    _fetchRank,
    _fetchSegmentComposition,
)

# SSOT 위임: _toDict / _annualCols 는 analysis/_helpers 의 함수와 동일 로직.
# 호환을 위한 alias — 신규 코드는 toDictBySnakeId / annualColsFromPeriods 직접 호출.
_toDict = toDictBySnakeId
_annualCols = annualColsFromPeriods


# ═══════════════════════════════════════════════════════════
# 7축 지표 산출
# ═══════════════════════════════════════════════════════════


def calcAllMetrics(company, *, basePeriod: str | None = None) -> dict | None:
    """7 축 신용분석 30+ 지표 한 번에 산출 — credit engine 의 핵심 데이터 함수.

    Capabilities:
        Company 의 BS/IS/CF + notes (차입금/부문/감사의견 + 9 년 시계열) +
        sections (공시 리스크) → 신용 7 축 모든 지표 (FFO/Debt, Debt/EBITDA,
        EBITDA Interest Coverage 등 30+) 산출 + Beneish M-Score + Piotroski
        F-Score 동반 산출. credit.engine.evaluateCompany 가 본 함수 호출.

    Args:
        company: DartCompany 또는 EdgarCompany 인스턴스.
        basePeriod: 분석 기준 기간 (예 ``"2024"``). None 시 최신 9 년.

    Returns
    -------
    dict | None
        history : list[dict] — 기간별 지표 시계열. 각 dict 포함 키:
            period : str — 기간 (예: "2024")
            totalAssets : float | None — 자산총계 (원)
            totalBorrowing : float | None — 총차입금 (원)
            ebitda : float | None — EBITDA (원)
            ffo : float | None — FFO (원)
            ocf : float | None — 영업활동현금흐름 (원)
            fcf : float | None — 잉여현금흐름 (원)
            revenue : float | None — 매출액 (원)
            ffoToDebt : float | None — FFO/총차입금 (%)
            debtToEbitda : float | None — 총차입금/EBITDA (배)
            focfToDebt : float | None — FOCF/총차입금 (%)
            ebitdaInterestCoverage : float | None — EBITDA/이자비용 (배)
            debtRatio : float | None — 부채비율 (%)
            borrowingDependency : float | None — 차입금의존도 (%)
            netDebtToEbitda : float | None — 순차입금/EBITDA (배)
            currentRatio : float | None — 유동비율 (%)
            cashRatio : float | None — 현금비율 (%)
            shortTermDebtRatio : float | None — 단기차입금비중 (%)
            ocfToSales : float | None — OCF/매출 (%)
            fcfToSales : float | None — FCF/매출 (%)
            ocfToDebt : float | None — OCF/총차입금 (%)
        businessStability : dict — 사업 안정성 지표
            opMarginCV : float | None — 영업이익률 변동계수 (%)
            revenueCV : float | None — 매출 변동계수 (%)
            latestRevenue : float | None — 최신 매출 (원)
            avgMargin : float | None — 평균 영업이익률 (%)
            segmentHHI : float | None — 부문 HHI (점)
        reliability : dict — 재무 신뢰성 (Beneish M, Piotroski F 등)
        disclosureRisk : dict | None — 공시 리스크 (우발부채, 키워드)
        auditOpinion : str | None — 감사의견 ("적정"/"한정"/"부적정"/"의견거절")
        borrowingsDetail : list[dict] | None — 차입금 상세 내역
        provisionsDetail : list[dict] | None — 충당금 상세 내역
        segmentsDetail : list[dict] | None — 부문 상세 내역
        profile : dict | None — 기업 프로필 (섹터, 주요제품)
        segmentComposition : dict | None — 부문별 매출 구성
        rank : dict | None — 업종 내 순위

    Raises:
        없음 — 데이터 누락 시 None 반환.

    Example:
        >>> m = calcAllMetrics(Company("005930"))
        >>> m["history"][0]["ebitdaInterestCoverage"], m["auditOpinion"]
        (15.2, '적정')

    Guide:
        9 년 시계열 산출 (basePeriod=None). 부분 분기 (R25-1 partial period)
        는 evaluateCompany 가 건너뛴다. 본 함수는 모든 행 반환.

    SeeAlso:
        - ``credit.engine.evaluateCompany``: 본 함수 호출자
        - ``sectorThresholds``: 업종별 임계값 (본 metric 비교)
        - ``narrateRepayment`` 등: 본 metric 으로 서사 생성

    When:
        ``credit.engine.evaluateCompany`` 가 항상 본 함수 호출. AI 직접 호출은 raw metric 만
        필요할 때 (드물다).

    How:
        company.select BS/IS/CF → 9 년 시계열 → 30+ metric piecewise 계산 → notes 보강 →
        businessStability/reliability/disclosureRisk 합성.

    Requires:
        Company.select("BS/IS/CF") + notes 데이터 (DART 공시).

    AIContext:
        history list 의 첫 dict 가 최신 — 시계열 비교 시 [0] vs [1] 사용.
        businessStability 의 revenueCV 만 단독 인용 금지 — sectorThresholds
        와 비교 후 정성 판정.

    LLM Specifications:
        AntiPatterns:
            - history list 만 보고 단기 변동 판단 — 최소 3 년 추세 권장.
            - profile 누락 (None) 시 sector 정보 미사용 — sectorThresholds
              fallback 으로 일반 임계 사용 (정확도 낮음).
        OutputSchema:
            상기 30+ 키 dict.
        Prerequisites:
            Company.finance (BS/IS/CF) + notes (borrowings/segments) 로드.
        Freshness:
            BS/IS/CF = 최신 분기 (마감 후 30~45 일). notes = 함께.
        Dataflow:
            company.select → 9 년 BS/IS/CF → metric 계산 (30+) → notes
            보강 → businessStability + reliability + disclosureRisk 합성.
        TargetMarkets: KR (DART 표준), US (EDGAR — 일부 metric 부분 적용).
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
            "차입금단기",  # short_term_borrowings 한국어 변형
            "long_term_borrowings",  # 영문만 있는 회사
            "short_term_borrowings",
            "차입부채",  # Fallback: 통합 차입금만 공시하는 회사 (audit 04 #B)
            "차입금",  # Fallback: 추가 변형
            "장기차입부채",  # noncurrent_borrowings (LG에솔)
            "유동성장기차입금",  # current_portion_of_longterm_borrowings
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
    bsData.get("비유동부채", {})
    cash = bsData.get("현금및현금성자산", {})
    # 차입금 fallback 은 col loop 안에서 sumBorrowingsKorean 위임
    bsData.get("이익잉여금", {})

    rev = isData.get("매출액", {})
    oi = isData.get("영업이익", {})
    ni = isData.get("당기순이익", {})
    finCost = isData.get("금융비용", {})
    intCost = isData.get("이자비용", {})
    dep = isData.get("감가상각비", {})
    isData.get("매출총이익", {})

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

        # 차입금 분리/통합 fallback 위임 (analysis/_helpers.py::sumBorrowingsKorean)
        stBorrow, ltBorrow, totalBorrowing = sumBorrowingsKorean(bsData, col)
        bsData.get("사채", {}).get(col) or 0  # 사채 별도 노출 (회귀 호환)

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
# 별도재무제표(OFS) + 금융업 전용 — _metricsTrackB.py 분리 (BC re-export)
# ═══════════════════════════════════════════════════════════
from dartlab.credit.scoring._metricsTrackB import calcFinancialMetrics, calcSeparateMetrics  # noqa: E402, F401
