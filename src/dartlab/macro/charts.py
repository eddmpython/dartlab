"""macro 전용 ChartSpec 생성기 — viz 엔진 VizSpec 프로토콜."""

from __future__ import annotations


def spec_fci_timeline(liquidity: dict) -> dict | None:
    """FCI 시계열."""
    fci = liquidity.get("fci")
    if not fci:
        return None
    ts = liquidity.get("timeseries") or {}
    hy_ts = ts.get("hy_spread")
    if not hy_ts:
        return None
    return {
        "chartType": "line",
        "title": "금융환경지수 (FCI)",
        "series": [{"name": "HY 스프레드", "data": [p["value"] for p in hy_ts if p.get("value")], "type": "line"}],
        "categories": [p["date"] for p in hy_ts if p.get("value")],
        "options": {"unit": "bps"},
    }


def spec_earnings_cycle(corporate: dict) -> dict | None:
    """전종목 영업이익 YoY."""
    ec = corporate.get("earningsCycle")
    if not ec or not ec.get("periods"):
        return None
    return {
        "chartType": "bar",
        "title": "전종목 영업이익 사이클",
        "series": [{"name": "YoY 변화율", "data": [y if y else 0 for y in ec["yoyChanges"]], "type": "bar"}],
        "categories": ec["periods"],
        "options": {"unit": "%"},
    }


def spec_ponzi_ratio(corporate: dict) -> dict | None:
    """ICR<1 비중 추이."""
    pr = corporate.get("ponziRatio")
    if not pr or not pr.get("periods"):
        return None
    return {
        "chartType": "line",
        "title": "Ponzi 비율 (ICR<1 기업 비중)",
        "series": [{"name": "Ponzi 비율", "data": [round(r * 100, 1) for r in pr["ratios"]], "type": "line"}],
        "categories": pr["periods"],
        "options": {"unit": "%"},
    }


def spec_recession_prob(forecast: dict) -> dict | None:
    """침체확률."""
    rp = forecast.get("recessionProb")
    sahm = forecast.get("sahmRule")
    if not rp:
        return None
    metrics = [{"name": "프로빗", "value": round(rp["probability"] * 100, 1)}]
    if sahm:
        metrics.append({"name": "Sahm Rule", "value": sahm["value"]})
    return {
        "chartType": "bar",
        "title": "침체 확률 지표",
        "series": [{"name": m["name"], "data": [m["value"]], "type": "bar"} for m in metrics],
        "categories": ["현재"],
        "options": {"unit": "%"},
    }
