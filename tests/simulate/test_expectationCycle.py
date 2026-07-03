"""Expectation cycle : issue/score/scorecard orchestration on injected fixtures (pure unit).

Covers (no network, no Company):
- issueMacro seals the contract (5 quantiles, 3 baselines sealed at issuance, live flag),
  and is idempotent per (variable, horizon, targetPeriod, issuedLive).
- scoreDue: not-due rows skipped, due rows scored, publication-lag grace honored, and a
  row past the grace window with no actual is sealed as an error row.
- buildScorecard: groups by variable x horizon x live, forces verified=False under the
  sample gate, and counts unscored/error rows honestly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.simulate.expectationCycle import buildScorecard, issueMacro, scoreDue


@dataclass
class FakeSimResult:
    status: str = "ok"
    model: dict = field(default_factory=lambda: {"endYm": "2026-05"})
    fan: dict = field(default_factory=dict)
    missing: list = field(default_factory=list)


def makeFan() -> dict:
    horizon = 12

    def rec(prefix: str, base: float) -> dict:
        out = {"transform": "logdiff100" if prefix == "level_q" else "level", "label": "x", "seriesId": "x"}
        for q, off in ((5, -2.0), (25, -1.0), (50, 0.0), (75, 1.0), (95, 2.0)):
            out[f"{prefix}{q}"] = [base + off + 0.1 * h for h in range(horizon)]
        return out

    return {
        "소비자물가": rec("level_q", 120.0),
        "기준금리": rec("q", 2.5),
        "원/달러": rec("level_q", 1400.0),
    }


def makeMonthly() -> dict[str, dict[str, float]]:
    yms = [f"{y}-{m:02d}" for y in range(2020, 2027) for m in range(1, 13)]
    yms = [ym for ym in yms if ym <= "2026-06"]
    return {
        "CPI": {ym: 100.0 + i * 0.3 for i, ym in enumerate(yms)},
        "BASE_RATE": {ym: 2.5 for ym in yms},
        "USDKRW": {ym: 1300.0 + i for i, ym in enumerate(yms)},
    }


def issueFixture(tmp_path, *, live=True):
    return issueMacro(
        live=live,
        horizons=(1, 3),
        baseDir=tmp_path,
        simResult=FakeSimResult(fan=makeFan()),
        monthlyBySeries=makeMonthly(),
    )


def test_issue_seals_contract_and_baselines(tmp_path):
    rows = issueFixture(tmp_path)
    assert len(rows) == 6  # 3 vars x 2 horizons
    r = rows[0]
    assert r.issuedLive is True and r.kind == "quantiles"
    assert set(r.baselines) == {"randomWalk", "persistence", "seasonalNaive"}
    assert isinstance(r.baselines["randomWalk"], dict) and len(r.baselines["randomWalk"]) == 5
    assert r.targetPeriod in ("2026-06", "2026-08")  # endYm 2026-05 + h


def test_issue_idempotent_same_month(tmp_path):
    first = issueFixture(tmp_path)
    second = issueFixture(tmp_path)
    assert len(first) == 6 and len(second) == 0  # re-run skips existing keys


def test_score_due_grace_and_error_seal(tmp_path):
    issueFixture(tmp_path)
    monthly = makeMonthly()
    # now=2026-07 : h=1 target 2026-06 due(actual 있음) · h=3 target 2026-08 미도래
    scores = scoreDue(now="2026-07", baseDir=tmp_path, monthlyBySeries=monthly)
    assert len(scores) == 3 and all(s.error is None for s in scores)
    # CPI 2026-06 실측 대조: crps 가 손계산 pinball 과 일치하는 행 존재
    assert any(s.crps is not None and s.crps >= 0 for s in scores)
    # now=2026-11 : 2026-08 은 due+3개월 경과인데 monthly 가 2026-06 까지뿐 -> error 봉인
    scores2 = scoreDue(now="2026-11", baseDir=tmp_path, monthlyBySeries=monthly)
    assert len(scores2) == 3 and all(s.error is not None for s in scores2)


def test_score_publication_lag_stays_pending(tmp_path):
    issueFixture(tmp_path)
    monthly = makeMonthly()
    for sid in monthly:
        monthly[sid].pop("2026-06", None)  # 발표 지연 시뮬
    scores = scoreDue(now="2026-07", baseDir=tmp_path, monthlyBySeries=monthly)
    assert scores == []  # grace 안에서는 error 봉인 없이 pending


@dataclass
class FakeRevenueResult:
    projected: list = field(default_factory=lambda: [110.0, 120.0, 130.0])
    scenarios: dict = field(
        default_factory=lambda: {
            "base": [110.0, 120.0, 130.0],
            "bull": [125.0, 140.0, 155.0],
            "bear": [95.0, 100.0, 105.0],
        }
    )
    method: str = "ensemble"
    sources: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)


def revenueFixture(tmp_path, *, live=True):
    from dartlab.simulate.expectationCycle import issueRevenue

    annual = {"005930": {2021: 80.0, 2022: 90.0, 2023: 95.0, 2024: 100.0, 2025: 105.0}}
    return issueRevenue(
        ["005930", "999999"],
        live=live,
        baseDir=tmp_path,
        resultByCode={"005930": FakeRevenueResult()},
        annualByCode=annual,
    )


def test_issue_revenue_quantile_mapping_and_census(tmp_path):
    rows, skipped = revenueFixture(tmp_path)
    assert len(rows) == 3 and skipped == {"999999": "예측 불가(projected 없음)"}
    r1 = next(r for r in rows if r.horizon == 1)
    assert r1.targetPeriod == "FY2026" and r1.freq == "Y"
    q = r1.quantiles
    assert (q[25], q[50], q[75]) == (95.0, 110.0, 125.0)  # bear/base/bull -> p25/p50/p75
    assert q[5] < q[25] and q[95] > q[75]  # 정규 근사 꼬리 확장
    assert "scenarioQuantileApprox" in r1.warnings
    assert r1.baselines["persistence"] == 105.0  # 최신 완결 FY 매출 봉인


def test_score_revenue_due_grace_and_actual(tmp_path):
    revenueFixture(tmp_path)
    annual = {"005930": {2026: 118.0}}
    # FY2026 은 2027-04 부터 due
    assert scoreDue(now="2027-03", baseDir=tmp_path, annualRevenueByCode=annual, monthlyBySeries={}) == []
    scores = scoreDue(now="2027-04", baseDir=tmp_path, annualRevenueByCode=annual, monthlyBySeries={})
    assert len(scores) == 1 and scores[0].error is None
    assert scores[0].coverageHit50 is True  # 118 in [95, 125]
    # FY2027 는 2028-04 due + grace 3개월: actual 없으면 2028-06 까지 pending, 2028-07 error 봉인
    assert scoreDue(now="2028-06", baseDir=tmp_path, annualRevenueByCode=annual, monthlyBySeries={}) == []
    scores2 = scoreDue(now="2028-07", baseDir=tmp_path, annualRevenueByCode=annual, monthlyBySeries={})
    assert len(scores2) == 1 and scores2[0].error is not None


class _FakePfYear:
    def __init__(self, operating_income, net_income):
        self.operating_income = operating_income
        self.net_income = net_income


class _FakePfResult:
    def __init__(self, factor):
        # 매출 성장경로에 단조 반응: growth% 합에 비례하는 이익 (계보 검증용 결정론)
        self.projections = [_FakePfYear(10.0 * factor + h, 7.0 * factor + h) for h in range(3)]


def _fakeProforma(series, growthPathPct, name):
    return _FakePfResult(factor=1.0 + sum(growthPathPct) / 100.0)


def test_issue_earnings_cascade_and_lineage(tmp_path):
    from dartlab.simulate.expectationCycle import issueEarnings

    revenueFixture(tmp_path)  # 모체 매출 기대 봉인 (005930)
    rows, skipped = issueEarnings(
        ["005930", "111111"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    assert skipped == {"111111": "매출 기대 없음(선행 issueRevenue 필요)"}
    assert len(rows) == 6  # 2 metric x 3 horizon
    r = next(r for r in rows if r.variable == "005930.operatingProfit" and r.horizon == 1)
    assert r.domain == "earnings" and r.targetPeriod == "FY2026"
    q = r.quantiles
    assert q[25] <= q[50] <= q[75]  # 단조 캐스케이드 보존
    assert r.sourceRefs[0].startswith("revenue.005930.revenue.Y1.FY2026@")  # 모체 계보
    assert "revenueQuantileMapped" in r.warnings
    # 결정론 재현: 같은 입력 재실행은 idempotent skip (기존 키)
    rows2, _ = issueEarnings(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    assert rows2 == []


def test_issue_earnings_seals_structured_proforma(tmp_path):
    from dartlab.simulate.expectationCycle import _PF_ACCOUNTS, issueEarnings
    from dartlab.simulate.expectationLedger import readProforma

    revenueFixture(tmp_path)
    issueEarnings(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    pf = readProforma(baseDir=tmp_path, code="005930")
    assert pf is not None
    # 34계정 x 3분위 x 3연도 = 306행, 계보(parentId) = 모체 매출 기대 행
    assert pf.height == len(_PF_ACCOUNTS) * 3 * 3
    row = pf.row(0, named=True)
    assert row["parentId"].startswith("revenue.005930.revenue.")
    assert set(pf.get_column("statement").unique().to_list()) == {"IS", "BS", "CF"}
    # 자체 존재키 idempotency: 재실행해도 계정 행 불변
    issueEarnings(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    assert readProforma(baseDir=tmp_path, code="005930").height == pf.height


def test_score_earnings_actual(tmp_path):
    from dartlab.simulate.expectationCycle import issueEarnings

    revenueFixture(tmp_path)
    issueEarnings(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    scores = scoreDue(
        now="2027-04",
        baseDir=tmp_path,
        monthlyBySeries={},
        annualRevenueByCode={"005930": {2026: 118.0}},
        fundamentalsByCode={"005930": {"operatingProfit": {2026: 11.5}, "netIncome": {2026: 8.2}}},
    )
    byVar = {}
    for s in scores:
        byVar.setdefault(s.expectationId.split(".")[2], s)
    assert len(scores) == 3  # revenue h1 + OP h1 + NI h1
    assert all(s.error is None for s in scores)


def test_issue_and_score_credit_stay_probability(tmp_path):
    from dartlab.simulate.expectationCycle import issueCredit

    hist = {"005930": [{"timestamp": "2026-06-30", "grade": "dCR-AA"}]}
    rows, skipped = issueCredit(
        ["005930", "222222"],
        live=True,
        baseDir=tmp_path,
        historyByCode=hist,
        stayProbByGrade={"dCR-AA": 0.9},
    )
    assert len(rows) == 1 and "222222" in skipped
    r = rows[0]
    assert r.kind == "direction" and r.direction["predicted"] == "stay" and r.direction["prob"] == 0.9
    target = r.targetPeriod  # 발행월 다음 분기
    # 분기말 후 등급 유지 -> actual "stay", brier = (0.9-1)^2
    histAfter = {"005930": hist["005930"] + [{"timestamp": "2027-01-15", "grade": "dCR-AA"}]}
    scores = scoreDue(now="2027-02", baseDir=tmp_path, monthlyBySeries={}, historyByCode=histAfter)
    creditScores = [s for s in scores if s.expectationId.startswith("credit.")]
    assert len(creditScores) == 1 and creditScores[0].brier is not None
    assert abs(creditScores[0].brier - 0.01) < 1e-9
    assert target.endswith("Q") is False  # sanity: "YYYYQn" 형식


def test_issue_and_score_price_direction(tmp_path):
    from dartlab.simulate.expectationCycle import issuePriceDirection

    rows, skipped = issuePriceDirection(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        mcUpsideByCode={"005930": 0.62},
        issuePriceByCode={"005930": 60000.0},
    )
    assert len(rows) == 1 and skipped == {}
    r = rows[0]
    assert r.direction["predicted"] == "up" and "mcUpsideProxy" in r.warnings
    target = r.targetPeriod
    closeUp = {"005930": {target: 66000.0}}
    scores = scoreDue(
        now=f"{int(target[:4]) + (target[5:7] == '12')}-{'01' if target[5:7] == '12' else f'{int(target[5:7]) + 1:02d}'}",
        baseDir=tmp_path,
        monthlyBySeries={},
        closeByCodeMonth=closeUp,
    )
    priceScores = [s for s in scores if s.expectationId.startswith("price.")]
    assert len(priceScores) == 1
    assert abs(priceScores[0].brier - (0.62 - 1.0) ** 2) < 1e-9  # actual up, predicted up


def test_scorecard_groups_and_sample_gate(tmp_path):
    issueFixture(tmp_path)
    scoreDue(now="2026-07", baseDir=tmp_path, monthlyBySeries=makeMonthly())
    card = buildScorecard(baseDir=tmp_path)
    assert card["totals"]["issued"] == 6 and card["totals"]["scored"] == 3
    assert card["totals"]["unscored"] == 3
    key = "macro.KR.CPI.M1.live"  # freq 포함 키: 분기/연간 동일 variable 혼입 차단
    assert key in card["groups"]
    assert card["groups"][key]["n"] == 1 and card["groups"][key]["verified"] is False


def quarterlyFixture(tmp_path, *, now="2026-07", years=(1,), published=frozenset({"2026Q1"})):
    """연간 매출·손익 봉인 후 분기 분해 발행 (계절성 주입: 매출 편중, 영업이익 균등).

    published 기본 = Q1 공시완료 (now=7월: Q2 는 분기말 경과·미공시 = nowcast 대상).
    """
    from dartlab.simulate.expectationCycle import issueEarnings, issueQuarterlyIs

    revenueFixture(tmp_path)
    issueEarnings(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    return issueQuarterlyIs(
        ["005930", "222222"],
        live=True,
        years=years,
        baseDir=tmp_path,
        seasonalityByCode={"005930": ([0.2, 0.3, 0.1, 0.4], [0.25, 0.25, 0.25, 0.25])},
        publishedByCode={"005930": set(published)},
        now=now,
    )


def test_issue_quarterly_seasonal_split_lineage_and_data_gate(tmp_path):
    from dartlab.simulate.expectationCycle import issueQuarterlyIs
    from dartlab.simulate.expectationLedger import readProforma

    rows, skipped = quarterlyFixture(tmp_path)
    assert skipped == {"222222": "연간 매출 기대 없음(h1, 선행 issueRevenue 필요)"}
    # 데이터 게이트: Q1 은 실제값 공시완료 -> 제외. Q2 는 분기말 경과·미공시 -> nowcast 발행.
    assert len(rows) == 6
    assert {r.targetPeriod for r in rows} == {"2026Q2", "2026Q3", "2026Q4"}
    revQ3 = next(r for r in rows if r.variable == "005930.revenue" and r.targetPeriod == "2026Q3")
    assert revQ3.freq == "Q" and revQ3.horizon == 3 and revQ3.domain == "revenue"
    # 연간 h1 (p25=95, p50=110, p75=125) x Q3 비중 0.1 = 시나리오 일관 분해
    assert abs(revQ3.quantiles[50] - 11.0) < 1e-9
    assert abs(revQ3.quantiles[25] - 9.5) < 1e-9 and abs(revQ3.quantiles[75] - 12.5) < 1e-9
    assert revQ3.sourceRefs[0].startswith("revenue.005930.revenue.Y1.FY2026@")  # 모체 계보
    assert "seasonalSplitOfAnnual" in revQ3.warnings and "quarterEndedAtIssue" not in revQ3.warnings
    revQ2 = next(r for r in rows if r.variable == "005930.revenue" and r.targetPeriod == "2026Q2")
    assert "quarterEndedAtIssue" in revQ2.warnings  # 분기말 경과·미공시 = nowcast 라벨
    opQ4 = next(r for r in rows if r.variable == "005930.operatingProfit" and r.targetPeriod == "2026Q4")
    assert opQ4.domain == "earnings" and "flatSeasonalityFallback" in opQ4.warnings
    # E-3표 분기 행: 3분기 x 3분위 x 2계정 = 18행 (연간 발행분과 별개)
    pf = readProforma(baseDir=tmp_path, code="005930")
    qpf = pf.filter(pf["targetPeriod"].str.contains("Q"))
    assert qpf.height == 18 and set(qpf.get_column("account").unique().to_list()) == {"revenue", "operating_income"}
    # idempotent 재실행
    rows2, _ = issueQuarterlyIs(
        ["005930"],
        live=True,
        years=(1,),
        baseDir=tmp_path,
        seasonalityByCode={"005930": ([0.2, 0.3, 0.1, 0.4], [0.25, 0.25, 0.25, 0.25])},
        publishedByCode={"005930": {"2026Q1"}},
        now="2026-07",
    )
    assert rows2 == [] and readProforma(baseDir=tmp_path, code="005930").height == pf.height


def test_issue_quarterly_skips_quarters_already_in_data(tmp_path):
    """공시완료 분기(실제값이 SSOT 에 존재)는 라이브 발행 금지 (달력 아님, 데이터 기준)."""
    rows, _ = quarterlyFixture(tmp_path, published={"2026Q1", "2026Q2"})
    assert {r.targetPeriod for r in rows} == {"2026Q3", "2026Q4"}
    assert all("quarterEndedAtIssue" not in r.warnings for r in rows)


def test_issue_quarterly_default_splits_next_fiscal_year_too(tmp_path):
    """기본 years=(1,2): 당해 잔여분기(Q2~Q4) + 차년 4분기 전부, 차년 계보 = FY2027 매출 부모."""
    rows, _ = quarterlyFixture(tmp_path, years=(1, 2))
    assert {r.targetPeriod for r in rows} == {
        "2026Q2",
        "2026Q3",
        "2026Q4",
        "2027Q1",
        "2027Q2",
        "2027Q3",
        "2027Q4",
    }
    assert len(rows) == 14  # (3 + 4) 분기 x 2지표
    q1 = next(r for r in rows if r.variable == "005930.revenue" and r.targetPeriod == "2027Q1")
    assert q1.horizon == 1 and q1.sourceRefs[0].startswith("revenue.005930.revenue.Y2.FY2027@")


def test_series_seasonality_from_finance_quarters():
    """_buildFinanceSeries(freq=Q) 형태에서 계절성: 완비 연도만, panel Q4 결손 대체 경로."""
    from dartlab.simulate.expectationCycle import _seriesSeasonality

    periods = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2", "2025-Q3"]
    series = {"IS": {"sales": [1.0, 2.0, 3.0, 4.0, 9.0, 9.0, 9.0]}}
    # 2025 는 Q4 미도래 -> 표본 제외, 2024 만
    assert _seriesSeasonality(series, periods, "sales", ["2024", "2025"]) == [0.1, 0.2, 0.3, 0.4]
    assert _seriesSeasonality(series, periods, "sales", ["2023"]) == [0.25] * 4
    assert _seriesSeasonality({"IS": {}}, periods, "sales", ["2024"]) == [0.25] * 4


def test_issue_quarterly_annual_cascade_not_polluted(tmp_path):
    """분기 행이 원장에 있어도 issueEarnings 연간 캐스케이드는 freq=Y 만 읽는다."""
    from dartlab.simulate.expectationCycle import issueEarnings

    quarterlyFixture(tmp_path)
    rows2, _ = issueEarnings(
        ["005930"],
        live=True,
        baseDir=tmp_path,
        proformaFn=_fakeProforma,
        seriesByCode={"005930": {"IS": {}}},
        annualByCode={"005930": {2025: 105.0}},
    )
    assert rows2 == []  # 분기 행 혼입으로 horizon 맵이 깨지면 여기서 재발행이 일어난다


def test_score_quarterly_due_grace_and_actual(tmp_path):
    quarterlyFixture(tmp_path)
    actuals = {
        "005930": {
            "revenue": {"2026Q2": 30.0, "2026Q3": 11.5},
            "operatingProfit": {"2026Q2": 2.4, "2026Q3": 2.6},
        }
    }
    # Q2(nowcast, 분기말 2026-06) 는 2026-08 due, Q3(분기말 2026-09) 는 2026-11 due
    early = scoreDue(now="2026-10", baseDir=tmp_path, monthlyBySeries={}, quarterlyByCode=actuals)
    assert len(early) == 2 and all(".2026Q2@" in s.expectationId for s in early)
    scores = scoreDue(now="2026-11", baseDir=tmp_path, monthlyBySeries={}, quarterlyByCode=actuals)
    q3 = [s for s in scores if ".2026Q3@" in s.expectationId]
    assert len(scores) == 2 and len(q3) == 2 and all(s.error is None for s in q3)
    rev = next(s for s in q3 if s.expectationId.startswith("revenue."))
    assert rev.coverageHit50 is True  # 11.5 in [9.5, 12.5]
    # Q4(분기말 2026-12) 는 2027-02 due + grace 3개월: 실적 없으면 2027-04 pending, 2027-05 error 봉인
    assert scoreDue(now="2027-03", baseDir=tmp_path, monthlyBySeries={}, quarterlyByCode=actuals) == []
    late = scoreDue(
        now="2027-05",
        baseDir=tmp_path,
        monthlyBySeries={},
        quarterlyByCode=actuals,
        annualRevenueByCode={"005930": {2026: 118.0}},
        fundamentalsByCode={"005930": {"operatingProfit": {2026: 11.5}, "netIncome": {2026: 8.2}}},
    )
    q4 = [s for s in late if ".2026Q4@" in s.expectationId]
    assert len(q4) == 2 and all(s.error is not None for s in q4)  # 결측 봉인(생존편향 금지)


def test_scorecard_separates_nowcast_group(tmp_path):
    """nowcast(분기말 경과 후 발행) 채점은 일반 예측 그룹과 혼합 집계 금지."""
    quarterlyFixture(tmp_path)
    actuals = {
        "005930": {
            "revenue": {"2026Q2": 30.0, "2026Q3": 11.5},
            "operatingProfit": {"2026Q2": 2.4, "2026Q3": 2.6},
        }
    }
    scoreDue(now="2026-10", baseDir=tmp_path, monthlyBySeries={}, quarterlyByCode=actuals)
    scoreDue(now="2026-11", baseDir=tmp_path, monthlyBySeries={}, quarterlyByCode=actuals)
    card = buildScorecard(baseDir=tmp_path)
    assert "revenue.005930.revenue.Q2.live.nowcast" in card["groups"]
    assert "revenue.005930.revenue.Q3.live" in card["groups"]
