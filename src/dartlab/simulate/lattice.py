"""시나리오 격자 : 재결합 삼항 격자 + beam 가지치기 + 격자 위 정확확률 결정 (L2.5 simulate).

MCTS형 "수천 가정 확대 → 가지치기 → 결정 수렴"의 정직 구현 (14-mcts-lattice-idea). 매크로 팩터
(유가·환율·금리)가 마디마다 {-1,0,+1}σ 삼항 분기하되 같은 누적상태를 병합(재결합)해 폭발을
억제한다: 순진 경로 트리 27^T (T=8 = 2.8e11) 대비 (2T+1)^3 상한 + beam 가지치기 = 실측 2,000
상태·손실 질량 0.16%·1.4e8배 억제. 분기 확률은 상관 정규밀도 커널로 동반이동을 담고(실측
P(oil+·fx+) 0.097 > P(oil+·fx-) 0.052), 드리프트는 0 (A 개념검증에서 VAR 가 OOS 랜덤워크에
패배 = RW+Σ 설계 확정, 14 §7).

결정은 잎 확률로 정확 가중한다: 회사 반응 = 측정 노출베타 x 잎 충격 (벌크 1행렬), top-K 진입
확률·확률가중 분위(p5/p95)·최악 5% 구간(bad worlds) 생존확률. RNG 0 = 몬테카를로와 달리 샘플
오차 없는 정확 이산 분포 + byte 결정론 (실측 MC 와 topKProb 상관 0.991 상호검증). 정직 프레임:
이기는 미래 하나를 찾지 않는다. 분포·강건성(대다수 잎 생존)·최악구간 생존만 낸다 (14 §1).

Layer: L2.5 simulate. scenarioSim(공분산)·table(베타·시총)·numpy·polars 만 의존 (하향).
"""

from __future__ import annotations

import itertools

import numpy as np
import polars as pl

from dartlab.simulate.factors import baseScoreExpr, factorBetaMap


