"""EDGAR financial replay assembly for the existing world-model tournament.

Each episode freezes parameters at the first filing for its origin quarter and consumes the next
quarter's first reported actions and outcome only as retrospective evidence. This is a conditional
transition test, not a trading backtest or an admission certificate. Cash flows absent from a
filing stay gaps. Model omissions (buybacks, investment portfolios, FX and other financing) stay
visible as prediction error, never as a balancing plug. Monetary values are scaled by origin
quarter revenue so large and small origins have equal scoring units.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta

import polars as pl

from dartlab.analysis.financial.edgarPitState import (
    CompiledQuarterlyFinancialState,
    EdgarStateError,
    FactEvidence,
    compileEdgarPeriodFlows,
    compileEdgarQuarterlyFinancialState,
)
from dartlab.analysis.financial.stepProjection import (
    FinancialAction,
    FinancialParameters,
    FinancialShock,
    FinancialState,
    FinancialStepError,
    projectFinancialStep,
)
from dartlab.simulate.financialWorld import FinancialWorldInputs, buildFinancialWorld
from dartlab.simulate.hindcast import WorldModelReplayEpisode
from dartlab.simulate.vintage import canonicalPayloadHash
from dartlab.simulate.world import ScenarioPath, StrategySpec, WorldModel, WorldState

_PARAMETER_TAGS = {
    "depreciation": ("DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet"),
    "tax": ("IncomeTaxExpenseBenefit",),
    "pretax": (
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    ),
    "netIncome": ("NetIncomeLoss",),
    "dividends": ("PaymentsOfDividends",),
    "interest": ("InterestExpense", "InterestExpenseDebt"),
}
_ACTION_TAGS = {
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    "termBorrow": ("ProceedsFromIssuanceOfLongTermDebt",),
    "termRepay": ("RepaymentsOfLongTermDebt",),
    "commercialPaperNet": ("ProceedsFromRepaymentsOfCommercialPaper",),
}
REPLAY_METRICS = ("cash", "debt", "ppe", "equity")
_WARNINGS = (
    "retrospectiveTransitionNotDecisionBacktest",
    "realizedRevenueIsDemandProxy",
    "depreciationIncludesAmortization",
    "financingScopeTermDebtAndNetCommercialPaper",
    "buybacksInvestmentsOtherFinancingAndFxNotModeled",
    "localReconstructionNotContemporaneousReceipt",
)
_CENSUS_SCHEMA = dict.fromkeys(("originAsOf", "fiscalThrough", "nextFiscalThrough", "status", "reason"), pl.String)
_EVIDENCE_SCHEMA = {
    **dict.fromkeys(
        (
            "episodeId",
            "role",
            "conceptId",
            "unit",
            "currency",
            "kind",
            "fiscalStart",
            "fiscalEnd",
            "filedAt",
            "accession",
            "form",
            "tag",
            "status",
            "derivation",
        ),
        pl.String,
    ),
    "value": pl.Float64,
    "derivationInputs": pl.List(pl.String),
}


@dataclass(frozen=True)
class FinancialReplay:
    """실행할 episode와 모든 공시 시점의 성공·결손 및 원문 근거 표를 보존한다."""

    episodes: tuple[WorldModelReplayEpisode, ...]
    census: pl.DataFrame
    evidence: pl.DataFrame
    models: tuple[WorldModel, ...]
    warnings: tuple[str, ...] = _WARNINGS


def _date(value: str) -> datetime:
    return datetime.strptime(str(value).replace("-", ""), "%Y%m%d")


def _flows(
    facts: pl.DataFrame,
    compiled: CompiledQuarterlyFinancialState,
    tags: dict[str, tuple[str, ...]],
) -> tuple[FactEvidence, ...]:
    quarter = compiled.quarters[-1]
    rows = compileEdgarPeriodFlows(
        facts,
        tags,
        knowledgeAsOf=compiled.knowledgeAsOf,
        fiscalStart=quarter.fiscalStart,
        fiscalEnd=quarter.fiscalEnd,
    )
    missing = sorted(set(tags) - {row.conceptId for row in rows})
    if missing:
        raise EdgarStateError(f"missing quarter flows: {', '.join(missing)}")
    return rows


def _ratio(value: float, denominator: float, label: str) -> float:
    if denominator <= 0 or not 0 <= value / denominator <= 1:
        raise EdgarStateError(f"unsupported financial ratio: {label}")
    return value / denominator


def _parameters(
    compiled: CompiledQuarterlyFinancialState,
    evidence: tuple[FactEvidence, ...],
    capacityHeadroom: float,
) -> FinancialParameters:
    values = {row.conceptId: row.value for row in evidence}
    state = compiled.state
    return FinancialParameters(
        taxRate=_ratio(values["tax"], values["pretax"], "taxRate"),
        depreciationRate=_ratio(values["depreciation"], state.ppe, "depreciationRate"),
        receivablesRatio=_ratio(state.receivables, state.revenue, "receivablesRatio"),
        payablesRatio=_ratio(state.payables, state.revenue, "payablesRatio"),
        revenuePerPpe=state.revenue * (1 + capacityHeadroom) / state.ppe,
        dividendPayout=_ratio(values["dividends"], values["netIncome"], "dividendPayout"),
    )


def _scaledState(state: FinancialState, scale: float) -> FinancialState:
    return FinancialState(
        **{key: value if key == "operatingMargin" else value / scale for key, value in asdict(state).items()}
    )


def _carryStep(ctx):
    """현재 상태가 다음 분기에도 그대로라는 사전 고정 비교 기준."""
    return dict(ctx.prior)


def _models(inputs: FinancialWorldInputs) -> tuple[WorldModel, ...]:
    model, _ = buildFinancialWorld(inputs, maxFinancing=10.0)
    stateIds = tuple(asdict(inputs.state))
    carryLaw = replace(
        model.laws[0],
        lawId="carryState",
        outputs=stateIds,
        fn=_carryStep,
        shockInputs=(),
        actionInputs=(),
        parameters={},
        provenance="prior-quarter-state",
        version="1",
    )
    carry = replace(model, modelId="carry", laws=(carryLaw,))
    return carry, model


def _episode(
    facts: pl.DataFrame,
    before: CompiledQuarterlyFinancialState,
    after: CompiledQuarterlyFinancialState,
    entityId: str,
    capacityHeadroom: float,
) -> tuple[WorldModelReplayEpisode, FinancialWorldInputs, list[dict]]:
    origin, outcome = before.knowledgeAsOf, after.knowledgeAsOf
    nextStart = after.quarters[-1].fiscalStart
    if _date(nextStart) != _date(before.fiscalThrough) + timedelta(days=1):
        raise EdgarStateError("next outcome is not the adjacent fiscal quarter")
    parameterEvidence = _flows(facts, before, _PARAMETER_TAGS)
    actionEvidence = _flows(facts, after, _ACTION_TAGS)
    params = _parameters(before, parameterEvidence, capacityHeadroom)
    scale = before.state.revenue
    if scale <= 0 or after.state.revenue <= 0:
        raise EdgarStateError("replay needs positive quarterly revenue")
    state = _scaledState(before.state, scale)
    actual = _scaledState(after.state, scale)
    actions = {row.conceptId: row.value for row in actionEvidence}
    if any(actions[key] < 0 for key in ("capex", "termBorrow", "termRepay")):
        raise EdgarStateError("negative gross financing or capex flow")
    # Commercial paper is reported net. Keep that interpretation in the evidence and warnings;
    # do not add the separately reported maturity components and double count it.
    borrow = (actions["termBorrow"] + max(actions["commercialPaperNet"], 0.0)) / scale
    repay = (actions["termRepay"] + max(-actions["commercialPaperNet"], 0.0)) / scale
    if max(borrow, repay) > 10 or repay > state.debt + borrow:
        raise EdgarStateError("observed financing is outside the financial world contract")
    interest = next(row.value for row in parameterEvidence if row.conceptId == "interest")
    debtRate = _ratio(interest, before.state.debt, "debtRate")
    initialRefs = (
        f"edgarState:{before.stateHash}",
        f"quarterRevenueScale:{scale:.17g}",
        f"parameters:{canonicalPayloadHash(parameterEvidence)}",
    )
    inputs = FinancialWorldInputs(
        state, params, origin, initialRefs, _WARNINGS, stepFrequency="quarter", parameterFrequency="quarter"
    )
    initial = WorldState(
        asdict(state), asOf=before.fiscalThrough, refs=initialRefs, knowledgeAsOf=origin, decisionAsOf=origin
    )
    path = ScenarioPath(
        f"{entityId}:{before.fiscalThrough}:{after.fiscalThrough}",
        (
            {
                "demandGrowth": actual.revenue / state.revenue - 1,
                "marginChange": actual.operatingMargin - state.operatingMargin,
                "debtRate": debtRate,
            },
        ),
        frequency="quarter",
        parameterDraws=asdict(params),
        knowledgeAsOf=outcome,
        validationStatus="retrospectiveOnly",
        historyStatus="realizedOutcome",
        refs=(
            f"edgarState:{after.stateHash}",
            f"parametersAsKnown:{origin}",
            f"capacityHeadroomAssumption:{capacityHeadroom:g}",
        ),
    )
    policy = StrategySpec(
        "reportedActions",
        (
            {
                "capexRatio": _ratio(actions["capex"], after.state.revenue, "capexRatio"),
                "inventoryRatio": _ratio(after.state.inventories, after.state.revenue, "inventoryRatio"),
                "borrow": borrow,
                "repay": repay,
            },
        ),
        refs=(f"actionEvidence:{canonicalPayloadHash(actionEvidence)}", f"edgarState:{after.stateHash}"),
        policyVersion="reported-quarter-v1",
        policyProvenance="retrospective SEC cash flows and inventory",
    )
    episode = WorldModelReplayEpisode(
        f"{entityId}:{before.fiscalThrough}",
        origin,
        outcome,
        "reportedGrowth" if actual.revenue >= state.revenue else "reportedContraction",
        initial,
        path,
        policy,
        ({metric: getattr(actual, metric) for metric in REPLAY_METRICS},),
    )
    evidence = [
        {"episodeId": episode.episodeId, "role": role, **asdict(item)}
        for role, items in (
            ("initial", before.evidence),
            ("parameter", parameterEvidence),
            ("action", actionEvidence),
            ("outcome", after.evidence),
        )
        for item in items
    ]
    return episode, inputs, evidence


def buildEdgarFinancialReplay(
    facts: pl.DataFrame,
    *,
    entityId: str,
    knowledgeAsOf: str,
    capacityHeadroom: float = 0.20,
) -> FinancialReplay:
    """Assemble first-filing quarter transitions and keep every excluded origin in a table.

    Args:
        facts: One company's companyfacts rows, kept in memory once.
        entityId: Ticker or stable company identifier for episode ids.
        knowledgeAsOf: Evaluation cutoff. Later filings never enter states, parameters or outcomes.
        capacityHeadroom: Explicit capacity proxy above origin revenue, between zero and one.

    Returns:
        Episodes for the existing tournament, two comparable models, census and evidence tables.
        Empty episodes mean no usable transitions; census supplies the reasons.

    Raises:
        ValueError: Invalid identity, cutoff, capacity assumption or multiple companies.

    Example:
        ``replay = buildEdgarFinancialReplay(facts, entityId="AAPL", knowledgeAsOf="20260930")``.
    """
    if not entityId or not 0 <= capacityHeadroom <= 1:
        raise ValueError("entityId and finite capacity headroom in [0, 1] are required")
    for column in ("cik", "entityName"):
        if column in facts.columns and facts[column].drop_nulls().n_unique() > 1:
            raise ValueError("financial replay requires exactly one company")
    cutoff = _date(knowledgeAsOf).strftime("%Y%m%d")
    periodic = facts.filter(pl.col("form").str.contains(r"^10-[KQ](?:/A)?$"))
    dates = sorted({_date(day).strftime("%Y%m%d") for day in periodic["filed"].drop_nulls()})
    records, states = [], []
    seen = set()
    for filed in dates:
        origin = (_date(filed) + timedelta(days=1)).strftime("%Y%m%d")
        if origin > cutoff:
            continue
        row = {"originAsOf": origin, "fiscalThrough": "", "nextFiscalThrough": "", "status": "stateGap", "reason": ""}
        records.append(row)
        try:
            compiled = compileEdgarQuarterlyFinancialState(facts, knowledgeAsOf=origin)
            row["fiscalThrough"] = compiled.fiscalThrough
            if (_date(origin) - _date(compiled.fiscalThrough)).days > 400:
                raise EdgarStateError("origin describes a stale fiscal period")
            if compiled.fiscalThrough in seen:
                row.update(status="duplicatePeriod", reason="first filing already retained")
                continue
            seen.add(compiled.fiscalThrough)
            states.append((compiled, row))
            row["status"] = "noOutcome"
        except EdgarStateError as error:
            row["reason"] = str(error)
    episodes, evidenceRows, models = [], [], ()
    for (before, row), (after, _) in zip(states, states[1:]):
        row["nextFiscalThrough"] = after.fiscalThrough
        try:
            episode, inputs, evidence = _episode(facts, before, after, entityId, capacityHeadroom)
            # Exercise the actual leaf here so unsupported source ratios remain census gaps.
            projectFinancialStep(
                inputs.state,
                inputs.parameters,
                FinancialShock(**episode.realizedPath.steps[0]),
                FinancialAction(**episode.observedPolicy.actionsByStep[0]),
            )
            episodes.append(episode)
            evidenceRows.extend(evidence)
            if not models:
                models = _models(inputs)
            row["status"] = "ready"
        except (EdgarStateError, FinancialStepError) as error:
            row.update(status="replayGap", reason=str(error))
    return FinancialReplay(
        tuple(episodes),
        pl.DataFrame(records, schema=_CENSUS_SCHEMA),
        pl.DataFrame(evidenceRows, schema=_EVIDENCE_SCHEMA),
        models,
    )
