"""Tests for the retrospective macro path adapter."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from dartlab.simulate import table
from dartlab.simulate.macroPaths import buildHistoricalMacroPaths, weeklyMacroInnovations


def _weeklyLevels(n: int = 12) -> pl.DataFrame:
    dates = [(date(2020, 1, 3) + timedelta(days=7 * i)).strftime("%Y%m%d") for i in range(n)]
    return pl.DataFrame(
        {
            "date": dates,
            "oil": [100.0 * (1.01**i) for i in range(n)],
            "rate": [1.0 + 0.1 * i for i in range(n)],
        }
    )


def testWeeklyMacroInnovationsExposeUnitsAndAvailabilityAssumption() -> None:
    panel, variables, warnings = weeklyMacroInnovations(_weeklyLevels(), knowledgeAsOf="20201231")
    units = {variable.variableId: variable.unit for variable in variables}
    assert units == {"rate": "percentagePointChange", "oil": "simpleReturn"}
    assert panel.height == 11
    assert panel["eventTime"].to_list() == panel["availableAt"].to_list()
    assert panel["oil"].to_list() == pytest.approx([0.01] * 11)
    assert panel["rate"].to_list() == pytest.approx([0.1] * 11)
    assert "macroReleaseVintageUnavailable" in warnings


def testHistoricalMacroPathsRemainRetrospectiveAndUseWeeklyGrid() -> None:
    result = buildHistoricalMacroPaths(
        _weeklyLevels(),
        knowledgeAsOf="20201231",
        horizonWeeks=4,
        pathCount=5,
        blockLengthWeeks=2,
        seed=3,
        minObservations=8,
    )
    assert result.audit.frequency == "week"
    assert result.audit.validationStatus == "retrospectiveOnly"
    assert result.audit.weightLabel == "empiricalResamplingMeasure"
    assert "availableAtAssumedEqualToEventTime" in result.audit.warnings
    assert {path.frequency for path in result.paths} == {"week"}
    assert {path.weightKind for path in result.paths} == {"resampled"}


def testRealMacroStoreBuildsAuditedPathsWhenInstalled() -> None:
    macro = table.macroDaily()
    if macro.height < 100:
        pytest.skip("macro store is not installed")
    asOf = str(macro["date"].max())
    result = buildHistoricalMacroPaths(
        macro,
        knowledgeAsOf=asOf,
        horizonWeeks=4,
        pathCount=4,
        blockLengthWeeks=2,
        seed=11,
        minObservations=52,
    )
    assert result.audit.observationCount >= 52
    assert result.audit.eventEnd <= asOf
    assert len(result.paths) == 4
    assert result.audit.certificateId == ""
