"""Compile a frozen company snapshot into an auditable financial world.\n\nThis L2.5 adapter maps explicit company state, scenario paths, and financial\nactions onto ``simulate.world``. The one-period accounting projection remains\nowned by ``analysis.financial.stepProjection``. Historical ratios and capacity\nheadroom remain surfaced assumptions, so the default result is conditional and\ncannot emit an automatic strategy recommendation.\n"""

from __future__ import annotations

from dataclasses import dataclass
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
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    simulateWorld,
)


@dataclass(frozen=True)
class FinancialWorldInputs:
    """동결된 회사 상태와 전이 파라미터, 근거, 경고를 묶는다."""

    state: FinancialState
    parameters: FinancialParameters
    asOf: str
    refs: tuple[str, ...]
    warnings: tuple[str, ...]


def _required(value, label: str) -> float:
    if value is None:
        raise SimulationBlocked(f"financial snapshot missing: {label}")
    return float(value)


def _firstPresent(*values):
    """Return the first non-None account value while preserving a reported zero."""

    return next((value for value in values if value is not None), None)


def financialInputsFromSnapshot(snapshot: Mapping, *, capacityHeadroom: float) -> FinancialWorldInputs:
    """Compile an honest reduced financial state from a frozen simulate snapshot."""

    if capacityHeadroom < 0:
        raise ValueError("capacityHeadroom must be nonnegative")
    series = snapshot.get("series")
    if not series:
        raise SimulationBlocked("financial snapshot missing: series")
    revenue = _required(snapshot.get("baseRevenue"), "baseRevenue")
    operatingMargin = _required(snapshot.get("baseMargin"), "baseMargin") / 100.0
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
    debt = sum(float(value) for value in debtParts if value is not None)
    warnings: list[str] = []
    if any(value is None for value in debtParts):
        warnings.append("partialDebtComponents")

    otherAssets = totalAssets - cash - receivables - inventories - ppe
    otherLiabilities = totalLiabilities - payables - debt
    otherNetAssets = otherAssets - otherLiabilities
    state = FinancialState(
        revenue=revenue,
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
        revenuePerPpe=(revenue * (1.0 + capacityHeadroom)) / ppe,
        dividendPayout=ratios.dividend_payout / 100.0,
    )
    warnings.extend(ratios.warnings)
    if ratios.confidence != "high":
        warnings.append(f"historicalRatioConfidence:{ratios.confidence}")
    warnings.append(f"capacityHeadroomAssumption:{capacityHeadroom:.6g}")
    return FinancialWorldInputs(
        state=state,
        parameters=params,
        asOf=str(snapshot.get("asOf", "")),
        refs=("simulate.registry:buildSnapshot", "analysis.financial.proforma:extractHistoricalRatios"),
        warnings=tuple(warnings),
    )


_STATE_IDS = (
    "revenue",
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
    "identityResidual",
    "identityResidualRatio",
    "netCash",
    "capacityBound",
)


