"""변동성 분석 — GARCH(1,1), HAR-RV, 변동성 기간구조.

학술 근거:
- Bollerslev (1986): GARCH(1,1)
- Corsi (2009): HAR-RV 모델
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_volatility(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """변동성 종합 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict with garchVol, harRV, volTermStructure, volRegime.
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

    # ── 실현 변동성 (다중 기간) ──
    for label, window in [("5d", 5), ("20d", 20), ("60d", 60), ("120d", 120), ("252d", 252)]:
        if len(log_returns) >= window:
            rv = float(np.std(log_returns[-window:]) * np.sqrt(252))
            result[f"realizedVol_{label}"] = round(rv, 4)

    # ── HAR-RV 모델 (Corsi 2009) ──
    # RV_t+1 = β0 + β1*RV_d + β2*RV_w + β3*RV_m + ε
    if len(log_returns) >= 66:
        rv_daily = log_returns ** 2
        rv_d = _rolling_mean(rv_daily, 1)
        rv_w = _rolling_mean(rv_daily, 5)
        rv_m = _rolling_mean(rv_daily, 22)

        # OLS fit (최근 44일 사용)
        valid_start = 22  # rv_m이 유효한 시점부터
        if len(rv_d) > valid_start + 22:
            y = rv_daily[valid_start + 1:][:44]
            X = np.column_stack([
                np.ones(44),
                rv_d[valid_start:][:44],
                rv_w[valid_start:][:44],
                rv_m[valid_start:][:44],
            ])
            if len(y) == 44 and X.shape[0] == 44:
                try:
                    beta = np.linalg.lstsq(X, y, rcond=None)[0]
                    # 1일 ahead 예측
                    x_latest = np.array([1.0, rv_d[-1], rv_w[-1], rv_m[-1]])
                    har_forecast = float(np.dot(beta, x_latest))
                    har_vol = float(np.sqrt(max(har_forecast, 0) * 252))
                    result["harRV"] = round(har_vol, 4)
                    result["harCoeffs"] = {
                        "intercept": round(float(beta[0]), 8),
                        "daily": round(float(beta[1]), 4),
                        "weekly": round(float(beta[2]), 4),
                        "monthly": round(float(beta[3]), 4),
                    }
                except np.linalg.LinAlgError:
                    pass

    # ── GARCH(1,1) (Bollerslev 1986) ──
    # σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
    if len(log_returns) >= 100:
        garch_result = _fit_garch11(log_returns[-252:] if len(log_returns) >= 252 else log_returns)
        if garch_result:
            result["garchVol"] = round(garch_result["forecastVol"], 4)
            result["garchParams"] = {
                "omega": round(garch_result["omega"], 10),
                "alpha": round(garch_result["alpha"], 4),
                "beta": round(garch_result["beta"], 4),
                "persistence": round(garch_result["alpha"] + garch_result["beta"], 4),
            }
            # 장기 변동성
            persistence = garch_result["alpha"] + garch_result["beta"]
            if persistence < 1:
                long_run_var = garch_result["omega"] / (1 - persistence)
                result["garchLongRunVol"] = round(float(np.sqrt(long_run_var * 252)), 4)

    # ── 변동성 기간구조 ──
    term_structure = {}
    for label in ["5d", "20d", "60d", "120d", "252d"]:
        key = f"realizedVol_{label}"
        if key in result:
            term_structure[label] = result[key]
    result["volTermStructure"] = term_structure

    # 기간구조 형태
    vols = list(term_structure.values())
    if len(vols) >= 3:
        if vols[0] > vols[-1] * 1.2:
            result["volCurveShape"] = "backwardation"  # 단기 > 장기 (스트레스)
        elif vols[-1] > vols[0] * 1.2:
            result["volCurveShape"] = "contango"  # 장기 > 단기 (정상)
        else:
            result["volCurveShape"] = "flat"

    # ── 변동성 레짐 ──
    if "realizedVol_20d" in result:
        rv20 = result["realizedVol_20d"]
        if rv20 > 0.5:
            result["volRegime"] = "extreme"
        elif rv20 > 0.3:
            result["volRegime"] = "high"
        elif rv20 > 0.15:
            result["volRegime"] = "normal"
        else:
            result["volRegime"] = "low"

    return result


