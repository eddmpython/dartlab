from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from dartlab.simulate.driverPaths import DriverFactorSpec, buildDriverPathSet
from dartlab.simulate.driverSources import (
    DriverSourceError,
    macroDriverHistorySource,
    panelMetricDriverHistorySource,
    priceReturnDriverHistorySource,
)


def _weeklyDates(n: int) -> list[str]:
    return [(date(2020, 1, 3) + timedelta(days=7 * index)).strftime("%Y%m%d") for index in range(n)]


def testPanelMetricDriverSourceFiltersByAvailabilityAndCarriesRefs() -> None:
    panel = pl.DataFrame(
        {
            "eventTime": ["20200101", "20200101", "20200401", "20200701", "20201001"],
            "availableAt": ["20200110", "20210110", "20200415", "20200715", "20201015"],
            "marginChange": [0.01, 9.99, -0.02, 0.03, 0.04],
        }
    )
    factor = DriverFactorSpec(
        "dartMarginChange",
        "ratioChange",
        "quarter",
        "change",
        "dart-margin-change-v1",
        sourceColumn="marginChange",
    )
    source = panelMetricDriverHistorySource(
        panel,
        cardId="dart-margin-change",
        providerId="dart",
        datasetId="finance.margin",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        sourceRefs=("data/dart/finance/005930.parquet", "column:marginChange"),
        knowledgeAsOf="20201231",
        warnings=("dartCurrentRetainedMayBeRevised",),
    )
    assert source.card.sourceRefs[:2] == ("data/dart/finance/005930.parquet", "column:marginChange")
    assert "knowledgeAsOf:20201231" in source.card.sourceRefs
    assert 9.99 not in source.panel["dartMarginChange"].to_list()

    pathSet = buildDriverPathSet(
        (source,),
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=4,
        minObservations=4,
    )
    assert pathSet.audit.historyStatus == "revisedHistory"
    assert "dartCurrentRetainedMayBeRevised" in pathSet.audit.warnings
    assert all(step["dartMarginChange"] != 9.99 for path in pathSet.paths for step in path.steps)


def testMacroDriverSourceKeepsReleaseVintageWarningAndFactorUnits() -> None:
    dates = _weeklyDates(8)
    macro = pl.DataFrame(
        {
            "date": dates,
            "oil": [100.0 * (1.01**index) for index in range(8)],
            "rate": [1.0 + 0.1 * index for index in range(8)],
        }
    )
    source = macroDriverHistorySource(
        macro,
        knowledgeAsOf="20201231",
        sourceRefs=("data/macro",),
        factorIds=("oil", "rate"),
    )
    units = {factor.variableId: factor.unit for factor in source.card.factors}
    assert units == {"oil": "simpleReturn", "rate": "percentagePointChange"}
    assert source.card.historyStatus == "revisedHistory"
    assert "macroReleaseVintageUnavailable" in source.card.warnings
    assert source.panel.height == 7


def testPriceReturnDriverSourceBuildsWeeklyEquityReturnsWithoutAsKnownLaundering() -> None:
    dates = _weeklyDates(7)
    prices = pl.DataFrame(
        {
            "date": dates + ["20240105"],
            "code": ["005930"] * 8,
            "close": [100.0, 110.0, 121.0, 108.9, 109.989, 111.08889, 112.1997789, 999.0],
        }
    )
    source = priceReturnDriverHistorySource(
        prices,
        code="005930",
        knowledgeAsOf=dates[6],
        sourceRefs=("data/gov/prices/date",),
    )
    assert source.card.factors[0].variableId == "equityReturnShock"
    assert source.card.historyStatus == "revisedHistory"
    assert "priceVintageUnavailable" in source.card.warnings
    assert source.panel["eventTime"].to_list() == dates[1:7]
    assert source.panel["equityReturnShock"].to_list()[:2] == pytest.approx([0.1, 0.1])
    assert 999.0 not in source.panel["equityReturnShock"].to_list()

    with pytest.raises(DriverSourceError, match="asKnown price history"):
        priceReturnDriverHistorySource(
            prices,
            code="005930",
            knowledgeAsOf=dates[6],
            sourceRefs=("data/gov/prices/date",),
            historyStatus="asKnown",
        )


def testPriceSourceRejectsDuplicateDatesWithoutAvailabilityColumn() -> None:
    prices = pl.DataFrame(
        {
            "date": ["20200103", "20200103", "20200110"],
            "code": ["005930", "005930", "005930"],
            "close": [100.0, 101.0, 102.0],
        }
    )
    with pytest.raises(DriverSourceError, match="duplicate price dates"):
        priceReturnDriverHistorySource(
            prices,
            code="005930",
            knowledgeAsOf="20201231",
            sourceRefs=("data/gov/prices/date",),
        )


def testStaticSnapshotCannotPretendToBeHistoryDriver() -> None:
    snapshot = pl.DataFrame({"code": ["005930"], "industry": ["semiconductor"], "momentum": [0.1]})
    factor = DriverFactorSpec("industryMomentum", "simpleReturn", "week", "innovation", "industry-mom-v1")
    with pytest.raises(DriverSourceError, match="missing columns"):
        panelMetricDriverHistorySource(
            snapshot,
            cardId="industry-snapshot",
            providerId="industry",
            datasetId="kindList",
            entityId="semiconductor",
            frequency="week",
            stepSpan=1,
            factors=(factor,),
            sourceRefs=("data/kindList/corpList.parquet",),
            knowledgeAsOf="20201231",
        )


def testMacroAndPriceDriverSourcesBuildOneJointPathSetOnlyOnCommonGrid() -> None:
    dates = _weeklyDates(8)
    macro = pl.DataFrame({"date": dates, "oil": [100.0 * (1.01**index) for index in range(8)]})
    prices = pl.DataFrame(
        {
            "date": dates,
            "code": ["005930"] * 8,
            "close": [100.0, 101.0, 99.0, 102.0, 103.0, 104.0, 106.0, 105.0],
        }
    )
    macroSource = macroDriverHistorySource(
        macro,
        knowledgeAsOf="20201231",
        sourceRefs=("data/macro",),
        factorIds=("oil",),
    )
    priceSource = priceReturnDriverHistorySource(
        prices,
        code="005930",
        knowledgeAsOf="20201231",
        sourceRefs=("data/gov/prices/date",),
    )
    pathSet = buildDriverPathSet(
        (macroSource, priceSource),
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=3,
        blockLength=1,
        seed=8,
        minObservations=6,
    )
    assert pathSet.audit.driverCardIds == ("macro-weekly-innovations", "equity-return-history")
    assert pathSet.audit.validationStatus == "retrospectiveOnly"
    assert {factor.variableId for factor in pathSet.factorSpecs} == {"oil", "equityReturnShock"}
