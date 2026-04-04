"""수익률 곡선 모델 — Nelson-Siegel 분해.

순수 데이터 + 판정 함수. numpy만 사용, 외부 의존성 없음.
core/ 계층 소속 — macro/rates에서 소비.

학술 근거:
- Nelson & Siegel (1987): "Parsimonious Modeling of Yield Curves"
- Diebold & Li (2006): "Forecasting the Term Structure of Government Bond Yields"
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NelsonSiegelResult:
    """Nelson-Siegel 수익률 곡선 분해 결과."""

    beta0: float  # Level (장기 금리 수준)
    beta1: float  # Slope (기울기: 양수=정상, 음수=역전)
    beta2: float  # Curvature (곡률: 중기 볼록/오목)
    lamb: float  # λ (감쇠 파라미터)
    fitted: np.ndarray  # 피팅된 수익률
    residuals: np.ndarray  # 잔차
    rmse: float  # RMSE
    interpretation: str  # 해석
    description: str


def _ns_factor_loadings(tau: np.ndarray, lamb: float) -> np.ndarray:
    """Nelson-Siegel 팩터 로딩 행렬 (T×3).

    y(τ) = β0 × 1 + β1 × [(1-e^(-τ/λ))/(τ/λ)] + β2 × [(1-e^(-τ/λ))/(τ/λ) - e^(-τ/λ)]
    """
    x = tau / lamb
    x = np.maximum(x, 1e-10)  # 0 방지
    exp_x = np.exp(-x)
    f1 = np.ones_like(tau)
    f2 = (1 - exp_x) / x
    f3 = f2 - exp_x
    return np.column_stack([f1, f2, f3])


def nelsonSiegel(
    maturities: list[float] | np.ndarray,
    yields: list[float] | np.ndarray,
) -> NelsonSiegelResult:
    """Nelson-Siegel 모델로 수익률 곡선 분해.

    Grid search로 최적 λ를 찾고, OLS로 β0, β1, β2를 추정한다.
    scipy 없이 numpy만 사용.

    Args:
        maturities: 만기 (년 단위). 예: [0.25, 1, 2, 3, 5, 7, 10, 20, 30]
        yields: 해당 만기의 수익률 (%). 예: [4.5, 4.3, 4.1, 4.0, 3.9, 3.85, 3.8, 3.9, 4.0]

    Returns:
        NelsonSiegelResult: β0(Level), β1(Slope), β2(Curvature) + 해석
    """
    tau = np.asarray(maturities, dtype=np.float64)
    y = np.asarray(yields, dtype=np.float64)

    # 유효 데이터만
    mask = ~(np.isnan(tau) | np.isnan(y))
    tau = tau[mask]
    y = y[mask]

    if len(tau) < 3:
        return NelsonSiegelResult(0, 0, 0, 1.0, np.array([]), np.array([]), 0, "insufficient", "데이터 3개 미만")

    # Grid search: λ = 0.5 ~ 5.0 (Diebold-Li 기본값 ~1.5)
    best_rmse = np.inf
    best_beta = np.zeros(3)
    best_lamb = 1.5

    for lamb in np.arange(0.3, 6.0, 0.1):
        X = _ns_factor_loadings(tau, lamb)
        # OLS: β = (X'X)^{-1} X'y
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        resid = y - X @ beta
        rmse = float(np.sqrt(np.mean(resid**2)))
        if rmse < best_rmse:
            best_rmse = rmse
            best_beta = beta
            best_lamb = lamb

    b0, b1, b2 = best_beta
    X_best = _ns_factor_loadings(tau, best_lamb)
    fitted = X_best @ best_beta
    residuals = y - fitted

    # 해석
    # β1: 양수 = 정상(단기>장기 spread 양수의 반대...). 실제: β1 ≈ -(장기-단기)
    # Nelson-Siegel에서 β1이 음수면 정상적 우상향, 양수면 역전
    # Slope = 장기 - 단기 ≈ β0 - (β0 + β1) = -β1
    effective_slope = -b1

    if effective_slope > 1.0:
        interp = "steep_normal"
        desc = f"수익률 곡선 가파른 정상 (기울기 {effective_slope:.2f}%p) — 경기 확장/인플레 기대"
    elif effective_slope > 0.0:
        interp = "normal"
        desc = f"수익률 곡선 정상 (기울기 {effective_slope:.2f}%p) — 정상적 시장"
    elif effective_slope > -0.5:
        interp = "flat"
        desc = f"수익률 곡선 평탄화 (기울기 {effective_slope:.2f}%p) — 경기 둔화 신호"
    else:
        interp = "inverted"
        desc = f"수익률 곡선 역전 (기울기 {effective_slope:.2f}%p) — 침체 경고"

    return NelsonSiegelResult(
        beta0=round(float(b0), 4),
        beta1=round(float(b1), 4),
        beta2=round(float(b2), 4),
        lamb=round(float(best_lamb), 2),
        fitted=fitted,
        residuals=residuals,
        rmse=round(best_rmse, 4),
        interpretation=interp,
        description=desc,
    )
