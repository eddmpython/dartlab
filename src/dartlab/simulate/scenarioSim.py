"""시나리오 몬테카를로 : 상관 매크로 충격 분포 + 조건부 시나리오 (L2.5 simulate).

디시전 트리(이산 분기)의 상위 모델. 매크로 팩터(유가·환율·금리)는 독립이 아니라 함께 움직인다
(한국은 원유 수입국이라 유가↓ = 원화 강세 = 금리 인하 동반). 이 모듈은 그 공분산을 역사에서
추정해 두 가지를 낸다:

1. 조건부 시나리오(더 깊은 시나리오): 한 팩터를 고정하면(유가 -30%) 나머지 팩터는 역사적 동반
   이동의 조건부 기대값으로 자동으로 채운다. 독립 충격(환율=0·금리=0)보다 현실적인 완결 시나리오.
2. 상관 몬테카를로(더 효율·고급): 손 이산 분기 몇 개 대신 수천 개 상관 충격 경로를 샘플해, 회사별
   "top-K 진입 확률"과 반응 꼬리(p5/p95) 분포를 낸다. 공간을 전수로 덮으니 효율적이고, 점 branch가
   아니라 확률이라 고급이며, 강건 종목(대다수 시나리오에서 상위)을 sweep 없이 직접 낸다.

전부 결정론(seed 고정 numpy). Layer: L2.5 simulate. table(macroDaily·betas)·scenarioTree(반응 정의)·numpy.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from dartlab.simulate.factors import factorBetaMap, factorNames
from dartlab.simulate.factors import macroChange as _factorChange


def _allFactors() -> tuple[str, ...]:
    """팩터 축 (factors 레지스트리 SSOT, 호출 시점 순회 = 등록 팩터 자동흡수)."""
    return tuple(factorNames())


def factorChanges(macroDaily: pl.DataFrame) -> pl.DataFrame:
    """매크로 일별 → 팩터 변화 (date, d_oil, d_fx, d_rate). 유가·환율 수익률, 금리 차분."""
    m = macroDaily.sort("date")
    present = [f for f in _allFactors() if f in m.columns]
    exprs = [_factorChange(f).alias(f"d_{f}") for f in present]
    return m.with_columns(exprs).select("date", *[f"d_{f}" for f in present])


def factorCovariance(macroDaily: pl.DataFrame, *, window: int = 750) -> dict:
    """팩터 변화 공분산 + 평균 → {"factors", "mean", "cov"}. 최근 window 거래일, 팩터 동반이동 구조.

    Args:
        macroDaily: table.macroDaily 산출 (date, oil, fx, rate). window: 추정 트레일링 거래일.

    Returns:
        {"factors": [...], "mean": np.ndarray, "cov": np.ndarray}. cov = 팩터 변화 공분산 (오프대각 =
        동반이동, 예 oil-fx 양 = 유가↑ 원화약세). 표본<30 이면 무상관 폴백(대각 미세 분산).
    """
    fc = factorChanges(macroDaily).tail(window).drop_nulls()
    cols = [c for c in fc.columns if c.startswith("d_")]
    factors = [c[2:] for c in cols]
    x = fc.select(cols).to_numpy()
    if x.shape[0] < 30 or not factors:
        return {"factors": factors, "mean": np.zeros(len(factors)), "cov": np.eye(len(factors)) * 1e-6}
    cov = np.atleast_2d(np.cov(x, rowvar=False))
    return {"factors": factors, "mean": x.mean(axis=0), "cov": cov}


def conditionalShock(covariance: dict, conditionFactor: str, conditionValue: float) -> dict[str, float]:
    """조건부 완결 시나리오: 한 팩터 고정 → 나머지 팩터 역사적 동반 조건부 기대 → shock dict (더 깊음).

    Args:
        covariance: factorCovariance 산출. conditionFactor: 고정 팩터 ("oil"|"fx"|"rate").
        conditionValue: 그 팩터 충격 (예 -0.30 = 유가 -30%).

    Returns:
        {factor: shock} 완결 시나리오. 고정 팩터 = conditionValue, 나머지 = E[o | c=value] =
        mean_o + (cov_oc/var_c)(value - mean_c). 독립 충격과 달리 팩터 동반이동을 반영 (유가 -30% 주면
        원화·금리도 역사적으로 동반한 만큼 채운다). 조건 팩터 부재/분산 0 이면 그 팩터만.

    Guide:
        - "유가 -30% 완결 시나리오" -> conditionalShock(cov, "oil", -0.30) -> {oil:-0.30, fx:..., rate:...}.
    """
    factors, mean, cov = covariance["factors"], covariance["mean"], covariance["cov"]
    if conditionFactor not in factors:
        return {conditionFactor: float(conditionValue)}
    ci = factors.index(conditionFactor)
    varC = float(cov[ci, ci])
    shock = {conditionFactor: float(conditionValue)}
    if varC <= 0:
        return shock
    for oi, f in enumerate(factors):
        if oi == ci:
            continue
        beta = float(cov[oi, ci]) / varC
        shock[f] = float(mean[oi] + beta * (conditionValue - mean[ci]))
    return shock


def _alignMatrices(baseScores: pl.DataFrame, betaByCode: pl.DataFrame, factors: list) -> tuple:
    """공통 종목으로 base·beta 정렬 → (codes, baseArr, betaMat[nCodes x nFactors]). null beta = 0."""
    baseCol = next((c for c in ("baseScore", "score", "consensus") if c in baseScores.columns), None)
    if baseCol is None:
        raise ValueError("baseScores 에 score/consensus 컬럼 필요")
    j = baseScores.select("code", base=pl.col(baseCol).cast(pl.Float64)).join(betaByCode, on="code", how="inner")
    codes = j["code"].to_list()
    baseArr = j["base"].to_numpy()
    betaMat = np.column_stack([j[factorBetaMap()[f]].fill_null(0.0).to_numpy() for f in factors])
    return codes, baseArr, betaMat


def monteCarloDecision(
    baseScores: pl.DataFrame,
    betaByCode: pl.DataFrame,
    covariance: dict,
    *,
    n: int = 2000,
    topK: int = 10,
    macroTilt: float = 1.0,
    horizon: int = 20,
    seed: int = 0,
) -> pl.DataFrame:
    """상관 시나리오 몬테카를로 → (code, topKProb, respMed, respP5, respP95, baseScore). 확률·꼬리 분포.

    Args:
        baseScores: (code, score|consensus) 기저 결정. betaByCode: table.macroBetaByCodeWide.
        covariance: factorCovariance 산출. n: 샘플 수. topK: 결정 종목 수. macroTilt: 매크로 가중.
        horizon: 충격 스케일 거래일 (분산 x horizon = 랜덤워크). seed: 결정론 RNG.

    Returns:
        (code, topKProb, respMed, respP5, respP95, baseScore) topKProb 내림차순. topKProb = 상관
        시나리오 분포에서 그 종목이 top-K 에 든 비율 = 강건성(대다수 시나리오 상위). respP5/P95 =
        반응 꼬리(하방/상방 위험). 이산 분기보다 효율(공간 전수)·고급(확률·꼬리)·강건(sweep 불요).

    Guide:
        - "상관 시나리오에서 강건한 top 종목" -> monteCarloDecision(base, betas, cov).head(topK).
    """
    factors, mean, cov = covariance["factors"], covariance["mean"], covariance["cov"]
    codes, baseArr, betaMat = _alignMatrices(baseScores, betaByCode, factors)
    nCodes = len(codes)
    empty = {
        "code": pl.Utf8,
        "topKProb": pl.Float64,
        "respMed": pl.Float64,
        "respP5": pl.Float64,
        "respP95": pl.Float64,
        "baseScore": pl.Float64,
    }
    if nCodes == 0 or not factors:
        return pl.DataFrame(schema=empty)
    rng = np.random.default_rng(seed)
    covReg = np.asarray(cov) * horizon + np.eye(len(factors)) * 1e-12  # 특이 공분산(금리 평탄 등) 방어
    shocks = rng.multivariate_normal(np.asarray(mean) * horizon, covReg, size=n)  # (n x nFactors) 상관 충격
    resp = betaMat @ shocks.T  # (nCodes x n) 회사별 시나리오 반응
    baseZ = (baseArr - baseArr.mean()) / (baseArr.std() + 1e-12)
    respZ = (resp - resp.mean(axis=0)) / (resp.std(axis=0) + 1e-12)
    adj = baseZ[:, None] + float(macroTilt) * respZ  # (nCodes x n)
    k = min(topK, nCodes)
    entry = np.zeros(nCodes)
    for j in range(n):
        entry[np.argpartition(adj[:, j], -k)[-k:]] += 1.0
    return pl.DataFrame(
        {
            "code": codes,
            "topKProb": entry / n,
            "respMed": np.median(resp, axis=1),
            "respP5": np.percentile(resp, 5, axis=1),
            "respP95": np.percentile(resp, 95, axis=1),
            "baseScore": baseArr,
        }
    ).sort("topKProb", descending=True)


def historicalStressShocks(macroDaily: pl.DataFrame, *, horizon: int = 20, k: int = 3) -> dict[str, dict]:
    """역사적 스트레스 에피소드 → 실제 팩터 동반이동 시나리오 (더 깊은 시나리오, 경험적).

    Args:
        macroDaily: table.macroDaily. horizon: 에피소드 창(거래일). k: 팩터별 상/하위 극단 에피소드 수.

    Returns:
        {episodeId: {factor: change}}. 각 팩터의 역사적 최악/최선 horizon 이동 구간의 실제 3팩터 동반
        변화를 시나리오로 (예 "oilCrash" = 역사상 유가 최악 구간의 실제 유가·환율·금리 동반 이동). 손
        가정이 아니라 역사가 준 완결 시나리오라 조건부보다도 현실적(비선형 동반 포함).

    Guide:
        - 역사 스트레스 테스트: historicalStressShocks(macroDaily) -> 실제 위기 구간 시나리오 dict.
    """
    m = macroDaily.sort("date")
    for f in _allFactors():
        if f in m.columns:
            chg = (pl.col(f) - pl.col(f).shift(horizon)) if f == "rate" else (pl.col(f) / pl.col(f).shift(horizon) - 1)
            m = m.with_columns(chg.alias(f"h_{f}"))
    hcols = [f"h_{f}" for f in _allFactors() if f"h_{f}" in m.columns]
    m = m.select("date", *hcols).drop_nulls()
    out: dict[str, dict] = {}
    for f in _allFactors():
        col = f"h_{f}"
        if col not in m.columns:
            continue
        srt = m.sort(col)
        for label, rows in (("Crash", srt.head(k)), ("Spike", srt.tail(k))):
            row = rows.tail(1) if label == "Crash" else rows.head(1)  # 가장 극단 1건
            if row.height:
                out[f"{f}{label}"] = {ff: float(row[f"h_{ff}"][0]) for ff in _allFactors() if f"h_{ff}" in m.columns}
    return out
