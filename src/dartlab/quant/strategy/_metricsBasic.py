"""표준 백테스트 메트릭 — Sharpe/Sortino/MDD/Winrate/PF/Expectancy/Turnover/Exposure.

scipy 의존 0. numpy + math 만. metrics.py facade 가 본 모듈을 re-export.
"""

from __future__ import annotations

import numpy as np

TRADING_DAYS = 252


def sharpe(returns: np.ndarray, rf: float = 0.0) -> float:
    """연환산 Sharpe ratio.

    Capabilities:
        일별 수익률 → (mean - rf/252) / std × √252 연환산 Sharpe. Sharpe (1966)
        risk-adjusted return 표준.

    Parameters
    ----------
    returns : np.ndarray
        일별 log return 시계열.
    rf : float
        연간 무위험 이자율. 기본 0.

    Returns
    -------
    float
        연환산 Sharpe ratio (배). 표본 < 2 또는 std=0 이면 0.0.

    Example:
        >>> sharpe(returns)
        1.45

    Guide:
        > 1.0 = 양호, > 2.0 = 우수, < 0 = 무위험 미달. DSR + haircutSharpe 와 함께
        다중 검정 보정 권장.

    When:
        백테스트 metrics + AI 전략 평가 진입점.

    How:
        ddof=1 std + 252 거래일 가정. log return 입력 가정.

    Requires:
        returns ≥ 2 + std > 0.

    Raises:
        없음 — 0.0 반환.

    See Also:
        - sortino : 하방편차 기반
        - dsr : 다중 시도 정정

    AIContext:
        Sharpe 단독 인용 + sample 길이/n_trials 누락 금지 — dsr 동반.
    """
    r = np.asarray(returns, dtype=np.float64)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return 0.0
    sd = float(np.std(r, ddof=1))
    if sd <= 0:
        return 0.0
    mu = float(np.mean(r)) - rf / TRADING_DAYS
    return float(mu / sd * np.sqrt(TRADING_DAYS))


def sortino(returns: np.ndarray, rf: float = 0.0) -> float:
    """Sortino ratio — 하방편차 기반.

    Capabilities:
        일별 수익률 → (mean - rf/252) / downsideStd × √252. Sharpe 대비 상방
        변동성 (좋은 변동) 보정 제외.

    Parameters
    ----------
    returns : np.ndarray
        일별 log return 시계열.
    rf : float
        연간 무위험 이자율. 기본 0.

    Returns
    -------
    float
        연환산 Sortino ratio (배). 하방 수익률 없거나 std=0 이면 0.0.

    Example:
        >>> sortino(returns)
        2.10

    Guide:
        Sharpe < Sortino = 상방 변동성 큰 자산 (성장주). 펀드 평가 시 Sortino 우선.

    When:
        백테스트 metrics + AI 비대칭 risk 답변.

    How:
        downside = r[r<0] → ddof=1 std → 연환산.

    Requires:
        returns ≥ 2 + 하방 수익률 ≥ 1.

    Raises:
        없음.

    See Also:
        - sharpe : 양방향 변동

    AIContext:
        Sharpe vs Sortino 차이 인용으로 비대칭성 평가.
    """
    r = np.asarray(returns, dtype=np.float64)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return 0.0
    # 하방편차는 목표 수익률 아래로 벗어난 정도를 전체 표본에 대해 재는 값이다.
    # 예전에는 손실 구간만 골라 그 "표준편차" 를 썼는데, 그것은 손실이 자기 평균에서
    # 얼마나 흩어졌는지를 잴 뿐 얼마나 아래인지는 재지 않는다. 그래서 매일 +2% 와
    # -1% 를 반복해 평균 +0.5% 를 내는 전략이 0.0 을 받았다. 손실 크기가 모두 같아
    # 흩어짐이 0 이기 때문이다. 좋은 전략이 최악으로 보이는 셈이다.
    target = rf / TRADING_DAYS
    shortfall = np.minimum(r - target, 0.0)
    dd = float(np.sqrt(np.mean(shortfall**2)))
    if dd <= 0:
        return 0.0
    mu = float(np.mean(r)) - target
    return float(mu / dd * np.sqrt(TRADING_DAYS))


