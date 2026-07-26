"""L2.5 simulate registry + runScenario - deterministic driver DAG end to end.

Unit tests (no Company load) cover the registry node fns over a synthetic snapshot:
- buildScenarioSheet wiring (4 nodes: macro -> rev -> proforma -> dcf) + topo evaluation.
- the transfer edge (rev.path) carries the macro shock onto base revenue.
- honest-gap: an absent base revenue cascades to None node values + a `partial` quality status
  (never 0), and the proforma leaf is not consulted on the gap path.
- determinism: a fresh sheet over the same synthetic snapshot yields identical per-node
  inputsHashes.
- adverse vs baseline: the adverse macro preset yields a lower terminal revenue.

One realData test (serial) runs `runScenario(Company("005930"))` for baseline + adverse, asserts
the revenue path / proforma populated, the inputsHash is deterministic across a re-run, and the
adverse scenario gives a lower terminal revenue than baseline. The Company is released with `del`.
"""

from __future__ import annotations

import pytest

from dartlab.simulate.registry import (
    DRIVER_DCF,
    DRIVER_PROFORMA,
    DRIVER_REV,
    buildScenarioSheet,
    buildSnapshot,
)
from dartlab.simulate.sheet import evaluateSheet
from dartlab.synth.scenario import SectorElasticity

# 반도체 elasticity (matches synth.scenario.SECTOR_ELASTICITY["반도체"]).
_SEMI = SectorElasticity(1.8, 0.8, 50, 0, "high")


def _syntheticSeries() -> dict:
    """A minimal IS/BS/CF series (4 quarters) sufficient for buildProforma to project."""
    rev = [70.0, 72.0, 74.0, 76.0]
    return {
        "IS": {
            "sales": rev,
            "gross_profit": [r * 0.4 for r in rev],
            "selling_and_administrative_expenses": [r * 0.2 for r in rev],
            "operating_profit": [r * 0.2 for r in rev],
            "profit_before_tax": [r * 0.18 for r in rev],
            "income_tax_expense": [r * 0.04 for r in rev],
            "net_profit": [r * 0.14 for r in rev],
        },
        "CF": {
            "operating_cashflow": [r * 0.22 for r in rev],
            "purchase_of_property_plant_and_equipment": [-r * 0.06 for r in rev],
            "depreciation_and_amortization": [r * 0.05 for r in rev],
            "dividends_paid": [-r * 0.03 for r in rev],
        },
        "BS": {
            "current_assets": [120.0, 122.0, 124.0, 126.0],
            "current_liabilities": [60.0, 61.0, 62.0, 63.0],
            "cash_and_cash_equivalents": [40.0, 41.0, 42.0, 43.0],
            "total_assets": [300.0, 305.0, 310.0, 315.0],
            "total_liabilities": [120.0, 121.0, 122.0, 123.0],
            "total_stockholders_equity": [180.0, 184.0, 188.0, 192.0],
            "shortterm_borrowings": [20.0, 20.0, 20.0, 20.0],
            "longterm_borrowings": [30.0, 30.0, 30.0, 30.0],
            "trade_receivables": [50.0, 51.0, 52.0, 53.0],
            "inventories": [40.0, 41.0, 42.0, 43.0],
            "trade_payables": [30.0, 31.0, 32.0, 33.0],
        },
    }


def _snapshot(
    *,
    baseRevenue: float | None,
    withSeries: bool = True,
    shares: int | None = 1000,
    netDebt: float | None = 10.0,
) -> dict:
    """A synthetic frozen snapshot (no Company) matching buildSnapshot's shape."""
    return {
        "series": _syntheticSeries() if withSeries else None,
        "baseRevenue": baseRevenue,
        "baseMargin": 20.0 if baseRevenue is not None else None,
        "netDebt": netDebt,
        "shares": shares,
        "elasticity": _SEMI,
        "sectorKey": "반도체",
        "baseWacc": 10.0,
        "terminalGrowth": 3.0,
        "asOf": "2024Q4",
        "latestAsOf": "2024Q4",
    }


