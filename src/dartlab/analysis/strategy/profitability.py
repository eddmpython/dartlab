"""2-1 수익성 분석 -- 마진, ROE/ROA, 듀퐁 분해."""

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


def calcMarginTrend(company) -> dict | None:
    """매출총이익률, 영업이익률, 순이익률 시계열."""
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    gross = _buildTimeline(data, "grossMargin", years)
    operating = _buildTimeline(data, "operatingMargin", years)
    net = _buildTimeline(data, "netMargin", years)

    if not any([gross, operating, net]):
        return None

    return {
        "grossMargin": gross,
        "operatingMargin": operating,
        "netMargin": net,
        "years": years[-_MAX_YEARS:],
    }


def calcReturnTrend(company) -> dict | None:
    """ROE, ROA 시계열 + 레버리지(ROE/ROA)."""
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    roe = _buildTimeline(data, "roe", years)
    roa = _buildTimeline(data, "roa", years)

    if not roe and not roa:
        return None

    # 레버리지 = ROE / ROA
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
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    margin = _buildTimeline(data, "dupontMargin", years)
    turnover = _buildTimeline(data, "dupontTurnover", years)
    leverage = _buildTimeline(data, "dupontLeverage", years)

    if not margin and not turnover and not leverage:
        return None

    return {"margin": margin, "turnover": turnover, "leverage": leverage}


def calcProfitabilityFlags(company) -> list[str]:
    """수익성 경고/기회 플래그."""
    flags: list[str] = []
    result = _getRatioSeries(company)
    if result is None:
        return flags

    data, years = result

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
        if latestRoe is not None and latestRoe > 15 and latestRoa is not None and latestRoa > 5:
            if lev < 2:
                flags.append(f"진성 고수익 (ROE {latestRoe:.1f}%, 낮은 레버리지)")

    return flags
