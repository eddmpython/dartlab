"""Adapt workbench lane dataframes into driver path source cards.

The functions in this module do not fetch data, admit paths, or infer causal
effects. They take already prepared workbench frames, preserve event and
availability timing, and create ``DriverHistorySource`` objects for
``driverPaths``. Static snapshots remain outside this module unless the caller
supplies a real time series with separate ``eventTime`` and ``availableAt``.
"""

from __future__ import annotations

import math

import polars as pl

from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.empiricalPaths import EmpiricalPathError
from dartlab.simulate.macroPaths import weeklyMacroInnovations

_FACTOR_TIMINGS = {"innovation", "change", "level", "rate"}
_HISTORY_STATUSES = {"asKnown", "revisedHistory"}


class DriverSourceError(ValueError):
    """Raised when a workbench lane cannot be represented as a safe driver source."""


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverSourceError(f"invalid {label}: {value}")
    return text


def _dateExpr(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8)


def _sourceColumn(factor: DriverFactorSpec) -> str:
    return factor.sourceColumn or factor.variableId


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _validateHistoryStatus(historyStatus: str, label: str) -> None:
    if historyStatus not in _HISTORY_STATUSES:
        raise DriverSourceError(f"invalid historyStatus for {label}: {historyStatus}")


def _validateFactorSpecs(factors: tuple[DriverFactorSpec, ...], *, frequency: str, label: str) -> None:
    if not factors:
        raise DriverSourceError(f"{label} needs at least one factor")
    variableIds = [factor.variableId for factor in factors]
    sourceColumns = [_sourceColumn(factor) for factor in factors]
    if len(set(variableIds)) != len(variableIds):
        raise DriverSourceError(f"{label} factor ids must be unique")
    if len(set(sourceColumns)) != len(sourceColumns):
        raise DriverSourceError(f"{label} source columns must be unique")
    for factor in factors:
        if (
            not factor.variableId
            or not factor.unit
            or factor.frequency != frequency
            or factor.timing not in _FACTOR_TIMINGS
            or not factor.transformId
        ):
            raise DriverSourceError(f"{label} factor contract is incomplete: {factor.variableId}")


def _validateSourceRefs(sourceRefs: tuple[str, ...], label: str) -> None:
    if not sourceRefs or any(not ref for ref in sourceRefs):
        raise DriverSourceError(f"{label} needs sourceRefs")


def _autoRefs(
    *,
    cardId: str,
    providerId: str,
    datasetId: str,
    entityId: str,
    knowledgeAsOf: str,
    frequency: str,
    stepSpan: int,
    factors: tuple[DriverFactorSpec, ...],
) -> tuple[str, ...]:
    return (
        f"driverSource:{cardId}",
        f"provider:{providerId}",
        f"dataset:{datasetId}",
        f"entity:{entityId}",
        f"knowledgeAsOf:{knowledgeAsOf}",
        f"frequency:{frequency}:{stepSpan}",
        *(
            f"factor:{factor.variableId}:{factor.unit}:{factor.timing}:{factor.transformId}:{_sourceColumn(factor)}"
            for factor in factors
        ),
    )


