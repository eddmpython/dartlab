"""2-1 수익성 분석 -- 이익의 흐름을 추적한다.

select()로 IS/BS 원본 계정을 가져와서
금액 + 비율 + YoY 변동을 시계열로 보여준다.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    MAX_RATIO_YEARS,
    annualColsFromPeriods,
    toDict,
)
from dartlab.analysis.financial._memoize import memoized_calc

_MAX_YEARS = MAX_RATIO_YEARS


def _yoy(cur, prev) -> float | None:
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _pctOf(part, total) -> float | None:
    if part is None or total is None or total == 0:
        return None
    return round(part / total * 100, 2)


# ── 이익 구조 시계열 ──


@memoized_calc
def calcMarginTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """이익 구조 시계열 -- 매출에서 순이익까지 금액과 마진.

    IS에서 매출/매출원가/매출총이익/판관비/영업이익/당기순이익을 가져와서
    금액 + 매출 대비 비율 + YoY를 기간별로 보여준다.
    """
    isResult = company.select(
        "IS",
        ["매출액", "매출원가", "매출총이익", "판매비와관리비", "영업이익", "당기순이익"],
    )
    parsed = toDict(isResult)
    if parsed is None:
        return None

    data, periods = parsed
    rev = data.get("매출액", {})
    cogs = data.get("매출원가", {})
    gp = data.get("매출총이익", {})
    sga = data.get("판매비와관리비", {})
    op = data.get("영업이익", {})
    ni = data.get("당기순이익", {})

    yCols = annualColsFromPeriods(periods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):  # 최신부터, 마지막은 YoY 계산용
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        r = rev.get(col)
        if r is None or r == 0:
            continue

        history.append(
            {
                "period": col,
                "revenue": r,
                "revenueYoy": _yoy(r, rev.get(prevCol)) if prevCol else None,
                "cogs": cogs.get(col),
                "grossProfit": gp.get(col),
                "grossMargin": _pctOf(gp.get(col), r),
                "sga": sga.get(col),
                "operatingIncome": op.get(col),
                "operatingMargin": _pctOf(op.get(col), r),
                "operatingIncomeYoy": _yoy(op.get(col), op.get(prevCol)) if prevCol else None,
                "netIncome": ni.get(col),
                "netMargin": _pctOf(ni.get(col), r),
                "netIncomeYoy": _yoy(ni.get(col), ni.get(prevCol)) if prevCol else None,
            }
        )

    return {"history": history} if history else None


# ── ROE 분해 (듀퐁 5요소) ──


@memoized_calc
def calcReturnTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """ROE 구조 분해 -- 수익을 어떻게 만드는가.

    IS + BS에서 원본 계정을 가져와서 듀퐁 5요소를 직접 계산.
    ROE = (NI/EBT) x (EBT/EBIT) x (EBIT/Rev) x (Rev/TA) x (TA/Equity)
        = 세금부담 x 이자부담 x 영업마진 x 자산회전 x 레버리지
    """
    isResult = company.select(
        "IS",
        ["매출액", "영업이익", "법인세차감전순이익", "당기순이익"],
    )
    bsResult = company.select("BS", ["자산총계", "자본총계"])

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    rev = isData.get("매출액", {})
    opIncome = isData.get("영업이익", {})
    pbt = isData.get("법인세차감전순이익", {})
    niRow = isData.get("당기순이익", {})
    ta = bsData.get("자산총계", {})
    eq = bsData.get("자본총계", {})

    yCols = annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        r = rev.get(col)
        o = opIncome.get(col)
        p = pbt.get(col)
        n = niRow.get(col)
        a = ta.get(col)
        e = eq.get(col)

        roe = _pctOf(n, e)
        roa = _pctOf(n, a)

        # 듀퐁 5요소 (원본에서 직접)
        taxBurden = round(n / p, 4) if n is not None and p is not None and p != 0 else None
        interestBurden = round(p / o, 4) if p is not None and o is not None and o != 0 else None
        operatingMargin = _pctOf(o, r)
        assetTurnover = round(r / a, 4) if r is not None and a is not None and a != 0 else None
        leverage = round(a / e, 4) if a is not None and e is not None and e != 0 else None

        history.append(
            {
                "period": col,
                "netIncome": n,
                "equity": e,
                "totalAssets": a,
                "roe": roe,
                "roa": roa,
                "taxBurden": taxBurden,
                "interestBurden": interestBurden,
                "operatingMargin": operatingMargin,
                "assetTurnover": assetTurnover,
                "leverage": leverage,
            }
        )

    return {"history": history} if history else None


# calcDupont은 calcReturnTrend에 통합
calcDupont = calcReturnTrend


# ── 마진 워터폴 ──


@memoized_calc
def calcMarginWaterfall(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 -> 순이익 마진 워터폴 분해.

    각 단계에서 얼마나 줄어드는지를 금액 + 비율(%)로 보여준다.
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
    parsed = toDict(isResult)
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
        if val is None or r is None or r == 0:
            return None
        return round(val / r * 100, 2)

    history = []
    for col in yCols:
        r = rev.get(col)
        if r is None or r == 0:
            continue

        steps = [{"label": "매출", "amount": r, "pct": 100.0, "cumPct": 100.0}]

        cogsV = cogs.get(col)
        gpV = gp.get(col)
        if cogsV is not None:
            steps.append(
                {
                    "label": "매출원가",
                    "amount": cogsV,
                    "pct": -abs(_pct(cogsV, r) or 0),
                    "cumPct": _pct(gpV, r) or round(100 - abs(_pct(cogsV, r) or 0), 2),
                }
            )
        if gpV is not None:
            steps.append({"label": "매출총이익", "amount": gpV, "pct": _pct(gpV, r), "cumPct": _pct(gpV, r)})

        sgaV = sgaRow.get(col)
        opV = opRow.get(col)
        if sgaV is not None:
            steps.append(
                {
                    "label": "판관비",
                    "amount": sgaV,
                    "pct": -abs(_pct(sgaV, r) or 0),
                    "cumPct": _pct(opV, r) or round((_pct(gpV, r) or 0) - abs(_pct(sgaV, r) or 0), 2),
                }
            )
        if opV is not None:
            steps.append({"label": "영업이익", "amount": opV, "pct": _pct(opV, r), "cumPct": _pct(opV, r)})

        fcV = finCost.get(col)
        fiV = finInc.get(col)
        opPct = _pct(opV, r) or 0
        if fcV is not None:
            steps.append(
                {
                    "label": "금융비용",
                    "amount": fcV,
                    "pct": -abs(_pct(fcV, r) or 0),
                    "cumPct": round(opPct - abs(_pct(fcV, r) or 0), 2),
                }
            )
        if fiV is not None:
            steps.append(
                {
                    "label": "금융수익",
                    "amount": fiV,
                    "pct": abs(_pct(fiV, r) or 0),
                    "cumPct": round(opPct - abs(_pct(fcV, r) or 0) + abs(_pct(fiV, r) or 0), 2),
                }
            )

        pbtV = pbt.get(col)
        if pbtV is not None:
            steps.append({"label": "세전이익", "amount": pbtV, "pct": _pct(pbtV, r), "cumPct": _pct(pbtV, r)})

        taxV = tax.get(col)
        if taxV is not None:
            steps.append(
                {
                    "label": "법인세",
                    "amount": taxV,
                    "pct": -abs(_pct(taxV, r) or 0),
                    "cumPct": round((_pct(pbtV, r) or 0) - abs(_pct(taxV, r) or 0), 2),
                }
            )

        niV = ni.get(col)
        if niV is not None:
            steps.append({"label": "순이익", "amount": niV, "pct": _pct(niV, r), "cumPct": _pct(niV, r)})

        history.append({"period": col, "steps": steps})

    return {"history": history} if history else None


# ── 플래그 ──


@memoized_calc
def calcProfitabilityFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """수익성 경고/기회 플래그."""
    flags: list[str] = []

    trend = calcMarginTrend(company, basePeriod=basePeriod)
    if trend and len(trend["history"]) >= 3:
        hist = trend["history"]
        # 영업이익률 3기 연속 하락
        oms = [h.get("operatingMargin") for h in hist[:3]]
        if all(v is not None for v in oms) and oms[0] < oms[1] < oms[2]:
            flags.append(f"영업이익률 3기 연속 하락 ({oms[0]:.1f}%)")
        if oms[0] is not None and oms[0] < 0:
            flags.append(f"영업적자 ({oms[0]:.1f}%)")

    ret = calcReturnTrend(company, basePeriod=basePeriod)
    if ret and ret["history"]:
        h = ret["history"][0]
        roe = h.get("roe")
        roa = h.get("roa")
        lev = h.get("leverage")
        if roe is not None and roa is not None and lev is not None:
            if lev > 3:
                flags.append(f"ROE의 레버리지 의존도 높음 (자산/자본 = {lev:.1f}배)")
            if roe > 15 and roa > 5 and lev < 2:
                flags.append(f"진성 고수익 (ROE {roe:.1f}%, 낮은 레버리지)")

    return flags


# ── Penman RNOA + FLEV/SPREAD 분해 ──


def _get(row: dict, col: str) -> float:
    v = row.get(col)
    return v if v is not None else 0


@memoized_calc
def calcPenmanDecomposition(company, *, basePeriod: str | None = None) -> dict | None:
    """Penman 분해 -- ROE가 영업력인지 레버리지인지 분리.

    ROCE = RNOA + FLEV × SPREAD
    RNOA = NOPAT / NOA  (순영업자산수익률)
    FLEV = NFO / Equity  (금융레버리지)
    NBC  = 순금융비용 / NFO  (순차입비용률)
    SPREAD = RNOA - NBC  (초과수익률)
    leverageEffect = FLEV × SPREAD  (레버리지 효과)

    반환::

        {
            "history": [
                {"period": str, "rnoa": float, "flev": float, "nbc": float,
                 "spread": float, "leverageEffect": float, "roce": float},
                ...
            ],
        }

    Guide::

        RNOA와 ROE를 비교하면 레버리지 효과를 알 수 있다.
        RNOA > NBC이면 차입이 주주에게 유리 (양의 SPREAD).
        RNOA < NBC이면 차입이 가치를 파괴.

    SeeAlso::

        - calcReturnTrend: 기존 5요소 DuPont
        - calcRoicTimeline: ROIC 시계열

    학술근거: Nissim & Penman (2001), Penman FSA&SV 5e.
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
            "사채",
            "현금및현금성자산",
        ],
    )

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    opRow = isData.get("영업이익", {})
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", {})
    finIncRow = isData.get("금융이익", {})
    finCostRow = isData.get("금융비용", {})

    eqRow = bsData.get("자본총계", {})
    recRow = bsData.get("매출채권및기타채권", {})
    invRow = bsData.get("재고자산", {})
    ppeRow = bsData.get("유형자산", {})
    intRow = bsData.get("무형자산", {})
    apRow = bsData.get("매입채무", {})
    advRow = bsData.get("선수금", {})
    contRow = bsData.get("계약부채", {})
    stRow = bsData.get("단기차입금", {})
    ltRow = bsData.get("장기차입금", {})
    bondRow = bsData.get("사채", {})
    cashRow = bsData.get("현금및현금성자산", {})

    yCols = annualColsFromPeriods(isPeriods, maxYears=_MAX_YEARS, basePeriod=basePeriod)
    if len(yCols) < 2:
        return None

    history = []
    for col in yCols:
        # NOPAT = 영업이익 × (1 - 유효세율)
        opIncome = _get(opRow, col)
        taxExpense = abs(_get(taxRow, col))
        ptIncome = abs(_get(ptRow, col))
        effectiveTaxRate = taxExpense / ptIncome if ptIncome > 0 else 0.25
        effectiveTaxRate = min(effectiveTaxRate, 0.5)
        nopat = opIncome * (1 - effectiveTaxRate) if opIncome != 0 else None

        # NOA = 영업자산 - 영업부채
        opAssets = _get(recRow, col) + _get(invRow, col) + _get(ppeRow, col) + _get(intRow, col)
        opLiab = _get(apRow, col) + _get(advRow, col) + _get(contRow, col)
        noa = opAssets - opLiab if opAssets > 0 else None

        # NFO = 금융부채 - 금융자산(현금)
        finDebt = _get(stRow, col) + _get(ltRow, col) + _get(bondRow, col)
        cash = _get(cashRow, col)
        nfo = finDebt - cash

        # 순금융비용
        finInc = _get(finIncRow, col)
        finCost = _get(finCostRow, col)
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


