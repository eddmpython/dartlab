"""거시 root 와 전달 채널 node 단위 회귀. registry 배선 없이 node 계약만 고정한다."""

from __future__ import annotations

import pytest

from dartlab.simulate.channels import (
    DEFAULT_BASE_MARGIN,
    DRIVER_FX,
    DRIVER_MACRO,
    DRIVER_RATE,
    PRESET_MARKET,
    dependencyValue,
    effectiveBaseMargin,
    gapValue,
    macroFxNode,
    macroPathNode,
    macroRateNode,
    marginPathNode,
    nodeIdFor,
    revenuePathNode,
    waccPathNode,
)
from dartlab.simulate.sheet import DriverNode, DriverSheet, NodeValue
from dartlab.simulate.transfer import transferMarginChannel, transferRevenueChannel, transferWaccChannel
from dartlab.synth.scenario import SectorElasticity, getPresetScenarios

# 금융 섹터처럼 금리 NIM 민감도가 있는 elasticity. 마진 채널의 금리 항까지 움직인다.
_FINANCIAL = SectorElasticity(0.6, 0.1, 10, 25, "medium")


def _snapshot(**overrides) -> dict:
    """채널 node 가 읽는 최소 snapshot."""

    snap = {
        "horizon": 3,
        "baseRevenue": 300.0,
        "baseMargin": 12.0,
        "baseWacc": 9.0,
        "elasticity": _FINANCIAL,
        "asOf": "2024Q4",
        "latestAsOf": "2025Q1",
    }
    snap.update(overrides)
    return snap


def _node(driverId: str, deps: tuple[str, ...] = ()) -> DriverNode:
    return DriverNode(nodeIdFor(driverId, "adverse"), driverId, "adverse", "all", deps, "fn")


def _pathValue(path: list[float | None]) -> NodeValue:
    return NodeValue(path[-1], tuple(path), "preset:adverse", (), "hash", "2024Q4", "2025Q1")


def _deps(gdp, fx, rate) -> dict:
    return {
        nodeIdFor(DRIVER_MACRO, "adverse"): _pathValue(gdp),
        nodeIdFor(DRIVER_FX, "adverse"): _pathValue(fx),
        nodeIdFor(DRIVER_RATE, "adverse"): _pathValue(rate),
    }


def testNodeIdForFoldsThePeriodCoordinate() -> None:
    """결정론 코어는 기간 좌표를 벡터에 접으므로 period key 는 항상 all 이다."""

    assert nodeIdFor("rev.path", "baseline") == "rev.path@baseline#all"


def testDependencyValueFailsWithoutWiring() -> None:
    """배선에 없는 상류 값은 기본값으로 메우지 않고 실패한다."""

    node = _node("rev.path")
    with pytest.raises(ValueError, match="needs its macro.path dependency"):
        dependencyValue({}, DRIVER_MACRO, node)
    value = _pathValue([1.0, 2.0])
    assert dependencyValue({nodeIdFor(DRIVER_MACRO, "adverse"): value}, DRIVER_MACRO, node) is value


def testGapValueKeepsReasonAndSnapshotClock() -> None:
    """결손 값은 None 이고 사유와 snapshot 시점이 그대로 남는다."""

    assert gapValue("dcf", "fcfPath_absent", {"asOf": "2024Q4", "latestAsOf": "2025Q1"}) == (
        None,
        None,
        "dcf:gap(fcfPath_absent)",
        (),
        {"gap": "fcfPath_absent"},
        "2024Q4",
        "2025Q1",
    )


def testEffectiveBaseMarginUsesSnapshotThenDefault() -> None:
    """기준 마진이 없을 때만 기본값을 쓴다."""

    assert effectiveBaseMargin({"baseMargin": 12.5}) == 12.5
    assert effectiveBaseMargin({"baseMargin": None}) == DEFAULT_BASE_MARGIN


