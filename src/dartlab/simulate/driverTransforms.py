"""Explicit grid transforms for driver history sources.

Transforms in this module make frequency alignment visible and auditable. They
do not improve source vintage quality, infer missing observations, or turn
state-like values into shocks. Each output row is selected using the target
row's own availability time and carries the original source weakness forward.
"""

from __future__ import annotations

import math
from dataclasses import asdict
from datetime import datetime
from typing import Mapping

import polars as pl

from dartlab.simulate.driverPaths import DriverAssumptionSource, DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.vintage import canonicalPayloadHash

_FACTOR_TIMINGS = {"level", "rate"}
_ASSUMPTION_FACTOR_TIMINGS = {"innovation", "change", "level", "rate"}
_STATE_MEASURE_KINDS = {"stock", "ratio", "stateFeature", "level", "rate"}
_FLOW_MEASURE_KINDS = {
    "flow",
    "periodFlow",
    "cumulative",
    "cumulativeFlow",
    "ytdCumulative",
    "annualCumulative",
}
_FLOW_PERIOD_SCOPES = {"quarter", "annual", "ytd", "ttm", "period"}


class DriverTransformError(ValueError):
    """Raised when a driver source transform would weaken timing or lineage."""


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverTransformError(f"invalid {label}: {value}")
    return text


def _dateExpr(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8)


