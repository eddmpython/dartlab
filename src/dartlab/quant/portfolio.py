"""포트폴리오 최적화 — MVO + HRP + 리스크 버짓팅.

학술 근거:
- Markowitz (1952): Portfolio Selection
- Lopez de Prado (2016): Hierarchical Risk Parity
- Maillard et al. (2010): Equal Risk Contribution
"""

from __future__ import annotations

import logging

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays

log = logging.getLogger(__name__)


def _build_returns(stockCodes: list[str]) -> tuple[np.ndarray | None, list[str]]:
    """종목별 OHLCV를 순차 수집하여 수익률 행렬 구성."""
    all_rets = []
    valid_codes = []
    for code in stockCodes:
        ohlcv = fetch_ohlcv(code)
        if ohlcv is None or ohlcv.is_empty():
            continue
        arr = ohlcv_to_arrays(ohlcv)
        close = arr.get("close")
        if close is None or len(close) < 30:
            continue
        rets = np.diff(np.log(close))
        all_rets.append(rets)
        valid_codes.append(code)
        del ohlcv  # 메모리 해제

    if len(valid_codes) < 2:
        return None, valid_codes

    # 길이 맞추기
    min_len = min(len(r) for r in all_rets)
    matrix = np.column_stack([r[-min_len:] for r in all_rets])
    return matrix, valid_codes


def analyze_meanvar(stockCodes: list[str], *, market: str = "auto", **kwargs) -> dict:
    """Markowitz 평균-분산 최적화."""
    result: dict = {"stockCodes": stockCodes}

    if len(stockCodes) < 2:
        w = {stockCodes[0]: 1.0} if stockCodes else {}
        return {**result, "minVariance": {"weights": w}, "info": "2종목 이상 필요"}

    returns, codes = _build_returns(stockCodes)
    if returns is None:
        return {**result, "error": f"수익률 데이터 부족 ({len(codes)}종목)"}

    n = len(codes)
    mu = np.mean(returns, axis=0) * 252
    cov = np.cov(returns.T) * 252

    result["validStocks"] = codes
    result["dataPoints"] = returns.shape[0]

    # Min-Variance: w = Σ⁻¹·1 / (1'·Σ⁻¹·1)
    try:
        inv_cov = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        inv_cov = np.linalg.pinv(cov)

    ones = np.ones(n)
    w_mv = inv_cov @ ones / (ones @ inv_cov @ ones)
    w_mv = np.clip(w_mv, 0, None)  # long-only
    w_mv /= w_mv.sum()

    ret_mv = float(w_mv @ mu)
    risk_mv = float(np.sqrt(w_mv @ cov @ w_mv))
    sharpe_mv = ret_mv / risk_mv if risk_mv > 0 else 0

    result["minVariance"] = {
        "weights": {c: round(float(w), 4) for c, w in zip(codes, w_mv)},
        "expectedReturn": round(ret_mv, 4),
        "risk": round(risk_mv, 4),
        "sharpe": round(sharpe_mv, 4),
    }

    # Tangency: w = Σ⁻¹·μ / (1'·Σ⁻¹·μ)
    w_tan = inv_cov @ mu
    if w_tan.sum() > 0:
        w_tan = np.clip(w_tan, 0, None)
        w_tan /= w_tan.sum()
        ret_t = float(w_tan @ mu)
        risk_t = float(np.sqrt(w_tan @ cov @ w_tan))
        sharpe_t = ret_t / risk_t if risk_t > 0 else 0
        result["tangency"] = {
            "weights": {c: round(float(w), 4) for c, w in zip(codes, w_tan)},
            "expectedReturn": round(ret_t, 4),
            "risk": round(risk_t, 4),
            "sharpe": round(sharpe_t, 4),
        }

    return result


