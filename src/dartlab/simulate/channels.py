"""Macro root and transfer-channel nodes of the deterministic scenario sheet.

`registry.buildScenarioSheet` wires three macro roots and three transfer channels in front of the
L2 leaf nodes (`proforma`, `dcf`). This module owns those six nodes and the small dependency and
honest-gap helpers every sheet node shares:

    macro.path (preset GDP)    macro.rate (preset policy rate)    macro.fx (preset KRW/USD)
      rev.path    <- macro.path, macro.fx     revenue channel
      margin.path <- macro.path, macro.rate   operating-margin channel
      wacc.path   <- macro.rate               discount-rate channel

Every node fn matches the `evaluateSheet` contract
``fn(node, sheet, depValues) -> (value, vector, provenance, refs, frozenInputs, asOf, latestAsOf)``.
The channel math is owned by `simulate.transfer`. Nodes read only the frozen snapshot and their
upstream paths; a missing or incomplete dependency raises instead of falling back to a baseline.

Layer: L3. Forward imports: L1.5 (`synth.scenario`), `simulate.sheet`, `simulate.transfer`.
"""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.simulate.sheet import DriverNode, DriverSheet, NodeValue
from dartlab.synth.scenario import SectorElasticity, getPresetScenarios

# Driver ids of the macro roots and transfer channels (§5 node table).
DRIVER_MACRO = "macro.path"
DRIVER_RATE = "macro.rate"
DRIVER_FX = "macro.fx"
DRIVER_REV = "rev.path"
DRIVER_MARGIN = "margin.path"
DRIVER_WACC = "wacc.path"

# The public verb is KR-only (entry.py blocks other markets). The presets and elasticities are KR
# baselines; a US run needs US presets and elasticities first, so this is the one place it is fixed.
PRESET_MARKET = "KR"

DEFAULT_BASE_MARGIN = 10.0  # legacy fallback when operating margin is unavailable.

SCENARIO_VARIABLES = ("gdp", "rate", "fx")


@dataclass(frozen=True)
class ScenarioPaths:
    """한 실행이 쓰는 거시 경로 세 개와 그 출처.

    프리셋 실행이면 ``userVariables`` 가 비어 있고 경로는 프리셋 그대로다. 사용자 시나리오면
    ``userVariables`` 에 사용자가 바꾼 변수가 들어 있고 나머지 경로는 ``base`` 프리셋에서 온다.
    검증과 해소는 ``simulate.assumptions.resolveScenarioPaths`` 가 맡는다.
    """

    name: str
    base: str
    gdp: tuple[float, ...]
    rate: tuple[float, ...]
    fx: tuple[float, ...]
    userVariables: tuple[str, ...] = ()

    @property
    def isUser(self) -> bool:
        """사용자가 바꾼 경로가 하나라도 있는지 알려 준다.

        Returns:
            ``userVariables`` 가 비어 있지 않으면 True.

        Raises:
            없음.

        Example:
            ``ScenarioPaths("baseline", "baseline", (1.0,), (2.5,), (1470.0,)).isUser`` 는 False 다.
        """
        return bool(self.userVariables)

    @property
    def maxHorizon(self) -> int:
        """세 경로가 모두 값을 가진 최대 연수를 돌려준다.

        Returns:
            ``gdp``, ``rate``, ``fx`` 경로 길이 중 가장 짧은 값.

        Raises:
            없음.

        Example:
            ``ScenarioPaths("s", "baseline", (1.0,) * 5, (2.0,) * 5, (3.0,) * 3).maxHorizon`` 는 3 이다.
        """
        return min(len(self.gdp), len(self.rate), len(self.fx))

    def path(self, variable: str) -> tuple[float, ...]:
        """변수 하나의 경로를 돌려준다.

        Args:
            variable: ``gdp``, ``rate``, ``fx`` 중 하나.

        Returns:
            그 변수의 연도별 경로.

        Raises:
            ValueError: 모르는 변수일 때.

        Example:
            ``paths.path("rate")`` 는 기준금리 경로다.
        """
        if variable not in SCENARIO_VARIABLES:
            raise ValueError(f"알 수 없는 거시 변수: {variable!r}")
        return getattr(self, variable)


