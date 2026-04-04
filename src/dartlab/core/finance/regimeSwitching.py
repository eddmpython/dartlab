"""경기국면 전환 모델 — Hamilton RS + Cleveland Fed 프로빗 + Conference Board LEI.

순수 데이터 + 판정 함수. numpy만 사용, 외부 통계 라이브러리 없음.
core/ 계층 소속 — macro(시장 해석) 엔진에서 소비.

학술 근거:
- Hamilton (1989): "A New Approach to the Economic Analysis of Nonstationary Time Series"
- Kim (1994): Smoother for Markov-Switching models
- Estrella & Mishkin (1996): Yield curve → recession probability
- Cleveland Fed: Yield Curve and Predicted GDP Growth model
- Conference Board: Leading Economic Index methodology
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erf, log, pi, sqrt

import numpy as np


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass(frozen=True)
class RecessionProb:
    """침체 확률 (Cleveland Fed 프로빗)."""

    probability: float  # 0.0~1.0
    zone: str  # "low" | "moderate" | "elevated" | "high"
    zoneLabel: str  # "낮음" | "보통" | "경계" | "높음"
    spread: float  # 입력 스프레드 값
    description: str


@dataclass(frozen=True)
class LEIResult:
    """Conference Board LEI 결과."""

    level: float  # LEI 합성 지수 값
    mom: float  # 전월 대비 변화
    mom6m: float | None  # 6개월 연율 변화
    signal: str  # "expansion" | "caution" | "recession_warning"
    signalLabel: str  # "확장" | "경계" | "침체경고"
    components: dict[str, float | None]  # 10개 구성요소
    description: str


# ══════════════════════════════════════
# Cleveland Fed 프로빗 모델
# ══════════════════════════════════════


def _normal_cdf(x: float) -> float:
    """표준정규분포 누적분포함수 (scipy 없이 구현)."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def clevelandProbit(spread10y3m: float) -> RecessionProb:
    """Cleveland Fed 프로빗: 10Y-3M 스프레드 → 12개월 내 침체 확률.

    Args:
        spread10y3m: 10년 국채 - 3개월 국채 스프레드 (%p)

    Returns:
        RecessionProb: 침체 확률 + 구간

    모델: P(recession) = Φ(α + β × spread)
    계수는 Cleveland Fed 공표값 (Estrella-Mishkin 1996 기반):
    α = -0.5333, β = -0.6330
    """
    alpha = -0.5333
    beta = -0.6330
    z = alpha + beta * spread10y3m
    prob = _normal_cdf(z)

    if prob < 0.15:
        zone, zone_label = "low", "낮음"
    elif prob < 0.30:
        zone, zone_label = "moderate", "보통"
    elif prob < 0.50:
        zone, zone_label = "elevated", "경계"
    else:
        zone, zone_label = "high", "높음"

    desc = f"12개월 내 침체 확률 {prob*100:.1f}% (10Y-3M 스프레드 {spread10y3m:+.2f}%p)"

    return RecessionProb(
        probability=round(prob, 4),
        zone=zone,
        zoneLabel=zone_label,
        spread=round(spread10y3m, 3),
        description=desc,
    )


# ══════════════════════════════════════
# Conference Board LEI
# ══════════════════════════════════════

# Conference Board 공표 가중치 (2023 기준)
_LEI_WEIGHTS: dict[str, float] = {
    "avg_weekly_hours": 0.2772,
    "initial_claims": 0.0314,  # 역수 사용
    "new_orders_consumer": 0.0505,
    "ism_new_orders": 0.0948,
    "new_orders_nondefense_cap": 0.0139,
    "building_permits": 0.0207,
    "sp500": 0.0381,
    "leading_credit": 0.3585,
    "term_spread": 0.1068,
    "consumer_expectations": 0.0081,
}


