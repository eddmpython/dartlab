from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from dartlab.simulate.driverPaths import DriverFactorSpec
from dartlab.simulate.driverRegistry import DriverRegistryCandidate, compileDriverRegistryPathSet
from dartlab.simulate.driverSources import filingMetricDriverHistorySource, priceReturnDriverHistorySource
from dartlab.simulate.driverTransforms import DriverTransformError, carryForwardDriverHistorySource


def _weeklyDates(n: int) -> list[str]:
    return [(date(2020, 5, 8) + timedelta(days=7 * index)).strftime("%Y%m%d") for index in range(n)]


def _filingSource():
    factor = DriverFactorSpec(
        "operatingMarginChange",
        "ratioChange",
        "quarter",
        "change",
        "dart-operating-margin-change-v1",
        sourceColumn="opMarginChange",
    )
    panel = pl.DataFrame(
        {
            "code": ["005930", "005930", "005930", "005930"],
            "period": ["20200331", "20200331", "20200630", "20200930"],
            "rceptDate": ["20200515", "20210517", "20200814", "20201116"],
            "rceptNo": ["202005150001", "202105170009", "202008140001", "202011160001"],
            "opMarginChange": [0.02, 9.99, -0.01, 0.03],
        }
    )
    return filingMetricDriverHistorySource(
        panel,
        cardId="dart-operating-margin-change",
        providerId="dart",
        datasetId="dart.finance.retained",
        entityId="005930",
        entityIdColumn="code",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        sourceRefs=("data/dart/finance/005930.parquet", "transform:operating-margin-change"),
        knowledgeAsOf="20201231",
        eventTimeColumn="period",
        availableAtColumn="rceptDate",
        filingIdColumn="rceptNo",
    )


def testCarryForwardUsesTargetRowAvailabilityNotGlobalCutoff() -> None:
    grid = pl.DataFrame({"eventTime": _weeklyDates(15), "availableAt": _weeklyDates(15)})
    source = carryForwardDriverHistorySource(
        _filingSource(),
        targetGrid=grid,
        targetFrequency="week",
        targetStepSpan=1,
        knowledgeAsOf="20201231",
        transformId="filing-carry-forward-to-week-v1",
        targetGridRef="grid:weekly-price-close",
    )
    assert source.card.frequency == "week"
    assert source.card.factors[0].timing == "level"
    assert source.card.factors[0].transformId.endswith("filing-carry-forward-to-week-v1")
    assert source.panel["eventTime"].to_list()[0] == "20200515"
    assert "20200508" not in source.panel["eventTime"].to_list()
    beforeSecondFiling = source.panel.filter(pl.col("eventTime") < "20200814")["operatingMarginChange"].to_list()
    assert len(beforeSecondFiling) == 13
    assert set(beforeSecondFiling) == {0.02}
    assert source.panel.filter(pl.col("eventTime") >= "20200814")["operatingMarginChange"].to_list() == [-0.01]
    assert "filingSourceNotExactAsKnown" in source.card.warnings
    assert any(ref.startswith("transformTrace:") for ref in source.card.sourceRefs)


def testCarryForwardGridCanJoinWeeklyPriceWithoutImplicitResample() -> None:
    dates = _weeklyDates(15)
    prices = pl.DataFrame(
        {
            "date": dates,
            "code": ["005930"] * len(dates),
            "close": [100.0 + float(index) for index in range(len(dates))],
        }
    )
    priceSource = priceReturnDriverHistorySource(
        prices,
        code="005930",
        knowledgeAsOf="20201231",
        sourceRefs=("data/gov/prices/date",),
    )
    filingWeekly = carryForwardDriverHistorySource(
        _filingSource(),
        targetGrid=priceSource.panel.select("eventTime", "availableAt"),
        targetFrequency="week",
        targetStepSpan=1,
        knowledgeAsOf="20201231",
        transformId="filing-carry-forward-to-week-v1",
        targetGridRef="grid:price-weekly-return",
    )
    result = compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "filing-margin-weekly",
                "pathHistory",
                filingWeekly,
                semanticRefs=("semantics:filing-carry-forward-state-feature",),
            ),
            DriverRegistryCandidate(
                "equity-return",
                "pathHistory",
                priceSource,
                semanticRefs=("semantics:equity-return-risk-factor",),
            ),
        ),
        registryId="weekly-driver-registry",
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=19,
        minObservations=8,
    )
    assert result.audit.commonObservationCount == 14
    assert result.pathSet.audit.frequency == "week"
    assert {factor.frequency for factor in result.pathSet.factorSpecs} == {"week"}
    assert "driverCarryForwardTransform" in result.audit.warnings


