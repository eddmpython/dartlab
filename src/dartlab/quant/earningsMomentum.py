"""이익 모멘텀 — SUE + PEAD.

학술 근거: Ball & Brown (1968), Bernard & Thomas (1989).
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.quant._helpers import load_scan_parquet, resolve_market

log = logging.getLogger(__name__)


def _parse(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def analyze_earnings(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """SUE + PEAD 이익 모멘텀 분석."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    lf = load_scan_parquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}
    try:
        stock = (
            lf.filter(pl.col("stockCode") == stockCode)
            .filter(pl.col("sj_div") == "IS")
            .filter(pl.col("account_nm").str.contains("영업이익"))
            .collect()
        )
    except Exception as e:
        return {**result, "error": str(e)}
    if stock.is_empty():
        return {**result, "error": "영업이익 데이터 없음"}

    cfs = stock.filter(pl.col("fs_nm").str.contains("연결"))
    if cfs.is_empty():
        cfs = stock

    yearly: dict[str, float] = {}
    for row in cfs.iter_rows(named=True):
        y = row.get("bsns_year")
        v = _parse(row.get("thstrm_amount"))
        if y and v is not None:
            if y not in yearly or abs(v) > abs(yearly.get(y, 0)):
                yearly[y] = v

    if len(yearly) < 2:
        return {**result, "error": f"연도 부족 ({len(yearly)}개)"}

    yrs = sorted(yearly.keys())
    vals = [yearly[y] for y in yrs]
    result["years"] = yrs
    result["opIncomeHistory"] = {y: v for y, v in zip(yrs, vals)}

    latest = vals[-1]
    prev = np.array(vals[:-1], dtype=np.float64)
    mu = float(np.mean(prev))
    sd = float(np.std(prev, ddof=1)) if len(prev) > 1 else 0

    sue = float((latest - mu) / sd) if sd > 0 else (3.0 if latest > mu else -3.0 if latest < mu else 0.0)
    result["sue"] = round(sue, 4)
    result["latestOpIncome"] = latest
    result["prevMean"] = round(mu, 0)

    if abs(sue) > 2:
        result["peadSignal"] = "positive_drift" if sue > 0 else "negative_drift"
        result["peadStrength"] = "strong"
    elif abs(sue) > 1:
        result["peadSignal"] = "mild_positive" if sue > 0 else "mild_negative"
        result["peadStrength"] = "moderate"
    else:
        result["peadSignal"] = "none"
        result["peadStrength"] = "weak"

    if len(vals) >= 3:
        diffs = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
        pos = sum(1 for d in diffs if d > 0)
        r = pos / len(diffs)
        result["earningsTrend"] = (
            "consistent_growth" if r == 1 else "mostly_growing" if r >= 0.7
            else "mostly_declining" if r <= 0.3 else "mixed"
        )
    return result