def conferenceBoardLEI(
    components: dict[str, float | None],
    prevLevel: float | None = None,
    prevLevel6m: float | None = None,
) -> LEIResult:
    """Conference Board LEI 복제.

    Args:
        components: 10개 구성요소의 표준화된 변화율 (%)
            - avg_weekly_hours: 제조업 주당 평균 근무시간 변화율
            - initial_claims: 신규 실업수당 청구 변화율 (역수)
            - new_orders_consumer: 소비재 신규수주 변화율
            - ism_new_orders: ISM 신규수주 (50 기준 편차)
            - new_orders_nondefense_cap: 비국방자본재 신규수주 변화율
            - building_permits: 건축허가 변화율
            - sp500: S&P500 변화율
            - leading_credit: Leading Credit Index 변화율
            - term_spread: 10Y-FF 스프레드 수준
            - consumer_expectations: 소비자기대지수 변화율
        prevLevel: 이전 LEI 수준 (MoM 계산용)
        prevLevel6m: 6개월 전 LEI 수준 (연율 변화 계산용)

    Returns:
        LEIResult: LEI 합성 지수 + 신호
    """
    weighted_sum = 0.0
    available = 0

    for key, weight in _LEI_WEIGHTS.items():
        val = components.get(key)
        if val is not None:
            weighted_sum += val * weight
            available += 1

    if available == 0:
        return LEIResult(
            level=0.0,
            mom=0.0,
            mom6m=None,
            signal="caution",
            signalLabel="데이터부족",
            components=components,
            description="LEI 구성요소 데이터 부족",
        )

    # 부분 구성요소일 때 비례 조정
    total_weight = sum(
        w for k, w in _LEI_WEIGHTS.items() if components.get(k) is not None
    )
    if total_weight > 0:
        level = weighted_sum / total_weight * 100  # 정규화
    else:
        level = weighted_sum * 100

    mom = level - prevLevel if prevLevel is not None else 0.0
    mom6m = None
    if prevLevel6m is not None and prevLevel6m != 0:
        mom6m = ((level / prevLevel6m) ** 2 - 1) * 100  # 6개월 연율

    # 신호 판별 (Conference Board 기준)
    # 6개월 연율 < -4.4% AND 5개 이상 구성요소 하락 → 침체경고
    declining = sum(1 for v in components.values() if v is not None and v < 0)
    if mom6m is not None and mom6m < -4.4 and declining >= 5:
        signal, signal_label = "recession_warning", "침체경고"
        desc = f"LEI 6개월 연율 {mom6m:.1f}% + {declining}개 구성요소 하락 → 침체 경고"
    elif mom < -0.1 or (mom6m is not None and mom6m < 0):
        signal, signal_label = "caution", "경계"
        desc = f"LEI 전월비 {mom:+.2f}, 경기 둔화 징후"
    else:
        signal, signal_label = "expansion", "확장"
        desc = f"LEI 전월비 {mom:+.2f}, 경기 확장 지속"

    return LEIResult(
        level=round(level, 2),
        mom=round(mom, 3),
        mom6m=round(mom6m, 2) if mom6m is not None else None,
        signal=signal,
        signalLabel=signal_label,
        components=components,
        description=desc,
    )


# ══════════════════════════════════════
# Sahm Rule (2019)
# ══════════════════════════════════════


@dataclass(frozen=True)
class SahmResult:
    """Sahm Rule 침체 지표."""

    value: float  # Sahm 지표 값 (%p)
    triggered: bool  # >= 0.5이면 침체 신호
    zone: str  # "normal" | "warning" | "recession"
    zoneLabel: str  # "정상" | "경고" | "침체"
    description: str