# ──────────────────────────────────────────────────────────────────────
# wiring + evaluation over a synthetic snapshot
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.unit
def test_buildScenarioSheet_has_four_nodes() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3)
    assert len(sheet.nodes) == 4
    assert {n.driverId for n in sheet.nodes.values()} == {"macro.path", "rev.path", "proforma", "dcf"}


@pytest.mark.unit
def test_evaluate_synthetic_dag_macro_to_proforma() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3)
    out = evaluateSheet(sheet)
    macro = out["macro.path@baseline#all"]
    rev = out["rev.path@baseline#all"]
    pf = out["proforma@baseline#all"]
    assert macro.provenance == "preset:baseline"
    assert macro.vector is not None and len(macro.vector) == 3
    assert rev.vector is not None and len(rev.vector) == 3
    assert rev.provenance.startswith("transfer:")
    assert rev.refs == ("simulate.transfer:transferRevenuePath",)
    # the L2 leaf produced projections (per-year FCF vector) + terminal revenue value.
    assert pf.value is not None
    assert pf.vector is not None and len(pf.vector) > 0
    assert pf.provenance.startswith("proforma:cashplug")
    assert pf.refs == ("analysis.financial.proforma:buildProforma",)


@pytest.mark.unit
def test_revPath_carries_macro_shock() -> None:
    # baseline (gdp positive) grows revenue above base; the transfer edge is wired.
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3)
    out = evaluateSheet(sheet)
    revVec = out["rev.path@baseline#all"].vector
    # baseline gdp = [1.5, 2.0, 2.2], fx = baseline (no fx shock) -> revenue grows.
    assert revVec[0] > 300.0


@pytest.mark.unit
def test_dcf_node_perShare_from_proforma_fcf() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0, shares=1000), scenario="baseline", horizon=3)
    out = evaluateSheet(sheet)
    dcf = out["dcf@baseline#all"]
    assert dcf.provenance.startswith("dcf:fcff")
    # enterprise value rides in the 1-tuple vector; per-share is the value (shares present).
    assert dcf.vector is not None and len(dcf.vector) == 1
    assert dcf.value is not None


@pytest.mark.unit
def test_dcf_node_honest_gap_when_shares_absent() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0, shares=None), scenario="baseline", horizon=3)
    out = evaluateSheet(sheet)
    dcf = out["dcf@baseline#all"]
    assert dcf.value is None  # honest-gap: no shares -> no per-share, NOT 0
    assert "shares_absent" in dcf.provenance


@pytest.mark.unit
def test_dcf_node_honest_gap_when_net_debt_absent() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0, netDebt=None), scenario="baseline", horizon=3)
    dcf = evaluateSheet(sheet)["dcf@baseline#all"]
    assert dcf.value is None
    assert dcf.vector is not None
    assert "netDebt_absent" in dcf.provenance


# ──────────────────────────────────────────────────────────────────────
# honest-gap: absent base revenue cascades to None (never 0)
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.unit
def test_honest_gap_absent_base_revenue_cascades() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=None), scenario="baseline", horizon=3)
    out = evaluateSheet(sheet)
    rev = out["rev.path@baseline#all"]
    pf = out["proforma@baseline#all"]
    dcf = out["dcf@baseline#all"]
    # rev path is a gap (None, not 0) and the proforma leaf is NOT consulted.
    assert rev.value is None
    assert rev.vector is None
    assert "gap" in rev.provenance
    assert pf.value is None
    assert "gap" in pf.provenance
    assert dcf.value is None


@pytest.mark.unit
def test_honest_gap_missing_series_skips_leaf() -> None:
    # base revenue present but series absent -> proforma is a gap, leaf not called.
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0, withSeries=False), scenario="baseline", horizon=3)
    out = evaluateSheet(sheet)
    pf = out["proforma@baseline#all"]
    assert pf.value is None
    assert "gap" in pf.provenance


# ──────────────────────────────────────────────────────────────────────
# determinism over the synthetic snapshot
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.unit
def test_synthetic_rerun_byte_identical() -> None:
    s1 = buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3)
    s2 = buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3)
    out1 = evaluateSheet(s1)
    out2 = evaluateSheet(s2)
    for nid in out1:
        assert out1[nid].inputsHash == out2[nid].inputsHash
        assert out1[nid].value == out2[nid].value
        assert out1[nid].vector == out2[nid].vector
        assert out1[nid].provenance == out2[nid].provenance


