"""Bind price, volume, unit cost, fixed cost, and capacity into world evolution.

The module stays inside the L2.5 ``simulate`` package and exposes no new public
dartlab verb. It exists so scenario paths and strategies can move operating
variables through a real state transition before any UI or narrative layer
claims a simulation result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from dartlab.simulate.world import (
    ActionSpec,
    ConstraintSpec,
    LawSpec,
    ObjectiveSpec,
    ScenarioPath,
    SimulationBlocked,
    SimulationRun,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    simulateWorld,
)

_ACCEPTED_EVIDENCE = {"observed", "deterministicDerived", "admittedEstimate", "explicitAssumption"}
_REQUIRED_INPUTS = {
    "price": ("currencyPerUnit", "price"),
    "demandVolume": ("units", "demandVolume"),
    "unitCost": ("currencyPerUnit", "unitCost"),
    "fixedCost": ("currency", "fixedCost"),
    "capacityUnits": ("units", "capacityUnits"),
    "cash": ("currency", "cash"),
    "debt": ("currency", "debt"),
}
_STATE_IDS = ("price", "demandVolume", "unitCost", "fixedCost", "capacityUnits", "cash", "debt")
_METRIC_IDS = (
    "soldVolume",
    "unmetVolume",
    "availableCapacityUnits",
    "revenue",
    "variableCost",
    "operatingProfit",
    "interest",
    "tax",
    "netIncome",
    "cashChange",
    "netCash",
    "cashRunwaySteps",
    "capacityUtilization",
    "capacityBound",
)


@dataclass(frozen=True)
class OperatingPrimitive:
    """One operating input value with its provenance boundary.

    Args:
        variableId: Canonical operating variable name.
        value: Numeric value used by the world initial state.
        unit: Unit contract expected by the transition law.
        evidenceRole: Observed, derived, admitted, or explicit assumption.
        sourceRef: Receipt, dataset, filing, or assumption reference.

    Returns:
        Dataclass used by ``operatingInputsFromPrimitives``.

    Raises:
        Errors are raised by the compiler, not by this plain container.

    Example:
        ``OperatingPrimitive("price", 10.0, "currencyPerUnit", "explicitAssumption", "assumption://price")``
    """

    variableId: str
    value: float
    unit: str
    evidenceRole: str
    sourceRef: str


@dataclass(frozen=True)
class OperatingWorldInputs:
    """Initial operating state and assumption parameters for a company world."""

    state: Mapping[str, float]
    asOf: str
    refs: tuple[str, ...]
    warnings: tuple[str, ...]
    priceElasticity: float
    capacityUnitsPerCurrency: float
    capacityDecayRate: float
    taxRate: float
    stepFrequency: str = "quarter"
    stepSpan: int = 1


def _finite(value: float, label: str) -> float:
    number = float(value)
    if number != number or number in {float("inf"), float("-inf")}:
        raise ValueError(f"{label} must be finite")
    return number


def _requireRefs(refs: tuple[str, ...], label: str) -> None:
    if not refs or any(not str(ref) for ref in refs):
        raise ValueError(f"{label} needs at least one source or assumption ref")


def operatingInputsFromPrimitives(
    primitives: Sequence[OperatingPrimitive],
    *,
    asOf: str,
    priceElasticity: float,
    capacityUnitsPerCurrency: float,
    capacityDecayRate: float = 0.0,
    taxRate: float = 0.0,
    warnings: tuple[str, ...] = (),
) -> OperatingWorldInputs:
    """Compile sourced operating variables into an executable initial state.

    Args:
        primitives: Required operating inputs, each carrying a source boundary.
        asOf: Decision or snapshot label for the initial state.
        priceElasticity: Demand response to strategy price changes.
        capacityUnitsPerCurrency: Capacity added per investment currency unit.
        capacityDecayRate: Per-step capacity decay ratio.
        taxRate: Simple tax rate applied when profit before tax is positive.
        warnings: Extra warnings inherited from upstream compilers.

    Returns:
        ``OperatingWorldInputs`` with values, refs, and assumption warnings.

    Raises:
        ValueError: If any input is missing, unit-drifted, unsigned, or out of range.

    Example:
        ``inputs = operatingInputsFromPrimitives(rows, asOf="2025Q4", priceElasticity=1.2, capacityUnitsPerCurrency=0.01)``
    """

    byId = {item.variableId: item for item in primitives}
    if len(byId) != len(tuple(primitives)):
        raise ValueError("operating primitives need unique variableId values")
    missing = sorted(set(_REQUIRED_INPUTS) - set(byId))
    if missing:
        raise ValueError(f"operating inputs are missing: {missing}")
    state: dict[str, float] = {}
    refs: list[str] = []
    outWarnings = list(warnings)
    for variableId, (unit, stateName) in _REQUIRED_INPUTS.items():
        item = byId[variableId]
        if item.unit != unit:
            raise ValueError(f"operating unit drift: {variableId}")
        if item.evidenceRole not in _ACCEPTED_EVIDENCE:
            raise ValueError(f"operating evidence role is not executable: {variableId}")
        if not item.sourceRef:
            raise ValueError(f"operating source ref is missing: {variableId}")
        value = _finite(item.value, variableId)
        if value < 0:
            raise ValueError(f"operating input must be nonnegative: {variableId}")
        state[stateName] = value
        refs.append(item.sourceRef)
        if item.evidenceRole == "explicitAssumption":
            outWarnings.append(f"operatingAssumption:{variableId}")
    elasticity = _finite(priceElasticity, "priceElasticity")
    capacityPerCurrency = _finite(capacityUnitsPerCurrency, "capacityUnitsPerCurrency")
    decay = _finite(capacityDecayRate, "capacityDecayRate")
    tax = _finite(taxRate, "taxRate")
    if elasticity < 0 or capacityPerCurrency < 0 or decay < 0 or decay > 1 or tax < 0 or tax > 1:
        raise ValueError("operating assumption parameters are outside their physical bounds")
    if not asOf:
        raise ValueError("operating world needs asOf")
    return OperatingWorldInputs(
        state=state,
        asOf=asOf,
        refs=tuple(refs),
        warnings=tuple(outWarnings),
        priceElasticity=elasticity,
        capacityUnitsPerCurrency=capacityPerCurrency,
        capacityDecayRate=decay,
        taxRate=tax,
    )


def _buildOperatingWorld(inputs: OperatingWorldInputs, *, maxFinancing: float, maxInvestment: float) -> WorldModel:
    if maxFinancing < 0 or maxInvestment < 0:
        raise ValueError("operating financing and investment limits must be nonnegative")
    metricUnits = {
        "capacityBound": "boolean",
        "capacityUtilization": "ratio",
        "cashRunwaySteps": "steps",
        "soldVolume": "units",
        "unmetVolume": "units",
        "availableCapacityUnits": "units",
    }
    variables = tuple(
        [
            VariableSpec(name, _REQUIRED_INPUTS[name][0], "state", lower=None if name == "cash" else 0.0)
            for name in _STATE_IDS
        ]
        + [
            VariableSpec("marketPriceChange", "ratioChangePerStep", "shock", lower=-1.0),
            VariableSpec("demandChange", "ratioChangePerStep", "shock", lower=-1.0),
            VariableSpec("unitCostChange", "ratioChangePerStep", "shock", lower=-1.0),
            VariableSpec("fixedCostChange", "ratioChangePerStep", "shock", lower=-1.0),
            VariableSpec("capacityChange", "ratioChangePerStep", "shock", lower=-1.0),
            VariableSpec("debtRate", "effectiveRatePerStep", "shock", lower=0.0, upper=1.0),
        ]
        + [VariableSpec(name, metricUnits.get(name, "currency"), "metric") for name in _METRIC_IDS]
    )
    actions = (
        ActionSpec("priceChange", "ratioChangePerStep", -0.9, 10.0, 0, 0.0, "explicitAssumption", "operating:price"),
        ActionSpec(
            "capacityInvestment",
            "currency",
            0.0,
            maxInvestment,
            1,
            1.0,
            "explicitAssumption",
            "operating:capacity",
        ),
        ActionSpec("borrow", "currency", 0.0, maxFinancing, 0, 0.0, "accountingIdentity", "operating:debt"),
        ActionSpec("repay", "currency", 0.0, maxFinancing, 0, 0.0, "accountingIdentity", "operating:debt"),
    )

    def operatingStep(ctx):
        """Move one period of operating variables through PnL, cash, debt, and capacity.

        Args:
            ctx: ``StepContext`` exposing declared prior state, shocks, and actions.

        Returns:
            Full next state and operating metrics for the current step.

        Raises:
            SimulationBlocked: If repayment exceeds debt available after borrowing.

        Example:
            ``outputs = operatingStep(ctx)``
        """

        priceMove = ctx.shocks["marketPriceChange"] + ctx.actions["priceChange"]
        price = max(0.0, ctx.prior["price"] * (1.0 + priceMove))
        demandMultiplier = 1.0 + ctx.shocks["demandChange"] - inputs.priceElasticity * ctx.actions["priceChange"]
        demandVolume = max(0.0, ctx.prior["demandVolume"] * demandMultiplier)
        unitCost = max(0.0, ctx.prior["unitCost"] * (1.0 + ctx.shocks["unitCostChange"]))
        fixedCost = max(0.0, ctx.prior["fixedCost"] * (1.0 + ctx.shocks["fixedCostChange"]))
        availableCapacityUnits = max(
            0.0,
            ctx.prior["capacityUnits"] * (1.0 - inputs.capacityDecayRate) * (1.0 + ctx.shocks["capacityChange"])
            + ctx.actions["capacityInvestment"] * inputs.capacityUnitsPerCurrency,
        )
        soldVolume = min(demandVolume, availableCapacityUnits)
        unmetVolume = max(0.0, demandVolume - soldVolume)
        revenue = price * soldVolume
        variableCost = unitCost * soldVolume
        operatingProfit = revenue - variableCost - fixedCost
        interest = ctx.prior["debt"] * ctx.shocks["debtRate"]
        pretax = operatingProfit - interest
        tax = max(0.0, pretax * inputs.taxRate)
        netIncome = pretax - tax
        debt = ctx.prior["debt"] + ctx.actions["borrow"] - ctx.actions["repay"]
        if debt < -1e-9:
            raise SimulationBlocked("operating repayment exceeds available debt")
        debt = max(0.0, debt)
        cashChange = netIncome - ctx.actionCost + ctx.actions["borrow"] - ctx.actions["repay"]
        cash = ctx.prior["cash"] + cashChange
        capacityUnits = availableCapacityUnits
        burn = max(0.0, -cashChange)
        cashRunwaySteps = cash / burn if burn > 1e-9 and cash > 0 else (0.0 if cash <= 0 else 1_000_000_000.0)
        capacityUtilization = soldVolume / availableCapacityUnits if availableCapacityUnits > 1e-9 else 0.0
        capacityBound = float(demandVolume > availableCapacityUnits + 1e-9)
        return {
            "price": price,
            "demandVolume": demandVolume,
            "unitCost": unitCost,
            "fixedCost": fixedCost,
            "capacityUnits": capacityUnits,
            "cash": cash,
            "debt": debt,
            "soldVolume": soldVolume,
            "unmetVolume": unmetVolume,
            "availableCapacityUnits": availableCapacityUnits,
            "revenue": revenue,
            "variableCost": variableCost,
            "operatingProfit": operatingProfit,
            "interest": interest,
            "tax": tax,
            "netIncome": netIncome,
            "cashChange": cashChange,
            "netCash": cash - debt,
            "cashRunwaySteps": cashRunwaySteps,
            "capacityUtilization": capacityUtilization,
            "capacityBound": capacityBound,
        }

    law = LawSpec(
        "operatingStep",
        outputs=_STATE_IDS + _METRIC_IDS,
        priorInputs=_STATE_IDS,
        shockInputs=(
            "marketPriceChange",
            "demandChange",
            "unitCostChange",
            "fixedCostChange",
            "capacityChange",
            "debtRate",
        ),
        actionInputs=("priceChange", "capacityInvestment", "borrow", "repay"),
        usesActionCost=True,
        evidenceKind="explicitAssumption",
        provenance="simulate.operatingWorld:operatingStep",
        version="1",
        parameters={
            "priceElasticity": inputs.priceElasticity,
            "capacityUnitsPerCurrency": inputs.capacityUnitsPerCurrency,
            "capacityDecayRate": inputs.capacityDecayRate,
            "taxRate": inputs.taxRate,
        },
        fn=operatingStep,
    )
    return WorldModel(
        "company-operating-world",
        "1",
        variables,
        actions,
        (law,),
        stepFrequency=inputs.stepFrequency,
        stepSpan=inputs.stepSpan,
    )


def buildOperatingPath(
    pathId: str,
    *,
    marketPriceChange: Sequence[float],
    demandChange: Sequence[float],
    unitCostChange: Sequence[float],
    fixedCostChange: Sequence[float],
    capacityChange: Sequence[float],
    debtRate: Sequence[float],
    refs: tuple[str, ...],
    weight: float | None = None,
    weightKind: str = "unweighted",
    frequency: str = "quarter",
) -> ScenarioPath:
    """Build a sourced operating scenario path.

    Args:
        pathId: Path identifier.
        marketPriceChange: Per-step market or ASP price movement.
        demandChange: Per-step demand volume movement before policy price response.
        unitCostChange: Per-step unit-cost movement.
        fixedCostChange: Per-step fixed-cost movement.
        capacityChange: Per-step physical capacity movement before investment.
        debtRate: Per-step debt rate.
        refs: Source or assumption references for the whole path.
        weight: Optional path weight.
        weightKind: Weight interpretation used by the world executor.
        frequency: Time grid label, default quarter.

    Returns:
        ``ScenarioPath`` consumable by ``runOperatingStrategies``.

    Raises:
        ValueError: If lengths differ or refs are absent.

    Example:
        ``path = buildOperatingPath("stress", marketPriceChange=(0,), demandChange=(-0.1,), unitCostChange=(0.05,), fixedCostChange=(0,), capacityChange=(0,), debtRate=(0.04,), refs=("assumption://stress",))``
    """

    _requireRefs(refs, "operating path")
    lengths = {
        len(marketPriceChange),
        len(demandChange),
        len(unitCostChange),
        len(fixedCostChange),
        len(capacityChange),
        len(debtRate),
    }
    if len(lengths) != 1:
        raise ValueError("operating shock paths must share a horizon")
    steps = tuple(
        {
            "marketPriceChange": float(marketPriceChange[i]),
            "demandChange": float(demandChange[i]),
            "unitCostChange": float(unitCostChange[i]),
            "fixedCostChange": float(fixedCostChange[i]),
            "capacityChange": float(capacityChange[i]),
            "debtRate": float(debtRate[i]),
        }
        for i in range(len(marketPriceChange))
    )
    return ScenarioPath(pathId, steps, weight=weight, weightKind=weightKind, refs=refs, frequency=frequency)


def buildOperatingStrategy(
    strategyId: str,
    *,
    priceChange: Sequence[float],
    capacityInvestment: Sequence[float],
    borrow: Sequence[float],
    repay: Sequence[float],
    refs: tuple[str, ...],
    isBaseline: bool = False,
) -> StrategySpec:
    """Build a sourced operating policy path.

    Args:
        strategyId: Strategy identifier.
        priceChange: Per-step policy price movement.
        capacityInvestment: Per-step capacity investment cash outflow.
        borrow: Per-step borrowing.
        repay: Per-step debt repayment.
        refs: Source or assumption references for the policy.
        isBaseline: Whether this policy is the comparison baseline.

    Returns:
        ``StrategySpec`` with one action row per step.

    Raises:
        ValueError: If lengths differ or refs are absent.

    Example:
        ``strategy = buildOperatingStrategy("invest", priceChange=(0,), capacityInvestment=(50,), borrow=(0,), repay=(0,), refs=("assumption://invest",))``
    """

    _requireRefs(refs, "operating strategy")
    lengths = {len(priceChange), len(capacityInvestment), len(borrow), len(repay)}
    if len(lengths) != 1:
        raise ValueError("operating action paths must share a horizon")
    actions = tuple(
        {
            "priceChange": float(priceChange[i]),
            "capacityInvestment": float(capacityInvestment[i]),
            "borrow": float(borrow[i]),
            "repay": float(repay[i]),
        }
        for i in range(len(priceChange))
    )
    return StrategySpec(strategyId, actions, refs=refs, isBaseline=isBaseline)


def runOperatingStrategies(
    inputs: OperatingWorldInputs,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    traceLimit: int | None = None,
) -> SimulationRun:
    """Run operating paths and compare policy-specific PnL and solvency.

    Args:
        inputs: Sourced initial operating state and assumption parameters.
        paths: Common scenario paths.
        strategies: Candidate policy schedules.
        debtLimit: Hard debt limit used for solvency breaches.
        maxFinancing: Per-step borrowing and repayment bound.
        maxInvestment: Per-step capacity investment bound.
        traceLimit: Optional retained trace cap for large path sets.

    Returns:
        ``SimulationRun`` containing PnL, cash, capacity, and runway traces.

    Raises:
        ValueError: If strategy or financing limits are invalid.

    Example:
        ``run = runOperatingStrategies(inputs, (path,), (baseline, invest), debtLimit=1000, maxFinancing=500, maxInvestment=500)``
    """

    model = _buildOperatingWorld(inputs, maxFinancing=maxFinancing, maxInvestment=maxInvestment)
    initial = WorldState(inputs.state, asOf=inputs.asOf, refs=inputs.refs)
    constraints = (
        ConstraintSpec("cash", "ge", 0.0),
        ConstraintSpec("debt", "le", debtLimit),
        ConstraintSpec("capacityUnits", "ge", 0.0),
    )
    objectives = (
        ObjectiveSpec("operatingProfit", reducer="cumulative", direction="maximize", risk="average"),
        ObjectiveSpec("netCash", reducer="terminal", direction="maximize", risk="worst"),
        ObjectiveSpec("cashRunwaySteps", reducer="minimum", direction="maximize", risk="worst"),
    )
    return simulateWorld(
        model,
        initial,
        paths,
        strategies,
        constraints=constraints,
        objectives=objectives,
        inputWarnings=inputs.warnings,
        traceLimit=traceLimit,
    )
