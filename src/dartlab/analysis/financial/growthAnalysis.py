"""2-2 성장성 분석 -- 무엇이 얼마나 커졌는가.

select()로 IS/BS/CF 원본 계정을 가져와서
금액 + YoY + CAGR + 이익 vs 매출 성장 괴리를 시계열로 보여준다.
"""

from __future__ import annotations

from dartlab.analysis.financial._seriesMath import _yoy
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, toDictBySnakeId
from dartlab.core.utils.helpers import annualColsFromPeriods as _annualColsFromPeriods

_MAX_YEARS = MAX_RATIO_YEARS


def _cagrFromList(values: list[float | None], periods: int) -> float | None:
    """양수 값 리스트에서 CAGR 산출.

    Returns
    -------
    float | None
        연복합성장률 (%). 양수 값 2개 미만이면 None.
    """
    valid = [v for v in values if v is not None and v > 0]
    if len(valid) < 2 or periods < 1:
        return None
    first, last = valid[0], valid[-1]
    if first <= 0:
        return None
    return round((pow(last / first, 1 / periods) - 1) * 100, 2)


# ── 성장 추이 ──


@memoizedCalc
def calcGrowthTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """성장 추이: 매출/영업이익/순이익/자산 금액 + YoY + 3 년 CAGR.

    Capabilities:
        IS + BS 의 4 핵심 지표 (revenue, operatingIncome, netIncome,
        totalAssets) 의 절대값 + YoY 변화 시계열 + 3 년 CAGR 산출. 성장 vs
        규모 동시 관찰. analysis() 성장성 축의 핵심 함수.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 9 키 (period + 4 지표 ×
              절대값/YoY)
            - ``cagr`` (dict): ``{revenue, operatingIncome, netIncome}`` 3 년 CAGR

    Raises:
        없음.

    Example:
        >>> r = calcGrowthTrend(Company("005930"))
        >>> r["cagr"]["revenue"], r["history"][0]["revenueYoy"]
        (8.5, 12.3)  # 3 년 CAGR 8.5%, 최근 YoY 12.3%

    Guide:
        revenue CAGR > 15% = 고성장, 5~15% = 중간, < 5% = 성숙. operatingIncome
        CAGR 이 revenue CAGR 보다 높으면 마진 개선 (operating leverage), 반대면
        마진 압박. totalAssets CAGR > revenue CAGR = 효율성 저하 신호.

    When:
        analysis() 성장성 축 시계열·표 표시, 보고서 헤더 CAGR 인용 시.

    How:
        IS + BS 시계열을 연도별 컬럼으로 매핑 → YoY/CAGR + turning point 주입.

    SeeAlso:
        - ``calcGrowthQuality``: 성장의 품질 (organic vs M&A 등)
        - ``calcSustainableGrowthRate``: ROE × (1-payout) sustainable rate
        - ``calcCagrComparison``: 동종 업종 CAGR 비교

    Requires:
        IS/매출액/영업이익/당기순이익 + BS/자산총계 시계열 ≥ 4 년 (CAGR 3 년).

    AIContext:
        cagr dict 의 3 지표 모두 양수 + 균형 = 우수 성장. cagr.revenue 만
        높고 operatingIncome 저조 = 외형 성장 + 마진 압박 (분석 깊이 필요).

    LLM Specifications:
        AntiPatterns:
            - YoY 1 년 변화만 보고 추세 단정. CAGR 3 년 함께 확인 필수.
            - revenue CAGR 음수 단정 → "쇠퇴". turnaround 시기 가능, 3 년
              vs 5 년 CAGR 비교.
        OutputSchema:
            ``{history: list[dict 9키], cagr: dict 3키}``.
        Prerequisites:
            IS + BS 시계열 ≥ 4 년.
        Freshness:
            최신 분기 + 시계열.
        Dataflow:
            IS → revenue/operatingIncome/netIncome 시계열 + BS → totalAssets
            → YoY + CAGR.
        TargetMarkets: KR (DART), US (EDGAR).
    """
    isResult = company.select("IS", ["매출액", "영업이익", "당기순이익"])
    bsResult = company.select("BS", ["자산총계"])

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData = bsParsed[0] if bsParsed else {}

    rev = isData.get("매출액", {})
    op = isData.get("영업이익", {})
    ni = isData.get("당기순이익", {})
    ta = bsData.get("자산총계", {})

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
    if len(yCols) < 2:
        return None
    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None

        _r = rev.get(col)
        _o = op.get(col)
        _n = ni.get(col)
        _rP = rev.get(prevCol) if prevCol else None
        _oP = op.get(prevCol) if prevCol else None
        _nP = ni.get(prevCol) if prevCol else None

        history.append(
            {
                "period": col,
                "revenue": _r,
                "revenueYoy": _yoy(_r, _rP) if prevCol else None,
                "operatingIncome": _o,
                "operatingIncomeYoy": _yoy(_o, _oP) if prevCol else None,
                "netIncome": _n,
                "netIncomeYoy": _yoy(_n, _nP) if prevCol else None,
                "totalAssets": ta.get(col),
                "totalAssetsYoy": _yoy(ta.get(col), ta.get(prevCol)) if prevCol else None,
            }
        )

    # CAGR
    revVals = [rev.get(c) for c in reversed(yCols)]
    opVals = [op.get(c) for c in reversed(yCols)]
    niVals = [ni.get(c) for c in reversed(yCols)]
    n = len(yCols) - 1

    # Phase 8 A5
    from dartlab.synth.turningPoint import injectTurningPoints

    turning_points = injectTurningPoints(history, seriesKey="revenueYoy", minDeltaPct=30.0)

    return (
        {
            "history": history,
            "cagr": {
                "revenue": _cagrFromList(revVals, n),
                "operatingIncome": _cagrFromList(opVals, n),
                "netIncome": _cagrFromList(niVals, n),
                "periods": n,
            },
            "turningPoints": turning_points,
        }
        if history
        else None
    )


