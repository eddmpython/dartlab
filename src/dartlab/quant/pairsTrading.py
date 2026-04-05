"""공적분 기반 페어 트레이딩 — Engle-Granger 2단계 검정.

학술 근거: Engle & Granger (1987), Gatev et al. (2006).
"""

from __future__ import annotations

import logging

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, load_scan_parquet, ohlcv_to_arrays

log = logging.getLogger(__name__)

# ADF 임계값 (Dickey-Fuller, n→∞)
_ADF_CRITICAL = {"1%": -3.43, "5%": -2.86, "10%": -2.57}


def analyze_pairs(*, market: str = "KR", stockCode: str | None = None, **kwargs) -> dict:
    """공적분 기반 페어 탐색."""
    result: dict = {"market": market}

    # 자산 상위 5종목 선정 (finance.parquet)
    top_codes = _get_top_stocks(market, n=5)
    if not top_codes:
        return {**result, "error": "종목 리스트 확보 실패"}

    if stockCode and stockCode not in top_codes:
        top_codes = [stockCode] + top_codes[:4]

    # OHLCV 수집 (순차, 메모리 안전)
    prices: dict[str, np.ndarray] = {}
    for code in top_codes:
        ohlcv = fetch_ohlcv(code)
        if ohlcv is not None and not ohlcv.is_empty():
            arr = ohlcv_to_arrays(ohlcv)
            if "close" in arr and len(arr["close"]) >= 60:
                prices[code] = np.log(arr["close"])

    codes = list(prices.keys())
    if len(codes) < 2:
        return {**result, "error": f"가격 데이터 부족 ({len(codes)}종목)"}

    # 모든 페어 ADF 검정
    pairs = []
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            a, b = codes[i], codes[j]
            pa, pb = prices[a], prices[b]
            ml = min(len(pa), len(pb))
            if ml < 60:
                continue
            spread = pa[-ml:] - pb[-ml:]

            adf_stat, beta, half_life = _adf_test(spread)
            if adf_stat is None:
                continue

            # 현재 스프레드 z-score
            z = (spread[-1] - np.mean(spread)) / max(np.std(spread), 1e-10)

            coint = "no"
            for level, cv in _ADF_CRITICAL.items():
                if adf_stat < cv:
                    coint = level
                    break

            pairs.append({
                "stockA": a, "stockB": b,
                "adfStat": round(float(adf_stat), 4),
                "cointegrated": coint,
                "halfLife": round(float(half_life), 1) if half_life and half_life > 0 else None,
                "spreadZ": round(float(z), 4),
                "dataPoints": ml,
            })

    pairs.sort(key=lambda x: x["adfStat"])
    result["pairs"] = pairs[:10]
    result["totalPairsTested"] = len(pairs)
    result["cointegratedPairs"] = sum(1 for p in pairs if p["cointegrated"] != "no")
    result["stocksUsed"] = codes
    return result


def _adf_test(spread: np.ndarray) -> tuple[float | None, float, float]:
    """ADF 검정 (numpy OLS).

    ΔX_t = α + β·X_{t-1} + ε
    t_stat = β / SE(β)
    half_life = -ln(2) / ln(1 + β)
    """
    n = len(spread)
    if n < 30:
        return None, 0, 0

    dx = np.diff(spread)
    x_lag = spread[:-1]

    # OLS: dx = α + β·x_lag
    X = np.column_stack([np.ones(n - 1), x_lag])
    try:
        beta = np.linalg.lstsq(X, dx, rcond=None)[0]
    except np.linalg.LinAlgError:
        return None, 0, 0

    b = float(beta[1])
    resid = dx - X @ beta
    mse = float(np.sum(resid ** 2) / (n - 3))
    x_var = float(np.sum((x_lag - np.mean(x_lag)) ** 2))
    if x_var == 0:
        return None, 0, 0

    se = np.sqrt(mse / x_var)
    t_stat = b / se if se > 0 else 0

    hl = -np.log(2) / np.log(1 + b) if b < 0 and b > -1 else 0

    return float(t_stat), b, float(hl)


def _get_top_stocks(market: str, n: int = 5) -> list[str]:
    """finance.parquet에서 자산 상위 N종목."""
    import polars as pl

    lf = load_scan_parquet("finance", market)
    if lf is None:
        return []

    try:
        bs = (
            lf.filter(pl.col("sj_div") == "BS")
            .filter(pl.col("account_nm") == "자산총계")
            .filter(pl.col("fs_nm").str.contains("연결"))
            .collect()
        )
    except Exception:
        return []

    if bs.is_empty():
        return []

    yr = bs.get_column("bsns_year").sort(descending=True).to_list()[0]
    bs = bs.filter(pl.col("bsns_year") == yr)

    # 금액 파싱 + 정렬
    stocks = []
    for row in bs.iter_rows(named=True):
        code = row.get("stockCode")
        val = row.get("thstrm_amount")
        if code and val:
            try:
                amt = float(str(val).replace(",", ""))
                stocks.append((code, amt))
            except (ValueError, TypeError):
                pass

    stocks.sort(key=lambda x: -x[1])
    return [s[0] for s in stocks[:n]]