def nodeIdFor(driverId: str, scenarioId: str) -> str:
    """Return the §6.1 node id of one driver in one scenario.

    Args:
        driverId: a driver id such as ``DRIVER_REV``.
        scenarioId: the scenario id such as ``"baseline"``.

    Returns:
        str: ``"{driverId}@{scenarioId}#all"``. The deterministic core folds the period coordinate
        into the node vector, so the period key is always ``all``.

    Raises:
        None.

    Example:
        >>> nodeIdFor("rev.path", "baseline")
        'rev.path@baseline#all'
    """
    return f"{driverId}@{scenarioId}#all"


def dependencyValue(depValues: dict, driverId: str, node: DriverNode) -> NodeValue:
    """Return the upstream node value of one driver in the same scenario.

    Args:
        depValues: the evaluated dependency values keyed by node id.
        driverId: the upstream driver id.
        node: the node being evaluated (its scenario selects the upstream node).

    Returns:
        NodeValue: the upstream value.

    Raises:
        ValueError: if the wiring does not provide that dependency. There is no default value.

    Example:
        >>> # used inside sheet node fns; not called directly.
    """
    key = nodeIdFor(driverId, node.scenarioId)
    if key not in depValues:
        raise ValueError(f"{node.nodeId} needs its {driverId} dependency")
    return depValues[key]


def _dependencyPath(depValues: dict, driverId: str, node: DriverNode) -> list[float]:
    """상류 거시 경로 벡터를 꺼낸다. 프리셋 경로에 결손이 있으면 0 으로 메우지 않고 실패한다."""
    vector = dependencyValue(depValues, driverId, node).vector
    if vector is None or any(value is None for value in vector):
        raise ValueError(f"{node.nodeId} got an incomplete {driverId} path")
    return [float(value) for value in vector]


def gapValue(prefix: str, reason: str, snap: dict) -> tuple:
    """Return an honest-gap node value: None value and vector, the reason kept in provenance.

    Args:
        prefix: the node family label used in provenance, such as ``"transfer"``.
        reason: the machine-readable gap reason.
        snap: the frozen sheet snapshot (supplies ``asOf`` and ``latestAsOf``).

    Returns:
        tuple: the 7-tuple node result with ``value`` and ``vector`` set to None.

    Raises:
        KeyError: if the snapshot lacks ``asOf`` or ``latestAsOf``.

    Example:
        >>> gapValue("dcf", "fcfPath_absent", {"asOf": None, "latestAsOf": None})[2]
        'dcf:gap(fcfPath_absent)'
    """
    return None, None, f"{prefix}:gap({reason})", (), {"gap": reason}, snap["asOf"], snap["latestAsOf"]


def effectiveBaseMargin(snap: dict) -> float:
    """Return the base operating margin the transfer channels and proforma shock share.

    Args:
        snap: the frozen sheet snapshot.

    Returns:
        float: the snapshot base margin, or ``DEFAULT_BASE_MARGIN`` when it is absent. The
        snapshot builder records that default as an assumption.

    Raises:
        KeyError: if the snapshot lacks ``baseMargin``.

    Example:
        >>> effectiveBaseMargin({"baseMargin": None})
        10.0
    """
    return float(snap["baseMargin"]) if snap["baseMargin"] is not None else DEFAULT_BASE_MARGIN


def _channelGap(snap: dict) -> str | None:
    """매출·마진 채널을 계산할 수 없는 사유. 과거 시점은 파라미터 vintage 가 없어 기권한다."""
    if snap.get("parameterVintageStatus", "available") != "available":
        return "historical_parameter_vintage_absent"
    if snap["baseRevenue"] is None:
        return "baseRevenue_absent"
    return None


def _presetNode(node: DriverNode, sheet: DriverSheet, variable: str) -> tuple:
    """거시 변수 하나의 경로를 root node 로 낸다. 모르는 프리셋은 KeyError 로 실패한다.

    snapshot 에 사용자 시나리오(``userScenario``)가 있으면 사용자가 바꾼 변수는 그 경로를 쓰고
    ``source="user"`` 를 frozen input 에 남긴다. 바꾸지 않은 변수는 사용자 시나리오의 base 프리셋
    경로를 그대로 쓰므로 같은 프리셋 node 와 inputsHash 가 같다.
    """
    snap = sheet.snapshot
    horizon = snap["horizon"]
    userScenario = snap.get("userScenario")
    if userScenario is not None and variable in userScenario.userVariables:
        path = [float(value) for value in userScenario.path(variable)[:horizon]]
        frozen = {"variable": variable, "path": path, "source": "user"}
        refs: tuple[str, ...] = (f"user:scenario/{userScenario.name}#{variable}",)
    else:
        presetName = node.scenarioId if userScenario is None else userScenario.base
        scenario = getPresetScenarios(PRESET_MARKET)[presetName]
        source = {"gdp": scenario.gdpGrowth, "rate": scenario.interestRate, "fx": scenario.krwUsd}[variable]
        path = [float(value) for value in source[:horizon]]
        frozen = {"variable": variable, "path": path}
        refs = (f"synth.scenario:PRESET_SCENARIOS_{PRESET_MARKET}/{scenario.name}#{variable}",)
    provenance = f"preset:{node.scenarioId}" if userScenario is None else f"user:{node.scenarioId}"
    value = path[-1] if path else None
    return value, tuple(path), provenance, refs, frozen, snap["asOf"], snap["latestAsOf"]


