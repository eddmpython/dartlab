"""Merton 구조 모형 — Distance to Default (D2D) + 부도 확률 (PD).

Merton (1974) 모형을 2-방정식 Newton-Raphson으로 풀어
주가 변동성 + 부채에서 부도 거리와 부도 확률을 추정한다.

Moody's KMV가 전 세계 은행에서 사용하는 사실상 표준.

수학:
    기업 자산 V는 GBM을 따른다고 가정.
    주식 E = V·N(d₁) - D·e^(-rT)·N(d₂)  (Black-Scholes call)
    σ_E·E = V·N(d₁)·σ_A                   (Itô 보조정리)
    D2D = (ln(V/D) + (r - σ_A²/2)·T) / (σ_A·√T)
    PD = N(-D2D) × 100  (%)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

try:
    from scipy.stats import norm
except ImportError:  # scipy는 optional — CI/경량 환경에서 없을 수 있음
    norm = None  # type: ignore[assignment]


@dataclass(slots=True)
class MertonResult:
    """Merton 모형 풀이 결과."""

    assetValue: float  # V₀ (추정 자산가치)
    assetVolatility: float  # σ_A (비율, 0.25 = 25%)
    d2d: float  # Distance to Default
    pd: float  # 부도확률 (%)
    equityValue: float  # E (시가총액)
    debtFaceValue: float  # D (총부채)
    riskFreeRate: float  # r
    maturity: float  # T
    equityVolatility: float  # σ_E (비율)
    converged: bool
    iterations: int


def calcEquityVolatility(returns: list[float], tradingDays: int = 252) -> float:
    """일별 수익률 → 연간 변동성 (비율).

    Args:
        returns: 일별 수익률 리스트 (0.01 = 1%). NaN/None 제거 후 계산.
        tradingDays: 연간 거래일 수.

    Returns:
        연간 변동성 (비율). 데이터 부족 시 0.0.
    """
    clean = [r for r in returns if r is not None and math.isfinite(r)]
    n = len(clean)
    if n < 20:
        return 0.0

    mean = sum(clean) / n
    variance = sum((r - mean) ** 2 for r in clean) / (n - 1)
    daily_vol = math.sqrt(variance)
    return daily_vol * math.sqrt(tradingDays)


def solveMerton(
    equityValue: float,
    debtFaceValue: float,
    equityVolatility: float,
    riskFreeRate: float = 0.035,
    maturity: float = 1.0,
    maxIter: int = 200,
    tol: float = 1e-8,
) -> MertonResult | None:
    """Merton 모형 2-방정식 Newton-Raphson 풀이.

    Args:
        equityValue: E (시가총액).
        debtFaceValue: D (총부채 액면가).
        equityVolatility: σ_E (연간 변동성, 비율. 0.3 = 30%).
        riskFreeRate: r (무위험이자율, 0.035 = 3.5%).
        maturity: T (만기, 년).
        maxIter: 최대 반복 횟수.
        tol: 수렴 허용오차.

    Returns:
        MertonResult 또는 입력 부적절 시 None.
    """
    if norm is None:
        raise ImportError("scipy 필요: pip install scipy")

    E = equityValue
    D = debtFaceValue
    sigma_E = equityVolatility

    if E <= 0 or D <= 0 or sigma_E <= 0 or maturity <= 0:
        return None

    sqrtT = math.sqrt(maturity)
    expRT = math.exp(-riskFreeRate * maturity)

    # 초기값
    V = E + D
    sigma_A = sigma_E * E / (E + D)

    for i in range(maxIter):
        if V <= 0 or sigma_A <= 0:
            return MertonResult(
                assetValue=V,
                assetVolatility=sigma_A,
                d2d=0.0,
                pd=100.0,
                equityValue=E,
                debtFaceValue=D,
                riskFreeRate=riskFreeRate,
                maturity=maturity,
                equityVolatility=sigma_E,
                converged=False,
                iterations=i,
            )

        d1 = (math.log(V / D) + (riskFreeRate + 0.5 * sigma_A**2) * maturity) / (sigma_A * sqrtT)
        d2 = d1 - sigma_A * sqrtT

        Nd1 = norm.cdf(d1)
        Nd2 = norm.cdf(d2)
        nd1 = norm.pdf(d1)

        # f1: E - V·N(d1) + D·e^(-rT)·N(d2) = 0
        f1 = E - V * Nd1 + D * expRT * Nd2
        # f2: σ_E·E - V·N(d1)·σ_A = 0
        f2 = sigma_E * E - V * Nd1 * sigma_A

        # 야코비안
        # ∂f1/∂V = -N(d1) - V·n(d1)·∂d1/∂V + D·e^(-rT)·n(d2)·∂d2/∂V
        # ∂d1/∂V = 1 / (V·σ_A·√T)
        dd1_dV = 1.0 / (V * sigma_A * sqrtT)
        dd2_dV = dd1_dV

        J11 = -Nd1  # ∂f1/∂V (simplified: higher order terms cancel)
        J12 = D * expRT * nd1 * sqrtT  # ∂f1/∂σ_A (via d2)
        # Actually compute full Jacobian
        J11 = -Nd1 - V * nd1 * dd1_dV + D * expRT * nd1 * dd2_dV  # nd1 = n(d1) ≈ n(d2) only at d1≈d2
        # Correct: n(d2) ≠ n(d1) in general
        nd2 = norm.pdf(d2)
        J11 = -Nd1 - V * nd1 * dd1_dV + D * expRT * nd2 * dd2_dV

        dd1_dsA = -(math.log(V / D) + (riskFreeRate - 0.5 * sigma_A**2) * maturity) / (sigma_A**2 * sqrtT)
        dd2_dsA = dd1_dsA - sqrtT

        J12 = -V * nd1 * dd1_dsA + D * expRT * nd2 * dd2_dsA

        # ∂f2/∂V = -N(d1)·σ_A - V·n(d1)·∂d1/∂V·σ_A
        J21 = -Nd1 * sigma_A - V * nd1 * dd1_dV * sigma_A
        # ∂f2/∂σ_A = -V·N(d1) - V·n(d1)·∂d1/∂σ_A·σ_A
        J22 = -V * Nd1 - V * nd1 * dd1_dsA * sigma_A

        # 행렬식
        det = J11 * J22 - J12 * J21
        if abs(det) < 1e-20:
            break

        # Newton step
        dV = (f1 * J22 - f2 * J12) / det
        dSigma = (J11 * f2 - J21 * f1) / det

        V_new = V - dV
        sigma_new = sigma_A - dSigma

        # 양수 보장 (step halving)
        step = 1.0
        while (V_new <= 0 or sigma_new <= 0) and step > 1e-4:
            step *= 0.5
            V_new = V - dV * step
            sigma_new = sigma_A - dSigma * step

        if V_new <= 0 or sigma_new <= 0:
            break

        V = V_new
        sigma_A = sigma_new

        if abs(dV) < tol * V and abs(dSigma) < tol * sigma_A:
            # 수렴
            d1_final = (math.log(V / D) + (riskFreeRate + 0.5 * sigma_A**2) * maturity) / (sigma_A * sqrtT)
            d2d = (math.log(V / D) + (riskFreeRate - 0.5 * sigma_A**2) * maturity) / (sigma_A * sqrtT)
            pd_pct = norm.cdf(-d2d) * 100

            return MertonResult(
                assetValue=V,
                assetVolatility=sigma_A,
                d2d=d2d,
                pd=pd_pct,
                equityValue=E,
                debtFaceValue=D,
                riskFreeRate=riskFreeRate,
                maturity=maturity,
                equityVolatility=sigma_E,
                converged=True,
                iterations=i + 1,
            )

    # 미수렴 — 마지막 값으로 D2D 계산
    if V > 0 and sigma_A > 0:
        d2d = (math.log(V / D) + (riskFreeRate - 0.5 * sigma_A**2) * maturity) / (sigma_A * sqrtT)
        pd_pct = norm.cdf(-d2d) * 100
    else:
        d2d = 0.0
        pd_pct = 100.0

    return MertonResult(
        assetValue=V,
        assetVolatility=sigma_A,
        d2d=d2d,
        pd=pd_pct,
        equityValue=E,
        debtFaceValue=D,
        riskFreeRate=riskFreeRate,
        maturity=maturity,
        equityVolatility=sigma_E,
        converged=False,
        iterations=maxIter,
    )
