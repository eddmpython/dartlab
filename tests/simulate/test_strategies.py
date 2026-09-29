"""Public `strategies` axis: one-company conditional strategy comparison across the KR presets.

Unit tests run over a synthetic snapshot (no Company load). They pin the contract the axis sells:
every preset is a case, every case runs the same strategies on one common path, the leader is the
feasible strategy with the highest terminal net cash, and nothing is ever a recommendation. One
realData test runs the public verb on 005930.
"""

from __future__ import annotations

import gc
from types import SimpleNamespace

import pytest

from dartlab.simulate import strategies as strategiesModule
from dartlab.simulate.entry import resolveSimulateCall
from dartlab.simulate.strategies import StrategyCase, compareStrategies, summarizeCases
from dartlab.synth.scenario import SectorElasticity, getPresetScenarios

_PRESETS = tuple(sorted(getPresetScenarios("KR")))


def _series(*, withPpe: bool = True) -> dict:
    q = 8
    balance = {
        "cash_and_cash_equivalents": [20.0] * q,
        "shortterm_borrowings": [10.0] * q,
        "longterm_borrowings": [20.0] * q,
        "debentures": [0.0] * q,
        "trade_receivables": [10.0] * q,
        "inventories": [10.0] * q,
        "trade_payables": [10.0] * q,
        "tangible_assets": [50.0] * q,
        "total_assets": [120.0] * q,
        "total_liabilities": [70.0] * q,
        "total_stockholders_equity": [50.0] * q,
        "current_assets": [50.0] * q,
        "current_liabilities": [30.0] * q,
    }
    if not withPpe:
        balance.pop("tangible_assets")
    return {
        "IS": {
            "sales": [25.0] * q,
            "operating_profit": [3.75] * q,
            "profit_before_tax": [3.0] * q,
            "income_tax_expense": [0.6] * q,
            "finance_costs": [0.75] * q,
            "gross_profit": [10.0] * q,
            "selling_and_administrative_expenses": [5.0] * q,
            "net_profit": [2.4] * q,
        },
        "BS": balance,
        "CF": {
            "depreciation": [1.25] * q,
            "purchase_of_property_plant_and_equipment": [2.0] * q,
            "dividends_paid": [0.5] * q,
        },
    }


def _snapshot(**overrides) -> dict:
    snapshot = {
        "series": _series(),
        "baseRevenue": 100.0,
        "baseMargin": 15.0,
        "netDebt": 10.0,
        "shares": 1000,
        "elasticity": SectorElasticity(1.8, 0.8, 50, 0, "high"),
        "sectorKey": "반도체",
        "baseWacc": 10.0,
        "terminalGrowth": 3.0,
        "asOf": "2025-Q4",
        "latestAsOf": "2025-Q4",
        "assumptions": (),
        "warnings": (),
        "parameterVintageStatus": "available",
    }
    snapshot.update(overrides)
    return snapshot


@pytest.fixture
def snapshotHolder(monkeypatch):
    holder = {"snapshot": _snapshot()}
    monkeypatch.setattr(strategiesModule, "buildSnapshot", lambda company, asOf=None: holder["snapshot"])
    return holder


def _company():
    return SimpleNamespace(stockCode="000000")


@pytest.mark.unit
def test_every_preset_is_a_case_and_nothing_is_a_recommendation(snapshotHolder) -> None:
    result = compareStrategies(_company(), horizon=3)

    assert tuple(case.scenarioName for case in result.cases) == _PRESETS
    assert result.decisionStatus == "conditionalOnly"
    assert result.recommendation is None
    assert all(case.decisionStatus == "conditionalOnly" for case in result.cases)
    assert {"policyEvaluationCertificateMissing", "caseLeaderIsNotRecommendation"} <= set(result.blockedReasons)
    assert [item.strategyId for item in result.strategies] == ["hold", "expand", "deleverage"]
    for case in result.cases:
        assert [outcome.strategyId for outcome in case.outcomes] == ["hold", "expand", "deleverage"]
        assert len(case.shockPath) == 3


@pytest.mark.unit
def test_case_leader_is_the_best_feasible_terminal_net_cash(snapshotHolder) -> None:
    result = compareStrategies(_company(), horizon=3)

    for case in result.cases:
        ranked = sorted((o for o in case.outcomes if o.feasible), key=lambda o: (-o.terminalNetCash, o.strategyId))
        assert case.leaderStrategyId == ranked[0].strategyId
        assert case.leaderMargin == pytest.approx(ranked[0].terminalNetCash - ranked[1].terminalNetCash)
        assert case.leaderMarginRatio == pytest.approx(case.leaderMargin / 100.0)
    fragile = min(result.cases, key=lambda case: (case.leaderMarginRatio, case.scenarioName))
    assert result.fragileCase == fragile.scenarioName


