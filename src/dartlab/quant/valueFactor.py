"""가치 팩터 — 장부가 기반 가치 신호.

학술 근거: Fama & French (1992), Lakonishok et al. (1994) — Contrarian Investment.
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant._helpers import fetch_ohlcv, load_scan_parquet, ohlcv_to_arrays, resolve_market

log = logging.getLogger(__name__)


def _parse(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _ext(df, sj, pat):
    rows = df.filter((pl.col("sj_div") == sj) & pl.col("account_nm").str.contains(pat))
    return _parse(rows.get_column("thstrm_amount").to_list()[0]) if len(rows) > 0 else None


def analyze_value(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """가치 신호 분석."""
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
    yr = cfs.get_column("bsns_year").sort(descending=True).to_list()[0]
    lat = cfs.filter(pl.col("bsns_year") == yr)

    equity = _ext(lat, "BS", "자본총계")
    ni = _ext(lat, "IS", "당기순이익")
    assets = _ext(lat, "BS", "자산총계")

    if equity is None or assets is None:
        return {**result, "error": "BS 데이터 불충분"}

    result["year"] = yr
    comp = {}
    if equity > 0 and ni is not None:
        comp["earningsYield"] = round(ni / equity * 100, 2)
    if assets > 0:
        comp["bookValueRatio"] = round(equity / assets * 100, 2)

    ohlcv = fetch_ohlcv(stockCode)
    if ohlcv is not None and not ohlcv.is_empty():
        arr = ohlcv_to_arrays(ohlcv)
        if "close" in arr and len(arr["close"]) > 0:
            comp["latestPrice"] = round(float(arr["close"][-1]), 2)

    result["components"] = comp
    score = 0.0
    n = 0
    if "earningsYield" in comp:
        score += min(max(comp["earningsYield"] / 10, -3), 3)
        n += 1
    if "bookValueRatio" in comp:
        score += min(max((comp["bookValueRatio"] - 30) / 20, -3), 3)
        n += 1
    result["valueScore"] = round(score / max(n, 1), 4)

    s = result["valueScore"]
    result["valueGrade"] = "deep_value" if s >= 1.5 else "value" if s >= 0.5 else "neutral" if s >= -0.5 else "growth"
    return result