def _moveKernel(cov: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """3^k 삼항 이동 {-1,0,1}^k 에 상관 정규밀도 가중 → (moves, probs). 동반이동이 커널에 들어감."""
    k = cov.shape[0]
    sd = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    corr = cov / np.outer(sd, sd)
    corr = np.where(np.isfinite(corr), corr, np.eye(k))
    moves = np.array(list(itertools.product((-1, 0, 1), repeat=k)), dtype=float)
    inv = np.linalg.pinv(corr + np.eye(k) * 1e-9)
    dens = np.exp(-0.5 * np.einsum("ij,jk,ik->i", moves, inv, moves))
    return moves, dens / dens.sum()


def growLattice(covariance: dict, *, steps: int = 8, stepDays: int = 5, beamWidth: int = 2000) -> dict:
    """재결합 격자 성장 → 잎 상태 분포. 결정론(RNG 0), 폭발 억제 = 재결합 + beam 가지치기.

    Args:
        covariance: scenarioSim.factorCovariance 산출 ({"factors","mean","cov"}). 드리프트(mean)는
            쓰지 않는다 (A 기각 = RW+Σ, 14 §7).
        steps: 마디 수 (기본 8 = 8주 지평).
        stepDays: 마디당 거래일 (공분산 스케일).
        beamWidth: 상태 상한. 초과 시 저확률 상태 컷 (손실 질량은 prunedMass 로 정직 보고).

    Returns:
        {"factors", "shocks" (nStates x k 누적 충격), "probs" (nStates, 합 <= 1), "stateCounts"
        (스텝별 상태 수 곡선), "prunedMass" (가지치기 손실 질량), "unitShock" (그리드 1칸 스케일)}.
        unitShock 은 커널 분산 모멘트 매칭: sqrt(cov_ii x stepDays / v_i).

    Guide:
        - 8주 지평 격자: growLattice(factorCovariance(macroDaily())) -> latticeDecision 입력.
        - 폭발 검증: stateCounts 가 (2T+1)^k 상한/beam 에 눌려있으면 정상.
    """
    factors, cov = covariance["factors"], np.asarray(covariance["cov"])
    k = len(factors)
    moves, mp = _moveKernel(cov)
    movesInt = moves.astype(int)
    v = (mp[:, None] * moves**2).sum(axis=0)
    unitShock = np.sqrt(np.clip(np.diag(cov), 0, None) * stepDays / np.clip(v, 1e-12, None))
    states: dict[tuple, float] = {tuple([0] * k): 1.0}
    counts: list[int] = []
    prunedMass = 0.0
    for _ in range(steps):
        new: dict[tuple, float] = {}
        for s, p in states.items():
            for mv, q in zip(movesInt, mp):
                ns = tuple(a + b for a, b in zip(s, mv))
                new[ns] = new.get(ns, 0.0) + p * q
        if len(new) > beamWidth:
            items = sorted(new.items(), key=lambda kv: kv[1], reverse=True)[:beamWidth]
            prunedMass += sum(new.values()) - sum(v2 for _, v2 in items)
            new = dict(items)
        states = new
        counts.append(len(states))
    grid = np.array(list(states.keys()), dtype=float)
    probs = np.array(list(states.values()))
    return {
        "factors": list(factors),
        "shocks": grid * unitShock[None, :],
        "probs": probs,
        "stateCounts": counts,
        "prunedMass": float(prunedMass),
        "unitShock": unitShock,
    }


def winsorizeBetas(betaByCode: pl.DataFrame, *, q: float = 0.01) -> pl.DataFrame:
    """노출베타 횡단 winsorize (양측 q 분위 클립) → 극단 베타 소형주 쏠림 완화 (정밀도 부채).

    Args:
        betaByCode: table.macroBetaByCodeWide 산출. q: 클립 분위 (기본 1%/99%).

    Returns:
        같은 스키마, 베타 컬럼만 [q, 1-q] 분위로 클립. 전결측 컬럼은 그대로 (0 대체 금지).
    """
    out = betaByCode
    for col in factorBetaMap().values():
        if col in out.columns and out[col].null_count() < out.height:
            lo, hi = out[col].quantile(q), out[col].quantile(1 - q)
            out = out.with_columns(pl.col(col).clip(lo, hi).alias(col))
    return out


def _baseCol(baseScores: pl.DataFrame) -> pl.Expr:
    """baseScores 점수 컬럼 인식 (factors.baseScoreExpr SSOT 위임)."""
    return baseScoreExpr(baseScores)


def latticeDecision(
    baseScores: pl.DataFrame,
    betaByCode: pl.DataFrame,
    lattice: dict,
    *,
    topK: int = 10,
    macroTilt: float = 1.0,
    stressQuantile: float = 0.05,
) -> pl.DataFrame:
    """격자 잎 확률로 정확 가중한 결정 → (code, topKProb, respMed, respP5, respP95, stressTopKProb).

    Args:
        baseScores: (code, score|consensus) 기저 판독 합의. betaByCode: 노출베타 (winsorizeBetas 권장).
        lattice: growLattice 산출. topK: 결정 종목 수. macroTilt: 매크로 반응 가중 (가정 축).
        stressQuantile: 최악 구간 확률질량 (기본 5% = bad worlds).

    Returns:
        topKProb 내림차순. topKProb = 잎 분포에서 top-K 진입 정확확률 (강건성 = 대다수 잎 생존).
        respP5/P95 = 확률가중 이산 분위 (꼬리). stressTopKProb = 유니버스 중앙 반응 최하
        stressQuantile 질량 상태(bad worlds)에서의 진입확률 (최악구간 생존). RNG 0 = byte 결정론.

    Guide:
        - 강건 top: latticeDecision(base, winsorizeBetas(betas), growLattice(cov)).head(topK).
        - 스트레스 생존 픽: stressTopKProb 높은 종목 = 나쁜 세계에서도 top 유지.
    """
    factors = lattice["factors"]
    j = baseScores.select("code", base=_baseCol(baseScores)).join(betaByCode, on="code", how="inner")
    codes = j["code"].to_list()
    schema = {
        "code": pl.Utf8,
        "topKProb": pl.Float64,
        "respMed": pl.Float64,
        "respP5": pl.Float64,
        "respP95": pl.Float64,
        "stressTopKProb": pl.Float64,
    }
    if not codes:
        return pl.DataFrame(schema=schema)
    baseArr = j["base"].to_numpy()
    betaMat = np.column_stack([j[factorBetaMap()[f]].fill_null(0.0).to_numpy() for f in factors])
    probs = lattice["probs"] / lattice["probs"].sum()  # 가지치기 잔여 질량 조건부 정규화
    resp = betaMat @ lattice["shocks"].T  # (nCodes x nStates)
    baseZ = (baseArr - baseArr.mean()) / (baseArr.std() + 1e-12)
    respZ = (resp - resp.mean(axis=0)) / (resp.std(axis=0) + 1e-12)
    adj = baseZ[:, None] + float(macroTilt) * respZ
    k = min(topK, len(codes))
    thresh = np.partition(adj, -k, axis=0)[-k]
    inTop = adj >= thresh[None, :]
    topKProb = inTop @ probs
    # bad worlds = 유니버스 중앙 반응 최하 stressQuantile 질량 상태 → 그 안 진입확률 (생존)
    sev = np.median(resp, axis=0)
    order = np.argsort(sev)
    cum = np.cumsum(probs[order])
    bad = order[: int(np.searchsorted(cum, stressQuantile) + 1)]
    badP = probs[bad] / max(probs[bad].sum(), 1e-300)
    stressTopKProb = inTop[:, bad] @ badP
    # 확률가중 이산 분위
    ordR = np.argsort(resp, axis=1)
    sortedResp = np.take_along_axis(resp, ordR, axis=1)
    cumP = np.cumsum(probs[ordR], axis=1)

    def qtile(q: float) -> np.ndarray:
        """확률가중 이산 분위: 누적확률이 q 를 처음 넘는 상태의 반응값."""
        idx = (cumP < q).sum(axis=1).clip(0, resp.shape[1] - 1)
        return sortedResp[np.arange(len(codes)), idx]

    return pl.DataFrame(
        {
            "code": codes,
            "topKProb": topKProb,
            "respMed": qtile(0.5),
            "respP5": qtile(0.05),
            "respP95": qtile(0.95),
            "stressTopKProb": stressTopKProb,
        },
        schema=schema,
    ).sort("topKProb", descending=True)


def hardenedTopK(
    baseScores: pl.DataFrame, decision: pl.DataFrame, *, topK: int = 15, candidateExtra: int = 10
) -> list[str]:
    """리스크 오버레이 결정규칙: base 상위 (topK+extra) 후보에서 매크로 꼬리(respP5) 최악 extra 개
    제거 → 경화 top-K (역사 검증 산물, 14 §9).

    역사 실측(2018~2026, 72표본 주 forward 8주): 매크로 틸트로 랭킹을 기울이면 유해(+0.47%·p5
    -12.3%)하지만, 이 오버레이는 평균을 올리고(+1.45% -> +1.82%) 주간 p5 꼬리를 40% 얕게 한다
    (-7.78% -> -4.68%). 격자의 정직 역할 = 방향 예측이 아니라 "덜 죽는 결정".

    Args:
        baseScores: (code, score|consensus) 기저 결정 (인증부호 합의 권장).
        decision: latticeDecision 산출 (respP5 소비).
        topK: 최종 종목 수. candidateExtra: 후보 여유분 = 제거 수.

    Returns:
        경화 top-K 종목코드 리스트 (base 점수순 후보 중 매크로 꼬리 얕은 순 유지). 결정론.

    Guide:
        - board 경화: hardenedTopK(baseScores, latticeDecision(base, betas, lat)).
    """
    cand = (
        baseScores.select("code", base=_baseCol(baseScores))
        .sort("base", descending=True)
        .head(topK + candidateExtra)
        .join(decision.select("code", "respP5"), on="code", how="left")
    )
    return cand.sort("respP5", descending=True, nulls_last=True).head(topK)["code"].to_list()
