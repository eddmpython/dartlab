"""재무제표 간 교차검증 — IS-CF 괴리, IS-BS 괴리, 종합 이상 점수.

3개 재무제표가 서로 맞는지, 비정상 패턴이 있는지를 시계열로 추적한다.
"""

from __future__ import annotations

from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

_MAX_YEARS = 8


# ── 유틸 ──


from dartlab.core.utils.safe import getFirst as _getFirst  # SSOT

# ── IS-CF 괴리 ──


@memoizedCalc
def calcIsCfDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """IS-CF 괴리 시계열 — 순이익 vs 영업CF.

    Capabilities:
        - 당기순이익과 영업현금흐름의 연도별 괴리율·방향·비경상 왜곡 플래그.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간 (annualColsFromPeriods 입력).

    Returns:
        dict | None: history 키에 period/netIncome/ocf/divergence/direction/
        nonRecurringDistortion 행 리스트. 데이터 부재 시 None.

    Guide:
        괴리율 = (NI - OCF) / |NI| * 100. 영업이익 대비 NI 가 30% 미만이면
        비경상 왜곡으로 표시.

    When:
        이익의 질·회계 신뢰성 검증, 종합 이상 점수 산출의 1 차 신호.

    How:
        IS 의 당기순이익·영업이익과 CF 의 영업CF 를 매핑 → 연도별 컬럼 순회.

    Requires:
        IS·CF rawNormalized parquet.

    Raises:
        없음.

    Example:
        >>> calcIsCfDivergence(Company("005930"))
        {"history": [{"period": "2024-12", "divergence": 12.3, ...}]}

    SeeAlso:
        - ``calcAnomalyScore``: 종합 이상 점수
        - ``earningsQuality.calcAccrualAnalysis``: 발생액 분석

    AIContext:
        AI 답변에서 이익 - 현금 괴리를 한 줄로 인용할 때.
    """
    isResult = company.select("IS", ["당기순이익", "영업이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])

    isParsed = toDictBySnakeId(isResult)
    cfParsed = toDictBySnakeId(cfResult)
    if isParsed is None or cfParsed is None:
        return None

    isData, _ = isParsed
    cfData, cfPeriods = cfParsed

    niRow = isData.get("당기순이익", {})
    opRow = isData.get("영업이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ni = _getF(niRow, col)
        ocf = _getF(ocfRow, col)
        opIncome = _getF(opRow, col)

        divergence = None
        direction = None
        if ni != 0:
            divergence = (ni - ocf) / abs(ni) * 100
            if ni > ocf:
                direction = "이익과대"
            elif ni < ocf:
                direction = "보수적"
            else:
                direction = "일치"

        # 일회성 왜곡 판정: 영업이익 대비 순이익이 극단적으로 작으면
        # 영업외 일회성 항목(중단사업손실, 대규모 손상 등)이 순이익을 지배
        nonRecurring = False
        if opIncome != 0 and abs(ni) < abs(opIncome) * 0.3:
            nonRecurring = True

        history.append(
            {
                "period": col,
                "netIncome": ni,
                "ocf": ocf,
                "divergence": divergence,
                "direction": direction,
                "nonRecurringDistortion": nonRecurring,
            }
        )

    return {"history": history} if history else None


# ── IS-BS 괴리 ──


@memoizedCalc
def calcIsBsDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """IS-BS 괴리 시계열 — 매출 성장 vs 매출채권/재고 성장.

    Capabilities:
        - 매출 성장률 vs 매출채권/재고 성장률의 %p 차이 (gap) 시계열.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history 키에 period/revenueGrowth/receivableGrowth/
        inventoryGrowth/revRecGap/revInvGap 행 리스트.

    Guide:
        gap > 20%p 는 매출 인식 의심 또는 재고 적체. 부호가 양수이면 BS 가
        더 빨리 증가.

    When:
        매출 인식 정책의 보수성·재고 적체 신호를 시계열로 확인할 때.

    How:
        IS 매출액 + BS 매출채권·재고를 매핑 → 연도별 growth 계산 후 차이 산출.

    Requires:
        BS/IS rawNormalized parquet.

    Raises:
        없음.

    Example:
        >>> calcIsBsDivergence(Company("005930"))
        {"history": [{"period": "...", "revRecGap": 5.2, ...}]}

    SeeAlso:
        - ``calcIsCfDivergence``: 이익-현금 괴리
        - ``calcAnomalyScore``: 종합 점수화

    AIContext:
        AI 답변에서 매출 인식 신뢰성 한 줄 인용 시.
    """
    isResult = company.select("IS", ["매출액"])
    bsResult = company.select("BS", ["매출채권및기타채권", "재고자산"])

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    revRow = isData.get("매출액", {})
    invRow = bsData.get("재고자산", {})

    _REC_KEYS = ["매출채권및기타채권"]

    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for i, col in enumerate(yCols):
        rev = _getF2(revRow, col)
        rec = _getFirst(bsData, _REC_KEYS, col)
        inv = _get(invRow, col)

        revenueGrowth = None
        receivableGrowth = None
        inventoryGrowth = None

        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevRev = _getF2(revRow, prevCol)
            prevRec = _getFirst(bsData, _REC_KEYS, prevCol)
            prevInv = _get(invRow, prevCol)

            if prevRev > 0:
                revenueGrowth = (rev - prevRev) / prevRev * 100
            if prevRec > 0:
                receivableGrowth = (rec - prevRec) / prevRec * 100
            if prevInv > 0:
                inventoryGrowth = (inv - prevInv) / prevInv * 100

        revRecGap = None
        if revenueGrowth is not None and receivableGrowth is not None:
            revRecGap = receivableGrowth - revenueGrowth

        revInvGap = None
        if revenueGrowth is not None and inventoryGrowth is not None:
            revInvGap = inventoryGrowth - revenueGrowth

        history.append(
            {
                "period": col,
                "revenueGrowth": revenueGrowth,
                "receivableGrowth": receivableGrowth,
                "inventoryGrowth": inventoryGrowth,
                "revRecGap": revRecGap,
                "revInvGap": revInvGap,
            }
        )

    return {"history": history} if history else None


# ── 종합 이상 점수 ──


@memoizedCalc
def calcAnomalyScore(company, *, basePeriod: str | None = None) -> dict | None:
    """종합 이상 점수 시계열 — 교차검증 결과 종합.

    Capabilities:
        - IS-CF 괴리 + IS-BS 괴리 + 발생액 + Beneish M-Score 를 5 항목
          가중합 (총 100 점) 으로 종합한 이상 점수 시계열.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history 키에 period/score/components 행 리스트. 데이터
        부재 시 None.

    Guide:
        가중치: IS-CF 30 + 매출채권 gap 20 + 재고 gap 20 + 발생액 15 +
        M-Score 15. 비경상 왜곡 시 IS-CF 절반 감쇄.

    When:
        재무제표 신뢰성에 대한 단일 스코어가 필요한 경우 (분석 보고 헤더).

    How:
        하위 4 calc 함수 결과를 period 키로 묶어 가중합 산출.

    Requires:
        IS/BS/CF 데이터 + earningsQuality 모듈.

    Raises:
        없음.

    Example:
        >>> calcAnomalyScore(Company("005930"))
        {"history": [{"period": "2024-12", "score": 35.2, ...}]}

    SeeAlso:
        - ``calcCrossStatementFlags``: 임계 초과 플래그
        - ``earningsQuality.calcBeneishTimeline``: M-Score

    AIContext:
        AI 답변에서 신뢰성 단일 스코어 인용.
    """
    isCf = calcIsCfDivergence(company, basePeriod=basePeriod)
    isBs = calcIsBsDivergence(company, basePeriod=basePeriod)

    if isCf is None:
        return None

    # 발생액 정보 (earningsQuality에서 가져오기)
    from dartlab.analysis.financial.earningsQuality import calcAccrualAnalysis, calcBeneishTimeline

    accrual = calcAccrualAnalysis(company, basePeriod=basePeriod)
    beneish = calcBeneishTimeline(company, basePeriod=basePeriod)

    # 기간별 데이터 매핑
    isCfMap = {h["period"]: h for h in isCf["history"]} if isCf else {}
    isBsMap = {h["period"]: h for h in isBs["history"]} if isBs else {}
    accrualMap = {h["period"]: h for h in accrual["history"]} if accrual else {}
    beneishMap = {h["period"]: h for h in beneish["history"]} if beneish else {}

    periods = list(isCfMap.keys())
    if not periods:
        return None

    history = []
    for period in periods:
        score = 0
        components = {}

        # 1. IS-CF 괴리 (0~30점)
        cf = isCfMap.get(period, {})
        div = cf.get("divergence")
        if div is not None:
            cfScore = min(30, abs(div) / 100 * 30)
            # 일회성 왜곡(중단사업손실 등)이면 점수 절반 감쇄
            if cf.get("nonRecurringDistortion"):
                cfScore = cfScore * 0.5
            score += cfScore
            components["isCfDivergence"] = cfScore

        # 2. IS-BS 괴리: 매출채권 (0~20점)
        bs = isBsMap.get(period, {})
        recGap = bs.get("revRecGap")
        if recGap is not None and recGap > 0:
            recScore = min(20, recGap / 50 * 20)
            score += recScore
            components["receivableGap"] = recScore

        # 3. IS-BS 괴리: 재고 (0~20점)
        invGap = bs.get("revInvGap")
        if invGap is not None and invGap > 0:
            invScore = min(20, invGap / 50 * 20)
            score += invScore
            components["inventoryGap"] = invScore

        # 4. 발생액 (0~15점)
        acc = accrualMap.get(period, {})
        sar = acc.get("sloanAccrualRatio")
        if sar is not None:
            accScore = min(15, abs(sar) / 0.15 * 15)
            score += accScore
            components["accrualRatio"] = accScore

        # 5. Beneish M-Score 호환 슬롯. 현재 canonical 입력 계약이 없어 map이 비며,
        # 점수를 종합 anomaly에 가산하지 않는다.
        ben = beneishMap.get(period, {})
        ms = ben.get("mScore")
        if ms is not None and ms > -2.22:
            # -2.22~-1.78 = 회색, -1.78+ = 위험
            mScoreNorm = min(15, max(0, (ms + 2.22) / 0.88 * 15))
            score += mScoreNorm
            components["beneishMScore"] = mScoreNorm

        history.append(
            {
                "period": period,
                "score": min(100, score),
                "components": components,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


@memoizedCalc
def calcCrossStatementFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """교차검증 경고 신호.

    Capabilities:
        - IS-CF 50%+ 괴리, 매출채권/재고 20%p+ 초과 성장, 종합 점수 70+ 시
          한국어 경고 문자열 리스트 생성.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        list[str]: 한국어 경고 메시지. 임계 초과 없으면 빈 리스트.

    Guide:
        flags 는 사용자 친화 한국어 한 줄. 정량 점수는 anomaly score 사용.

    When:
        보고서·UI 의 위험 배너 영역에 표시할 경고 문구가 필요할 때.

    How:
        하위 calc 3 종 결과를 임계값과 비교 후 한국어 포맷팅.

    Requires:
        하위 3 calc 가용성.

    Raises:
        없음.

    Example:
        >>> calcCrossStatementFlags(Company("005930"))
        ["IS-CF 괴리 ..."]

    SeeAlso:
        - ``calcAnomalyScore``: 정량 점수

    AIContext:
        AI 답변 위험 경고 배너 인용.
    """
    flags = []

    isCf = calcIsCfDivergence(company, basePeriod=basePeriod)
    if isCf and isCf["history"]:
        h0 = isCf["history"][0]
        div = h0.get("divergence")
        if div is not None and abs(div) > 50:
            suffix = " (일회성 영업외항목 왜곡)" if h0.get("nonRecurringDistortion") else ""
            flags.append(f"IS-CF 괴리 {div:.0f}% — 순이익 대비 현금흐름 극심한 차이{suffix}")

    isBs = calcIsBsDivergence(company, basePeriod=basePeriod)
    if isBs and isBs["history"]:
        h0 = isBs["history"][0]
        recGap = h0.get("revRecGap")
        if recGap is not None and recGap > 20:
            flags.append(f"매출채권 성장이 매출 성장보다 {recGap:.0f}%p 빠름 — 매출 인식 의심")
        invGap = h0.get("revInvGap")
        if invGap is not None and invGap > 20:
            flags.append(f"재고 성장이 매출 성장보다 {invGap:.0f}%p 빠름 — 재고 적체 또는 부풀리기")

    anomaly = calcAnomalyScore(company, basePeriod=basePeriod)
    if anomaly and anomaly["history"]:
        h0 = anomaly["history"][0]
        if h0["score"] > 70:
            flags.append(f"종합 이상점수 {h0['score']:.0f} — 재무제표 신뢰성 주의")

    return flags


# ── BS-CF Articulation Check ──


@memoizedCalc
def calcArticulationCheck(company, *, basePeriod: str | None = None) -> dict | None:
    """BS-CF 정합성 검증 — 재무제표 3표가 수학적으로 연결되는지.

    Capabilities:
        - PPE/현금/자본 정합 3 식의 오차 시계열 산출.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history 키에 period/ppeError/cashError/equityError/
        maxErrorPct 행 리스트. 데이터 부재 시 None.

    Guide:
        정합 식 — delta_PPE ≈ CAPEX - 감가상각 - 처분 / delta_Cash ≈
        OCF + ICF + FCF / delta_Equity ≈ NI - 배당 + OCI + 신주발행. 오차가
        크면 연결범위 변동, 환율 효과, 재분류 가능성.

    When:
        재무제표 연결 변경·재분류·환율 효과 의심 시점에 정합성 검증.

    How:
        BS/CF/IS 3 표를 매핑 후 3 정합 식에 대한 잔차 산출.

    Requires:
        BS/IS/CF rawNormalized parquet.

    Raises:
        없음.

    Example:
        >>> calcArticulationCheck(Company("005930"))
        {"history": [{"period": "...", "maxErrorPct": 3.2, ...}]}

    SeeAlso:
        - ``calcAnomalyScore``: 종합 신뢰성 점수

    AIContext:
        AI 답변에서 연결 범위 변동 가능성 인용 시. 학술근거: Articulation
        of Financial Statements (FASB/IASB).
    """
    bsResult = company.select(
        "BS",
        ["유형자산", "현금및현금성자산", "자본총계"],
    )
    cfResult = company.select(
        "CF",
        ["영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "유형자산의취득", "유형자산의처분"],
    )
    isResult = company.select("IS", ["당기순이익"])

    bsParsed = toDictBySnakeId(bsResult)
    cfParsed = toDictBySnakeId(cfResult)
    isParsed = toDictBySnakeId(isResult)
    if bsParsed is None or cfParsed is None or isParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    cfData, _ = cfParsed
    isData, _ = isParsed

    ppeRow = bsData.get("유형자산", {})
    cashRow = bsData.get("현금및현금성자산", {})
    eqRow = bsData.get("자본총계", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    icfRow = cfData.get("투자활동현금흐름", {})
    fcfRow = cfData.get("재무활동현금흐름", {})
    capexRow = cfData.get("유형자산의취득", {})
    dispRow = cfData.get("유형자산의처분", {})
    niRow = isData.get("당기순이익", {})

    yCols = annualColsFromPeriods(bsPeriods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i in range(len(yCols) - 1):
        col = yCols[i]
        prevCol = yCols[i + 1]

        # 1. PPE 정합
        ppeCur = _get(ppeRow, col)
        ppePrev = _get(ppeRow, prevCol)
        capex = abs(_getF3(capexRow, col))
        disp = abs(_getF3(dispRow, col))
        # 감가상각은 추정 (유형자산/10)
        depEst = ppePrev / 10 if ppePrev > 0 else 0
        ppeExpected = ppePrev + capex - depEst - disp
        ppeActual = ppeCur
        ppeError = abs(ppeActual - ppeExpected) / ppePrev * 100 if ppePrev > 0 else None

        # 2. 현금 정합
        cashCur = _get(cashRow, col)
        cashPrev = _get(cashRow, prevCol)
        ocf = _getF3(ocfRow, col)
        icf = _getF3(icfRow, col)
        fcf = _getF3(fcfRow, col)
        cashExpected = cashPrev + ocf + icf + fcf
        cashError = abs(cashCur - cashExpected) / abs(cashPrev) * 100 if cashPrev != 0 else None

        # 3. 자본 정합
        eqCur = _get(eqRow, col)
        eqPrev = _get(eqRow, prevCol)
        ni = _getF3(niRow, col)
        eqExpected = eqPrev + ni  # 배당/OCI 미포함이므로 대략적
        eqError = abs(eqCur - eqExpected) / abs(eqPrev) * 100 if eqPrev != 0 else None

        errors = [e for e in [ppeError, cashError, eqError] if e is not None]
        maxErr = max(errors) if errors else None

        history.append(
            {
                "period": col,
                "ppeError": round(ppeError, 1) if ppeError is not None else None,
                "cashError": round(cashError, 1) if cashError is not None else None,
                "equityError": round(eqError, 1) if eqError is not None else None,
                "maxErrorPct": round(maxErr, 1) if maxErr is not None else None,
            }
        )

    return {"history": history} if history else None
