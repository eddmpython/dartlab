"""L2.5 simulate foundation — sheet structures, topo executor, and the macro transfer.

Pure-unit tests (no Company load) cover:
- NodeValue determinism (computeInputsHash stability + normalization).
- buildOrder topological order + cycle / missing-dep errors.
- evaluateSheet end-to-end on a synthetic DAG + byte-identical re-run.
- transferMacroToFundamentals numeric port (vs the documented legacy parity) and
  transferRevenuePath carry, on synthetic inputs.

One realData test runs the minimal macro -> rev -> proforma DAG on 005930, calls the L2 leaf
buildProforma once, and asserts a ProFormaYear + deterministic inputsHash. The Company is
released with `del` immediately after.
"""

from __future__ import annotations

import pytest

from dartlab.simulate.sheet import (
    DriverNode,
    DriverSheet,
    NodeValue,
    buildOrder,
    computeInputsHash,
    evaluateSheet,
)
from dartlab.simulate.transfer import (
    transferMacroToFundamentals,
    transferRevenuePath,
)
from dartlab.synth.scenario import SectorElasticity

# 반도체 elasticity (matches synth.scenario.SECTOR_ELASTICITY["반도체"]).
_SEMI = SectorElasticity(1.8, 0.8, 50, 0, "high")


# ──────────────────────────────────────────────────────────────────────
# computeInputsHash — determinism + normalization
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.unit
def test_inputsHash_is_64_hex() -> None:
    h = computeInputsHash((), "macro.path", {"gdp": [1.5, 2.0, 2.2]})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


@pytest.mark.unit
def test_inputsHash_stable_across_calls() -> None:
    a = computeInputsHash(("aa", "bb"), "fn", {"x": 1.0, "y": [2.0, 3.0]})
    b = computeInputsHash(("aa", "bb"), "fn", {"x": 1.0, "y": [2.0, 3.0]})
    assert a == b


@pytest.mark.unit
def test_inputsHash_parent_order_independent() -> None:
    # sorted internally -> parent order must not change the hash.
    a = computeInputsHash(("aa", "bb"), "fn", {"x": 1.0})
    b = computeInputsHash(("bb", "aa"), "fn", {"x": 1.0})
    assert a == b


@pytest.mark.unit
def test_inputsHash_float_normalized() -> None:
    # 1e-12 jitter below the 1e-9 rounding floor -> same hash.
    a = computeInputsHash((), "fn", {"x": 1.0})
    b = computeInputsHash((), "fn", {"x": 1.0 + 1e-12})
    assert a == b
    # a real difference above the floor -> different hash.
    c = computeInputsHash((), "fn", {"x": 1.001})
    assert a != c


@pytest.mark.unit
def test_inputsHash_sensitive_to_fn_and_inputs() -> None:
    base = computeInputsHash((), "fnA", {"x": 1.0})
    assert base != computeInputsHash((), "fnB", {"x": 1.0})
    assert base != computeInputsHash((), "fnA", {"x": 2.0})


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (["a,b", "c"], ["a", "b,c"]),
        ({"a:b": "c"}, {"a": "b:c"}),
        (None, "None"),
        ([1, 2], (1, 2)),
        (True, 1),
    ],
)
def test_inputsHash_preserves_types_and_container_boundaries(left, right) -> None:
    assert computeInputsHash((), "fn", left) != computeInputsHash((), "fn", right)


def test_inputsHash_rejects_unstable_object_fallback() -> None:
    with pytest.raises(TypeError, match="cannot encode"):
        computeInputsHash((), "fn", object())


# ──────────────────────────────────────────────────────────────────────
# buildOrder — topological order + errors
# ──────────────────────────────────────────────────────────────────────
def _node(nid: str, deps: tuple[str, ...], fn: str = "f") -> DriverNode:
    return DriverNode(nid, nid, "base", "all", deps, fn)


@pytest.mark.unit
def test_buildOrder_linear() -> None:
    s = DriverSheet()
    s.add(_node("a", ()))
    s.add(_node("b", ("a",)))
    s.add(_node("c", ("b",)))
    assert buildOrder(s) == ("a", "b", "c")


@pytest.mark.unit
def test_buildOrder_deterministic_ties() -> None:
    # two independent roots -> sorted by nodeId, stable across runs.
    s = DriverSheet()
    s.add(_node("z", ()))
    s.add(_node("a", ()))
    s.add(_node("m", ("a", "z")))
    order = buildOrder(s)
    assert order.index("a") < order.index("m")
    assert order.index("z") < order.index("m")
    assert order[:2] == ("a", "z")  # sorted ties


