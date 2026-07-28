"""2-3 안정성 분석 -- 부채 구조와 지급 능력을 추적한다.

select()로 BS/IS/CF 원본 계정을 가져와서
부채비율 + 이자보상배율 + 부실 판별을 금액과 함께 보여준다.
레버리지가 늘었는지, 이자를 갚을 수 있는지를 금액으로 파악.
"""

from __future__ import annotations

from dartlab.analysis.financial._seriesMath import _yoy
from dartlab.analysis.financial.accountSums import sumBorrowings
from dartlab.analysis.financial.companyContext import getRatios
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import (
    MAX_RATIO_YEARS,
    annualColsFromPeriods,
    toDictBySnakeId,
)

_MAX_YEARS = MAX_RATIO_YEARS


def _isHoldingOrFinancial(company) -> bool:
    """지주사 또는 금융업 판별."""
    try:
        name = getattr(company, "corpName", "") or ""
        if any(k in name for k in ("지주", "홀딩스", "Holdings")):
            return True
        sector = getattr(company, "sector", None)
        if sector is not None:
            from dartlab.frame.sector import Sector

            if sector.sector == Sector.FINANCIALS:
                return True
    except (AttributeError, ImportError):
        pass
    return False


from dartlab.core.utils.calc import safePct as _pctOf  # noqa: E402

# ── 레버리지 구조 시계열 ──