def sahmRule(unemploymentSeries: list[float]) -> SahmResult:
    """Sahm Rule: 실업률 3개월 MA - 12개월 최저 3개월 MA.

    Args:
        unemploymentSeries: 월간 실업률 시계열 (최소 15개월)

    Returns:
        SahmResult: >= 0.5%p이면 침체 시작 신호
    """
    if len(unemploymentSeries) < 15:
        return SahmResult(0.0, False, "normal", "데이터부족", "실업률 시계열 15개월 미만")

    # 3개월 이동평균
    ma3_current = sum(unemploymentSeries[-3:]) / 3
    # 12개월 내 3개월 MA 최저점
    ma3_min = min(
        sum(unemploymentSeries[i : i + 3]) / 3
        for i in range(len(unemploymentSeries) - 15, len(unemploymentSeries) - 2)
    )

    sahm = ma3_current - ma3_min

    if sahm >= 0.5:
        return SahmResult(round(sahm, 2), True, "recession", "침체", f"Sahm {sahm:.2f}%p ≥ 0.5 — 침체 신호 발동")
    elif sahm >= 0.3:
        return SahmResult(round(sahm, 2), False, "warning", "경고", f"Sahm {sahm:.2f}%p — 침체 접근 중")
    else:
        return SahmResult(round(sahm, 2), False, "normal", "정상", f"Sahm {sahm:.2f}%p — 정상")


# ══════════════════════════════════════
# Hamilton Regime Switching (1989)
# numpy 직접 구현 — 외부 의존성 없음
# ══════════════════════════════════════


@dataclass(frozen=True)
class HamiltonResult:
    """Hamilton Regime Switching 결과."""

    filteredProbs: np.ndarray  # (T, 2) — P(s_t=j | Y_t)
    smoothedProbs: np.ndarray  # (T, 2) — P(s_t=j | Y_T)
    currentRegime: int  # 0 또는 1 (smoothed 기준 최종 시점)
    currentProb: float  # 현재 regime의 확률
    regimeLabels: tuple[str, str]  # ("expansion", "contraction")
    params: dict  # 추정된 파라미터
    logLikelihood: float
    converged: bool
    iterations: int


def _gaussian_density(y: float, mu: float, sigma: float) -> float:
    """정규분포 밀도 f(y | mu, sigma). 언더플로 방지를 위해 로그로 계산."""
    if sigma <= 0:
        return 1e-300
    z = (y - mu) / sigma
    log_density = -0.5 * log(2 * pi) - log(sigma) - 0.5 * z * z
    return max(np.exp(log_density), 1e-300)


def _ergodic_probs(p00: float, p11: float) -> np.ndarray:
    """정상 상태(ergodic) 확률: πP = π."""
    denom = 2.0 - p00 - p11
    if abs(denom) < 1e-10:
        return np.array([0.5, 0.5])
    pi0 = (1.0 - p11) / denom
    return np.array([pi0, 1.0 - pi0])


