"""resourceStream contracts의 strict JSON과 pin behavior mirror tests."""

from __future__ import annotations

import json
from datetime import date

import pytest

from dartlab.providers.resourceStream.contracts import (
    ResourceManifest,
    ResourcePredicate,
    ResourceReadReceipt,
    ResourceReadRequest,
    ResourceShard,
    canonicalJsonBytes,
)

pytestmark = pytest.mark.unit


def test_canonicalJsonBytes_isDeterministicAndStrict() -> None:
    assert canonicalJsonBytes({"b": 2, "a": [1, True]}) == canonicalJsonBytes({"a": [1, True], "b": 2})
    assert canonicalJsonBytes({"한글": "값"}).decode("utf-8") == '{"한글":"값"}'
    with pytest.raises(TypeError, match="직렬화"):
        canonicalJsonBytes({"date": date(2025, 1, 1)})
    with pytest.raises(TypeError, match="mapping key"):
        canonicalJsonBytes({1: "not-strict"})
    with pytest.raises(ValueError, match="non-finite"):
        canonicalJsonBytes({"ratio": float("nan")})


def test_fromMapping_roundTripsRequestAndRejectsMalformedPredicate() -> None:
    original = ResourceReadRequest(
        columns=("companyId", "value"),
        predicates=(ResourcePredicate("fy", "isin", (2024, 2025)),),
        companyIds=("B", "A"),
        batchRows=64,
        maxRows=700,
        maxBytes=4_096,
        includeSourcePath=False,
    )
    decoded = json.loads(original.toBytes())
    restored = ResourceReadRequest.fromMapping(decoded)
    assert restored == original
    with pytest.raises(TypeError, match="predicate item"):
        ResourceReadRequest.fromMapping({"columns": ["value"], "predicates": ["fy > 2024"]})
    with pytest.raises(TypeError, match="bool"):
        ResourceReadRequest.fromMapping({"columns": ["value"], "includeSourcePath": "false"})
    with pytest.raises(TypeError, match="column과 operator"):
        ResourcePredicate.fromMapping({"column": date(2025, 1, 1), "operator": "eq", "value": 1})


def test_queryPin_excludesPagingBudgetsButPinsSemantics() -> None:
    first = ResourceReadRequest(
        columns=("companyId", "value"),
        predicates=(ResourcePredicate("meta", "eq", {"b": 2, "a": 1}),),
        companyIds=("B", "A"),
        batchRows=32,
        maxRows=100,
        maxBytes=2_000,
    )
    sourcePin = "resource-source-full:abc"
    firstPin = first.queryPin("resource.test")
    resumed = ResourceReadRequest(
        columns=first.columns,
        predicates=(ResourcePredicate("meta", "eq", {"a": 1, "b": 2}),),
        companyIds=("A", "B"),
        batchRows=8,
        maxRows=10,
        maxBytes=500,
        startRow=100,
        expectedSourcePin=sourcePin,
        expectedQueryPin=firstPin,
    )
    assert resumed.queryPin("resource.test") == firstPin
    changed = ResourceReadRequest(columns=("value", "companyId"))
    assert changed.queryPin("resource.test") != firstPin


def test_toMapping_excludesAbsoluteExecutionRoot() -> None:
    manifest = ResourceManifest(
        resourceId="resource.test",
        rootPath="C:/private/resource",
        shards=(ResourceShard("A", "A.parquet", 20, 10, "digest"),),
        schemaFields=(("value", "int64"),),
        totalBytes=20,
        integrityMode="full",
        sourcePin="resource-source-full:abc",
    )
    mapping = manifest.toMapping()
    assert "rootPath" not in mapping
    assert mapping["cacheValidation"] == "fileSet+size+mtimeNs+cacheDocumentSha256"
    assert ResourcePredicate("fy", "ge", 2024).toMapping() == {
        "column": "fy",
        "operator": "ge",
        "value": 2024,
    }


def test_toBytes_areStrictJsonForExternalProcess() -> None:
    receipt = ResourceReadReceipt(
        sourcePin="resource-source-full:abc",
        queryPin="resource-query:def",
        integrityMode="full",
        startRow=0,
        nextRow=2,
        batchCount=1,
        rowCount=2,
        byteCount=64,
        truncated=True,
    )
    assert json.loads(receipt.toBytes())["nextRow"] == 2
    assert json.loads(ResourceReadRequest(("value",)).toBytes())["columns"] == ["value"]
