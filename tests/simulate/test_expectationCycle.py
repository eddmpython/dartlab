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


def test_scorecard_groups_and_sample_gate(tmp_path):
    issueFixture(tmp_path)
    scoreDue(now="2026-07", baseDir=tmp_path, monthlyBySeries=makeMonthly())
    card = buildScorecard(baseDir=tmp_path)
    assert card["totals"]["issued"] == 6 and card["totals"]["scored"] == 3
    assert card["totals"]["unscored"] == 3
    key = "macro.KR.CPI.h1.live"
    assert key in card["groups"]
    assert card["groups"][key]["n"] == 1 and card["groups"][key]["verified"] is False