# ── McKinsey ROIC Tree ──


@memoized_calc
def calcRoicTree(company, *, basePeriod: str | None = None) -> dict | None:
    """McKinsey ROIC Tree — ROIC가 높은/낮은 이유를 원인까지 추적.

    ROIC = Operating Margin × Capital Turnover
    Operating Margin = 1 - (COGS/Rev) - (SGA/Rev) - Tax Rate
    Capital Turnover = Revenue / Invested Capital
      IC = Working Capital (AR+Inv-AP) + Fixed Capital (PPE+Intangible)

    반환::

        {
            "history": [
                {
                    "period": str,
                    "roic": float,
                    "operatingMargin": float,
                    "capitalTurnover": float,
                    "grossMargin": float,
                    "sgaRatio": float,
                    "effectiveTaxRate": float,
                    "wcTurnover": float,
                    "fixedTurnover": float,
                    "marginDriver": str,
                    "turnoverDriver": str,
                },
                ...
            ],
        }

    학술근거: Koller, Goedhart, Wessels - Valuation (McKinsey).
    """
    isResult = company.select(
        "IS",
        ["매출액", "매출원가", "판매비와관리비", "영업이익", "법인세비용", "법인세차감전순이익"],
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
            "사채",
            "현금및현금성자산",
        ],
    )

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})
    sgaRow = isData.get("판매비와관리비", {})
    opRow = isData.get("영업이익", {})
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", {})

    arRow = bsData.get("매출채권및기타채권", {})
    invRow = bsData.get("재고자산", {})
    apRow = bsData.get("매입채무", {})
    ppeRow = bsData.get("유형자산", {})
    intRow = bsData.get("무형자산", {})
    eqRow = bsData.get("자본총계", {})
    stRow = bsData.get("단기차입금", {})
    ltRow = bsData.get("장기차입금", {})
    bondRow = bsData.get("사채", {})
    cashRow = bsData.get("현금및현금성자산", {})

    yCols = annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        rev = _get(revRow, col)
        if rev <= 0:
            continue
        cogs = _get(cogsRow, col)
        sga = _get(sgaRow, col)
        opIncome = _get(opRow, col)
        taxExp = abs(_get(taxRow, col))
        ptIncome = abs(_get(ptRow, col))

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