@pytest.mark.unit
def test_inputs_hash_includes_data_vintage() -> None:
    latest = _snapshot(baseRevenue=300.0)
    historical = dict(latest)
    historical["asOf"] = "2023-Q4"
    out1 = evaluateSheet(buildScenarioSheet(latest, scenario="baseline", horizon=3))
    out2 = evaluateSheet(buildScenarioSheet(historical, scenario="baseline", horizon=3))
    assert out1["macro.path@baseline#all"].inputsHash != out2["macro.path@baseline#all"].inputsHash


@pytest.mark.unit
def test_run_scenario_surfaces_assumptions_and_warnings(monkeypatch) -> None:
    from dartlab.simulate.run import runScenario

    snapshot = _snapshot(baseRevenue=300.0)
    snapshot.update(
        requestedAsOf="2023-Q4",
        assumptions=("baseWacc10Pct",),
        warnings=("periodScopedPitOnly",),
    )
    monkeypatch.setattr("dartlab.simulate.run.buildSnapshot", lambda company, asOf=None: snapshot)

    result = runScenario(object(), scenario="baseline", horizon=3, asOf="2023Q4")

    assert result.quality == "partial"
    assert result.assumptions == ("baseWacc10Pct",)
    assert "periodScopedPitOnly" in result.warnings
    assert result.requestedAsOf == "2023-Q4"


@pytest.mark.unit
def test_run_scenario_preserves_lens_context_without_changing_driver_hashes(monkeypatch) -> None:
    from dartlab.simulate.run import runScenario

    snapshot = _snapshot(baseRevenue=300.0)
    monkeypatch.setattr("dartlab.simulate.run.buildSnapshot", lambda company, asOf=None: snapshot)
    product = {
        "identity": {"engine": "macro"},
        "assumptions": [{"id": "edgeSign", "value": "registryPrior"}],
        "scenarios": [{"id": "ratesUp"}],
    }

    plain = runScenario(object(), scenario="baseline", horizon=3)
    contextual = runScenario(
        object(),
        scenario="baseline",
        horizon=3,
        lensBundle={"products": {"macro": product}},
    )

    assert contextual.lensProducts == {"macro": product}
    assert len(contextual.assumptionLedger) == 2
    assert all(row["appliedToDriverSheet"] is False for row in contextual.assumptionLedger)
    assert {key: row.inputsHash for key, row in contextual.nodes.items()} == {
        key: row.inputsHash for key, row in plain.nodes.items()
    }


@pytest.mark.unit
def test_adverse_lower_revenue_than_baseline() -> None:
    base = evaluateSheet(buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3))
    adv = evaluateSheet(buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="adverse", horizon=3))
    baseRevTerminal = base["rev.path@baseline#all"].value
    advRevTerminal = adv["rev.path@adverse#all"].value
    assert advRevTerminal < baseRevTerminal  # recession shrinks the revenue path


@pytest.mark.unit
def test_unknown_scenario_is_rejected() -> None:
    """조용한 baseline 폴백은 입력과 provenance 를 서로 다르게 만들어 금지한다."""
    with pytest.raises(ValueError, match="scenario"):
        buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="not-a-scenario", horizon=3)


@pytest.mark.unit
@pytest.mark.parametrize("horizon", [0, -1, 4, True])
def test_horizon_outside_preset_path_is_rejected(horizon) -> None:
    """결과 horizon 과 실제 벡터 길이가 달라지는 요청은 계산 전에 차단한다."""
    with pytest.raises((TypeError, ValueError), match="horizon"):
        buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=horizon)