def _hamilton_filter(
    y: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    phi: float,
    p00: float,
    p11: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Hamilton 필터 (forward recursion).

    Args:
        y: (T,) GDP 성장률 시계열
        mu: (2,) regime별 평균
        sigma: (2,) regime별 표준편차
        phi: AR(1) 계수
        p00, p11: 전이확률 (regime 유지 확률)

    Returns:
        filtered: (T, 2) — P(s_t=j | Y_t)
        predicted: (T, 2) — P(s_t=j | Y_{t-1})
        log_lik: 로그우도
    """
    T = len(y)
    P = np.array([[p00, 1 - p00], [1 - p11, p11]])  # 전이행렬

    filtered = np.zeros((T, 2))
    predicted = np.zeros((T, 2))

    xi = _ergodic_probs(p00, p11)
    log_lik = 0.0

    for t in range(T):
        # Prediction
        xi_pred = P.T @ xi
        xi_pred = np.maximum(xi_pred, 1e-10)
        xi_pred /= xi_pred.sum()
        predicted[t] = xi_pred

        # 조건부 밀도
        resid0 = y[t] - mu[0] - (phi * y[t - 1] if t > 0 else 0.0)
        resid1 = y[t] - mu[1] - (phi * y[t - 1] if t > 0 else 0.0)
        eta = np.array([
            _gaussian_density(y[t], mu[0] + (phi * y[t - 1] if t > 0 else 0.0), sigma[0]),
            _gaussian_density(y[t], mu[1] + (phi * y[t - 1] if t > 0 else 0.0), sigma[1]),
        ])

        # 주변 우도
        f_yt = xi_pred @ eta
        if f_yt < 1e-300:
            f_yt = 1e-300

        # Update (Bayes)
        xi = (xi_pred * eta) / f_yt
        xi = np.maximum(xi, 1e-10)
        xi /= xi.sum()
        filtered[t] = xi

        log_lik += log(f_yt)

    return filtered, predicted, log_lik


def _kim_smoother(
    filtered: np.ndarray,
    predicted: np.ndarray,
    p00: float,
    p11: float,
) -> np.ndarray:
    """Kim smoother (backward recursion).

    Returns:
        smoothed: (T, 2) — P(s_t=j | Y_T)
    """
    T = filtered.shape[0]
    P = np.array([[p00, 1 - p00], [1 - p11, p11]])
    smoothed = np.zeros((T, 2))
    smoothed[T - 1] = filtered[T - 1]

    for t in range(T - 2, -1, -1):
        for i in range(2):
            s = 0.0
            for j in range(2):
                pred_j = max(predicted[t + 1, j], 1e-10)
                s += P[i, j] * smoothed[t + 1, j] / pred_j
            smoothed[t, i] = filtered[t, i] * s
        # 정규화
        total = smoothed[t].sum()
        if total > 0:
            smoothed[t] /= total

    return smoothed


def hamiltonRegime(
    series: list[float] | np.ndarray,
    maxIter: int = 200,
    tol: float = 1e-6,
) -> HamiltonResult:
    """Hamilton Regime Switching — EM 알고리즘으로 추정.

    2-regime AR(1) Markov-Switching 모델:
    y_t = μ_{s_t} + φ × y_{t-1} + ε_t,  ε_t ~ N(0, σ²_{s_t})

    Args:
        series: GDP 성장률 시계열 (분기, 최소 20기간)
        maxIter: EM 최대 반복 횟수
        tol: 로그우도 수렴 기준

    Returns:
        HamiltonResult: 필터/스무더 확률 + 파라미터
    """
    y = np.asarray(series, dtype=np.float64)
    T = len(y)

    if T < 10:
        empty = np.full((T, 2), 0.5)
        return HamiltonResult(
            filteredProbs=empty,
            smoothedProbs=empty,
            currentRegime=0,
            currentProb=0.5,
            regimeLabels=("expansion", "contraction"),
            params={},
            logLikelihood=0.0,
            converged=False,
            iterations=0,
        )

    # ── 초기값 ──
    median = float(np.median(y))
    mu = np.array([float(np.mean(y[y >= median])), float(np.mean(y[y < median]))])
    sigma = np.array([float(np.std(y[y >= median])) + 0.01, float(np.std(y[y < median])) + 0.01])
    phi = 0.0
    p00 = 0.90
    p11 = 0.90

    # regime 0 = 확장 (높은 평균), regime 1 = 침체 (낮은 평균)
    if mu[0] < mu[1]:
        mu[0], mu[1] = mu[1], mu[0]
        sigma[0], sigma[1] = sigma[1], sigma[0]

    prev_ll = -np.inf
    converged = False

    for iteration in range(maxIter):
        # ── E-step ──
        filtered, predicted, log_lik = _hamilton_filter(y, mu, sigma, phi, p00, p11)
        smoothed = _kim_smoother(filtered, predicted, p00, p11)

        # 수렴 체크
        if abs(log_lik - prev_ll) < tol:
            converged = True
            break
        prev_ll = log_lik

        # ── M-step ──
        w = smoothed  # (T, 2) — smoothed regime 확률

        # 전이확률 갱신 (joint smoothed approximation)
        P_mat = np.array([[p00, 1 - p00], [1 - p11, p11]])
        numer = np.zeros((2, 2))
        denom_p = np.zeros(2)
        for t in range(1, T):
            for i in range(2):
                for j in range(2):
                    joint = filtered[t - 1, i] * P_mat[i, j] * smoothed[t, j]
                    pred_j = max(predicted[t, j], 1e-10)
                    joint *= (smoothed[t, j] / max(filtered[t, j], 1e-10)) if filtered[t, j] > 1e-10 else 1.0
                    # 단순화: joint ≈ w[t-1, i] * P[i,j] * (w[t,j] / pred[t,j])
                    joint_simple = w[t - 1, i] * P_mat[i, j] * w[t, j] / pred_j
                    numer[i, j] += joint_simple
                denom_p[i] += w[t - 1, i]

        for i in range(2):
            if denom_p[i] > 0:
                for j in range(2):
                    numer[i, j] /= denom_p[i]
        # 정규화
        for i in range(2):
            row_sum = numer[i].sum()
            if row_sum > 0:
                numer[i] /= row_sum
        p00 = np.clip(numer[0, 0], 0.01, 0.99)
        p11 = np.clip(numer[1, 1], 0.01, 0.99)

        # AR 계수 (가중 OLS)
        wx = 0.0
        wxx = 0.0
        for t in range(1, T):
            for j in range(2):
                resid = y[t] - mu[j]
                x = y[t - 1] - mu[j]
                wx += w[t, j] * resid * x
                wxx += w[t, j] * x * x
        if wxx > 0:
            phi = np.clip(wx / wxx, -0.95, 0.95)

        # Regime 평균
        for j in range(2):
            numer_mu = 0.0
            denom_mu = 0.0
            for t in range(T):
                ar_term = phi * y[t - 1] if t > 0 else 0.0
                numer_mu += w[t, j] * (y[t] - ar_term)
                denom_mu += w[t, j]
            if denom_mu > 0:
                mu[j] = numer_mu / denom_mu

        # Regime 분산
        for j in range(2):
            numer_var = 0.0
            denom_var = 0.0
            for t in range(T):
                ar_term = phi * y[t - 1] if t > 0 else 0.0
                resid = y[t] - mu[j] - ar_term
                numer_var += w[t, j] * resid * resid
                denom_var += w[t, j]
            if denom_var > 0:
                sigma[j] = max(sqrt(numer_var / denom_var), 0.01)

        # regime 0이 항상 확장(높은 평균)이도록 유지
        if mu[0] < mu[1]:
            mu[0], mu[1] = mu[1], mu[0]
            sigma[0], sigma[1] = sigma[1], sigma[0]
            p00, p11 = p11, p00
            filtered = filtered[:, ::-1]
            smoothed = smoothed[:, ::-1]
            predicted = predicted[:, ::-1]

    # 최종 필터/스무더
    filtered, predicted, log_lik = _hamilton_filter(y, mu, sigma, phi, p00, p11)
    smoothed = _kim_smoother(filtered, predicted, p00, p11)

    current_regime = int(np.argmax(smoothed[-1]))
    current_prob = float(smoothed[-1, current_regime])

    return HamiltonResult(
        filteredProbs=filtered,
        smoothedProbs=smoothed,
        currentRegime=current_regime,
        currentProb=round(current_prob, 4),
        regimeLabels=("expansion", "contraction"),
        params={
            "mu_expansion": round(float(mu[0]), 4),
            "mu_contraction": round(float(mu[1]), 4),
            "sigma_expansion": round(float(sigma[0]), 4),
            "sigma_contraction": round(float(sigma[1]), 4),
            "phi": round(float(phi), 4),
            "p_stay_expansion": round(float(p00), 4),
            "p_stay_contraction": round(float(p11), 4),
        },
        logLikelihood=round(log_lik, 2),
        converged=converged,
        iterations=iteration + 1,
    )
