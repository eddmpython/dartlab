"""자본배분 분석 — 배당, 주주환원, 재투자, FCF 사용처 시계열.

벌어들인 돈을 어디에 쓰는지를 시계열로 추적한다.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    annualColsFromPeriods,
    getFlowValue,
    isQuarterlyFallback,
    toDictBySnakeId,
)
from dartlab.analysis.financial._memoize import memoized_calc

_MAX_YEARS = 8


# ── 유틸 ──


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _pct(part: float, total: float) -> float | None:
    if total is None or total == 0:
        return None
    return round(part / total * 100, 2)


# ── 배당 정책 ──


@memoized_calc
def calcDividendPolicy(company, *, basePeriod: str | None = None) -> dict | None:
    """배당 정책 시계열 — 배당성향, 배당금 추이, 연속 배당.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "dividendsPaid": float,
                    "netIncome": float,
                    "payoutRatio": float | None,
                    "dividendGrowth": float | None,
                },
                ...
            ],
            "consecutiveYears": int,
        }
    """
    cfResult = company.select("CF", ["dividends_paid"])
    isResult = company.select("IS", ["당기순이익"])

    cfParsed = toDictBySnakeId(cfResult)
    isParsed = toDictBySnakeId(isResult)
    if cfParsed is None or isParsed is None:
        return None

    cfData, cfPeriods = cfParsed
    isData, _ = isParsed

    divRow = cfData.get("dividends_paid", {})
    niRow = isData.get("net_profit", {})

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    _qMode = isQuarterlyFallback(yCols)
    _allP = set(cfPeriods)

    def _getF(row: dict, col: str) -> float:
        v = getFlowValue(row, col, _qMode, _allP)
        return v if v is not None else 0

    history = []
    consecutiveYears = 0
    countingConsecutive = True

    for i, col in enumerate(yCols):
        divPaid = abs(_getF(divRow, col))  # CF에서 음수로 나옴
        ni = _getF(niRow, col)

        payoutRatio = _pct(divPaid, ni) if ni > 0 else None

        # 배당 성장률
        dividendGrowth = None
        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevDiv = abs(_getF(divRow, prevCol))
            if prevDiv > 0:
                dividendGrowth = round((divPaid - prevDiv) / prevDiv * 100, 2)

        history.append(
            {
                "period": col,
                "dividendsPaid": divPaid,
                "netIncome": ni,
                "payoutRatio": payoutRatio,
                "dividendGrowth": dividendGrowth,
            }
        )

        # 연속 배당 연수
        if countingConsecutive:
            if divPaid > 0:
                consecutiveYears += 1
            else:
                countingConsecutive = False

    return {"history": history, "consecutiveYears": consecutiveYears} if history else None


# ── 주주환원 ──


@memoized_calc
def calcShareholderReturn(company, *, basePeriod: str | None = None) -> dict | None:
    """주주환��� 시계열 — 배당 + 자사주 매입 vs FCF.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "dividendsPaid": float,
                    "treasuryStockPurchase": float,
                    "totalReturn": float,
                    "fcf": float,
                    "returnToFcf": float | None,
                },
                ...
            ],
        }
    """
    cfResult = company.select(
        "CF",
        [
            "operating_cashflow",
            "purchase_of_property_plant_and_equipment",
            "purchase_of_intangible_assets",
            "dividends_paid",
            "purchase_of_treasury_stock",
        ],
    )

    cfParsed = toDictBySnakeId(cfResult)
    if cfParsed is None:
        return None

    cfData, cfPeriods = cfParsed

    ocfRow = cfData.get("operating_cashflow", {})
    capexRow = cfData.get("purchase_of_property_plant_and_equipment", {})
    intCapexRow = cfData.get("purchase_of_intangible_assets", {})
    divRow = cfData.get("dividends_paid", {})
    tsRow = cfData.get("purchase_of_treasury_stock", {})

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    _qMode2 = isQuarterlyFallback(yCols)
    _allP2 = set(cfPeriods)

    def _getF2(row: dict, col: str) -> float:
        v = getFlowValue(row, col, _qMode2, _allP2)
        return v if v is not None else 0

    history = []
    for col in yCols:
        divPaid = abs(_getF2(divRow, col))
        ocf = _getF2(ocfRow, col)
        capex = abs(_getF2(capexRow, col)) + abs(_getF2(intCapexRow, col))
        fcf = ocf - capex

        tsPurchase = abs(_getF2(tsRow, col))

        totalReturn = divPaid + tsPurchase
        returnToFcf = _pct(totalReturn, fcf) if fcf > 0 else None

        history.append(
            {
                "period": col,
                "dividendsPaid": divPaid,
                "treasuryStockPurchase": tsPurchase,
                "totalReturn": totalReturn,
                "fcf": fcf,
                "returnToFcf": returnToFcf,
            }
        )

    return {"history": history} if history else None


# ── 재투자 ──


@memoized_calc
def calcReinvestment(company, *, basePeriod: str | None = None) -> dict | None:
    """재투자 시계열 — 재투자율, CAPEX/매출.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "capex": float,
                    "operatingIncome": float,
                    "revenue": float,
                    "capexToRevenue": float | None,
                    "retentionRate": float | None,
                },
                ...
            ],
        }
    """
    cfResult = company.select(
        "CF",
        ["purchase_of_property_plant_and_equipment", "purchase_of_intangible_assets", "dividends_paid"],
    )
    isResult = company.select("IS", ["영업이익", "매출액", "당기순이익"])

    cfParsed = toDictBySnakeId(cfResult)
    isParsed = toDictBySnakeId(isResult)
    if cfParsed is None or isParsed is None:
        return None

    cfData, cfPeriods = cfParsed
    isData, _ = isParsed

    capexRow = cfData.get("purchase_of_property_plant_and_equipment", {})
    intCapexRow = cfData.get("purchase_of_intangible_assets", {})
    divRow = cfData.get("dividends_paid", {})
    opRow = isData.get("operating_profit", {})
    revRow = isData.get("sales", {})
    niRow = isData.get("net_profit", {})

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    _qMode3 = isQuarterlyFallback(yCols)
    _allP3 = set(cfPeriods)

    def _getF3(row: dict, col: str) -> float:
        v = getFlowValue(row, col, _qMode3, _allP3)
        return v if v is not None else 0

    history = []
    for col in yCols:
        capex = abs(_getF3(capexRow, col)) + abs(_getF3(intCapexRow, col))
        opIncome = _getF3(opRow, col)
        rev = _getF3(revRow, col)
        ni = _getF3(niRow, col)
        divPaid = abs(_getF3(divRow, col))

        # 유보율 = 1 - 배당성향
        retentionRate = None
        if ni > 0:
            payoutRatio = divPaid / ni
            retentionRate = (1 - payoutRatio) * 100

        history.append(
            {
                "period": col,
                "capex": capex,
                "operatingIncome": opIncome,
                "revenue": rev,
                "capexToRevenue": _pct(capex, rev),
                "retentionRate": retentionRate,
            }
        )

    return {"history": history} if history else None


# ─�� FCF 사용처 분해 ──


@memoized_calc
def calcFcfUsage(company, *, basePeriod: str | None = None) -> dict | None:
    """FCF 사용처 분해 시계열 — 배당/부채상환/잔여.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "fcf": float,
                    "dividendsPaid": float,
                    "debtRepaid": float,
                    "residual": float,
                },
                ...
            ],
        }
    """
    cfResult = company.select(
        "CF",
        [
            "operating_cashflow",
            "purchase_of_property_plant_and_equipment",
            "purchase_of_intangible_assets",
            "dividends_paid",
            "repayment_of_longterm_borrowings",
            "redemption_of_current_portion_of_longterm_borrowings",
            "repayment_of_bonds_and_longterm_borrowings",
        ],
    )
    cfParsed = toDictBySnakeId(cfResult)
    if cfParsed is None:
        return None

    cfData, cfPeriods = cfParsed
    ocfRow = cfData.get("operating_cashflow", {})
    capexRow = cfData.get("purchase_of_property_plant_and_equipment", {})
    intCapexRow = cfData.get("purchase_of_intangible_assets", {})
    divRow = cfData.get("dividends_paid", {})
    repayRow1 = cfData.get("repayment_of_longterm_borrowings", {})
    repayRow2 = cfData.get("redemption_of_current_portion_of_longterm_borrowings", {})
    repayRow3 = cfData.get("repayment_of_bonds_and_longterm_borrowings", {})

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    _qMode4 = isQuarterlyFallback(yCols)
    _allP4 = set(cfPeriods)

    def _getF4(row: dict, col: str) -> float:
        v = getFlowValue(row, col, _qMode4, _allP4)
        return v if v is not None else 0

    history = []
    for col in yCols:
        ocf = _getF4(ocfRow, col)
        capex = abs(_getF4(capexRow, col)) + abs(_getF4(intCapexRow, col))
        fcf = ocf - capex
        divPaid = abs(_getF4(divRow, col))
        debtRepaid = abs(_getF4(repayRow1, col)) + abs(_getF4(repayRow2, col)) + abs(_getF4(repayRow3, col))
        residual = fcf - divPaid - debtRepaid

        history.append(
            {
                "period": col,
                "fcf": fcf,
                "dividendsPaid": divPaid,
                "debtRepaid": debtRepaid,
                "residual": residual,
            }
        )

    return {"history": history} if history else None


# ── 배당 서술 보강 (docs) ──


@memoized_calc
def calcDividendDocs(company, *, basePeriod: str | None = None) -> dict | None:
    """docs dividend 토픽에서 배당성향, 배당수익률, 주당배당금 추출.

    반환::

        {
            "dps": float | None,
            "payoutRatio": float | None,
            "dividendYield": float | None,
            "period": str,
        }
    """
    from dartlab.analysis.financial._helpers import parseNumStr

    result = company.select("dividend", ["주당현금배당금", "현금배당성향", "현금배당수익률"])
    if result is None:
        return None

    import polars as pl

    df = result if isinstance(result, pl.DataFrame) else getattr(result, "df", None)
    if df is None or "항목" not in df.columns:
        return None

    from dartlab.analysis.financial._helpers import periodCols

    pCols = periodCols(df)
    if not pCols:
        return None

    latestCol = pCols[0]
    items = df["항목"].to_list()
    vals = df[latestCol].to_list()

    dps = None
    payoutRatio = None
    dividendYield = None

    for it, v in zip(items, vals):
        it = str(it)
        parsed = parseNumStr(str(v))
        if parsed is None:
            continue
        if "주당현금배당금" in it and "보통주" in it and dps is None:
            dps = parsed
        elif "현금배당성향" in it and "당기" in it and payoutRatio is None:
            payoutRatio = parsed
        elif "현금배당수익률" in it and "보통주" in it and dividendYield is None:
            dividendYield = parsed

    if dps is None and payoutRatio is None and dividendYield is None:
        return None

    return {
        "dps": dps,
        "payoutRatio": payoutRatio,
        "dividendYield": dividendYield,
        "period": latestCol,
    }


# ── 자사주 현황 (docs/report) ──


@memoized_calc
def calcTreasuryStockStatus(company, *, basePeriod: str | None = None) -> dict | None:
    """treasuryStock 토픽에서 자사주 취득/처분/소각 현황 추출.

    반환::

        {
            "rows": [
                {"method": str, "beginShares": float, "acquired": float,
                 "disposed": float, "retired": float, "endShares": float},
                ...
            ],
        }
    """
    result = company.show("treasuryStock")
    if result is None:
        return None

    import polars as pl

    if not isinstance(result, pl.DataFrame):
        return None

    # report 토픽 — 이미 수치 DataFrame
    if "기말수량" not in result.columns and "기말잔량" not in result.columns:
        return None

    endCol = "기말수량" if "기말수량" in result.columns else "기말잔량"
    beginCol = "기초수량" if "기초수량" in result.columns else None
    acqCol = "변동수량(취득)" if "변동수량(취득)" in result.columns else None
    dispCol = "변동수량(처분)" if "변동수량(처분)" in result.columns else None
    retCol = "변동수량(소각)" if "변동수량(소각)" in result.columns else None

    # 총계 행만 추출
    rows = []
    for row in result.iter_rows(named=True):
        method = str(row.get("취득방법(대)", row.get("취득방법(중)", "")))
        if "총계" not in method:
            continue
        entry = {"method": method}
        if beginCol:
            entry["beginShares"] = row.get(beginCol)
        if acqCol:
            entry["acquired"] = row.get(acqCol)
        if dispCol:
            entry["disposed"] = row.get(dispCol)
        if retCol:
            entry["retired"] = row.get(retCol)
        entry["endShares"] = row.get(endCol)
        rows.append(entry)

    return {"rows": rows} if rows else None


# ── 플래그 ──


@memoized_calc
def calcCapitalAllocationFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """자본배분 경고 신호."""
    flags = []

    dividend = calcDividendPolicy(company, basePeriod=basePeriod)
    if dividend and dividend["history"]:
        h0 = dividend["history"][0]
        pr = h0.get("payoutRatio")
        if pr is not None and pr > 100:
            flags.append(f"배당���향 {pr:.0f}% — 이익 초과 배당")

        # 배당 3년 연속 감소
        hist = dividend["history"]
        if len(hist) >= 3:
            divs = [h["dividendsPaid"] for h in hist[:3]]
            if divs[0] < divs[1] < divs[2] and divs[2] > 0:
                flags.append("배당금 3년 연속 감소")

    shareholder = calcShareholderReturn(company, basePeriod=basePeriod)
    if shareholder and shareholder["history"]:
        h0 = shareholder["history"][0]
        rtf = h0.get("returnToFcf")
        if rtf is not None and rtf > 100:
            flags.append(f"주주환원/FCF {rtf:.0f}% — FCF 초과 환원")

    reinvest = calcReinvestment(company, basePeriod=basePeriod)
    if reinvest and reinvest["history"]:
        h0 = reinvest["history"][0]
        cr = h0.get("capexToRevenue")
        if cr is not None and cr < 1:
            flags.append(f"CAPEX/매출 {cr:.1f}% — 극소 투자")

    return flags