@memoizedCalc
def calcLeverageTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """레버리지 구조 시계열 — 부채로 얼마나 버티는가.

    Capabilities:
        부채총계/자본총계/자산총계/현금/총차입금 원본 + 부채비율/자기자본
        비율/순차입금비율 시계열. 차입금은 회사별 키 패턴 무관 sumBorrowings
        헬퍼로 단·장기 + 사채 + 유동성장기차입금 합산. notesDetail 로 차입금/
        리스 주석 enrichment + injectTurningPoints 로 변곡점 자동 라벨.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 12 키 (period, totalDebt + YoY, equity +
              YoY, totalAssets, cash, totalBorrowing, netDebt, debtRatio,
              equityRatio, netDebtRatio)
            - ``turningPoints`` (list[dict]): debtRatio Δ ≥ 25pp 변곡점
            - ``notesDetail`` (dict, optional): borrowings + lease 주석

    Raises:
        없음.

    Example:
        >>> r = calcLeverageTrend(Company("005930"))
        >>> r["history"][0]["debtRatio"], r["history"][0]["netDebtRatio"]
        (35.2, -8.1)  # 부채비율 35%, 순현금 (netDebt 음수)

    Guide:
        - 부채비율 > 200% 가 2+ 년 연속 = 자본 잠식 위험 (KR 제조업 기준).
        - 순차입금비율 음수 = 순현금 (자기자본보다 현금이 많음, 삼성전자
          전형).
        - 차입금 키 회사별 다양 (사채/유동성장기차입금) → sumBorrowings 가
          12 키 합산하므로 누락 없음.

    When:
        자본 안정성 시계열 진단, credit engine leverage 축 입력 생성.

    How:
        BS rawNormalized → 자본구조 항목·차입금 합산 → 3 비율 + netDebt →
        injectTurningPoints + fetchNotesDetail enrichment.

    SeeAlso:
        - ``calcCoverageTrend``: IC (이자보상)
        - ``calcFundingSources``: 자본/부채/차입 funding mix
        - ``credit.engine``: 7 축 종합 (본 함수가 leverage 축 입력)

    Requires:
        BS (부채총계 + 자본총계 + 자산총계 + 현금 + 차입금 12 키 후보) ≥ 2 년.

    AIContext:
        debtRatio + netDebt 부호 함께 인용. netDebt < 0 (순현금) 회사는
        부채비율 높아도 안전 — netDebt 부호 우선 판단. turningPoints 있으면
        구조 변화 시점 (M&A·구조조정) 시그널로 활용.

    LLM Specifications:
        AntiPatterns:
            - 부채비율 단독 인용 — netDebt 부호 함께 (순현금 회사 오판 방지).
            - 단기·장기 차입금 별도 합산 시도 — sumBorrowings 가 12 키 모두
              합산 (회사별 키 패턴 무관).
        OutputSchema:
            ``{history: list[dict 12키], turningPoints: list, notesDetail?: dict}``.
        Prerequisites:
            BS 7 계정 + 차입금 12 키 후보.
        Freshness:
            분기 + 시계열.
        Dataflow:
            BS → 부채/자본/자산/현금/차입금 → 3 비율 + netDebt →
            injectTurningPoints + fetchNotesDetail enrichment.
        TargetMarkets: KR (DART), US (EDGAR — 표준).
    """
    bsResult = company.select(
        "BS",
        [
            "부채총계",
            "자본총계",
            "자산총계",
            "현금및현금성자산",
            "단기차입금",
            "장기차입금",
            "차입금단기",
            "long_term_borrowings",
            "short_term_borrowings",
            "차입부채",
            "장기차입부채",
            "유동성장기차입금",
            "사채",
        ],
    )
    parsed = toDictBySnakeId(bsResult)
    if parsed is None:
        return None

    data, periods = parsed
    debt = data.get("total_liabilities", {})
    equity = data.get("total_stockholders_equity", {})
    ta = data.get("total_assets", {})
    cash = data.get("cash_and_cash_equivalents", {})

    yCols = annualColsFromPeriods(periods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        d = debt.get(col)
        e = equity.get(col)
        a = ta.get(col)
        c = cash.get(col)

        # 차입금: 회사 키 패턴 무관 헬퍼
        totalBorrowing = sumBorrowings(data, col)
        netDebt = totalBorrowing - (c or 0) if totalBorrowing > 0 else None

        debtRatio = _pctOf(d, e)
        equityRatio = _pctOf(e, a)
        netDebtRatio = _pctOf(netDebt, e) if netDebt is not None else None

        history.append(
            {
                "period": col,
                "totalDebt": d,
                "totalDebtYoy": _yoy(d, debt.get(prevCol)) if prevCol else None,
                "equity": e,
                "equityYoy": _yoy(e, equity.get(prevCol)) if prevCol else None,
                "totalAssets": a,
                "cash": c,
                "totalBorrowing": totalBorrowing if totalBorrowing > 0 else None,
                "netDebt": netDebt,
                "debtRatio": debtRatio,
                "equityRatio": equityRatio,
                "netDebtRatio": netDebtRatio,
            }
        )

    if not history:
        return None

    result: dict = {"history": history}

    # Phase 8 A5
    from dartlab.synth.turningPoint import injectTurningPoints

    result["turningPoints"] = injectTurningPoints(history, seriesKey="debtRatio", minDeltaPct=25.0)

    # notes enrichment — 차입금 구성 + 리스부채
    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    notesDetail = fetchNotesDetail(company, ["borrowings", "lease"])
    if notesDetail:
        result["notesDetail"] = notesDetail

    return result


# ── 이자보상 시계열 ──


@memoizedCalc
def calcCoverageTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """이자보상배율 시계열 — 영업이익으로 이자를 몇 배 커버하는가.

    Capabilities:
        영업이익 / 이자비용 시계열 + 이자비용 소스 추적 (IS 이자비용 → CF
        interest_paid → IS 금융비용 우선순위). 금융비용은 외환손실·파생상품
        등 비이자 항목 포함하여 과대계상 위험이 있어 폴백으로만 사용.
        Damodaran 의 신용등급 매핑 표준 입력.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 5 키 (period + operatingIncome
              + operatingIncomeYoy + interestExpense + interestExpenseSource
              + interestCoverage).

    Raises:
        없음.

    Example:
        >>> r = calcCoverageTrend(Company("005930"))
        >>> r["history"][0]["interestCoverage"]
        18.5  # 이자 18.5 배 커버 — AA 등급 매핑

    Guide:
        Damodaran 신용등급 매핑 (대기업):
        - IC > 12.5: AAA / IC 9.5~12.5: AA / IC 7.5~9.5: A+
        - IC 6~7.5: A / IC 4.5~6: A-/BBB+ / IC 3~4.5: BBB
        - IC 1.5~3: BB / IC < 1: 부도 위험.
        IC < 1 가 2~3 년 연속이면 채무 재조정 신호.

    When:
        이자 부담 시계열 진단, Damodaran 신용등급 매핑 입력 생성.

    How:
        IS 영업이익 + (이자비용 우선) → CF interest_paid → IS 금융비용 폴백
        순으로 이자비용 결정 → IC = 영업이익 / |이자비용|.

    SeeAlso:
        - ``calcLeverageTrend``: 부채/자본 구조
        - ``calcDistressScore``: Altman Z (IC 직접 변수 아님, EBIT/TA)
        - ``credit.scoring.metrics.calcAllMetrics``: 7 축 종합 진단

    Requires:
        IS (영업이익, 이자비용 또는 금융비용) + CF (interest_paid 폴백).

    AIContext:
        IC 절대값 + source + YoY 함께 인용. source = "금융비용" 일 때는
        과대계상 가능성 명시. 순현금 회사 (netDebt < 0) 는 IC 낮아도
        문제 없음 — calcLeverageTrend 함께 확인.

    LLM Specifications:
        AntiPatterns:
            - source 무시하고 IC 인용 — "금융비용" 폴백은 외환손실 포함
              과대계상.
            - 순현금 회사에 IC < 3 → "이자 부담" 단정 — netDebt 함께 확인.
        OutputSchema:
            ``{history: list[dict 5키]}``.
        Prerequisites:
            IS 영업이익 + 이자비용/금융비용 또는 CF interest_paid.
        Freshness:
            분기 + 시계열.
        Dataflow:
            IS → 영업이익 + (이자비용 또는 금융비용) + CF (interest_paid
            폴백) → 우선순위 분기 → IC = 영업이익 / |이자비용|.
        TargetMarkets: KR (DART), US (EDGAR — Interest Expense 표준).
    """
    isResult = company.select("IS", ["영업이익", "금융비용", "이자비용"])
    parsed = toDictBySnakeId(isResult)
    if parsed is None:
        return None

    data, periods = parsed
    op = data.get("operating_profit", {})
    finCost = data.get("finance_costs", {})
    intCost = data.get("interest_expense", {})

    # CF interest_paid (실제 현금 이자 지급액)
    cfIntPaid: dict = {}
    try:
        cfResult = company.select("CF", ["interest_paid"])
        cfParsed = toDictBySnakeId(cfResult)
        if cfParsed is not None:
            cfData, _ = cfParsed
            cfIntPaid = cfData.get("interest_paid", {})
    except (ValueError, KeyError, AttributeError):
        pass

    yCols = annualColsFromPeriods(periods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None
    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        o = op.get(col)

        # 이자비용 우선순위: IS 이자비용 → CF interest_paid → IS 금융비용
        intVal = intCost.get(col)
        cfVal = cfIntPaid.get(col)
        finVal = finCost.get(col)

        if intVal:
            interest = intVal
            source = "이자비용"
        elif cfVal:
            interest = abs(cfVal)  # CF는 지출이라 음수일 수 있음
            source = "CF이자지급"
        elif finVal:
            interest = finVal
            source = "금융비용"
        else:
            interest = None
            source = None

        coverage = None
        if o is not None and interest is not None and interest != 0:
            coverage = round(o / abs(interest), 2)

        history.append(
            {
                "period": col,
                "operatingIncome": o,
                "operatingIncomeYoy": _yoy(o, op.get(prevCol)) if prevCol else None,
                "interestExpense": interest,
                "interestExpenseSource": source,
                "interestCoverage": coverage,
            }
        )

    return {"history": history} if history else None


# ── 부실 판별: calcDistressScore + calcDistressEnsemble 는 _stabilityDistress.py 로 분리 ──

from dartlab.analysis.financial._stabilityDistress import (  # noqa: E402
    calcDistressEnsemble,
    calcDistressScore,
)


@memoizedCalc
def calcDebtMaturity(company, *, basePeriod: str | None = None) -> dict | None:
    """부채 만기 구조 — 단기/장기/사채 + 차환 리스크.

    Capabilities:
        단기차입금/장기차입금/사채 분해 + 단기차입금 비중 + 유동부채/부채총계
        + 차환능력 (단기차입금/OCF) 시계열. 업종별 계정 폴백 (제조 → 금융
        → 바이오). 차환 리스크 (refinancing risk) 정량화.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 8 키 (period + 3 차입금 분해
              + totalBorrowing + 3 비율 지표).

    Raises:
        없음.

    Example:
        >>> r = calcDebtMaturity(Company("005930"))
        >>> r["history"][0]["refinancingRisk"]
        0.8  # OCF 가 단기차입 1.25 배 — 양호

    Guide:
        - 단기차입금 비중 > 50% + refinancingRisk > 2 = 차환 위기 신호.
        - 사채 (회사채) 만기 도래 시 시장 환경 (금리/스프레드) 함께 확인.
        - 금융업/바이오는 차입 구조 다름 — 자동 폴백 분기.

    When:
        차환 리스크 진단·만기 구조 분석 시.

    How:
        BS 차입금 (제조 → 금융 → 바이오 폴백) + CF OCF → 단기 비중·유동/
        부채총계·refinancingRisk 시계열.

    SeeAlso:
        - ``calcLeverageTrend``: 부채/자본 구조 (위 함수와 paired)
        - ``calcCoverageTrend``: 이자보상배율
        - ``calcFundingSources``: 자금조달 원천 (CF/투자/재무)

    Requires:
        BS (단기/장기차입금/사채 또는 차입부채/발행사채 또는 유동/장기금융부채)
        + CF (영업활동현금흐름).

    AIContext:
        단기차입 비중 + refinancingRisk 함께 인용. 단기 비중 높아도
        OCF 가 충분하면 (refinancingRisk < 1) 안전. KR 회사채 시장 활황기 vs
        냉각기에 따라 차환 난이도 달라짐.

    LLM Specifications:
        AntiPatterns:
            - 단기차입금 비중만으로 위험 판정 — OCF 와 비교 필수.
            - 금융업/바이오에 제조업 폴백 기대 — 본 함수가 자동 분기.
        OutputSchema:
            ``{history: list[dict 8키]}``.
        Prerequisites:
            BS 차입금 계정 (업종별 키) + CF 영업현금흐름.
        Freshness:
            BS 분기 + CF 분기.
        Dataflow:
            BS → 단기/장기/사채 (제조) 또는 차입부채/발행사채 (금융) 또는
            유동/장기금융부채 (바이오) → 합산 → CF 영업현금흐름 → 단기/OCF
            = refinancingRisk.
        TargetMarkets: KR (DART 표준), US (EDGAR Long-term/Current Debt).
    """
    bsResult = company.select(
        "BS",
        [
            "단기차입금",
            "장기차입금",
            "사채",
            "차입부채",
            "발행사채",
            "유동금융부채",
            "장기금융부채",
            "유동부채",
            "비유동부채",
            "부채총계",
        ],
    )
    parsed = toDictBySnakeId(bsResult, maxPeriods=5)
    if parsed is None:
        return None

    data, periods = parsed
    # 일반 제조업
    stRow = data.get("단기차입금", {})
    ltRow = data.get("장기차입금", {})
    bondsRow = data.get("사채", {})
    # 금융업
    borrowRow = data.get("차입부채", {})
    issuedBondRow = data.get("발행사채", {})
    # 바이오 등
    curFinRow = data.get("유동금융부채", {})
    ltFinRow = data.get("장기금융부채", {})

    clRow = data.get("유동부채", {})
    data.get("비유동부채", {})
    tlRow = data.get("부채총계", {})

    # 연도 컬럼만
    annualPeriods = annualColsFromPeriods(periods, basePeriod, 5)
    if not annualPeriods:
        return None

    # OCF for 차환능력 평가
    cfResult = company.select("CF", ["영업활동현금흐름"])
    cfParsed = toDictBySnakeId(cfResult, maxPeriods=5) if cfResult else None
    cfData = cfParsed[0] if cfParsed else {}
    ocfRow = cfData.get("영업활동현금흐름", {})
    history = []
    for col in annualPeriods:
        # 차입금: 업종별 계정 대응
        st = stRow.get(col) or 0
        lt = ltRow.get(col) or 0
        bondsVal = bondsRow.get(col) or 0
        totalBorrowing = st + lt + bondsVal

        # 금융업 fallback
        if totalBorrowing == 0:
            borrow = borrowRow.get(col) or 0
            issued = issuedBondRow.get(col) or 0
            totalBorrowing = borrow + issued
            st = borrow  # 금융업 차입부채를 단기로 근사
            lt = issued

        # 바이오 등 fallback
        if totalBorrowing == 0:
            curFin = curFinRow.get(col) or 0
            ltFin = ltFinRow.get(col) or 0
            totalBorrowing = curFin + ltFin
            st = curFin
            lt = ltFin

        cl = clRow.get(col) or 0
        tl = tlRow.get(col) or 0
        ocf = ocfRow.get(col)

        shortTermRatio = round(st / totalBorrowing * 100, 2) if totalBorrowing > 0 else None
        currentToTotal = round(cl / tl * 100, 2) if tl > 0 else None

        # 단기차입금/OCF = 차환능력 (낮을수록 안전)
        refinancingRisk = None
        if ocf is not None and ocf > 0 and st > 0:
            refinancingRisk = round(st / ocf, 2)

        history.append(
            {
                "period": col,
                "shortTermBorrowing": st,
                "longTermBorrowing": lt,
                "bonds": bondsVal,
                "totalBorrowing": totalBorrowing,
                "shortTermRatio": shortTermRatio,
                "currentToTotalDebt": currentToTotal,
                "refinancingRisk": refinancingRisk,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


@memoizedCalc
def calcStabilityFlags(company, *, basePeriod: str | None = None) -> dict:
    """안정성 경고/기회 플래그.

    Capabilities:
        - 부채비율·IC·차환 리스크 임계 초과 시 한국어 flags + enrichedFlags
          (메타 포함) 동시 산출.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict: flags (한국어 메시지 리스트) + enrichedFlags (메타 dict 리스트).

    Guide:
        지주/금융사 vs 제조업의 임계 자동 분기. 단기 비중 + OCF 동시 평가.

    When:
        보고서·UI 위험 배너에 안정성 경고 한 줄 표시.

    How:
        ``calcLeverageTrend`` + ``calcCoverageTrend`` + ``calcDebtMaturity``
        결과를 업종별 임계와 비교 후 (메시지, 메타) 생성.

    Requires:
        하위 3 calc 가용성.

    Raises:
        없음.

    Example:
        >>> calcStabilityFlags(Company("005930"))
        {"flags": ["..."], "enrichedFlags": [...]}

    SeeAlso:
        - ``calcLeverageTrend``: 본 함수 입력

    AIContext:
        AI 답변에서 안정성 위험 한 줄 인용 시.
    """
    flags: list[str] = []
    enriched: list[dict] = []

    # 레버리지
    isFinancial = _isHoldingOrFinancial(company)
    lev = calcLeverageTrend(company, basePeriod=basePeriod)
    if lev and lev["history"]:
        hist = lev["history"]
        h0 = hist[0]
        dr = h0.get("debtRatio")
        if dr is not None:
            if isFinancial:
                # 금융업: 예수부채로 부채비율이 구조적으로 높음. 비금융 기준 적용 불가
                # 양호/보통은 플래그로 안 넣음 (중복 방지). 과다만 경고.
                if dr >= 1500:
                    flags.append(f"부채비율 {dr:.0f}% -- 금융업 과다")
            elif dr > 200:
                flags.append(f"부채비율 {dr:.0f}% -- 재무 위험")
            elif dr < 50:
                flags.append(f"부채비율 {dr:.0f}% -- 매우 안정")

        # 부채 3기 연속 증가
        if len(hist) >= 3:
            debts = [h.get("totalDebt") for h in hist[:3]]
            if all(v is not None for v in debts) and debts[0] > debts[1] > debts[2]:
                yoy = h0.get("totalDebtYoy")
                flags.append(f"부채 3기 연속 증가 (최근 +{yoy:.0f}%)" if yoy else "부채 3기 연속 증가")

    # 이자보상
    cov = calcCoverageTrend(company, basePeriod=basePeriod)
    if cov and cov["history"]:
        h0 = cov["history"][0]
        ic = h0.get("interestCoverage")
        source = h0.get("interestExpenseSource")
        # 순현금 여부 확인 -- 순현금이면 금융비용 기반 저배율은 오진 가능
        isNetCash = False
        if lev and lev["history"]:
            nd = lev["history"][0].get("netDebt")
            if nd is not None and nd < 0:
                isNetCash = True
        # 지주사/금융업: 영업이익 구조적 저수준 (지분법이익이 영업외에 잡힘)
        if ic is not None:
            if isFinancial:
                # 지주사/금융은 영업이익 기반 이자보상배율이 구조적으로 낮음
                if ic < 1:
                    flags.append(f"이자보상배율 {ic:.1f}배 -- 지주/금융 구조상 저수준 (영업외 수익이 이자 커버)")
            elif ic < 1 and not isNetCash:
                flags.append(f"이자보상배율 {ic:.1f}배 -- 이자 지급 불능 위험")
            elif ic < 3 and not (isNetCash and source == "금융비용"):
                flags.append(f"이자보상배율 {ic:.1f}배 -- 이자 부담 과다")

    # Altman Z-Score (제조업 기반 모형 — 금융/지주사는 구조적 왜곡)
    if not isFinancial:
        distress = calcDistressScore(company, basePeriod=basePeriod)
        if distress and distress.get("latestScore") is not None:
            z = distress["latestScore"]
            if z < 1.81:
                msg = f"Altman Z-Score {z:.2f} -- 부실 위험 구간"
                flags.append(msg)
                meta = distress.get("diagnosticMeta", {})
                enriched.append(
                    {
                        "code": "ALTMAN_DISTRESS",
                        "message": msg,
                        "precision": meta.get("precision"),
                        "baseRate": meta.get("marketNote", ""),
                        "reference": meta.get("reference", ""),
                        "sectorNote": "금융업/지주회사 부채 구조 왜곡 — Z-Score 부적합" if isFinancial else "",
                    }
                )

    return {"flags": flags, "enrichedFlags": enriched}