@pytest.mark.unit
def test_snapshot_asof_slices_quarterly_series_and_keeps_latest_separate(monkeypatch) -> None:
    """asOf 는 라벨이 아니라 분기 시리즈 절단이며 latestAsOf 와 분리된다."""

    class _FakeCompany:
        sectorParams = None

        def _buildFinanceSeries(self, *, freq="Q"):
            assert freq == "Q"
            periods = ["2019-Q1", "2019-Q2", "2019-Q3", "2019-Q4", "2020-Q1"]
            series = {
                "IS": {
                    "sales": [10.0, 20.0, 30.0, 40.0, 1000.0],
                    "operating_profit": [1.0, 2.0, 3.0, 4.0, 500.0],
                },
                "BS": {
                    "cash_and_cash_equivalents": [1.0, 2.0, 3.0, 4.0, 999.0],
                    "shortterm_borrowings": [2.0, 3.0, 4.0, 5.0, 999.0],
                },
                "CF": {},
            }
            return series, periods

    monkeypatch.setattr("dartlab.simulate.registry._getSeriesAndShares", lambda company: (None, 100, "KRW"))
    monkeypatch.setattr("dartlab.simulate.registry._resolveSectorKey", lambda company: "반도체")

    snap = buildSnapshot(_FakeCompany(), asOf="2019Q4")

    assert snap["asOf"] == "2019-Q4"
    assert snap["latestAsOf"] == "2020-Q1"
    assert snap["requestedAsOf"] == "2019-Q4"
    assert snap["series"]["IS"]["sales"] == [10.0, 20.0, 30.0, 40.0]
    assert snap["baseRevenue"] == 100.0
    assert snap["baseMargin"] == 10.0
    assert snap["netDebt"] == 1.0
    # 역사 시점의 발행주식수 vintage 가 없으므로 현재 shares 를 섞지 않고 결손으로 둔다.
    assert snap["shares"] is None
    assert "historicalSharesUnavailable" in snap["warnings"]


@pytest.mark.unit
def test_snapshot_rejects_asof_outside_available_periods(monkeypatch) -> None:
    class _FakeCompany:
        sectorParams = None

        def _buildFinanceSeries(self, *, freq="Q"):
            return {"IS": {"sales": [1.0]}, "BS": {}, "CF": {}}, ["2020-Q1"]

    monkeypatch.setattr("dartlab.simulate.registry._getSeriesAndShares", lambda company: (None, 100, "KRW"))
    monkeypatch.setattr("dartlab.simulate.registry._resolveSectorKey", lambda company: None)

    with pytest.raises(ValueError, match="asOf"):
        buildSnapshot(_FakeCompany(), asOf="2019Q4")
    with pytest.raises(ValueError, match="asOf"):
        buildSnapshot(_FakeCompany(), asOf="2021Q1")


# ──────────────────────────────────────────────────────────────────────
# realData - runScenario on one company (serial, del after)
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.realData
@pytest.mark.serial
def test_realData_runScenario_005930() -> None:
    """005930: runScenario(baseline) populates paths + proforma; deterministic; adverse < baseline."""
    from dartlab.providers.dart.company import Company
    from dartlab.simulate.run import runScenario

    c = Company("005930")
    try:
        baseline = runScenario(c, scenario="baseline", horizon=3)
        if baseline.revenuePath is None or baseline.proformaYears == 0:
            pytest.skip("005930 finance series unavailable - realData skip environment")

        # paths + proforma populated.
        assert baseline.scenarioName == "baseline"
        assert len(baseline.revenuePath) == 3
        assert baseline.proformaYears > 0
        assert baseline.fcfPath is not None
        assert baseline.nodes[DRIVER_REV].refs == ("simulate.transfer:transferRevenuePath",)
        assert baseline.nodes[DRIVER_PROFORMA].provenance.startswith("proforma:cashplug")
        assert baseline.nodes[DRIVER_DCF].provenance.startswith("dcf:fcff")

        # deterministic: a second run produces identical per-node inputsHashes.
        baseline2 = runScenario(c, scenario="baseline", horizon=3)
        for driverId, audit in baseline.nodes.items():
            assert audit.inputsHash == baseline2.nodes[driverId].inputsHash

        # adverse scenario gives a lower terminal revenue than baseline (qualitative).
        adverse = runScenario(c, scenario="adverse", horizon=3)
        assert adverse.revenuePath is not None
        assert adverse.revenuePath[-1] < baseline.revenuePath[-1]
    finally:
        del c
