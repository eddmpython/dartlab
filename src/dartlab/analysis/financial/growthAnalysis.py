"""2-2 성장성 분석 -- 무엇이 얼마나 커졌는가.

select()로 IS/BS/CF 원본 계정을 가져와서
금액 + YoY + CAGR + 이익 vs 매출 성장 괴리를 시계열로 보여준다.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    MAX_RATIO_YEARS,
    toDict,
)
from dartlab.analysis.financial._helpers import (
    annualColsFromPeriods as _annualColsFromPeriods,
)
from dartlab.analysis.financial._memoize import memoized_calc

_MAX_YEARS = MAX_RATIO_YEARS


def _yoy(cur, prev) -> float | None:
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _cagrFromList(values: list[float | None], periods: int) -> float | None:
    valid = [v for v in values if v is not None and v > 0]
    if len(valid) < 2 or periods < 1:
        return None
    first, last = valid[0], valid[-1]
    if first <= 0:
        return None
    return round((pow(last / first, 1 / periods) - 1) * 100, 2)


# ── 성장 추이 ──


@memoized_calc
def calcGrowthTrend(company, *, basePeriod: str | None = None) -> dict | None:
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

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
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
                "revenue": _cagrFromList(revVals, n),
                "operatingIncome": _cagrFromList(opVals, n),
                "netIncome": _cagrFromList(niVals, n),
                "periods": n,
            },
        }
        if history
        else None
    )


# ── 성장 품질 ──


@memoized_calc
def calcGrowthQuality(company, *, basePeriod: str | None = None) -> dict | None:
    """성장 품질 -- 매출 성장이 이익으로 이어지는가.

    매출 vs 영업이익 성장률 괴리를 본다.
    매출만 크고 이익이 안 따라오면 외형 위주.
    """
    trend = calcGrowthTrend(company, basePeriod=basePeriod)
    if trend is None or len(trend["history"]) < 2:
        return None

    cagr = trend["cagr"]
    revCagr = cagr.get("revenue")
    opCagr = cagr.get("operatingIncome")

    niCagr = cagr.get("netIncome")
    hist = trend["history"]

    quality = "판단 불가"
    if revCagr is not None and opCagr is not None:
        if revCagr < 0:
            quality = "역성장"
        elif niCagr is not None and niCagr < -5:
            quality = "이익 역성장"
        elif opCagr < revCagr * 0.5:
            # 최신 기 영업이익 YoY가 양수이면 "개선 중"으로 완화 (턴어라운드 기업 배려)
            latestOpYoy = hist[0].get("operatingIncomeYoy") if hist else None
            if latestOpYoy is not None and latestOpYoy > 10:
                quality = "개선 중"
            else:
                quality = "외형 위주"
        elif opCagr > revCagr * 1.5 and opCagr > 0:
            quality = "내실 위주"
        elif revCagr > 0 and opCagr > 0:
            quality = "균형"

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


@memoized_calc
def calcSustainableGrowthRate(company, *, basePeriod: str | None = None) -> dict | None:
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

    # 배당성향: CF 배당금지급 / 당기순이익
    from dartlab.analysis.financial._helpers import toDictBySnakeId

    cfResult = company.select("CF", ["dividends_paid"])
    cfParsed = toDictBySnakeId(cfResult)
    divRow = cfParsed[0].get("dividends_paid", {}) if cfParsed else {}

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
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
        divPaid = abs(divRow.get(col) or 0)
        payoutRatio = round(divPaid / niVal * 100, 2) if niVal and niVal > 0 and divPaid > 0 else None

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


@memoized_calc
def calcGrowthFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """성장성 경고/기회 플래그."""
    flags: list[str] = []

    trend = calcGrowthTrend(company, basePeriod=basePeriod)
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


# ── 계정별 CAGR 비교 ──


def _cagr(start: float, end: float, years: int) -> float | None:
    """CAGR 계산. 시작/끝이 양수일 때만."""
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return round(((end / start) ** (1 / years) - 1) * 100, 2)


@memoized_calc
def calcCagrComparison(company, *, basePeriod: str | None = None) -> dict | None:
    """계정별 CAGR 비교 — 절대값 장기 추세로 구조적 변화 감지.

    매출 CAGR vs 영업이익 CAGR → 마진 방향
    자산 CAGR vs 매출 CAGR → 자산 효율 방향
    부채 CAGR vs 자본 CAGR → 레버리지 방향

    반환::

        {
            "comparisons": [
                {"label": str, "item1": str, "cagr1": float,
                 "item2": str, "cagr2": float, "gap": float, "signal": str},
                ...
            ],
            "period": str,
        }
    """
    isResult = company.select("IS", ["매출액", "영업이익"])
    bsResult = company.select("BS", ["자산총계", "부채총계", "자본총계"])
    cfResult = company.select("CF", ["유형자산의취득"])

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    cfParsed = toDict(cfResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed
    cfData = cfParsed[0] if cfParsed else {}

    yCols = _annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 3:
        return None

    def _v(row, col):
        v = row.get(col) if row else None
        return v if v is not None else 0

    latest = yCols[0]
    oldest = yCols[-1]
    years = len(yCols) - 1

    revRow = isData.get("매출액", {})
    opRow = isData.get("영업이익", {})
    taRow = bsData.get("자산총계", {})
    tlRow = bsData.get("부채총계", {})
    teRow = bsData.get("자본총계", {})
    capexRow = cfData.get("유형자산의취득", {})

    pairs = [
        ("마진 방향", "매출", _v(revRow, oldest), _v(revRow, latest), "영업이익", _v(opRow, oldest), _v(opRow, latest)),
        ("자산 효율", "자산", _v(taRow, oldest), _v(taRow, latest), "매출", _v(revRow, oldest), _v(revRow, latest)),
        ("레버리지", "부채", _v(tlRow, oldest), _v(tlRow, latest), "자본", _v(teRow, oldest), _v(teRow, latest)),
        (
            "투자 방향",
            "CAPEX",
            abs(_v(capexRow, oldest)),
            abs(_v(capexRow, latest)),
            "매출",
            _v(revRow, oldest),
            _v(revRow, latest),
        ),
    ]

    comparisons = []
    for label, name1, start1, end1, name2, start2, end2 in pairs:
        c1 = _cagr(start1, end1, years)
        c2 = _cagr(start2, end2, years)
        if c1 is not None and c2 is not None:
            gap = round(c1 - c2, 2)
            if label == "마진 방향":
                signal = "마진 확대" if gap <= 0 else "마진 압박"
            elif label == "자산 효율":
                signal = "효율 개선" if gap <= 0 else "효율 하락"
            elif label == "레버리지":
                signal = "디레버리징" if gap <= 0 else "레버리지 확대"
            else:
                signal = "투자 확대" if gap > 0 else "투자 축소"
            comparisons.append(
                {
                    "label": label,
                    "item1": name1,
                    "cagr1": c1,
                    "item2": name2,
                    "cagr2": c2,
                    "gap": gap,
                    "signal": signal,
                }
            )

    if not comparisons:
        return None
    return {"comparisons": comparisons, "period": f"{oldest} → {latest}"}
