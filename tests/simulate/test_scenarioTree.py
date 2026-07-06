"""시나리오 디시전 트리 : 합성 데이터로 반응·산업집계·트리·책임팩터·결정론 (순수 유닛, 네트워크 0).

Covers:
- scenarioResponse: 회사 반응 = Σ 노출베타 x 충격 (측정 베타 소비).
- industryResponse: 업종 집계 (산업층).
- adjustedScores: base(z) + macroTilt x 반응(z) 랭킹 결합.
- buildDecisionTree: 진입/이탈 + 책임 팩터 역추적 + 누적 분기 + 결정론.
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate import scenarioTree as st


def _betas():
    return pl.DataFrame(
        {
            "code": ["a", "b", "c", "d"],
            "rateBeta": [None, None, None, None],
            "fxBeta": [0.0, 0.0, 0.0, 0.0],
            "oilBeta": [5.0, -5.0, 0.0, 0.0],
        }
    )


def testScenarioResponseFromBetas():
    resp = st.scenarioResponse(_betas(), {"oil": 0.5})
    byCode = {r["code"]: r["response"] for r in resp.iter_rows(named=True)}
    assert abs(byCode["a"] - 2.5) < 1e-9  # oilBeta 5 x shock 0.5
    assert abs(byCode["b"] + 2.5) < 1e-9  # 음의 oilBeta = 반대 반응
    assert abs(byCode["c"]) < 1e-9  # 무노출 = 무반응 (손 가정 아닌 측정 베타)


def testIndustryResponseAggregates():
    imap = pl.DataFrame({"code": ["a", "b", "c", "d"], "industry": ["energy", "energy", "air", "air"]})
    ir = st.industryResponse(_betas(), imap, {"oil": 1.0})
    byInd = {r["industry"]: r["response"] for r in ir.iter_rows(named=True)}
    assert byInd["energy"] == 0.0  # median(5, -5) = 0 (혼합 업종)
    # 순수 방향 업종 테스트: 전부 양 베타
    imap2 = pl.DataFrame({"code": ["a", "c"], "industry": ["oilUp", "oilUp"]})
    b2 = pl.DataFrame({"code": ["a", "c"], "rateBeta": [None, None], "fxBeta": [0.0, 0.0], "oilBeta": [4.0, 2.0]})
    ir2 = st.industryResponse(b2, imap2, {"oil": 1.0})
    assert ir2["response"][0] == 3.0  # median(4, 2)


def testAdjustedScoresZSpace():
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [0.0, 0.0, 0.0, 10.0]})
    adj = st.adjustedScores(base, _betas(), {"oil": 0.5}, macroTilt=3.0)
    m = {r["code"]: r["adjusted"] for r in adj.iter_rows(named=True)}
    # a: 낮은 base + 높은 oil 반응, macroTilt 3 이면 d(높은 base·무반응) 추월
    assert m["a"] > m["d"]
    # macroTilt 0 이면 base 만 = d 최고
    adj0 = st.adjustedScores(base, _betas(), {"oil": 0.5}, macroTilt=0.0)
    m0 = {r["code"]: r["adjusted"] for r in adj0.iter_rows(named=True)}
    assert m0["d"] == max(m0.values())


def testBuildDecisionTreeEntrantsAndResponsible():
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [0.0, 0.0, 0.0, 10.0]})
    branches = [st.ScenarioBranch("oilUp", "유가+50%", {"oil": 0.5})]
    tree = st.buildDecisionTree(base, _betas(), branches, topK=1, macroTilt=3.0)
    byId = {n["branchId"]: n for n in tree["nodes"]}
    assert byId["root"]["topK"] == ["d"]  # 무충격 = 최고 base
    oil = byId["oilUp"]
    assert oil["topK"] == ["a"]  # 유가 충격 = 고 oilBeta 진입
    assert "a" in oil["entrants"] and "d" in oil["exiters"]  # a 진입·d 이탈
    assert oil["responsible"]["a"]["factor"] == "oil"  # 책임 팩터 = 유가 (역추적)
    assert oil["responsible"]["a"]["contribution"] > 0  # 양의 기여
    assert {e["parent"] for e in tree["edges"]} == {"root"}  # 루트 직속


def testCumulativeShocksNested():
    # 중첩 분기: oilUp -> (oilUp + rateHike) 경로는 충격 누적
    branches = [
        st.ScenarioBranch("oilUp", "유가+30%", {"oil": 0.3}),
        st.ScenarioBranch("oilUpRate", "유가+30%·금리+1%", {"rate": 0.01}, parent="oilUp"),
    ]
    byId = {b.branchId: b for b in branches}
    cs = st._cumulativeShocks(byId, "oilUpRate")
    assert cs == {"oil": 0.3, "rate": 0.01}  # 부모 충격 + 자신 증분 누적
    ordered = st._topoOrder(branches)
    assert [b.branchId for b in ordered].index("oilUp") < [b.branchId for b in ordered].index("oilUpRate")


def testBuildDecisionTreeDeterministic():
    base = pl.DataFrame({"code": ["a", "b", "c", "d"], "score": [1.0, 2.0, 3.0, 4.0]})
    branches = st.scenariosToBranches(["oilShockUp", "oilShockDown"])
    t1 = st.buildDecisionTree(base, _betas(), branches, topK=2, macroTilt=1.0)
    t2 = st.buildDecisionTree(base, _betas(), branches, topK=2, macroTilt=1.0)
    assert [n["topK"] for n in t1["nodes"]] == [n["topK"] for n in t2["nodes"]]  # 같은 입력 = 같은 트리


def testScenariosToBranchesSkipsBaseline():
    br = st.scenariosToBranches(["baseline", "oilShockUp", "rateHike"])
    ids = {b.branchId for b in br}
    assert "baseline" not in ids  # 무충격 baseline 은 루트라 분기 제외
    assert ids == {"oilShockUp", "rateHike"}
    assert all(b.parent is None for b in br)  # 단층 = 루트 직속
