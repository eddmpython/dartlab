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
