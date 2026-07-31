"""Event Study 공용 계산.

analysis와 quant가 함께 쓰는 CAR/BHAR 계산을 L1.5 synth에 둔다.
"""

from __future__ import annotations

import numpy as np


def _marketModel(stockReturns: np.ndarray, marketReturns: np.ndarray) -> tuple[float, float, float] | None:
    """OLS alpha, beta, residual sigma. 추정 불가면 None.

    예전에는 표본 부족·특이행렬에서 ``(0.0, 1.0, 0.01)`` 을 돌려줬다. 이 값은 추정
    결과와 구분되지 않은 채 alpha·beta·sigma 로 보고됐고, 무엇보다 고정 sigma 가
    t 값과 유의성 판정의 분모가 돼 "유의 abnormal drift" 라는 결론을 만들었다.
    추정하지 못한 것은 추정값이 아니므로 호출자가 실패로 다루게 한다.
    """
    if len(stockReturns) < 20 or len(marketReturns) != len(stockReturns):
        return None
    X = np.column_stack([np.ones(len(marketReturns)), marketReturns])
    try:
        beta, *_ = np.linalg.lstsq(X, stockReturns, rcond=None)
    except np.linalg.LinAlgError:
        return None
    a, b = float(beta[0]), float(beta[1])
    resid = stockReturns - X @ beta
    sigma = float(resid.std(ddof=2))
    return a, b, max(sigma, 1e-6)


def calcCAR(
    stockReturns: np.ndarray,
    marketReturns: np.ndarray,
    *,
    eventIdx: int,
    estimationWindow: tuple[int, int] = (-120, -30),
    eventWindow: tuple[int, int] = (-5, 5),
) -> dict:
    """Cumulative Abnormal Return - MacKinlay event-study 표준.

    시장모형을 추정하지 못하면(추정 구간 20 관측 미만 또는 특이행렬) 값을 만들지 않고
    다른 실패와 같은 ``{"error": ...}`` 를 돌려준다.
    """
    n = len(stockReturns)
    est_lo = eventIdx + estimationWindow[0]
    est_hi = eventIdx + estimationWindow[1]
    ev_lo = eventIdx + eventWindow[0]
    ev_hi = eventIdx + eventWindow[1]
    if est_lo < 0 or ev_hi >= n:
        return {"error": "window out of range"}

    s_est = np.asarray(stockReturns[est_lo : est_hi + 1], dtype=np.float64)
    m_est = np.asarray(marketReturns[est_lo : est_hi + 1], dtype=np.float64)
    model = _marketModel(s_est, m_est)
    if model is None:
        return {"error": f"market model not estimable (estimation obs={len(s_est)}, 최소 20 필요 또는 특이행렬)"}
    alpha, beta, sigma = model

    s_ev = np.asarray(stockReturns[ev_lo : ev_hi + 1], dtype=np.float64)
    m_ev = np.asarray(marketReturns[ev_lo : ev_hi + 1], dtype=np.float64)
    expected = alpha + beta * m_ev
    ar = s_ev - expected
    car = float(ar.sum())
    L = len(ar)
    scar = car / (sigma * np.sqrt(L)) if sigma > 0 else 0.0

    return {
        "eventIdx": eventIdx,
        "alpha": round(alpha, 5),
        "beta": round(beta, 3),
        "sigma": round(sigma, 5),
        "ar": ar,
        "car": round(car, 4),
        "carPct": round(car * 100, 2),
        "scar": round(scar, 3),
        "tStat": round(scar, 3),
        "isSignificant": bool(abs(scar) > 1.96),
        "windowL": L,
        "interpretation": (
            f"event idx {eventIdx}, CAR {round(car * 100, 2)}% (L={L}d), "
            f"t={round(scar, 2)}. " + ("유의 abnormal drift." if abs(scar) > 1.96 else "통계 비유의.")
        ),
    }


def calcBHAR(
    stockReturns: np.ndarray,
    marketReturns: np.ndarray,
    *,
    eventIdx: int,
    holdWindow: int = 60,
) -> dict:
    """Buy-and-Hold Abnormal Return."""
    n = len(stockReturns)
    hi = eventIdx + holdWindow
    if hi >= n:
        return {"error": "window out of range"}
    s = stockReturns[eventIdx + 1 : hi + 1]
    m = marketReturns[eventIdx + 1 : hi + 1]
    if len(s) < 5:
        return {"error": "too few obs"}
    bhar_s = float(np.prod(1 + s) - 1)
    bhar_m = float(np.prod(1 + m) - 1)
    bhar = bhar_s - bhar_m
    return {
        "eventIdx": eventIdx,
        "holdWindow": holdWindow,
        "bharStock": round(bhar_s * 100, 2),
        "bharMarket": round(bhar_m * 100, 2),
        "bhar": round(bhar * 100, 2),
        "interpretation": (
            f"event {eventIdx} 후 {holdWindow}일 BHAR {round(bhar * 100, 2)}% "
            f"(종목 {round(bhar_s * 100, 1)}%, 시장 {round(bhar_m * 100, 1)}%)."
        ),
    }