def macroPathNode(node: DriverNode, sheet: DriverSheet, depValues: dict) -> tuple:
    """`macro.path` node: the preset GDP path for the node's scenario (§5).

    Capabilities:
        Emits the preset GDP path for the scenario named by ``node.scenarioId`` from
        `synth.scenario.getPresetScenarios` (KR), truncated to the snapshot horizon. The
        representative value is terminal-year GDP and the vector is the GDP path. The rate and
        FX paths are their own root nodes (`macro.rate`, `macro.fx`), so every downstream channel
        reads its macro inputs through dependencies rather than re-reading the preset.

    Args:
        node: the macro.path DriverNode (its `scenarioId` selects the preset).
        sheet: the DriverSheet (its `snapshot["horizon"]` truncates the path).
        depValues: empty (macro.path is a root node).

    Returns:
        tuple: ``(gdpTerminal, gdpVector, provenance, refs, frozenInputs, asOf, latestAsOf)``
        with ``provenance = "preset:{scenarioId}"`` and ``frozenInputs = {"variable", "path"}``.

    Raises:
        KeyError: if validation was bypassed and the scenario id is unknown.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.

    Requires:
        ``synth.scenario.getPresetScenarios`` and the snapshot's ``horizon`` / ``asOf``.
    """
    return _presetNode(node, sheet, "gdp")


def macroRateNode(node: DriverNode, sheet: DriverSheet, depValues: dict) -> tuple:
    """`macro.rate` node: the preset policy-rate path for the node's scenario (root node).

    Args:
        node: the macro.rate DriverNode (its `scenarioId` selects the preset).
        sheet: the DriverSheet (its `snapshot["horizon"]` truncates the path).
        depValues: empty (macro.rate is a root node).

    Returns:
        tuple: the 7-tuple node result whose vector is the policy-rate path.

    Raises:
        KeyError: if validation was bypassed and the scenario id is unknown.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.
    """
    return _presetNode(node, sheet, "rate")


def macroFxNode(node: DriverNode, sheet: DriverSheet, depValues: dict) -> tuple:
    """`macro.fx` node: the preset KRW/USD path for the node's scenario (root node).

    Args:
        node: the macro.fx DriverNode (its `scenarioId` selects the preset).
        sheet: the DriverSheet (its `snapshot["horizon"]` truncates the path).
        depValues: empty (macro.fx is a root node).

    Returns:
        tuple: the 7-tuple node result whose vector is the KRW/USD path.

    Raises:
        KeyError: if validation was bypassed and the scenario id is unknown.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.
    """
    return _presetNode(node, sheet, "fx")


