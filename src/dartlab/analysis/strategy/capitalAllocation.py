"""자본배분 분석 — 배당, 주주환원, 재투자, FCF 사용처 시계열.

벌어들인 돈을 어디에 쓰는지를 시계열로 추적한다.
"""

from __future__ import annotations

_MAX_YEARS = 5


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.strategy._helpers import toDictBySnakeId

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


# ── 배당 정책 ──


def calcDividendPolicy(company) -> dict | None:
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

    cfParsed = _toDict(cfResult)
    isParsed = _toDict(isResult)
    if cfParsed is None or isParsed is None:
        return None

    cfData, cfPeriods = cfParsed
    isData, _ = isParsed

    divRow = cfData.get("dividends_paid", {})
    niRow = isData.get("net_profit", {})

    yCols = _annualCols(cfPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    consecutiveYears = 0
    countingConsecutive = True

    for i, col in enumerate(yCols):
        divPaid = abs(_get(divRow, col))  # CF에서 음수로 나옴
        ni = _get(niRow, col)

        payoutRatio = _pct(divPaid, ni) if ni > 0 else None

        # 배당 성장률
        dividendGrowth = None
        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevDiv = abs(_get(divRow, prevCol))
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


def calcShareholderReturn(company) -> dict | None:
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

    cfParsed = _toDict(cfResult)
    if cfParsed is None:
        return None

    cfData, cfPeriods = cfParsed

    ocfRow = cfData.get("operating_cashflow", {})
    capexRow = cfData.get("purchase_of_property_plant_and_equipment", {})
    intCapexRow = cfData.get("purchase_of_intangible_assets", {})
    divRow = cfData.get("dividends_paid", {})
    tsRow = cfData.get("purchase_of_treasury_stock", {})

    yCols = _annualCols(cfPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        divPaid = abs(_get(divRow, col))
        ocf = _get(ocfRow, col)
        capex = abs(_get(capexRow, col)) + abs(_get(intCapexRow, col))
        fcf = ocf - capex

        tsPurchase = abs(_get(tsRow, col))

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


def calcReinvestment(company) -> dict | None:
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

    cfParsed = _toDict(cfResult)
    isParsed = _toDict(isResult)
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

    yCols = _annualCols(cfPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        capex = abs(_get(capexRow, col)) + abs(_get(intCapexRow, col))
        opIncome = _get(opRow, col)
        rev = _get(revRow, col)
        ni = _get(niRow, col)
        divPaid = abs(_get(divRow, col))

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


def calcFcfUsage(company) -> dict | None:
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
    cfParsed = _toDict(cfResult)
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

    yCols = _annualCols(cfPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ocf = _get(ocfRow, col)
        capex = abs(_get(capexRow, col)) + abs(_get(intCapexRow, col))
        fcf = ocf - capex
        divPaid = abs(_get(divRow, col))
        debtRepaid = abs(_get(repayRow1, col)) + abs(_get(repayRow2, col)) + abs(_get(repayRow3, col))
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


# ── 플래그 ─���


def calcCapitalAllocationFlags(company) -> list[str]:
    """��본배분 경고 신호."""
    flags = []

    dividend = calcDividendPolicy(company)
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

    shareholder = calcShareholderReturn(company)
    if shareholder and shareholder["history"]:
        h0 = shareholder["history"][0]
        rtf = h0.get("returnToFcf")
        if rtf is not None and rtf > 100:
            flags.append(f"주주환원/FCF {rtf:.0f}% — FCF 초과 환원")

    reinvest = calcReinvestment(company)
    if reinvest and reinvest["history"]:
        h0 = reinvest["history"][0]
        cr = h0.get("capexToRevenue")
        if cr is not None and cr < 1:
            flags.append(f"CAPEX/매출 {cr:.1f}% — 극소 투자")

    return flags
