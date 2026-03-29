"""세금 분석 — 유효세율, 세금 현금화, 이연법인세 시계열.

세금 부담의 실체와 미래 세금 리스크를 시계열로 추적한다.
"""

from __future__ import annotations

_MAX_YEARS = 5


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDict

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


# ── 유효세율 ──


def calcEffectiveTaxRate(company) -> dict | None:
    """유효세율 시계열 — 법인세비용/세전이익.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "preTaxIncome": float,
                    "taxExpense": float,
                    "effectiveTaxRate": float | None,
                    "statutoryRate": float,
                    "taxGap": float | None,
                },
                ...
            ],
        }
    """
    accounts = ["법인세비용", "법인세차감전순이익", "세전이익"]
    isResult = company.select("IS", accounts)
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", isData.get("세전이익", {}))

    yCols = _annualCols(isPeriods, _MAX_YEARS)
    if not yCols:
        return None

    # 법정세율 (한국 기준, 2023~)
    statutoryRate = 24.0  # 과세표준 구간에 따라 다르나 대기업 근사

    history = []
    for col in yCols:
        ptIncome = _get(ptRow, col)
        taxExpense = _get(taxRow, col)

        effectiveTaxRate = None
        taxGap = None
        if ptIncome > 0:
            effectiveTaxRate = abs(taxExpense) / ptIncome * 100
            taxGap = effectiveTaxRate - statutoryRate

        history.append(
            {
                "period": col,
                "preTaxIncome": ptIncome,
                "taxExpense": taxExpense,
                "effectiveTaxRate": effectiveTaxRate,
                "statutoryRate": statutoryRate,
                "taxGap": taxGap,
            }
        )

    return {"history": history} if history else None


# ── 세금 현금화 ──


def calcTaxCashConversion(company) -> dict | None:
    """세금 현금화 시계열 — IS 법인세비용 vs CF 법인세납부.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "taxExpense": float,
                    "taxPaid": float | None,
                    "taxCashRatio": float | None,
                },
                ...
            ],
        }
    """
    isResult = company.select("IS", ["법인세비용"])
    cfResult = company.select("CF", ["payments_of_income_taxes"])

    isParsed = _toDict(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    taxExpRow = isData.get("법인세비용", {})

    from dartlab.analysis.financial._helpers import toDictBySnakeId

    cfParsed = toDictBySnakeId(cfResult)
    cfData = cfParsed[0] if cfParsed else {}
    taxPaidRow = cfData.get("payments_of_income_taxes", {})

    yCols = _annualCols(isPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        taxExpense = abs(_get(taxExpRow, col))
        taxPaidVal = taxPaidRow.get(col) if taxPaidRow else None
        taxPaid = abs(taxPaidVal) if taxPaidVal is not None else None

        taxCashRatio = None
        if taxPaid is not None and taxExpense > 0:
            taxCashRatio = taxPaid / taxExpense * 100

        history.append(
            {
                "period": col,
                "taxExpense": taxExpense,
                "taxPaid": taxPaid,
                "taxCashRatio": taxCashRatio,
            }
        )

    return {"history": history} if history else None


# ── 이연법인세 ──


def calcDeferredTax(company) -> dict | None:
    """이연법인세 시계열 — 이연자산/부채 추세.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "deferredTaxAsset": float,
                    "deferredTaxLiability": float,
                    "netDeferredTax": float,
                    "dtaToTotalAssets": float | None,
                },
                ...
            ],
        }
    """
    bsResult = company.select("BS", ["이연법인세자산", "이연법인세부채", "자산총계"])
    bsParsed = _toDict(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    dtaRow = bsData.get("이연법인세자산", {})
    dtlRow = bsData.get("이연법인세부채", {})
    taRow = bsData.get("자산총계", {})

    yCols = _annualCols(bsPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        dta = _get(dtaRow, col)
        dtl = _get(dtlRow, col)
        ta = _get(taRow, col)
        netDt = dta - dtl

        history.append(
            {
                "period": col,
                "deferredTaxAsset": dta,
                "deferredTaxLiability": dtl,
                "netDeferredTax": netDt,
                "dtaToTotalAssets": _pct(dta, ta),
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


def calcTaxFlags(company) -> list[str]:
    """세금 관련 경고 신호."""
    flags = []

    etr = calcEffectiveTaxRate(company)
    if etr and etr["history"]:
        h0 = etr["history"][0]
        rate = h0.get("effectiveTaxRate")
        if rate is not None:
            if rate < 10:
                flags.append(f"유효세율 {rate:.1f}% — 극저세율 (세금 혜택 또는 이연)")
            elif rate > 35:
                flags.append(f"유효세율 {rate:.1f}% — 고세율 (추가 세금 부담)")

    cashConv = calcTaxCashConversion(company)
    if cashConv and cashConv["history"]:
        h0 = cashConv["history"][0]
        tcr = h0.get("taxCashRatio")
        if tcr is not None and tcr > 150:
            flags.append(f"세금현금비율 {tcr:.0f}% — 법인세 과대 납부 (과거 이연분 정산)")

    deferred = calcDeferredTax(company)
    if deferred and len(deferred["history"]) >= 2:
        hist = deferred["history"]
        dta0 = hist[0]["deferredTaxAsset"]
        dta1 = hist[1]["deferredTaxAsset"]
        if dta1 > 0 and dta0 / dta1 > 2:
            flags.append(f"이연법인세자산 {dta0 / dta1:.1f}배 급증 — 미래 과세소득 가정 검토")

    return flags
