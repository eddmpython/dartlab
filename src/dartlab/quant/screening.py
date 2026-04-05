"""팩터 스크리닝 프리셋.

학술 근거: Novy-Marx (2013), Piotroski (2000) F-Score.
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant._helpers import load_scan_parquet

log = logging.getLogger(__name__)

_PRESETS = {
    "quality": {"desc": "고품질: ROA > 5%, 부채비율 < 60%", "roa_min": 5, "debt_max": 60},
    "value": {"desc": "가치주: 부채비율 < 40%, 영업마진 > 10%", "debt_max": 40, "margin_min": 10},
    "growth": {"desc": "성장주: 매출 YoY 성장 > 10%", "growth_min": 10},
    "dividend": {"desc": "배당주: DPS > 0 (배당 지급 종목)"},
    "momentum": {"desc": "모멘텀: 가격 데이터 필요 — dartlab.quant('모멘텀', code) 사용", "price_only": True},
    "lowvol": {"desc": "저변동: 가격 데이터 필요 — dartlab.quant('변동성', code) 사용", "price_only": True},
}


def _parse(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def analyze_screen(*, market: str = "KR", preset: str = "quality", stockCode: str | None = None, **kwargs) -> dict:
    """팩터 스크리닝."""
    if preset not in _PRESETS:
        return {"error": f"알 수 없는 프리셋: {preset}", "available": list(_PRESETS.keys())}

    cfg = _PRESETS[preset]
    result: dict = {"market": market, "preset": preset, "criteria": cfg["desc"]}

    if cfg.get("price_only"):
        return {**result, "info": cfg["desc"]}

    if preset == "dividend":
        return _screen_dividend(result, market, stockCode)

    lf = load_scan_parquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}

    try:
        df = lf.filter(pl.col("fs_nm").str.contains("연결")).collect()
        if df.is_empty():
            df = lf.collect()
    except Exception as e:
        return {**result, "error": str(e)}

    yr = df.get_column("bsns_year").sort(descending=True).to_list()[0]
    df = df.filter(pl.col("bsns_year") == yr)

    # 종목별 지표
    stocks: dict[str, dict] = {}
    for row in df.iter_rows(named=True):
        code = row.get("stockCode")
        if not code:
            continue
        if code not in stocks:
            stocks[code] = {"name": row.get("corp_name", "")}
        sj = row.get("sj_div", "")
        nm = str(row.get("account_nm", ""))
        amt = _parse(row.get("thstrm_amount"))
        prev = _parse(row.get("frmtrm_amount"))
        s = stocks[code]
        if sj == "IS" and nm == "매출액":
            s["sales"] = amt
            s["prev_sales"] = prev
        if sj == "IS" and nm == "영업이익":
            s["op"] = amt
        if sj == "IS" and "당기순이익" in nm:
            s["ni"] = amt
        if sj == "BS" and nm == "자산총계":
            s["assets"] = amt
        if sj == "BS" and nm == "부채총계":
            s["debt"] = amt

    passed = []
    for code, s in stocks.items():
        sales = s.get("sales")
        op = s.get("op")
        ni = s.get("ni")
        assets = s.get("assets")
        debt = s.get("debt")

        margin = (op / sales * 100) if sales and sales > 0 and op else None
        roa = (ni / assets * 100) if assets and assets > 0 and ni else None
        dr = (debt / assets * 100) if assets and assets > 0 and debt else None

        if preset == "quality":
            if roa is not None and roa > cfg["roa_min"] and dr is not None and dr < cfg["debt_max"]:
                passed.append({"stockCode": code, "name": s.get("name", ""), "ROA": round(roa, 2), "debtRatio": round(dr, 2)})
        elif preset == "value":
            if dr is not None and dr < cfg["debt_max"] and margin is not None and margin > cfg["margin_min"]:
                passed.append({"stockCode": code, "name": s.get("name", ""), "opMargin": round(margin, 2), "debtRatio": round(dr, 2)})
        elif preset == "growth":
            prev_sales = s.get("prev_sales")
            if sales and prev_sales and prev_sales > 0:
                growth = (sales - prev_sales) / abs(prev_sales) * 100
                if growth > cfg["growth_min"]:
                    passed.append({"stockCode": code, "name": s.get("name", ""), "salesGrowth": round(growth, 2)})

    # 정렬
    sort_key = {"quality": "ROA", "value": "opMargin", "growth": "salesGrowth"}.get(preset, "ROA")
    passed.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    if stockCode:
        target = [s for s in passed if s["stockCode"] == stockCode]
        result["targetPassed"] = len(target) > 0
        if target:
            result["target"] = target[0]

    result["stocks"] = passed[:30]
    result["count"] = len(passed)
    result["year"] = yr
    return result


def _screen_dividend(result: dict, market: str, stockCode: str | None) -> dict:
    lf = load_scan_parquet("dividend", market)
    if lf is None:
        return {**result, "error": "dividend.parquet 없음"}
    try:
        df = lf.collect()
    except Exception as e:
        return {**result, "error": str(e)}

    # DPS > 0인 종목 찾기
    code_col = next((c for c in ["stockCode", "종목코드"] if c in df.columns), None)
    if code_col is None:
        return {**result, "error": "종목코드 컬럼 없음"}

    # thstrm 또는 DPS 관련 컬럼 탐색
    dps_col = next((c for c in df.columns if "주당" in c or "DPS" in c or "thstrm" == c), None)
    if dps_col:
        stocks_with_div = df.filter(pl.col(dps_col).is_not_null()).select(code_col).unique().to_series().to_list()
        result["count"] = len(stocks_with_div)
        result["stocks"] = [{"stockCode": s} for s in stocks_with_div[:30]]
    else:
        result["count"] = 0
        result["stocks"] = []

    return result