@pytest.mark.unit
def test_buildOrder_cycle_raises() -> None:
    s = DriverSheet()
    s.add(_node("a", ("b",)))
    s.add(_node("b", ("a",)))
    with pytest.raises(ValueError, match="cycle"):
        buildOrder(s)


@pytest.mark.unit
def test_buildOrder_missing_dep_raises() -> None:
    s = DriverSheet()
    s.add(_node("a", ("ghost",)))
    with pytest.raises(ValueError, match="missing"):
        buildOrder(s)


@pytest.mark.unit
def test_sheet_add_rejects_duplicate() -> None:
    s = DriverSheet()
    s.add(_node("a", ()))
    with pytest.raises(ValueError, match="duplicate"):
        s.add(_node("a", ()))


# ──────────────────────────────────────────────────────────────────────
# evaluateSheet — executor end to end + determinism + errors
# ──────────────────────────────────────────────────────────────────────
def _buildSyntheticSheet() -> DriverSheet:
    """A 3-node synthetic DAG: const -> double -> add-parent. No dartlab leaf, pure arithmetic."""
    sheet = DriverSheet(snapshot={"seed": 2.0})

    def fnConst(node, sht, deps):
        v = sht.snapshot["seed"]
        return (v, (v,), "const", ("ref:seed",), {"seed": v}, "2024Q4", "2024Q4")

    def fnDouble(node, sht, deps):
        parent = deps["a@base#all"]
        v = parent.value * 2
        return (v, (v,), "double", ("ref:double",), {"in": parent.value}, "2024Q4", "2024Q4")

    def fnAdd(node, sht, deps):
        v = deps["a@base#all"].value + deps["b@base#all"].value
        frozen = {"a": deps["a@base#all"].value, "b": deps["b@base#all"].value}
        return (v, (v,), "add", ("ref:add",), frozen, "2024Q4", "2024Q4")

    sheet.registry["fnConst"] = fnConst
    sheet.registry["fnDouble"] = fnDouble
    sheet.registry["fnAdd"] = fnAdd
    sheet.add(DriverNode("a@base#all", "a", "base", "all", (), "fnConst"))
    sheet.add(DriverNode("b@base#all", "b", "base", "all", ("a@base#all",), "fnDouble"))
    sheet.add(DriverNode("c@base#all", "c", "base", "all", ("a@base#all", "b@base#all"), "fnAdd"))
    return sheet


@pytest.mark.unit
def test_evaluateSheet_resolves_deps() -> None:
    out = evaluateSheet(_buildSyntheticSheet())
    assert out["a@base#all"].value == 2.0
    assert out["b@base#all"].value == 4.0
    assert out["c@base#all"].value == 6.0  # 2 + 4
    assert out["c@base#all"].provenance == "add"
    assert out["c@base#all"].refs == ("ref:add",)


@pytest.mark.unit
def test_evaluateSheet_writes_det_back() -> None:
    sheet = _buildSyntheticSheet()
    evaluateSheet(sheet)
    assert isinstance(sheet.nodes["c@base#all"].det, NodeValue)
    assert sheet.nodes["c@base#all"].det.value == 6.0
    assert sheet.nodes["c@base#all"].ai is None  # deterministic core never touches the lens slot


@pytest.mark.unit
def test_evaluateSheet_rerun_byte_identical() -> None:
    out1 = evaluateSheet(_buildSyntheticSheet())
    out2 = evaluateSheet(_buildSyntheticSheet())
    for nid in out1:
        a, b = out1[nid], out2[nid]
        assert a.value == b.value
        assert a.vector == b.vector
        assert a.inputsHash == b.inputsHash
        assert a.provenance == b.provenance
        assert a.refs == b.refs


@pytest.mark.unit
def test_evaluateSheet_inputsHash_propagates() -> None:
    # changing an upstream input changes the downstream hash (chained inputsHash).
    s1 = _buildSyntheticSheet()
    s2 = _buildSyntheticSheet()
    s2.snapshot["seed"] = 3.0
    out1 = evaluateSheet(s1)
    out2 = evaluateSheet(s2)
    assert out1["a@base#all"].inputsHash != out2["a@base#all"].inputsHash
    assert out1["c@base#all"].inputsHash != out2["c@base#all"].inputsHash


@pytest.mark.unit
def test_evaluateSheet_missing_registry_fn_raises() -> None:
    s = DriverSheet()
    s.add(DriverNode("a@base#all", "a", "base", "all", (), "fnGhost"))
    with pytest.raises(ValueError, match="registry fn"):
        evaluateSheet(s)


