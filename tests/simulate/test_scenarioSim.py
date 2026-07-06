"""상관 시나리오 몬테카를로 : 합성 데이터로 공분산·조건부·MC·역사스트레스 (순수 유닛, 네트워크 0).

Covers:
- factorCovariance: 팩터 동반이동 구조 추정.
- conditionalShock: 한 팩터 고정 → 나머지 역사적 동반 조건부 기대 (더 깊은 시나리오).
- monteCarloDecision: 상관 충격 분포 → top-K 진입 확률 + 결정론.
- historicalStressShocks: 실제 극단 구간 동반이동.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl

from dartlab.simulate import scenarioSim as ss


def _corrMacro(n: int = 200):
    """유가와 환율이 양의 상관(fx 변화 = 0.5 x oil 변화 + 노이즈), 금리 평탄인 합성 매크로."""
    dates = [(date(2025, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]
    rng = np.random.default_rng(7)
    oilRet = rng.normal(0.0, 0.02, n)
    fxRet = 0.5 * oilRet + rng.normal(0.0, 0.004, n)
    oil = 100.0 * np.cumprod(1 + oilRet)
    fx = 1300.0 * np.cumprod(1 + fxRet)
    return pl.DataFrame({"date": dates, "oil": oil, "fx": fx, "rate": [3.0] * n})


def testFactorCovarianceCapturesCoMovement():
    cov = ss.factorCovariance(_corrMacro())
    factors = cov["factors"]
    oi, fi = factors.index("oil"), factors.index("fx")
    assert cov["cov"][oi, fi] > 0  # 유가·환율 양의 동반 (독립 아님)


def testConditionalShockFillsCoMovers():
    cov = ss.factorCovariance(_corrMacro())
    sh = ss.conditionalShock(cov, "oil", -0.30)
    assert sh["oil"] == -0.30  # 고정 팩터
    # fx 변화 = 0.5 x oil 이므로 조건부 fx ~ 0.5 x (-0.30) = -0.15 (독립 충격의 0 이 아님)
    assert abs(sh["fx"] - (-0.15)) < 0.04  # 역사적 동반 채움
    # 무조건(rate 무상관) rate 는 ~0
    assert abs(sh["rate"]) < 0.01


def _betas():
    # 극단 oil 베타(a=+10, d=-10) 양극단 + 미미(b=+1, c=-1). 대칭 충격에서 극단이 top 차지.
    return pl.DataFrame(
        {
            "code": ["a", "b", "c", "d"],
            "rateBeta": [None, None, None, None],
            "fxBeta": [0.0, 0.0, 0.0, 0.0],
            "oilBeta": [10.0, 1.0, -1.0, -10.0],
        }
    )


def testMonteCarloDecisionTopKProbAndDeterminism():
    cov = ss.factorCovariance(_corrMacro())
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [0.0, 0.0, 0.0, 0.0]})
    mc = ss.monteCarloDecision(base, _betas(), cov, n=1000, topK=1, macroTilt=3.0, seed=0)
    assert set(mc.columns) >= {"code", "topKProb", "respP5", "respP95"}
    probs = {r["code"]: r["topKProb"] for r in mc.iter_rows(named=True)}
    # 유가↑엔 a(+10), 유가↓엔 d(-10) top1 = 극단 베타가 대칭 시나리오 대부분 차지 (미미 b·c 는 드묾)
    assert probs["a"] > probs["b"] and probs["d"] > probs["c"]
    assert probs["a"] + probs["d"] > 0.8
    assert mc.filter(pl.col("code") == "a")["respP95"][0] > mc.filter(pl.col("code") == "a")["respP5"][0]  # 꼬리 폭
    # 결정론: 같은 seed = 같은 결과
    mc2 = ss.monteCarloDecision(base, _betas(), cov, n=1000, topK=1, macroTilt=3.0, seed=0)
    assert mc["topKProb"].to_list() == mc2["topKProb"].to_list()


def testHistoricalStressShocksCaptureEpisodes():
    # 유가 급락 구간을 심은 합성 매크로 → oilCrash 에피소드가 유가 음의 이동 포착
    dates = [(date(2025, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(60)]
    oil = [100.0] * 30 + [60.0] * 30  # 중간에 -40% 급락
    hs = ss.historicalStressShocks(
        pl.DataFrame({"date": dates, "oil": oil, "fx": [1300.0] * 60, "rate": [3.0] * 60}), horizon=20
    )
    assert "oilCrash" in hs
    assert hs["oilCrash"]["oil"] < -0.1  # 급락 구간 = 유가 음의 이동
