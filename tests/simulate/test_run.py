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
def test_buildScenarioSheet_wires_one_node_per_macro_input_and_channel() -> None:
    sheet = buildScenarioSheet(_snapshot(baseRevenue=300.0), scenario="baseline", horizon=3)
    deps = {node.driverId: {sheet.nodes[dep].driverId for dep in node.deps} for node in sheet.nodes.values()}
    assert deps == {
        "macro.path": set(),
        "macro.rate": set(),
        "macro.fx": set(),
        "rev.path": {"macro.path", "macro.fx"},
        "margin.path": {"macro.path", "macro.rate"},
        "wacc.path": {"macro.rate"},
        "proforma": {"rev.path", "margin.path"},
        "dcf": {"proforma", "wacc.path"},
    }


def _sheetWithRatePath(snapshot: dict, rates: list[float]):
    """baseline 시트의 금리 root 만 바꾼다. 다른 입력이 같으므로 금리 채널만 격리된다."""
    from dartlab.simulate.registry import _FN_MACRO_RATE

    sheet = buildScenarioSheet(snapshot, scenario="baseline", horizon=3)
    snap = sheet.snapshot

    def ratePath(node, sht, deps):
        return rates[-1], tuple(rates), "preset:baseline", (), {"path": rates}, snap["asOf"], snap["latestAsOf"]

    sheet.registry[_FN_MACRO_RATE] = ratePath
    return sheet


@pytest.mark.unit
def test_rate_shock_reaches_wacc_and_dcf_but_not_revenue() -> None:
    """금리만 올린 경로는 매출을 건드리지 않고 WACC 경로를 올려 기업가치를 낮춘다."""
    from dartlab.synth.scenario import BASELINE_RATE

    flat = evaluateSheet(_sheetWithRatePath(_snapshot(baseRevenue=300.0), [BASELINE_RATE] * 3))
    shocked = evaluateSheet(_sheetWithRatePath(_snapshot(baseRevenue=300.0), [BASELINE_RATE + 2.0] * 3))

    assert shocked["rev.path@baseline#all"].vector == flat["rev.path@baseline#all"].vector
    assert flat["wacc.path@baseline#all"].vector == (10.0, 10.0, 10.0)
    assert shocked["wacc.path@baseline#all"].vector == (11.0, 11.0, 11.0)
    assert shocked["dcf@baseline#all"].vector[0] < flat["dcf@baseline#all"].vector[0]
    assert shocked["dcf@baseline#all"].inputsHash != flat["dcf@baseline#all"].inputsHash


@pytest.mark.unit
def test_margin_channel_reaches_proforma_fcf() -> None:
    """마진만 움직이는 탄성(매출 GDP 탄성 0)에서도 GDP 경로가 FCF 를 바꾼다. 표시용 경로가 아니다."""
    snapshot = _snapshot(baseRevenue=300.0)
    snapshot["elasticity"] = SectorElasticity(0.0, 0.0, 50, 0, "high")
    baseline = evaluateSheet(buildScenarioSheet(snapshot, scenario="baseline", horizon=3))
    adverse = evaluateSheet(buildScenarioSheet(snapshot, scenario="adverse", horizon=3))

    assert adverse["margin.path@adverse#all"].vector != baseline["margin.path@baseline#all"].vector
    assert adverse["proforma@adverse#all"].vector != baseline["proforma@baseline#all"].vector


@pytest.mark.unit
def test_transfer_channels_match_combined_transfer_byte_for_byte() -> None:
    from dartlab.simulate.transfer import (
        transferMarginChannel,
        transferRevenueChannel,
        transferRevenuePath,
        transferWaccChannel,
    )

    financials = SectorElasticity(0.4, -0.2, 20, 35, "moderate")
    for elasticity in (_SEMI, financials):
        gdp, rate, fx = [-3.0, 0.5, 2.2], [1.0, 3.5, 2.0], [1600, 1420, 1510]
        revenue, margin, wacc = transferRevenuePath(100.0, -49.0, gdp, rate, fx, elasticity, 9.0)
        assert transferRevenueChannel(100.0, gdp, fx, elasticity) == revenue
        assert transferMarginChannel(-49.0, gdp, rate, elasticity) == margin
        assert transferWaccChannel(9.0, rate) == wacc


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
    assert rev.refs == ("simulate.transfer:transferRevenueChannel",)
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


def _dcfNode():
    from dartlab.simulate.sheet import DriverNode

    return DriverNode(
        "dcf@baseline#all",
        "dcf",
        "baseline",
        "all",
        ("proforma@baseline#all", "wacc.path@baseline#all"),
        "simulate.dcf",
    )


def _dcfDeps(fcf: tuple, wacc: tuple) -> dict:
    from dartlab.simulate.sheet import NodeValue

    return {
        "proforma@baseline#all": NodeValue(100.0, fcf, "test", (), "a" * 64, "2024Q4", "2024Q4"),
        "wacc.path@baseline#all": NodeValue(wacc[-1], wacc, "test", (), "b" * 64, "2024Q4", "2024Q4"),
    }