def analyze_riskparity(stockCodes: list[str], *, market: str = "auto", **kwargs) -> dict:
    """HRP — 계층적 리스크 패리티 (Lopez de Prado 2016)."""
    result: dict = {"stockCodes": stockCodes}

    if len(stockCodes) < 2:
        w = {stockCodes[0]: 1.0} if stockCodes else {}
        return {**result, "weights": w, "info": "2종목 이상 필요"}

    returns, codes = _build_returns(stockCodes)
    if returns is None:
        return {**result, "error": "수익률 데이터 부족"}

    n = len(codes)
    cov = np.cov(returns.T) * 252
    corr = np.corrcoef(returns.T)

    # 1. 거리 행렬
    dist = np.sqrt(0.5 * (1 - corr))

    # 2. Single-linkage clustering (numpy)
    order = _hierarchical_cluster(dist, n)

    # 3. Recursive bisection
    weights = np.ones(n)
    _recursive_bisection(weights, cov, order)
    weights /= weights.sum()

    # Risk contribution
    port_var = float(weights @ cov @ weights)
    rc = weights * (cov @ weights) / max(port_var, 1e-12)

    result["weights"] = {codes[i]: round(float(weights[i]), 4) for i in range(n)}
    result["riskContribution"] = {codes[i]: round(float(rc[i]), 4) for i in range(n)}
    result["clusterOrder"] = [codes[i] for i in order]
    return result


def _hierarchical_cluster(dist: np.ndarray, n: int) -> list[int]:
    """Single-linkage clustering → leaf order."""
    # Simplified: just sort by average distance to all others
    avg_dist = np.mean(dist, axis=1)
    return list(np.argsort(avg_dist))


def _recursive_bisection(weights: np.ndarray, cov: np.ndarray, order: list[int]):
    """Recursive bisection for HRP weights."""
    if len(order) <= 1:
        return

    mid = len(order) // 2
    left = order[:mid]
    right = order[mid:]

    var_left = _cluster_variance(cov, left)
    var_right = _cluster_variance(cov, right)

    alpha = 1 - var_left / (var_left + var_right) if (var_left + var_right) > 0 else 0.5

    for i in left:
        weights[i] *= alpha
    for i in right:
        weights[i] *= (1 - alpha)

    _recursive_bisection(weights, cov, left)
    _recursive_bisection(weights, cov, right)


def _cluster_variance(cov: np.ndarray, indices: list[int]) -> float:
    """클러스터의 역분산 가중 분산."""
    sub_cov = cov[np.ix_(indices, indices)]
    n = len(indices)
    if n == 1:
        return float(sub_cov[0, 0])
    # 역분산 가중
    ivp = 1 / np.diag(sub_cov)
    ivp /= ivp.sum()
    return float(ivp @ sub_cov @ ivp)


def analyze_allocation(stockCodes: list[str], *, market: str = "auto", **kwargs) -> dict:
    """리스크 버짓팅 — Equal Risk Contribution."""
    result: dict = {"stockCodes": stockCodes}

    if len(stockCodes) < 2:
        w = {stockCodes[0]: 1.0} if stockCodes else {}
        return {**result, "weights": w, "info": "2종목 이상 필요"}

    returns, codes = _build_returns(stockCodes)
    if returns is None:
        return {**result, "error": "수익률 데이터 부족"}

    n = len(codes)
    cov = np.cov(returns.T) * 252
    target_rc = 1.0 / n

    # 초기: 동일 가중
    w = np.ones(n) / n

    converged = False
    for _ in range(200):
        sigma_w = cov @ w
        port_var = float(w @ sigma_w)
        if port_var < 1e-12:
            break
        rc = w * sigma_w / port_var

        # 조정
        adj = target_rc / (rc + 1e-12)
        w_new = w * adj
        w_new = np.clip(w_new, 1e-6, None)
        w_new /= w_new.sum()

        if np.max(np.abs(w_new - w)) < 1e-8:
            converged = True
            w = w_new
            break
        w = w_new

    # 최종 risk contribution
    sigma_w = cov @ w
    port_var = float(w @ sigma_w)
    rc = w * sigma_w / max(port_var, 1e-12)

    result["weights"] = {codes[i]: round(float(w[i]), 4) for i in range(n)}
    result["riskContribution"] = {codes[i]: round(float(rc[i]), 4) for i in range(n)}
    result["converged"] = converged
    result["targetRC"] = round(target_rc, 4)
    return result
