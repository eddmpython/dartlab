"""꼬리위험 분석 — CVaR, 최대낙폭, Sortino, 하방편차.

학술 근거:
- Artzner et al. (1999): Coherent risk measures (CVaR/Expected Shortfall)
- Sortino & van der Meer (1991): Sortino ratio
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_tailrisk(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """꼬리위험 종합 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict with cvar95, maxDrawdown, sortino, downsideDev 등.
    """
    market = resolve_market(stockCode, market)
    ohlcv = fetch_ohlcv(stockCode, **kwargs)
    if ohlcv is None or ohlcv.is_empty():
        return {"error": f"{stockCode} 주가 데이터 없음"}

    arr = ohlcv_to_arrays(ohlcv)
    if "close" not in arr or len(arr["close"]) < 30:
        return {"error": f"{stockCode} 데이터 부족 (최소 30일 필요)"}

    close = arr["close"]
    n = len(close)
    daily_returns = np.diff(np.log(close))

    result: dict = {
        "stockCode": stockCode,
        "market": market,
        "dataPoints": n,
    }

    # ── VaR & CVaR (역사적 시뮬레이션) ──
    for confidence, label in [(0.95, "95"), (0.99, "99")]:
        var_pct = float(np.percentile(daily_returns, (1 - confidence) * 100))
        # CVaR = VaR 이하 평균 (Expected Shortfall)
        tail = daily_returns[daily_returns <= var_pct]
        cvar = float(np.mean(tail)) if len(tail) > 0 else var_pct

        result[f"var{label}"] = round(var_pct, 6)
        result[f"cvar{label}"] = round(cvar, 6)
        # 연환산
        result[f"var{label}_annual"] = round(var_pct * np.sqrt(252), 4)
        result[f"cvar{label}_annual"] = round(cvar * np.sqrt(252), 4)

    # ── 최대낙폭 (Maximum Drawdown) ──
    cumulative = np.cumprod(1 + np.diff(close) / close[:-1])
    cumulative = np.insert(cumulative, 0, 1.0)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_dd = float(np.min(drawdowns))
    max_dd_idx = int(np.argmin(drawdowns))

    result["maxDrawdown"] = round(max_dd, 4)
    if "date" in arr and max_dd_idx < len(arr["date"]):
        result["maxDrawdownDate"] = str(arr["date"][max_dd_idx])

    # 현재 낙폭
    current_dd = float(drawdowns[-1])
    result["currentDrawdown"] = round(current_dd, 4)

    # ── 하방편차 (Downside Deviation) ──
    # MAR = 0 (무위험수익률 0 가정)
    negative_returns = daily_returns[daily_returns < 0]
    downside_dev = float(np.sqrt(np.mean(negative_returns ** 2))) if len(negative_returns) > 0 else 0
    result["downsideDev"] = round(downside_dev * np.sqrt(252), 4)

    # ── Sortino Ratio ──
    # (연간수익률 - 0) / 하방편차
    annual_return = float(np.mean(daily_returns) * 252)
    if downside_dev > 0:
        sortino = annual_return / (downside_dev * np.sqrt(252))
    else:
        sortino = 0.0
    result["sortino"] = round(float(sortino), 4)
    result["annualReturn"] = round(annual_return, 4)

    # ── Calmar Ratio ──
    # 연간수익률 / |최대낙폭|
    if abs(max_dd) > 0:
        calmar = annual_return / abs(max_dd)
    else:
        calmar = 0.0
    result["calmar"] = round(float(calmar), 4)

    # ── 변동성 (연환산) ──
    vol = float(np.std(daily_returns) * np.sqrt(252))
    result["volatility"] = round(vol, 4)

    # ── Sharpe Ratio (무위험수익률 0 가정) ──
    if vol > 0:
        sharpe = annual_return / vol
    else:
        sharpe = 0.0
    result["sharpe"] = round(float(sharpe), 4)

    # ── 왜도/첨도 ──
    if len(daily_returns) >= 30:
        skewness = float(_skewness(daily_returns))
        kurtosis = float(_kurtosis(daily_returns))
        result["skewness"] = round(skewness, 4)
        result["kurtosis"] = round(kurtosis, 4)
        # 음의 왜도 + 높은 첨도 = 꼬리위험 높음
        if skewness < -0.5 and kurtosis > 4:
            result["tailRiskGrade"] = "high"
        elif skewness < 0 and kurtosis > 3:
            result["tailRiskGrade"] = "medium"
        else:
            result["tailRiskGrade"] = "low"

    # ── 극단 손실 빈도 ──
    # 일일 수익률 -3% 이하 빈도
    extreme_losses = np.sum(daily_returns < -0.03)
    result["extremeLossDays"] = int(extreme_losses)
    result["extremeLossFreq"] = round(float(extreme_losses / len(daily_returns)), 4)

    return result


def _skewness(x: np.ndarray) -> float:
    """3차 중심적률 / 표준편차³."""
    n = len(x)
    if n < 3:
        return 0.0
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s == 0:
        return 0.0
    return float((n / ((n - 1) * (n - 2))) * np.sum(((x - m) / s) ** 3))


def _kurtosis(x: np.ndarray) -> float:
    """4차 중심적률 / 표준편차⁴ (excess kurtosis)."""
    n = len(x)
    if n < 4:
        return 0.0
    m = np.mean(x)
    s = np.std(x, ddof=1)
    if s == 0:
        return 0.0
    k = float(np.mean(((x - m) / s) ** 4))
    # excess kurtosis (정규분포 = 0)
    return k - 3.0
