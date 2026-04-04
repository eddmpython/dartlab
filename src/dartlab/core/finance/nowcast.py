"""GDP Nowcasting — Dynamic Factor Model + Kalman 필터.

numpy 직접 구현 — 외부 통계 라이브러리 없음.
core/ 계층 소속 — macro(시장 해석) 엔진에서 소비.

학술 근거:
- Banbura, Giannone & Reichlin (2011): "Nowcasting"
- Doz, Giannone & Reichlin (2011): "A two-step estimator for large approximate DFMs"
- NY Fed Staff Nowcast technical paper
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass(frozen=True)
class NowcastResult:
    """GDP Nowcasting 결과."""

    gdpEstimate: float  # GDP 성장률 추정 (%)
    confidence: str  # "high" | "medium" | "low"
    factor: np.ndarray  # 추출된 공통 팩터 시계열
    factorCurrent: float  # 최신 팩터 값
    loadings: np.ndarray  # 팩터 로딩 (변수별 가중치)
    logLikelihood: float
    converged: bool
    iterations: int
    description: str


# ══════════════════════════════════════
# Kalman 필터 (결측치 처리 포함)
# ══════════════════════════════════════


def _kalman_filter(
    y: np.ndarray,
    A: np.ndarray,
    H: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    a0: np.ndarray,
    P0: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Kalman 필터 — 결측치(NaN) 자동 처리.

    Args:
        y: (T, n) 관측 행렬 (NaN = 결측)
        A: (rp, rp) 상태 전이 행렬
        H: (n, rp) 관측 행렬
        Q: (rp, rp) 상태 잡음 공분산
        R: (n, n) 관측 잡음 공분산 (대각)
        a0: (rp,) 초기 상태
        P0: (rp, rp) 초기 공분산

    Returns:
        a_pred, a_filt, P_pred, P_filt, log_lik
    """
    T, n = y.shape
    rp = A.shape[0]

    a_pred = np.zeros((T, rp))
    a_filt = np.zeros((T, rp))
    P_pred = np.zeros((T, rp, rp))
    P_filt = np.zeros((T, rp, rp))
    log_lik = 0.0

    a_prev = a0.copy()
    P_prev = P0.copy()

    for t in range(T):
        # Prediction
        a_pred[t] = A @ a_prev
        P_pred[t] = A @ P_prev @ A.T + Q

        # 관측 가능한 변수
        obs_mask = ~np.isnan(y[t])
        W = np.where(obs_mask)[0]

        if len(W) == 0:
            # 결측 — update 스킵
            a_filt[t] = a_pred[t]
            P_filt[t] = P_pred[t]
        else:
            H_t = H[W, :]
            R_t = R[np.ix_(W, W)]
            y_obs = y[t, W]

            # Innovation
            v = y_obs - H_t @ a_pred[t]
            F = H_t @ P_pred[t] @ H_t.T + R_t

            # Kalman gain (solve for numerical stability)
            try:
                K = np.linalg.solve(F, H_t @ P_pred[t].T).T
            except np.linalg.LinAlgError:
                K = P_pred[t] @ H_t.T @ np.linalg.pinv(F)

            # Update
            a_filt[t] = a_pred[t] + K @ v
            P_filt[t] = P_pred[t] - K @ H_t @ P_pred[t]
            # 대칭 보장
            P_filt[t] = 0.5 * (P_filt[t] + P_filt[t].T)

            # 로그우도
            try:
                sign, logdet = np.linalg.slogdet(F)
                if sign > 0:
                    log_lik += -0.5 * (len(W) * np.log(2 * np.pi) + logdet + v @ np.linalg.solve(F, v))
            except np.linalg.LinAlgError:
                pass

        a_prev = a_filt[t]
        P_prev = P_filt[t]

    return a_pred, a_filt, P_pred, P_filt, log_lik


