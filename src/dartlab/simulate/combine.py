"""표면 결합 : AdaHedge 파라미터 프리 온라인 결합 (L2.5 simulate).

표면 가중을 백테스트 적합이 아니라 온라인 학습으로 정한다 (06 §7b). 표면 = 전문가, 매주 각
표면이 손실을 입고, 곱셈 가중으로 결합한다. AdaHedge 는 학습률까지 과거 손실의 결정론 함수라
조정 나사가 0 이다: 이것이 "커브핏 없음"의 구조적 증명이다. 보장 = 어떤 분포 가정 없이 사후
최강 표면 대비 누적 후회 O(sqrt(T ln N)). 주간 지연 피드백은 sqrt2 배 이내.

주장 규율: 상대 보장(최강 표면 추종)이지 수익 보장이 아니다 (never-claim 상속). 손실은
사전 봉인한 함수([0,1] 클립)여야 한다. 표면 추가·은퇴는 sleeping-experts 규약 (본 골격은
고정 표면 집합, 동적 집합은 확장).

Layer: L2.5 simulate. numpy 만 의존.
"""

from __future__ import annotations

import numpy as np


def adaHedge(losses: np.ndarray) -> dict:
    """AdaHedge: (T, N) 주간 표면 손실 → 매주 가중 + 누적 후회 (학습률 자가조정).

    Args:
        losses: (nWeeks, nSurfaces) 각 주 각 표면의 손실 (권장 [0,1] 클립. 예 판독 Brier
            또는 net 재무 손실). NaN 은 그 주 그 표면 결측(가중 유지).

    Returns:
        {"weights": (T, N) 각 주 사용 가중, "combinedLoss": (T,), "regret": float 사후 최강
        표면 대비 누적 후회, "finalWeights": (N,)}. 결정론: 같은 손실 = 같은 가중 (재현 가능).
    """
    T, N = losses.shape
    L = np.zeros(N)  # 표면별 누적 손실
    delta = 0.0  # 누적 mixability gap (학습률 자가조정의 심장)
    weights = np.zeros((T, N))
    combined = np.zeros(T)
    for t in range(T):
        eta = np.log(N) / delta if delta > 0 else np.inf
        if np.isinf(eta):
            w = np.ones(N) / N
        else:
            shifted = -eta * (L - L.min())
            w = np.exp(shifted)
            w = w / w.sum()
        weights[t] = w
        lt = losses[t]
        valid = ~np.isnan(lt)
        ltFilled = np.where(valid, lt, 0.0)
        hedgeLoss = float(np.sum(w * ltFilled))
        combined[t] = hedgeLoss
        # mixability gap: hedge 손실 vs mix 손실 (AdaHedge 자가조정 갱신). eta=inf(첫 라운드,
        # 균등 가중)면 mix 손실 = 최소 손실 (극단 집중 극한), gap = 평균-최소 > 0 로 부트스트랩.
        if np.isinf(eta):
            mixLoss = float(ltFilled[valid].min()) if valid.any() else hedgeLoss
        else:
            mixLoss = -np.log(np.sum(w * np.exp(-eta * ltFilled))) / eta
        delta += max(hedgeLoss - mixLoss, 0.0)
        L = L + ltFilled
    bestSurfaceLoss = float(L.min())
    regret = float(combined.sum() - bestSurfaceLoss)
    return {
        "weights": weights,
        "combinedLoss": combined,
        "regret": regret,
        "finalWeights": weights[-1] if T else np.ones(N) / N,
    }
