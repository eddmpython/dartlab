"""Overfitting guards — Lopez de Prado AFML/Bailey-López de Prado.

DSR (2014) · PBO (2015) · CPCV (AFML Ch.12). 표준정규 CDF/PPF 자체 구현
(Abramowitz-Stegun + Acklam 2000). scipy 의존 0.
"""

from __future__ import annotations

import math
from itertools import combinations

import numpy as np

from ._metricsBasic import TRADING_DAYS


def _normCdf(x: float) -> float:
    """표준정규 CDF (math.erf 기반)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normPpf(p: float) -> float:
    """표준정규 inverse CDF — Beasley-Springer-Moro 근사 (Acklam 2000)."""
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")
    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    ]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (
            (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
        )
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
        (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
    )


def dsr(observedSharpe: float, returns: np.ndarray, nTrials: int = 1) -> float:
    """Deflated Sharpe Ratio (Bailey-López de Prado 2014).

    Capabilities:
        백테스트 시도 횟수(n_trials) 와 returns 의 skewness/kurtosis 를 정정해서
        "이 Sharpe 가 우연이 아닐 확률" 을 [0, 1] 로 반환. DSR > 0.95 → 통계적
        강함, < 0.5 → 의심.

    Args:
        observedSharpe: 관측 Sharpe (연환산)
        returns: 일별 수익률 (skew/kurtosis 계산용)
        nTrials: 다중 백테스트 시도 횟수 (1 이면 정정 약함)

    Returns:
        DSR ∈ [0, 1]

    Example:
        >>> dsr(1.5, returns, nTrials=10)
        0.78

    Guide:
        Bailey-Lopez 2014 SR* 와 결합. n_trials 100+ 면 통계적 압박 큼. 본 함수
        는 within-strategy DSR — between-strategy 는 haircutSharpe.

    When:
        백테스트 거버넌스 + AI 전략 진정성 답변.

    How:
        skewness/kurtosis 정정 후 SR variance → null 기대 max SR (Euler) →
        z-stat → CDF.

    Requires:
        returns ≥ 30 + observedSharpe 연환산.

    Raises:
        없음.

    See Also:
        - haircutSharpe : between-strategy 보정
        - pbo : 과적합 확률

    AIContext:
        DSR + Sharpe 동시 인용 — 단순 Sharpe 만으로 진정성 단정 금지.
    """
    r = np.asarray(returns, dtype=np.float64)
    r = r[~np.isnan(r)]
    T = len(r)
    if T < 30:
        return 0.0
    mu = float(np.mean(r))
    sd = float(np.std(r, ddof=1))
    if sd <= 0:
        return 0.0
    z = (r - mu) / sd
    skew = float(np.mean(z**3))
    kurt = float(np.mean(z**4) - 3.0)
    sr = observedSharpe / np.sqrt(TRADING_DAYS)
    em = np.euler_gamma
    if nTrials < 2:
        sr0 = 0.0
    else:
        z1 = _normPpf(1 - 1.0 / nTrials)
        z2 = _normPpf(1 - 1.0 / (nTrials * math.e))
        sr0 = (1 - em) * z1 + em * z2
        sr0 /= np.sqrt(TRADING_DAYS)
    var_sr = (1 - skew * sr + (kurt / 4.0) * sr**2) / (T - 1)
    if var_sr <= 0:
        return 0.0
    z_dsr = (sr - sr0) / np.sqrt(var_sr)
    return float(_normCdf(z_dsr))


def pbo(inSample: np.ndarray, outOfSample: np.ndarray) -> float | None:
    """Probability of Backtest Overfitting (Bailey-Borwein-López de Prado-Zhu 2015).

    Capabilities:
        in-sample 에서 최고 성과 전략이 out-of-sample 중간값 이하일 확률. PBO >
        0.5 = 과적합. CSCV 기반.

    Args:
        inSample: shape (n_trials, n_segments) — 각 trial × split 의 IS Sharpe
        outOfSample: shape (n_trials, n_segments) — 동일 trial 의 OOS Sharpe

    Returns:
        PBO ∈ [0, 1]

    Example:
        >>> pbo(is_arr, oos_arr)
        0.35

    Guide:
        PBO < 0.3 = 강건. > 0.5 = 강한 과적합. cpcvSplits + 본 함수 결합 표준.

    When:
        백테스트 거버넌스 + AI 과적합 답변.

    How:
        각 segment 에서 IS argmax → OOS rank → 중간값 이하 카운트 / segment 수.

    Requires:
        inSample/outOfSample 동일 shape (≥ 2 segment).

    Raises:
        없음 — 0.0 반환.

    See Also:
        - dsr : DSR 단일 정정
        - cpcvSplits : 분할 생성

    AIContext:
        DSR + PBO 동시 인용 — 과적합 양면 진단.
    """
    is_arr = np.asarray(inSample, dtype=np.float64)
    oos_arr = np.asarray(outOfSample, dtype=np.float64)
    if is_arr.ndim != 2 or oos_arr.ndim != 2 or is_arr.shape != oos_arr.shape:
        return 0.0
    nTrials, n_segments = is_arr.shape
    if n_segments < 2:
        return 0.0
    # 시행이 하나뿐이면 "최고 시행" 이 자기 자신이라 OOS 순위가 언제나 1 이 되고,
    # 결과가 무조건 1.0 으로 고정된다. OOS 성적이 정반대여도 같은 값이 나오므로
    # 그 숫자는 과적합에 대해 아무 말도 하지 않는다. 최대 과적합이라고 단언하는
    # 대신 판정 불가를 알린다. 이미 refit 경로가 같은 이유로 None 을 쓰고 있다.
    if nTrials < 2:
        return None
    overfit_count = 0
    for s in range(n_segments):
        best_trial = int(np.argmax(is_arr[:, s]))
        oos_rank = float(np.sum(oos_arr[:, s] >= oos_arr[best_trial, s])) / nTrials
        if oos_rank > 0.5:
            overfit_count += 1
    return float(overfit_count / n_segments)


def cpcvSplits(nObs: int, nSplits: int = 6, nTest: int = 2, embargo: int = 0) -> list[tuple]:
    """Combinatorial Purged Cross-Validation 인덱스 분할.

    Capabilities:
        Lopez de Prado AFML Ch.12 CPCV — n_splits choose n_test 조합 + embargo
        purge. pbo + DSR 의 base.

    Args:
        nObs: 시계열 길이
        nSplits: 전체 분할 수
        nTest: test 그룹 수 (nSplits choose nTest 만큼 split 생성)
        embargo: test 양 끝에서 purge 할 관측치 수

    Yields:
        (train_idx, test_idx) tuples

    Example:
        >>> list(cpcvSplits(100, nSplits=6, nTest=2))[:1]

    Guide:
        nSplits 6 + nTest 2 → 15 split (C(6,2)). embargo 는 1 일 거래 다음 영향
        제거.

    When:
        백테스트 CV 분할 + pbo 입력 생성.

    How:
        np.array_split → combinations(C(n,k)) → embargo purge → train_idx 생성.

    Requires:
        nObs ≥ nSplits × 2.

    Raises:
        없음 — 부족 시 empty yield.

    See Also:
        - pbo : 본 함수 결과 소비
        - dsr : 단일 정정

    AIContext:
        CPCV + pbo + DSR 3 종 결합으로 과적합 회피 표준 protocol.
    """
    if nObs < nSplits * 2:
        return
    bins = np.array_split(np.arange(nObs), nSplits)
    for combo in combinations(range(nSplits), nTest):
        test_groups = [bins[i] for i in combo]
        test_idx = np.concatenate(test_groups)
        purged = set(test_idx.tolist())
        for tg in test_groups:
            lo = max(0, tg[0] - embargo)
            hi = min(nObs, tg[-1] + 1 + embargo)
            for k in range(lo, hi):
                purged.add(k)
        train_idx = np.array([i for i in range(nObs) if i not in purged], dtype=np.int64)
        yield train_idx, test_idx