def _dateObject(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d")


def _sourceColumn(factor: DriverFactorSpec) -> str:
    return factor.sourceColumn or factor.variableId


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _sourceMeasureKind(value: str, *, targetTiming: str) -> str:
    kind = str(value).strip()
    if not kind:
        raise DriverTransformError("sourceMeasureKind is required for carry-forward")
    if kind in _FLOW_MEASURE_KINDS:
        raise DriverTransformError("flow measures cannot be carry-forwarded as executable driver history")
    if kind not in _STATE_MEASURE_KINDS:
        raise DriverTransformError(f"unsupported sourceMeasureKind for carry-forward: {kind}")
    if targetTiming == "rate" and kind != "rate":
        raise DriverTransformError("rate carry-forward requires rate sourceMeasureKind")
    return kind


def _flowSourceMeasureKind(value: str) -> str:
    kind = str(value).strip()
    if kind not in _FLOW_MEASURE_KINDS:
        raise DriverTransformError("flow explicit assumption requires flow sourceMeasureKind")
    return kind


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise DriverTransformError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise DriverTransformError(f"{label} must be finite")
    return number


def _validateAssumptionFactors(
    factors: tuple[DriverFactorSpec, ...],
    *,
    targetFrequency: str,
    label: str,
) -> tuple[str, ...]:
    if not factors:
        raise DriverTransformError(f"{label} needs at least one output factor")
    variableIds = [factor.variableId for factor in factors]
    if len(set(variableIds)) != len(variableIds):
        raise DriverTransformError(f"{label} factor ids must be unique")
    for factor in factors:
        if (
            not factor.variableId
            or not factor.unit
            or factor.frequency != targetFrequency
            or factor.timing not in _ASSUMPTION_FACTOR_TIMINGS
            or not factor.transformId
        ):
            raise DriverTransformError(f"{label} factor contract is incomplete: {factor.variableId}")
    return tuple(variableIds)


def _validateAssumptionSteps(
    steps: tuple[Mapping[str, float], ...],
    *,
    variableIds: tuple[str, ...],
    label: str,
) -> tuple[dict[str, float], ...]:
    expected = set(variableIds)
    if not steps:
        raise DriverTransformError(f"{label} needs assumption steps")
    out: list[dict[str, float]] = []
    for stepIndex, step in enumerate(steps):
        if set(step) != expected:
            raise DriverTransformError(f"{label} factor coverage drift at step {stepIndex}")
        out.append(
            {variableId: _finite(value, f"{label}.{variableId}.{stepIndex}") for variableId, value in step.items()}
        )
    return tuple(out)


def _flowPeriod(
    *,
    periodStart: str,
    periodEnd: str,
    periodScope: str,
) -> tuple[str, str, str]:
    start = _dateText(periodStart, "periodStart")
    end = _dateText(periodEnd, "periodEnd")
    scope = str(periodScope).strip()
    if scope not in _FLOW_PERIOD_SCOPES:
        raise DriverTransformError(f"unsupported flow periodScope: {scope}")
    if start > end:
        raise DriverTransformError("periodStart must not be after periodEnd")
    return start, end, scope


def _validateTargetGrid(
    targetGrid: pl.DataFrame,
    *,
    eventTimeColumn: str,
    availableAtColumn: str,
    knowledgeAsOf: str,
) -> tuple[dict[str, str], ...]:
    required = {eventTimeColumn, availableAtColumn}
    if not required.issubset(targetGrid.columns):
        raise DriverTransformError(f"target grid missing columns: {sorted(required - set(targetGrid.columns))}")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    dated = targetGrid.with_columns(
        _dateExpr(eventTimeColumn).alias("__event"),
        _dateExpr(availableAtColumn).alias("__available"),
    )
    malformed = dated.filter(
        pl.col("__event").is_null()
        | pl.col("__available").is_null()
        | (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise DriverTransformError("target grid contains malformed eventTime or availableAt")
    rows = (
        dated.filter((pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .select("__event", "__available")
        .sort(["__event", "__available"])
        .to_dicts()
    )
    if not rows:
        raise DriverTransformError("target grid has no rows available by knowledgeAsOf")
    if len({row["__event"] for row in rows}) != len(rows):
        raise DriverTransformError("duplicate target eventTime needs an explicit aggregation transform")
    if any(row["__available"] < row["__event"] for row in rows):
        raise DriverTransformError("target grid availableAt cannot be earlier than eventTime")
    return tuple({"eventTime": row["__event"], "availableAt": row["__available"]} for row in rows)


def _sourceRows(source: DriverHistorySource, *, knowledgeAsOf: str) -> tuple[dict[str, str | float], ...]:
    card = source.card
    required = {"eventTime", "availableAt", *(_sourceColumn(factor) for factor in card.factors)}
    if not required.issubset(source.panel.columns):
        raise DriverTransformError(f"source panel missing columns: {sorted(required - set(source.panel.columns))}")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    valueExprs = [
        pl.col(_sourceColumn(factor)).cast(pl.Float64, strict=False).alias(factor.variableId) for factor in card.factors
    ]
    variableIds = [factor.variableId for factor in card.factors]
    dated = source.panel.with_columns(
        _dateExpr("eventTime").alias("__event"),
        _dateExpr("availableAt").alias("__available"),
        *valueExprs,
    )
    malformed = dated.filter(
        pl.col("__event").is_null()
        | pl.col("__available").is_null()
        | (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise DriverTransformError("source panel contains malformed eventTime or availableAt")
    rows = (
        dated.filter((pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .select(
            pl.col("__event").alias("sourceEventTime"), pl.col("__available").alias("sourceAvailableAt"), *variableIds
        )
        .drop_nulls(variableIds)
        .sort(["sourceEventTime", "sourceAvailableAt"])
        .unique(subset=["sourceEventTime"], keep="last", maintain_order=True)
        .to_dicts()
    )
    if not rows:
        raise DriverTransformError("source panel has no rows available by knowledgeAsOf")
    for row in rows:
        for variableId in variableIds:
            if not math.isfinite(float(row[variableId])):
                raise DriverTransformError(f"source panel contains non-finite values: {variableId}")
    return tuple(rows)


def _carriedRows(
    sourceRows: tuple[dict[str, str | float], ...],
    targetRows: tuple[dict[str, str], ...],
    *,
    variableIds: tuple[str, ...],
    maxStalenessDays: int | None,
) -> tuple[dict[str, str | float], ...]:
    out: list[dict[str, str | float]] = []
    for target in targetRows:
        targetEvent = target["eventTime"]
        targetAvailable = target["availableAt"]
        eligible = [
            row
            for row in sourceRows
            if str(row["sourceEventTime"]) <= targetEvent and str(row["sourceAvailableAt"]) <= targetAvailable
        ]
        if maxStalenessDays is not None:
            eligible = [
                row
                for row in eligible
                if (_dateObject(targetEvent) - _dateObject(str(row["sourceEventTime"]))).days <= maxStalenessDays
            ]
        if not eligible:
            continue
        picked = sorted(eligible, key=lambda row: (str(row["sourceEventTime"]), str(row["sourceAvailableAt"])))[-1]
        out.append(
            {
                "eventTime": targetEvent,
                "availableAt": max(targetAvailable, str(picked["sourceAvailableAt"])),
                "sourceEventTime": str(picked["sourceEventTime"]),
                "sourceAvailableAt": str(picked["sourceAvailableAt"]),
                **{variableId: float(picked[variableId]) for variableId in variableIds},
            }
        )
    if not out:
        raise DriverTransformError("no carried rows available on target grid")
    return tuple(out)


def _sourceFlowPeriodRow(
    source: DriverHistorySource,
    *,
    periodEnd: str,
    knowledgeAsOf: str,
) -> dict[str, str | float]:
    rows = _sourceRows(source, knowledgeAsOf=knowledgeAsOf)
    matches = [row for row in rows if str(row["sourceEventTime"]) == periodEnd]
    if not matches:
        raise DriverTransformError("source flow period is not available by knowledgeAsOf")
    return sorted(matches, key=lambda row: str(row["sourceAvailableAt"]))[-1]


def carryForwardDriverHistorySource(
    source: DriverHistorySource,
    *,
    targetGrid: pl.DataFrame,
    targetFrequency: str,
    targetStepSpan: int,
    knowledgeAsOf: str,
    transformId: str,
    targetGridRef: str,
    sourceMeasureKind: str = "stateFeature",
    targetEventTimeColumn: str = "eventTime",
    targetAvailableAtColumn: str = "availableAt",
    targetTiming: str = "level",
    maxStalenessDays: int | None = None,
    cardId: str = "",
) -> DriverHistorySource:
    """Carry a lower-frequency source forward on an explicit target grid.

    Args:
        source: Historical driver source to align.
        targetGrid: DataFrame with target event and availability columns.
        targetFrequency: Frequency of the resulting source.
        targetStepSpan: Positive step span of the resulting source.
        knowledgeAsOf: Decision cutoff for both source and target rows.
        transformId: Stable transform identifier for the carry-forward rule.
        targetGridRef: Source reference for the target grid.
        sourceMeasureKind: Source measure semantics. Flow and cumulative flow
            measures are not executable carry-forward driver history.
        targetEventTimeColumn: Target grid event time column.
        targetAvailableAtColumn: Target grid availability column.
        targetTiming: Output timing. Carry-forward allows only ``level`` or ``rate``.
        maxStalenessDays: Optional maximum age from source event to target event.
        cardId: Optional output card id. Defaults to a derived id.

    Returns:
        ``DriverHistorySource`` on the target grid with source weakness preserved.

    Raises:
        DriverTransformError: If the transform would fabricate availability, rows, or shock timing.

    Example:
        ``weekly = carryForwardDriverHistorySource(filing, targetGrid=priceGrid, targetFrequency="week", targetStepSpan=1, knowledgeAsOf="20251231", transformId="filing-carry-forward-to-week-v1", targetGridRef="grid:price-weekly")``
    """

    if not targetFrequency or targetStepSpan < 1 or not transformId or not targetGridRef:
        raise DriverTransformError("carry-forward transform needs target contract, transformId, and targetGridRef")
    if targetTiming not in _FACTOR_TIMINGS:
        raise DriverTransformError("carry-forward cannot create shock timing")
    if maxStalenessDays is not None and maxStalenessDays < 1:
        raise DriverTransformError("maxStalenessDays must be positive when supplied")
    card = source.card
    if card.sourceKind != "history" or card.status != "active":
        raise DriverTransformError("carry-forward source must be an active history card")
    measureKind = _sourceMeasureKind(sourceMeasureKind, targetTiming=targetTiming)
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    targetRows = _validateTargetGrid(
        targetGrid,
        eventTimeColumn=targetEventTimeColumn,
        availableAtColumn=targetAvailableAtColumn,
        knowledgeAsOf=cutoff,
    )
    variableIds = tuple(factor.variableId for factor in card.factors)
    carried = _carriedRows(
        _sourceRows(source, knowledgeAsOf=cutoff),
        targetRows,
        variableIds=variableIds,
        maxStalenessDays=maxStalenessDays,
    )
    traceHash = canonicalPayloadHash(
        {
            "schemaVersion": "driver-carry-forward-trace-v1",
            "sourceCard": asdict(card),
            "targetFrequency": targetFrequency,
            "targetStepSpan": targetStepSpan,
            "knowledgeAsOf": cutoff,
            "transformId": transformId,
            "targetGridRef": targetGridRef,
            "sourceMeasureKind": measureKind,
            "targetTiming": targetTiming,
            "maxStalenessDays": maxStalenessDays,
            "rows": carried,
        }
    )
    factors = tuple(
        DriverFactorSpec(
            factor.variableId,
            factor.unit,
            targetFrequency,
            targetTiming,
            f"{factor.transformId}+{transformId}",
        )
        for factor in card.factors
    )
    sourceRefs = _dedupe(
        (
            *card.sourceRefs,
            "simulate.driverTransforms:carryForwardDriverHistorySource",
            f"sourceCard:{card.cardId}",
            f"sourceFrequency:{card.frequency}:{card.stepSpan}",
            f"targetFrequency:{targetFrequency}:{targetStepSpan}",
            f"targetGridRef:{targetGridRef}",
            f"sourceMeasureKind:{measureKind}",
            f"transformId:{transformId}",
            f"transformTrace:{traceHash}",
            *((f"maxStalenessDays:{maxStalenessDays}",) if maxStalenessDays is not None else ()),
        )
    )
    warnings = _dedupe(
        (
            *card.warnings,
            "driverCarryForwardTransform",
            f"carryForwardFrom:{card.frequency}:to:{targetFrequency}",
        )
    )
    outPanel = pl.DataFrame(carried).select("eventTime", "availableAt", *variableIds)
    outCard = DriverCard(
        cardId=cardId or f"{card.cardId}-{targetFrequency}-carry-forward",
        sourceKind="history",
        providerId=card.providerId,
        datasetId=card.datasetId,
        entityId=card.entityId,
        frequency=targetFrequency,
        stepSpan=targetStepSpan,
        factors=factors,
        historyStatus=card.historyStatus,
        sourceRefs=sourceRefs,
        status=card.status,
        warnings=warnings,
    )
    return DriverHistorySource(outCard, outPanel)


def flowMeasureExplicitAssumptionSource(
    source: DriverHistorySource,
    *,
    steps: tuple[Mapping[str, float], ...],
    targetFrequency: str,
    targetStepSpan: int,
    factors: tuple[DriverFactorSpec, ...],
    knowledgeAsOf: str,
    assumptionId: str,
    claim: str,
    falsifier: str,
    periodStart: str,
    periodEnd: str,
    periodScope: str,
    sourceMeasureKind: str,
    transformId: str,
    sourceRef: str,
    cardId: str = "",
) -> DriverAssumptionSource:
    """Bind a historical flow period to explicit future assumption steps.

    Args:
        source: Historical flow source used only as evidence and lineage.
        steps: Explicit future factor values supplied by the caller.
        targetFrequency: Frequency of the assumption path.
        targetStepSpan: Positive target step span.
        factors: Output factor contracts for the explicit assumption.
        knowledgeAsOf: Decision cutoff for the selected historical flow period.
        assumptionId: Stable assumption identifier.
        claim: Human-readable assumption claim.
        falsifier: Observable condition that can disprove the assumption.
        periodStart: Start date of the historical flow period used as evidence.
        periodEnd: End date of the historical flow period used as evidence.
        periodScope: Period scope such as ``quarter`` or ``ytd``.
        sourceMeasureKind: Flow measure kind. Non-flow state measures are rejected.
        transformId: Stable transform identifier for the evidence-to-assumption boundary.
        sourceRef: Caller-supplied assumption or decision reference.
        cardId: Optional output card id.

    Returns:
        ``DriverAssumptionSource`` whose values are explicit assumptions, not history.

    Raises:
        DriverTransformError: If source flow, period boundary, claim, or step contracts fail.

    Example:
        ``assumption = flowMeasureExplicitAssumptionSource(flow, steps=steps, targetFrequency="quarter", targetStepSpan=1, factors=factors, knowledgeAsOf="20251231", assumptionId="rev-demand", claim="Revenue weakness maps to demand.", falsifier="Orders do not decline.", periodStart="20250101", periodEnd="20250331", periodScope="quarter", sourceMeasureKind="flow", transformId="flow-to-demand-v1", sourceRef="assumption://rev-demand")``
    """

    if (
        not targetFrequency
        or targetStepSpan < 1
        or not assumptionId
        or not claim
        or not falsifier
        or not transformId
        or not sourceRef
    ):
        raise DriverTransformError("flow explicit assumption needs target contract, id, claim, falsifier, and refs")
    card = source.card
    if card.sourceKind != "history" or card.status != "active":
        raise DriverTransformError("flow explicit assumption source must be an active history card")
    measureKind = _flowSourceMeasureKind(sourceMeasureKind)
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    start, end, scope = _flowPeriod(periodStart=periodStart, periodEnd=periodEnd, periodScope=periodScope)
    variableIds = _validateAssumptionFactors(factors, targetFrequency=targetFrequency, label="flow explicit assumption")
    cleanSteps = _validateAssumptionSteps(steps, variableIds=variableIds, label="flow explicit assumption")
    sourceRow = _sourceFlowPeriodRow(source, periodEnd=end, knowledgeAsOf=cutoff)
    traceHash = canonicalPayloadHash(
        {
            "schemaVersion": "flow-explicit-assumption-trace-v1",
            "sourceCard": asdict(card),
            "sourceSelectedRow": sourceRow,
            "sourceMeasureKind": measureKind,
            "periodStart": start,
            "periodEnd": end,
            "periodScope": scope,
            "targetFrequency": targetFrequency,
            "targetStepSpan": targetStepSpan,
            "factors": factors,
            "steps": cleanSteps,
            "knowledgeAsOf": cutoff,
            "assumptionId": assumptionId,
            "claim": claim,
            "falsifier": falsifier,
            "transformId": transformId,
            "sourceRef": sourceRef,
        }
    )
    sourceRefs = _dedupe(
        (
            *card.sourceRefs,
            sourceRef,
            "simulate.driverTransforms:flowMeasureExplicitAssumptionSource",
            f"sourceFlowCard:{card.cardId}",
            f"sourceMeasureKind:{measureKind}",
            f"flowPeriodStart:{start}",
            f"flowPeriodEnd:{end}",
            f"flowPeriodScope:{scope}",
            f"sourceFlowAvailableAt:{sourceRow['sourceAvailableAt']}",
            f"targetFrequency:{targetFrequency}:{targetStepSpan}",
            f"assumptionId:{assumptionId}",
            f"transformId:{transformId}",
            f"transformTrace:{traceHash}",
        )
    )
    warnings = _dedupe(
        (
            *card.warnings,
            "flowMeasureExplicitAssumption",
            f"flowAssumptionFrom:{card.cardId}",
            f"sourceHistoryStatus:{card.historyStatus}",
        )
    )
    outCard = DriverCard(
        cardId=cardId or f"{card.cardId}-explicit-assumption",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="manual-flow-assumption",
        entityId=card.entityId,
        frequency=targetFrequency,
        stepSpan=targetStepSpan,
        factors=factors,
        historyStatus="explicitAssumption",
        sourceRefs=sourceRefs,
        status="active",
        assumptionId=assumptionId,
        claim=claim,
        falsifier=falsifier,
        warnings=warnings,
    )
    return DriverAssumptionSource(outCard, cleanSteps)
