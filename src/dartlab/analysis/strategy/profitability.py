"""2-1 수익성 분석 -- 마진, ROE/ROA, 듀퐁 분해, 마진 워터폴."""

from __future__ import annotations

from dartlab.analysis.strategy._helpers import (
    MAX_RATIO_YEARS,
    buildTimeline,
    getRatioSeries,
    toDict,
)


def calcMarginTrend(company) -> dict | None:
    """매출총이익률, 영업이익률, 순이익률 시계열."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    gross = buildTimeline(data, "grossMargin", years)
    operating = buildTimeline(data, "operatingMargin", years)
    net = buildTimeline(data, "netMargin", years)

    if not any([gross, operating, net]):
        return None

    return {
        "grossMargin": gross,
        "operatingMargin": operating,
        "netMargin": net,
        "years": years[-MAX_RATIO_YEARS:],
    }


def calcReturnTrend(company) -> dict | None:
    """ROE, ROA 시계열 + 레버리지(ROE/ROA)."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    roe = buildTimeline(data, "roe", years)
    roa = buildTimeline(data, "roa", years)

    if not roe and not roa:
        return None

    leverage = []
    for r, a in zip(roe, roa):
        rv = r.get("value")
        av = a.get("value")
        if rv is not None and av is not None and av != 0:
            leverage.append({"period": r["period"], "value": round(rv / av, 2)})
        else:
            leverage.append({"period": r["period"], "value": None})

    return {"roe": roe, "roa": roa, "leverage": leverage}


def calcDupont(company) -> dict | None:
    """듀퐁 5요소 분해 시계열.

    ROE = 세금부담률 x 이자부담률 x 영업마진 x 자산회전율 x 재무레버리지
        = (NI/EBT) x (EBT/EBIT) x (EBIT/Rev) x (Rev/TA) x (TA/Equity)

    3요소(margin, turnover, leverage)에 taxBurden, interestBurden 추가.
    """
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    margin = buildTimeline(data, "dupontMargin", years)
    turnover = buildTimeline(data, "dupontTurnover", years)
    leverage = buildTimeline(data, "dupontLeverage", years)

    if not margin and not turnover and not leverage:
        return None

    # 5요소 확장: 세금부담률, 이자부담률
    opMargin = buildTimeline(data, "operatingMargin", years)
    netMargin = buildTimeline(data, "netMargin", years)
    preTaxMargin = buildTimeline(data, "preTaxMargin", years)
    effectiveTaxRate = buildTimeline(data, "effectiveTaxRate", years)

    taxBurden = []
    interestBurden = []
    for i in range(len(margin)):
        nm = netMargin[i]["value"] if i < len(netMargin) else None
        ptm = preTaxMargin[i]["value"] if i < len(preTaxMargin) else None
        om = opMargin[i]["value"] if i < len(opMargin) else None
        etr = effectiveTaxRate[i]["value"] if i < len(effectiveTaxRate) else None
        period = margin[i]["period"]

        # 세금부담률 = NI/EBT = 1 - 유효세율
        tb = round(1 - etr / 100, 4) if etr is not None else None
        taxBurden.append({"period": period, "value": tb})

        # 이자부담률 = EBT/EBIT = preTaxMargin / operatingMargin
        ib = None
        if ptm is not None and om is not None and om != 0:
            ib = round(ptm / om, 4)
        interestBurden.append({"period": period, "value": ib})

    return {
        "taxBurden": taxBurden,
        "interestBurden": interestBurden,
        "operatingMargin": opMargin,
        "turnover": turnover,
        "leverage": leverage,
        "margin": margin,
    }


