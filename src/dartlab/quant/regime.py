"""레짐 감지 — Hamilton 2-state HMM + 추세추종 신호.

학술 근거:
- Hamilton (1989): Regime switching model
- Moskowitz, Ooi, Pedersen (2012): Time-series momentum / trend-following
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_regime(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """레짐 감지 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict with regime, probability, trendSignal.
    """
    market = resolve_market(stockCode, market)
    ohlcv = fetch_ohlcv(stockCode, **kwargs)
    if ohlcv is None or ohlcv.is_empty():
        return {"error": f"{stockCode} 주가 데이터 없음"}

    arr = ohlcv_to_arrays(ohlcv)
    close = arr.get("close")
    if close is None or len(close) < 60:
        return {"error": f"{stockCode} 데이터 부족 (최소 60일)"}

    n = len(close)
    log_returns = np.diff(np.log(close))

    result: dict = {
        "stockCode": stockCode,
        "market": market,
        "dataPoints": n,
    }

    # ── Hamilton 2-State HMM (EM 알고리즘) ──
    hmm = _fit_hmm_2state(log_returns)
    if hmm:
        result["regime"] = hmm["currentRegime"]
        result["regimeLabel"] = "강세" if hmm["currentRegime"] == "bull" else "약세"
        result["bullProb"] = round(hmm["bullProb"], 4)
        result["bearProb"] = round(hmm["bearProb"], 4)
        result["regimeDuration"] = hmm["duration"]
        result["hmmParams"] = {
            "bullMean": round(hmm["mu_bull"] * 252, 4),
            "bearMean": round(hmm["mu_bear"] * 252, 4),
            "bullVol": round(hmm["sigma_bull"] * np.sqrt(252), 4),
            "bearVol": round(hmm["sigma_bear"] * np.sqrt(252), 4),
            "transitionProb": {
                "bullToBear": round(hmm["p_bull_to_bear"], 4),
                "bearToBull": round(hmm["p_bear_to_bull"], 4),
            },
        }

    # ── 추세추종 신호 (EWMA crossover) ──
    # 단기(8일) vs 장기(32일) EWMA
    for fast, slow, label in [(8, 32, "short"), (21, 63, "medium"), (50, 200, "long")]:
        if n > slow:
            ema_fast = _ewma(close, fast)
            ema_slow = _ewma(close, slow)
            signal = "long" if ema_fast[-1] > ema_slow[-1] else "short"
            strength = abs(ema_fast[-1] - ema_slow[-1]) / ema_slow[-1]
            result[f"trend_{label}"] = {
                "signal": signal,
                "strength": round(float(strength), 4),
            }

    # ── 추세 강도 (ADX 기반) ──
    if "high" in arr and "low" in arr and n >= 14:
        from dartlab.quant.indicators import vadx

        adx = vadx(arr["high"], arr["low"], close)
        valid_adx = adx[~np.isnan(adx)]
        if len(valid_adx) > 0:
            latest_adx = float(valid_adx[-1])
            result["adx"] = round(latest_adx, 2)
            if latest_adx > 40:
                result["trendStrength"] = "very_strong"
            elif latest_adx > 25:
                result["trendStrength"] = "strong"
            elif latest_adx > 20:
                result["trendStrength"] = "moderate"
            else:
                result["trendStrength"] = "weak"

    # ── 종합 판단 ──
    trend_signals = []
    for k in ["trend_short", "trend_medium", "trend_long"]:
        if k in result:
            trend_signals.append(result[k]["signal"])

    long_count = sum(1 for s in trend_signals if s == "long")
    if len(trend_signals) > 0:
        if long_count == len(trend_signals):
            result["trendVerdict"] = "strong_uptrend"
        elif long_count >= len(trend_signals) * 0.67:
            result["trendVerdict"] = "uptrend"
        elif long_count <= len(trend_signals) * 0.33:
            if long_count == 0:
                result["trendVerdict"] = "strong_downtrend"
            else:
                result["trendVerdict"] = "downtrend"
        else:
            result["trendVerdict"] = "mixed"

    return result


def _ewma(data: np.ndarray, span: int) -> np.ndarray:
    """지수 가중 이동평균."""
    alpha = 2.0 / (span + 1)
    result = np.empty(len(data))
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    return result


def _fit_hmm_2state(returns: np.ndarray, max_iter: int = 100, tol: float = 1e-6) -> dict | None:
    """2-state Gaussian HMM — EM 알고리즘.

    State 0 = bull (높은 수익, 낮은 변동성)
    State 1 = bear (낮은 수익, 높은 변동성)
    """
    n = len(returns)
    if n < 50:
        return None

    # 초기화 — 양/음 수익률로 분류
    mu = np.array([np.mean(returns[returns > 0]) if np.any(returns > 0) else 0.001,
                    np.mean(returns[returns <= 0]) if np.any(returns <= 0) else -0.001])
    sigma = np.array([np.std(returns[returns > 0]) if np.any(returns > 0) else 0.01,
                      np.std(returns[returns <= 0]) if np.any(returns <= 0) else 0.02])

    # 전이 확률 초기화
    A = np.array([[0.95, 0.05], [0.10, 0.90]])
    pi = np.array([0.6, 0.4])

    for _ in range(max_iter):
        # E-step: forward-backward
        B = np.column_stack([
            _gaussian_pdf(returns, mu[0], sigma[0]),
            _gaussian_pdf(returns, mu[1], sigma[1]),
        ])
        B = np.clip(B, 1e-300, None)

        alpha, scale = _forward(B, A, pi)
        beta = _backward(B, A, scale)
        gamma = alpha * beta
        gamma_sum = gamma.sum(axis=1, keepdims=True)
        gamma_sum = np.clip(gamma_sum, 1e-300, None)
        gamma = gamma / gamma_sum

        # xi
        xi = np.zeros((n - 1, 2, 2))
        for t in range(n - 1):
            for i in range(2):
                for j in range(2):
                    xi[t, i, j] = alpha[t, i] * A[i, j] * B[t + 1, j] * beta[t + 1, j]
            denom = xi[t].sum()
            if denom > 0:
                xi[t] /= denom

        # M-step
        mu_new = np.array([
            np.sum(gamma[:, k] * returns) / np.sum(gamma[:, k])
            for k in range(2)
        ])
        sigma_new = np.array([
            np.sqrt(np.sum(gamma[:, k] * (returns - mu_new[k]) ** 2) / np.sum(gamma[:, k]))
            for k in range(2)
        ])
        sigma_new = np.clip(sigma_new, 1e-6, None)

        A_new = np.zeros((2, 2))
        for i in range(2):
            for j in range(2):
                A_new[i, j] = np.sum(xi[:, i, j]) / np.sum(gamma[:-1, i])
            row_sum = A_new[i].sum()
            if row_sum > 0:
                A_new[i] /= row_sum

        # 수렴 체크
        if np.max(np.abs(mu - mu_new)) < tol and np.max(np.abs(sigma - sigma_new)) < tol:
            break

        mu, sigma, A = mu_new, sigma_new, A_new

    # bull = 높은 평균 수익률 state
    bull_idx = 0 if mu[0] > mu[1] else 1
    bear_idx = 1 - bull_idx

    # 마지막 관측의 regime
    bull_prob = float(gamma[-1, bull_idx])
    current_regime = "bull" if bull_prob > 0.5 else "bear"

    # 현재 레짐 지속 일수
    duration = 1
    for t in range(n - 2, -1, -1):
        if (gamma[t, bull_idx] > 0.5) == (bull_prob > 0.5):
            duration += 1
        else:
            break

    return {
        "currentRegime": current_regime,
        "bullProb": bull_prob,
        "bearProb": 1 - bull_prob,
        "duration": duration,
        "mu_bull": float(mu[bull_idx]),
        "mu_bear": float(mu[bear_idx]),
        "sigma_bull": float(sigma[bull_idx]),
        "sigma_bear": float(sigma[bear_idx]),
        "p_bull_to_bear": float(A[bull_idx, bear_idx]),
        "p_bear_to_bull": float(A[bear_idx, bull_idx]),
    }


def _gaussian_pdf(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """가우시안 확률밀도."""
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))


def _forward(B, A, pi):
    """forward pass with scaling."""
    n, k = B.shape
    alpha = np.zeros((n, k))
    scale = np.zeros(n)

    alpha[0] = pi * B[0]
    scale[0] = alpha[0].sum()
    if scale[0] > 0:
        alpha[0] /= scale[0]

    for t in range(1, n):
        alpha[t] = B[t] * (alpha[t - 1] @ A)
        scale[t] = alpha[t].sum()
        if scale[t] > 0:
            alpha[t] /= scale[t]

    return alpha, scale


def _backward(B, A, scale):
    """backward pass with scaling."""
    n, k = B.shape
    beta = np.zeros((n, k))
    beta[-1] = 1.0

    for t in range(n - 2, -1, -1):
        beta[t] = A @ (B[t + 1] * beta[t + 1])
        if scale[t + 1] > 0:
            beta[t] /= scale[t + 1]

    return beta