@pytest.mark.unit
def test_rate_hike_preset_raises_the_debt_rate_path(snapshotHolder) -> None:
    result = compareStrategies(_company(), horizon=3)
    byName = {case.scenarioName: case for case in result.cases}

    hike = [step["debtRate"] for step in byName["rate_hike"].shockPath]
    base = [step["debtRate"] for step in byName["baseline"].shockPath]
    assert hike[-1] > base[-1]


@pytest.mark.unit
def test_comparison_is_deterministic(snapshotHolder) -> None:
    first = compareStrategies(_company(), horizon=3)
    second = compareStrategies(_company(), horizon=3)

    assert [case.runHash for case in first.cases] == [case.runHash for case in second.cases]
    assert first.leaderByCase == second.leaderByCase


@pytest.mark.unit
def test_missing_account_is_an_honest_gap_not_zero(snapshotHolder) -> None:
    snapshotHolder["snapshot"] = _snapshot(series=_series(withPpe=False))

    result = compareStrategies(_company(), horizon=3)

    assert result.cases == ()
    assert result.quality == "partial"
    assert result.gaps and "ppe" in result.gaps[0]
    assert result.recommendation is None


@pytest.mark.unit
def test_historical_period_abstains_without_parameter_vintage(snapshotHolder) -> None:
    snapshotHolder["snapshot"] = _snapshot(parameterVintageStatus="unavailable")

    result = compareStrategies(_company(), horizon=3)

    assert result.cases == ()
    assert result.gaps == ("historical_parameter_vintage_absent",)


@pytest.mark.unit
def test_horizon_beyond_the_presets_is_rejected_before_work() -> None:
    with pytest.raises(ValueError, match="horizon"):
        compareStrategies(_company(), horizon=99)


def _case(name: str, leader: str | None, ratio: float | None) -> StrategyCase:
    return StrategyCase(
        name, leader, None if ratio is None else ratio * 100.0, ratio, (), (), (), "conditionalOnly", "x"
    )


@pytest.mark.unit
def test_summary_reports_reversal_and_the_case_closest_to_flipping() -> None:
    summary = summarizeCases(
        (
            _case("adverse", "deleverage", 0.002),
            _case("baseline", "hold", 0.010),
            _case("rate_hike", "deleverage", 0.001),
        )
    )

    assert summary["leaderReversal"] is True
    assert summary["stableLeader"] is None
    assert summary["reversalCases"] == ("adverse", "rate_hike")
    assert summary["fragileCase"] == "rate_hike"


@pytest.mark.unit
def test_summary_names_a_stable_leader_only_when_every_case_has_one() -> None:
    stable = summarizeCases((_case("adverse", "hold", 0.01), _case("baseline", "hold", 0.02)))
    missing = summarizeCases((_case("adverse", None, None), _case("baseline", "hold", 0.02)))

    assert stable["stableLeader"] == "hold" and stable["leaderReversal"] is False
    assert missing["stableLeader"] is None and missing["allLed"] is False


@pytest.mark.unit
def test_company_axis_contract() -> None:
    from dartlab.providers.dart.company import Company

    with pytest.raises(ValueError, match="scenario"):
        Company.simulate(SimpleNamespace(), "strategies", scenario="adverse")
    with pytest.raises(ValueError, match="축"):
        Company.simulate(SimpleNamespace(), "unknown")


@pytest.mark.unit
def test_entry_axis_parsing() -> None:
    assert resolveSimulateCall("005930", None) == ("scenario", "005930")
    assert resolveSimulateCall("scenario", "005930") == ("scenario", "005930")
    assert resolveSimulateCall("strategies", "005930") == ("strategies", "005930")
    with pytest.raises(ValueError, match="종목코드"):
        resolveSimulateCall("strategies", None)
    with pytest.raises(ValueError, match="축"):
        resolveSimulateCall("bogus", "005930")


@pytest.mark.realData
@pytest.mark.serial
def test_realData_strategies_axis_005930() -> None:
    import dartlab

    result = dartlab.simulate("strategies", "005930", horizon=3)
    try:
        if result.gaps:
            pytest.skip(f"005930 financial state unavailable: {result.gaps}")
        assert tuple(case.scenarioName for case in result.cases) == _PRESETS
        assert result.decisionStatus == "conditionalOnly"
        assert result.recommendation is None
        assert all(case.leaderStrategyId is not None for case in result.cases)
        assert result.fragileCase in _PRESETS
    finally:
        del result
        gc.collect()
