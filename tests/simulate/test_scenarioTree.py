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


def testDecisionNetworkEmitsLayeredGraph():
    # GUI 표시 계약: 신경망식 층상 그래프(입력→회사→업종→결정) 데이터 방출 (GUI 미포함)
    base = pl.DataFrame({"code": ["a", "b"], "score": [1.0, 2.0]})
    betas = pl.DataFrame({"code": ["a", "b"], "rateBeta": [None, None], "fxBeta": [0.0, 0.0], "oilBeta": [3.0, -1.0]})
    imap = pl.DataFrame({"code": ["a", "b"], "industry": ["energy", "air"]})
    net = st.decisionNetwork(base, betas, imap, {"oil": 0.3}, topK=1)
    layers = {n["layer"] for n in net["nodes"]}
    assert {"input", "company", "industry", "output"} <= layers  # 4층 신경망식
    assert net["stats"]["nCompanies"] == 2 and net["stats"]["nInput"] == 1
    oilEdges = [e for e in net["edges"] if e["from"] == "macro:oil"]
    assert len(oilEdges) == 2  # 매크로→회사 발화 엣지 (weight=측정 베타)
    assert abs(next(e["weight"] for e in oilEdges if e["to"] == "company:a") - 3.0) < 1e-9  # 엣지 가중 = oilBeta
    comp = {n["id"]: n for n in net["nodes"] if n["layer"] == "company"}
    assert "inTopK" in comp["company:a"] and net["stats"]["nEdges"] > 0  # 회사 노드 결정진입 표시 + 엣지 실재
    import json

    json.dumps(net)  # GUI fetch 소비 계약: 직렬화 가능


def testRateScenarioUnitsMatchSeries():
    # 2026-07-06 단위 결함 가드: rate 시리즈는 percent 단위(0.5~5.25)라 +100bp = 1.0 (0.01 아님)
    assert st.DEFAULT_SCENARIOS["rateHike"].shocks["rate"] == 1.0
    betas = pl.DataFrame({"code": ["a"], "rateBeta": [0.02], "fxBeta": [0.0], "oilBeta": [0.0]})
    r = st.scenarioResponse(betas, st.DEFAULT_SCENARIOS["rateHike"].shocks)
    assert abs(r["response"][0] - 0.02) < 1e-12  # +100bp x beta(per %p) = 유효 반응 (0.00% 결함 재발 방지)


def _elasticityFixtures():
    """업종 A = 유가 완전 추종 성장, 업종 B = 반대부호 성장 (공통차감 후에도 차등 노출 잔존)."""
    import math

    dOil = [
        0.10,
        -0.08,
        0.12,
        -0.05,
        0.07,
        -0.11,
        0.09,
        -0.04,
        0.06,
        -0.09,
        0.13,
        -0.03,
        0.08,
        -0.07,
        0.05,
        -0.10,
        0.11,
        -0.06,
        0.04,
        -0.02,
    ]
    oilLevel, cur = [], 100.0
    for d in dOil:
        cur *= math.exp(d)
        oilLevel.append(cur)
    # 분기 첫날 관측 매크로 (2019Q1 ~ 2023Q4 = 20분기)
    dates, oilSeries = [], []
    q = 0
    for y in range(2019, 2024):
        for qn in range(4):
            dates.append(f"{y}{qn * 3 + 1:02d}15")
            oilSeries.append(oilLevel[q])
            q += 1
    macro = pl.DataFrame({"date": dates, "rate": [3.0] * 20, "fx": [1300.0] * 20, "oil": oilSeries})
    rows = []
    periods = [(y, qn) for y in range(2019, 2024) for qn in range(1, 5)]
    for ind, sign, codes in (("A", 1.0, [f"a{i}" for i in range(5)]), ("B", -1.0, [f"b{i}" for i in range(5)])):
        for i, code in enumerate(codes):
            vals: list[float] = []
            for q in range(20):
                if q < 4:
                    vals.append(100.0 + q)
                else:
                    noise = 0.002 * ((q * 7 + i * 3) % 5 - 2)  # 결정론 소음 (완전적합 se=0 방지)
                    vals.append(vals[q - 4] * math.exp(sign * 0.5 * dOil[q] + noise))
            for q, (y, qn) in enumerate(periods):
                rows.append(
                    {
                        "code": code,
                        "period": f"{y}Q{qn}",
                        "rceptDate": f"{y}{qn * 2 + 3:02d}15",
                        "account": "revenue",
                        "amount": vals[q],
                    }
                )
    grid = pl.DataFrame(rows)
    imap = pl.DataFrame(
        {"code": [f"a{i}" for i in range(5)] + [f"b{i}" for i in range(5)], "industry": ["A"] * 5 + ["B"] * 5}
    )
    return grid, macro, imap


def testIndustryElasticityTGateAndConditionalE():
    grid, macro, imap = _elasticityFixtures()
    el = st.industryElasticity(grid, macro, imap, minQuarters=10, minFirms=3, tGate=3.0)
    pairs = {(r["industry"], r["factor"]): r["beta"] for r in el.iter_rows(named=True)}
    assert ("A", "oil") in pairs and pairs[("A", "oil")] > 0  # 완전 추종 = 통과 + 양 베타
    assert ("B", "oil") in pairs and pairs[("B", "oil")] < 0  # 반대 노출 = 음 베타
    assert not any(f == "rate" for _, f in pairs)  # 무변동 팩터 = 무통과 (조작 없음)
    # 조건부 E: A 만 이동, 비인증 업종/타계정 무변 + conditioned 플래그
    from dartlab.simulate import estimate as est

    e = est.estimateQuarters(grid, asOf="20240101", horizonQ=1)
    elA = el.filter(pl.col("industry") == "A")
    ce = st.conditionalE(e, {"oil": 0.30}, elA, imap)
    a0 = ce.filter(pl.col("code") == "a0").row(0, named=True)
    b0 = ce.filter(pl.col("code") == "b0").row(0, named=True)
    base = e.filter(pl.col("code") == "a0").row(0, named=True)
    assert a0["conditioned"] and not b0["conditioned"]  # 인증 업종만 조건화 (기권 명시)
    import math

    assert abs(a0["p50"] - base["p50"] * math.exp(a0["shiftLog"])) < 1e-9  # 분위 exp 이동
    assert abs(b0["p50"] - e.filter(pl.col("code") == "b0").row(0, named=True)["p50"]) < 1e-12  # 무변
