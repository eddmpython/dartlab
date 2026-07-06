"""E 연장 층 : 방법 라우팅·PIT 컷·기권·밴드 단조·봉인/채점 왕복 (순수 유닛, 네트워크 0).

Covers:
- 흐름=전년동기 seasonal, 저량=직전분기 carry (실측 선택 방법 라우팅).
- PIT 컷: rceptDate > asOf 행은 앵커·오차분위에 미반영 (look-ahead 0).
- 앵커 결손 = 기권 (무행, 0 대체 금지).
- seriesWithE: A+E 통합 연장선 1 포맷.
- sealEstimates 봉인 + 같은 vintage 재발행 스킵 + scoreEstimatesDue pinball 채점 왕복.
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate import estimate as est


def _grid(rows: list[tuple[str, str, str, str, float]]) -> pl.DataFrame:
    return pl.DataFrame([{"code": c, "period": p, "rceptDate": r, "account": a, "amount": v} for c, p, r, a, v in rows])


def _seasonalGrid(code: str = "a", years: tuple[int, ...] = (2023, 2024, 2025)) -> pl.DataFrame:
    """완전 반복 계절 매출(100/200/300/400) + 증가 자본 = 오차 0 계절 시계열."""
    rows = []
    for y in years:
        for qn, rev in zip((1, 2, 3, 4), (100.0, 200.0, 300.0, 400.0)):
            rcept = f"{y}{qn * 2 + 3:02d}15"
            rows.append((code, f"{y}Q{qn}", rcept, "revenue", rev))
            rows.append((code, f"{y}Q{qn}", rcept, "equity", 1000.0 + (y - 2023) * 40 + qn * 10))
    return _grid(rows)


def testFlowSeasonalStockCarryRouting():
    e = est.estimateQuarters(_seasonalGrid(), asOf="20260101", horizonQ=4)
    rev = {r["period"]: r for r in e.filter(pl.col("account") == "revenue").iter_rows(named=True)}
    # 완전 반복 계절 = 과거 편차 0 = p50 == 앵커(전년동기) 정확 재현
    assert rev["2026Q1"]["p50"] == 100.0 and rev["2026Q1"]["method"] == "seasonal"
    assert rev["2026Q4"]["p50"] == 400.0
    assert rev["2026Q1"]["p5"] == rev["2026Q1"]["p95"] == 100.0  # 편차 0 = 밴드 폭 0
    eq = e.filter((pl.col("account") == "equity") & (pl.col("horizon") == 1)).row(0, named=True)
    assert eq["method"] == "carry" and eq["anchor"] == 1000.0 + 80 + 40  # 최종 관측 carry
    for r in e.iter_rows(named=True):
        assert r["p5"] <= r["p25"] <= r["p50"] <= r["p75"] <= r["p95"]  # 밴드 단조


def testPitCutExcludesFutureVintage():
    g = _seasonalGrid()
    # 2025Q4 접수(20251115)가 asOf 이후면 최종 관측이 2025Q3 로 물러난다
    e = est.estimateQuarters(g, asOf="20251001", horizonQ=1)
    rev = e.filter((pl.col("account") == "revenue") & (pl.col("horizon") == 1)).row(0, named=True)
    assert rev["period"] == "2025Q4" and rev["anchor"] == 400.0  # lastQi=2025Q3 → 다음 분기 2025Q4


def testAbstainOnMissingSeasonalAnchor():
    g = _seasonalGrid()
    # 2025Q2 행 제거 = 2026Q2 의 전년동기 앵커 결손 → 그 지평만 무행 (기권)
    g2 = g.filter(~((pl.col("period") == "2025Q2") & (pl.col("account") == "revenue")))
    e = est.estimateQuarters(g2, asOf="20260101", horizonQ=4)
    revPeriods = set(e.filter(pl.col("account") == "revenue")["period"].to_list())
    assert "2026Q2" not in revPeriods and "2026Q1" in revPeriods


def testBandScaleIndependentOfAnchor():
    # 근제로 앵커에서도 밴드 폭은 최근 4분기 규모(scale)로 유지 (|앵커| 분모 폭발 결함 가드, e-v2)
    rows = []
    vals = {2023: [10.0, 20.0, 30.0, 40.0], 2024: [11.0, 22.0, 33.0, 44.0], 2025: [12.0, 24.0, 0.1, 48.0]}
    for y, vs in vals.items():
        for qn, v in zip((1, 2, 3, 4), vs):
            rows.append(("a", f"{y}Q{qn}", f"{y}{qn * 2 + 3:02d}15", "netIncome", v))
    e = est.estimateQuarters(_grid(rows), asOf="20260101", horizonQ=4)
    q3 = e.filter(pl.col("period") == "2026Q3").row(0, named=True)  # 앵커 0.1 (근제로)
    q4 = e.filter(pl.col("period") == "2026Q4").row(0, named=True)  # 앵커 48
    w3, w4 = q3["p95"] - q3["p5"], q4["p95"] - q4["p5"]
    assert abs(w3 - w4) < 1e-9  # 같은 시계열 = 같은 scale·d 분위 → 밴드 폭 동일 (앵커 무관)
    assert w3 < 100.0  # 근제로 앵커에서도 폭발 없음


def testSeriesWithEUnifiedFormat():
    g = _seasonalGrid()
    e = est.estimateQuarters(g, asOf="20260101", horizonQ=2)
    s = est.seriesWithE(g, e, code="a").filter(pl.col("account") == "revenue")
    basisByPeriod = {r["period"]: r["basis"] for r in s.iter_rows(named=True)}
    assert basisByPeriod["2025Q4"] == "A" and basisByPeriod["2026Q1"] == "E"  # 실적 뒤로 E 연장
    assert s.filter(pl.col("basis") == "E")["value"].null_count() == 0  # E value = p50


def testSealScoreRoundtrip(tmp_path):
    g = _seasonalGrid()
    e = est.estimateQuarters(g, asOf="20260101", horizonQ=1)
    n = est.sealEstimates(e, asOf="20260101", baseDir=tmp_path, issuedAt="2026-01-02T00:00+00:00")
    assert n == e.height and n > 0
    again = est.sealEstimates(e, asOf="20260101", baseDir=tmp_path, issuedAt="2026-01-03T00:00+00:00")
    assert again == 0  # 같은 vintage 재발행 스킵
    # 실제치 도착: 2026Q1 매출 110 (E=100 대비 +10%), 자본 1130
    actual = _grid([("a", "2026Q1", "20260515", "revenue", 110.0), ("a", "2026Q1", "20260515", "equity", 1130.0)])
    scored = est.scoreEstimatesDue(baseDir=tmp_path, grid=actual)
    assert scored == 2
    from dartlab.simulate import expectationLedger as eled

    sc = eled.readScores(baseDir=tmp_path)
    assert sc.height == 2 and sc["crps"].null_count() == 0  # pinball 채점 봉인
    assert est.scoreEstimatesDue(baseDir=tmp_path, grid=actual) == 0  # 채점 완료분 재채점 없음
