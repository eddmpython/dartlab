"""Compile a frozen company snapshot into an auditable financial world.

This L2.5 adapter maps explicit company state, scenario paths, operating
assumptions, and financial actions onto ``simulate.world``. The one-period
accounting projection remains owned by ``analysis.financial.stepProjection``.
Historical ratios, unit economics, and capacity headroom remain surfaced
assumptions, so the default result is conditional and cannot emit an automatic
strategy recommendation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Mapping, Sequence

from dartlab.analysis.financial.proforma import extractHistoricalRatios
from dartlab.analysis.financial.stepProjection import (
    FinancialAction,
    FinancialParameters,
    FinancialShock,
    FinancialState,
    projectFinancialStep,
)
from dartlab.core.utils.extract import getLatest
from dartlab.simulate.world import (
    ActionSpec,
    ConstraintSpec,
    LawSpec,
    ObjectiveSpec,
    ScenarioPath,
    SimulationBlocked,
    SimulationRun,
    SimulationSpecError,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    simulateWorld,
)


@dataclass(frozen=True)
class OperatingDriverInputs:
    """제품 가격, 물량, 단위원가, 고정비의 기준 상태를 보존한다."""

    unitPrice: float
    demandUnits: float
    unitCost: float
    fixedCost: float
    capacityUnits: float
    refs: tuple[str, ...] = ()
    evidenceRole: str = "explicitAssumption"


@dataclass(frozen=True)
class FinancialWorldInputs:
    """동결된 회사 상태와 전이 파라미터, 운영 드라이버, 근거, 경고를 묶는다."""

    state: FinancialState
    parameters: FinancialParameters
    asOf: str
    refs: tuple[str, ...]
    warnings: tuple[str, ...]
    stepFrequency: str = "year"
    stepSpan: int = 1
    parameterFrequency: str = "year"
    operatingDrivers: OperatingDriverInputs | None = None


@dataclass(frozen=True)
class _OperatingProjection:
    unitPrice: float
    demandUnits: float
    unitCost: float
    fixedCost: float
    demandGrowth: float
    marginChange: float
    servedUnits: float
    unmetUnits: float
    capacityUnits: float
    capacityRevenue: float
    operatingRevenue: float
    operatingProfit: float


_STATE_IDS = (
    "revenue",
    "latentDemandRevenue",
    "operatingMargin",
    "cash",
    "debt",
    "receivables",
    "inventories",
    "payables",
    "ppe",
    "otherNetAssets",
    "equity",
)
_METRIC_IDS = (
    "demandRevenue",
    "capacityRevenue",
    "capacityUtilization",
    "unmetDemand",
    "operatingProfit",
    "depreciation",
    "capex",
    "interest",
    "tax",
    "netIncome",
    "dividends",
    "deltaNwc",
    "cfo",
    "cashChange",
    "cashBurn",
    "cashRunwaySteps",
    "identityResidual",
    "identityResidualRatio",
    "netCash",
    "capacityBound",
)
_OPERATING_STATE_IDS = ("unitPrice", "demandUnits", "unitCost", "fixedCost", "capacityUnits")
_OPERATING_SHOCK_IDS = (
    "priceChange",
    "volumeChange",
    "unitCostChange",
    "fixedCostChange",
    "capacityChange",
    "debtRate",
)
_OPERATING_METRIC_IDS = (
    "derivedDemandGrowth",
    "derivedMarginChange",
    "servedUnits",
    "unmetUnits",
    "effectiveCapacityUnits",
    "operatingDriverRevenue",
    "operatingDriverProfit",
    "unitGrossProfit",
)
_FINANCIAL_PARAMETER_UNITS = {
    "taxRate": "ratioPerStep",
    "depreciationRate": "ratioPerStep",
    "receivablesRatio": "ratio",
    "payablesRatio": "ratio",
    "revenuePerPpe": "currencyPerCurrency",
    "dividendPayout": "ratio",
}
_RUNWAY_CAP_STEPS = 1_000_000.0


def _required(value, label: str) -> float:
    if value is None:
        raise SimulationBlocked(f"financial snapshot missing: {label}")
    return float(value)


def _firstPresent(*values):
    """Return the first non-None account value while preserving a reported zero."""

    return next((value for value in values if value is not None), None)


def _validateOperatingDrivers(operatingDrivers: OperatingDriverInputs) -> None:
    values = {
        "unitPrice": operatingDrivers.unitPrice,
        "demandUnits": operatingDrivers.demandUnits,
        "unitCost": operatingDrivers.unitCost,
        "fixedCost": operatingDrivers.fixedCost,
        "capacityUnits": operatingDrivers.capacityUnits,
    }
    if values["unitPrice"] <= 0:
        raise ValueError("unitPrice must be positive")
    if any(float(value) < 0 for value in values.values() if value is not None):
        raise ValueError("operating driver values must be nonnegative")
    if not operatingDrivers.evidenceRole:
        raise ValueError("operating driver evidenceRole is required")


def _reconcileOperatingDrivers(
    operatingDrivers: OperatingDriverInputs,
    *,
    revenue: float,
    operatingMargin: float,
    capacityHeadroom: float,
    tolerance: float,
) -> tuple[float, float, float]:
    servedUnits = min(operatingDrivers.demandUnits, operatingDrivers.capacityUnits)
    realizedRevenue = servedUnits * operatingDrivers.unitPrice
    latentDemandRevenue = operatingDrivers.demandUnits * operatingDrivers.unitPrice
    capacityRevenue = operatingDrivers.capacityUnits * operatingDrivers.unitPrice
    operatingProfit = realizedRevenue - servedUnits * operatingDrivers.unitCost - operatingDrivers.fixedCost
    observedProfit = revenue * operatingMargin
    revenueTolerance = max(1.0, abs(revenue)) * tolerance
    if abs(realizedRevenue - revenue) > revenueTolerance:
        raise SimulationSpecError("operating drivers do not reconcile with observed revenue")
    if abs(operatingProfit - observedProfit) > revenueTolerance:
        raise SimulationSpecError("operating drivers do not reconcile with observed margin")
    if revenue > 0:
        impliedHeadroom = capacityRevenue / revenue - 1.0
        if abs(impliedHeadroom - capacityHeadroom) > max(tolerance, abs(capacityHeadroom) * tolerance):
            raise SimulationSpecError("operating capacity does not reconcile with capacityHeadroom")
    return latentDemandRevenue, capacityRevenue, operatingProfit


def _cashRunwaySteps(cash: float, cashBurn: float) -> float:
    if cash <= 0:
        return 0.0
    if cashBurn <= 0:
        return _RUNWAY_CAP_STEPS
    return min(_RUNWAY_CAP_STEPS, cash / cashBurn)


def _deriveOperatingProjection(ctx, state: FinancialState, params: FinancialParameters) -> _OperatingProjection:
    unitPrice = ctx.prior["unitPrice"] * (1.0 + ctx.shocks["priceChange"])
    demandUnits = ctx.prior["demandUnits"] * (1.0 + ctx.shocks["volumeChange"])
    unitCost = ctx.prior["unitCost"] * (1.0 + ctx.shocks["unitCostChange"])
    fixedCost = ctx.prior["fixedCost"] * (1.0 + ctx.shocks["fixedCostChange"])
    capacityUnits = ctx.prior["capacityUnits"] * (1.0 + ctx.shocks["capacityChange"])
    if unitPrice <= 0 or demandUnits < 0 or unitCost < 0 or fixedCost < 0 or capacityUnits < 0:
        raise SimulationBlocked("operating driver step produced an impossible unit state")
    demandRevenue = unitPrice * demandUnits
    if state.latentDemandRevenue <= 0:
        if demandRevenue > 0:
            raise SimulationBlocked("operating demand growth needs positive prior latent demand")
        demandGrowth = -1.0
    else:
        demandGrowth = demandRevenue / state.latentDemandRevenue - 1.0
    capacityRevenue = capacityUnits * unitPrice
    servedUnits = min(demandUnits, capacityUnits)
    operatingRevenue = servedUnits * unitPrice
    unmetUnits = max(0.0, demandUnits - servedUnits)
    operatingProfit = operatingRevenue - servedUnits * unitCost - fixedCost
    if operatingRevenue <= 0:
        if fixedCost > 0:
            raise SimulationBlocked(
                "fixed operating cost with zero realized revenue needs a direct operating-profit leaf"
            )
        targetMargin = state.operatingMargin
    else:
        targetMargin = operatingProfit / operatingRevenue
    if targetMargin < -1.0 or targetMargin > 1.0:
        raise SimulationBlocked("operating driver margin is outside the current financial leaf range")
    return _OperatingProjection(
        unitPrice=unitPrice,
        demandUnits=demandUnits,
        unitCost=unitCost,
        fixedCost=fixedCost,
        demandGrowth=demandGrowth,
        marginChange=targetMargin - state.operatingMargin,
        servedUnits=servedUnits,
        unmetUnits=unmetUnits,
        capacityUnits=capacityUnits,
        capacityRevenue=capacityRevenue,
        operatingRevenue=operatingRevenue,
        operatingProfit=operatingProfit,
    )


def financialInputsFromSnapshot(
    snapshot: Mapping,
    *,
    capacityHeadroom: float,
    operatingDrivers: OperatingDriverInputs | None = None,
    operatingDriverTolerance: float = 1e-6,
) -> FinancialWorldInputs:
    """Compile an honest reduced financial state from a frozen simulate snapshot.

    Args:
        snapshot: Frozen company snapshot with series, base revenue, margin, and as-of fields.
        capacityHeadroom: Explicit capacity slack over observed revenue.
        operatingDrivers: Optional sourced unit price, demand, cost, fixed cost, and capacity state.
        operatingDriverTolerance: Reconciliation tolerance for operating drivers versus observed values.

    Returns:
        ``FinancialWorldInputs`` carrying state, parameters, refs, warnings, and optional drivers.

    Raises:
        ValueError: If explicit assumptions are outside physical bounds.
        SimulationBlocked: If required point-in-time financial accounts are missing.
        SimulationSpecError: If operating drivers fail revenue, margin, or capacity reconciliation.

    Example:
        ``inputs = financialInputsFromSnapshot(snapshot, capacityHeadroom=0.1)``
    """

    if capacityHeadroom < 0:
        raise ValueError("capacityHeadroom must be nonnegative")
    if operatingDriverTolerance < 0:
        raise ValueError("operatingDriverTolerance must be nonnegative")
    if operatingDrivers is not None:
        _validateOperatingDrivers(operatingDrivers)
    series = snapshot.get("series")
    if not series:
        raise SimulationBlocked("financial snapshot missing: series")
    revenue = _required(snapshot.get("baseRevenue"), "baseRevenue")
    operatingMargin = _required(snapshot.get("baseMargin"), "baseMargin") / 100.0
    operatingDemandRevenue = revenue
    operatingCapacityRevenue = revenue * (1.0 + capacityHeadroom)
    if operatingDrivers is not None:
        operatingDemandRevenue, operatingCapacityRevenue, _operatingProfit = _reconcileOperatingDrivers(
            operatingDrivers,
            revenue=revenue,
            operatingMargin=operatingMargin,
            capacityHeadroom=capacityHeadroom,
            tolerance=operatingDriverTolerance,
        )
    cash = _required(getLatest(series, "BS", "cash_and_cash_equivalents"), "cash")
    receivables = _required(
        _firstPresent(
            getLatest(series, "BS", "trade_receivables"),
            getLatest(series, "BS", "trade_and_other_receivables"),
        ),
        "receivables",
    )
    inventories = _required(getLatest(series, "BS", "inventories"), "inventories")
    payables = _required(
        _firstPresent(
            getLatest(series, "BS", "trade_payables"),
            getLatest(series, "BS", "trade_and_other_payables"),
        ),
        "payables",
    )
    ppe = _required(getLatest(series, "BS", "tangible_assets"), "ppe")
    totalAssets = _required(getLatest(series, "BS", "total_assets"), "totalAssets")
    totalLiabilities = _required(getLatest(series, "BS", "total_liabilities"), "totalLiabilities")
    equity = _required(
        _firstPresent(
            getLatest(series, "BS", "total_stockholders_equity"),
            getLatest(series, "BS", "owners_of_parent_equity"),
        ),
        "equity",
    )
    debtParts = (
        getLatest(series, "BS", "shortterm_borrowings"),
        getLatest(series, "BS", "longterm_borrowings"),
        getLatest(series, "BS", "debentures"),
    )
    if all(value is None for value in debtParts):
        raise SimulationBlocked("financial snapshot missing: debt")
    if any(value is None for value in debtParts):
        raise SimulationBlocked("financial snapshot has incomplete debt components")
    debt = sum(float(value) for value in debtParts if value is not None)
    warnings: list[str] = []
    warnings.extend(f"snapshotAssumption:{item}" for item in snapshot.get("assumptions", ()))
    warnings.extend(f"snapshotWarning:{item}" for item in snapshot.get("warnings", ()))

    otherAssets = totalAssets - cash - receivables - inventories - ppe
    otherLiabilities = totalLiabilities - payables - debt
    otherNetAssets = otherAssets - otherLiabilities
    state = FinancialState(
        revenue=revenue,
        latentDemandRevenue=operatingDemandRevenue,
        operatingMargin=operatingMargin,
        cash=cash,
        debt=debt,
        receivables=receivables,
        inventories=inventories,
        payables=payables,
        ppe=ppe,
        otherNetAssets=otherNetAssets,
        equity=equity,
    )

    ratios = extractHistoricalRatios(series)
    depreciationRate = (ratios.depreciation_ratio / 100.0) * revenue / ppe
    params = FinancialParameters(
        taxRate=ratios.effective_tax_rate / 100.0,
        depreciationRate=depreciationRate,
        receivablesRatio=ratios.receivables_to_revenue / 100.0,
        payablesRatio=ratios.payables_to_revenue / 100.0,
        revenuePerPpe=operatingCapacityRevenue / ppe,
        dividendPayout=ratios.dividend_payout / 100.0,
    )
    warnings.extend(ratios.warnings)
    if ratios.confidence != "high":
        warnings.append(f"historicalRatioConfidence:{ratios.confidence}")
    refs = ("simulate.registry:buildSnapshot", "analysis.financial.proforma:extractHistoricalRatios")
    if operatingDrivers is not None:
        warnings.append(f"operatingDriverInputs:{operatingDrivers.evidenceRole}")
        warnings.append(f"capacityHeadroomFromOperatingDrivers:{capacityHeadroom:.6g}")
        refs = refs + tuple(operatingDrivers.refs)
    else:
        warnings.append(f"capacityHeadroomAssumption:{capacityHeadroom:.6g}")
    return FinancialWorldInputs(
        state=state,
        parameters=params,
        asOf=str(snapshot.get("asOf", "")),
        refs=refs,
        warnings=tuple(warnings),
        operatingDrivers=operatingDrivers,
    )


def _financialVariables(*, operatingMode: bool) -> tuple[VariableSpec, ...]:
    metricUnits = {
        "identityResidualRatio": "ratio",
        "capacityUtilization": "ratio",
        "cashRunwaySteps": "stepCountCapped",
        "capacityBound": "boolean",
        "derivedDemandGrowth": "ratioChangePerStep",
        "derivedMarginChange": "ratioPointChangePerStep",
        "servedUnits": "unit",
        "unmetUnits": "unit",
        "effectiveCapacityUnits": "unit",
        "unitGrossProfit": "currencyPerUnit",
    }
    operatingStates = (
        (
            VariableSpec("unitPrice", "currencyPerUnit", "state", lower=0.0),
            VariableSpec("demandUnits", "unit", "state", lower=0.0),
            VariableSpec("unitCost", "currencyPerUnit", "state", lower=0.0),
            VariableSpec("fixedCost", "currencyPerStep", "state", lower=0.0),
            VariableSpec("capacityUnits", "unit", "state", lower=0.0),
        )
        if operatingMode
        else ()
    )
    if operatingMode:
        shocks = tuple(
            VariableSpec(name, "ratioChangePerStep", "shock", lower=-1.0)
            for name in ("priceChange", "volumeChange", "unitCostChange", "fixedCostChange", "capacityChange")
        ) + (VariableSpec("debtRate", "effectiveRatePerStep", "shock", lower=0.0, upper=1.0),)
    else:
        shocks = (
            VariableSpec("demandGrowth", "ratioChangePerStep", "shock", lower=-1.0),
            VariableSpec("marginChange", "ratioPointChangePerStep", "shock", lower=-1.0, upper=1.0),
            VariableSpec("debtRate", "effectiveRatePerStep", "shock", lower=0.0, upper=1.0),
        )
    metricIds = _METRIC_IDS + (_OPERATING_METRIC_IDS if operatingMode else ())
    return tuple(
        [VariableSpec(name, "currency" if name != "operatingMargin" else "ratio", "state") for name in _STATE_IDS]
        + list(operatingStates)
        + list(shocks)
        + [VariableSpec(name, metricUnits.get(name, "currency"), "metric") for name in metricIds]
    )


def buildFinancialWorld(
    inputs: FinancialWorldInputs,
    *,
    maxFinancing: float,
) -> tuple[WorldModel, WorldState]:
    """Bind the analysis-owned one-step leaf into the generic world executor.

    Args:
        inputs: Compiled financial world inputs.
        maxFinancing: Per-step borrowing and repayment bound.

    Returns:
        ``WorldModel`` and matching ``WorldState`` ready for ``simulateWorld``.

    Raises:
        ValueError: If financing limits or step contract values are invalid.
        SimulationSpecError: If parameter frequency does not match the world step.

    Example:
        ``model, initial = buildFinancialWorld(inputs, maxFinancing=50.0)``
    """

    if maxFinancing < 0:
        raise ValueError("maxFinancing must be nonnegative")
    if not inputs.stepFrequency or inputs.stepSpan < 1:
        raise ValueError("financial world needs a valid step contract")
    if inputs.parameterFrequency != inputs.stepFrequency:
        raise SimulationSpecError("financial parameter frequency must match the world step frequency")
    operatingMode = inputs.operatingDrivers is not None
    if operatingMode:
        _validateOperatingDrivers(inputs.operatingDrivers)
    variables = _financialVariables(operatingMode=operatingMode)
    actions = (
        ActionSpec("capexRatio", "ratio", 0.0, 1.0, 0, 0.0, "explicitAssumption", "financial-step:capex"),
        ActionSpec("inventoryRatio", "ratio", 0.0, 1.0, 0, 0.0, "explicitAssumption", "financial-step:nwc"),
        ActionSpec("borrow", "currency", 0.0, maxFinancing, 0, 0.0, "accountingIdentity", "financial-step:debt"),
        ActionSpec("repay", "currency", 0.0, maxFinancing, 0, 0.0, "accountingIdentity", "financial-step:debt"),
    )
    params = inputs.parameters

    def financialStep(ctx):
        """한 기간의 세계 입력을 analysis 소유 재무 전이 leaf로 전달한다.

        Args:
            ctx: Generic world step context with declared prior state, shocks, actions, and path parameters.

        Returns:
            Next state and financial metrics for one simulated period.

        Raises:
            SimulationBlocked: If the operating driver bridge produces an impossible capacity state.
            FinancialStepError: Propagated when the analysis leaf rejects the period projection.

        Example:
            ``outputs = financialStep(ctx)``
        """

        state = FinancialState(**{name: ctx.prior[name] for name in _STATE_IDS})
        parameterValues = {}
        for name in params.__dataclass_fields__:
            value = ctx.pathParameters.get(name, getattr(params, name))
            parameterValues[name] = None if value is None else float(value)
        effectiveParameters = FinancialParameters(**parameterValues)
        operatingProjection = _deriveOperatingProjection(ctx, state, effectiveParameters) if operatingMode else None
        if operatingProjection is None:
            shock = FinancialShock(
                demandGrowth=ctx.shocks["demandGrowth"],
                marginChange=ctx.shocks["marginChange"],
                debtRate=ctx.shocks["debtRate"],
            )
        else:
            if state.ppe <= 0:
                raise SimulationBlocked("operating capacity needs positive PPE")
            effectiveParameters = replace(
                effectiveParameters,
                revenuePerPpe=operatingProjection.capacityRevenue / state.ppe,
            )
            shock = FinancialShock(
                demandGrowth=operatingProjection.demandGrowth,
                marginChange=operatingProjection.marginChange,
                debtRate=ctx.shocks["debtRate"],
            )
        action = FinancialAction(
            capexRatio=ctx.actions["capexRatio"],
            inventoryRatio=ctx.actions["inventoryRatio"],
            borrow=ctx.actions["borrow"],
            repay=ctx.actions["repay"],
        )
        result = projectFinancialStep(state, effectiveParameters, shock, action)
        nextState = {name: getattr(result.state, name) for name in _STATE_IDS}
        if operatingProjection is not None:
            capacityUnitsPerPpe = operatingProjection.capacityUnits / state.ppe
            nextState.update(
                {
                    "unitPrice": operatingProjection.unitPrice,
                    "demandUnits": operatingProjection.demandUnits,
                    "unitCost": operatingProjection.unitCost,
                    "fixedCost": operatingProjection.fixedCost,
                    "capacityUnits": result.state.ppe * capacityUnitsPerPpe,
                }
            )
        cashBurn = max(0.0, -result.cashChange)
        metrics = {
            "demandRevenue": result.demandRevenue,
            "capacityRevenue": result.capacityRevenue,
            "capacityUtilization": result.state.revenue / result.capacityRevenue if result.capacityRevenue > 0 else 0.0,
            "unmetDemand": result.unmetDemand,
            "operatingProfit": result.operatingProfit,
            "depreciation": result.depreciation,
            "capex": result.capex,
            "interest": result.interest,
            "tax": result.tax,
            "netIncome": result.netIncome,
            "dividends": result.dividends,
            "deltaNwc": result.deltaNwc,
            "cfo": result.cfo,
            "cashChange": result.cashChange,
            "cashBurn": cashBurn,
            "cashRunwaySteps": _cashRunwaySteps(result.state.cash, cashBurn),
            "identityResidual": result.identityResidual,
            "identityResidualRatio": result.identityResidual / max(abs(result.state.equity), 1.0),
            "netCash": result.state.cash - result.state.debt,
            "capacityBound": float(result.capacityBound),
        }
        if operatingProjection is not None:
            metrics.update(
                {
                    "derivedDemandGrowth": operatingProjection.demandGrowth,
                    "derivedMarginChange": operatingProjection.marginChange,
                    "servedUnits": operatingProjection.servedUnits,
                    "unmetUnits": operatingProjection.unmetUnits,
                    "effectiveCapacityUnits": operatingProjection.capacityUnits,
                    "operatingDriverRevenue": operatingProjection.operatingRevenue,
                    "operatingDriverProfit": operatingProjection.operatingProfit,
                    "unitGrossProfit": operatingProjection.unitPrice - operatingProjection.unitCost,
                }
            )
        return {**nextState, **metrics}

    metricIds = _METRIC_IDS + (_OPERATING_METRIC_IDS if operatingMode else ())
    law = LawSpec(
        lawId="financialStep",
        outputs=_STATE_IDS + (_OPERATING_STATE_IDS if operatingMode else ()) + metricIds,
        priorInputs=_STATE_IDS + (_OPERATING_STATE_IDS if operatingMode else ()),
        shockInputs=_OPERATING_SHOCK_IDS if operatingMode else ("demandGrowth", "marginChange", "debtRate"),
        actionInputs=("capexRatio", "inventoryRatio", "borrow", "repay"),
        pathParameterInputs=tuple(_FINANCIAL_PARAMETER_UNITS),
        pathParameterUnits=_FINANCIAL_PARAMETER_UNITS,
        evidenceKind="explicitAssumption",
        provenance="analysis.financial.stepProjection:projectFinancialStep",
        version="3" if operatingMode else "2",
        parameters={
            **asdict(params),
            "parameterFrequency": inputs.parameterFrequency,
            "operatingDriverMode": operatingMode,
        },
        fn=financialStep,
    )
    initialValues = {name: float(getattr(inputs.state, name)) for name in _STATE_IDS}
    if operatingMode:
        initialValues.update({name: float(getattr(inputs.operatingDrivers, name)) for name in _OPERATING_STATE_IDS})
    initial = WorldState(values=initialValues, asOf=inputs.asOf, refs=inputs.refs)
    return WorldModel(
        "company-financial-world",
        "3" if operatingMode else "2",
        variables,
        actions,
        (law,),
        stepFrequency=inputs.stepFrequency,
        stepSpan=inputs.stepSpan,
    ), initial


def buildFinancialPath(
    pathId: str,
    *,
    demandGrowth: Sequence[float],
    marginChange: Sequence[float],
    debtRate: Sequence[float],
    weight: float | None = None,
    weightKind: str = "unweighted",
    refs: tuple[str, ...] = (),
    frequency: str = "year",
    stepSpan: int = 1,
    parameterDraws: Mapping[str, float] | None = None,
) -> ScenarioPath:
    """연간 수요 성장, 마진 증분, 금리 수준을 명시적 세계 경로로 만든다.

    Args:
        pathId: Scenario path identifier.
        demandGrowth: Per-step latent demand revenue growth.
        marginChange: Per-step operating margin point change.
        debtRate: Per-step effective debt rate.
        weight: Optional path weight.
        weightKind: Weight interpretation used by the world executor.
        refs: Evidence or assumption references for the path.
        frequency: Time grid label.
        stepSpan: Number of frequency units per step.
        parameterDraws: Optional path-level parameter overrides.

    Returns:
        ``ScenarioPath`` consumable by ``runFinancialStrategies``.

    Raises:
        ValueError: If shock paths do not share one horizon.

    Example:
        ``path = buildFinancialPath("base", demandGrowth=(0,), marginChange=(0,), debtRate=(0.05,))``
    """

    lengths = {len(demandGrowth), len(marginChange), len(debtRate)}
    if len(lengths) != 1:
        raise ValueError("financial shock paths must share a horizon")
    steps = tuple(
        {
            "demandGrowth": float(demandGrowth[i]),
            "marginChange": float(marginChange[i]),
            "debtRate": float(debtRate[i]),
        }
        for i in range(len(demandGrowth))
    )
    return ScenarioPath(
        pathId,
        steps,
        weight=weight,
        weightKind=weightKind,
        refs=refs,
        frequency=frequency,
        stepSpan=stepSpan,
        parameterDraws={} if parameterDraws is None else parameterDraws,
    )


def buildOperatingFinancialPath(
    pathId: str,
    *,
    priceChange: Sequence[float],
    volumeChange: Sequence[float],
    unitCostChange: Sequence[float],
    fixedCostChange: Sequence[float],
    capacityChange: Sequence[float],
    debtRate: Sequence[float],
    weight: float | None = None,
    weightKind: str = "unweighted",
    refs: tuple[str, ...] = (),
    frequency: str = "quarter",
    stepSpan: int = 1,
    parameterDraws: Mapping[str, float] | None = None,
) -> ScenarioPath:
    """제품 가격, 물량, 단위원가, 고정비, 생산능력 변화를 명시적 운영 경로로 만든다.

    Args:
        pathId: Scenario path identifier.
        priceChange: Per-step unit price movement.
        volumeChange: Per-step demand unit movement.
        unitCostChange: Per-step variable unit cost movement.
        fixedCostChange: Per-step fixed cost movement.
        capacityChange: Per-step physical capacity movement.
        debtRate: Per-step effective debt rate.
        weight: Optional path weight.
        weightKind: Weight interpretation used by the world executor.
        refs: Evidence or assumption references for the path.
        frequency: Time grid label.
        stepSpan: Number of frequency units per step.
        parameterDraws: Optional path-level parameter overrides.

    Returns:
        ``ScenarioPath`` consumable by the operating-driver financial world.

    Raises:
        ValueError: If driver paths do not share one horizon.

    Example:
        ``path = buildOperatingFinancialPath("unit", priceChange=(0,), volumeChange=(0,), unitCostChange=(0,), fixedCostChange=(0,), capacityChange=(0,), debtRate=(0.05,))``
    """

    lengths = {
        len(priceChange),
        len(volumeChange),
        len(unitCostChange),
        len(fixedCostChange),
        len(capacityChange),
        len(debtRate),
    }
    if len(lengths) != 1:
        raise ValueError("operating driver paths must share a horizon")
    steps = tuple(
        {
            "priceChange": float(priceChange[i]),
            "volumeChange": float(volumeChange[i]),
            "unitCostChange": float(unitCostChange[i]),
            "fixedCostChange": float(fixedCostChange[i]),
            "capacityChange": float(capacityChange[i]),
            "debtRate": float(debtRate[i]),
        }
        for i in range(len(priceChange))
    )
    return ScenarioPath(
        pathId,
        steps,
        weight=weight,
        weightKind=weightKind,
        refs=refs,
        frequency=frequency,
        stepSpan=stepSpan,
        parameterDraws={} if parameterDraws is None else parameterDraws,
    )


def buildFinancialStrategy(
    strategyId: str,
    *,
    capexRatio: Sequence[float],
    inventoryRatio: Sequence[float],
    borrow: Sequence[float],
    repay: Sequence[float],
    refs: tuple[str, ...] = (),
    isBaseline: bool = False,
) -> StrategySpec:
    """기간별 투자, 재고, 차입, 상환 계획을 하나의 전략으로 만든다.

    Args:
        strategyId: Strategy identifier.
        capexRatio: Per-step capex as a ratio of realized revenue.
        inventoryRatio: Per-step inventory as a ratio of realized revenue.
        borrow: Per-step borrowing.
        repay: Per-step debt repayment.
        refs: Evidence or assumption references for the strategy.
        isBaseline: Whether this strategy is the comparison baseline.

    Returns:
        ``StrategySpec`` containing one action row per step.

    Raises:
        ValueError: If action paths do not share one horizon.

    Example:
        ``strategy = buildFinancialStrategy("hold", capexRatio=(0.05,), inventoryRatio=(0.1,), borrow=(0,), repay=(0,))``
    """

    lengths = {len(capexRatio), len(inventoryRatio), len(borrow), len(repay)}
    if len(lengths) != 1:
        raise ValueError("financial action paths must share a horizon")
    actions = tuple(
        {
            "capexRatio": float(capexRatio[i]),
            "inventoryRatio": float(inventoryRatio[i]),
            "borrow": float(borrow[i]),
            "repay": float(repay[i]),
        }
        for i in range(len(capexRatio))
    )
    return StrategySpec(strategyId, actions, refs=refs, isBaseline=isBaseline)


def runFinancialStrategies(
    inputs: FinancialWorldInputs,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
) -> SimulationRun:
    """동일한 회사 상태와 세계 경로에서 여러 재무 전략을 비교한다.

    Args:
        inputs: Compiled financial world inputs.
        paths: Scenario paths to evaluate.
        strategies: Candidate financial strategies.
        debtLimit: Hard debt ceiling used as a constraint.
        maxFinancing: Per-step borrowing and repayment bound.

    Returns:
        ``SimulationRun`` containing traces, breaches, Pareto set, and conditional decision status.

    Raises:
        ValueError: If world construction inputs are invalid.
        SimulationSpecError: If model, path, strategy, or objective contracts are malformed.

    Example:
        ``run = runFinancialStrategies(inputs, (path,), (strategy,), debtLimit=100.0, maxFinancing=50.0)``
    """

    model, initial = buildFinancialWorld(
        inputs,
        maxFinancing=maxFinancing,
    )
    constraints = (
        ConstraintSpec("cash", "ge", 0.0),
        ConstraintSpec("debt", "le", debtLimit),
        ConstraintSpec("identityResidualRatio", "ge", -1e-10),
        ConstraintSpec("identityResidualRatio", "le", 1e-10),
    )
    objectives = (
        ObjectiveSpec("netCash", direction="maximize", risk="worst"),
        ObjectiveSpec("debt", direction="minimize", risk="worst"),
    )
    return simulateWorld(
        model,
        initial,
        paths,
        strategies,
        constraints=constraints,
        objectives=objectives,
        inputWarnings=inputs.warnings,
    )
