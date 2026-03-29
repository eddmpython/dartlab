"""2-1 수익성 분석 -- 이익의 흐름을 추적한다.

select()로 IS/BS 원본 계정을 가져와서
금액 + 비율 + YoY 변동을 시계열로 보여준다.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    MAX_RATIO_YEARS,
    toDict,
)

_MAX_YEARS = MAX_RATIO_YEARS


def _annualCols(periods: list[str], maxYears: int = _MAX_YEARS) -> list[str]:
    cols = sorted([c for c in periods if "Q" not in c], reverse=True)
    if cols:
        return cols[:maxYears]
    return sorted([c for c in periods if c.endswith("Q4")], reverse=True)[:maxYears]


def _yoy(cur, prev) -> float | None:
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _pctOf(part, total) -> float | None:
    if part is None or total is None or total == 0:
        return None
    return round(part / total * 100, 2)


# ── 이익 구조 시계열 ──


def calcMarginTrend(company) -> dict | None:
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

    yCols = _annualCols(periods, _MAX_YEARS + 1)
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


def calcReturnTrend(company) -> dict | None:
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

    yCols = _annualCols(isPeriods, _MAX_YEARS)
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


def calcMarginWaterfall(company) -> dict | None:
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

    yCols = _annualCols(periods, _MAX_YEARS)
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


def calcProfitabilityFlags(company) -> list[str]:
    """수익성 경고/기회 플래그."""
    flags: list[str] = []

    trend = calcMarginTrend(company)
    if trend and len(trend["history"]) >= 3:
        hist = trend["history"]
        # 영업이익률 3기 연속 하락
        oms = [h.get("operatingMargin") for h in hist[:3]]
        if all(v is not None for v in oms) and oms[0] < oms[1] < oms[2]:
            flags.append(f"영업이익률 3기 연속 하락 ({oms[0]:.1f}%)")
        if oms[0] is not None and oms[0] < 0:
            flags.append(f"영업적자 ({oms[0]:.1f}%)")

    ret = calcReturnTrend(company)
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