def _rolling_mean(arr: np.ndarray, window: int) -> np.ndarray:
    """간단 rolling mean."""
    if window <= 1:
        return arr.copy()
    kernel = np.ones(window) / window
    return np.convolve(arr, kernel, mode="same")


def _fit_garch11(returns: np.ndarray) -> dict | None:
    """GARCH(1,1) numpy MLE — Nelder-Mead simplex.

    σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}
    """
    n = len(returns)
    if n < 50:
        return None

    mean_r = np.mean(returns)
    resid = returns - mean_r
    var_init = float(np.var(resid))

    def neg_log_likelihood(params):
        omega, alpha, beta = params
        if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1:
            return 1e10

        sigma2 = np.empty(n)
        sigma2[0] = var_init

        for t in range(1, n):
            sigma2[t] = omega + alpha * resid[t - 1] ** 2 + beta * sigma2[t - 1]
            if sigma2[t] <= 0:
                return 1e10

        ll = -0.5 * np.sum(np.log(sigma2) + resid ** 2 / sigma2)
        return -ll

    # Nelder-Mead simplex optimization
    best_params = _nelder_mead(
        neg_log_likelihood,
        x0=np.array([var_init * 0.05, 0.08, 0.85]),
        max_iter=500,
    )

    if best_params is None:
        return None

    omega, alpha, beta = best_params
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1:
        return None

    # 1일 ahead 예측
    sigma2 = np.empty(n)
    sigma2[0] = var_init
    for t in range(1, n):
        sigma2[t] = omega + alpha * resid[t - 1] ** 2 + beta * sigma2[t - 1]

    forecast_var = omega + alpha * resid[-1] ** 2 + beta * sigma2[-1]
    forecast_vol = float(np.sqrt(max(forecast_var, 0) * 252))

    return {
        "omega": float(omega),
        "alpha": float(alpha),
        "beta": float(beta),
        "forecastVol": forecast_vol,
    }


def _nelder_mead(fn, x0: np.ndarray, max_iter: int = 500, tol: float = 1e-8) -> np.ndarray | None:
    """간이 Nelder-Mead simplex optimizer (numpy only)."""
    n = len(x0)
    # simplex 초기화
    simplex = np.zeros((n + 1, n))
    simplex[0] = x0
    for i in range(n):
        point = x0.copy()
        point[i] *= 1.05 if point[i] != 0 else 0.00025
        simplex[i + 1] = point

    f_values = np.array([fn(simplex[i]) for i in range(n + 1)])

    for _ in range(max_iter):
        # 정렬
        order = np.argsort(f_values)
        simplex = simplex[order]
        f_values = f_values[order]

        # 수렴 체크
        if np.max(np.abs(f_values[-1] - f_values[0])) < tol:
            break

        # centroid (worst 제외)
        centroid = np.mean(simplex[:-1], axis=0)

        # reflection
        xr = centroid + (centroid - simplex[-1])
        fr = fn(xr)

        if fr < f_values[0]:
            # expansion
            xe = centroid + 2 * (centroid - simplex[-1])
            fe = fn(xe)
            if fe < fr:
                simplex[-1] = xe
                f_values[-1] = fe
            else:
                simplex[-1] = xr
                f_values[-1] = fr
        elif fr < f_values[-2]:
            simplex[-1] = xr
            f_values[-1] = fr
        else:
            # contraction
            xc = centroid + 0.5 * (simplex[-1] - centroid)
            fc = fn(xc)
            if fc < f_values[-1]:
                simplex[-1] = xc
                f_values[-1] = fc
            else:
                # shrink
                for i in range(1, n + 1):
                    simplex[i] = simplex[0] + 0.5 * (simplex[i] - simplex[0])
                    f_values[i] = fn(simplex[i])

    best = simplex[np.argmin(f_values)]
    if fn(best) > 1e9:
        return None
    return best
