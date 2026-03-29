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


def _fetchRiskFreeRate() -> float | None:
    """무위험이자율 (국고채 10년) 조회. 실패 시 None."""
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        result = g("ecos", "TREASURY_10Y")
        if result is not None and hasattr(result, "df"):
            df = result.df
            valCols = [c for c in df.columns if c not in ("date", "indicator", "label")]
            if valCols:
                last = df.select(valCols[-1]).to_series().drop_nulls()
                if len(last) > 0:
                    return float(last[-1])
    except (ImportError, AttributeError, TypeError, ValueError, KeyError):
        pass
    return None


# 캐시: 세션 내 1회만 조회
_riskFreeRateCache: dict[str, float | None] = {}


def _getRiskFreeRate() -> float:
    """무위험이자율. 캐시 + fallback 3.5%."""
    if "rf" not in _riskFreeRateCache:
        rf = _fetchRiskFreeRate()
        _riskFreeRateCache["rf"] = rf
    cached = _riskFreeRateCache["rf"]
    return cached if cached is not None else 3.5


def _estimateWacc(
    equity: float,
    debt: float,
    interestExpense: float | None = None,
    financeCosts: float | None = None,
    effectiveTaxRate: float | None = None,
) -> dict | None:
    """동적 WACC 추정.

    - CoD: interestExpense / totalBorrowing 우선, 없으면 financeCosts. fallback 5%.
    - CoE: CAPM = Rf + 시장 프리미엄(5.5%). Beta 없이 간이 적용.
    - Tax shield: 유효세율 적용. fallback 22%.
    """
    if equity is None or debt is None or equity <= 0:
        return None

    rf = _getRiskFreeRate()
    erp = 5.5  # 한국 시장 리스크 프리미엄

    # CoE = Rf + Beta * ERP (Beta 미제공 시 1.0 가정)
    costOfEquity = rf + 1.0 * erp

    # CoD: 이자비용(순수) 우선 → 금융비용(넓은) fallback → 고정 5%
    costOfDebt = 5.0  # fallback
    kdSource = "fallback"
    # 순수 이자비용이 있으면 우선 사용 (금융비용은 환차손/파생손실 포함)
    if interestExpense is not None and debt > 0:
        impliedRate = abs(interestExpense) / debt * 100
        if 0.5 < impliedRate < 15:
            costOfDebt = round(impliedRate, 2)
            kdSource = "interestExpense"
    # 이자비용 없으면 금융비용으로 추정 (환차손/파생손실 포함 → 상한 6% clamp)
    if kdSource == "fallback" and financeCosts is not None and debt > 0:
        impliedRate = abs(financeCosts) / debt * 100
        if 0.5 < impliedRate < 15:
            # 금융비용은 이자 외 항목 포함 → 보수적 clamp
            clamped = min(impliedRate, 6.0)
            costOfDebt = round(clamped, 2)
            kdSource = "financeCosts"

    # 세율
    taxRate = effectiveTaxRate if effectiveTaxRate is not None and 0 < effectiveTaxRate < 50 else 22.0

    debtRatio = debt / equity
    debtWeight = debtRatio / (1 + debtRatio) if debtRatio > 0 else 0
    equityWeight = 1 - debtWeight

    wacc = equityWeight * costOfEquity + debtWeight * costOfDebt * (1 - taxRate / 100)

    return {
        "wacc": round(wacc, 2),
        "costOfEquity": round(costOfEquity, 2),
        "costOfDebt": round(costOfDebt, 2),
        "kdSource": kdSource,
        "riskFreeRate": round(rf, 2),
        "taxRate": round(taxRate, 2),
        "equityWeight": round(equityWeight * 100, 1),
        "debtWeight": round(debtWeight * 100, 1),
    }


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

    # WACC 추정에 필요한 부채/자본 + 금융비용 + 유효세율
    bsResult = company.select(
        "BS",
        [
            "자본총계",
            "부채총계",
            "단기차입금",
            "장기차입금",
            "사채",
            "차입부채",
            "발행사채",
            "유동금융부채",
            "장기금융부채",
        ],
    )
    isResult = company.select("IS", ["이자비용", "금융비용", "법인세비용", "법인세차감전순이익"])
    bsParsed = _toDict(bsResult)
    isParsed = _toDict(isResult)
    bsData = bsParsed[0] if bsParsed else {}
    isData = isParsed[0] if isParsed else {}

    eqRow = bsData.get("자본총계", {})
    debtRow = bsData.get("부채총계", {})
    # 차입금: 업종별 계정명 차이 대응
    stRow = bsData.get("단기차입금", {})
    ltRow = bsData.get("장기차입금", {})
    bondsRow = bsData.get("사채", {})
    # 금융업: 차입부채/발행사채
    borrowRow = bsData.get("차입부채", {})
    issuedBondRow = bsData.get("발행사채", {})
    # 바이오 등: 유동금융부채/장기금융부채
    curFinRow = bsData.get("유동금융부채", {})
    ltFinRow = bsData.get("장기금융부채", {})
    ieRow = isData.get("이자비용", {})  # 순수 이자비용 (우선)
    fcRow = isData.get("금융비용", {})  # 넓은 금융비용 (fallback)
    taxRow = isData.get("법인세비용", {})
    pbtRow = isData.get("법인세차감전순이익", {})

    history = []
    for period, roic in reversed(annualPairs):  # 최신 먼저
        equity = eqRow.get(period)
        totalDebt = debtRow.get(period)
        # 차입금 합산: 업종별 계정 대응
        tb = (stRow.get(period) or 0) + (ltRow.get(period) or 0) + (bondsRow.get(period) or 0)
        if tb == 0:
            tb = (borrowRow.get(period) or 0) + (issuedBondRow.get(period) or 0)
        if tb == 0:
            tb = (curFinRow.get(period) or 0) + (ltFinRow.get(period) or 0)
        totalBorrowing = tb

        ie = ieRow.get(period)  # 순수 이자비용
        fc = fcRow.get(period)  # 넓은 금융비용
        taxExp = taxRow.get(period)
        pbtVal = pbtRow.get(period)

        etr = None
        if pbtVal and pbtVal > 0 and taxExp is not None:
            etr = abs(taxExp) / pbtVal * 100

        waccResult = _estimateWacc(
            equity,
            totalBorrowing or totalDebt or 0,
            interestExpense=ie,
            financeCosts=fc,
            effectiveTaxRate=etr,
        )
        waccVal = waccResult["wacc"] if waccResult else None

        spread = None
        if roic is not None and waccVal is not None:
            spread = round(roic - waccVal, 2)

        history.append(
            {
                "period": period,
                "roic": roic,
                "wacc": waccResult,
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
    isResult = company.select("IS", ["영업이익", "법인세비용", "법인세차감전순이익", "이자비용", "금융비용"])
    bsResult = company.select(
        "BS",
        [
            "자본총계",
            "부채총계",
            "단기차입금",
            "장기차입금",
            "사채",
            "차입부채",
            "발행사채",
            "유동금융부채",
            "장기금융부채",
        ],
    )

    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    opRow = isData.get("영업이익", {})
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", {})
    ieRow = isData.get("이자비용", {})  # 순수 이자비용 (우선)
    fcRow = isData.get("금융비용", {})  # 넓은 금융비용 (fallback)
    eqRow = bsData.get("자본총계", {})
    debtRow = bsData.get("부채총계", {})
    stRow = bsData.get("단기차입금", {})
    ltRow = bsData.get("장기차입금", {})
    bondsRow = bsData.get("사채", {})
    borrowRow = bsData.get("차입부채", {})
    issuedBondRow = bsData.get("발행사채", {})
    curFinRow = bsData.get("유동금융부채", {})
    ltFinRow = bsData.get("장기금융부채", {})

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
        tb = _get(stRow, col) + _get(ltRow, col) + _get(bondsRow, col)
        if tb == 0:
            tb = _get(borrowRow, col) + _get(issuedBondRow, col)
        if tb == 0:
            tb = _get(curFinRow, col) + _get(ltFinRow, col)
        totalBorrowing = tb
        investedCapital = equity + totalDebt

        ie = ieRow.get(col)  # 순수 이자비용
        fc = fcRow.get(col)  # 넓은 금융비용
        etr = effectiveTaxRate * 100

        waccResult = _estimateWacc(
            equity, totalBorrowing or totalDebt, interestExpense=ie, financeCosts=fc, effectiveTaxRate=etr
        )
        waccVal = waccResult["wacc"] if waccResult else None

        eva = None
        if nopat is not None and waccVal is not None and investedCapital > 0:
            eva = nopat - (investedCapital * waccVal / 100)

        history.append(
            {
                "period": col,
                "nopat": nopat,
                "investedCapital": investedCapital,
                "wacc": waccResult,
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