def mdd(equity: np.ndarray) -> float:
    """최대낙폭 (Maximum Drawdown).

    Capabilities:
        누적 자산 곡선 → cumulative peak 대비 최대 낙폭 (음수). Calmar 비율의
        분모 + 매크로 리스크 표준.

    Parameters
    ----------
    equity : np.ndarray
        누적 자산 곡선 (예: 초기 1.0 부터).

    Returns
    -------
    float
        최대낙폭 비율 (음수, %). 예: -0.25 = -25% 낙폭. 표본 < 2 이면 0.0.

    Example:
        >>> mdd(np.array([1.0, 1.1, 0.9, 0.95]))
        -0.182

    Guide:
        |mdd| > 0.5 = 회복 어려움. 시점 (Drawdown date) 함께 인용해 macro
        이벤트 연결.

    When:
        백테스트 metrics + AI 낙폭 답변.

    How:
        cumulative max → (equity - peak) / peak → min.

    Requires:
        equity ≥ 2.

    Raises:
        없음.

    See Also:
        - calcTailrisk : VaR/CVaR 동반

    AIContext:
        mdd 값 + 시점 함께 인용 (macro 이벤트 매핑).
    """
    e = np.asarray(equity, dtype=np.float64)
    e = e[~np.isnan(e)]
    if len(e) < 2:
        return 0.0
    peak = np.maximum.accumulate(e)
    dd = (e - peak) / peak
    return float(np.min(dd))


def winrate(tradePnls: np.ndarray) -> float:
    """승률 — pnl > 0 비율.

    Capabilities:
        거래별 손익 → 양수 비율. 트레이딩 평가 표준 metric.

    Parameters
    ----------
    tradePnls : np.ndarray
        거래별 손익 배열.

    Returns
    -------
    float
        승률 (비율, 0~1). 거래 없으면 0.0.

    Example:
        >>> winrate(np.array([1, -1, 2, -0.5]))
        0.5

    Guide:
        winrate 50% 미만이어도 profitFactor 큰 전략 흑자 가능 — 둘 함께 인용.

    When:
        백테스트 metrics + AI 전략 승률 답변.

    How:
        sum(p > 0) / n.

    Requires:
        tradePnls 비어있지 않음.

    Raises:
        없음.

    See Also:
        - profitFactor : 총 수익/손실 비율
        - expectancy : 거래당 평균

    AIContext:
        winrate < 50% + PF > 1.5 → 비대칭 양봉 전략.
    """
    p = np.asarray(tradePnls, dtype=np.float64)
    if len(p) == 0:
        return 0.0
    return float(np.sum(p > 0) / len(p))


