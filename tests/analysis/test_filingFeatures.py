"""EDGAR owner feature envelope와 public Data Workbench 수직 슬라이스 tests."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, cast

import polars as pl
import pytest

import dartlab.analysis.financial.dataAssets as dataAssets
from dartlab.analysis.financial.filingFeatures import buildEdgarFinancialFeatureInput
from dartlab.dataHub import DataQuery, DataResult, FactorProjection, TimeContext, data
from dartlab.dataHub.featureQuery import featureObservationSetFromValue


def _filing(accn: str, filed: str, fiscalEnd: str, *, scale: float = 1.0) -> pl.DataFrame:
    stock = {
        "CashAndCashEquivalentsAtCarryingValue": 10.0,
        "AccountsReceivableNetCurrent": 20.0,
        "InventoryNet": 5.0,
        "AccountsPayableCurrent": 15.0,
        "PropertyPlantAndEquipmentNet": 30.0,
        "Assets": 100.0,
        "Liabilities": 60.0,
        "StockholdersEquity": 40.0,
        "LongTermDebtCurrent": 8.0,
        "LongTermDebtNoncurrent": 12.0,
    }
    rows = [
        {
            "namespace": "us-gaap",
            "tag": tag,
            "unit": "USD",
            "val": value * scale,
            "form": "10-Q",
            "filed": filed,
            "start": None,
            "end": fiscalEnd,
            "accn": accn,
        }
        for tag, value in stock.items()
    ]
    end = date.fromisoformat(fiscalEnd)
    for lag in range(3, -1, -1):
        quarterEnd = end - timedelta(days=91 * lag)
        quarterStart = quarterEnd - timedelta(days=89)
        for tag, value in (
            ("RevenueFromContractWithCustomerExcludingAssessedTax", 100.0),
            ("OperatingIncomeLoss", 20.0),
        ):
            rows.append(
                {
                    "namespace": "us-gaap",
                    "tag": tag,
                    "unit": "USD",
                    "val": value * scale,
                    "form": "10-Q",
                    "filed": filed,
                    "start": quarterStart.isoformat(),
                    "end": quarterEnd.isoformat(),
                    "accn": accn,
                }
            )
    return pl.DataFrame(rows)


def testOwnerEnvelopeIsCutoffStableAndKeepsConditionalRetainedTruth() -> None:
    original = _filing("original", "2025-01-30", "2024-12-31")
    first = buildEdgarFinancialFeatureInput(original, entityId="US:AAPL", knownAt="20250201")
    laterCutoff = buildEdgarFinancialFeatureInput(original, entityId="US:AAPL", knownAt="20250202")

    assert first == laterCutoff
    dataset = featureObservationSetFromValue(first)
    assert dataset is not None
    assert len(dataset.observations) == 10
    assert {item.entityId for item in dataset.observations} == {"US:AAPL"}
    assert {item.availableAt for item in dataset.observations} == {"20250130"}
    assert {item.knowledgeAsOf for item in dataset.observations} == {"20250130"}
    assert {item.vintage.revisionPolicy for item in dataset.observations} == {"latestRetained"}
    assert {item.vintage.coverage for item in dataset.observations} == {"periodOnly"}


def testFlowOnlyMeasuresSucceedWithoutStockAndReturnOnlyRequestedFeatures() -> None:
    facts = _filing("flow", "2025-01-30", "2024-12-31").filter(pl.col("start").is_not_null())
    payload = buildEdgarFinancialFeatureInput(
        facts,
        entityId="US:FLOW",
        knownAt="20250201",
        measures=(
            "financial.revenue",
            "financial.operatingMargin",
        ),
    )

    dataset = featureObservationSetFromValue(payload)
    assert dataset is not None
    values = {item.signalId: item.value for item in dataset.observations}
    assert values == {
        "financial.revenue": 100.0,
        "financial.operatingMargin": 0.2,
    }
    assert {item.vintage.artifactKind for item in dataset.observations} == {"edgarCompiledFlowEvidence"}


def testRevenueOnlyDoesNotRequireOperatingProfitFacts() -> None:
    facts = _filing("revenue", "2025-01-30", "2024-12-31").filter(
        (pl.col("start").is_not_null()) & (pl.col("tag") == "RevenueFromContractWithCustomerExcludingAssessedTax")
    )

    payload = buildEdgarFinancialFeatureInput(
        facts,
        entityId="US:REVENUE",
        knownAt="20250201",
        measures=("financial.revenue",),
    )
    dataset = featureObservationSetFromValue(payload)

    assert dataset is not None
    assert len(dataset.observations) == 1
    assert dataset.observations[0].signalId == "financial.revenue"
    assert dataset.observations[0].value == 100.0
    with pytest.raises(ValueError, match="four common standalone"):
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:REVENUE",
            knownAt="20250201",
            measures=("financial.operatingMargin",),
        )


def testStockMeasureOrNoMeasureKeepsStrictFullStateContract() -> None:
    facts = _filing("flow", "2025-01-30", "2024-12-31").filter(pl.col("start").is_not_null())

    with pytest.raises(ValueError, match="no stock facts"):
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:FLOW",
            knownAt="20250201",
            measures=("financial.cash",),
        )
    with pytest.raises(ValueError, match="no stock facts"):
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:FLOW",
            knownAt="20250201",
        )


def testUnknownOrDuplicateMeasureFailsBeforeCompilation() -> None:
    facts = _filing("flow", "2025-01-30", "2024-12-31")

    with pytest.raises(ValueError, match="지원되지 않습니다"):
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:FLOW",
            knownAt="20250201",
            measures=("financial.unknown",),
        )
    with pytest.raises(ValueError, match="중복"):
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:FLOW",
            knownAt="20250201",
            measures=("financial.revenue", "financial.revenue"),
        )


def testFutureAmendmentDoesNotLeakAndLaterCutoffChangesStableRevision() -> None:
    original = _filing("original", "2025-01-30", "2024-12-31")
    amendment = _filing("amendment", "2025-03-15", "2024-12-31", scale=1.1)
    before = buildEdgarFinancialFeatureInput(original, entityId="US:AAPL", knownAt="20250201")
    withFuture = buildEdgarFinancialFeatureInput(
        pl.concat([original, amendment]),
        entityId="US:AAPL",
        knownAt="20250201",
    )
    after = buildEdgarFinancialFeatureInput(
        pl.concat([original, amendment]),
        entityId="US:AAPL",
        knownAt="20250401",
    )

    assert before == withFuture
    beforeDataset = featureObservationSetFromValue(before)
    afterDataset = featureObservationSetFromValue(after)
    assert beforeDataset is not None and afterDataset is not None
    beforeRevenue = next(item for item in beforeDataset.observations if item.signalId == "financial.revenue")
    afterRevenue = next(item for item in afterDataset.observations if item.signalId == "financial.revenue")
    assert beforeRevenue.value == 100.0
    assert afterRevenue.value == pytest.approx(110.0)
    assert beforeRevenue.revisionId != afterRevenue.revisionId


def testFlowOnlyCutoffExcludesFutureAmendmentAndChangesExactRevision() -> None:
    original = _filing("original", "2025-01-30", "2024-12-31")
    amendment = _filing("amendment", "2025-03-15", "2024-12-31", scale=1.1)
    facts = pl.concat((original, amendment))
    measures = (
        "financial.revenue",
        "financial.operatingMargin",
    )

    before = featureObservationSetFromValue(
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:AAPL",
            knownAt="20250201",
            measures=measures,
        )
    )
    after = featureObservationSetFromValue(
        buildEdgarFinancialFeatureInput(
            facts,
            entityId="US:AAPL",
            knownAt="20250401",
            measures=measures,
        )
    )

    assert before is not None and after is not None
    beforeRevenue = next(item for item in before.observations if item.signalId == "financial.revenue")
    afterRevenue = next(item for item in after.observations if item.signalId == "financial.revenue")
    assert beforeRevenue.value == 100.0
    assert afterRevenue.value == pytest.approx(110.0)
    assert beforeRevenue.availableAt == "20250130"
    assert afterRevenue.availableAt == "20250315"
    assert beforeRevenue.revisionId != afterRevenue.revisionId


def testResolvedCikPathSkipsCompanyResolution(monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab
    import dartlab.providers.edgar.finance.facts as factReader

    monkeypatch.setattr(
        dartlab,
        "Company",
        lambda _subject: pytest.fail("resolved universe CIK는 Company를 다시 해소하면 안 됩니다"),
    )
    monkeypatch.setattr(
        factReader,
        "readCompanyFactsLocal",
        lambda cik, **_kwargs: _filing(cik, "2025-01-30", "2024-12-31"),
    )

    payload = dataAssets.edgarFinancialFeatures(
        subject="US:AAPL",
        sourceEntityId="320193",
        knownAt="20250201",
    )

    dataset = featureObservationSetFromValue(payload)
    assert dataset is not None
    assert {item.entityId for item in dataset.observations} == {"US:AAPL"}


def testOnePublicQueryReturnsVerifiedConditionalPitFactor(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = buildEdgarFinancialFeatureInput(
        _filing("original", "2025-01-30", "2024-12-31"),
        entityId="US:AAPL",
        knownAt="20250201",
    )
    calls: list[dict[str, object]] = []

    def owner(**kwargs: object):
        calls.append(kwargs)
        return payload

    monkeypatch.setattr(dataAssets, "edgarFinancialFeatures", owner)
    result = cast(
        DataResult,
        cast(Any, data)(
            "query",
            query={
                "requests": [
                    {
                        "assetId": "analysis.edgarFinancialFeatures",
                        "requestId": "aaplPit",
                        "subjects": ["AAPL"],
                        "projection": {"kind": "factor", "measures": ["financial.revenue"]},
                        "time": {"knownAt": "20250201"},
                    }
                ]
            },
        ),
    )

    assert result.status == "partial"
    assert {gap.code for gap in result.gaps} == {"FEATURE_OBSERVATION_CONDITIONAL"}
    assert calls == [
        {
            "knownAt": "20250201",
            "measures": ("financial.revenue",),
            "subject": "AAPL",
        }
    ]
    assert result.dataSnapshotId is not None
    assert len(result.partitions) == 1
    row = result.partitions[0].data.to_dicts()[0]
    assert row["entityId"] == "US:AAPL"
    assert row["measureId"] == "financial.revenue"
    assert row["value"] == 100.0
    assert row["knownAt"] == "20250130"
    assert row["status"] == "conditional"
    assert row["revisionPolicy"] == "latestRetained"
    assert row["observationId"]
    assert row["featureVersionId"].startswith("feature-version:")


def testKnownAtIsRequiredBeforeOwnerExecution(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def owner(**_kwargs: object):
        nonlocal calls
        calls += 1
        return {}

    monkeypatch.setattr(dataAssets, "edgarFinancialFeatures", owner)
    result = cast(
        DataResult,
        data(
            "query",
            "analysis.edgarFinancialFeatures",
            query=DataQuery(subjects=("AAPL",), projection=FactorProjection()),
        ),
    )

    assert result.status == "failed"
    assert calls == 0
    assert [gap.code for gap in result.gaps] == ["FEATURE_KNOWN_AT_REQUIRED"]
