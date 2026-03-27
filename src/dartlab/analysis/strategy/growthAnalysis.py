"""2-2 성장성 분석 -- 성장률 추이, 성장 품질."""

from __future__ import annotations

_MAX_YEARS = 5


def _getRatioSeries(company) -> tuple[dict, list[str]] | None:
    """ratioSeries를 안전하게 가져온다."""
    try:
        result = company.finance.ratioSeries
        if result is None:
            return None
        return result
    except (ValueError, KeyError, AttributeError):
        return None


def _buildTimeline(data: dict, field: str, years: list[str]) -> list[dict]:
    """시계열 데이터를 [{period, value}, ...] 형태로 변환."""
    vals = data.get("RATIO", {}).get(field, [])
    n = min(len(vals), len(years), _MAX_YEARS)
    if n == 0:
        return []
    return [
        {"period": years[i], "value": vals[i]}
        for i in range(len(years) - n, len(years))
    ]


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
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    revenue = _buildTimeline(data, "revenueGrowth", years)
    opProfit = _buildTimeline(data, "operatingProfitGrowth", years)
    netProfit = _buildTimeline(data, "netProfitGrowth", years)
    asset = _buildTimeline(data, "assetGrowth", years)

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
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    revVals = data.get("RATIO", {}).get("revenue", [])
    opVals = data.get("RATIO", {}).get("operatingProfit", [])
    npVals = data.get("RATIO", {}).get("netProfit", [])

    n = min(len(revVals), len(years))
    if n < 2:
        return None

    revCagr = _cagr(revVals[-_MAX_YEARS:], min(n - 1, _MAX_YEARS - 1))
    opCagr = _cagr(opVals[-_MAX_YEARS:], min(n - 1, _MAX_YEARS - 1))
    npCagr = _cagr(npVals[-_MAX_YEARS:], min(n - 1, _MAX_YEARS - 1))

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
        "periods": min(n - 1, _MAX_YEARS - 1),
    }


def calcGrowthFlags(company) -> list[str]:
    """성장성 경고/기회 플래그."""
    flags: list[str] = []
    result = _getRatioSeries(company)
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
