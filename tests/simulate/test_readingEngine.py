"""판독 엔진 R1 : 합성 데이터로 계약·의견화·채점·사이클 (순수 유닛, 네트워크 0).

Covers:
- readingLedger: 봉인 라운드트립 + append-only(봉인 키 중복 거부) + unscored 필터.
- opine: 연속 표면 극단 방향(상위=+1·하위=-1·중간=0) + 이벤트 방향화 사전 적용.
- readingScorecard: 진짜 엣지 표면은 |t| 큼, 노이즈 표면은 factor-zoo 미달 라벨. 방향화 게이트.
- readingCycle: issueReadings 봉인 → scoreReadingsDue 채점 왕복 (주입 행렬).
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.simulate import opine, readingCycle, readingLedger, readingScorecard
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
