"""투자 분석 — ROIC, WACC Spread, 투자 강도, EVA 시계열.

투자가 실제로 가치를 만드는지를 시계열로 추적한다.
"""

from __future__ import annotations

_MAX_YEARS = 5


# ── 유틸 ──


def _toDictBySnakeId(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.strategy._helpers import toDictBySnakeId

    return toDictBySnakeId(selectResult)


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.strategy._helpers import toDict

    return toDict(selectResult)


def _annualCols(periods: list[str], maxYears: int = _MAX_YEARS) -> list[str]:
    cols = sorted([c for c in periods if "Q" not in c], reverse=True)
    if cols:
        return cols[:maxYears]
    return sorted([c for c in periods if c.endswith("Q4")], reverse=True)[:maxYears]


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _pct(part: float, total: float) -> float | None:
    if total is None or total == 0:
        return None
    return part / total * 100


def _estimateWacc(equity: float, debt: float) -> float | None:
    """부채/자본 비율로 WACC 추정."""
    if equity is None or debt is None or equity <= 0:
        return None
    debtRatio = debt / equity
    debtWeight = debtRatio / (1 + debtRatio) if debtRatio > 0 else 0
    equityWeight = 1 - debtWeight
    costOfDebt = 5.0
    costOfEquity = 8.0
    return equityWeight * costOfEquity + debtWeight * costOfDebt * 0.75


# ── ROIC + Spread ──


def calcRoicTimeline(company) -> dict | None:
    """ROIC 연간 시계열 + WACC 추정 + Spread (가치 창출/파괴).

    ratioSeries에서 Q4(연간) 값만 추출하여 연간 시계열로 변환.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "roic": float | None,
                    "waccEstimate": float | None,
                    "spread": float | None,
                },
                ...
            ],
        }
    """
    from dartlab.analysis.strategy._helpers import getRatioSeries

    rs = getRatioSeries(company)
    if rs is None:
        return None

    data, years = rs
    ratioDict = data.get("RATIO", {})
    roicVals = ratioDict.get("roic", [])

    if not roicVals or not years:
        return None

    # Q4(연간) 데이터만 필터
    annualPairs = []
    for i, y in enumerate(years):
        if "Q" not in y or y.endswith("Q4"):
            roic = roicVals[i] if i < len(roicVals) else None
            annualPairs.append((y, roic))

    if not annualPairs:
        return None

    # 최신 _MAX_YEARS개
    annualPairs = annualPairs[-_MAX_YEARS:]

    # WACC 추정에 필요한 부채/자본
    bsResult = company.select("BS", ["자본총계", "부채총계"])
    bsParsed = _toDict(bsResult)
    bsData = bsParsed[0] if bsParsed else {}
    eqRow = bsData.get("자본총계", {})
    debtRow = bsData.get("부채총계", {})

    history = []
    for period, roic in reversed(annualPairs):  # 최신 먼저
        equity = eqRow.get(period)
        debt = debtRow.get(period)
        waccEstimate = _estimateWacc(equity, debt)

        spread = None
        if roic is not None and waccEstimate is not None:
            spread = roic - waccEstimate

        history.append(
            {
                "period": period,
                "roic": roic,
                "waccEstimate": waccEstimate,
                "spread": spread,
            }
        )

    return {"history": history} if history else None


# ── 투자 강도 ──


def calcInvestmentIntensity(company) -> dict | None:
    """투자 강도 시계열 — CAPEX/매출, 유무형 비율.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "capexToRevenue": float | None,
                    "tangibleRatio": float | None,
                    "intangibleRatio": float | None,
                },
                ...
            ],
        }
    """
    cfResult = company.select(
        "CF",
        ["purchase_of_property_plant_and_equipment", "purchase_of_intangible_assets"],
    )
    isResult = company.select("IS", ["매출액"])
    bsResult = company.select("BS", ["유형자산", "무형자산", "자산총계"])

    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    cfParsed = _toDictBySnakeId(cfResult)
    cfData = cfParsed[0] if cfParsed else {}
    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    capexRow = cfData.get("purchase_of_property_plant_and_equipment", {})
    intCapexRow = cfData.get("purchase_of_intangible_assets", {})
    revRow = isData.get("매출액", {})
    ppeRow = bsData.get("유형자산", {})
    intRow = bsData.get("무형자산", {})
    taRow = bsData.get("자산총계", {})

    yCols = _annualCols(isPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        capex = abs(_get(capexRow, col)) + abs(_get(intCapexRow, col))
        rev = _get(revRow, col)
        ppe = _get(ppeRow, col)
        intangible = _get(intRow, col)
        ta = _get(taRow, col)

        history.append(
            {
                "period": col,
                "capexToRevenue": _pct(capex, rev),
                "tangibleRatio": _pct(ppe, ta),
                "intangibleRatio": _pct(intangible, ta),
            }
        )

    return {"history": history} if history else None


# ── EVA ──


def calcEvaTimeline(company) -> dict | None:
    """EVA(경제적 부가가치) 시계열 — NOPAT - (투하자본 x WACC).

    반환::

        {
            "history": [
                {
                    "period": str,
                    "nopat": float | None,
                    "investedCapital": float,
                    "waccEstimate": float | None,
                    "eva": float | None,
                },
                ...
            ],
        }
    """
    isResult = company.select("IS", ["영업이익", "법인세비용", "법인세차감전순이익"])
    bsResult = company.select("BS", ["자본총계", "부채총계"])

    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    opRow = isData.get("영업이익", {})
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", {})
    eqRow = bsData.get("자본총계", {})
    debtRow = bsData.get("부채총계", {})

    yCols = _annualCols(isPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        opIncome = _get(opRow, col)
        taxExpense = _get(taxRow, col)
        ptIncome = _get(ptRow, col)

        # 유효세율
        effectiveTaxRate = abs(taxExpense) / abs(ptIncome) if ptIncome != 0 else 0.25
        effectiveTaxRate = min(effectiveTaxRate, 0.5)

        nopat = opIncome * (1 - effectiveTaxRate) if opIncome != 0 else None

        # 투하자본 = 자본 + 부채
        equity = _get(eqRow, col)
        totalDebt = _get(debtRow, col)
        investedCapital = equity + totalDebt

        # WACC 자체 계산 (ROIC 의존 제거)
        waccEstimate = _estimateWacc(equity, totalDebt)

        eva = None
        if nopat is not None and waccEstimate is not None and investedCapital > 0:
            eva = nopat - (investedCapital * waccEstimate / 100)

        history.append(
            {
                "period": col,
                "nopat": nopat,
                "investedCapital": investedCapital,
                "waccEstimate": waccEstimate,
                "eva": eva,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


def calcInvestmentFlags(company) -> list[str]:
    """투자 분석 경고 신호."""
    flags = []

    roic = calcRoicTimeline(company)
    if roic and len(roic["history"]) >= 2:
        hist = roic["history"]
        negSpreads = 0
        for h in hist[:2]:
            s = h.get("spread")
            if s is not None and s < 0:
                negSpreads += 1
        if negSpreads >= 2:
            flags.append("ROIC < WACC 2년 연속 — 가치 파괴 지속")

    eva = calcEvaTimeline(company)
    if eva and len(eva["history"]) >= 3:
        hist = eva["history"]
        negEva = sum(1 for h in hist[:3] if h.get("eva") is not None and h["eva"] < 0)
        if negEva >= 3:
            flags.append("EVA 3년 연속 음수 — 경제적 부가가치 적자")

    intensity = calcInvestmentIntensity(company)
    if intensity and len(intensity["history"]) >= 2:
        hist = intensity["history"]
        h0 = hist[0]
        h1 = hist[1]
        ir0 = h0.get("intangibleRatio")
        ir1 = h1.get("intangibleRatio")
        if ir0 is not None and ir1 is not None and ir0 - ir1 > 10:
            flags.append(f"무형자산비율 +{ir0 - ir1:.0f}%p 급등 — 대규모 인수 또는 영업권 증가")

    return flags
