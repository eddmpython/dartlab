"""Eager child supervisor의 spawn, deadline, artifact 회수 tests."""

from __future__ import annotations

import multiprocessing
import os
import time

import pytest

from dartlab.dataHub.compositePaging import _decodeEagerResult
from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.contracts import (
    DataAssetDescriptor,
    DataQuery,
    FactorProjection,
    QueryBudget,
)
from dartlab.dataHub.isolation.eagerProcess import (
    eagerCodePin,
    eagerResultAt,
    packEagerSeal,
    validateEagerSeal,
)
from dartlab.dataHub.isolation.eagerSupervisor import runEagerSeal
from dartlab.dataHub.pagingRuntime import (
    MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES,
    ownerProcessArtifactRoot,
)

_CONTRACT_HASH = "b" * 64


def _fixtureFrame(*, subject: str):
    return {
        "subject": subject,
        "noRefresh": os.environ.get("DARTLAB_NO_REFRESH"),
        "hfOffline": os.environ.get("HF_HUB_OFFLINE"),
    }


def _fixtureHang(*, subject: str):
    del subject
    while True:
        time.sleep(1)


def _descriptor(attribute: str = "_fixtureFrame") -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId="analysis.eagerSupervisorFixture",
        assetVersionId="analysis.eagerSupervisorFixture:v1",
        owner="tests.dataHub.test_eagerSupervisor",
        layer="L2",
        kind="computed",
        label="Eager supervisor fixture",
        description="Fixture-only eager process",
        sourceRef=f"python:tests.dataHub.test_eagerSupervisor:{attribute}",
        queryable=True,
        executorKind="callable",
        executorModule="tests.dataHub.test_eagerSupervisor",
        executorAttribute=attribute,
        subjectParam="subject",
        selectorKind="subject",
        selectorRequired=True,
        executionMode="subjectFanout",
    )


def _query(subjects: tuple[str, ...] = ("AAPL", "MSFT")) -> DataQuery:
    return DataQuery(
        subjects=subjects,
        budget=QueryBudget(
            maxRows=100,
            maxBytes=192 * 1024,
            timeoutMs=20_000,
            maxAssets=1,
            maxSubjects=10,
            maxConcurrency=1,
        ),
    )


def _assertArtifactRootEmpty() -> None:
    root = ownerProcessArtifactRoot()
    assert not root.exists() or not tuple(root.iterdir())


def testSpawnChildSealsAllSelectorsAndLeavesZeroLive(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    descriptor = _descriptor()
    query = _query()
    selectors = tuple({"subject": subject} for subject in query.subjects)

    outcome = runEagerSeal(
        descriptor,
        query,
        selectors,
        requestId="fixture",
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        universeSnapshotId=None,
        publicDeadline=time.perf_counter() + 30,
        minimumWorkSeconds=0.05,
    )

    assert outcome.status == "ok", outcome
    assert outcome.seal is not None
    assert outcome.zeroLive
    assert outcome.ipcFrameCount == 2
    assert outcome.ipcByteCount <= 2 * MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES
    packed = packEagerSeal(outcome.seal)
    validateEagerSeal(
        packed,
        selectors=selectors,
        descriptor=descriptor,
        requestId="fixture",
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
    )
    decoded = [
        _decodeEagerResult(eagerResultAt(packed, selectors=selectors, index=index)).partitions[0].data
        for index in range(len(selectors))
    ]
    assert [item["subject"] for item in decoded] == ["AAPL", "MSFT"]
    assert all(item["noRefresh"] == "1" for item in decoded)
    assert all(item["hfOffline"] == "1" for item in decoded)
    _assertArtifactRootEmpty()


def testShortBudgetRejectsBeforeSpawn(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    before = {child.pid for child in multiprocessing.active_children() if child.pid is not None}

    outcome = runEagerSeal(
        _descriptor(),
        _query(("AAPL",)),
        ({"subject": "AAPL"},),
        requestId="fixture",
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        universeSnapshotId=None,
        publicDeadline=time.perf_counter() + 0.05,
        cleanupGraceSeconds=0.02,
        minimumWorkSeconds=0.1,
    )

    after = {child.pid for child in multiprocessing.active_children() if child.pid is not None}
    assert outcome.status == "budgetRejected"
    assert not outcome.spawned
    assert outcome.zeroLive
    assert outcome.errorCode == "PAGEABLE_EAGER_PROCESS_BUDGET"
    assert after == before
    _assertArtifactRootEmpty()


def testFactorProjectionMeasuresRejectDescriptorOnlyParentPin(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    descriptor = _descriptor()
    base = _query(("AAPL",))
    query = DataQuery(
        subjects=base.subjects,
        projection=FactorProjection(measures=("fixture.value",)),
        budget=base.budget,
    )
    descriptorOnlyPin = eagerCodePin(descriptor)

    with pytest.raises(ContinuationError) as captured:
        runEagerSeal(
            descriptor,
            query,
            ({"subject": "AAPL"},),
            requestId="fixture",
            snapshotId="catalog:fixture",
            contractHash=_CONTRACT_HASH,
            universeSnapshotId=None,
            publicDeadline=time.perf_counter() + 30,
            codePin=descriptorOnlyPin,
            minimumWorkSeconds=0.05,
        )

    assert captured.value.code == "PAGEABLE_EAGER_CODE_PIN_FAILED"
    _assertArtifactRootEmpty()


def testHungChildIsKilledWithinDeadlineAndLeavesZeroLive(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    started = time.perf_counter()

    outcome = runEagerSeal(
        _descriptor("_fixtureHang"),
        _query(("AAPL",)),
        ({"subject": "AAPL"},),
        requestId="fixture",
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        universeSnapshotId=None,
        publicDeadline=started + 3,
        cleanupGraceSeconds=0.5,
        minimumWorkSeconds=0.05,
    )

    assert outcome.status == "timedOut", outcome
    assert outcome.errorCode == "CONTINUATION_TIMEOUT"
    assert outcome.spawned
    assert outcome.zeroLive
    assert time.perf_counter() - started < 3.75
    _assertArtifactRootEmpty()