def testCarryForwardRejectsAmbiguousGridAndStaleRows() -> None:
    with pytest.raises(DriverTransformError, match="target grid missing columns"):
        carryForwardDriverHistorySource(
            _filingSource(),
            targetGrid=pl.DataFrame({"eventTime": ["20200515"]}),
            targetFrequency="week",
            targetStepSpan=1,
            knowledgeAsOf="20201231",
            transformId="filing-carry-forward-to-week-v1",
            targetGridRef="grid:bad",
        )

    with pytest.raises(DriverTransformError, match="duplicate target eventTime"):
        carryForwardDriverHistorySource(
            _filingSource(),
            targetGrid=pl.DataFrame(
                {
                    "eventTime": ["20200515", "20200515"],
                    "availableAt": ["20200515", "20200515"],
                }
            ),
            targetFrequency="week",
            targetStepSpan=1,
            knowledgeAsOf="20201231",
            transformId="filing-carry-forward-to-week-v1",
            targetGridRef="grid:bad",
        )

    with pytest.raises(DriverTransformError, match="no carried rows available"):
        carryForwardDriverHistorySource(
            _filingSource(),
            targetGrid=pl.DataFrame(
                {
                    "eventTime": ["20201231"],
                    "availableAt": ["20201231"],
                }
            ),
            targetFrequency="week",
            targetStepSpan=1,
            knowledgeAsOf="20201231",
            transformId="filing-carry-forward-to-week-v1",
            targetGridRef="grid:stale",
            maxStalenessDays=30,
        )


def testCarryForwardRejectsFlowMeasuresAsExecutableDriverHistory() -> None:
    grid = pl.DataFrame({"eventTime": _weeklyDates(15), "availableAt": _weeklyDates(15)})
    for sourceMeasureKind in ("flow", "periodFlow", "cumulativeFlow"):
        with pytest.raises(DriverTransformError, match="flow measures cannot be carry-forwarded"):
            carryForwardDriverHistorySource(
                _filingSource(),
                targetGrid=grid,
                targetFrequency="week",
                targetStepSpan=1,
                knowledgeAsOf="20201231",
                transformId="filing-carry-forward-to-week-v1",
                targetGridRef="grid:weekly-price-close",
                sourceMeasureKind=sourceMeasureKind,
            )


def testCarryForwardBindsSourceMeasureKindInRefsAndTrace() -> None:
    grid = pl.DataFrame({"eventTime": _weeklyDates(15), "availableAt": _weeklyDates(15)})
    ratio = carryForwardDriverHistorySource(
        _filingSource(),
        targetGrid=grid,
        targetFrequency="week",
        targetStepSpan=1,
        knowledgeAsOf="20201231",
        transformId="filing-carry-forward-to-week-v1",
        targetGridRef="grid:weekly-price-close",
        sourceMeasureKind="ratio",
    )
    state = carryForwardDriverHistorySource(
        _filingSource(),
        targetGrid=grid,
        targetFrequency="week",
        targetStepSpan=1,
        knowledgeAsOf="20201231",
        transformId="filing-carry-forward-to-week-v1",
        targetGridRef="grid:weekly-price-close",
        sourceMeasureKind="stateFeature",
    )
    ratioTrace = next(ref for ref in ratio.card.sourceRefs if ref.startswith("transformTrace:"))
    stateTrace = next(ref for ref in state.card.sourceRefs if ref.startswith("transformTrace:"))
    assert "sourceMeasureKind:ratio" in ratio.card.sourceRefs
    assert "sourceMeasureKind:stateFeature" in state.card.sourceRefs
    assert ratioTrace != stateTrace
