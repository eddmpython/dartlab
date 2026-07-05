"""가정 sweep : 다중검정 통제 통계 (CSCV-PBO·Deflated Sharpe·강건 선정) (L2.5 simulate).

가정 격자(표면 가중·게이트·임계) 위의 성과 행렬에서 다중검정 신기루를 통제한다 (06 §5).
선정은 최고 성적 가정이 아니라 강건성(대다수 가정에서 반복 상위, median)으로, sweep 마다
PBO·열화 기울기·DSR 을 자동 산출한다 (실측: edge 0 신호 위 최고 가정 +0.50%/주 vs 중앙값
+0.04%/주 = 선택 편향. PBO 로 정량화). 전부 numpy 자급 (외부 의존 0).

- ``cscvPbo`` : Bailey-López de Prado CSCV 로 backtest overfitting 확률 + OOS 열화 기울기.
- ``deflatedSharpe`` : False Strategy 정리로 N 시도 보정 Sharpe (유효 N = config 클러스터 수).
- ``robustSelection`` : 가정 대다수에서 반복 상위인 종목 (median 강건성, 최고 가정 인용 금지).

Layer: L2.5 simulate. numpy 만 의존.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

_EULER = 0.5772156649015329


def cscvPbo(perf: np.ndarray, sBlocks: int = 16) -> dict:
    """CSCV: perf (configs x periods) → PBO + OOS 열화 기울기 + P(OOS 손실).

    Args:
        perf: (nConfigs, nPeriods) 가정별 기간별 성과 (예 주간 초과수익).
        sBlocks: 대칭 분할 블록 수 (짝수). C(sBlocks, sBlocks/2) 조합 전수.

    Returns:
        {"pbo", "nCombos", "oosDegradeSlope", "pOosLoss"}. PBO 0.5 = IS 최고가정이 OOS 동전던지기.
    """
    nC, nW = perf.shape
    valid = ~np.isnan(perf)
    perf0 = np.where(valid, perf, 0.0)
    edges = np.linspace(0, nW, sBlocks + 1).astype(int)
    bSum = np.stack([perf0[:, edges[b] : edges[b + 1]].sum(axis=1) for b in range(sBlocks)], axis=1)
    bSq = np.stack([(perf0[:, edges[b] : edges[b + 1]] ** 2).sum(axis=1) for b in range(sBlocks)], axis=1)
    bN = np.stack([valid[:, edges[b] : edges[b + 1]].sum(axis=1) for b in range(sBlocks)], axis=1)

    def sharpe(mask: np.ndarray) -> np.ndarray:
        """블록 마스크 구간의 config 별 Sharpe (블록 합·제곱합 사전계산 재사용)."""
        n = bN[:, mask].sum(axis=1)
        m = bSum[:, mask].sum(axis=1) / np.maximum(n, 1)
        v = bSq[:, mask].sum(axis=1) / np.maximum(n, 1) - m**2
        return m / np.sqrt(np.maximum(v, 1e-12))

    lambdas, isBest, oosBest = [], [], []
    for combo in combinations(range(sBlocks), sBlocks // 2):
        inMask = np.zeros(sBlocks, dtype=bool)
        inMask[list(combo)] = True
        rIs, rOos = sharpe(inMask), sharpe(~inMask)
        nStar = int(np.argmax(rIs))
        omega = np.sum(rOos <= rOos[nStar]) / (len(rOos) + 1)
        omega = min(max(omega, 1e-6), 1 - 1e-6)
        lambdas.append(np.log(omega / (1 - omega)))
        isBest.append(rIs[nStar])
        oosBest.append(rOos[nStar])
    lam = np.array(lambdas)
    isB, oosB = np.array(isBest), np.array(oosBest)
    slope = float(np.polyfit(isB, oosB, 1)[0]) if len(isB) > 1 else float("nan")
    return {
        "pbo": float((lam <= 0).mean()),
        "nCombos": len(lam),
        "oosDegradeSlope": slope,
        "pOosLoss": float((oosB < 0).mean()),
    }


def deflatedSharpe(perf: np.ndarray, *, nEff: int | None = None) -> dict:
    """Deflated Sharpe: 선택된(최고) 가정의 Sharpe 를 N 시도 노이즈 천장 대비 보정.

    Args:
        perf: (nConfigs, nPeriods) 성과 행렬.
        nEff: 유효 시도 수 (None = config 수). config 상관 클러스터 수를 넣는 것이 정직.

    Returns:
        {"srMax", "sr0", "dsr", "nEff"}. dsr>=0.95 만 발간 승격 (06 §5).
    """
    means = np.nanmean(perf, axis=1)
    stds = np.nanstd(perf, axis=1)
    srs = means / np.where(stds > 0, stds, np.nan)
    srs = srs[~np.isnan(srs)]
    if srs.size < 2:
        return {"srMax": float("nan"), "sr0": float("nan"), "dsr": float("nan"), "nEff": nEff or srs.size}
    n = nEff or srs.size
    varSr = float(np.var(srs, ddof=1))
    from math import erf, log, sqrt

    def normInv(p: float) -> float:
        """표준정규 역 CDF (Acklam 근사, scipy 외부 의존 회피)."""
        a = [
            -39.6968302866538,
            220.946098424521,
            -275.928510446969,
            138.357751867269,
            -30.6647980661472,
            2.50662827745924,
        ]
        b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857]
        c = [
            -0.00778489400243029,
            -0.322396458041136,
            -2.40075827716184,
            -2.54973253934373,
            4.37466414146497,
            2.93816398269878,
        ]
        d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742]
        pl_ = 0.02425
        if p < pl_:
            q = sqrt(-2 * log(p))
            return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
                (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
            )
        if p <= 1 - pl_:
            q = p - 0.5
            r = q * q
            return (
                (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
                * q
                / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
            )
        q = sqrt(-2 * log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )

    sr0 = sqrt(varSr) * ((1 - _EULER) * normInv(1 - 1.0 / n) + _EULER * normInv(1 - 1.0 / (n * np.e)))
    srMax = float(np.nanmax(srs))
    nObs = perf.shape[1]
    dsr = 0.5 * (1 + erf(((srMax - sr0) * sqrt(max(nObs - 1, 1))) / sqrt(2)))
    return {"srMax": srMax, "sr0": float(sr0), "dsr": float(dsr), "nEff": n}


def robustSelection(
    configScores: np.ndarray, codes: list[str], *, topQ: float = 0.9, robustFrac: float = 0.8
) -> list[str]:
    """가정 대다수에서 반복 상위인 종목 (median 강건성. 최고 가정 top 인용 금지).

    Args:
        configScores: (nCodes, nConfigs) 종목별 가정별 점수.
        codes: 종목코드 (행 순서).
        topQ: 각 가정에서 상위로 치는 분위 (기본 0.9).
        robustFrac: 이 비율 이상 가정에서 상위여야 강건 (기본 0.8).

    Returns:
        강건 상위 종목코드.
    """
    nConfigs = configScores.shape[1]
    hit = np.zeros(configScores.shape[0])
    for c in range(nConfigs):
        cut = np.quantile(configScores[:, c], topQ)
        hit += (configScores[:, c] >= cut).astype(int)
    robust = np.array(codes)[hit >= nConfigs * robustFrac]
    return list(robust)