def calcMarginWaterfall(company) -> dict | None:
    """매출 -> 순이익 마진 워터폴 분해.

    각 단계에서 얼마나 줄어드는지를 비율(%)로 보여준다:
    매출(100%) -> -매출원가 -> 매출총이익 -> -판관비 -> 영업이익
    -> -이자비용 -> +이자수익 -> 세전이익 -> -법인세 -> 순이익

    반환::

        {
            "history": [
                {
                    "period": str,
                    "steps": [
                        {"label": str, "pct": float, "cumPct": float},
                        ...
                    ],
                },
                ...
            ],
        }
    """
    isResult = company.select(
        "IS",
        [
            "매출액",
            "매출원가",
            "매출총이익",
            "판매비와관리비",
            "영업이익",
            "이자비용",
            "이자수익",
            "법인세차감전순이익",
            "법인세비용",
            "당기순이익",
        ],
    )
    parsed = toDict(isResult, maxPeriods=MAX_RATIO_YEARS)
    if parsed is None:
        return None

    data, periods = parsed
    rev = data.get("매출액", {})
    cogs = data.get("매출원가", {})
    gp = data.get("매출총이익", {})
    sgaRow = data.get("판매비와관리비", {})
    opRow = data.get("영업이익", {})
    intExp = data.get("이자비용", {})
    intInc = data.get("이자수익", {})
    pbt = data.get("법인세차감전순이익", {})
    tax = data.get("법인세비용", {})
    ni = data.get("당기순이익", {})

    annualPeriods = sorted([p for p in periods if "Q" not in p])
    if not annualPeriods:
        annualPeriods = sorted([p for p in periods if p.endswith("Q4")])
    annualPeriods = annualPeriods[-MAX_RATIO_YEARS:]

    history = []
    for col in reversed(annualPeriods):
        r = rev.get(col)
        if r is None or r == 0:
            continue

        def _pct(val):
            if val is None:
                return None
            return round(val / r * 100, 2)

        steps = [
            {"label": "매출", "pct": 100.0, "cumPct": 100.0},
        ]
        cogsP = _pct(cogs.get(col))
        if cogsP is not None:
            steps.append({"label": "매출원가", "pct": -abs(cogsP), "cumPct": _pct(gp.get(col)) or (100 - abs(cogsP))})

        gpP = _pct(gp.get(col))
        if gpP is not None:
            steps.append({"label": "매출총이익", "pct": gpP, "cumPct": gpP})

        sgaP = _pct(sgaRow.get(col))
        if sgaP is not None:
            steps.append(
                {"label": "판관비", "pct": -abs(sgaP), "cumPct": _pct(opRow.get(col)) or (gpP or 0) - abs(sgaP)}
            )

        opP = _pct(opRow.get(col))
        if opP is not None:
            steps.append({"label": "영업이익", "pct": opP, "cumPct": opP})

        intExpP = _pct(intExp.get(col))
        intIncP = _pct(intInc.get(col))
        if intExpP is not None:
            steps.append({"label": "이자비용", "pct": -abs(intExpP), "cumPct": round((opP or 0) - abs(intExpP), 2)})
        if intIncP is not None:
            steps.append(
                {
                    "label": "이자수익",
                    "pct": abs(intIncP),
                    "cumPct": round((opP or 0) - abs(intExpP or 0) + abs(intIncP), 2),
                }
            )

        pbtP = _pct(pbt.get(col))
        if pbtP is not None:
            steps.append({"label": "세전이익", "pct": pbtP, "cumPct": pbtP})

        taxP = _pct(tax.get(col))
        if taxP is not None:
            steps.append({"label": "법��세", "pct": -abs(taxP), "cumPct": round((pbtP or 0) - abs(taxP), 2)})

        niP = _pct(ni.get(col))
        if niP is not None:
            steps.append({"label": "순이익", "pct": niP, "cumPct": niP})

        history.append({"period": col, "steps": steps})

    return {"history": history} if history else None


def calcProfitabilityFlags(company) -> list[str]:
    """수익성 경고/기회 플래그."""
    flags: list[str] = []
    result = getRatioSeries(company)
    if result is None:
        return flags

    data, _years = result

    # 영업이익률 추세
    om = data.get("RATIO", {}).get("operatingMargin", [])
    recent = [v for v in om[-3:] if v is not None]
    if len(recent) >= 3 and all(recent[i] > recent[i + 1] for i in range(len(recent) - 1)):
        flags.append(f"영업이익률 3기 연속 하락 ({recent[-1]:.1f}%)")
    if recent and recent[-1] is not None and recent[-1] < 0:
        flags.append(f"영업적자 ({recent[-1]:.1f}%)")

    # ROE 레버리지 과다
    roe = data.get("RATIO", {}).get("roe", [])
    roa = data.get("RATIO", {}).get("roa", [])
    if roe and roa:
        latestRoe = next((v for v in reversed(roe) if v is not None), None)
        latestRoa = next((v for v in reversed(roa) if v is not None), None)
        if latestRoe is not None and latestRoa is not None and latestRoa > 0:
            lev = latestRoe / latestRoa
            if lev > 3:
                flags.append(f"ROE의 레버리지 의존도 높음 (ROE/ROA = {lev:.1f}배)")
            if latestRoe > 15 and latestRoa > 5 and lev < 2:
                flags.append(f"진성 고수익 (ROE {latestRoe:.1f}%, 낮은 레버리지)")

    return flags
