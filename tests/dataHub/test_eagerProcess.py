"""Eager result bundle codec와 engine code pin 회귀 tests."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import polars as pl
import pytest

import dartlab
from dartlab.dataHub.compositePaging import _encodeEagerResult
from dartlab.dataHub.continuation import ContinuationError, arrowSchemaDigest, canonicalDigest
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataPartition,
    DataResult,
)
from dartlab.dataHub.eagerProcess import (
    _EAGER_SCHEMA,
    _MAX_BUNDLE_BYTES,
    EagerSeal,
    _arrowPayload,
    eagerCodePin,
    eagerResultAt,
    packEagerSeal,
    unpackEagerSeal,
    validateEagerSeal,
)

_CONTRACT_HASH = "a" * 64
_PUBLIC_EAGER_ERRORS = (
    "OFFLINE_NETWORK_BLOCKED",
    "PAGEABLE_EAGER_CODE_PIN_FAILED",
    "PAGEABLE_EAGER_EXECUTOR_UNSUPPORTED",
    "PAGEABLE_EAGER_PROCESS_BUDGET",
    "PAGEABLE_EAGER_PROCESS_FAILED",
    "PAGEABLE_EAGER_SEAL_BUDGET",
    "PAGEABLE_EAGER_SEAL_RESULT_BUDGET",
    "PAGEABLE_EAGER_SEAL_ROW_BUDGET",
    "PAGEABLE_EAGER_SELECTOR_UNSUPPORTED",
    "PAGEABLE_EAGER_WRITE_BLOCKED",
)


def _engineFixture(*args, **kwargs):
    return {"args": args, "kwargs": kwargs}


def _descriptor(*, executorKind: str = "callable", sourceRef: str | None = None) -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId="analysis.eagerCodecFixture",
        assetVersionId="analysis.eagerCodecFixture:v1",
        owner="fixtureAxis" if executorKind == "engineAxis" else "tests.dataHub.test_eagerProcess",
        layer="L2",
        kind="computed",
        label="Eager codec fixture",
        description="Fixture-only eager bundle",
        sourceRef=sourceRef or "python:tests.dataHub.test_eagerProcess:_engineFixture",
        queryable=True,
        executorKind=executorKind,
        executorModule="tests.dataHub.test_eagerProcess" if executorKind == "callable" else None,
        executorAttribute="_engineFixture" if executorKind == "callable" else None,
    )


def _seal() -> tuple[EagerSeal, tuple[dict[str, str], ...], DataAssetDescriptor]:
    descriptor = _descriptor()
    selector = {"subject": "AAPL"}
    asset = AssetRef(descriptor.assetId, descriptor.assetVersionId)
    frame = pl.DataFrame({"entityId": ["AAPL"], "value": [1]})
    partition = DataPartition(
        asset=asset,
        projectionKind="native",
        data=frame,
        schema=tuple((name, str(dtype)) for name, dtype in frame.schema.items()),
        rowCount=1,
        truncated=False,
        selector=tuple(selector.items()),
        temporalStatus="LATEST_ONLY",
        lineageRefs=(descriptor.sourceRef,),
        requestId="fixture",
    )
    result = DataResult(
        status="ok",
        partitions=(partition,),
        assets=(asset,),
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        coverage=Coverage(1, 1, 1, 0),
        gaps=(),
        lineageRefs=(descriptor.sourceRef,),
        executionReceipts=(),
    )
    resultPayload = _encodeEagerResult(result, maxBytes=64 * 1024)
    bundle = _arrowPayload(
        __import__("pyarrow").Table.from_pylist(
            [
                {
                    "resultIndex": 0,
                    "selectorDigest": canonicalDigest(selector),
                    "resultPayload": resultPayload,
                    "resultDigest": hashlib.sha256(resultPayload).hexdigest(),
                }
            ],
            schema=_EAGER_SCHEMA,
        )
    )
    return (
        EagerSeal(
            bundle,
            hashlib.sha256(bundle).hexdigest(),
            len(bundle),
            1,
            arrowSchemaDigest(_EAGER_SCHEMA),
        ),
        (selector,),
        descriptor,
    )


def testSealPackRoundTripBindsArrowResultAndRequestIdentity() -> None:
    seal, selectors, descriptor = _seal()

    packed = packEagerSeal(seal)
    restored = unpackEagerSeal(packed, selectors=selectors)
    payload = eagerResultAt(packed, selectors=selectors, index=0)
    validated = validateEagerSeal(
        packed,
        selectors=selectors,
        descriptor=descriptor,
        requestId="fixture",
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
    )

    assert restored == seal
    assert validated == seal
    assert payload
    assert seal.byteCount <= _MAX_BUNDLE_BYTES == 192 * 1024


@pytest.mark.parametrize("code", _PUBLIC_EAGER_ERRORS)
def testPublicEagerErrorsRemainMachineReadable(code: str) -> None:
    error = ContinuationError(code)

    assert error.code == code
    assert code not in str(error)


def testSealTamperAndIdentityMismatchFailClosed() -> None:
    seal, selectors, descriptor = _seal()
    packed = packEagerSeal(seal)

    with pytest.raises(ContinuationError):
        unpackEagerSeal(dict(packed) | {"rawDigest": "0" * 64}, selectors=selectors)
    with pytest.raises(ContinuationError):
        unpackEagerSeal(packed, selectors=({"subject": "MSFT"},))
    with pytest.raises(ContinuationError):
        validateEagerSeal(
            packed,
            selectors=selectors,
            descriptor=descriptor,
            requestId="other",
            snapshotId="catalog:fixture",
            contractHash=_CONTRACT_HASH,
        )
    oversized = EagerSeal(
        b"x" * (_MAX_BUNDLE_BYTES + 1),
        hashlib.sha256(b"x" * (_MAX_BUNDLE_BYTES + 1)).hexdigest(),
        _MAX_BUNDLE_BYTES + 1,
        1,
        arrowSchemaDigest(_EAGER_SCHEMA),
    )
    with pytest.raises(ContinuationError):
        packEagerSeal(oversized)


def testEngineAxisPinIncludesDeclaredRegistryModulePayload(tmp_path, monkeypatch) -> None:
    moduleName = "tests.eager_engine_registry_fixture"
    modulePath = tmp_path / "eager_engine_registry_fixture.py"
    modulePath.write_text("REGISTRY = {'version': 1}\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location(moduleName, modulePath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[moduleName] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(dartlab, "fixtureAxis", _engineFixture, raising=False)
    descriptor = _descriptor(
        executorKind="engineAxis",
        sourceRef=f"python:{moduleName}:REGISTRY",
    )
    try:
        first = eagerCodePin(
            descriptor,
            requestedMeasures=("financial.revenue",),
        )
        modulePath.write_text("REGISTRY = {'version': 2}\n", encoding="utf-8")
        second = eagerCodePin(
            descriptor,
            requestedMeasures=("financial.revenue",),
        )
        margin = eagerCodePin(
            descriptor,
            requestedMeasures=("financial.operatingMargin",),
        )
    finally:
        sys.modules.pop(moduleName, None)

    assert first != second
    assert second != margin
    assert len(first) == len(second) == 64


def testCallablePinDriftsWhenRequestedMeasuresChange() -> None:
    descriptor = _descriptor()

    revenue = eagerCodePin(
        descriptor,
        requestedMeasures=("financial.revenue",),
    )
    margin = eagerCodePin(
        descriptor,
        requestedMeasures=("financial.operatingMargin",),
    )

    assert revenue != margin
