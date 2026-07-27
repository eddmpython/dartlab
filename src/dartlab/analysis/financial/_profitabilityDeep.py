"""profitability.py 깊이 분석 — calcMarginWaterfall + calcPenmanDecomposition + calcRoicTree.

본체 profitability.py 에서 분리, BC re-export 로 호환 유지.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial.accountSums import sumBorrowings
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safePct as _pctOf
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get
_MAX_YEARS = MAX_RATIO_YEARS


def _yoy(*args, **kwargs):
    from dartlab.analysis.financial.profitability import _yoy as _f

    return _f(*args, **kwargs)


def _isFinancialSector(*args, **kwargs):
    from dartlab.analysis.financial.profitability import _isFinancialSector as _f

    return _f(*args, **kwargs)


def _waterfallSteps(col: str, r: float, rows: dict[str, dict], pctFn) -> list[dict]:
    """한 연도의 매출에서 순이익까지 단계 목록. 없는 계정은 단계를 건너뛴다.

    Parameters
    ----------
    col : str
        연도 컬럼.
    r : float
        매출액 (0 아님이 보장됨).
    rows : dict[str, dict]
        cogs/gp/sga/op/finCost/finInc/pbt/tax/ni 행 dict.
    pctFn : Callable
        매출 대비 비율 계산 함수.

    Returns
    -------
    list[dict]
        label / amount / pct / cumPct 단계 목록.
    """
    steps = [{"label": "매출", "amount": r, "pct": 100.0, "cumPct": 100.0}]

    cogsV = rows["cogs"].get(col)
    gpV = rows["gp"].get(col)
    if cogsV is not None:
        steps.append(
            {
                "label": "매출원가",
                "amount": cogsV,
                "pct": -abs(pctFn(cogsV, r) or 0),
                "cumPct": pctFn(gpV, r) or round(100 - abs(pctFn(cogsV, r) or 0), 2),
            }
        )
    if gpV is not None:
        steps.append({"label": "매출총이익", "amount": gpV, "pct": pctFn(gpV, r), "cumPct": pctFn(gpV, r)})

    sgaV = rows["sga"].get(col)
    opV = rows["op"].get(col)
    if sgaV is not None:
        steps.append(
            {
                "label": "판관비",
                "amount": sgaV,
                "pct": -abs(pctFn(sgaV, r) or 0),
                "cumPct": pctFn(opV, r) or round((pctFn(gpV, r) or 0) - abs(pctFn(sgaV, r) or 0), 2),
            }
        )
    if opV is not None:
        steps.append({"label": "영업이익", "amount": opV, "pct": pctFn(opV, r), "cumPct": pctFn(opV, r)})

    fcV = rows["finCost"].get(col)
    fiV = rows["finInc"].get(col)
    opPct = pctFn(opV, r) or 0
    if fcV is not None:
        steps.append(
            {
                "label": "금융비용",
                "amount": fcV,
                "pct": -abs(pctFn(fcV, r) or 0),
                "cumPct": round(opPct - abs(pctFn(fcV, r) or 0), 2),
            }
        )
    if fiV is not None:
        steps.append(
            {
                "label": "금융수익",
                "amount": fiV,
                "pct": abs(pctFn(fiV, r) or 0),
                "cumPct": round(opPct - abs(pctFn(fcV, r) or 0) + abs(pctFn(fiV, r) or 0), 2),
            }
        )

    pbtV = rows["pbt"].get(col)
    if pbtV is not None:
        steps.append({"label": "세전이익", "amount": pbtV, "pct": pctFn(pbtV, r), "cumPct": pctFn(pbtV, r)})

    taxV = rows["tax"].get(col)
    if taxV is not None:
        steps.append(
            {
                "label": "법인세",
                "amount": taxV,
                "pct": -abs(pctFn(taxV, r) or 0),
                "cumPct": round((pctFn(pbtV, r) or 0) - abs(pctFn(taxV, r) or 0), 2),
            }
        )

    niV = rows["ni"].get(col)
    if niV is not None:
        steps.append({"label": "순이익", "amount": niV, "pct": pctFn(niV, r), "cumPct": pctFn(niV, r)})

    return steps


@memoizedCalc
def calcMarginWaterfall(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 → 순이익 워터폴 분해 — 단계별 금액 + 매출 대비 비중.

    Capabilities:
        매출 출발 → 매출원가/판관비/금융비용·수익/법인세 차감 → 당기순이익
        도착까지 단계별 amount + pct + cumPct (누적) 시계열. UI 워터폴 차트
        직접 입력. 영업외 (금융손익) 가 마진을 얼마나 갉아먹는지 가시화.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 [{period, steps: list[dict]}]
              steps 각 키: label + amount + pct + cumPct.

    Raises:
        없음.

    Example:
        >>> r = calcMarginWaterfall(Company("005930"))
        >>> [s["label"] for s in r["history"][0]["steps"][:3]]
        ['매출', '매출원가', '매출총이익']

    Guide:
        한국 회사 흔한 패턴: 영업이익률 8% → 금융비용/외환손익 차감 후
        순이익률 5%. 영업 vs 영업외 영향 분리하여 본업 수익성 평가.
        매출 0 period 는 자동 skip.

    When:
        본업 vs 영업외 영향 분리 점검, 워터폴 차트 입력 직전.

    How:
        IS 10 계정 → 매출 대비 pct + 누적 cumPct 단계별 산출.

    SeeAlso:
        - ``calcMarginTrend``: 마진 5 단계 시계열
        - ``calcReturnTrend``: ROE 듀퐁 분해
        - ``calcCostBreakdown``: 비용 비중 (워터폴 입력)

    Requires:
        IS (매출 + COGS + 판관비 + 금융비용/수익 + 법인세 + 순이익) ≥ 1 년.

    AIContext:
        워터폴 step label + cumPct 로 어디서 마진이 빠지는지 인용. 금융비용
        > 5% 이면 영업외 부담 큼 신호. KR 재벌은 지분법손익이 영업외로
        잡혀 순이익률 크게 변동.

    LLM Specifications:
        AntiPatterns:
            - 순이익률 단독 인용 — 워터폴 단계 함께 (영업 vs 영업외 분리).
            - 매출 0 period 인용 — 본 함수가 자동 skip.
        OutputSchema:
            ``{history: list[{period, steps: list[{label,amount,pct,cumPct}]}]}``.
        Prerequisites:
            IS 10 계정 (매출/원가/총이익/판관비/영업이익/금융비용수익/PBT/세금/순이익).
        Freshness:
            분기 + 시계열.
        Dataflow:
            IS → 10 계정 → 단계별 amount + pct (매출 대비) + cumPct (누적).
        TargetMarkets: KR (DART), US (EDGAR — IS 표준).
    """
    isResult = company.select(
        "IS",
        [
            "매출액",
            "매출원가",
            "매출총이익",
            "판매비와관리비",
            "영업이익",
            "금융비용",
            "금융수익",
            "법인세차감전순이익",
            "법인세비용",
            "당기순이익",
        ],
    )
    parsed = toDictBySnakeId(isResult)
    if parsed is None:
        return None

    data, periods = parsed
    rev = data.get("매출액", {})
    cogs = data.get("매출원가", {})
    gp = data.get("매출총이익", {})
    sgaRow = data.get("판매비와관리비", {})
    opRow = data.get("영업이익", {})
    finCost = data.get("금융비용", {})
    finInc = data.get("금융수익", {})
    pbt = data.get("법인세차감전순이익", {})
    tax = data.get("법인세비용", {})
    ni = data.get("당기순이익", {})

    yCols = annualColsFromPeriods(periods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    def _pct(val, r):
        """매출 대비 비율 계산 (%)."""
        if val is None or r is None or r == 0:
            return None
        return round(val / r * 100, 2)

    rows = {
        "cogs": cogs,
        "gp": gp,
        "sga": sgaRow,
        "op": opRow,
        "finCost": finCost,
        "finInc": finInc,
        "pbt": pbt,
        "tax": tax,
        "ni": ni,
    }

    history = []
    for col in yCols:
        r = rev.get(col)
        if r is None or r == 0:
            continue
        history.append({"period": col, "steps": _waterfallSteps(col, r, rows, _pct)})

    return {"history": history} if history else None


@memoizedCalc
def calcPenmanDecomposition(company, *, basePeriod: str | None = None) -> dict | None:
    """Penman ROE 분해 — RNOA (영업력) vs FLEV × SPREAD (레버리지 효과) 분리.

    Capabilities:
        Penman & Nissim (2001, RAS) 의 ROE 분해 — ROCE = RNOA + FLEV × SPREAD.
        영업 수익성 (RNOA) 과 레버리지 효과를 분리해 "ROE 가 영업 efficiency
        에서 왔는가 아니면 financial leverage 에서 왔는가" 판정. NOA (Net
        Operating Assets) + NFO (Net Financial Obligations) 회계 분리 기반.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 분해 (period, rnoa, flev, nbc,
              spread, leverageEffect, roce)

    Raises:
        없음.

    Example:
        >>> r = calcPenmanDecomposition(Company("005930"))
        >>> r["history"][0]
        {'period': '2024', 'rnoa': 15, 'flev': 0.3, 'nbc': 3, 'spread': 12,
         'leverageEffect': 3.6, 'roce': 18.6}
        # ROE 18.6% = 영업 15% + 레버리지 효과 3.6%p (안전한 레버리지)

    Guide:
        진성 고수익 = RNOA > 15% + FLEV 낮음 (< 0.5). 레버리지 의존 = FLEV
        > 1 + RNOA 보통 (10%). SPREAD 음수면 부채가 ROE 를 깎는 중 (적색
        신호 — 부채 cost 가 영업 수익 초과).

    When:
        ROE 원천 (영업력 vs 레버리지) 분리 평가 시점.

    How:
        IS/BS → NOPAT/NOA/NFO 분리 → RNOA + FLEV × SPREAD 합산.

    SeeAlso:
        - ``calcRoicTree``: McKinsey ROIC 분해
        - ``calcReturnTrend``: ROE/ROA 시계열
        - ``calcAssetStructure``: NOA 산출 (본 함수 입력 데이터)
        - Penman, S. & Nissim, D. (2001) "Ratio Analysis and Equity Valuation"

    Requires:
        IS + BS 시계열 + 영업/비영업 분리 (calcAssetStructure 와 같은 로직).

    AIContext:
        ROE 만 인용 금지 — RNOA + leverageEffect 분해 결과 함께 노출. 진성
        고수익 회사 (Penman 의 quality of earnings) 식별에 핵심.

    LLM Specifications:
        AntiPatterns:
            - SPREAD 양수만 보고 "안전" 단정 — FLEV 비율 함께 확인 (FLEV 1+
              이면 작은 SPREAD 변화에도 ROE 큰 영향).
            - 단년도 RNOA 만 보고 "영업력 우수" — 3 년 추세 권장.
        OutputSchema:
            ``{history: list[dict 7키]}``.
        Prerequisites:
            IS/operatingIncome + BS/equity + NOA/NFO 분리 가능.
        Freshness:
            최신 분기 + 시계열.
        Dataflow:
            IS/BS → 영업/비영업 분리 → NOPAT/NOA → RNOA + FLEV + NBC →
            SPREAD = RNOA - NBC → leverageEffect = FLEV × SPREAD → ROCE.
        TargetMarkets: KR (DART), US (EDGAR). 표준 회계 동일.
    """
    isResult = company.select("IS", ["영업이익", "법인세비용", "법인세차감전순이익", "금융이익", "금융비용"])
    bsResult = company.select(
        "BS",
        [
            "자산총계",
            "자본총계",
            "매출채권및기타채권",
            "재고자산",
            "유형자산",
            "무형자산",
            "매입채무",
            "선수금",
            "계약부채",
            "단기차입금",
            "장기차입금",
            "차입금단기",
            "long_term_borrowings",
            "short_term_borrowings",
            "차입부채",
            "장기차입부채",
            "유동성장기차입금",
            "사채",
            "현금및현금성자산",
        ],
    )

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    opRow = isData.get("operating_profit", {})
    taxRow = isData.get("income_tax_expense") or isData.get("income_taxes", {})
    ptRow = isData.get("profit_before_tax", {})
    finIncRow = isData.get("finance_income", {})
    finCostRow = isData.get("finance_costs", {})

    eqRow = bsData.get("total_stockholders_equity", {})
    recRow = bsData.get("trade_and_other_receivables", {})
    invRow = bsData.get("inventories", {})
    ppeRow = bsData.get("tangible_assets", {})
    intRow = bsData.get("intangible_assets", {})
    apRow = bsData.get("trade_and_other_payables", {})
    advRow = bsData.get("advance_from_customers", {})
    contRow = bsData.get("contract_liabilities", {})
    bsData.get("shortterm_borrowings", {})
    bsData.get("longterm_borrowings", {})
    bsData.get("borrowings", {})  # 통합 차입금 fallback
    bsData.get("debentures", {})
    cashRow = bsData.get("cash_and_cash_equivalents", {})

    yCols = annualColsFromPeriods(isPeriods, maxYears=_MAX_YEARS, basePeriod=basePeriod)
    if len(yCols) < 2:
        return None

    history = []
    for col in yCols:
        # NOPAT = 영업이익 × (1 - 유효세율)
        opIncome = _getF(opRow, col)
        taxExpense = abs(_getF(taxRow, col))
        ptIncome = abs(_getF(ptRow, col))
        effectiveTaxRate = taxExpense / ptIncome if ptIncome > 0 else 0.25
        effectiveTaxRate = min(effectiveTaxRate, 0.5)
        nopat = opIncome * (1 - effectiveTaxRate) if opIncome != 0 else None

        # NOA = 영업자산 - 영업부채
        opAssets = _get(recRow, col) + _get(invRow, col) + _get(ppeRow, col) + _get(intRow, col)
        opLiab = _get(apRow, col) + _get(advRow, col) + _get(contRow, col)
        noa = opAssets - opLiab if opAssets > 0 else None

        # NFO = 금융부채 - 금융자산(현금)
        # 차입금: 회사 키 패턴 무관 헬퍼
        finDebt = sumBorrowings(bsData, col)
        cash = _get(cashRow, col)
        nfo = finDebt - cash

        # 순금융비용
        finInc = _getF(finIncRow, col)
        finCost = _getF(finCostRow, col)
        netFinCost = finCost - finInc  # 양수 = 순비용

        equity = _get(eqRow, col)

        # RNOA
        rnoa = round(nopat / noa * 100, 2) if nopat is not None and noa and noa > 0 else None
        # FLEV
        flev = round(nfo / equity, 2) if equity > 0 else None
        # NBC
        nbc = round(netFinCost * (1 - effectiveTaxRate) / abs(nfo) * 100, 2) if nfo != 0 else None
        # SPREAD
        spread = round(rnoa - nbc, 2) if rnoa is not None and nbc is not None else None
        # Leverage Effect
        levEffect = round(flev * spread, 2) if flev is not None and spread is not None else None
        # ROCE (검증: ≈ RNOA + leverageEffect)
        roce = round(rnoa + levEffect, 2) if rnoa is not None and levEffect is not None else None

        history.append(
            {
                "period": col,
                "rnoa": rnoa,
                "flev": flev,
                "nbc": nbc,
                "spread": spread,
                "leverageEffect": levEffect,
                "roce": roce,
            }
        )

    if not history:
        return None

    return {"history": history}


@memoizedCalc
def calcRoicTree(company, *, basePeriod: str | None = None) -> dict | None:
    """McKinsey ROIC Tree → ROIC 분해 (마진 × 회전율 → COGS/SG&A/Tax + WC/Fixed).

    Capabilities:
        McKinsey "Valuation" (Koller 2020) 의 ROIC 분해 — ROIC = Margin × Turnover.
        Margin 은 (COGS/Rev + SG&A/Rev + TaxRate) 로 분해, Turnover 는 WC vs
        Fixed Capital 로 분해. ROIC 변화의 원인 (마진 vs 회전율) 자동 식별.
        Penman/Damodaran 의 ROE 분해와 보완.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 ROIC tree (period, roic,
              operatingMargin, capitalTurnover, grossMargin, sgaRatio,
              effectiveTaxRate, wcTurnover, fixedTurnover, marginDriver,
              turnoverDriver)

    Raises:
        없음.

    Example:
        >>> r = calcRoicTree(Company("005930"))
        >>> r["history"][0]["roic"], r["history"][0]["marginDriver"]
        (15, 'cogs')  # ROIC 15%, 변화 주도 = COGS

    Guide:
        ROIC 임계: > 15% = excellent (cost of capital 10% 가정), 10~15% =
        good, < 10% = value destroyer. marginDriver 가 "cogs" 인데 매출 증가
        시기 = 규모 경제, "sga" 우세 = 영업 효율 개선 또는 악화.

    When:
        ROIC 변화 원인 (마진 vs 회전율) 진단, WACC 대비 가치창출 평가.

    How:
        IS → 마진 분해 + BS → IC (WC+Fixed) → ROIC = margin × turnover.

    SeeAlso:
        - ``calcMarginTrend``: 마진 단순 시계열
        - ``calcReturnTrend``: ROE/ROA/ROIC 시계열
        - ``calcPenmanDecomposition``: ROE 분해 (RNOA + FLEV × Spread)
        - Koller, T. (2020) "Valuation: Measuring and Managing"

    Requires:
        IS 시계열 (매출/매출원가/판관비/세금) + BS (운전자본 + 고정자본) ≥ 2 년.

    AIContext:
        ROIC > WACC = value creator, < WACC = value destroyer. marginDriver +
        turnoverDriver 라벨을 사용자에게 노출 — "왜 ROIC 가 변했는지" 직접
        설명.

    LLM Specifications:
        AntiPatterns:
            - ROIC 절대값만 인용 — WACC 와 비교 필수 (calcDFV 의 qualityWACC
              사용 권장).
            - 단년도 분해 — 3 년 추세로 marginDriver 의 안정성 확인 필수.
        OutputSchema:
            ``{history: list[dict 11키]}``.
        Prerequisites:
            IS + BS 시계열 + standardAccounts (매출원가/판관비/세금).
        Freshness:
            최신 분기 + 시계열 (5 년 권장).
        Dataflow:
            IS → margin 분해 (COGS/SG&A/Tax) + BS → IC = WC + Fixed →
            Turnover → ROIC = margin × turnover → driver 식별.
        TargetMarkets: KR (DART), US (EDGAR). 표준 계정 매핑.
    """
    isResult = company.select(
        "IS", ["매출액", "매출원가", "판매비와관리비", "영업이익", "법인세비용", "법인세차감전순이익"]
    )
    bsResult = company.select(
        "BS",
        [
            "매출채권및기타채권",
            "재고자산",
            "매입채무",
            "유형자산",
            "무형자산",
            "자본총계",
            "단기차입금",
            "장기차입금",
            "차입금단기",
            "long_term_borrowings",
            "short_term_borrowings",
            "차입부채",
            "장기차입부채",
            "유동성장기차입금",
            "사채",
            "현금및현금성자산",
        ],
    )

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    revRow = isData.get("sales", {})
    cogsRow = isData.get("cost_of_sales", {})
    sgaRow = isData.get("selling_and_administrative_expenses", {})
    opRow = isData.get("operating_profit", {})
    taxRow = isData.get("income_tax_expense") or isData.get("income_taxes", {})
    ptRow = isData.get("profit_before_tax", {})

    arRow = bsData.get("trade_and_other_receivables", {})
    invRow = bsData.get("inventories", {})
    apRow = bsData.get("trade_and_other_payables", {})
    ppeRow = bsData.get("tangible_assets", {})
    intRow = bsData.get("intangible_assets", {})
    bsData.get("total_stockholders_equity", {})
    bsData.get("shortterm_borrowings", {})
    bsData.get("longterm_borrowings", {})
    bsData.get("borrowings", {})  # 통합 차입금 fallback
    bsData.get("debentures", {})
    bsData.get("cash_and_cash_equivalents", {})

    yCols = annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        rev = _getF(revRow, col)
        if rev <= 0:
            continue
        cogs = _getF(cogsRow, col)
        sga = _getF(sgaRow, col)
        opIncome = _getF(opRow, col)
        taxExp = abs(_getF(taxRow, col))
        ptIncome = abs(_getF(ptRow, col))

        # Margin 분해
        grossMargin = round((rev - cogs) / rev * 100, 2) if cogs else None
        sgaRatio = round(sga / rev * 100, 2) if sga else None
        opMargin = round(opIncome / rev * 100, 2)
        effectiveTax = round(taxExp / ptIncome * 100, 2) if ptIncome > 0 else 25.0
        effectiveTax = min(effectiveTax, 50.0)

        # NOPAT
        nopat = opIncome * (1 - effectiveTax / 100)

        # Invested Capital
        wc = _get(arRow, col) + _get(invRow, col) - _get(apRow, col)
        fc = _get(ppeRow, col) + _get(intRow, col)
        ic = wc + fc if (wc + fc) > 0 else None

        # ROIC
        roic = round(nopat / ic * 100, 2) if ic and ic > 0 else None

        # Capital Turnover
        capTurnover = round(rev / ic, 2) if ic and ic > 0 else None

        # WC/Fixed Turnover
        wcTurnover = round(rev / wc, 2) if wc > 0 else None
        fixedTurnover = round(rev / fc, 2) if fc > 0 else None

        # 마진 드라이버 판단
        if grossMargin is not None and sgaRatio is not None:
            if grossMargin > 40:
                marginDriver = "높은 가격결정력 (매출총이익률 > 40%)"
            elif sgaRatio and sgaRatio < 15:
                marginDriver = "낮은 판관비 (SGA < 15%)"
            elif opMargin > 15:
                marginDriver = "고마진 사업모델"
            elif opMargin < 5:
                marginDriver = "박리다매 또는 원가 경쟁"
            else:
                marginDriver = "보통 수준"
        else:
            marginDriver = None

        # 자본회전 드라이버 판단
        if capTurnover is not None:
            if capTurnover > 2:
                turnoverDriver = "자산 경량 모델 (자본회전 > 2회)"
            elif capTurnover < 0.5:
                turnoverDriver = "자본 집약 (자본회전 < 0.5회)"
            else:
                turnoverDriver = "보통 수준"
        else:
            turnoverDriver = None

        history.append(
            {
                "period": col,
                "roic": roic,
                "operatingMargin": opMargin,
                "capitalTurnover": capTurnover,
                "grossMargin": grossMargin,
                "sgaRatio": sgaRatio,
                "effectiveTaxRate": round(effectiveTax, 1),
                "wcTurnover": wcTurnover,
                "fixedTurnover": fixedTurnover,
                "marginDriver": marginDriver,
                "turnoverDriver": turnoverDriver,
            }
        )

    if not history:
        return None
    return {"history": history}