def buildFinancialWorld(
    inputs: FinancialWorldInputs,
    *,
    maxFinancing: float,
    transitionEvidence: str = "explicitAssumption",
) -> tuple[WorldModel, WorldState]:
    """Bind the analysis-owned one-step leaf into the generic world executor."""

    if maxFinancing < 0:
        raise ValueError("maxFinancing must be nonnegative")
    metricUnits = {
        "identityResidualRatio": "ratio",
        "capacityBound": "boolean",
    }
    variables = tuple(
        [VariableSpec(name, "currency" if name != "operatingMargin" else "ratio", "state") for name in _STATE_IDS]
        + [
            VariableSpec("demandGrowth", "ratio", "shock", lower=-1.0),
            VariableSpec("marginDelta", "ratio", "shock", lower=-1.0, upper=1.0),
            VariableSpec("debtRate", "ratio", "shock", lower=0.0, upper=1.0),
        ]
        + [VariableSpec(name, metricUnits.get(name, "currency"), "metric") for name in _METRIC_IDS]
    )
    actions = (
        ActionSpec("capexRatio", "ratio", 0.0, 1.0, 0, 0.0, "accountingIdentity", "financial-step:capex"),
        ActionSpec("inventoryRatio", "ratio", 0.0, 1.0, 0, 0.0, "accountingIdentity", "financial-step:nwc"),
        ActionSpec("borrow", "currency", 0.0, maxFinancing, 0, 0.0, "accountingIdentity", "financial-step:debt"),
        ActionSpec("repay", "currency", 0.0, maxFinancing, 0, 0.0, "accountingIdentity", "financial-step:debt"),
    )
    params = inputs.parameters

    def financialStep(ctx):
        """한 기간의 세계 입력을 analysis 소유 재무 전이 leaf로 전달한다."""

        state = FinancialState(**{name: ctx.prior[name] for name in _STATE_IDS})
        shock = FinancialShock(
            demandGrowth=ctx.shocks["demandGrowth"],
            marginDelta=ctx.shocks["marginDelta"],
            debtRate=ctx.shocks["debtRate"],
        )
        action = FinancialAction(
            capexRatio=ctx.actions["capexRatio"],
            inventoryRatio=ctx.actions["inventoryRatio"],
            borrow=ctx.actions["borrow"],
            repay=ctx.actions["repay"],
        )
        result = projectFinancialStep(state, params, shock, action)
        nextState = {name: getattr(result.state, name) for name in _STATE_IDS}
        metrics = {
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
            "identityResidual": result.identityResidual,
            "identityResidualRatio": result.identityResidual / max(abs(result.state.equity), 1.0),
            "netCash": result.state.cash - result.state.debt,
            "capacityBound": float(result.capacityBound),
        }
        return {**nextState, **metrics}

    law = LawSpec(
        lawId="financialStep",
        outputs=_STATE_IDS + _METRIC_IDS,
        priorInputs=_STATE_IDS,
        shockInputs=("demandGrowth", "marginDelta", "debtRate"),
        actionInputs=("capexRatio", "inventoryRatio", "borrow", "repay"),
        evidenceKind=transitionEvidence,
        provenance="analysis.financial.stepProjection:projectFinancialStep",
        version="1",
        fn=financialStep,
    )
    initial = WorldState(
        values={name: float(getattr(inputs.state, name)) for name in _STATE_IDS},
        asOf=inputs.asOf,
        refs=inputs.refs,
    )
    return WorldModel("company-financial-world", "1", variables, actions, (law,)), initial


def buildFinancialPath(
    pathId: str,
    *,
    demandGrowth: Sequence[float],
    marginDelta: Sequence[float],
    debtRate: Sequence[float],
    weight: float | None = None,
    weightKind: str = "unweighted",
    refs: tuple[str, ...] = (),
) -> ScenarioPath:
    """기간별 수요, 마진, 금리 조건을 하나의 명시적 세계 경로로 만든다."""

    lengths = {len(demandGrowth), len(marginDelta), len(debtRate)}
    if len(lengths) != 1:
        raise ValueError("financial shock paths must share a horizon")
    steps = tuple(
        {"demandGrowth": float(demandGrowth[i]), "marginDelta": float(marginDelta[i]), "debtRate": float(debtRate[i])}
        for i in range(len(demandGrowth))
    )
    return ScenarioPath(pathId, steps, weight=weight, weightKind=weightKind, refs=refs)


def buildFinancialStrategy(
    strategyId: str,
    *,
    capexRatio: Sequence[float],
    inventoryRatio: Sequence[float],
    borrow: Sequence[float],
    repay: Sequence[float],
    refs: tuple[str, ...] = (),
) -> StrategySpec:
    """기간별 투자, 재고, 차입, 상환 계획을 하나의 전략으로 만든다."""

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
    return StrategySpec(strategyId, actions, refs=refs)


def runFinancialStrategies(
    inputs: FinancialWorldInputs,
    paths: tuple[ScenarioPath, ...],
    strategies: tuple[StrategySpec, ...],
    *,
    debtLimit: float,
    maxFinancing: float,
    transitionEvidence: str = "explicitAssumption",
) -> SimulationRun:
    """동일한 회사 상태와 세계 경로에서 여러 재무 전략을 비교한다."""

    model, initial = buildFinancialWorld(
        inputs,
        maxFinancing=maxFinancing,
        transitionEvidence=transitionEvidence,
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
    return simulateWorld(model, initial, paths, strategies, constraints=constraints, objectives=objectives)