# ──────────────────────────────────────────────────────────────────────
# transfer — numeric port + carry (synthetic inputs)
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.unit
def test_transfer_single_year_documented_values() -> None:
    rev, mgn, wacc = transferMacroToFundamentals(
        100.0, 10.0, gdp=-3.0, rate=1.0, fx=1600, elasticity=_SEMI, baseWacc=10.0
    )
    # value verified byte-identical to the live legacy _applyMacroShock (see
    # test_transfer_recomputes_legacy_arithmetic); the concept-proof docstring example was stale.
    assert round(rev, 4) == 95.3075
    assert round(mgn, 4) == 8.5
    assert round(wacc, 4) == 9.25


@pytest.mark.unit
def test_transfer_recomputes_legacy_arithmetic() -> None:
    # Independently recompute the legacy formula and assert byte-equality with the port.
    from dartlab.synth.scenario import BASELINE_FX, BASELINE_RATE

    baseRev, baseMargin, baseWacc = 300.0, 15.0, 10.0
    gdp, rate, fx = -3.0, 1.0, 1600.0
    revGdpEffect = _SEMI.revenueToGdp * gdp / 100
    fxChangePct = (fx - BASELINE_FX) / BASELINE_FX * 100
    revFxEffect = _SEMI.revenueToFx * fxChangePct / 1000
    expRev = baseRev * (1 + revGdpEffect + revFxEffect)
    expMargin = max(baseMargin + _SEMI.marginToGdp * gdp / 100 + _SEMI.nimToRate * (rate - BASELINE_RATE) / 100, -50)
    expWacc = baseWacc + (rate - BASELINE_RATE) * 0.5

    gotRev, gotMargin, gotWacc = transferMacroToFundamentals(baseRev, baseMargin, gdp, rate, fx, _SEMI, baseWacc)
    assert gotRev == expRev
    assert gotMargin == expMargin
    assert gotWacc == expWacc


@pytest.mark.unit
def test_transfer_margin_floor() -> None:
    # a catastrophic GDP shock floors margin at -50 (legacy max(margin, -50)).
    _, mgn, _ = transferMacroToFundamentals(100.0, 0.0, gdp=-200.0, rate=2.5, fx=1470, elasticity=_SEMI, baseWacc=10.0)
    assert mgn == -50


@pytest.mark.unit
def test_transfer_baseline_macro_no_shock() -> None:
    # at baseline (gdp=0, rate=BASELINE_RATE, fx=BASELINE_FX) revenue/margin/wacc are unchanged.
    from dartlab.synth.scenario import BASELINE_FX, BASELINE_RATE

    rev, mgn, wacc = transferMacroToFundamentals(
        100.0, 10.0, gdp=0.0, rate=BASELINE_RATE, fx=BASELINE_FX, elasticity=_SEMI, baseWacc=10.0
    )
    assert rev == 100.0
    assert mgn == 10.0
    assert wacc == 10.0


@pytest.mark.unit
def test_transferRevenuePath_carry() -> None:
    rev, mgn, wacc = transferRevenuePath(
        100.0, 10.0, [-3.0, -1.0, 0.5], [1.0, 1.5, 2.0], [1600, 1580, 1550], _SEMI, 10.0
    )
    assert len(rev) == len(mgn) == len(wacc) == 3
    # year 1's base is year 0's adjusted revenue (the carry): recompute year 1 from rev[0].
    y1 = transferMacroToFundamentals(rev[0], mgn[0], -1.0, 1.5, 1580, _SEMI, 10.0)
    assert rev[1] == y1[0]
    assert mgn[1] == y1[1]


@pytest.mark.unit
def test_transferRevenuePath_horizon_is_min_length() -> None:
    rev, mgn, wacc = transferRevenuePath(100.0, 10.0, [1.0, 2.0], [2.5], [1470, 1470], _SEMI, 10.0)
    assert len(rev) == 1  # min(2, 1, 2)


# ──────────────────────────────────────────────────────────────────────
# realData — minimal macro -> rev -> proforma DAG on one company
# ──────────────────────────────────────────────────────────────────────
_BASELINE_GDP = [1.5, 2.0, 2.2]
_BASELINE_RATE_PATH = [2.5, 2.5, 2.5]
_BASELINE_FX_PATH = [1470.0, 1470.0, 1470.0]


