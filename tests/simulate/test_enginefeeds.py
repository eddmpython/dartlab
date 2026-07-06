"""엔진 피드 배선 : industry 업종 동행 모멘텀·credit 자금조달 압력·멱등 설치 (순수 유닛).

Covers:
- industryFeedProvider: 업종 중앙 mom20x5, 최소 종목 수 미달 업종 무행, ctx priceM 재사용.
- creditFeedProvider: 52주 rolling 자금조달 건수(주 격자 인덱스), 0건 종목 무행, 시장별 타입.
- installEngineFeeds 멱등 + 레지스트리 등재.
"""

from __future__ import annotations

import polars as pl

from dartlab.simulate import enginefeeds as ef
from dartlab.simulate import feeds as fd


def testIndustryFeedMedianAndMinSize(monkeypatch):
    from dartlab.simulate import table

    # 업종 X = 5종목 (중앙 계산), 업종 Y = 1종목 (미달 무행)
    codes = [f"x{i}" for i in range(5)] + ["y0"]
    priceM = pl.DataFrame({"code": codes, "week": [202607] * 6, "mom20x5": [0.01, 0.02, 0.03, 0.04, 0.05, 0.9]})
    imap = pl.DataFrame({"code": codes, "industry": ["X"] * 5 + ["Y"]})
    monkeypatch.setattr(table, "industryMap", lambda baseDir=None: imap)
    out = ef.industryFeedProvider({"priceM": priceM, "market": "KR"})
    byCode = {r["code"]: r["indMom"] for r in out.iter_rows(named=True)}
    assert byCode["x0"] == 0.03  # 업종 중앙값
    assert "y0" not in byCode  # 최소 종목 수 미달 = 무행 (강제 0 금지)


def testCreditFeedRollingWindow():
    # 유상증자 2건 (202601, 202603): 창 내 누적 2 → 202601 이전은 무행
    eventM = pl.DataFrame(
        {"code": ["a", "a"], "week": [202601, 202603], "reportType": ["유상증자결정", "전환사채권발행결정"]}
    )
    weekEnd = pl.DataFrame({"week": [202601, 202602, 202603, 202604], "date": ["d1", "d2", "d3", "d4"]})
    out = ef.creditFeedProvider({"eventM": eventM, "weekEnd": weekEnd, "market": "KR"})
    byWeek = {r["week"]: r["fin52w"] for r in out.iter_rows(named=True)}
    assert byWeek[202601] == 1.0 and byWeek[202602] == 1.0  # 발생 후 창 유지
    assert byWeek[202603] == 2.0 and byWeek[202604] == 2.0  # 누적
    # US 시장: 한국 타입 미매치 = 무행, securitiesOffering 매치
    usEv = pl.DataFrame({"code": ["b"], "week": [202601], "reportType": ["securitiesOffering"]})
    usOut = ef.creditFeedProvider({"eventM": usEv, "weekEnd": weekEnd, "market": "US"})
    assert usOut.height > 0 and usOut["code"].unique().to_list() == ["b"]


def testEstimateFeedForwardEp(monkeypatch):
    from dartlab.simulate import estimate, table

    # E 층 시뮬 소비 루프: 다음 분기 순이익 E(p50) / 시총 = epFwd (최신 주 한정)
    rows = []
    for y in (2023, 2024, 2025):
        for qn, v in zip((1, 2, 3, 4), (10.0, 20.0, 30.0, 40.0)):
            rows.append(
                {
                    "code": "a",
                    "period": f"{y}Q{qn}",
                    "rceptDate": f"{y}{qn * 2 + 3:02d}15",
                    "account": "netIncome",
                    "amount": v,
                }
            )
    monkeypatch.setattr(estimate, "quarterGrid", lambda market, d=None: pl.DataFrame(rows))
    monkeypatch.setattr(
        table, "marketCap", lambda d=None: pl.DataFrame({"date": ["20260110"], "code": ["a"], "mktcap": [1000.0]})
    )
    weekEnd = pl.DataFrame({"week": [202602], "date": ["20260110"]})
    out = ef.estimateFeedProvider({"weekEnd": weekEnd, "market": "KR"})
    r = out.row(0, named=True)
    assert r["week"] == 202602 and abs(r["epFwd"] - 10.0 / 1000.0) < 1e-12  # 완전 계절 E=10 / 시총 1000


def testInstallEngineFeedsIdempotent():
    before = {f.axis for f in fd.companyFeeds()}
    try:
        ef.installEngineFeeds()
        ef.installEngineFeeds()  # 재설치 = 교체 (중복 없음)
        axes = [f.axis for f in fd.companyFeeds()]
        assert axes.count("industry") == 1 and axes.count("credit") == 1 and axes.count("estimate") == 1
    finally:
        for axis in {"industry", "credit", "estimate"} - before:
            fd.unregisterCompanyFeed(axis)