def profitFactor(tradePnls: np.ndarray) -> float:
    """총 수익 / 총 손실 비율.

    Capabilities:
        승 거래 합 / 손 거래 합 (절댓값). 1.5+ = 양호, 2.0+ = 우수.

    Parameters
    ----------
    tradePnls : np.ndarray
        거래별 손익 배열.

    Returns
    -------
    float
        Profit Factor (배). 손실 0 이면 inf (수익 있을 때) 또는 0.0.

    Example:
        >>> profitFactor(np.array([3, -1, 2, -1]))
        2.5

    Guide:
        winrate × avgWin / avgLoss = PF. PF 1.0 = breakeven (수수료 차감 후 손실).

    When:
        백테스트 metrics + AI 전략 비율 답변.

    How:
        sum(p>0) / |sum(p<0)|.

    Requires:
        tradePnls 비어있지 않음.

    Raises:
        없음 — 손실 0 + 수익 0 → 0.0.

    See Also:
        - winrate : 승률
        - expectancy : 거래당 평균

    AIContext:
        PF + winrate 인용으로 양봉/음봉 비율 답변.
    """
    p = np.asarray(tradePnls, dtype=np.float64)
    if len(p) == 0:
        return 0.0
    gains = float(np.sum(p[p > 0]))
    losses = -float(np.sum(p[p < 0]))
    if losses <= 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def expectancy(tradePnls: np.ndarray) -> float:
    """1 거래당 기대수익.

    Capabilities:
        거래별 손익 평균. 양수 = 흑자 전략, 음수 = 적자.

    Parameters
    ----------
    tradePnls : np.ndarray
        거래별 손익 배열.

    Returns
    -------
    float
        거래당 평균 손익 (원). 거래 없으면 0.0.

    Example:
        >>> expectancy(np.array([1, -1, 2, -0.5]))
        0.375

    Guide:
        expectancy × 거래 빈도 = 연간 기대 수익. 수수료 차감 후 인용.

    When:
        백테스트 metrics + AI 거래당 기대값 답변.

    How:
        mean(p).

    Requires:
        tradePnls 비어있지 않음.

    Raises:
        없음.

    See Also:
        - profitFactor : 총합 비율
        - sharpe : 위험 조정

    AIContext:
        expectancy × 빈도 = 연간 기대 수익, 수수료 차감 후 인용.
    """
    p = np.asarray(tradePnls, dtype=np.float64)
    if len(p) == 0:
        return 0.0
    return float(np.mean(p))


def turnover(positions: np.ndarray) -> float:
    """포지션 회전율 — 절대값 변화 합계.

    Capabilities:
        포지션 시계열 절대값 차분 합 → 매매 빈도. 거래비용 추정 + 전략 활성도.

    Parameters
    ----------
    positions : np.ndarray
        시점별 포지션 크기 배열.

    Returns
    -------
    float
        총 회전 (절대값 변화 합, 배). 표본 < 2 이면 0.0.

    Example:
        >>> turnover(np.array([0, 1, 0, 1]))
        3.0

    Guide:
        연간 turnover × spread/2 = 대략 transaction cost. 1000% / 년 = 일평균 4%
        회전 (highfreq).

    When:
        백테스트 비용 추정 + AI 전략 빈도 답변.

    How:
        sum(|diff(positions)|).

    Requires:
        positions ≥ 2.

    Raises:
        없음.

    See Also:
        - exposure : 포지션 유지 비율

    AIContext:
        turnover × spread = 대략 거래비용 추정.
    """
    p = np.asarray(positions, dtype=np.float64)
    if len(p) < 2:
        return 0.0
    return float(np.sum(np.abs(np.diff(p))))


def exposure(positions: np.ndarray) -> float:
    """포지션 유지 비율 — non-zero 비중.

    Capabilities:
        포지션 시계열에서 |p| > 0 시점 비율. 시장 노출 정량화.

    Parameters
    ----------
    positions : np.ndarray
        시점별 포지션 크기 배열.

    Returns
    -------
    float
        포지션 유지 비율 (0~1). 포지션 없으면 0.0.

    Example:
        >>> exposure(np.array([0, 1, 0, 1]))
        0.5

    Guide:
        exposure 1.0 = 항상 시장 노출 (buy & hold). 0.3 = 70% 캐쉬 보유.
        annualReturn 인용 시 exposure 보정.

    When:
        백테스트 + AI 시장 노출 답변.

    How:
        sum(|p| > 1e-9) / n.

    Requires:
        positions 비어있지 않음.

    Raises:
        없음.

    See Also:
        - turnover : 변화량

    AIContext:
        exposure 보정 후 annualReturn 인용 (캐쉬 보유 기간 반영).
    """
    p = np.asarray(positions, dtype=np.float64)
    if len(p) == 0:
        return 0.0
    return float(np.sum(np.abs(p) > 1e-9) / len(p))
