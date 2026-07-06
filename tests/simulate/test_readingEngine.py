"""판독 엔진 R1 : 합성 데이터로 계약·의견화·채점·사이클 (순수 유닛, 네트워크 0).

Covers:
- readingLedger: 봉인 라운드트립 + append-only(봉인 키 중복 거부) + unscored 필터.
- opine: 연속 표면 극단 방향(상위=+1·하위=-1·중간=0) + 이벤트 방향화 사전 적용.
- readingScorecard: 진짜 엣지 표면은 |t| 큼, 노이즈 표면은 factor-zoo 미달 라벨. 방향화 게이트.
- readingCycle: issueReadings 봉인 → scoreReadingsDue 채점 왕복 (주입 행렬).
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from dartlab.simulate import opine, readingCycle, readingLedger, readingScorecard, sweep
from dartlab.simulate.reading import Reading


def _reading(code: str, surface: str, direction: int, score: float) -> Reading:
    return Reading(code, "KR", surface, 202607, "20260213", 5, direction, score)


def testLedgerRoundtripAndAppendOnly(tmp_path):
    rows = [_reading("005930", "fund.ep", 1, 0.9), _reading("000660", "fund.ep", -1, 0.1)]
    readingLedger.appendReadings(rows, issuedAt="2026-02-13T00:00", issuedLive=True, baseDir=tmp_path)
    got = readingLedger.readReadings(week=202607, baseDir=tmp_path)
    assert got.height == 2
    assert set(got["direction"].to_list()) == {1, -1}
    with pytest.raises(ValueError):  # 봉인 키 중복 거부
        readingLedger.appendReadings(rows, issuedAt="2026-02-13T00:00", issuedLive=True, baseDir=tmp_path)
    assert readingLedger.unscoredReadings(baseDir=tmp_path).height == 2


def testReadingRefsAndConditionRoundtrip(tmp_path):
    r = Reading(
        "005930",
        "KR",
        "fund.ep",
        202607,
        "20260213",
        5,
        1,
        0.9,
        refs=("dart.finance", "fundDaily"),
        condition="rate_hike",
    )
    readingLedger.appendReadings([r], issuedAt="t", issuedLive=True, baseDir=tmp_path)
    got = readingLedger.readReadings(baseDir=tmp_path)
    assert got["refs"][0] == "dart.finance fundDaily"  # 근거 참조 봉인 (재계산 계약)
    assert got["condition"][0] == "rate_hike"  # 조건 태그 봉인 (레짐 조건부 채점용)


def testOpineDirections():
    # 5종목 fund.ep 랭크: 최상위 +1, 최하위 -1, 중간 0
    fundM = pl.DataFrame(
        {
            "code": ["a", "b", "c", "d", "e"],
            "week": [202607] * 5,
            "ep": [0.01, 0.02, 0.03, 0.04, 0.05],
            "bm": [0.1] * 5,
        }
    )
    priceM = pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "week": pl.Int64,
            "ret5": pl.Float64,
            "mom20x5": pl.Float64,
            "volShock": pl.Float64,
            "high52": pl.Float64,
        }
    )
    eventM = pl.DataFrame({"code": ["a"], "week": [202607], "reportType": ["유상증자결정"]})
    r = opine.opine(priceM, fundM, eventM, directionByType={"유상증자결정": -1})
    ep = r.filter(pl.col("surface") == "fund.ep").sort("ep" if "ep" in r.columns else "score")
    epByCode = {row["code"]: row["direction"] for row in r.filter(pl.col("surface") == "fund.ep").iter_rows(named=True)}
    assert epByCode["e"] == 1 and epByCode["a"] == -1  # 최고 E/P 상방, 최저 하방
    ev = r.filter(pl.col("surface") == "event.dilutionGovernance")
    assert ev.height == 1 and ev["direction"][0] == -1  # 유상증자 = 하방


def testScorecardSeparatesEdgeFromNoise():
    # 20종목 x 40주. edge 표면 score 는 초과와 동행, noise 표면 score 는 무관.
    # 주별 공통 노이즈로 std>0 (결정론 아님) → t 유한, edge 가 noise 보다 큼.
    codes = [f"c{i:02d}" for i in range(20)]
    rows, labs = [], []
    for w in range(202601, 202641):
        wkNoise = ((w % 11) - 5) * 0.003  # 주별 공통 성분 (횡단면 초과엔 상쇄되나 표본 변동 유발)
        for i, code in enumerate(codes):
            signal = (i / 19 - 0.5) * 0.04  # 랭크 상위일수록 초과 큼
            idio = (((i * 17 + w) % 7) - 3) * 0.004  # 종목·주 특이 노이즈
            ex = signal + idio + wkNoise
            labs.append({"code": code, "week": w, "exRaw": ex, "exNeutral": ex})
            rows.append(
                {"code": code, "week": w, "surface": "edge", "direction": 0, "score": i / 19, "abstainReason": None}
            )
            rows.append(
                {
                    "code": code,
                    "week": w,
                    "surface": "noise",
                    "direction": 0,
                    "score": ((i * 13 + w * 3) % 20) / 19,
                    "abstainReason": None,
                }
            )
    card = readingScorecard.scorecard(pl.DataFrame(rows), pl.DataFrame(labs))
    byS = {r["surface"]: r for r in card.iter_rows(named=True)}
    assert byS["edge"]["t"] > byS["noise"]["t"]  # 엣지 표면이 노이즈보다 t 큼
    assert byS["edge"]["spread"] > 0  # 상위 랭크 = 양의 초과
    assert byS["edge"]["verdict"] == "통과"  # 강한 엣지는 factor-zoo 허들 통과


def testDeriveEventDirectionsGate():
    # 강한 음의 타입(200건 med -2%) 은 방향화, 약한 타입(50건) 은 게이트 탈락
    rows, labs = [], []
    for w in range(202601, 202641):
        for k in range(6):  # 240 강한 음 이벤트
            code = f"s{k}"
            labs.append({"code": code, "week": w, "exRaw": -0.02, "exNeutral": -0.02})
            rows.append({"code": code, "week": w, "reportType": "유상증자결정"})
    eventM = pl.DataFrame(rows)
    labels = pl.DataFrame(labs).unique(["code", "week"])
    dirs = readingScorecard.deriveEventDirections(eventM, labels)
    assert dirs.get("유상증자결정") == -1  # 게이트 통과 + 하방


def testIssueAndScoreCycle(tmp_path):
    weekEnd = pl.DataFrame({"week": [202607], "date": ["20260213"]})
    fundM = pl.DataFrame(
        {
            "code": ["a", "b", "c", "d", "e"],
            "week": [202607] * 5,
            "ep": [0.01, 0.02, 0.03, 0.04, 0.05],
            "bm": [0.02] * 5,
        }
    )
    priceM = pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "week": pl.Int64,
            "ret5": pl.Float64,
            "mom20x5": pl.Float64,
            "volShock": pl.Float64,
            "high52": pl.Float64,
        }
    )
    eventM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    n = readingCycle.issueReadings(
        week=202607,
        baseDir=tmp_path,
        matrices=(weekMap, weekEnd, priceM, fundM, eventM),
        directionByType={},
    )
    assert n == 10  # 5종목 x 2 재무 표면
    labels = pl.DataFrame(
        {
            "code": ["a", "b", "c", "d", "e"],
            "week": [202607] * 5,
            "exRaw": [-0.02, -0.01, 0.0, 0.01, 0.02],
            "exNeutral": [-0.02, -0.01, 0.0, 0.01, 0.02],
        }
    )
    scored = readingCycle.scoreReadingsDue(baseDir=tmp_path, labels=labels)
    assert scored == 10
    assert readingLedger.unscoredReadings(baseDir=tmp_path).height == 0  # 전부 채점됨


def testAbstainFirstClassAndCompleteness(tmp_path):
    # 거래 유니버스 5종목, 재무는 3종목만 → 재무 표면에서 2종목 기권행 발행 (완전성 강제)
    weekEnd = pl.DataFrame({"week": [202607], "date": ["20260213"]})
    priceM = pl.DataFrame(
        {
            "code": ["a", "b", "c", "d", "e"],
            "week": [202607] * 5,
            "ret5": [0.01, 0.02, 0.03, 0.04, 0.05],
            "mom20x5": [0.0] * 5,
            "volShock": [0.0] * 5,
            "high52": [0.9] * 5,
            "maxRet20": [0.05] * 5,
        }
    )
    fundM = pl.DataFrame({"code": ["a", "b", "c"], "week": [202607] * 3, "ep": [0.01, 0.02, 0.03], "bm": [0.02] * 3})
    eventM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    readingCycle.issueReadings(
        week=202607, baseDir=tmp_path, matrices=(weekMap, weekEnd, priceM, fundM, eventM), directionByType={}
    )
    led = readingLedger.readReadings(baseDir=tmp_path)
    abstain = led.filter(pl.col("abstainReason").is_not_null())
    assert abstain.height == 4  # fund.ep + fund.bm 각 2종목(d,e) 기권 = 4행 (price 4신호는 전종목 발행)
    assert set(abstain["abstainReason"].unique().to_list()) == {"noData"}
    # 완전성: fund.ep 표면에 유니버스 5종목 전부 (판독 3 + 기권 2) 기록 = silent 누락 0
    epRows = led.filter(pl.col("surface") == "fund.ep")
    assert set(epRows["stockCode"].to_list()) == {"a", "b", "c", "d", "e"}
    assert epRows.filter(pl.col("score").is_null()).height == 2  # 기권 2 (score null, 0 대체 아님)


def testScorecardReportsAbstainRate():
    rows, labs = [], []
    for w in range(202601, 202641):
        for i, code in enumerate([f"c{i:02d}" for i in range(10)]):
            labs.append({"code": code, "week": w, "exNeutral": (i / 9 - 0.5) * 0.03})
            if i < 6:  # 6종목 판독, 4종목 기권 → 기권률 0.4
                rows.append({"code": code, "week": w, "surface": "s", "direction": 0, "score": i / 9})
            else:
                rows.append({"code": code, "week": w, "surface": "s", "direction": 0, "score": None})
    card = readingScorecard.scorecard(pl.DataFrame(rows), pl.DataFrame(labs))
    r = card.filter(pl.col("surface") == "s").row(0, named=True)
    assert abs(r["abstainRate"] - 0.4) < 1e-9  # 기권률 채점 (4/10)


def testSweepPboOnNoiseIsHalf():
    # edge 0 순수 노이즈: PBO ~0.5 (IS 최고 가정이 OOS 동전던지기), 강건 선정 0
    rng = np.random.default_rng(11)
    perf = rng.normal(0, 0.01, size=(120, 480))
    r = sweep.cscvPbo(perf, sBlocks=10)
    assert 0.3 < r["pbo"] < 0.7  # 노이즈면 0.5 근방
    assert r["oosDegradeSlope"] < 0.5  # IS 최고가 OOS 로 열화
    d = sweep.deflatedSharpe(perf, nEff=40)
    assert d["dsr"] < 0.95  # 노이즈는 발간 승격 불가


def testSweepRobustSelectionPrefersConsistent():
    # 한 종목만 모든 가정에서 최상위 → 강건 선정에 포함, 나머지 노이즈는 배제
    rng = np.random.default_rng(3)
    scores = rng.normal(size=(50, 100))
    scores[0, :] = 10.0  # code0 은 모든 가정 최상위
    robust = sweep.robustSelection(scores, [f"c{i}" for i in range(50)])
    assert "c0" in robust and len(robust) < 10


def testAdaHedgeConvergesToBestSurface():
    # 표면0 이 명확히 우월 → 가중 수렴 + 후회 << sqrt(T ln N) 경계
    from dartlab.simulate.combine import adaHedge

    rng = np.random.default_rng(7)
    T, N = 200, 4
    losses = rng.uniform(0.4, 0.6, size=(T, N))
    losses[:, 0] = rng.uniform(0.1, 0.3, size=T)
    r = adaHedge(losses)
    assert r["finalWeights"][0] == r["finalWeights"].max()  # 우월 표면 최대 가중
    assert r["regret"] < (T * np.log(N)) ** 0.5  # 후회 경계 준수


def testBoardConsensusAndRedFlagGate():
    from dartlab.simulate import board

    r = pl.DataFrame(
        {
            "code": ["a", "a", "b", "b", "c", "c"],
            "week": [202607] * 6,
            "surface": ["fund.ep", "event.dilutionGovernance"] * 3,
            "direction": [1, 0, 1, -1, -1, 0],
            "score": [0.9, 0.5, 0.85, 0.1, 0.1, 0.5],
        }
    )
    b = board.board100(r, surfaceWeights={"fund.ep": 2.0, "event.dilutionGovernance": 1.0}, n=3)
    byCode = {row["code"]: row["consensus"] for row in b.iter_rows(named=True)}
    assert byCode["a"] == max(byCode.values())  # 재무 상방·이벤트 중립 = 최고 합의
    top = board.applyGates(b, redFlagCodes={"b"}, n=2)
    assert "b" not in top["code"].to_list()  # red-flag 제외


def _mats(week):
    weekEnd = pl.DataFrame({"week": [week], "date": ["20260213"]})
    fundM = pl.DataFrame(
        {"code": ["a", "b", "c", "d", "e"], "week": [week] * 5, "ep": [0.01, 0.02, 0.03, 0.04, 0.05], "bm": [0.02] * 5}
    )
    priceM = pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "week": pl.Int64,
            "ret5": pl.Float64,
            "mom20x5": pl.Float64,
            "volShock": pl.Float64,
            "high52": pl.Float64,
        }
    )
    eventM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    return (weekMap, weekEnd, priceM, fundM, eventM)


def testRunWeekHashChain(tmp_path):
    from dartlab.simulate import runweek
    from dartlab.simulate.runweek import hashBlock

    lab = pl.DataFrame(
        {
            "code": ["a", "b", "c", "d", "e"],
            "week": [202607] * 5,
            "exRaw": [-0.02, -0.01, 0.0, 0.01, 0.02],
            "exNeutral": [-0.02, -0.01, 0.0, 0.01, 0.02],
        }
    )
    b1 = runweek.runWeek(week=202607, baseDir=tmp_path, matrices=_mats(202607), labels=lab)
    b2 = runweek.runWeek(
        week=202608, baseDir=tmp_path, matrices=_mats(202608), labels=lab.with_columns(week=pl.lit(202608))
    )
    assert b1["readingCount"] == 10
    assert b2["prevHash"] == b1["hash"]  # 해시체인 연결
    body = {k: v for k, v in b1.items() if k != "hash"}
    assert hashBlock(body) == b1["hash"]  # 결정론 재현 (외부 재검산 가능)
    assert "codeVersionHash" in b1 and "combinedWeights" in b1  # §7b 봉인 필드


def testRunWeekFullWiring(tmp_path):
    from dartlab.simulate import runweek

    # 25주 x 20종목: fund.ep 진짜 엣지 → AdaHedge 가중 + 인증 요약이 블록에 채워지는지
    weeks = list(range(202601, 202626))
    codes = [f"c{i:02d}" for i in range(20)]
    fundRows, labRows, weRows = [], [], []
    for w in weeks:
        weRows.append({"week": w, "date": f"2026{(w - 202600):02d}01"})
        for i, code in enumerate(codes):
            bm = 0.01 * (((i * 13 + w) % 20) + 1)  # 변동은 있으나 엣지 없는 노이즈 표면
            fundRows.append({"code": code, "week": w, "ep": 0.01 * (i + 1), "bm": bm})
            ex = (i / 19 - 0.5) * 0.03 + (((i * 7 + w) % 5) - 2) * 0.002
            labRows.append({"code": code, "week": w, "exRaw": ex, "exNeutral": ex})
    weekEnd = pl.DataFrame(weRows)
    fundM = pl.DataFrame(fundRows)
    labels = pl.DataFrame(labRows)
    priceM = pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "week": pl.Int64,
            "ret5": pl.Float64,
            "mom20x5": pl.Float64,
            "volShock": pl.Float64,
            "high52": pl.Float64,
        }
    )
    eventM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    mats = (weekMap, weekEnd, priceM, fundM, eventM)
    block = None
    for w in weeks:
        block = runweek.runWeek(week=w, baseDir=tmp_path, matrices=mats, labels=labels, nBoot=200)
    assert set(block["combinedWeights"]) == {"fund.ep", "fund.bm"}  # AdaHedge 가중 배선 (죽은 표면 아님)
    assert block["certifySummary"] is not None  # 25주 >= 20 → 인증 실행
    assert block["top10"]  # net 게이트 통과 top10 (주입 경로는 red-flag 만)
    assert block["combinedWeights"]["fund.ep"] >= block["combinedWeights"]["fund.bm"]  # 엣지 표면 가중 우위


def testCascadeDagAsData():
    import json

    from dartlab.simulate import cascade

    r = pl.DataFrame(
        {
            "code": ["a", "a"],
            "surface": ["fund.ep", "event.dilutionGovernance"],
            "direction": [1, -1],
            "score": [0.9, 0.1],
        }
    )
    prof = {"fund": {"stalenessDays": 47}, "financing": {"유상증자결정": 1}, "market": {"sizePctile": 0.8}}
    dag = cascade.companyCascade("a", 202607, r, prof, surfaceWeights={"fund.ep": 2.0, "event.dilutionGovernance": 1.0})
    layers = [n["layer"] for n in dag["nodes"]]
    assert "profile" in layers and "surface" in layers and "decision" in layers
    dec = [n for n in dag["nodes"] if n["layer"] == "decision"][0]
    assert abs(dec["consensus"] - 0.8) < 1e-9  # 2.0*1*0.8 + 1.0*-1*0.8 = 0.8
    json.dumps(dag, ensure_ascii=False)  # 프론트 소비 계약: 직렬화 가능


def testRelationshipPropagate():
    from dartlab.simulate import cascade

    edges = [{"from": "big", "to": "small", "weight": 0.8}, {"from": "big", "to": "other", "weight": 0.5}]
    r = cascade.relationshipPropagate({"big": 1.0}, edges, elasticity=0.5)
    byCode = {row["code"]: row for row in r.iter_rows(named=True)}
    assert byCode["small"]["direction"] == 1  # 대형 상방 → 계열 추종 상방
    assert byCode["small"]["score"] > byCode["other"]["score"]  # 강한 엣지 = 강한 전파
    assert r["surface"][0] == "cascade.groupLeadLag"  # 일반 판독 계약(봉인·채점)


def testCascade8LayerAndRecompute():
    from dartlab.simulate import cascade

    r = pl.DataFrame(
        {
            "code": ["a", "a"],
            "surface": ["fund.ep", "event.dilutionGovernance"],
            "direction": [1, -1],
            "score": [0.9, 0.1],
        }
    )
    prof = {"fund": {"stalenessDays": 47}, "financing": {}, "market": {"sizePctile": 0.8}}
    rel = cascade.relationshipPropagate({"peer": 1.0}, [{"from": "peer", "to": "a", "weight": 0.6}], elasticity=0.5)
    dag = cascade.assembleCascade(
        "a",
        202607,
        profileState=prof,
        surfaceReadings=r,
        economyReading={"score": 0.5},
        industryReading={"score": 0.5},
        relationshipReadings=rel,
        elasticities={"economy->industry": 0.6, "industry->company": 0.5, "relationship": 0.4},
    )
    layers = {n["layer"] for n in dag["nodes"]}
    assert {"economy", "industry", "relationship", "surface", "decision"} <= layers  # 8층 노드
    assert any(e.get("assumptionId") == "cascade:economy->industry" for e in dag["edges"])  # 층간 탄성=가정 id
    # 재계산 계약: 경제 노드 편집 → 산업 하류만 dirty 재실행 (결정론)
    out = cascade.recompute(dag, {"economy": 1.0})
    assert "economy" in out["dirty"] and "industry:a" in out["dirty"]  # dirty 전파
    ind = [n for n in out["nodes"] if n["id"] == "industry:a"][0]
    assert abs(ind["value"] - 0.6) < 1e-9  # 1.0 * weight1 * elasticity0.6
    assert cascade.recompute(dag, {"economy": 1.0})["nodes"] == out["nodes"]  # 결정론 재현


def testInterLayerAssumptions():
    from dartlab.simulate import cascade

    rows = cascade.interLayerAssumptions({"economy->industry": 0.6, "relationship": 0.4})
    assert len(rows) == 2
    assert all(r.unit and r.period and r.falsification for r in rows)  # 가정 계약 필수 필드
    assert rows[0].dimension == "layerElasticity"


def testIssueReadingsPicksLatestPriceWeek(tmp_path, monkeypatch):
    # 미래 투영 레버(락업만기 = 공시+26주)가 readings.max 를 미래로 끌어도 가격 커버 최신주를 발행한다.
    priceM = pl.DataFrame(
        {
            "code": ["a", "b"],
            "week": [202610, 202610],
            "ret5": [0.01, 0.02],
            "mom20x5": [0.0, 0.0],
            "volShock": [0.0, 0.0],
            "high52": [0.9, 0.9],
            "maxRet20": [0.05, 0.05],
        }
    )
    fundM = pl.DataFrame({"code": ["a", "b"], "week": [202610, 202610], "ep": [0.01, 0.02], "bm": [0.02, 0.02]})
    eventM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    weekEnd = pl.DataFrame({"week": [202610], "date": ["20260306"]})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    real = readingCycle._opine.opine

    def fakeOpine(p, f, e, *, directionByType=None):
        r = real(p, f, e, directionByType=directionByType)
        future = pl.DataFrame(
            {
                "code": ["a"],
                "week": [202636],  # 202610 + 26주 락업 투영 (가격 없는 미래)
                "surface": ["lever.lockupExpiry"],
                "direction": [-1],
                "score": [0.0],
                "abstainReason": [None],
            }
        )
        return pl.concat([r, future.select(r.columns)])

    monkeypatch.setattr(readingCycle._opine, "opine", fakeOpine)
    readingCycle.issueReadings(
        week=None, baseDir=tmp_path, matrices=(weekMap, weekEnd, priceM, fundM, eventM), directionByType={}
    )
    led = readingLedger.readReadings(baseDir=tmp_path)
    assert led["week"].unique().to_list() == [202610]  # 미래 202636 아닌 가격 최신주 (near-empty 블록 차단)


def testRecomputePreservesSurfaceContribution():
    from dartlab.simulate import cascade

    # R5 드롭 결함 수정: 경제 노드 편집이 표면 신호를 0 으로 떨어뜨리지 않는다 (표면 value 필드 보존).
    r = pl.DataFrame(
        {"code": ["a", "a"], "surface": ["price.volShock", "fund.ep"], "direction": [1, 1], "score": [0.9, 0.9]}
    )
    prof = {"fund": {"stalenessDays": 47}, "financing": {}, "market": {"sizePctile": 0.8}}
    dag = cascade.assembleCascade(
        "a",
        202607,
        profileState=prof,
        surfaceReadings=r,
        economyReading={"score": 0.7},
        industryReading={"score": 0.6},
        elasticities={"economy->industry": 0.6, "industry->company": 0.5},
    )
    # 표면 base = 2 x (weight1 x dir1 x strength0.8) = 1.6. 초기엔 + 산업 folding(0.6x0.5=0.3) = 1.9
    dec0 = next(n for n in dag["nodes"] if n["layer"] == "decision")["consensus"]
    assert abs(dec0 - 1.9) < 1e-9  # 초기 == 표면 + 층 folding (제작기 일관성)
    out = cascade.recompute(dag, {"economy": 0.0})
    dec1 = next(n for n in out["nodes"] if n["layer"] == "decision")["consensus"]
    assert dec1 > 1.0  # 표면 기여 보존 (옛 결함이면 ~0 으로 붕괴)
    assert abs(dec1 - dec0) > 1e-6  # 경제는 여전히 결정을 바꾼다 (산업 경유 전파)
    assert cascade.recompute(dag, {"economy": 0.0})["nodes"] == out["nodes"]  # 결정론 재현


def testEconomyReadingVotesFromMacro(monkeypatch):
    from datetime import date, timedelta

    from dartlab.simulate import cascade, table

    d = [(date(2026, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(24)]
    # 확장: 유가 상승·원화 강세(fx 하락)·금리 하락 = 3표 → score 1.0
    up = pl.DataFrame(
        {
            "date": d,
            "rate": [3.0 - 0.01 * i for i in range(24)],
            "fx": [1300.0 - i for i in range(24)],
            "oil": [100.0 + i for i in range(24)],
        }
    )
    monkeypatch.setattr(table, "macroDaily", lambda dataDir=None: up)
    econ = cascade.economyReading(d[-1])
    assert econ["available"] and econ["score"] == 1.0 and econ["direction"] == 1  # 실 macro 도출(데모 스칼라 아님)
    # 수축: 반대 방향 = 0표
    down = pl.DataFrame(
        {
            "date": d,
            "rate": [3.0 + 0.01 * i for i in range(24)],
            "fx": [1300.0 + i for i in range(24)],
            "oil": [100.0 - i for i in range(24)],
        }
    )
    monkeypatch.setattr(table, "macroDaily", lambda dataDir=None: down)
    assert cascade.economyReading(d[-1])["score"] == 0.0  # 유가↓·원화약세·금리↑ = 수축


def testRunweekLatticeOverlayHelper(monkeypatch):
    from datetime import date, timedelta

    from dartlab.simulate import runweek, table

    d = [(date(2026, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(40)]
    oil = [100.0 + 3.0 * np.sin(i / 3) for i in range(40)]
    macro = pl.DataFrame({"date": d, "rate": [3.0] * 40, "fx": [1300.0] * 40, "oil": oil})
    betas = pl.DataFrame(
        {
            "code": [f"c{i}" for i in range(12)],
            "rateBeta": [None] * 12,
            "fxBeta": [0.0] * 12,
            "oilBeta": [0.0] * 11 + [50.0],  # c11 = 매크로 꼬리 최악 (취약)
        }
    )
    monkeypatch.setattr(table, "macroDaily", lambda baseDir=None: macro)
    monkeypatch.setattr(table, "macroBetaByCodeWide", lambda asOf, baseDir=None: betas)
    weekEnd = pl.DataFrame({"week": [202601], "date": [d[-1]]})
    cand = pl.DataFrame({"code": [f"c{i}" for i in range(12)], "consensus": [float(12 - i) for i in range(12)]})
    top, dropped = runweek._latticeOverlay(cand, weekEnd, 202601, None, topK=10)
    assert top.height == 10 and dropped is not None
    assert "c11" in dropped  # 검증된 오버레이(14 §9): 매크로 꼬리 최악 종목이 top10 에서 제거


def testIndustryReadingFromMomentum():
    from dartlab.simulate import cascade

    imap = pl.DataFrame({"code": ["a", "b"], "industry": ["energy", "air"]})
    mom = pl.DataFrame({"industry": ["energy", "air"], "momentum": [0.05, -0.08]})
    r = cascade.industryReading("a", imap, mom)
    assert r["available"] and r["industry"] == "energy" and r["direction"] == 1 and r["score"] > 0.5  # 뜨거운 업종
    assert cascade.industryReading("b", imap, mom)["direction"] == -1  # 식은 업종 = 하방
    assert cascade.industryReading("z", imap, mom)["available"] is False  # 미매칭 = 중립(0 대체 금지)


def testProfileTraitCatalogIsExhaustive():
    from dartlab.simulate.profile import traitCatalog

    tc = traitCatalog()
    assert len(tc) == 9  # extractionCatalog 9 대분류 전수 (손 선별 0)
    assert sum(tc.values()) > 50  # 88개념급 (카탈로그 구동)
    assert tc["note"] > tc["segment"]  # 노트 개념이 세그먼트보다 많음 (카탈로그 사실)


def testProfileMarketBetaAndReplay():
    from dartlab.simulate import profile

    rng = np.random.default_rng(9)
    mkt = rng.normal(0, 0.01, 200)
    codeRet = 2.0 * mkt + rng.normal(0, 0.001, 200)  # 베타 ~2
    assert abs(profile.marketBeta(codeRet, mkt) - 2.0) < 0.15
    indep = rng.normal(0, 0.01, 200)
    assert abs(profile.marketBeta(indep, mkt)) < 0.5  # 독립 = 베타 ~0
    # replay 항등성: 같은 상태 dict = 같은 해시 (11 §2 재현성 가드)
    state = {"code": "005930", "asOf": "20260213", "exposure": {"marketBeta": 1.2}}
    assert profile.replayHash(state) == profile.replayHash(dict(state))
    assert profile.replayHash(state) != profile.replayHash({**state, "asOf": "20260214"})


def _synthMacro(n: int = 40):
    """합성 거시(date 'YYYYMMDD', rate 평탄, fx·oil 변동) → 베타 배선 유닛 (R4 축5)."""
    from datetime import date, timedelta

    dates = [(date(2026, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]
    oil = [100.0 + 5.0 * np.sin(i / 3.0) for i in range(n)]
    fx = [1300.0 + 10.0 * np.cos(i / 4.0) for i in range(n)]
    return dates, oil, fx, pl.DataFrame({"date": dates, "rate": [3.0] * n, "fx": fx, "oil": oil})


def testMacroBetasWiring(monkeypatch):
    from dartlab.simulate import profile

    dates, oil, _fx, macro = _synthMacro()
    monkeypatch.setattr(profile._table, "macroDaily", lambda d=None: macro)
    # 종목 일수익 = 4.0 x 유가 수익률 (완전 상관) → oilBeta ~ 4.0
    ret = [0.0] + [4.0 * (oil[i] / oil[i - 1] - 1) for i in range(1, len(oil))]
    res = profile._macroBetas(pl.DataFrame({"date": dates, "ret": ret}), None)
    assert set(res) == {"rateBeta", "fxBeta", "oilBeta"}
    assert res["rateBeta"] is None  # 금리 평탄(var 0) = None (0 대체 금지)
    assert abs(res["oilBeta"] - 4.0) < 0.05  # 완전 상관 회귀 = 계수 복원


def testMacroBetaByCodeBulk(monkeypatch):
    from dartlab.simulate import table

    dates, oil, _fx, macro = _synthMacro(60)
    # codeA 일수익 = 5.0 x 유가수익률(누적 종가), codeB = 유가 무관(평탄)
    closeA, closeB, rows = [1000.0], [1000.0], []
    for i in range(1, len(oil)):
        closeA.append(closeA[-1] * (1 + 5.0 * (oil[i] / oil[i - 1] - 1)))
        closeB.append(closeB[-1] * 1.001)
    for i, dt in enumerate(dates):
        rows.append({"date": dt, "code": "A", "close": closeA[i], "shares": 1.0, "mktcap": closeA[i]})
        rows.append({"date": dt, "code": "B", "close": closeB[i], "shares": 1.0, "mktcap": closeB[i]})
    px = pl.DataFrame(rows)
    monkeypatch.setattr(table, "dailyPrices", lambda baseDir=None: px)
    monkeypatch.setattr(table, "macroDaily", lambda baseDir=None: macro)
    out = table.macroBetaByCode(dates[-1], factor="oil", window=250)
    byCode = {r["code"]: r["beta"] for r in out.iter_rows(named=True)}
    assert abs(byCode["A"] - 5.0) < 0.05  # 벌크 groupby 베타 = 계수 복원 (Company 루프 0)
    assert abs(byCode.get("B", 0.0)) < 0.5  # 유가 무관 종목 = 베타 ~0


def testRelationshipEdgesCounterparty(monkeypatch):
    from dartlab.simulate import profile

    monkeypatch.setattr(
        profile, "_eventTraits", lambda c, a, t, d: {"최대주주변경": 2, "주식등의대량보유상황보고서": 1}
    )
    monkeypatch.setattr(
        profile._table,
        "counterpartyFilings",
        lambda code, asOf, dataDir=None: pl.DataFrame({"counterparty": ["삼성물산", "국민연금공단"], "count": [71, 9]}),
    )
    rel = profile._relationshipEdges("005930", "20260101", None)
    assert rel["distinctCounterparties"] == 2  # 상대방 실명 파싱 (축2 counterparty, None 아님)
    assert rel["counterparties"][0]["counterparty"] == "삼성물산"  # 최다 보유자 우선
    assert rel["edgeCount"] == 3  # 이벤트 엣지 밀도 병존


def testSellTaxAndTickFloor():
    from dartlab.simulate import costs

    assert costs.sellTaxRate("20251231") == 0.0015  # 2026 전 0.15%
    assert costs.sellTaxRate("20260101") == 0.0020  # 2026-01-01 부터 0.20%
    assert costs.tickFloorFrac(1500) == pytest.approx(1 / 1500)  # <2000 = 1원 틱
    assert costs.tickFloorFrac(100000) == pytest.approx(100 / 100000)  # 5만~20만 = 100원 틱
    assert costs.tickFloorFrac(0) == 0.0  # 이상치 방어


def testCostFloorWiderSpreadCostsMore():
    from dartlab.simulate import costs

    dates = [f"202601{d:02d}" for d in range(1, 26)]
    rows = []
    for dt in dates:
        rows.append({"date": dt, "code": "flat", "high": 10000.0, "low": 10000.0, "close": 10000.0})
        rows.append({"date": dt, "code": "wide", "high": 10500.0, "low": 9500.0, "close": 10000.0})
    dhl = pl.DataFrame(rows)
    weekEnd = pl.DataFrame({"week": [202604], "date": ["20260125"]})
    cf = costs.costFloorWeekly(weekEnd, dhl)
    byCode = {r["code"]: r for r in cf.iter_rows(named=True)}
    floor = 0.0020 + 2 * costs.INST_FEE  # 세율+기관비용 하한 (2026)
    assert byCode["flat"]["costFloor"] >= floor  # 무스프레드도 세율·기관비용 바닥
    assert byCode["wide"]["costFloor"] > byCode["flat"]["costFloor"]  # 넓은 스프레드 = 큰 비용
    assert byCode["wide"]["spread"] > 0  # 스프레드 추정 양수


def testNetPositiveAvoidZeroCost():
    from dartlab.simulate import costs

    edge = pl.DataFrame({"code": ["a", "b"], "edge": [0.02, 0.005]})
    floor = pl.DataFrame({"code": ["a", "b"], "costFloor": [0.01, 0.01]})
    passed = costs.netPositive(edge, floor)
    assert passed == {"a"}  # a: 0.02-0.01>0 통과, b: 0.005-0.01<0 탈락
    passedAvoid = costs.netPositive(edge, floor, avoidCodes={"b"})
    assert "b" in passedAvoid  # 회피 종목은 비용 0 이라 작은 엣지도 통과


def _panelToLong(W):
    rows = []
    T, L = W.shape
    for t in range(T):
        for k in range(L):
            rows.append({"surface": f"s{k:02d}", "week": 202600 + t, "spread": float(W[t, k])})
    return pl.DataFrame(rows)


def testBenjaminiHochbergControlsFdr():
    from dartlab.simulate import certify

    p = np.array([0.001, 0.2, 0.3, 0.4, 0.5])
    rej = certify.benjaminiHochberg(p, 0.1)
    assert rej[0] and not rej[1:].any()  # 유의한 1개만 기각
    rng = np.random.default_rng(0)
    pn = rng.uniform(size=1000)  # 전부 null
    assert certify.benjaminiHochberg(pn, 0.1).sum() < 20  # 거짓 발견 억제


def testCertifyNoiseYieldsNoCertification():
    from dartlab.simulate import certify

    rng = np.random.default_rng(1)
    W = rng.normal(0, 0.01, size=(120, 30))  # 순수 노이즈 30 표면
    res = certify.certify(_panelToLong(W), nBoot=300)
    assert res["spaP"] > 0.10  # 노이즈는 SPA 인증 불가
    assert (res["surfaces"]["verdict"] == "인증").sum() == 0  # 인증 0 (factor zoo 통제)


def testCertifyRealEdgeIsCertified():
    from dartlab.simulate import certify

    rng = np.random.default_rng(2)
    W = rng.normal(0, 0.01, size=(120, 30))
    W[:, 5] += 0.006  # 표면 s05 = 진짜 엣지 (t~6.6)
    res = certify.certify(_panelToLong(W), nBoot=300)
    assert res["spaP"] < 0.05  # 진짜 최고표면 = SPA 기각
    v = {r["surface"]: r["verdict"] for r in res["surfaces"].iter_rows(named=True)}
    assert v["s05"] == "인증"  # FDR + t허들 + RW 전부 통과


def testCorrClusterEffNAndShrink():
    from dartlab.simulate import certify

    rng = np.random.default_rng(4)
    base = rng.normal(size=(200, 1))
    wCorr = np.hstack([base, base, base])  # 3 완전 상관 = 유효 1
    wIndep = rng.normal(size=(200, 3))  # 독립 3 = 유효 ~3
    assert certify.corrClusterEffN(wCorr) < 1.2
    assert 2.4 < certify.corrClusterEffN(wIndep) <= 3.01
    sh = certify.empiricalBayesShrink(np.array([0.10, 0.0, -0.10, 0.0, 0.0]), np.array([0.05] * 5))
    assert abs(sh[0]) < 0.10  # 극단 추정이 대평균으로 수축


def _conformalPanel(sigmaByWeek, nWeeks, nCodes, seed):
    rng = np.random.default_rng(seed)
    rows = []
    for t in range(nWeeks):
        sig = sigmaByWeek(t)
        for c in range(nCodes):
            rows.append(
                {
                    "week": 202600 + t,
                    "code": f"c{c:02d}",
                    "pred": 0.0,
                    "actual": float(rng.normal(0, sig)),
                    "scale": 1.0,
                    "size": float(rng.random()),
                }
            )
    return pl.DataFrame(rows)


def testWinklerRewardsTightCoverage():
    from dartlab.simulate import conformal

    y = np.array([0.0])
    tight = conformal.winklerScore(np.array([-0.1]), np.array([0.1]), y, 0.2)[0]
    wide = conformal.winklerScore(np.array([-0.5]), np.array([0.5]), y, 0.2)[0]
    miss = conformal.winklerScore(np.array([0.2]), np.array([0.4]), y, 0.2)[0]
    assert tight < wide  # 좁고 적중 = 낮음
    assert miss > wide  # 미적중 = 페널티


def testConformalCoverageConvergesToDeclared():
    from dartlab.simulate import conformal

    panel = _conformalPanel(lambda t: 0.02, 150, 40, 5)
    res = conformal.aciBands(panel, alpha0=0.2, gamma=0.1)
    assert 0.73 <= res["coverage"] <= 0.87  # 선언 80% 에 실측 커버리지 수렴
    assert res["byBucket"].height == 5  # Mondrian 버킷별 커버리지 병기


def testConformalAdaptsToDistributionShift():
    from dartlab.simulate import conformal

    panel = _conformalPanel(lambda t: 0.02 if t < 75 else 0.06, 150, 40, 9)
    res = conformal.aciBands(panel, alpha0=0.2, gamma=0.2)
    cc = res["coverageCurve"].filter(pl.col("week") >= 202600 + 100)  # 이동 후 안정 구간
    lateCoverage = float(cc["coverage"].mean())
    assert 0.70 <= lateCoverage <= 0.88  # 분산 3배 이동에도 장기 커버리지 선언값 근방 유지


def _gridReadingsLabels():
    codes = [f"c{i:02d}" for i in range(20)]
    rows, labs = [], []
    for w in range(202601, 202631):
        for i, code in enumerate(codes):
            s = i / 19
            ex = (s - 0.5) * 0.04 + (((i * 7 + w) % 5) - 2) * 0.002
            labs.append({"code": code, "week": w, "exNeutral": ex})
            eDir = 1 if s > 0.6 else (-1 if s < 0.4 else 0)
            rows.append({"code": code, "week": w, "surface": "edge", "direction": eDir, "score": s})
            ns = ((i * 13 + w * 3) % 20) / 19
            nDir = 1 if ns > 0.6 else (-1 if ns < 0.4 else 0)
            rows.append({"code": code, "week": w, "surface": "noise", "direction": nDir, "score": ns})
    return pl.DataFrame(rows), pl.DataFrame(labs)


def testAssumptionGridContract():
    from dartlab.simulate import assume

    schemes = {"edge": {"edge": 1.0, "noise": 0.0}, "noise": {"edge": 0.0, "noise": 1.0}}
    grid = assume.assumptionGrid(schemes, topKs=(5, 10), minSurfaces=(1,), horizons=(5,))
    assert len(grid) == 2 * 2 * 1 * 1 * 1  # 스킴2 x topK2 x minS1 x hz1 x preset1
    row = grid[0].rows[0]
    assert row.unit and row.period and row.source and row.falsification  # 필수 필드 비어있지 않음
    assert {r.dimension for r in grid[0].rows} == {
        "weightScheme",
        "consensusTopK",
        "minSurfaces",
        "horizon",
        "scenarioPreset",
    }


def testApplyGridEdgeBeatsNoiseAndFeedsSweep():
    from dartlab.simulate import assume, sweep

    readings, labels = _gridReadingsLabels()
    schemes = {
        "edge": {"edge": 1.0, "noise": 0.0},
        "noise": {"edge": 0.0, "noise": 1.0},
        "equal": {"edge": 1.0, "noise": 1.0},
    }
    grid = assume.assumptionGrid(schemes, topKs=(5,), minSurfaces=(1,), horizons=(5,))
    res = assume.applyGrid(readings, labels, grid)
    assert res["perf"].shape == (3, 30)  # (nConfigs x nWeeks)
    byId = {cid: i for i, cid in enumerate(res["configIds"])}
    edgePerf = np.nanmean(res["perf"][byId["edge|k5|m1|h5|baseline"]])
    noisePerf = np.nanmean(res["perf"][byId["noise|k5|m1|h5|baseline"]])
    assert edgePerf > noisePerf  # edge 가중 config 가 노이즈보다 높은 성과
    pbo = sweep.cscvPbo(res["perf"], sBlocks=6)  # sweep 통합 (성과 행렬 소비)
    assert "pbo" in pbo and 0 <= pbo["pbo"] <= 1


def testSealAssumptions(tmp_path):
    from dartlab.simulate import assume

    schemes = {"edge": {"edge": 1.0}}
    grid = assume.assumptionGrid(schemes, topKs=(5,), minSurfaces=(1,))
    p = assume.sealAssumptions(
        grid,
        {"edge|k5|m1|h5|baseline": {"pbo": 0.1, "dsr": 0.9}},
        week=202607,
        issuedLive=True,
        issuedAt="t",
        baseDir=tmp_path,
    )
    got = pl.read_parquet(p)
    assert got.height == 1 and got["issuedLive"][0]  # 봉인 + issuedLive 권위


def testMmcResidualizeFlagsRedundant():
    from dartlab.simulate import residual

    rng = np.random.default_rng(6)
    codes = [f"c{i:02d}" for i in range(30)]
    rows, labs = [], []
    for w in range(202601, 202641):
        sigA = rng.random(len(codes))  # 독립 신호 A
        sigC = rng.random(len(codes))  # 독립 신호 C
        for i, code in enumerate(codes):
            ex = 0.04 * (sigA[i] - 0.5) + 0.04 * (sigC[i] - 0.5) + rng.normal(0, 0.005)
            labs.append({"code": code, "week": w, "exNeutral": ex})
            rows.append({"code": code, "week": w, "surface": "A", "direction": 0, "score": float(sigA[i])})
            rows.append({"code": code, "week": w, "surface": "B", "direction": 0, "score": float(sigA[i])})  # A 복제
            rows.append({"code": code, "week": w, "surface": "C", "direction": 0, "score": float(sigC[i])})
    readings, labels = pl.DataFrame(rows), pl.DataFrame(labs)
    dupe = residual.mmcContribution(readings, labels, "B", ["A"])
    indep = residual.mmcContribution(readings, labels, "C", ["A"])
    assert dupe["redundant"]  # B 는 A 복제 = 증분 t 붕괴 = 중복
    assert not indep["redundant"]  # C 는 독립 = 증분 t 유지
    assert abs(indep["residualT"]) > abs(dupe["residualT"])  # 독립 표면이 더 큰 증분


def testRegimeClassifierDeterministicAndVersioned():
    from dartlab.simulate import regime

    assert len(regime.regimeVersionHash()) == 16  # 분류기 봉인 해시 (변경=새 시리즈)
    mw = pl.DataFrame({"week": list(range(202601, 202641)), "mktRet": [(-1) ** i * 0.03 for i in range(40)]})
    reg = regime.classifyRegimes(mw)
    assert set(reg["regime"].unique().to_list()) <= {"calmUp", "calmDown", "stressUp", "stressDown"}
    reg2 = regime.classifyRegimes(mw)
    assert reg["regime"].to_list() == reg2["regime"].to_list()  # 결정론 (같은 입력=같은 태그)


def testScoreConditionalMatchesRegimeAndAirtime():
    from dartlab.simulate import regime

    reg = pl.DataFrame({"week": [202601, 202602, 202603], "regime": ["stressDown", "calmUp", "stressDown"]})
    readings = pl.DataFrame(
        {
            "code": ["a", "a", "a", "b"],
            "week": [202601, 202602, 202603, 202602],
            "surface": ["s"] * 4,
            "condition": ["stressDown", "stressDown", "stressDown", None],
        }
    )
    out = regime.scoreConditional(readings, reg)
    # 조건 stressDown 판독은 stressDown 주(202601,202603)만 채점, 202602(calmUp)는 미채점
    condScored = out["scored"].filter(pl.col("condition") == "stressDown")
    assert set(condScored["week"].to_list()) == {202601, 202603}
    assert 202602 in out["scored"].filter(pl.col("condition").is_null())["week"].to_list()  # 무조건은 항상
    air = {r["condition"]: r for r in out["airtime"].iter_rows(named=True)}
    assert air["stressDown"]["liveWeeks"] == 3 and air["stressDown"]["realizedWeeks"] == 2  # airtime 분모


def testGiacominiWhiteDetectsConditionalDifference():
    from dartlab.simulate import regime

    rng = np.random.default_rng(8)
    T = 250
    stress = (rng.random(T) < 0.4).astype(float)
    inst = np.column_stack([np.ones(T), stress])
    # B 가 stress 에서 명확히 우월: d = lossA - lossB > 0 (stress 주에)
    d = 0.02 * stress + rng.normal(0, 0.005, T)
    lossA, lossB = d, np.zeros(T)
    gw = regime.giacominiWhite(lossA, lossB, inst)
    assert gw["pValue"] < 0.05  # 조건부 예측력 차이 검출
    same = regime.giacominiWhite(np.ones(T), np.ones(T), inst)
    assert same["pValue"] > 0.5  # 손실 동일 = 기각 불가


def testFundDailyStepIsPitCarryNoInterpolation():
    from dartlab.simulate import fundDaily

    grid = pl.DataFrame(
        {
            "code": ["a", "a"],
            "period": ["2026Q1", "2026Q2"],
            "rceptDate": ["20260101", "20260401"],
            "account": ["netIncome", "netIncome"],
            "amount": [100.0, 120.0],
        }
    )
    dates = pl.DataFrame({"date": ["20260110", "20260215", "20260415", "20260515"]})
    d = fundDaily.fundDailyStep(grid, dates).sort("date")
    assert d["amount"].to_list() == [100.0, 100.0, 120.0, 120.0]  # 계단(보간 아님): 발효 전 최신값 유지
    assert d.filter(pl.col("date") == "20260215")["tau"][0] == 45  # 이벤트타임 경과일


def testSueSeasonalSurprise():
    from dartlab.simulate import fundDaily

    amounts = [100.0, 102, 104, 106, 120, 123, 126, 129, 145, 149, 153, 200]  # 마지막 분기 서프라이즈
    periods = [f"{2023 + i // 4}Q{i % 4 + 1}" for i in range(12)]
    grid = pl.DataFrame(
        {
            "code": ["a"] * 12,
            "period": periods,
            "rceptDate": [f"2023{i:02d}01" for i in range(1, 13)],
            "account": ["netIncome"] * 12,
            "amount": amounts,
        }
    )
    s = fundDaily.sue(grid).sort("period")
    last = s.filter(pl.col("period") == "2025Q4")["sue"][0]
    assert last is not None and last > 2.0  # 큰 계절 서프라이즈 = 높은 양의 SUE


def testEarAnnouncementExcess():
    from dartlab.simulate import fundDaily

    dates = [f"202601{d:02d}" for d in range(9, 20)]
    rows = []
    for i, dt in enumerate(dates):
        rows.append({"date": dt, "code": "a", "close": 100.0 * (1.02**i)})  # a 발표후 +2%/일
        rows.append({"date": dt, "code": "b", "close": 100.0})  # b 시장 평평
    px = pl.DataFrame(rows)
    grid = pl.DataFrame(
        {"code": ["a"], "period": ["2026Q1"], "rceptDate": ["20260110"], "account": ["netIncome"], "amount": [100.0]}
    )
    e = fundDaily.ear(grid, px, window=3)
    assert e["ear"][0] > 0.02  # 발표창 양의 초과수익


def testChowLinIsDisplayOnly():
    from dartlab.simulate import fundDaily

    out = fundDaily.chowLinDisplay(np.array([100.0, 120, 90, 110]), periodsPerQuarter=3)
    assert out["displayOnly"] is True and "look-ahead" in out["warning"]  # 피처 금지 라벨
    assert len(out["series"]) == 12  # 4분기 x 3 = 12 월


def testLeverLedgerAndReadings():
    from dartlab.simulate import levers

    ids = {lv.leverId for lv in levers.LEVER_LEDGER}
    assert "usPead" in ids and "usIndexInclusion" in ids  # do-not-build 원장에 박제
    surfs = {s.surface for s in levers.leverSurfaces()}
    assert "lever.treasuryAcquire" in surfs and "lever.usPead" not in surfs  # 수확만 등재
    ev = pl.DataFrame(
        {
            "code": ["a", "b", "c"],
            "week": [202607] * 3,
            "reportType": ["자기주식취득결정", "유상증자결정", "전환청구권행사"],
        }
    )
    r = levers.leverReadings(ev)
    byS = {row["surface"]: row for row in r.iter_rows(named=True)}
    assert byS["lever.treasuryAcquire"]["direction"] == 1  # 문헌 long prior
    assert byS["lever.rightsOffering"]["direction"] == -1  # 문헌 avoid prior (희석)
    assert byS["lever.cbChain"]["direction"] == -1  # CB 사슬 회피
    assert not any(s.startswith("lever.us") for s in byS)  # do-not-build 무발행
    r2 = levers.leverReadings(ev, directionByType={"자기주식취득결정": -1})
    byS2 = {row["surface"]: row for row in r2.iter_rows(named=True)}
    assert byS2["lever.treasuryAcquire"]["direction"] == -1  # 데이터 방향이 문헌 prior 이김


def testMarketParameterizationAndEdgarMap():
    import pytest as _pytest

    from dartlab.simulate import markets

    assert markets.marketStatus("KR") == "wired"  # KR 배선 완료
    assert markets.marketStatus("US") == "wired"  # US 도 EDGAR 실배선 완료 (tableUs)
    markets.requireWired("KR")
    markets.requireWired("US")  # 둘 다 판독 가능
    with _pytest.raises(ValueError):  # 미지원 시장은 차단
        markets.requireWired("JP")
    assert markets.tableModule("US").__name__.endswith("tableUs")  # US → tableUs 라우팅
    m = markets.leverSourceMap()
    assert m["insiderBuy"]["form"] == "Form 4"  # KR 레버 → US EDGAR 폼 매핑 (10 §1b)
    assert m["auditDelay"]["form"] == "NT 10-K / NT 10-Q"


def testTraitConditionalScorecard():
    # 형질 버킷 A 는 표면에 엣지, B 는 노이즈 → A 셀 통과, B 동물원구분불가 (형질이 표면을 가름)
    codes = [f"c{i:02d}" for i in range(20)]
    trait = pl.DataFrame({"code": codes, "traitBucket": ["A" if i < 10 else "B" for i in range(20)]})
    rows, labs = [], []
    for w in range(202601, 202641):
        wkN = ((w % 11) - 5) * 0.003
        for i, code in enumerate(codes):
            isA = i < 10
            rank = (i % 10) / 9
            ex = ((rank - 0.5) * 0.05 if isA else (((i * 13 + w) % 10) / 9 - 0.5) * 0.002) + wkN
            labs.append({"code": code, "week": w, "exNeutral": ex})
            score = rank if isA else ((i * 7 + w * 3) % 10) / 9
            rows.append({"code": code, "week": w, "surface": "s", "direction": 0, "score": score})
    card = readingScorecard.traitConditionalScorecard(pl.DataFrame(rows), pl.DataFrame(labs), trait, traitName="hist")
    byBucket = {r["traitBucket"]: r for r in card.iter_rows(named=True)}
    assert byBucket["A"]["t"] > byBucket["B"]["t"]  # 형질 A 버킷에서 표면이 더 강함
    assert byBucket["A"]["verdict"] == "통과"  # A 셀 승격
    assert card["traitName"][0] == "hist"  # 형질 축 라벨


def testBacktestFullEngineReplay():
    from dartlab.simulate import backtest

    # 25주 x 20종목 fund.ep 엣지 → 백테스트가 성적표·인증·sweep 전부 산출
    weeks = list(range(202601, 202626))
    codes = [f"c{i:02d}" for i in range(20)]
    fundRows, labRows, weRows = [], [], []
    for w in weeks:
        weRows.append({"week": w, "date": f"2026{(w - 202600):02d}01"})
        for i, code in enumerate(codes):
            bm = 0.01 * (((i * 13 + w) % 20) + 1)
            fundRows.append({"code": code, "week": w, "ep": 0.01 * (i + 1), "bm": bm})
            ex = (i / 19 - 0.5) * 0.03 + (((i * 7 + w) % 5) - 2) * 0.002
            labRows.append({"code": code, "week": w, "exRaw": ex, "exNeutral": ex})
    priceM = pl.DataFrame(
        schema={
            "code": pl.Utf8,
            "week": pl.Int64,
            "ret5": pl.Float64,
            "mom20x5": pl.Float64,
            "volShock": pl.Float64,
            "high52": pl.Float64,
            "maxRet20": pl.Float64,
        }
    )
    eventM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    mats = (weekMap, pl.DataFrame(weRows), priceM, pl.DataFrame(fundRows), eventM)
    r = backtest.backtest(matrices=mats, labels=pl.DataFrame(labRows), nBoot=150)
    assert r["weeks"] == 25 and r["universe"] == 20  # 전 역사 replay
    assert "fund.ep" in r["scorecard"]["surface"].to_list()  # 성적표 산출
    assert r["certify"]["surfaces"].height >= 1  # 인증 깔때기 실행
    assert r["sweep"]["nConfigs"] > 0 and r["sweep"]["pbo"] is not None  # sweep 실행 (PBO/DSR/robust)


def testSimTypeRegistryAndOtsAnchor():
    from dartlab.simulate import runweek, simtype

    reg = simtype.listSimTypes()
    assert {"economy", "finance", "price", "quant", "reading"} <= set(reg)  # 첫 등재 + 판독 엔진
    assert all(s.sourceLineage and s.assumptionAxis and s.scoringRule for s in reg.values())  # 4계약 충족
    assert simtype.isScorable("reading") and simtype.isScorable("quant")  # 채점 가능
    # 새 시뮬 등재 (4계약) + unscorable 라벨
    simtype.registerSimType(
        simtype.SimTypeSpec("explore", ("x",), ("y",), simtype.OUTPUT_CROSS_SECTIONAL, "unscorable")
    )
    assert not simtype.isScorable("explore")  # 탐색 전용 = 영구 미채점
    with pytest.raises(ValueError):  # 4계약 미충족 거부
        simtype.registerSimType(simtype.SimTypeSpec("bad", (), (), simtype.OUTPUT_EXTENSION, ""))
    # OpenTimestamps 앵커 페이로드
    ots = runweek.otsAnchor({"hash": "abc", "week": 202607})
    assert ots["hash"] == "abc" and ots["algorithm"] == "sha256" and "runbook" in ots


def testLeverRefineDerivable():
    from dartlab.simulate import leverRefine

    ev = pl.DataFrame(
        {
            "code": ["a", "a", "a", "b", "c"],
            "week": [202607, 202607, 202607, 202607, 202607],
            "reportType": ["임원ㆍ주요주주특정증권등소유상황보고서"] * 4 + ["증권신고서"],
        }
    )
    ins = leverRefine.insiderClusterReadings(ev)
    byCode = {r["code"]: r for r in ins.iter_rows(named=True)}
    assert byCode["a"]["score"] > byCode["b"]["score"]  # a 3건 군집 > b 1건 (군집 강도)
    assert byCode["a"]["surface"] == "lever.insiderCluster"
    lk = leverRefine.lockupExpiryReadings(ev)
    assert lk["direction"][0] == -1  # 락업 만료 회피
    assert lk["week"][0] == 202607 + 26  # 발행주 + 표준 락업 26주 (연내)
    caps = pl.DataFrame(
        {"date": ["20260213"] * 5, "code": [f"c{i}" for i in range(5)], "mktcap": [10.0, 20, 30, 40, 50]}
    )
    wm = pl.DataFrame({"date": ["20260213"], "week": [202607]})
    idx = leverRefine.indexInclusionReadings(caps, wm, lowerPct=0.7, upperPct=0.95)
    assert idx.height >= 1 and idx["surface"][0] == "lever.indexInclusion"  # 경계 밴드 후보
