"""퀄리티 팩터 — Asness 복합 (수익성+안전성+성장성).

학술 근거: Asness, Frazzini, Pedersen (2019) — Quality Minus Junk.
데이터: scan 프리빌드 finance.parquet 직접 읽기. 다른 엔진 import 금지.
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant._helpers import load_scan_parquet, resolve_market

log = logging.getLogger(__name__)


def _parse_amount(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _extract(df: pl.DataFrame, sj: str, pattern: str) -> float | None:
    rows = df.filter((pl.col("sj_div") == sj) & pl.col("account_nm").str.contains(pattern))
    if len(rows) == 0:
        return None
    return _parse_amount(rows.get_column("thstrm_amount").to_list()[0])


def analyze_quality(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """Asness 퀄리티 팩터 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict with qualityScore, profitabilityZ, safetyZ, grade.
    """
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    lf = load_scan_parquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}

    try:
        stock = lf.filter(pl.col("stockCode") == stockCode).collect()
    except Exception as e:
        return {**result, "error": str(e)}

    if stock.is_empty():
        return {**result, "error": "재무데이터 없음"}

    cfs = stock.filter(pl.col("fs_nm").str.contains("연결"))
    if cfs.is_empty():
        cfs = stock
    latest_year = cfs.get_column("bsns_year").sort(descending=True).to_list()[0]
    latest = cfs.filter(pl.col("bsns_year") == latest_year)

    sales = _extract(latest, "IS", "^매출액$|^수익\\(매출액\\)$|^매출$")
    op = _extract(latest, "IS", "영업이익")
    ni = _extract(latest, "IS", "당기순이익")
    assets = _extract(latest, "BS", "자산총계")
    debt = _extract(latest, "BS", "부채총계")
    equity = _extract(latest, "BS", "자본총계")

    metrics = {}
    if sales and sales > 0 and op is not None:
        metrics["operatingMargin"] = round(op / sales * 100, 2)
    if assets and assets > 0 and ni is not None:
        metrics["ROA"] = round(ni / assets * 100, 2)
    if equity and equity > 0 and ni is not None:
        metrics["ROE"] = round(ni / equity * 100, 2)
    if assets and assets > 0 and debt is not None:
        metrics["debtRatio"] = round(debt / assets * 100, 2)

    result["year"] = latest_year
    result["metrics"] = metrics

    prof_z = 0.0
    n_prof = 0
    if "operatingMargin" in metrics:
        prof_z += min(max(metrics["operatingMargin"] / 10, -3), 3)
        n_prof += 1
    if "ROA" in metrics:
        prof_z += min(max(metrics["ROA"] / 5, -3), 3)
        n_prof += 1
    if "ROE" in metrics:
        prof_z += min(max(metrics["ROE"] / 10, -3), 3)
        n_prof += 1
    prof_z = prof_z / max(n_prof, 1)

    safety_z = 0.0
    if "debtRatio" in metrics:
        safety_z = min(max((50 - metrics["debtRatio"]) / 20, -3), 3)

    composite = prof_z * 0.6 + safety_z * 0.4
    result["profitabilityZ"] = round(float(prof_z), 4)
    result["safetyZ"] = round(float(safety_z), 4)
    result["qualityScore"] = round(float(composite), 4)

    if composite >= 1.5:
        result["grade"] = "A"
    elif composite >= 0.5:
        result["grade"] = "B"
    elif composite >= -0.5:
        result["grade"] = "C"
    elif composite >= -1.5:
        result["grade"] = "D"
    else:
        result["grade"] = "F"

    return result
