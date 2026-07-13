"""시나리오 격자 : 합성 데이터로 커널·성장·가지치기·결정·생존 다각 검증 (순수 유닛, 네트워크 0).

Covers:
- _moveKernel: 상관 동반이동이 분기 확률에 반영.
- growLattice: 질량 보존(무가지치기 합=1) + 재결합 상한((2T+1)^k) + beam 손실질량 정직 보고 + 결정론.
- latticeDecision: 정확확률 top-K + 확률가중 분위 + bad worlds 스트레스 생존 + MC 정합.
- winsorizeBetas / table.liquidUniverse: 정밀도 부채 헬퍼.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl

from dartlab.simulate import lattice as lt
from dartlab.simulate import scenarioSim as ss


def _corrCov(rho: float = 0.6) -> dict:
    """oil-fx 상관 rho, rate 미세분산 무상관인 합성 공분산 (factorCovariance 스키마)."""
    sd = np.array([0.02, 0.005, 0.001])
    corr = np.array([[1.0, rho, 0.0], [rho, 1.0, 0.0], [0.0, 0.0, 1.0]])
    return {"factors": ["oil", "fx", "rate"], "mean": np.zeros(3), "cov": corr * np.outer(sd, sd)}


def testMoveKernelCoMovement():
    moves, mp = lt._moveKernel(np.asarray(_corrCov(0.6)["cov"]))
    both = mp[(moves[:, 0] == 1) & (moves[:, 1] == 1)].sum()
    opp = mp[(moves[:, 0] == 1) & (moves[:, 1] == -1)].sum()
    assert both > opp  # 양의 상관 = 동반 상승이 반대 이동보다 확률 큼
    assert abs(mp.sum() - 1.0) < 1e-12  # 커널 정규화


def testGrowLatticeMassAndRecombination():
    lat = lt.growLattice(_corrCov(), steps=3, stepDays=5, beamWidth=10**9)  # 무가지치기
    assert abs(lat["probs"].sum() - 1.0) < 1e-9  # 질량 보존
    assert lat["prunedMass"] == 0.0
    assert lat["stateCounts"][-1] == 7**3  # 재결합 상한 (2T+1)^k, T=3·k=3 = 343 (27^3=19683 아님)
    assert lat["shocks"].shape == (343, 3)


def testGrowLatticeBeamPruningHonest():
    lat = lt.growLattice(_corrCov(), steps=5, stepDays=5, beamWidth=200)
    assert lat["stateCounts"][-1] <= 200  # beam 상한
    assert lat["prunedMass"] > 0  # 손실 질량 정직 보고
    assert abs(lat["probs"].sum() + lat["prunedMass"] - 1.0) < 1e-9  # 질량 회계 등식 (잔여+손실=1)
    # 충분 beam 이면 저확률 꼬리만 컷 = 커버리지 유지 (T=5 무가지치기 1331 상태 대비 600 유지)
    wide = lt.growLattice(_corrCov(), steps=5, stepDays=5, beamWidth=600)
    assert wide["probs"].sum() > 0.95


def testGrowLatticeDeterministic():
    a = lt.growLattice(_corrCov(), steps=4, beamWidth=300)
    b = lt.growLattice(_corrCov(), steps=4, beamWidth=300)
    assert np.array_equal(a["shocks"], b["shocks"]) and np.array_equal(a["probs"], b["probs"])  # RNG 0


def _betas4():
    """양극단(+10/-10) + 미미(+1/-1) oil 베타 4종목."""
    return pl.DataFrame(
        {
            "code": ["a", "b", "c", "d"],
            "rateBeta": [None, None, None, None],
            "fxBeta": [0.0, 0.0, 0.0, 0.0],
            "oilBeta": [10.0, 1.0, -1.0, -10.0],
        }
    )


def testLatticeDecisionProbAndTails():
    lat = lt.growLattice(_corrCov(), steps=6, beamWidth=2000)
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [0.0, 0.0, 0.0, 0.0]})
    dec = lt.latticeDecision(base, _betas4(), lat, topK=1, macroTilt=3.0)
    p = {r["code"]: r for r in dec.iter_rows(named=True)}
    assert p["a"]["topKProb"] > p["b"]["topKProb"] and p["d"]["topKProb"] > p["c"]["topKProb"]  # 극단이 top 차지
    assert p["a"]["topKProb"] + p["d"]["topKProb"] > 0.8  # 대칭 충격 = 양극단 합이 대부분
    assert p["a"]["respP95"] > 0 > p["a"]["respP5"]  # 노출 종목 꼬리 폭
    assert abs(p["b"]["respMed"]) < abs(p["a"]["respMed"]) + 1e-9  # 저베타 = 좁은 반응


def testLatticeStressSurvivalPrefersNegativeBeta():
    # 유니버스 중앙 반응이 유가를 따르도록 양베타 다수 구성 → bad worlds = 유가 하락 상태
    betas = pl.DataFrame(
        {
            "code": ["p5", "p2", "p1", "n5"],
            "rateBeta": [None] * 4,
            "fxBeta": [0.0] * 4,
            "oilBeta": [5.0, 2.0, 1.0, -5.0],
        }
    )
    base = pl.DataFrame({"code": ["p5", "p2", "p1", "n5"], "score": [0.0] * 4})
    lat = lt.growLattice(_corrCov(), steps=6, beamWidth=2000)
    dec = lt.latticeDecision(base, betas, lat, topK=1, macroTilt=3.0)
    p = {r["code"]: r for r in dec.iter_rows(named=True)}
    # 나쁜 세계(유가↓)에서는 음베타 n5 가 top1 = 스트레스 생존확률이 압도적
    assert p["n5"]["stressTopKProb"] > 0.9
    assert p["n5"]["stressTopKProb"] > p["p5"]["stressTopKProb"]


def testLatticeMatchesMonteCarloOnSynthetic():
    cov = _corrCov()
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [0.0, 0.0, 0.0, 0.0]})
    lat = lt.growLattice(cov, steps=6, stepDays=5, beamWidth=2000)
    dec = lt.latticeDecision(base, _betas4(), lat, topK=1, macroTilt=3.0)
    mc = ss.monteCarloDecision(base, _betas4(), cov, n=4000, topK=1, macroTilt=3.0, horizon=30, seed=0)
    j = dec.select("code", lp=pl.col("topKProb")).join(mc.select("code", mp=pl.col("topKProb")), on="code", how="inner")
    corr = np.corrcoef(j["lp"].to_numpy(), j["mp"].to_numpy())[0, 1]
    assert corr > 0.95  # 정확 격자와 표본 MC 상호검증 (같은 분포의 두 근사)


def testWinsorizeBetasClipsExtremes():
    b = pl.DataFrame(
        {
            "code": [f"c{i}" for i in range(100)],
            "rateBeta": [None] * 100,
            "fxBeta": [0.0] * 100,
            "oilBeta": [float(i) for i in range(99)] + [1e6],  # 극단 1건
        }
    )
    w = lt.winsorizeBetas(b, q=0.01)
    assert w["oilBeta"].max() < 1e6  # 극단 클립
    assert w["rateBeta"].null_count() == 100  # 전결측 컬럼 불변 (0 대체 금지)


def testHardenedTopKDropsMacroFragile():
    # base 상위 3 후보 중 매크로 꼬리(respP5) 최악 1개 제거 → 경화 top2 (리스크 오버레이 규칙)
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [4.0, 3.0, 2.0, 1.0]})
    dec = pl.DataFrame(
        {"code": ["a", "b", "c", "d"], "respP5": [-0.9, -0.1, -0.2, -0.05]}  # a = 가장 취약
    )
    picks = lt.hardenedTopK(base, dec, topK=2, candidateExtra=1)
    assert "a" not in picks  # base 1위여도 매크로 꼬리 최악이면 제거
    assert set(picks) == {"b", "c"}  # 후보(top3) 중 꼬리 얕은 2개 유지
    assert picks == lt.hardenedTopK(base, dec, topK=2, candidateExtra=1)  # 결정론


def testHardenedTopKTiesKeepDeterministicBaseOrder():
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [4.0, 3.0, 2.0, 1.0]})
    dec = pl.DataFrame({"code": ["d", "b", "a", "c"], "respP5": [0.0, 0.0, 0.0, 0.0]})
    assert lt.hardenedTopK(base, dec, topK=2, candidateExtra=2) == ["a", "b"]


def testLiquidUniverseFiltersSmallCaps(monkeypatch):
    from dartlab.simulate import table

    d = [(date(2026, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(2)]
    caps = pl.DataFrame(
        {
            "date": [d[0]] * 4 + [d[1]] * 4,
            "code": ["a", "b", "c", "d"] * 2,
            "mktcap": [100.0, 200.0, 300.0, 400.0] * 2,
        }
    )
    monkeypatch.setattr(table, "marketCap", lambda baseDir=None: caps)
    u = table.liquidUniverse(d[1], mktcapQuantile=0.3)
    assert "a" not in u and {"c", "d"} <= u  # 하위 30% 컷


def testFactorMarginalsWeightedQuantiles():
    import numpy as np

    from dartlab.simulate import lattice as lt

    # 3상태 격자: -0.1(25%) / 0(50%) / +0.1(25%) → p50=0, p5=-0.1, p95=+0.1 (가중 분위)
    fake = {
        "factors": ["oil"],
        "shocks": np.array([[-0.1], [0.0], [0.1]]),
        "probs": np.array([0.25, 0.5, 0.25]),
    }
    m = lt.factorMarginals(fake)
    assert m["oil"][50] == 0.0 and m["oil"][5] == -0.1 and m["oil"][95] == 0.1
    vals = [m["oil"][p] for p in (5, 25, 50, 75, 95)]
    assert vals == sorted(vals)  # 단조