@pytest.mark.unit
def test_dcf_node_blocks_incomplete_fcf_without_time_compaction() -> None:
    from dartlab.simulate.registry import _fnDcf
    from dartlab.simulate.sheet import DriverSheet

    sheet = DriverSheet(snapshot=_snapshot(baseRevenue=300.0))

    value, vector, provenance, *_ = _fnDcf(_dcfNode(), sheet, _dcfDeps((100.0, None, 100.0), (10.0, 10.0, 10.0)))

    assert value is None
    assert vector is None
    assert provenance == "dcf:gap(fcfPath_incomplete)"


@pytest.mark.unit
def test_dcf_node_blocks_invalid_terminal_growth_contract() -> None:
    from dartlab.simulate.registry import _fnDcf
    from dartlab.simulate.sheet import DriverSheet

    snapshot = _snapshot(baseRevenue=300.0)
    snapshot.update(terminalGrowth=3.0)
    sheet = DriverSheet(snapshot=snapshot)

    value, vector, provenance, *_ = _fnDcf(_dcfNode(), sheet, _dcfDeps((100.0, 100.0), (4.0, 3.0)))

    assert value is None
    assert vector is None
    assert provenance == "dcf:gap(terminalGrowth_not_below_wacc)"


@pytest.mark.unit
def test_dcf_node_flat_wacc_path_reproduces_constant_rate_formula() -> None:
    from dartlab.simulate.registry import _fnDcf
    from dartlab.simulate.sheet import DriverSheet

    snapshot = _snapshot(baseRevenue=300.0, netDebt=0.0)
    sheet = DriverSheet(snapshot=snapshot)
    fcf = (100.0, 110.0, 120.0)

    _value, vector, *_ = _fnDcf(_dcfNode(), sheet, _dcfDeps(fcf, (10.0, 10.0, 10.0)))

    pv = sum(cash / 1.1 ** (year + 1) for year, cash in enumerate(fcf))
    terminal = 120.0 * 1.03 / (0.10 - 0.03) / 1.1**3
    assert vector[0] == pytest.approx(round(pv + terminal, 2))


@pytest.mark.unit
def test_dcf_node_requires_wacc_dependency_instead_of_falling_back() -> None:
    from dartlab.simulate.registry import _fnDcf
    from dartlab.simulate.sheet import DriverSheet

    sheet = DriverSheet(snapshot=_snapshot(baseRevenue=300.0))
    deps = _dcfDeps((100.0, 100.0), (10.0, 10.0))
    deps.pop("wacc.path@baseline#all")

    with pytest.raises(ValueError, match="wacc.path"):
        _fnDcf(_dcfNode(), sheet, deps)


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
def test_finance_series_content_changes_proforma_and_dcf_hashes() -> None:
    first = _snapshot(baseRevenue=300.0)
    changed = _snapshot(baseRevenue=300.0)
    changed["series"]["CF"]["purchase_of_property_plant_and_equipment"] = [-200.0] * 4

    out1 = evaluateSheet(buildScenarioSheet(first, scenario="baseline", horizon=3))
    out2 = evaluateSheet(buildScenarioSheet(changed, scenario="baseline", horizon=3))

    assert out1["proforma@baseline#all"].vector != out2["proforma@baseline#all"].vector
    assert out1["proforma@baseline#all"].inputsHash != out2["proforma@baseline#all"].inputsHash
    assert out1["dcf@baseline#all"].inputsHash != out2["dcf@baseline#all"].inputsHash


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
def test_run_scenario_preserves_data_input_gaps_and_downgrades_quality(monkeypatch) -> None:
    from dartlab.simulate.run import runScenario

    snapshot = _snapshot(baseRevenue=300.0)
    snapshot["dataInputGaps"] = ("FEATURE_OBSERVATION_CONDITIONAL:unsigned exact history",)
    monkeypatch.setattr("dartlab.simulate.run.buildSnapshot", lambda company, asOf=None: snapshot)

    result = runScenario(object(), scenario="baseline", horizon=3)

    assert result.quality == "partial"
    assert result.dataInputGaps == ("FEATURE_OBSERVATION_CONDITIONAL:unsigned exact history",)
    assert any("FEATURE_OBSERVATION_CONDITIONAL" in warning for warning in result.warnings)


