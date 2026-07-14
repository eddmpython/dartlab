from __future__ import annotations

from dataclasses import replace

import polars as pl
import pytest

from dartlab.simulate.driverPaths import DriverCard, DriverFactorSpec, DriverHistorySource
from dartlab.simulate.driverRegistry import (
    DriverRegistryCandidate,
    DriverRegistryError,
    DriverRegistryLaneSpec,
    compileDriverRegistryPathSet,
    discoverDriverRegistryCandidates,
)
from dartlab.simulate.driverSources import (
    filingMetricDriverHistorySource,
    panelMetricDriverHistorySource,
    priceReturnDriverHistorySource,
)


def _filingSource() -> DriverHistorySource:
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


def _industryTimeSeriesSource() -> DriverHistorySource:
    factor = DriverFactorSpec(
        "industryOrderChange",
        "simpleReturn",
        "quarter",
        "change",
        "industry-order-change-quarterly-v1",
        sourceColumn="orderChange",
    )
    panel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930"],
            "availableAt": ["20200410", "20200710", "20201012"],
            "orderChange": [0.01, -0.03, 0.04],
        }
    )
    return panelMetricDriverHistorySource(
        panel,
        cardId="industry-order-change",
        providerId="industry",
        datasetId="industry.metric.quarterly",
        entityId="semiconductor",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        sourceRefs=("data/industry/metrics/semiconductor.parquet",),
        knowledgeAsOf="20201231",
    )


def testRegistryCompilesWorkbenchSourcesAndPreservesWeakLineage() -> None:
    result = compileDriverRegistryPathSet(
        (
            DriverRegistryCandidate(
                "filing-margin",
                "pathHistory",
                _filingSource(),
                semanticRefs=("semantics:financial-filing-change-path",),
                selectionReason="Quarterly filing metric transformed to ratio change.",
            ),
            DriverRegistryCandidate(
                "industry-orders",
                "pathHistory",
                _industryTimeSeriesSource(),
                semanticRefs=("semantics:industry-time-series-path",),
                selectionReason="Industry metric has real eventTime and availableAt.",
            ),
        ),
        registryId="kr-semiconductor-driver-registry",
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=17,
        minObservations=3,
    )
    assert result.audit.commonObservationCount == 3
    assert result.audit.sourceObservationCounts == (
        ("filing-margin", 3),
        ("industry-orders", 3),
    )
    assert result.pathSet.audit.validationStatus == "retrospectiveOnly"
    assert "driverRegistryContainsRevisedHistory" in result.audit.warnings
    assert "filingSourceNotExactAsKnown" in result.audit.warnings
    assert "dartRetainedFinanceRowsAreConditionalUntilRawFilingReceiptsExist" in result.audit.warnings
    assert all(step["operatingMarginChange"] != 9.99 for path in result.pathSet.paths for step in path.steps)


def testDiscoveryBuildsRegistryCandidatesFromLaneSpecs() -> None:
    specs = (
        DriverRegistryLaneSpec(
            "filing-margin",
            "pathHistory",
            "dart",
            "dart.finance.retained",
            "005930",
            ("operatingMarginChange",),
            semanticRefs=("semantics:financial-filing-change-path",),
            selectionReason="Quarterly filing metric transformed to ratio change.",
            requiredSourceRefs=("filingTrace:", "filingIdColumn:rceptNo"),
        ),
        DriverRegistryLaneSpec(
            "industry-orders",
            "pathHistory",
            "industry",
            "industry.metric.quarterly",
            "semiconductor",
            ("industryOrderChange",),
            semanticRefs=("semantics:industry-time-series-path",),
            selectionReason="Industry metric has real eventTime and availableAt.",
            requiredSourceRefs=("data/industry/metrics/semiconductor.parquet",),
        ),
    )
    candidates = discoverDriverRegistryCandidates(
        (_filingSource(), _industryTimeSeriesSource()),
        specs,
    )
    assert tuple(candidate.laneId for candidate in candidates) == ("filing-margin", "industry-orders")
    assert all(any(ref.startswith("driverDiscovery:") for ref in candidate.semanticRefs) for candidate in candidates)
    assert "sourceCard:dart-operating-margin-change" in candidates[0].semanticRefs

    result = compileDriverRegistryPathSet(
        candidates,
        registryId="discovered-kr-semiconductor-drivers",
        knowledgeAsOf="20201231",
        horizon=2,
        pathCount=2,
        blockLength=1,
        seed=17,
        minObservations=3,
    )
    assert result.audit.commonObservationCount == 3
    assert any(ref.startswith("driverDiscovery:") for ref in result.audit.semanticRefs)
    assert result.audit.laneIds == ("filing-margin", "industry-orders")


