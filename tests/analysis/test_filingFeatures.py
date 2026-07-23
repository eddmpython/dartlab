"""EDGAR owner feature envelope와 public Data Workbench 수직 슬라이스 tests."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, cast

import polars as pl
import pytest

import dartlab.analysis.financial.dataAssets as dataAssets
from dartlab.analysis.financial.filingFeatures import buildEdgarFinancialFeatureInput
from dartlab.data import DataQuery, DataResult, FactorProjection, TimeContext, data
from dartlab.data.featureQuery import featureObservationSetFromValue


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
    assert calls == [{"knownAt": "20250201", "subject": "AAPL"}]
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