def _normalizeHistoryPanel(
    panel: pl.DataFrame,
    *,
    factors: tuple[DriverFactorSpec, ...],
    eventTimeColumn: str,
    availableAtColumn: str,
    knowledgeAsOf: str,
    label: str,
) -> pl.DataFrame:
    required = {eventTimeColumn, availableAtColumn, *(_sourceColumn(factor) for factor in factors)}
    if not required.issubset(panel.columns):
        raise DriverSourceError(f"{label} missing columns: {sorted(required - set(panel.columns))}")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    dated = panel.with_columns(
        _dateExpr(eventTimeColumn).alias("__event"),
        _dateExpr(availableAtColumn).alias("__available"),
    )
    malformed = dated.filter(
        (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise DriverSourceError(f"{label} contains malformed eventTime or availableAt")
    valueExprs = [
        pl.col(_sourceColumn(factor)).cast(pl.Float64, strict=False).alias(factor.variableId) for factor in factors
    ]
    variableIds = [factor.variableId for factor in factors]
    out = (
        dated.filter((pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .select(pl.col("__event").alias("eventTime"), pl.col("__available").alias("availableAt"), *valueExprs)
        .drop_nulls(variableIds)
        .sort(["eventTime", "availableAt"])
        .unique(subset=["eventTime"], keep="last", maintain_order=True)
    )
    if out.height == 0:
        raise DriverSourceError(f"{label} has no rows available by knowledgeAsOf")
    for variableId in variableIds:
        values = out[variableId].to_list()
        if any(not math.isfinite(float(value)) for value in values):
            raise DriverSourceError(f"{label} contains non-finite factor values: {variableId}")
    return out


def panelMetricDriverHistorySource(
    panel: pl.DataFrame,
    *,
    cardId: str,
    providerId: str,
    datasetId: str,
    entityId: str,
    frequency: str,
    stepSpan: int,
    factors: tuple[DriverFactorSpec, ...],
    sourceRefs: tuple[str, ...],
    knowledgeAsOf: str,
    eventTimeColumn: str = "eventTime",
    availableAtColumn: str = "availableAt",
    historyStatus: str = "revisedHistory",
    status: str = "active",
    warnings: tuple[str, ...] = (),
) -> DriverHistorySource:
    """Create a history driver source from a time-indexed workbench panel.

    Args:
        panel: DataFrame with event time, availability time, and factor columns.
        cardId: Stable driver card identifier.
        providerId: Source provider or workbench lane identifier.
        datasetId: Dataset or artifact identifier.
        entityId: Company, market, industry, or universe identifier.
        frequency: Step frequency shared with the eventual path set.
        stepSpan: Positive number of frequency units per step.
        factors: Driver factor contracts, including source columns when renamed.
        sourceRefs: Provider, artifact, and transform references.
        knowledgeAsOf: Decision cutoff. Rows newer than this are removed.
        eventTimeColumn: Column describing when the driver event occurred.
        availableAtColumn: Column describing when the row was usable.
        historyStatus: ``asKnown`` only when the lane has true PIT availability.
        status: Driver card status.
        warnings: Honest-gap labels carried into the path audit.

    Returns:
        ``DriverHistorySource`` with normalized ``eventTime`` and ``availableAt``.

    Raises:
        DriverSourceError: If timing, refs, factor contracts, or finite values fail.

    Example:
        ``source = panelMetricDriverHistorySource(panel, cardId="dart-margin", providerId="dart", datasetId="finance", entityId="005930", frequency="quarter", stepSpan=1, factors=factors, sourceRefs=("data/dart/finance",), knowledgeAsOf="20251231")``
    """

    if not cardId or not providerId or not datasetId or not entityId or not frequency or stepSpan < 1:
        raise DriverSourceError("driver source identifiers and step contract are required")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    factorTuple = tuple(factors)
    _validateHistoryStatus(historyStatus, cardId)
    _validateFactorSpecs(factorTuple, frequency=frequency, label=cardId)
    _validateSourceRefs(tuple(sourceRefs), cardId)
    normalized = _normalizeHistoryPanel(
        panel,
        factors=factorTuple,
        eventTimeColumn=eventTimeColumn,
        availableAtColumn=availableAtColumn,
        knowledgeAsOf=cutoff,
        label=cardId,
    )
    cardFactors = tuple(
        DriverFactorSpec(
            factor.variableId,
            factor.unit,
            factor.frequency,
            factor.timing,
            factor.transformId,
        )
        for factor in factorTuple
    )
    refs = _dedupe(
        (
            *tuple(sourceRefs),
            *_autoRefs(
                cardId=cardId,
                providerId=providerId,
                datasetId=datasetId,
                entityId=entityId,
                knowledgeAsOf=cutoff,
                frequency=frequency,
                stepSpan=stepSpan,
                factors=factorTuple,
            ),
            "simulate.driverSources:panelMetricDriverHistorySource",
        )
    )
    card = DriverCard(
        cardId=cardId,
        sourceKind="history",
        providerId=providerId,
        datasetId=datasetId,
        entityId=entityId,
        frequency=frequency,
        stepSpan=stepSpan,
        factors=cardFactors,
        historyStatus=historyStatus,
        sourceRefs=refs,
        status=status,
        warnings=tuple(warnings),
    )
    return DriverHistorySource(card, normalized)


def priceReturnDriverHistorySource(
    priceDaily: pl.DataFrame,
    *,
    code: str,
    knowledgeAsOf: str,
    sourceRefs: tuple[str, ...],
    cardId: str = "equity-return-history",
    providerId: str = "gov",
    datasetId: str = "gov.prices.daily",
    variableId: str = "equityReturnShock",
    dateColumn: str = "date",
    codeColumn: str = "code",
    closeColumn: str = "close",
    availableAtColumn: str = "",
    frequency: str = "week",
    stepSpan: int = 1,
    returnWindow: int = 1,
    historyStatus: str = "revisedHistory",
) -> DriverHistorySource:
    """Create an equity-return driver source from daily price observations.

    Args:
        priceDaily: Daily price frame with code, date, and close columns.
        code: Company or security code to filter.
        knowledgeAsOf: Decision cutoff. Later events and later availability are removed.
        sourceRefs: Provider, artifact, and query references.
        cardId: Stable driver card identifier.
        providerId: Provider identifier.
        datasetId: Dataset identifier.
        variableId: Output factor id. Defaults to an equity return, not a product price shock.
        dateColumn: Event date column.
        codeColumn: Security code column.
        closeColumn: Closing price column.
        availableAtColumn: Optional row availability column. Required for ``asKnown``.
        frequency: ``day`` or ``week`` output grid.
        stepSpan: Positive step span.
        returnWindow: Return window in output grid units.
        historyStatus: ``asKnown`` only when true row availability is supplied.

    Returns:
        ``DriverHistorySource`` carrying simple-return innovations.

    Raises:
        DriverSourceError: If price rows are ambiguous, non-positive, or not PIT-filterable.

    Example:
        ``source = priceReturnDriverHistorySource(prices, code="005930", knowledgeAsOf="20251231", sourceRefs=("data/gov/prices/date",))``
    """

    if not code or not variableId:
        raise DriverSourceError("price driver needs code and variableId")
    if frequency not in {"day", "week"} or stepSpan < 1 or returnWindow < 1:
        raise DriverSourceError("price driver step contract is invalid")
    if historyStatus == "asKnown" and not availableAtColumn:
        raise DriverSourceError("asKnown price history needs an explicit availableAt column")
    _validateHistoryStatus(historyStatus, cardId)
    _validateSourceRefs(tuple(sourceRefs), cardId)
    required = {dateColumn, codeColumn, closeColumn}
    if availableAtColumn:
        required.add(availableAtColumn)
    if not required.issubset(priceDaily.columns):
        raise DriverSourceError(f"{cardId} missing columns: {sorted(required - set(priceDaily.columns))}")
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    availableExpr = _dateExpr(availableAtColumn) if availableAtColumn else _dateExpr(dateColumn)
    base = (
        priceDaily.with_columns(
            _dateExpr(dateColumn).alias("__event"),
            availableExpr.alias("__available"),
            pl.col(closeColumn).cast(pl.Float64, strict=False).alias("__close"),
            pl.col(codeColumn).cast(pl.Utf8).alias("__code"),
        )
        .filter((pl.col("__code") == str(code)) & (pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .select("__event", "__available", "__close")
        .drop_nulls(["__event", "__available", "__close"])
        .sort(["__event", "__available"])
    )
    malformed = base.filter(
        (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise DriverSourceError(f"{cardId} contains malformed date values")
    if base.height == 0:
        raise DriverSourceError(f"{cardId} has no rows available by knowledgeAsOf")
    if not availableAtColumn and base.group_by("__event").len().filter(pl.col("len") > 1).height:
        raise DriverSourceError("duplicate price dates need an explicit availableAt column")
    if base.filter(pl.col("__close") <= 0).height:
        raise DriverSourceError("price driver requires positive close values")
    levels = base.unique(subset=["__event"], keep="last", maintain_order=True)
    if frequency == "week":
        levels = (
            levels.with_columns(pl.col("__event").str.to_date("%Y%m%d").alias("__date"))
            .with_columns((pl.col("__date").dt.iso_year() * 100 + pl.col("__date").dt.week()).alias("__week"))
            .group_by("__week")
            .agg(
                pl.col("__event").sort_by("__event").last().alias("eventTime"),
                pl.col("__available").sort_by("__event").last().alias("availableAt"),
                pl.col("__close").sort_by("__event").last().alias("__close"),
            )
            .sort("eventTime")
        )
    else:
        levels = levels.rename({"__event": "eventTime", "__available": "availableAt"}).sort("eventTime")
    returns = (
        levels.with_columns((pl.col("__close") / pl.col("__close").shift(returnWindow) - 1.0).alias(variableId))
        .select("eventTime", "availableAt", variableId)
        .drop_nulls(variableId)
    )
    if returns.height == 0:
        raise DriverSourceError("price driver has insufficient rows for returnWindow")
    factor = DriverFactorSpec(
        variableId,
        "simpleReturn",
        frequency,
        "innovation",
        f"price-simple-return-{frequency}-{returnWindow}-v1",
    )
    warnings = () if availableAtColumn else ("availableAtAssumedEqualToEventTime", "priceVintageUnavailable")
    return panelMetricDriverHistorySource(
        returns,
        cardId=cardId,
        providerId=providerId,
        datasetId=datasetId,
        entityId=str(code),
        frequency=frequency,
        stepSpan=stepSpan,
        factors=(factor,),
        sourceRefs=tuple(sourceRefs)
        + (
            "simulate.driverSources:priceReturnDriverHistorySource",
            f"priceCode:{code}",
            f"returnWindow:{returnWindow}",
        ),
        knowledgeAsOf=cutoff,
        historyStatus=historyStatus,
        warnings=warnings,
    )


def macroDriverHistorySource(
    macroDaily: pl.DataFrame,
    *,
    knowledgeAsOf: str,
    sourceRefs: tuple[str, ...],
    cardId: str = "macro-weekly-innovations",
    providerId: str = "macro",
    datasetId: str = "macro.observations",
    entityId: str = "KR",
    factorIds: tuple[str, ...] = (),
) -> DriverHistorySource:
    """Create a revised-history weekly macro innovation driver source.

    Args:
        macroDaily: Daily macro level panel accepted by ``weeklyMacroInnovations``.
        knowledgeAsOf: Decision cutoff for available macro observations.
        sourceRefs: Macro provider and artifact references.
        cardId: Stable driver card identifier.
        providerId: Provider identifier.
        datasetId: Dataset identifier.
        entityId: Market or region identifier.
        factorIds: Optional registered macro factor subset.

    Returns:
        ``DriverHistorySource`` on a weekly grid with innovation factor contracts.

    Raises:
        DriverSourceError: If the macro lane has no requested factors or safe rows.

    Example:
        ``source = macroDriverHistorySource(macro, knowledgeAsOf="20251231", sourceRefs=("data/macro",), factorIds=("oil",))``
    """

    _validateSourceRefs(tuple(sourceRefs), cardId)
    cutoff = _dateText(knowledgeAsOf, "knowledgeAsOf")
    try:
        panel, variables, warnings = weeklyMacroInnovations(macroDaily, knowledgeAsOf=cutoff)
    except EmpiricalPathError as error:
        raise DriverSourceError(str(error)) from error
    variableById = {variable.variableId: variable for variable in variables}
    requested = tuple(factorIds) if factorIds else tuple(variable.variableId for variable in variables)
    if not requested or set(requested) - set(variableById):
        raise DriverSourceError(f"macro driver requested unknown factors: {sorted(set(requested) - set(variableById))}")
    selectedPanel = panel.select("eventTime", "availableAt", *requested)
    factors = tuple(
        DriverFactorSpec(
            variableId,
            variableById[variableId].unit,
            "week",
            "innovation",
            f"macro-weekly-innovation-{variableId}-v1",
            sourceColumn=variableId,
        )
        for variableId in requested
    )
    return panelMetricDriverHistorySource(
        selectedPanel,
        cardId=cardId,
        providerId=providerId,
        datasetId=datasetId,
        entityId=entityId,
        frequency="week",
        stepSpan=1,
        factors=factors,
        sourceRefs=tuple(sourceRefs)
        + (
            "simulate.table:macroDaily",
            "simulate.macroPaths:weeklyMacroInnovations",
            "simulate.driverSources:macroDriverHistorySource",
        ),
        knowledgeAsOf=cutoff,
        historyStatus="revisedHistory",
        warnings=tuple(warnings),
    )