def revenuePathNode(node: DriverNode, sheet: DriverSheet, depValues: dict) -> tuple:
    """`rev.path` node: the revenue channel of the owned macro->fundamentals edge (§2/§5).

    Capabilities:
        Chains `simulate.transfer.transferRevenueChannel` over the GDP and FX dependency paths onto
        base revenue + sector elasticity, producing the scenario's absolute revenue vector. The
        margin and WACC channels are separate nodes. honest-gap: if base revenue is absent the
        node value is None (never 0).

    Args:
        node: the rev.path DriverNode (depends on the scenario's macro.path and macro.fx).
        sheet: the DriverSheet whose snapshot holds base revenue and elasticity.
        depValues: the GDP and FX NodeValues of the same scenario.

    Returns:
        tuple: ``(revTerminal, revVector, provenance, refs, frozenInputs, asOf, latestAsOf)`` with
        ``provenance`` describing the transfer; value/vector are None when base revenue is absent.

    Raises:
        ValueError: if the GDP or FX dependency is missing or incomplete.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.

    Requires:
        The macro.path and macro.fx dependency vectors and the snapshot base metrics.
    """
    from dartlab.simulate.transfer import transferRevenueChannel

    snap = sheet.snapshot
    gap = _channelGap(snap)
    if gap is not None:
        # honest-gap: no base revenue or no parameter vintage -> no scenario path.
        return gapValue("transfer", gap, snap)

    elasticity: SectorElasticity = snap["elasticity"]
    gdp = _dependencyPath(depValues, DRIVER_MACRO, node)
    fx = _dependencyPath(depValues, DRIVER_FX, node)
    revPath = transferRevenueChannel(snap["baseRevenue"], gdp, fx, elasticity)
    frozen = {"baseRevenue": snap["baseRevenue"], "rev": revPath}
    prov = "transfer:rev*(1+bgdp*gdp+bfx*fxDelta)"
    refs = ("simulate.transfer:transferRevenueChannel",)
    value = revPath[-1] if revPath else None
    return value, tuple(revPath), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


def marginPathNode(node: DriverNode, sheet: DriverSheet, depValues: dict) -> tuple:
    """`margin.path` node: the operating-margin channel of the transfer (GDP, rate for financials).

    Capabilities:
        Carries the base operating margin over the horizon with the sector's GDP margin shock and
        the rate NIM shock (non-zero only for financials), floored at -50 each year. The proforma
        node applies this path as a margin shock on top of its own projection, so the channel
        moves operating profit and FCF instead of being display-only.

    Args:
        node: the margin.path DriverNode (depends on macro.path and macro.rate).
        sheet: the DriverSheet whose snapshot holds base margin and elasticity.
        depValues: the GDP and policy-rate NodeValues of the same scenario.

    Returns:
        tuple: ``(terminalMargin, marginVector, provenance, refs, frozenInputs, asOf, latestAsOf)``;
        value and vector are None on an honest gap.

    Raises:
        ValueError: if the GDP or rate dependency is missing or incomplete.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.
    """
    from dartlab.simulate.transfer import transferMarginChannel

    snap = sheet.snapshot
    gap = _channelGap(snap)
    if gap is not None:
        return gapValue("transfer", gap, snap)
    baseMargin = effectiveBaseMargin(snap)
    gdp = _dependencyPath(depValues, DRIVER_MACRO, node)
    rate = _dependencyPath(depValues, DRIVER_RATE, node)
    marginPath = transferMarginChannel(baseMargin, gdp, rate, snap["elasticity"])
    frozen = {"baseMargin": baseMargin, "margin": marginPath}
    prov = "transfer:margin+bm*gdp+nim*rateDelta"
    refs = ("simulate.transfer:transferMarginChannel",)
    value = marginPath[-1] if marginPath else None
    return value, tuple(marginPath), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


def waccPathNode(node: DriverNode, sheet: DriverSheet, depValues: dict) -> tuple:
    """`wacc.path` node: the discount-rate channel of the transfer (half the rate change).

    Capabilities:
        Maps the scenario's policy-rate path onto a per-year WACC path around the snapshot base
        WACC. The dcf node discounts each year at this path, so a rate shock changes the value.

    Args:
        node: the wacc.path DriverNode (depends on macro.rate).
        sheet: the DriverSheet whose snapshot holds the base WACC.
        depValues: the policy-rate NodeValue of the same scenario.

    Returns:
        tuple: ``(terminalWacc, waccVector, provenance, refs, frozenInputs, asOf, latestAsOf)``;
        value and vector are None when the parameter vintage is unavailable.

    Raises:
        ValueError: if the rate dependency is missing or incomplete.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.
    """
    from dartlab.simulate.transfer import transferWaccChannel

    snap = sheet.snapshot
    if snap.get("parameterVintageStatus", "available") != "available":
        return gapValue("transfer", "historical_parameter_vintage_absent", snap)
    rate = _dependencyPath(depValues, DRIVER_RATE, node)
    waccPath = transferWaccChannel(float(snap["baseWacc"]), rate)
    frozen = {"baseWacc": float(snap["baseWacc"]), "wacc": waccPath}
    prov = "transfer:wacc+0.5*rateDelta"
    refs = ("simulate.transfer:transferWaccChannel",)
    value = waccPath[-1] if waccPath else None
    return value, tuple(waccPath), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]
