"""2-1 수익성 분석 -- 마진, ROE/ROA, 듀퐁 분해."""

from __future__ import annotations

from dartlab.analysis.strategy._helpers import (
    MAX_RATIO_YEARS,
    buildTimeline,
    getRatioSeries,
)


def calcMarginTrend(company) -> dict | None:
    """매출총이익률, 영업이익률, 순이익률 시계열."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    gross = buildTimeline(data, "grossMargin", years)
    operating = buildTimeline(data, "operatingMargin", years)
    net = buildTimeline(data, "netMargin", years)

    if not any([gross, operating, net]):
        return None

    return {
        "grossMargin": gross,
        "operatingMargin": operating,
        "netMargin": net,
        "years": years[-MAX_RATIO_YEARS:],
    }


def calcReturnTrend(company) -> dict | None:
    """ROE, ROA 시계열 + 레버리지(ROE/ROA)."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    roe = buildTimeline(data, "roe", years)
    roa = buildTimeline(data, "roa", years)

    if not roe and not roa:
        return None

    leverage = []
    for r, a in zip(roe, roa):
        rv = r.get("value")
        av = a.get("value")
        if rv is not None and av is not None and av != 0:
            leverage.append({"period": r["period"], "value": round(rv / av, 2)})
        else:
            leverage.append({"period": r["period"], "value": None})

    return {"roe": roe, "roa": roa, "leverage": leverage}


def calcDupont(company) -> dict | None:
    """듀퐁 3요소 분해 시계열: 순이익률 x 자산회전율 x 재무레버리지."""
    result = getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    margin = buildTimeline(data, "dupontMargin", years)
    turnover = buildTimeline(data, "dupontTurnover", years)
    leverage = buildTimeline(data, "dupontLeverage", years)

    if not margin and not turnover and not leverage:
        return None

    return {"margin": margin, "turnover": turnover, "leverage": leverage}


def calcProfitabilityFlags(company) -> list[str]:
    """수익성 경고/기회 플래그."""
    flags: list[str] = []
    result = getRatioSeries(company)
    if result is None:
        return flags

    data, _years = result

    # 영업이익률 추세
    om = data.get("RATIO", {}).get("operatingMargin", [])
    recent = [v for v in om[-3:] if v is not None]
    if len(recent) >= 3 and all(recent[i] > recent[i + 1] for i in range(len(recent) - 1)):
        flags.append(f"영업이익률 3기 연속 하락 ({recent[-1]:.1f}%)")
    if recent and recent[-1] is not None and recent[-1] < 0:
        flags.append(f"영업적자 ({recent[-1]:.1f}%)")

    # ROE 레버리지 과다
    roe = data.get("RATIO", {}).get("roe", [])
    roa = data.get("RATIO", {}).get("roa", [])
    if roe and roa:
        latestRoe = next((v for v in reversed(roe) if v is not None), None)
        latestRoa = next((v for v in reversed(roa) if v is not None), None)
        if latestRoe is not None and latestRoa is not None and latestRoa > 0:
            lev = latestRoe / latestRoa
            if lev > 3:
                flags.append(f"ROE의 레버리지 의존도 높음 (ROE/ROA = {lev:.1f}배)")
            if latestRoe > 15 and latestRoa > 5 and lev < 2:
                flags.append(f"진성 고수익 (ROE {latestRoe:.1f}%, 낮은 레버리지)")

    return flags