# ── 성장 품질 ──


@memoizedCalc
def calcGrowthQuality(company, *, basePeriod: str | None = None) -> dict | None:
    """성장 품질: 매출 성장이 이익으로 이어지는가.

    Capabilities:
        매출 CAGR vs 영업이익 CAGR 비교 → 품질 판정 (균형/내실/외형/개선/
        역성장). 연도별 YoY 비교로 operating leverage 시계열 산출. 외형
        위주 (이익 < 매출 성장 절반) 식별.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``quality`` (str): "역성장"|"이익 역성장"|"외형 위주"|"개선 중"|
              "내실 위주"|"균형"|"판단 불가"
            - ``cagr`` (dict): 3 년 CAGR (revenue/operatingIncome/netIncome).
            - ``leverageEffect`` (list[dict]): 연도별 op-leverage 시계열.

    Raises:
        없음.

    Example:
        >>> r = calcGrowthQuality(Company("005930"))
        >>> r["quality"], r["cagr"]["revenue"]
        ('균형', 8.5)

    Guide:
        "외형 위주" (이익 CAGR < 매출 CAGR × 0.5) 가 2~3 년 연속이면 마진
        압박 경고. 최근 영업이익 YoY > 10% 면 "개선 중" 으로 완화 (턴어라운드
        기업 배려). "내실 위주" = 이익 CAGR > 매출 CAGR × 1.5.

    When:
        성장의 질 정성 라벨이 필요할 때 (외형 vs 내실 판정·op leverage 시계열).

    How:
        ``calcGrowthTrend`` 의 cagr·history 를 받아 비율 비교 → quality
        라벨 + leverageEffect 시계열 산출.

    SeeAlso:
        - ``calcGrowthTrend``: 본 함수의 입력 (CAGR + 시계열)
        - ``calcSustainableGrowthRate``: SGR vs 실제 갭
        - ``calcOperatingLeverage``: DOL 시계열

    Requires:
        IS (매출/영업이익/순이익) ≥ 2 년 (calcGrowthTrend 결과 사용).

    AIContext:
        quality 라벨 + cagr 절대값 + leverage 추세 함께 인용. KR 회사 흔한
        함정: 매출 성장 강조 후 이익 정체 (외형 위주). 본 함수가 자동 라벨링.

    LLM Specifications:
        AntiPatterns:
            - quality 라벨 단독 인용. CAGR 절대값 함께.
            - "외형 위주" 단년도 판정. 본 함수가 3 년 CAGR 기반 자동.
        OutputSchema:
            ``{quality: str, cagr: dict, leverageEffect: list[dict 4키]}``.
        Prerequisites:
            IS 시계열 ≥ 2 년 (calcGrowthTrend 결과).
        Freshness:
            분기 + 시계열.
        Dataflow:
            calcGrowthTrend → CAGR + YoY → 매출 vs 이익 비교 → quality 라벨 +
            op-leverage 시계열.
        TargetMarkets: KR (DART), US (EDGAR, IS 표준).
    """
    trend = calcGrowthTrend(company, basePeriod=basePeriod)
    if trend is None or len(trend["history"]) < 2:
        return None

    cagr = trend["cagr"]
    revCagr = cagr.get("revenue")
    opCagr = cagr.get("operatingIncome")

    niCagr = cagr.get("netIncome")
    hist = trend["history"]

    quality = "판단 불가"
    if revCagr is not None and opCagr is not None:
        if revCagr < 0:
            quality = "역성장"
        elif niCagr is not None and niCagr < -5:
            quality = "이익 역성장"
        elif opCagr < revCagr * 0.5:
            # 최신 기 영업이익 YoY가 양수이면 "개선 중"으로 완화 (턴어라운드 기업 배려)
            latestOpYoy = hist[0].get("operatingIncomeYoy") if hist else None
            if latestOpYoy is not None and latestOpYoy > 10:
                quality = "개선 중"
            else:
                quality = "외형 위주"
        elif opCagr > revCagr * 1.5 and opCagr > 0:
            quality = "내실 위주"
        elif revCagr > 0 and opCagr > 0:
            quality = "균형"

    # 이익 성장률이 매출보다 빠른지 (operating leverage)
    hist = trend["history"]
    leverageEffect = []
    for h in hist:
        ry = h.get("revenueYoy")
        oy = h.get("operatingIncomeYoy")
        if ry is not None and oy is not None and ry != 0:
            leverageEffect.append(
                {
                    "period": h["period"],
                    "revenueYoy": ry,
                    "operatingIncomeYoy": oy,
                    "operatingLeverage": round(oy / ry, 2),
                }
            )

    return {
        "quality": quality,
        "cagr": cagr,
        "leverageEffect": leverageEffect,
    }


