"""투자 분석 -- ROIC, NOPAT, 투자 강도 시계열.

select()로 IS/BS/CF 원본 계정을 가져와서
투자가 실제로 가치를 만드는지를 금액과 함께 시계열로 추적한다.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import toDict

_MAX_YEARS = 5


def _toDictBySnakeId(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDictBySnakeId

    return toDictBySnakeId(selectResult)


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
    return round(part / total * 100, 2)


def _yoy(cur, prev) -> float | None:
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _estimateWacc(company) -> float | None:
    """company에서 WACC 추정 (compute_company_wacc 래퍼)."""
    try:
        from dartlab.analysis.forecast.proforma import compute_company_wacc

        annual = company.finance.annual
        if annual is None:
            return None
        series, _ = annual
        sectorParams = getattr(company, "sectorParams", None)
        marketCap = None
        market = getattr(company, "market", None)
        if market and isinstance(market, dict):
            marketCap = market.get("marketCap")
        wacc, _ = compute_company_wacc(
            series,
            sector_params=sectorParams,
            market_cap=marketCap,
            currency=getattr(company, "currency", "KRW"),
        )
        return round(wacc, 2)
    except (ImportError, AttributeError, TypeError, ValueError):
        return None


# ── ROIC (NOPAT / 투하자본) ──


def calcRoicTimeline(company) -> dict | None:
    """ROIC 시계열 -- 투하자본 대비 실제 수익률.

    IS에서 영업이익 + 세율, BS에서 자본 + 차입금으로 직접 계산.
    ROIC = NOPAT / Invested Capital
    """
    isResult = company.select("IS", ["영업이익", "법인세비용", "법인세차감전순이익"])
    bsResult = company.select(
        "BS",
        ["자본총계", "단기차입금", "장기차입금", "사채", "현금및현금성자산"],
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
    eqRow = bsData.get("자본총계", {})
    stRow = bsData.get("단기차입금", {})
    ltRow = bsData.get("장기차입금", {})
    bondRow = bsData.get("사채", {})
    cashRow = bsData.get("현금및현금성자산", {})

    yCols = _annualCols(isPeriods, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        opIncome = _get(opRow, col)
        taxExpense = _get(taxRow, col)
        ptIncome = _get(ptRow, col)

        # 유효세율
        effectiveTaxRate = abs(taxExpense) / abs(ptIncome) if ptIncome != 0 else 0.25
        effectiveTaxRate = min(effectiveTaxRate, 0.5)

        nopat = round(opIncome * (1 - effectiveTaxRate)) if opIncome != 0 else None

        equity = _get(eqRow, col)
        totalBorrowing = _get(stRow, col) + _get(ltRow, col) + _get(bondRow, col)
        cash = _get(cashRow, col)
        investedCapital = equity + totalBorrowing - cash

        roic = round(nopat / investedCapital * 100, 2) if nopat is not None and investedCapital > 0 else None

        history.append(
            {
                "period": col,
                "operatingIncome": opIncome if opIncome != 0 else None,
                "effectiveTaxRate": round(effectiveTaxRate * 100, 2),
                "nopat": nopat,
                "equity": equity if equity != 0 else None,
                "totalBorrowing": totalBorrowing if totalBorrowing > 0 else None,
                "cash": cash if cash != 0 else None,
                "investedCapital": investedCapital if investedCapital > 0 else None,
                "roic": roic,
                "roicYoy": _yoy(roic, None),  # 이전 기간 ROIC는 아래서 계산
            }
        )

    # ROIC YoY 후처리 (history가 최신→과거 순)
    for i in range(len(history) - 1):
        cur = history[i].get("roic")
        prev = history[i + 1].get("roic")
        history[i]["roicYoy"] = _yoy(cur, prev)

    # WACC 추정 (최신 시점 1회만, 전 기간 동일 적용)
    waccEstimate = _estimateWacc(company)
    if waccEstimate is not None:
        for h in history:
            h["waccEstimate"] = waccEstimate
            roic = h.get("roic")
            h["spread"] = round(roic - waccEstimate, 2) if roic is not None else None

    return {"history": history} if history else None


# ── 투자 강도 ──


def calcInvestmentIntensity(company) -> dict | None:
    """투자 강도 시계열 -- CAPEX/매출, 유무형 비율."""
    cfResult = company.select(
        "CF",
        ["purchase_of_property_plant_and_equipment", "purchase_of_intangible_assets"],
    )
    isResult = company.select("IS", ["매출액"])
    bsResult = company.select("BS", ["유형자산", "무형자산", "자산총계"])

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
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
                "capex": capex if capex > 0 else None,
                "revenue": rev if rev != 0 else None,
                "tangibleAssets": ppe if ppe != 0 else None,
                "intangibleAssets": intangible if intangible != 0 else None,
                "totalAssets": ta if ta != 0 else None,
                "capexToRevenue": _pct(capex, rev),
                "tangibleRatio": _pct(ppe, ta),
                "intangibleRatio": _pct(intangible, ta),
            }
        )

    return {"history": history} if history else None


# ── NOPAT + 투하자본 ──


def calcEvaTimeline(company) -> dict | None:
    """NOPAT + 투하자본 시계열."""
    isResult = company.select("IS", ["영업이익", "법인세비용", "법인세차감전순이익"])
    bsResult = company.select("BS", ["자본총계", "부채총계"])

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
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

        equity = _get(eqRow, col)
        totalDebt = _get(debtRow, col)
        investedCapital = equity + totalDebt

        # NOPAT / 투하자본 = 투하자본수익률
        nopatReturn = None
        if nopat is not None and investedCapital > 0:
            nopatReturn = round(nopat / investedCapital * 100, 2)

        history.append(
            {
                "period": col,
                "nopat": nopat,
                "investedCapital": investedCapital,
                "nopatReturn": nopatReturn,
                "waccEstimate": None,
                "eva": None,
            }
        )

    # WACC 추정 + EVA 계산
    waccEstimate = _estimateWacc(company)
    if waccEstimate is not None:
        for h in history:
            h["waccEstimate"] = waccEstimate
            nopat = h.get("nopat")
            ic = h.get("investedCapital")
            if nopat is not None and ic is not None and ic > 0:
                h["eva"] = round(nopat - ic * waccEstimate / 100)

    return {"history": history} if history else None


# ── 타법인 출자 현황 (docs) ──


def calcInvestmentInOther(company) -> dict | None:
    """investmentInOtherDetail docs 토픽에서 타법인 출자 총액 추출.

    반환::

        {
            "totalBookValue": float | None,
            "description": str | None,
            "period": str | None,
        }
    """
    import re

    from dartlab.analysis.financial._helpers import parseNumStr

    result = company.show("investmentInOtherDetail")
    if result is None:
        return None

    import polars as pl

    if not isinstance(result, pl.DataFrame):
        return None

    # block index 형태 — text 블록에서 총액 서술 추출
    if "block" in result.columns and "preview" in result.columns:
        textBlocks = result.filter(pl.col("type") == "text")
        for row in textBlocks.iter_rows(named=True):
            preview = str(row.get("preview", ""))
            # "타법인 출자 금액은 장부금액 기준 59조 2,469억원" 패턴
            m = re.search(r"출자\s*금액[^\d]*?([\d,]+)\s*조\s*([\d,]+)\s*억", preview)
            if m:
                tril = parseNumStr(m.group(1))
                bil = parseNumStr(m.group(2))
                if tril is not None and bil is not None:
                    total = tril * 10000 + bil  # 억원 단위
                    # 연도 추출
                    ym = re.search(r"(\d{4})년", preview)
                    period = ym.group(1) if ym else None
                    return {
                        "totalBookValue": total,
                        "description": preview[:200],
                        "period": period,
                    }
            # "XX억원" 패턴 (조 단위 없는 경우)
            m2 = re.search(r"출자\s*금액[^\d]*?([\d,]+)\s*억", preview)
            if m2:
                bil = parseNumStr(m2.group(1))
                if bil is not None:
                    ym = re.search(r"(\d{4})년", preview)
                    period = ym.group(1) if ym else None
                    return {
                        "totalBookValue": bil,
                        "description": preview[:200],
                        "period": period,
                    }

    return None


# ── 플래그 ──


def calcInvestmentFlags(company) -> list[str]:
    """투자 분석 경고 신호."""
    flags = []

    roic = calcRoicTimeline(company)
    if roic and len(roic["history"]) >= 3:
        hist = roic["history"]
        declining = all(h.get("roic") is not None and h["roic"] < 5 for h in hist[:3])
        if declining:
            latest = hist[0].get("roic")
            flags.append(f"ROIC {latest:.1f}% — 3년 연속 저수익 (자본비용 미회수 가능성)")

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