def _kalman_smoother(
    a_pred: np.ndarray,
    a_filt: np.ndarray,
    P_pred: np.ndarray,
    P_filt: np.ndarray,
    A: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Rauch-Tung-Striebel smoother.

    Returns:
        a_smooth, P_smooth
    """
    T = a_filt.shape[0]
    rp = A.shape[0]

    a_smooth = np.zeros_like(a_filt)
    P_smooth = np.zeros_like(P_filt)

    a_smooth[T - 1] = a_filt[T - 1]
    P_smooth[T - 1] = P_filt[T - 1]

    for t in range(T - 2, -1, -1):
        try:
            J = P_filt[t] @ A.T @ np.linalg.inv(P_pred[t + 1])
        except np.linalg.LinAlgError:
            J = P_filt[t] @ A.T @ np.linalg.pinv(P_pred[t + 1])

        a_smooth[t] = a_filt[t] + J @ (a_smooth[t + 1] - a_pred[t + 1])
        P_smooth[t] = P_filt[t] + J @ (P_smooth[t + 1] - P_pred[t + 1]) @ J.T
        P_smooth[t] = 0.5 * (P_smooth[t] + P_smooth[t].T)

    return a_smooth, P_smooth


# ══════════════════════════════════════
# Dynamic Factor Model — EM 추정
# ══════════════════════════════════════


def gdpNowcast(
    indicators: np.ndarray,
    nFactors: int = 1,
    arOrder: int = 1,
    maxIter: int = 50,
    tol: float = 1e-4,
) -> NowcastResult:
    """Dynamic Factor Model로 GDP Nowcasting.

    PCA 초기화 → Kalman 필터/스무더 → EM 반복.

    Args:
        indicators: (T, n) 행렬 — n개 월간 거시지표. NaN = 결측/미발표.
            마지막 열이 GDP(분기)면 분기 미발표 월은 NaN.
        nFactors: 추출할 공통 팩터 수 (기본 1)
        arOrder: 팩터 AR 차수 (기본 1)
        maxIter: EM 최대 반복
        tol: 로그우도 수렴 기준

    Returns:
        NowcastResult
    """
    y = np.asarray(indicators, dtype=np.float64)
    T, n = y.shape
    r = nFactors
    p = arOrder
    rp = r * p

    if T < rp + 5 or n < r + 1:
        return NowcastResult(
            gdpEstimate=0.0,
            confidence="low",
            factor=np.zeros(T),
            factorCurrent=0.0,
            loadings=np.zeros(n),
            logLikelihood=0.0,
            converged=False,
            iterations=0,
            description="데이터 부족",
        )

    # ── 표준화 ──
    col_means = np.nanmean(y, axis=0)
    col_stds = np.nanstd(y, axis=0)
    col_stds[col_stds < 1e-10] = 1.0
    y_std = (y - col_means) / col_stds

    # 결측 채우기 (PCA 초기화용)
    y_filled = y_std.copy()
    for j in range(n):
        mask = np.isnan(y_filled[:, j])
        if mask.any():
            y_filled[mask, j] = 0.0  # 평균(=0, 표준화 후)

    # ── PCA 초기화 ──
    C = y_filled.T @ y_filled / T
    eigenvalues, eigenvectors = np.linalg.eigh(C)
    # 상위 r개 (eigh는 오름차순)
    V_r = eigenvectors[:, -r:][:, ::-1]
    D_r = eigenvalues[-r:][::-1]

    Lambda = V_r * np.sqrt(np.maximum(D_r, 1e-6))  # n × r
    f_init = y_filled @ V_r  # T × r

    # VAR(p) OLS
    if p == 1 and r == 1:
        f_lag = f_init[:-1, 0]
        f_cur = f_init[1:, 0]
        denom = f_lag @ f_lag
        A_coef = (f_lag @ f_cur / denom) if denom > 0 else 0.5
        A_coef = np.clip(A_coef, -0.95, 0.95)
        residuals = f_cur - A_coef * f_lag
        Q_val = float(np.var(residuals)) + 1e-6
    else:
        # 일반 VAR(p)
        X_lag = np.column_stack([f_init[p - 1 - i : T - 1 - i] for i in range(p)])  # (T-p) × rp
        Y_cur = f_init[p:]  # (T-p) × r
        try:
            beta = np.linalg.lstsq(X_lag, Y_cur, rcond=None)[0]  # rp × r
        except np.linalg.LinAlgError:
            beta = np.zeros((rp, r))
        residuals = Y_cur - X_lag @ beta
        Q_val = float(np.mean(np.var(residuals, axis=0))) + 1e-6
        A_coef = beta.T  # r × rp

    # 상태공간 구성
    A_comp = np.zeros((rp, rp))
    if p == 1 and r == 1:
        A_comp[0, 0] = A_coef
    else:
        A_comp[:r, :] = A_coef if isinstance(A_coef, np.ndarray) else np.array([[A_coef]])
        if rp > r:
            A_comp[r:, : rp - r] = np.eye(rp - r)  # companion identity

    H = np.zeros((n, rp))
    H[:, :r] = Lambda

    Q_full = np.zeros((rp, rp))
    if r == 1:
        Q_full[0, 0] = Q_val
    else:
        np.fill_diagonal(Q_full[:r, :r], Q_val)

    R_diag = np.diag(np.maximum(np.diag(C - Lambda @ Lambda.T), 1e-6))

    a0 = np.zeros(rp)
    P0 = 10.0 * np.eye(rp)

    prev_ll = -np.inf
    converged = False
    iteration = 0

    for iteration in range(maxIter):
        # ── E-step ──
        a_pred, a_filt, P_pred, P_filt, log_lik = _kalman_filter(y_std, A_comp, H, Q_full, R_diag, a0, P0)
        a_smooth, P_smooth = _kalman_smoother(a_pred, a_filt, P_pred, P_filt, A_comp)

        if abs(log_lik - prev_ll) < tol:
            converged = True
            break
        prev_ll = log_lik

        # ── M-step ──

        # 충분 통계량
        S_ff = np.zeros((rp, rp))
        S_ff1 = np.zeros((rp, rp))
        S_f1f1 = np.zeros((rp, rp))
        count = 0
        for t in range(1, T):
            S_ff += P_smooth[t] + np.outer(a_smooth[t], a_smooth[t])
            S_f1f1 += P_smooth[t - 1] + np.outer(a_smooth[t - 1], a_smooth[t - 1])
            # Cross: P_{t,t-1|T} 근사
            try:
                J_prev = P_filt[t - 1] @ A_comp.T @ np.linalg.inv(P_pred[t])
            except np.linalg.LinAlgError:
                J_prev = np.zeros((rp, rp))
            P_cross = P_smooth[t] @ J_prev.T
            S_ff1 += P_cross + np.outer(a_smooth[t], a_smooth[t - 1])
            count += 1

        if count > 0:
            S_ff /= count
            S_ff1 /= count
            S_f1f1 /= count

        # A 갱신
        try:
            A_new = S_ff1[:r, :] @ np.linalg.inv(S_f1f1)
            # 안정성: 고유값 체크
            eigs = np.linalg.eigvals(A_new[:r, :r] if r > 1 else np.array([[A_new[0, 0]]]))
            if np.all(np.abs(eigs) < 0.99):
                A_comp[:r, :] = A_new
        except np.linalg.LinAlgError:
            pass

        # Q 갱신
        Q_new = S_ff[:r, :r] - A_comp[:r, :] @ S_f1f1 @ A_comp[:r, :].T
        Q_new = 0.5 * (Q_new + Q_new.T)
        np.fill_diagonal(Q_new, np.maximum(np.diag(Q_new), 1e-6))
        Q_full[:r, :r] = Q_new

        # Lambda, R 갱신 (변수별)
        for i in range(n):
            obs_t = np.where(~np.isnan(y_std[:, i]))[0]
            if len(obs_t) < 3:
                continue

            yf = np.zeros(r)
            ff = np.zeros((r, r))
            for t in obs_t:
                f_t = a_smooth[t, :r]
                yf += y_std[t, i] * f_t
                ff += P_smooth[t, :r, :r] + np.outer(f_t, f_t)

            try:
                Lambda[i, :] = yf @ np.linalg.inv(ff)
            except np.linalg.LinAlgError:
                pass

            resid_var = 0.0
            for t in obs_t:
                f_t = a_smooth[t, :r]
                e = y_std[t, i] - Lambda[i, :] @ f_t
                resid_var += e * e + Lambda[i, :] @ P_smooth[t, :r, :r] @ Lambda[i, :]
            R_diag[i, i] = max(resid_var / len(obs_t), 1e-6)

        H[:, :r] = Lambda

    # 최종 필터
    a_pred, a_filt, P_pred, P_filt, log_lik = _kalman_filter(y_std, A_comp, H, Q_full, R_diag, a0, P0)
    a_smooth, P_smooth = _kalman_smoother(a_pred, a_filt, P_pred, P_filt, A_comp)

    # 팩터 추출
    factor = a_smooth[:, 0]
    factor_current = float(factor[-1])

    # GDP nowcast: 마지막 열이 GDP라고 가정
    gdp_loading = float(Lambda[-1, 0]) if n > 0 else 0.0
    gdp_estimate = factor_current * gdp_loading * col_stds[-1] + col_means[-1]

    # 신뢰도
    P_current = float(P_filt[-1, 0, 0])
    obs_count = np.sum(~np.isnan(y_std[-1]))
    if obs_count > n * 0.7 and P_current < 1.0:
        confidence = "high"
    elif obs_count > n * 0.3:
        confidence = "medium"
    else:
        confidence = "low"

    return NowcastResult(
        gdpEstimate=round(float(gdp_estimate), 2),
        confidence=confidence,
        factor=factor,
        factorCurrent=round(factor_current, 4),
        loadings=Lambda[:, 0],
        logLikelihood=round(log_lik, 2),
        converged=converged,
        iterations=iteration + 1,
        description=f"GDP nowcast {gdp_estimate:.2f}% (팩터 {factor_current:.3f}, 신뢰도 {confidence})",
    )