def testDiscoveryRejectsMissingAmbiguousAndUnprovenSourceRefs() -> None:
    source = _filingSource()
    missingSpec = DriverRegistryLaneSpec(
        "filing-margin",
        "pathHistory",
        "dart",
        "dart.finance.retained",
        "005930",
        ("operatingMarginChange",),
        semanticRefs=("semantics:financial-filing-change-path",),
        selectionReason="Quarterly filing metric transformed to ratio change.",
        requiredSourceRefs=("sourceReceiptRef:",),
    )
    with pytest.raises(DriverRegistryError, match="missing required sourceRefs"):
        discoverDriverRegistryCandidates((source,), (missingSpec,))

    ambiguousSource = DriverHistorySource(
        replace(source.card, cardId="dart-operating-margin-change-copy"), source.panel
    )
    ambiguousSpec = replace(missingSpec, requiredSourceRefs=("filingTrace:",))
    with pytest.raises(DriverRegistryError, match="ambiguous driver registry discovery"):
        discoverDriverRegistryCandidates((source, ambiguousSource), (ambiguousSpec,))

    missingLaneSpec = replace(ambiguousSpec, providerId="edgar")
    with pytest.raises(DriverRegistryError, match="missing source for lane"):
        discoverDriverRegistryCandidates((source,), (missingLaneSpec,))


def testRegistryRejectsSnapshotOrObservedFeatureAsPathHistory() -> None:
    with pytest.raises(DriverRegistryError, match="cannot be registered as driver path"):
        compileDriverRegistryPathSet(
            (
                DriverRegistryCandidate(
                    "industry-map",
                    "stateSnapshot",
                    _industryTimeSeriesSource(),
                    semanticRefs=("semantics:industry-classification-state",),
                    selectionReason="Latest industry map is a state dimension.",
                ),
            ),
            registryId="bad-registry",
            knowledgeAsOf="20201231",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
        )


