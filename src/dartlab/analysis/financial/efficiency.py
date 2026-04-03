"""2-4 효율성 분석 -- 자산을 얼마나 빨리 돌리는가.

select()로 IS/BS 원본 계정을 가져와서
회전율 + CCC를 금액과 함께 보여준다.
재고가 쌓이는지, 매출채권 회수가 느려지는지를 금액으로 파악.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    MAX_RATIO_YEARS,
    getFlowValue,
    isQuarterlyFallback,
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


def _turnover(revenue, balance) -> float | None:
    if revenue is None or balance is None or balance == 0:
        return None
    return round(revenue / balance, 2)


def _days(revenue, balance) -> float | None:
    if revenue is None or balance is None or revenue == 0:
        return None
    return round(balance / revenue * 365, 1)


# ── 자산 회전 ──


@memoized_calc
def calcTurnoverTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """자산 회전 시계열 -- 자산을 얼마나 효율적으로 쓰는가.

    IS(매출) + BS(자산/채권/재고)에서 원본 금액과 회전율을 동시에 본다.
    """
    isResult = company.select("IS", ["매출액", "매출원가"])
    bsResult = company.select(
        "BS",
        ["자산총계", "매출채권", "매출채권및기타채권", "재고자산", "매입채무", "매입채무및기타채무"],
    )

    isParsed = toDict(isResult)
    bsParsed = toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    rev = isData.get("매출액", {})
    cogs = isData.get("매출원가", {})
    ta = bsData.get("자산총계", {})
    ar = bsData.get("매출채권", {}) or bsData.get("매출채권및기타채권", {})
    inv = bsData.get("재고자산", {})
    ap = bsData.get("매입채무", {}) or bsData.get("매입채무및기타채무", {})

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    _qMode = isQuarterlyFallback(yCols)
    _allP = set(isPeriods)

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        r = getFlowValue(rev, col, _qMode, _allP)
        c = getFlowValue(cogs, col, _qMode, _allP)

        arVal = ar.get(col)
        invVal = inv.get(col)
        apVal = ap.get(col)
        taVal = ta.get(col)

        # 회전율
        totalAssetTurnover = _turnover(r, taVal)
        receivablesTurnover = _turnover(r, arVal)
        inventoryTurnover = _turnover(c, invVal)  # COGS 기준

        # CCC 구성 (일수)
        dso = _days(r, arVal)
        dio = _days(c, invVal)
        dpo = _days(c, apVal)
        ccc = round(dso + dio - dpo, 1) if dso is not None and dio is not None and dpo is not None else None

        history.append(
            {
                "period": col,
                "revenue": r,
                "totalAssets": taVal,
                "receivables": arVal,
                "receivablesYoy": _yoy(arVal, ar.get(prevCol)) if prevCol else None,
                "inventory": invVal,
                "inventoryYoy": _yoy(invVal, inv.get(prevCol)) if prevCol else None,
                "payables": apVal,
                "totalAssetTurnover": totalAssetTurnover,
                "receivablesTurnover": receivablesTurnover,
                "inventoryTurnover": inventoryTurnover,
                "dso": dso,
                "dio": dio,
                "dpo": dpo,
                "ccc": ccc,
            }
        )

    return {"history": history} if history else None


# calcCccTrend는 calcTurnoverTrend에 통합
calcCccTrend = calcTurnoverTrend


# ── 플래그 ──


@memoized_calc
def calcEfficiencyFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """효율성 경고/기회 플래그."""
    flags: list[str] = []

    trend = calcTurnoverTrend(company, basePeriod=basePeriod)
    if trend is None or len(trend["history"]) < 2:
        return flags

    hist = trend["history"]

    # 총자산회전율 3기 연속 하락
    if len(hist) >= 3:
        tats = [h.get("totalAssetTurnover") for h in hist[:3]]
        if all(v is not None for v in tats) and tats[0] < tats[1] < tats[2]:
            flags.append(f"총자산회전율 3기 연속 하락 ({tats[0]:.2f}회)")

    # 재고 급증 (매출 대비)
    h0, h1 = hist[0], hist[1]
    invYoy = h0.get("inventoryYoy")
    revYoy = h0.get("revenue")
    revPrev = h1.get("revenue")
    if invYoy is not None and revPrev is not None and revPrev > 0:
        revGrowth = _yoy(revYoy, revPrev)
        # 여기서는 이미 계산된 inventoryYoy 사용
        if invYoy is not None and invYoy > 20:
            flags.append(f"재고자산 +{invYoy:.0f}% 급증")

    # CCC
    if len(hist) >= 2:
        ccc0 = hist[0].get("ccc")
        ccc1 = hist[1].get("ccc")
        if ccc0 is not None and ccc1 is not None:
            diff = ccc0 - ccc1
            if diff > 20:
                flags.append(f"CCC {diff:.0f}일 악화 ({ccc0:.0f}일)")
            if ccc0 < 0:
                flags.append(f"CCC {ccc0:.0f}일 -- 운전자본 유리 구조")

    return flags
