"""Data Workbench result identity가 실제 반환값에 결박되는지 검증한다."""

from __future__ import annotations

import polars as pl
import pyarrow as pa

from dartlab.data.contentSeal import contentHash
from dartlab.data.contracts import (
    DataAssetDescriptor,
    DataQuery,
    FactorProjection,
    TimeContext,
)
from dartlab.data.execution import _temporalGap


def _factorQuery() -> dict:
    return {
        "projection": {
            "kind": "factor",
            "measures": ["roe"],
            "unit": "percent",
            "frequency": "Y",
        }
    }


def testFactorResultIdentityBindsReturnedValues(monkeypatch) -> None:
    import dartlab

    current = {"value": 12.0}

    def scan(*args, **kwargs):
        return pl.DataFrame(
            {
                "종목코드": ["005930"],
                "종목명": ["삼성전자"],
                "2025": [current["value"]],
            }
        )

    monkeypatch.setattr(dartlab, "scan", scan)

    first = dartlab.data("query", "scan.ratio", query=_factorQuery())
    repeated = dartlab.data("query", "scan.ratio", query=_factorQuery())
    current["value"] = 13.0
    changed = dartlab.data("query", "scan.ratio", query=_factorQuery())

    firstPartition = first.partitions[0]
    changedPartition = changed.partitions[0]
    assert first.dataSnapshotId is not None
    assert first.dataSnapshotId.startswith("data-content-snapshot:")
    assert first.dataSnapshotId == repeated.dataSnapshotId
    assert firstPartition.contentHash == repeated.partitions[0].contentHash
    assert first.executionReceipts == repeated.executionReceipts
    assert first.snapshotId == changed.snapshotId
    assert first.contractHash == changed.contractHash
    assert first.dataSnapshotId != changed.dataSnapshotId
    assert firstPartition.contentHash != changedPartition.contentHash
    assert first.executionReceipts != changed.executionReceipts
    assert firstPartition.lineage is not None
    assert first.executionReceipts == (firstPartition.lineage.runId,)
    assert firstPartition.data["evidenceRef"].unique().to_list() == list(first.executionReceipts)
    assertion = next(row for row in firstPartition.qualityAssertions if row.assertionId == "contentSealed")
    assert assertion.success is True
    assert assertion.observed == firstPartition.contentHash


def testContentHashNormalizesMappingOrderAndArrowChunks() -> None:
    assert contentHash({"a": 1, "b": [2, 3]}) == contentHash({"b": [2, 3], "a": 1})

    first = pa.table({"entity": ["KR:005930", "US:AAPL"], "value": [1.0, 2.0]})
    chunked = pa.concat_tables([first.slice(0, 1), first.slice(1, 1)])
    assert len(chunked.column("entity").chunks) == 2
    assert contentHash(first) == contentHash(chunked)


def testOpaqueNativeResultFailsClosedWithoutFakeContentSnapshot(monkeypatch) -> None:
    import dartlab

    class Opaque:
        def __repr__(self) -> str:
            return "Opaque()"

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: Opaque())
    result = dartlab.data("query", "scan.governance", query={"projection": {"kind": "native"}})

    assert result.status == "ok"
    assert result.partitions[0].contentHash is None
    assert result.dataSnapshotId is None
    assertion = next(row for row in result.partitions[0].qualityAssertions if row.assertionId == "contentSealed")
    assert assertion.success is False
    assert assertion.severity == "warning"


def testCanonicalFactorPitRequiresObservedRowTiming() -> None:
    descriptor = DataAssetDescriptor(
        assetId="test.pitFactor",
        assetVersionId="asset:" + "a" * 64,
        owner="test",
        layer="L2",
        kind="factor",
        label="PIT factor",
        description="PIT factor",
        sourceRef="test:source",
        queryable=True,
        temporalSupport=("latest", "knownAt"),
        executorKind="callable",
        executionMode="ownerBulk",
    )
    query = DataQuery(
        projection=FactorProjection(unit="percent"),
        time=TimeContext(knownAt="2025-03-31"),
    )

    gap = _temporalGap(descriptor, query)

    assert gap is not None
    assert gap.code == "OBSERVATION_PIT_METADATA_REQUIRED"