def testRegistryRejectsSemanticLaunderingOfPriceMacroAndFinancialRatios() -> None:
    prices = pl.DataFrame(
        {
            "date": ["20200103", "20200110", "20200117", "20200124"],
            "code": ["005930", "005930", "005930", "005930"],
            "close": [100.0, 101.0, 102.0, 103.0],
        }
    )
    badPrice = priceReturnDriverHistorySource(
        prices,
        code="005930",
        knowledgeAsOf="20200124",
        sourceRefs=("data/gov/prices/date",),
        variableId="marketPriceChange",
        frequency="week",
    )
    with pytest.raises(DriverRegistryError, match="equity price history cannot be registered as operating shock"):
        compileDriverRegistryPathSet(
            (
                DriverRegistryCandidate(
                    "equity-price-as-product-price",
                    "pathHistory",
                    badPrice,
                    semanticRefs=("semantics:equity-return-risk-factor",),
                ),
            ),
            registryId="bad-price-registry",
            knowledgeAsOf="20200124",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
            minObservations=3,
        )

    macroLevelCard = DriverCard(
        cardId="macro-oil-level",
        sourceKind="history",
        providerId="macro",
        datasetId="macro.observations",
        entityId="KR",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("oilLevel", "indexLevel", "quarter", "level", "macro-oil-level-v1"),),
        historyStatus="revisedHistory",
        sourceRefs=("data/macro/oil",),
    )
    macroPanel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930"],
            "availableAt": ["20200401", "20200701", "20201001"],
            "oilLevel": [50.0, 55.0, 60.0],
        }
    )
    with pytest.raises(DriverRegistryError, match="macro level must be transformed"):
        compileDriverRegistryPathSet(
            (
                DriverRegistryCandidate(
                    "macro-level",
                    "pathHistory",
                    DriverHistorySource(macroLevelCard, macroPanel),
                    semanticRefs=("semantics:macro-level-state",),
                ),
            ),
            registryId="bad-macro-registry",
            knowledgeAsOf="20201231",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
            minObservations=3,
        )

    ratioLevelCard = DriverCard(
        cardId="dart-margin-level",
        sourceKind="history",
        providerId="dart",
        datasetId="dart.finance.retained",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(DriverFactorSpec("operatingMargin", "ratio", "quarter", "level", "dart-margin-level-v1"),),
        historyStatus="revisedHistory",
        sourceRefs=("data/dart/finance/005930.parquet",),
    )
    ratioPanel = pl.DataFrame(
        {
            "eventTime": ["20200331", "20200630", "20200930"],
            "availableAt": ["20200515", "20200814", "20201116"],
            "operatingMargin": [0.1, 0.12, 0.11],
        }
    )
    with pytest.raises(DriverRegistryError, match="financial ratio level must remain state"):
        compileDriverRegistryPathSet(
            (
                DriverRegistryCandidate(
                    "ratio-level",
                    "pathHistory",
                    DriverHistorySource(ratioLevelCard, ratioPanel),
                    semanticRefs=("semantics:financial-ratio-state",),
                ),
            ),
            registryId="bad-ratio-registry",
            knowledgeAsOf="20201231",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
            minObservations=3,
        )


def testRegistryRequiresSemanticRefsAndCommonSupport() -> None:
    with pytest.raises(DriverRegistryError, match="semanticRefs"):
        compileDriverRegistryPathSet(
            (DriverRegistryCandidate("filing-margin", "pathHistory", _filingSource()),),
            registryId="missing-semantics",
            knowledgeAsOf="20201231",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
            minObservations=3,
        )

    sparseIndustry = panelMetricDriverHistorySource(
        pl.DataFrame(
            {
                "eventTime": ["20201231"],
                "availableAt": ["20201231"],
                "orderChange": [0.01],
            }
        ),
        cardId="industry-order-change",
        providerId="industry",
        datasetId="industry.metric.quarterly",
        entityId="semiconductor",
        frequency="quarter",
        stepSpan=1,
        factors=(
            DriverFactorSpec(
                "industryOrderChange",
                "simpleReturn",
                "quarter",
                "change",
                "industry-order-change-quarterly-v1",
                sourceColumn="orderChange",
            ),
        ),
        sourceRefs=("data/industry/metrics/semiconductor.parquet",),
        knowledgeAsOf="20201231",
    )
    with pytest.raises(DriverRegistryError, match="common driver support below minObservations"):
        compileDriverRegistryPathSet(
            (
                DriverRegistryCandidate(
                    "filing-margin",
                    "pathHistory",
                    _filingSource(),
                    semanticRefs=("semantics:financial-filing-change-path",),
                ),
                DriverRegistryCandidate(
                    "industry-orders",
                    "pathHistory",
                    sparseIndustry,
                    semanticRefs=("semantics:industry-time-series-path",),
                ),
            ),
            registryId="sparse-registry",
            knowledgeAsOf="20201231",
            horizon=1,
            pathCount=1,
            blockLength=1,
            seed=1,
            minObservations=3,
        )