# ── SGR + 갭 ──


@memoizedCalc
def calcSustainableGrowthRate(company, *, basePeriod: str | None = None) -> dict | None:
    """지속가능성장률 (SGR) vs 실제 매출성장률 갭: 외부 자본 필요 여부 판정.

    Capabilities:
        Higgins (1981) SGR = ROE × (1 - payout). 내부 retained 만으로 가능
        성장률. 실제 매출성장률과 비교해 양수 갭 = 외부 자본 (debt 또는 equity
        issuance) 필요, 음수 갭 = 잉여 (자사주매입/배당 확대 여력).

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 9 키 (period, revenue,
              netIncome, equity, roe, payoutRatio, sgr, actualGrowth, gap)

    Raises:
        없음.

    Example:
        >>> r = calcSustainableGrowthRate(Company("005930"))
        >>> r["history"][0]
        {'roe': 15, 'payoutRatio': 25, 'sgr': 11.25, 'actualGrowth': 8,
         'gap': -3.25, ...}
        # 실제 8% < SGR 11.25% → 여유 (자사주매입/배당 확대 가능)

    Guide:
        gap > 5%p = 외부 자본 강한 필요 (보통 유상증자 or 신규 차입 발생).
        gap < -5%p = 누적 현금. 자사주매입 (조용한 환원) 또는 배당 확대
        가능. KR 우량 회사 (삼성/현대) 는 보통 gap 음수.

    When:
        외부 자금 의존도·자사주 환원 여력 진단, 재무 정책 적정성 검토.

    How:
        IS/BS/CF 매핑 → ROE = NI/Equity → payoutRatio = 배당/NI → SGR =
        ROE × (1 - payout/100) → gap = actualGrowth - SGR.

    SeeAlso:
        - ``calcGrowthTrend``: 실제 성장률 시계열
        - ``calcDividendPolicy``: 배당성향 (본 함수 입력)
        - ``calcShareholderReturn``: 자사주매입 + 배당 합산

    Requires:
        IS (매출/순이익) + BS (자본총계) + CF (배당) ≥ 2 년.

    AIContext:
        gap 부호 함께 노출. "외부 자본 필요" vs "여유" 라벨로 직관적 설명.
        ROE 가 낮은 (5% 미만) 회사는 SGR 도 낮아 gap 양수 흔함.

    LLM Specifications:
        AntiPatterns:
            - 단년도 gap 만 보고 "유상증자 임박" 단정. 3 년 추세 + 차입금
              증가율 함께 확인.
            - 무배당 (payoutRatio=0) 회사 → SGR = ROE 그대로. 정상.
        OutputSchema:
            ``{history: list[dict 9키]}``.
        Prerequisites:
            IS/BS/CF 시계열 ≥ 2 년.
        Freshness:
            최신 분기.
        Dataflow:
            IS → revenue/NI → BS → equity → ROE = NI/Equity → CF/dividends
            → payoutRatio → SGR = ROE × (1 - payout/100) → gap = actual - SGR.
        TargetMarkets: KR (DART), US (EDGAR).
    """
    # snakeId 단일 패턴
    isResult = company.select("IS", ["매출액", "당기순이익"])
    bsResult = company.select("BS", ["자본총계"])
    cfResult = company.select("CF", ["dividends_paid"])

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    cfParsed = toDictBySnakeId(cfResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    rev = isData.get("sales", {})
    ni = isData.get("net_profit", {})
    eq = bsData.get("stockholders_equity", {})

    divRow = cfParsed[0].get("dividends_paid", {}) if cfParsed else {}

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
    if len(yCols) < 2:
        return None
    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        niVal = ni.get(col)
        eqVal = eq.get(col)
        revVal = rev.get(col)
        revPrev = rev.get(prevCol) if prevCol else None

        roe = round(niVal / eqVal * 100, 2) if niVal is not None and eqVal and eqVal != 0 else None
        actualGrowth = _yoy(revVal, revPrev)
        divPaid = abs(divRow.get(col) or 0)
        payoutRatio = round(divPaid / niVal * 100, 2) if niVal and niVal > 0 and divPaid > 0 else None

        sgr = None
        retentionRatio = None
        if roe is not None:
            if payoutRatio is not None and payoutRatio >= 0:
                retentionRatio = round(1 - payoutRatio / 100, 4)
            else:
                retentionRatio = 1.0
            sgr = round(roe * retentionRatio, 2)

        gap = round(actualGrowth - sgr, 2) if sgr is not None and actualGrowth is not None else None

        history.append(
            {
                "period": col,
                "revenue": revVal,
                "netIncome": niVal,
                "equity": eqVal,
                "roe": roe,
                "payoutRatio": payoutRatio,
                "sgr": sgr,
                "actualGrowth": actualGrowth,
                "gap": gap,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


@memoizedCalc
def calcGrowthFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """성장성 경고/기회 플래그.

    Capabilities:
        - 매출 3 기 연속 역성장·매출 고성장 (20%+)·성장-이익 괴리 시 한국어
          flags 생성.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        list[str]: 한국어 경고/기회 메시지. 임계 미달 시 빈 리스트.

    Guide:
        외형 성장 (매출 ≥ 10%) + 이익 감소 (영업이익 < 0) 동시 발생 시
        수익성 희석 경고.

    When:
        보고서·UI 위험 배너에 성장 관련 경고 한 줄 표시할 때.

    How:
        ``calcGrowthTrend`` 의 history 를 임계값과 비교 후 한국어 포맷팅.

    Requires:
        ``calcGrowthTrend`` 가용성.

    Raises:
        없음.

    Example:
        >>> calcGrowthFlags(Company("005930"))
        ["매출 고성장 (25.0%)"]

    SeeAlso:
        - ``calcGrowthTrend``: 본 함수 입력

    AIContext:
        AI 답변 성장성 경고 인용 시.
    """
    flags: list[str] = []

    trend = calcGrowthTrend(company, basePeriod=basePeriod)
    if trend is None:
        return flags

    hist = trend["history"]

    # 매출 3기 연속 역성장
    if len(hist) >= 3:
        revYoys = [h.get("revenueYoy") for h in hist[:3]]
        if all(v is not None and v < 0 for v in revYoys):
            flags.append(f"매출 3기 연속 역성장 (최근 {revYoys[0]:.1f}%)")

    # 매출 고성장
    if hist and hist[0].get("revenueYoy") is not None and hist[0]["revenueYoy"] > 20:
        flags.append(f"매출 고성장 ({hist[0]['revenueYoy']:.1f}%)")

    # 매출 성장 > 이익 감소 괴리
    if hist:
        h = hist[0]
        ry = h.get("revenueYoy")
        oy = h.get("operatingIncomeYoy")
        if ry is not None and oy is not None and ry > 10 and oy < 0:
            flags.append(f"매출 성장({ry:.0f}%)에도 이익 감소({oy:.0f}%) -- 수익성 희석")

    return flags


# ── 계정별 CAGR 비교 ──


from dartlab.core.utils.calc import cagr as _cagr  # noqa: E402


@memoizedCalc
def calcCagrComparison(company, *, basePeriod: str | None = None) -> dict | None:
    """계정별 CAGR 비교: 장기 구조 변화 감지.

    Capabilities:
        매출/영업이익/자산/부채/자본 5 계정의 CAGR (Compound Annual Growth
        Rate) 산출 + 3 쌍 비교 (매출 vs 영업이익 = 마진 방향, 자산 vs 매출 =
        효율 방향, 부채 vs 자본 = 레버리지 방향). 각 쌍에 양호/주의/경고
        signal 자동 라벨.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``comparisons`` (list[dict]): 3 쌍 비교 (label, item1/cagr1,
              item2/cagr2, gap, signal).
            - ``period`` (str): CAGR 산출 기간 ("2017 → 2025").

    Raises:
        없음.

    Example:
        >>> r = calcCagrComparison(Company("005930"))
        >>> r["comparisons"][0]["signal"]
        '양호'  # 영업이익 > 매출 CAGR

    Guide:
        - 자산 CAGR > 매출 CAGR + 5pp = 자산 효율 악화 (놀고 있는 자산 증가).
        - 부채 CAGR > 자본 CAGR + 10pp = 레버리지 확대 (유의).
        - 영업이익 CAGR < 매출 CAGR - 5pp = 마진 압박.
        Damodaran "intrinsic growth" 평가 시 매출 CAGR 가 출발점.

    When:
        장기 구조 변화 진단 (마진 방향·자산 효율·레버리지) 시.

    How:
        IS/BS 5 계정 CAGR 산출 → 3 쌍 비교 (매출-영업이익, 자산-매출,
        부채-자본) → gap 임계로 양호/주의/경고 라벨링.

    SeeAlso:
        - ``calcGrowthTrend``: 단기 YoY + 3y CAGR
        - ``calcGrowthQuality``: 매출/이익 CAGR 정성 판정
        - ``calcAssetStructure``: 자산 영업/비영업 분리

    Requires:
        IS (매출/영업이익) + BS (자산/부채/자본) ≥ 3 년.

    AIContext:
        gap + signal 함께 인용. 단년도 비교 아님. 장기 (3+ 년) 구조 변화
        진단. 산업 사이클 (반도체/조선) 회사는 단기 CAGR 왜곡 가능. 사이클
        포함 7~10 년 권장.

    LLM Specifications:
        AntiPatterns:
            - 1~2 년 CAGR 인용. 사이클 왜곡, 최소 3 년 (본 함수가 강제).
            - signal "경고" 단독 인용. gap 절대값 + 산업 평균 함께.
        OutputSchema:
            ``{comparisons: list[dict 7키], period: str}``.
        Prerequisites:
            IS + BS 시계열 ≥ 3 년.
        Freshness:
            연간 (CAGR 의 본질).
        Dataflow:
            IS/BS → 매출/영업이익/자산/부채/자본 → CAGR 5 종 → 3 쌍 비교 →
            gap → signal 라벨.
        TargetMarkets: KR (DART), US (EDGAR, 표준).
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    bsResult = company.select("BS", ["자산총계", "부채총계", "자본총계"])
    cfResult = company.select("CF", ["유형자산의취득"])

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    cfParsed = toDictBySnakeId(cfResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed
    cfData = cfParsed[0] if cfParsed else {}

    yCols = _annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 3:
        return None

    def _v(row, col):
        """BS 행에서 값 추출 (None → 0)."""
        v = row.get(col) if row else None
        return v if v is not None else 0

    def _vF(row, col):
        """IS/CF flow 행에서 값 추출 (None → 0)."""
        v = row.get(col)
        return v if v is not None else 0

    latest = yCols[0]
    oldest = yCols[-1]
    years = len(yCols) - 1

    revRow = isData.get("매출액", {})
    opRow = isData.get("영업이익", {})
    taRow = bsData.get("자산총계", {})
    tlRow = bsData.get("부채총계", {})
    teRow = bsData.get("자본총계", {})
    capexRow = cfData.get("유형자산의취득", {})

    pairs = [
        (
            "마진 방향",
            "매출",
            _vF(revRow, oldest),
            _vF(revRow, latest),
            "영업이익",
            _vF(opRow, oldest),
            _vF(opRow, latest),
        ),
        ("자산 효율", "자산", _v(taRow, oldest), _v(taRow, latest), "매출", _vF(revRow, oldest), _vF(revRow, latest)),
        ("레버리지", "부채", _v(tlRow, oldest), _v(tlRow, latest), "자본", _v(teRow, oldest), _v(teRow, latest)),
        (
            "투자 방향",
            "CAPEX",
            abs(_vF(capexRow, oldest)),
            abs(_vF(capexRow, latest)),
            "매출",
            _vF(revRow, oldest),
            _vF(revRow, latest),
        ),
    ]

    comparisons = []
    for label, name1, start1, end1, name2, start2, end2 in pairs:
        c1 = _cagr(start1, end1, years)
        c2 = _cagr(start2, end2, years)
        if c1 is not None and c2 is not None:
            gap = round(c1 - c2, 2)
            if label == "마진 방향":
                signal = "마진 확대" if gap <= 0 else "마진 압박"
            elif label == "자산 효율":
                signal = "효율 개선" if gap <= 0 else "효율 하락"
            elif label == "레버리지":
                signal = "디레버리징" if gap <= 0 else "레버리지 확대"
            else:
                signal = "투자 확대" if gap > 0 else "투자 축소"
            comparisons.append(
                {
                    "label": label,
                    "item1": name1,
                    "cagr1": c1,
                    "item2": name2,
                    "cagr2": c2,
                    "gap": gap,
                    "signal": signal,
                }
            )

    if not comparisons:
        return None
    return {"comparisons": comparisons, "period": f"{oldest} → {latest}"}