def testMacroRootsEmitPresetPathsTruncatedToHorizon() -> None:
    """세 root 는 같은 프리셋의 GDP, 금리, 환율 경로를 horizon 만큼 낸다."""

    sheet = DriverSheet(snapshot=_snapshot(horizon=2))
    preset = getPresetScenarios(PRESET_MARKET)["adverse"]
    for fn, driverId, expected, variable in (
        (macroPathNode, DRIVER_MACRO, preset.gdpGrowth, "gdp"),
        (macroRateNode, DRIVER_RATE, preset.interestRate, "rate"),
        (macroFxNode, DRIVER_FX, preset.krwUsd, "fx"),
    ):
        value, vector, provenance, refs, frozen, asOf, latestAsOf = fn(_node(driverId), sheet, {})
        assert vector == tuple(float(item) for item in expected[:2])
        assert value == vector[-1]
        assert provenance == "preset:adverse"
        assert refs == (f"synth.scenario:PRESET_SCENARIOS_{PRESET_MARKET}/{preset.name}#{variable}",)
        assert frozen == {"variable": variable, "path": list(vector)}
        assert (asOf, latestAsOf) == ("2024Q4", "2025Q1")


def testChannelNodesProjectTheTransferChannels() -> None:
    """세 채널 node 의 경로는 transfer 채널 함수를 그대로 투영한다."""

    sheet = DriverSheet(snapshot=_snapshot())
    gdp, fx, rate = [-1.0, 0.5, 2.0], [1450.0, 1500.0, 1380.0], [3.5, 4.0, 2.75]
    deps = _deps(gdp, fx, rate)

    revenue = revenuePathNode(_node("rev.path"), sheet, deps)
    margin = marginPathNode(_node("margin.path"), sheet, deps)
    wacc = waccPathNode(_node("wacc.path"), sheet, deps)

    assert list(revenue[1]) == transferRevenueChannel(300.0, gdp, fx, _FINANCIAL)
    assert list(margin[1]) == transferMarginChannel(12.0, gdp, rate, _FINANCIAL)
    assert list(wacc[1]) == transferWaccChannel(9.0, rate)
    assert revenue[0] == revenue[1][-1]
    assert margin[3] == ("simulate.transfer:transferMarginChannel",)
    assert wacc[4] == {"baseWacc": 9.0, "wacc": list(wacc[1])}


def testChannelNodesAbstainWithoutParameterVintageOrBaseRevenue() -> None:
    """과거 시점 파라미터 vintage 가 없거나 기준 매출이 없으면 경로 대신 결손을 낸다."""

    deps = _deps([1.0, 1.0, 1.0], [1400.0, 1400.0, 1400.0], [3.0, 3.0, 3.0])
    historical = DriverSheet(snapshot=_snapshot(parameterVintageStatus="historicalAbsent"))
    for fn, driverId in ((revenuePathNode, "rev.path"), (marginPathNode, "margin.path"), (waccPathNode, "wacc.path")):
        result = fn(_node(driverId), historical, deps)
        assert result[:3] == (None, None, "transfer:gap(historical_parameter_vintage_absent)")

    noRevenue = DriverSheet(snapshot=_snapshot(baseRevenue=None))
    assert revenuePathNode(_node("rev.path"), noRevenue, deps)[2] == "transfer:gap(baseRevenue_absent)"
    assert marginPathNode(_node("margin.path"), noRevenue, deps)[2] == "transfer:gap(baseRevenue_absent)"
    assert waccPathNode(_node("wacc.path"), noRevenue, deps)[1] is not None


def testChannelNodesRejectIncompleteMacroPaths() -> None:
    """프리셋 경로에 결손이 있으면 0 으로 메우지 않고 실패한다."""

    sheet = DriverSheet(snapshot=_snapshot())
    deps = _deps([1.0, None, 1.0], [1400.0, 1400.0, 1400.0], [3.0, None, 3.0])

    with pytest.raises(ValueError, match="incomplete macro.path path"):
        revenuePathNode(_node("rev.path"), sheet, deps)
    with pytest.raises(ValueError, match="incomplete macro.rate path"):
        waccPathNode(_node("wacc.path"), sheet, deps)