@pytest.mark.unit
def test_run_scenario_surfaces_structured_data_evidence(monkeypatch) -> None:
    from dartlab.simulate.run import runScenario

    snapshot = _snapshot(baseRevenue=300.0)
    snapshot["dataEvidence"] = {
        "status": "partial",
        "coverage": {
            "requestedAssets": 1,
            "resolvedAssets": 1,
            "succeededPartitions": 1,
            "failedPartitions": 0,
        },
        "assets": (("analysis.simulationInputs", "asset-version:test"),),
        "gaps": (
            {
                "code": "FEATURE_OBSERVATION_CONDITIONAL",
                "message": "unsigned history",
                "assetId": "analysis.simulationInputs",
                "subject": "000001",
                "systemic": False,
                "requestId": None,
            },
        ),
        "partitions": (
            {
                "assetId": "analysis.simulationInputs",
                "assetVersionId": "asset-version:test",
                "requestId": None,
                "selector": (("subject", "000001"),),
                "temporalStatus": "validAt",
                "contentHash": "p" * 64,
                "truncated": False,
            },
        ),
        "qualityAssertions": (),
        "catalogSnapshotId": "data-snapshot:test",
        "dataSnapshotId": "data-content-snapshot:test",
        "contractHash": "c" * 64,
        "lineageRefs": ("lineage:test",),
        "executionReceipts": ("data-execution:test",),
        "materializationReceiptJson": None,
    }
    monkeypatch.setattr("dartlab.simulate.run.buildSnapshot", lambda company, asOf=None: snapshot)

    result = runScenario(object(), scenario="baseline", horizon=3)

    assert result.quality == "partial"
    assert result.dataEvidence is not None
    assert result.dataEvidence.status == "partial"
    assert result.dataEvidence.gaps[0].code == "FEATURE_OBSERVATION_CONDITIONAL"
    assert result.dataEvidence.partitions[0].contentHash == "p" * 64


@pytest.mark.unit
def test_run_scenario_treats_unresolved_quality_assertion_as_partial(monkeypatch) -> None:
    from dartlab.simulate.run import runScenario

    snapshot = _snapshot(baseRevenue=300.0)
    snapshot["dataEvidence"] = {
        "status": "ok",
        "coverage": {
            "requestedAssets": 1,
            "resolvedAssets": 1,
            "succeededPartitions": 1,
            "failedPartitions": 0,
        },
        "assets": (),
        "gaps": (),
        "partitions": (),
        "qualityAssertions": (
            {
                "assertionId": "input.complete",
                "success": None,
                "severity": "error",
                "assetId": "analysis.simulationInputs",
            },
        ),
        "catalogSnapshotId": "data-snapshot:test",
        "dataSnapshotId": "data-content-snapshot:test",
        "contractHash": "c" * 64,
        "lineageRefs": (),
        "executionReceipts": (),
        "materializationReceiptJson": None,
    }
    monkeypatch.setattr("dartlab.simulate.run.buildSnapshot", lambda company, asOf=None: snapshot)

    result = runScenario(object(), scenario="baseline", horizon=3)

    assert result.quality == "partial"


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
        stockCode = "000001"
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

    monkeypatch.setattr("dartlab.simulate.registry._resolveSectorKey", lambda company: "반도체")

    snap = buildSnapshot(_FakeCompany(), asOf="2019Q4")

    assert snap["asOf"] == "2019-Q4"
    assert snap["latestAsOf"] == "2020-Q1"
    assert snap["requestedAsOf"] == "2019-Q4"
    assert snap["series"]["IS"]["sales"] == [10.0, 20.0, 30.0, 40.0]
    assert snap["baseRevenue"] == 100.0
    assert snap["baseMargin"] == 10.0
    assert snap["netDebt"] is None
    assert "netDebtUnavailable" in snap["warnings"]
    # 역사 시점의 발행주식수 vintage 가 없으므로 현재 shares 를 섞지 않고 결손으로 둔다.
    assert snap["shares"] is None
    assert "historicalSharesUnavailable" in snap["warnings"]
    assert snap["parameterVintageStatus"] == "unavailable"
    assert "historicalSimulationParametersUnavailable" in snap["warnings"]


@pytest.mark.unit
def test_historical_run_blocks_current_parameter_leak(monkeypatch) -> None:
    from dartlab.simulate.run import runScenario

    snapshot = _snapshot(baseRevenue=300.0)
    snapshot.update(
        asOf="2023-Q4",
        latestAsOf="2024-Q4",
        requestedAsOf="2023-Q4",
        parameterVintageStatus="unavailable",
        warnings=("historicalSimulationParametersUnavailable",),
    )
    monkeypatch.setattr("dartlab.simulate.run.buildSnapshot", lambda company, asOf=None: snapshot)

    result = runScenario(object(), scenario="baseline", horizon=3, asOf="2023Q4")

    assert result.quality == "partial"
    assert result.revenuePath is None
    assert result.marginPath is None
    assert "historical_parameter_vintage_absent" in result.nodes[DRIVER_REV].provenance


@pytest.mark.unit
def test_snapshot_rejects_asof_outside_available_periods(monkeypatch) -> None:
    class _FakeCompany:
        stockCode = "000001"
        sectorParams = None

        def _buildFinanceSeries(self, *, freq="Q"):
            return {"IS": {"sales": [1.0]}, "BS": {}, "CF": {}}, ["2020-Q1"]

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
        assert baseline.nodes[DRIVER_REV].refs == ("simulate.transfer:transferRevenueChannel",)
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
