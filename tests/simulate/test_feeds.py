"""작업대 피드 레지스트리 : 등록 = 표면 자동 등재 + 실패 격리 (순수 유닛, 네트워크 0).

Covers:
- registerCompanyFeed/unregister 멱등 + 시장 필터.
- extraFeedMatrices: 정상 피드 소비 + 실패 피드 격리(오류 명시, silent 0) + 스키마 미충족 검출.
- opine 자동 표면: 새 피드 축 → "<axis>.<col>" 표면, 새 컬럼 → 표면 자동 (손 매핑 0 = 자동흡수).
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate import feeds as fd
from dartlab.simulate import opine


def _emptyEvent() -> pl.DataFrame:
    return pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "reportType": pl.Utf8})


def _priceM() -> pl.DataFrame:
    return pl.DataFrame(
        {"code": ["a", "b", "c", "d", "e"], "week": [202607] * 5, "ret5": [0.01, 0.02, 0.03, 0.04, 0.05]}
    )


def testFeedRegistryAndIsolation():
    good = fd.CompanyFeed(
        "alt", lambda ctx: pl.DataFrame({"code": ["a", "b"], "week": [202607, 202607], "zzz": [1.0, 2.0]})
    )
    bad = fd.CompanyFeed("boom", lambda ctx: (_ for _ in ()).throw(RuntimeError("피드 고장")))
    empty = fd.CompanyFeed("hollow", lambda ctx: pl.DataFrame({"x": [1]}))  # (code, week) 미충족
    usOnly = fd.CompanyFeed("usOnly", lambda ctx: _priceM(), markets=("US",))
    try:
        for f in (good, bad, empty, usOnly):
            fd.registerCompanyFeed(f)
        fd.registerCompanyFeed(good)  # 재등록 = 교체 (멱등)
        mats, errors = fd.extraFeedMatrices({"market": "KR"})
        assert "alt" in mats and mats["alt"].height == 2  # 정상 피드 소비
        assert "boom" in errors and "RuntimeError" in errors["boom"]  # 실패 격리 + 오류 명시 (silent 0)
        assert "hollow" in errors  # 스키마 미충족 검출
        assert "usOnly" not in mats and "usOnly" not in errors  # 시장 필터 (KR 런에 US 피드 미실행)
    finally:
        for axis in ("alt", "boom", "hollow", "usOnly"):
            fd.unregisterCompanyFeed(axis)
    assert fd.companyFeeds() == [f for f in fd.companyFeeds() if f.axis not in ("alt", "boom")]  # 해제 대칭


def testOpineAutoSurfaceFromFeedAxis():
    # 새 엔진 피드 = 등록 1줄 → "<axis>.<col>" 표면 자동 등재 (opine 수정 0)
    extra = {
        "quantX": pl.DataFrame(
            {"code": ["a", "b", "c", "d", "e"], "week": [202607] * 5, "alpha1": [1.0, 2.0, 3.0, 4.0, 5.0]}
        )
    }
    fundM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "ep": pl.Float64, "bm": pl.Float64})
    r = opine.opine(_priceM(), fundM, _emptyEvent(), directionByType={}, extraMatrices=extra)
    surfaces = set(r["surface"].unique().to_list())
    assert "quantX.alpha1" in surfaces  # 피드 축 자동 표면
    auto = r.filter(pl.col("surface") == "quantX.alpha1")
    byCode = {row["code"]: row["direction"] for row in auto.iter_rows(named=True)}
    assert byCode["e"] == 1 and byCode["a"] == -1  # 자동 표면도 동일 06 §2 방향 규칙


def testIssueReadingsConsumesRegisteredFeed(tmp_path):
    # 등록 1줄 = 발행 사이클이 자동 소비 → 원장까지 표면 도달 (엔진 추가 자동흡수 end-to-end)
    from dartlab.simulate import readingCycle, readingLedger

    feed = fd.CompanyFeed(
        "quantX",
        lambda ctx: pl.DataFrame(
            {"code": ["a", "b", "c", "d", "e"], "week": [202607] * 5, "alpha1": [1.0, 2.0, 3.0, 4.0, 5.0]}
        ),
    )
    weekEnd = pl.DataFrame({"week": [202607], "date": ["20260213"]})
    weekMap = pl.DataFrame(schema={"date": pl.Utf8, "week": pl.Int64})
    fundM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "ep": pl.Float64, "bm": pl.Float64})
    try:
        fd.registerCompanyFeed(feed)
        readingCycle.issueReadings(
            week=202607,
            baseDir=tmp_path,
            matrices=(weekMap, weekEnd, _priceM(), fundM, _emptyEvent()),
            directionByType={},
        )
        led = readingLedger.readReadings(baseDir=tmp_path)
        assert "quantX.alpha1" in set(led["surface"].to_list())  # 피드 표면이 봉인 원장까지 자동 도달
    finally:
        fd.unregisterCompanyFeed("quantX")


def testOpineAutoSurfaceFromNewColumn():
    # table 행렬에 새 수치 컬럼 추가 = 표면 자동 (손 매핑 삭제 검증)
    priceM = _priceM().with_columns(newSignal=pl.Series([5.0, 4.0, 3.0, 2.0, 1.0]))
    fundM = pl.DataFrame(schema={"code": pl.Utf8, "week": pl.Int64, "ep": pl.Float64})
    r = opine.opine(priceM, fundM, _emptyEvent(), directionByType={})
    surfaces = set(r["surface"].unique().to_list())
    assert {"price.ret5", "price.newSignal"} <= surfaces  # 기존 + 신규 컬럼 둘 다 자동
    ns = {
        row["code"]: row["direction"] for row in r.filter(pl.col("surface") == "price.newSignal").iter_rows(named=True)
    }
    assert ns["a"] == 1 and ns["e"] == -1  # 역순 신호 = 방향 반대 (랭크 규칙 일관)
