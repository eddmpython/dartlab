"""macro 전용 ChartSpec 생성기 — viz 엔진 VizSpec 프로토콜."""

from __future__ import annotations


def spec_fci_timeline(liquidity: dict) -> dict | None:
    """FCI 시계열."""
    ts = liquidity.get("timeseries") or {}
    hy_ts = ts.get("hy_spread")
    if not hy_ts:
        return None
    return {
        "chartType": "line",
        "title": "금융환경지수 (HY 스프레드)",
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
    """침체확률 지표."""
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


def spec_cycle_indicators(timeseries: dict) -> dict | None:
    """사이클 핵심 지표 시계열 (HY/VIX/장단기차)."""
    series = []
    categories = None
    for label, key in [("HY 스프레드", "hy_spread"), ("VIX", "vix"), ("장단기차", "term_spread")]:
        ts = timeseries.get(key)
        if ts:
            series.append({"name": label, "data": [p["value"] for p in ts if p.get("value")], "type": "line"})
            if categories is None:
                categories = [p["date"] for p in ts if p.get("value")]
    if not series:
        return None
    return {
        "chartType": "line",
        "title": "사이클 지표 추이",
        "series": series,
        "categories": categories or [],
        "options": {"unit": ""},
    }


def spec_fear_greed_components(fearGreed: dict) -> dict | None:
    """공포탐욕 4요소 분해."""
    comps = fearGreed.get("components") or {}
    if not comps:
        return None
    return {
        "chartType": "bar",
        "title": "공포탐욕 구성요소",
        "series": [{"name": k, "data": [round(v, 1)], "type": "bar"} for k, v in comps.items()],
        "categories": ["현재"],
        "options": {"unit": "점"},
    }


def spec_trade_tot(trade: dict) -> dict | None:
    """교역조건 추이 (KR)."""
    ts = trade.get("timeseries") or {}
    exp_ts = ts.get("export_price")
    imp_ts = ts.get("import_price")
    if not exp_ts or not imp_ts:
        return None
    return {
        "chartType": "line",
        "title": "수출/수입 물가지수",
        "series": [
            {"name": "수출물가", "data": [p["value"] for p in exp_ts if p.get("value")], "type": "line"},
            {"name": "수입물가", "data": [p["value"] for p in imp_ts if p.get("value")], "type": "line"},
        ],
        "categories": [p["date"] for p in exp_ts if p.get("value")],
        "options": {"unit": "지수"},
    }


def spec_corporate_table(corporate: dict) -> list[dict] | None:
    """기업집계 연도별 테이블 데이터."""
    ec = corporate.get("earningsCycle")
    pr = corporate.get("ponziRatio")
    lc = corporate.get("leverageCycle")
    if not ec or not ec.get("periods"):
        return None
    rows = []
    for i, period in enumerate(ec["periods"]):
        row = {"연도": period}
        if ec.get("totalOperatingIncome"):
            row["영업이익(억)"] = f"{ec['totalOperatingIncome'][i]:,.0f}" if i < len(ec["totalOperatingIncome"]) else "—"
        if ec.get("yoyChanges"):
            yoy = ec["yoyChanges"][i] if i < len(ec["yoyChanges"]) else None
            row["YoY"] = f"{yoy:+.1f}%" if yoy else "—"
        if pr and pr.get("ratios") and i < len(pr["ratios"]):
            row["Ponzi"] = f"{pr['ratios'][i]:.1%}"
        if lc and lc.get("medianDebtRatio") and i < len(lc["medianDebtRatio"]):
            row["부채비율"] = f"{lc['medianDebtRatio'][i]:.1f}%"
        rows.append(row)
    return rows
