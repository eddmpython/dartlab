"""2-2 성장성 분석 -- 성장률 추이, 성장 품질."""

from __future__ import annotations

from dartlab.analysis.strategy._helpers import (
    MAX_RATIO_YEARS,
    buildTimeline,
    getRatioSeries,
)


def _cagr(values: list[float | None], periods: int) -> float | None:
    """CAGR 계산."""
    valid = [v for v in values if v is not None and v > 0]
    if len(valid) < 2 or periods < 1:
        return None
    first, last = valid[0], valid[-1]
    if first <= 0:
        return None
    return (pow(last / first, 1 / periods) - 1) * 100


def calcGrowthTrend(company) -> dict | None:
    """매출/영업이익/순이익/자산 YoY 성장률 시계열."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    revenue = buildTimeline(data, "revenueGrowth", years)
    opProfit = buildTimeline(data, "operatingProfitGrowth", years)
    netProfit = buildTimeline(data, "netProfitGrowth", years)
    asset = buildTimeline(data, "assetGrowth", years)

    if not any([revenue, opProfit, netProfit]):
        return None

    return {
        "revenueGrowth": revenue,
        "operatingProfitGrowth": opProfit,
        "netProfitGrowth": netProfit,
        "assetGrowth": asset,
    }


def calcGrowthQuality(company) -> dict | None:
    """성장 품질 -- 외형 vs 내실, CAGR."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    revVals = data.get("RATIO", {}).get("revenue", [])
    opVals = data.get("RATIO", {}).get("operatingProfit", [])
    npVals = data.get("RATIO", {}).get("netProfit", [])

    n = min(len(revVals), len(years))
    if n < 2:
        return None

    revCagr = _cagr(revVals[-MAX_RATIO_YEARS:], min(n - 1, MAX_RATIO_YEARS - 1))
    opCagr = _cagr(opVals[-MAX_RATIO_YEARS:], min(n - 1, MAX_RATIO_YEARS - 1))
    npCagr = _cagr(npVals[-MAX_RATIO_YEARS:], min(n - 1, MAX_RATIO_YEARS - 1))

    # 외형 vs 내실 판별
    quality = "균형"
    if revCagr is not None and opCagr is not None:
        if revCagr > 0 and opCagr < revCagr * 0.5:
            quality = "외형 위주"
        elif opCagr > revCagr * 1.5:
            quality = "내실 위주"

    return {
        "revenueCagr": revCagr,
        "operatingProfitCagr": opCagr,
        "netProfitCagr": npCagr,
        "quality": quality,
        "periods": min(n - 1, MAX_RATIO_YEARS - 1),
    }


def calcGrowthFlags(company) -> list[str]:
    """성장성 경고/기회 플래그."""
    flags: list[str] = []
    result = getRatioSeries(company)
    if result is None:
        return flags

    data, _years = result
    revG = data.get("RATIO", {}).get("revenueGrowth", [])
    opG = data.get("RATIO", {}).get("operatingProfitGrowth", [])

    recent = [v for v in revG[-3:] if v is not None]
    if len(recent) >= 3 and all(v < 0 for v in recent):
        flags.append(f"매출 3기 연속 역성장 (최근 {recent[-1]:.1f}%)")

    if recent and recent[-1] is not None and recent[-1] > 20:
        flags.append(f"매출 고성장 ({recent[-1]:.1f}%)")

    # 매출 성장 > 이익 성장 괴리
    recentRev = [v for v in revG[-1:] if v is not None]
    recentOp = [v for v in opG[-1:] if v is not None]
    if recentRev and recentOp:
        rv, ov = recentRev[0], recentOp[0]
        if rv > 10 and ov < 0:
            flags.append(f"매출 성장({rv:.0f}%)에도 이익 감소({ov:.0f}%) -- 수익성 희석")

    return flags
