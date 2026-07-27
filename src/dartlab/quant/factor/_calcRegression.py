"""quant/factor/calc 헬퍼 — CAPM fallback · multi-OLS · 해석 문장 · rank.

quant/factor/calc.py 가 1089 줄 god module 이라 헬퍼 분리.
identity 보존을 위해 calc.py 가 본 모듈에서 re-export 한다.

수치/해석 헬퍼:
- _capmFallback — factor build 실패 시 1-factor CAPM
- _multiOls — 다변수 OLS + t-stats + residuals
- _rank1d — 1D array → tie-averaged rank
- _interpret — factor loading 정성 해석 list
- _interpretFactorSharpe — Sharpe + factor → 한 줄
- _interpretIC — ICIR + factor → 예측력 한 줄
- _interpretRiskDecomp — systematic share + factor 기여 → 한 줄
"""

from __future__ import annotations

import numpy as np


def _capmFallback(stockCode: str, market: str, sr: np.ndarray, br: np.ndarray) -> dict:
    """팩터 빌드 실패 시 1-factor CAPM."""
    ml = min(len(sr), len(br))
    if ml < 30:
        return {"error": "공통 기간 부족"}
    y = sr[-ml:]
    x = br[-ml:]
    cov = float(np.cov(y, x, ddof=1)[0, 1])
    var = float(np.var(x, ddof=1))
    beta = cov / var if var > 0 else 0
    alpha = float(np.mean(y) - beta * np.mean(x))
    yhat = alpha + beta * x
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return {
        "stockCode": stockCode,
        "market": market,
        "model": "CAPM-fallback",
        "info": "factorBuild 실패 → 1-factor CAPM으로 fallback",
        "dataPoints": int(ml),
        "MKT": {"loading": round(beta, 4), "tstat": None},
        "alpha": round(alpha * 252, 4),
        "rSquared": round(r2, 4),
    }


def _multiOls(y, X):
    """다변수 OLS + t-stats + residuals.

    Returns:
        (betas, alpha, r2, t_stats, residuals). residuals 는 알파 시계열
        (팩터 제거 후 잔여 일별 수익). IR 계산의 원료.
    """
    n, k = X.shape
    X_aug = np.column_stack([np.ones(n), X])
    try:
        beta = np.linalg.lstsq(X_aug, y, rcond=None)[0]
        y_hat = X_aug @ beta
        resid = y - y_hat
        ss_res = float(np.sum(resid**2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        t_stats = None
        if n > k + 1:
            mse = ss_res / (n - k - 1)
            try:
                cov = mse * np.linalg.inv(X_aug.T @ X_aug)
                se = np.sqrt(np.diag(cov))
                t_stats = beta / se
                t_stats = t_stats[1:]
            except np.linalg.LinAlgError:
                pass

        return beta[1:], float(beta[0]), r2, t_stats, resid
    except np.linalg.LinAlgError:
        return np.zeros(k), 0.0, 0.0, None, None


def _interpret(result: dict, names: list[str]) -> list[str]:
    """factor loading → 정성 해석 list."""
    interp = []
    for name in names:
        info = result.get(name)
        if not isinstance(info, dict):
            continue
        ld = info.get("loading", 0)
        ts = info.get("tstat")
        sig = ts is not None and abs(ts) > 2.0

        if name == "MKT":
            if ld > 1.2:
                interp.append(f"공격적 시장 민감도 (β={ld:.2f})")
            elif ld < 0.8:
                interp.append(f"방어적 (β={ld:.2f})")
        elif sig:
            labels = {
                "SMB": ("소형주 특성", "대형주 특성"),
                "HML": ("고BM(가치)", "저BM(성장)"),
                "RMW": ("고수익성(profitable)", "저수익성(weak)"),
                "CMA": ("보수적 투자(conservative)", "공격적 투자(aggressive)"),
            }
            pos, neg = labels.get(name, ("양", "음"))
            interp.append(pos if ld > 0 else neg)

    return interp


def _interpretFactorSharpe(sharpe: float, factor: str) -> str:
    """Sharpe ratio + 팩터 방향 → 정성 평가 한 줄."""
    if sharpe > 1.5:
        level = "매우 강한 alpha"
    elif sharpe > 1.0:
        level = "강한 alpha"
    elif sharpe > 0.5:
        level = "약한 alpha"
    elif sharpe > 0:
        level = "유의미하지 않음"
    elif sharpe > -0.5:
        level = "역방향 약함"
    else:
        level = "역방향 강함"

    direction_map = {
        "smb": ("소형주 프리미엄", "대형주 프리미엄"),
        "hml": ("가치주 프리미엄", "성장주 프리미엄"),
        "rmw": ("고수익성 프리미엄", "저수익성 프리미엄"),
        "cma": ("보수적 투자 프리미엄", "공격적 투자 프리미엄"),
    }
    pos, neg = direction_map.get(factor, (f"{factor.upper()} 프리미엄", f"{factor.upper()} 역방향"))
    direction = pos if sharpe > 0 else neg
    return f"{level} ({direction})"


def _interpretRiskDecomp(sysShare: float, factorContrib: dict) -> str:
    """systematic 비중 + 최대 기여 팩터 → 정성 평가."""
    if sysShare > 70:
        kind = "팩터 의존 (시장 분산효과 큼)"
    elif sysShare > 50:
        kind = "팩터 + 고유 균형"
    elif sysShare > 30:
        kind = "고유 리스크 우세"
    else:
        kind = "거의 idiosyncratic (팩터 노출 작음)"
    if not factorContrib:
        return kind
    top = max(factorContrib.items(), key=lambda x: abs(x[1]))
    return f"{kind} | 최대 팩터 기여: {top[0]} ({top[1]:+.1f}%)"


def _rank1d(arr: np.ndarray) -> np.ndarray:
    """1D array → rank (ties averaged, 1-based normalized to 0..1 scale irrelevant)."""
    order = arr.argsort()
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(len(arr), dtype=np.float64)
    uniq, inv = np.unique(arr, return_inverse=True)
    if len(uniq) < len(arr):
        sums = np.zeros(len(uniq), dtype=np.float64)
        counts = np.zeros(len(uniq), dtype=np.float64)
        np.add.at(sums, inv, ranks)
        np.add.at(counts, inv, 1.0)
        avg = sums / counts
        ranks = avg[inv]
    return ranks


def _interpretIC(icir: float, factor: str, *, nDays: int | None = None) -> str:
    """ICIR + 팩터 → 정성 한 줄. 단년도 sample 한계 caveat 포함."""
    a = abs(icir)
    if a > 2.0:
        level = "매우 강한 예측력 (sample 제한 주의)"
    elif a > 1.0:
        level = "강한 예측력"
    elif a > 0.5:
        level = "중간 예측력"
    elif a > 0.2:
        level = "약한 예측력"
    else:
        level = "노이즈 수준"
    sign = "+" if icir > 0 else "-"
    suffix = ""
    if nDays is not None and nDays < 30:
        suffix = " [단기 sample]"
    return f"{level} ({sign}{factor}){suffix}"


__all__ = [
    "_capmFallback",
    "_interpret",
    "_interpretFactorSharpe",
    "_interpretIC",
    "_interpretRiskDecomp",
    "_multiOls",
    "_rank1d",
]
