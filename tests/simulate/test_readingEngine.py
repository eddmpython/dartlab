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


def testProfileTraitCatalogIsExhaustive():
    from dartlab.simulate.profile import traitCatalog

    tc = traitCatalog()
    assert len(tc) == 9  # extractionCatalog 9 대분류 전수 (손 선별 0)
    assert sum(tc.values()) > 50  # 88개념급 (카탈로그 구동)
    assert tc["note"] > tc["segment"]  # 노트 개념이 세그먼트보다 많음 (카탈로그 사실)


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
