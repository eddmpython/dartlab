"""2-2 성장성 분석 -- 무엇이 얼마나 커졌는가.

select()로 IS/BS/CF 원본 계정을 가져와서
금액 + YoY + CAGR + 이익 vs 매출 성장 괴리를 시계열로 보여준다.
"""

from __future__ import annotations

from dartlab.analysis.strategy._helpers import (
    MAX_RATIO_YEARS,
    getRatioSeries,
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


def _cagr(values: list[float | None], periods: int) -> float | None:
    valid = [v for v in values if v is not None and v > 0]
    if len(valid) < 2 or periods < 1:
        return None
    first, last = valid[0], valid[-1]
    if first <= 0:
        return None
    return round((pow(last / first, 1 / periods) - 1) * 100, 2)


# ── 성장 추이 ──


def calcGrowthTrend(company) -> dict | None:
    """성장 추이 -- 매출/영업이익/순이익/자산의 금액과 YoY.

    IS + BS에서 원본 금액을 가져와 규모감과 방향을 동시에 본다.
    """
    isResult = company.select(
        "IS",
        ["매출액", "영업이익", "당기순이익"],
    )
    bsResult = company.select("BS", ["자산총계"])

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData = bsParsed[0] if bsParsed else {}

    rev = isData.get("매출액", {})
    op = isData.get("영업이익", {})
    ni = isData.get("당기순이익", {})
    ta = bsData.get("자산총계", {})

    yCols = _annualCols(isPeriods, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None

        history.append(
            {
                "period": col,
                "revenue": rev.get(col),
                "revenueYoy": _yoy(rev.get(col), rev.get(prevCol)) if prevCol else None,
                "operatingIncome": op.get(col),
                "operatingIncomeYoy": _yoy(op.get(col), op.get(prevCol)) if prevCol else None,
                "netIncome": ni.get(col),
                "netIncomeYoy": _yoy(ni.get(col), ni.get(prevCol)) if prevCol else None,
                "totalAssets": ta.get(col),
                "totalAssetsYoy": _yoy(ta.get(col), ta.get(prevCol)) if prevCol else None,
            }
        )

    # CAGR
    revVals = [rev.get(c) for c in reversed(yCols)]
    opVals = [op.get(c) for c in reversed(yCols)]
    niVals = [ni.get(c) for c in reversed(yCols)]
    n = len(yCols) - 1

    return (
        {
            "history": history,
            "cagr": {
                "revenue": _cagr(revVals, n),
                "operatingIncome": _cagr(opVals, n),
                "netIncome": _cagr(niVals, n),
                "periods": n,
            },
        }
        if history
        else None
    )


# ── 성장 품질 ──


def calcGrowthQuality(company) -> dict | None:
    """성장 품질 -- 매출 성장이 이익으로 이어지는가.

    매출 vs 영업이익 성장률 괴리를 본다.
    매출만 크고 이익이 안 따라오면 외형 위주.
    """
    trend = calcGrowthTrend(company)
    if trend is None or len(trend["history"]) < 2:
        return None

    cagr = trend["cagr"]
    revCagr = cagr.get("revenue")
    opCagr = cagr.get("operatingIncome")

    quality = "판단 불가"
    if revCagr is not None and opCagr is not None:
        if revCagr > 0 and opCagr < revCagr * 0.5:
            quality = "외형 위주"
        elif opCagr > revCagr * 1.5 and opCagr > 0:
            quality = "내실 위주"
        elif revCagr > 0 and opCagr > 0:
            quality = "균형"
        elif revCagr < 0:
            quality = "역성장"

    # 이익 성장률이 매출보다 빠른지 (operating leverage)
    hist = trend["history"]
    leverageEffect = []
    for h in hist:
        ry = h.get("revenueYoy")
        oy = h.get("operatingIncomeYoy")
        if ry is not None and oy is not None and ry != 0:
            leverageEffect.append(
                {
                    "period": h["period"],
                    "revenueYoy": ry,
                    "operatingIncomeYoy": oy,
                    "operatingLeverage": round(oy / ry, 2),
                }
            )

    return {
        "quality": quality,
        "cagr": cagr,
        "leverageEffect": leverageEffect,
    }


# ── SGR + 갭 ──


def calcSustainableGrowthRate(company) -> dict | None:
    """지속가능성장률(SGR) vs 실제 매출성장률 갭.

    SGR = ROE x (1 - 배당성향/100)
    gap = 실제 매출성장률 - SGR
    - gap > 0: 외부 자본 필요 (성장이 내부 역량 초과)
    - gap < 0: 여유 (자사주/배당 확대 여력)
    """
    isResult = company.select("IS", ["매출액", "당기순이익"])
    bsResult = company.select("BS", ["자본총계"])

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    rev = isData.get("매출액", {})
    ni = isData.get("당기순이익", {})
    eq = bsData.get("자본총계", {})

    # 배당성향은 ratioSeries에서 (배당은 IS/BS로 직접 구하기 어려움)
    result = getRatioSeries(company)
    payoutData = {}
    if result:
        data, years = result
        payoutVals = data.get("RATIO", {}).get("dividendPayoutRatio", [])
        for i, y in enumerate(years):
            if i < len(payoutVals):
                payoutData[y] = payoutVals[i]

    yCols = _annualCols(isPeriods, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        niVal = ni.get(col)
        eqVal = eq.get(col)
        revVal = rev.get(col)
        revPrev = rev.get(prevCol) if prevCol else None

        roe = round(niVal / eqVal * 100, 2) if niVal is not None and eqVal and eqVal != 0 else None
        actualGrowth = _yoy(revVal, revPrev)
        payoutRatio = payoutData.get(col)

        sgr = None
        retentionRatio = None
        if roe is not None:
            if payoutRatio is not None and payoutRatio >= 0:
                retentionRatio = round(1 - payoutRatio / 100, 4)
            else:
                retentionRatio = 1.0
            sgr = round(roe * retentionRatio, 2)

        gap = round(actualGrowth - sgr, 2) if sgr is not None and actualGrowth is not None else None

        history.append(
            {
                "period": col,
                "revenue": revVal,
                "netIncome": niVal,
                "equity": eqVal,
                "roe": roe,
                "payoutRatio": payoutRatio,
                "sgr": sgr,
                "actualGrowth": actualGrowth,
                "gap": gap,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


def calcGrowthFlags(company) -> list[str]:
    """성장성 경고/기회 플래그."""
    flags: list[str] = []

    trend = calcGrowthTrend(company)
    if trend is None:
        return flags

    hist = trend["history"]

    # 매출 3기 연속 역성장
    if len(hist) >= 3:
        revYoys = [h.get("revenueYoy") for h in hist[:3]]
        if all(v is not None and v < 0 for v in revYoys):
            flags.append(f"매출 3기 연속 역성장 (최근 {revYoys[0]:.1f}%)")

    # 매출 고성장
    if hist and hist[0].get("revenueYoy") is not None and hist[0]["revenueYoy"] > 20:
        flags.append(f"매출 고성장 ({hist[0]['revenueYoy']:.1f}%)")

    # 매출 성장 > 이익 감소 괴리
    if hist:
        h = hist[0]
        ry = h.get("revenueYoy")
        oy = h.get("operatingIncomeYoy")
        if ry is not None and oy is not None and ry > 10 and oy < 0:
            flags.append(f"매출 성장({ry:.0f}%)에도 이익 감소({oy:.0f}%) -- 수익성 희석")

    return flags