def _buildRealDag(series: dict, baseRevenue: float, baseMargin: float, asOf: str) -> DriverSheet:
    """macro.path -> rev.path (transfer edge) -> proforma (L2 leaf buildProforma). One leaf call."""
    from dartlab.analysis.financial.proforma import buildProforma

    sheet = DriverSheet(snapshot={"series": series, "baseRevenue": baseRevenue, "baseMargin": baseMargin})

    def fnMacroPath(node, sht, deps):
        gdp = tuple(_BASELINE_GDP)
        frozen = {"gdp": list(_BASELINE_GDP), "rate": list(_BASELINE_RATE_PATH), "fx": list(_BASELINE_FX_PATH)}
        return (gdp[-1], gdp, "preset:baseline", ("synth.scenario:PRESET_SCENARIOS_KR/baseline",), frozen, asOf, asOf)

    def fnRevPath(node, sht, deps):
        revPath, marginPath, waccPath = transferRevenuePath(
            sht.snapshot["baseRevenue"],
            sht.snapshot["baseMargin"],
            list(_BASELINE_GDP),
            list(_BASELINE_RATE_PATH),
            list(_BASELINE_FX_PATH),
            _SEMI,
            baseWacc=10.0,
        )
        frozen = {"rev": revPath, "margin": marginPath, "wacc": waccPath}
        prov = "transfer:rev*(1+bgdp*gdp+bfx*fxDelta),margin+bm*gdp,wacc+0.5*rateDelta"
        return (revPath[-1], tuple(revPath), prov, ("simulate.transfer:transferRevenuePath",), frozen, asOf, asOf)

    def fnProforma(node, sht, deps):
        revPath = list(deps["rev.path@baseline#all"].vector)
        base = sht.snapshot["baseRevenue"]
        # edge wiring: buildProforma wants a growth path (% per year); transfer gives an absolute
        # revenue path. Convert here (the node owns the wiring, not the leaf math).
        growthPath: list[float] = []
        prev = base
        for r in revPath:
            growthPath.append((r / prev - 1.0) * 100.0 if prev else 0.0)
            prev = r
        pf = buildProforma(sht.snapshot["series"], revenueGrowthPath=growthPath, scenarioName="baseline")
        proj = pf.projections
        ni = tuple(round(y.net_income, 2) for y in proj)
        frozen = {"growthPath": [round(g, 9) for g in growthPath], "wacc": round(pf.wacc, 9)}
        prov = f"proforma:cashplug,wacc={pf.wacc:.2f},years={len(proj)}"
        return (
            round(proj[-1].revenue, 2) if proj else None,
            ni,
            prov,
            ("analysis.financial.proforma:buildProforma",),
            frozen,
            asOf,
            asOf,
        )

    sheet.registry["fnMacroPath"] = fnMacroPath
    sheet.registry["fnRevPath"] = fnRevPath
    sheet.registry["fnProforma"] = fnProforma
    sheet.add(DriverNode("macro.path@baseline#all", "macro.path", "baseline", "all", (), "fnMacroPath"))
    sheet.add(
        DriverNode("rev.path@baseline#all", "rev.path", "baseline", "all", ("macro.path@baseline#all",), "fnRevPath")
    )
    sheet.add(
        DriverNode("proforma@baseline#all", "proforma", "baseline", "all", ("rev.path@baseline#all",), "fnProforma")
    )
    return sheet


@pytest.mark.realData
@pytest.mark.serial
def test_realData_macro_rev_proforma_dag() -> None:
    """005930: macro -> rev -> proforma DAG produces a ProFormaYear + deterministic inputsHash."""
    from dartlab.analysis.forecast.simulation import _extractBaseMetrics
    from dartlab.providers.dart.company import Company

    c = Company("005930")
    try:
        ts = c._buildFinanceSeries(freq="Q")
        series = ts[0] if isinstance(ts, tuple) else ts
        if not series:
            pytest.skip("005930 finance series unavailable — realData skip environment")
        base = _extractBaseMetrics(series)
        baseRev = base["revenue"] or 0.0
        if baseRev <= 0:
            pytest.skip("005930 base revenue unavailable — realData skip environment")
        baseMargin = base["margin"] if base["margin"] is not None else 10.0
        asOf = "2024Q4"

        sheet = _buildRealDag(series, baseRev, baseMargin, asOf)
        out = evaluateSheet(sheet)

        pf = out["proforma@baseline#all"]
        # the L2 leaf produced IS/BS/CF projections (ProFormaYear vector = per-year net income).
        assert pf.value is not None
        assert pf.vector is not None and len(pf.vector) > 0
        assert pf.provenance.startswith("proforma:cashplug")
        assert pf.refs == ("analysis.financial.proforma:buildProforma",)

        # deterministic: a fresh sheet over the same snapshot gives the same inputsHash.
        sheet2 = _buildRealDag(series, baseRev, baseMargin, asOf)
        out2 = evaluateSheet(sheet2)
        for nid in out:
            assert out[nid].inputsHash == out2[nid].inputsHash
            assert out[nid].value == out2[nid].value
            assert out[nid].vector == out2[nid].vector
    finally:
        del c
