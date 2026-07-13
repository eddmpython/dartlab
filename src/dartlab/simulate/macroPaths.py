"""Adapt observed macro levels into retrospective weekly joint world paths."""

from __future__ import annotations

from dataclasses import replace

import polars as pl

from dartlab.simulate.empiricalPaths import (
    EmpiricalPathError,
    EmpiricalPathSet,
    PathVariable,
    buildJointBlockPaths,
)
from dartlab.simulate.factors import macroFactors


def weeklyMacroInnovations(
    macroDaily: pl.DataFrame,
    *,
    knowledgeAsOf: str,
) -> tuple[pl.DataFrame, tuple[PathVariable, ...], tuple[str, ...]]:
    """Convert factor levels known by a cutoff into native weekly innovations.

    The current macro store has observation dates but no separate release
    vintage. ``availableAt`` therefore equals the observation date and the
    output must remain retrospective revised history.
    """

    if "date" not in macroDaily.columns:
        raise EmpiricalPathError("macro panel needs a date column")
    cutoff = str(knowledgeAsOf).replace("-", "")[:8]
    specs = tuple(factor for factor in macroFactors() if factor.factor in macroDaily.columns)
    if not specs:
        raise EmpiricalPathError("macro panel has no registered factors")
    levels = (
        macroDaily.with_columns(pl.col("date").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("date"))
        .filter(pl.col("date") <= cutoff)
        .sort("date")
        .select("date", *(pl.col(factor.factor).cast(pl.Float64, strict=False) for factor in specs))
        .with_columns(*(pl.col(factor.factor).forward_fill().alias(factor.factor) for factor in specs))
        .with_columns(
            pl.col("date").str.to_date("%Y%m%d").alias("__date"),
        )
        .with_columns((pl.col("__date").dt.iso_year() * 100 + pl.col("__date").dt.week()).alias("__week"))
    )
    weekly = (
        levels.group_by("__week")
        .agg(
            pl.col("date").sort_by("date").last().alias("eventTime"),
            *(pl.col(factor.factor).sort_by("date").last().alias(factor.factor) for factor in specs),
        )
        .sort("eventTime")
    )
    changes = []
    variables: list[PathVariable] = []
    for factor in specs:
        if factor.kind == "level":
            changes.append((pl.col(factor.factor) - pl.col(factor.factor).shift(1)).alias(factor.factor))
            unit = "percentagePointChange"
        else:
            changes.append((pl.col(factor.factor) / pl.col(factor.factor).shift(1) - 1).alias(factor.factor))
            unit = "simpleReturn"
        variables.append(PathVariable(factor.factor, factor.factor, unit))
    panel = (
        weekly.with_columns(*changes)
        .with_columns(pl.col("eventTime").alias("availableAt"))
        .select("eventTime", "availableAt", *(factor.factor for factor in specs))
        .drop_nulls([factor.factor for factor in specs])
    )
    warnings = (
        "historyStatus:revisedHistory",
        "availableAtAssumedEqualToEventTime",
        "macroReleaseVintageUnavailable",
    )
    return panel, tuple(variables), warnings


def buildHistoricalMacroPaths(
    macroDaily: pl.DataFrame,
    *,
    knowledgeAsOf: str,
    horizonWeeks: int,
    pathCount: int,
    blockLengthWeeks: int,
    seed: int,
    minObservations: int = 52,
    refs: tuple[str, ...] = (),
) -> EmpiricalPathSet:
    """Build unadmitted weekly macro resamples from revised observed history."""

    panel, variables, warnings = weeklyMacroInnovations(macroDaily, knowledgeAsOf=knowledgeAsOf)
    result = buildJointBlockPaths(
        panel,
        variables,
        knowledgeAsOf=knowledgeAsOf,
        frequency="week",
        horizon=horizonWeeks,
        pathCount=pathCount,
        blockLength=blockLengthWeeks,
        seed=seed,
        historyStatus="revisedHistory",
        minObservations=minObservations,
        refs=tuple(refs) + ("simulate.table:macroDaily", "simulate.macroPaths:weeklyMacroInnovations"),
    )
    audit = replace(result.audit, warnings=tuple(dict.fromkeys(result.audit.warnings + warnings)))
    return EmpiricalPathSet(result.paths, audit)
