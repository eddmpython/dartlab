"""Eager child strict offline과 source write 차단 tests."""

from __future__ import annotations

import socket
import sqlite3
import subprocess
import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from dartlab.data.contracts import DataAssetDescriptor, DataQuery, QueryBudget
from dartlab.data.eagerSupervisor import runEagerSeal
from dartlab.data.pagingRuntime import ownerProcessArtifactRoot

_CONTRACT_HASH = "c" * 64


def _fixtureNetwork(*, subject: str, outputPath: str):
    del subject, outputPath
    return socket.getaddrinfo("huggingface.co", 443)


def _fixturePythonWrite(*, subject: str, outputPath: str):
    del subject
    Path(outputPath).write_text("blocked", encoding="utf-8")
    return {"written": True}


def _fixtureSqliteWrite(*, subject: str, outputPath: str):
    del subject
    connection = sqlite3.connect(outputPath)
    try:
        connection.execute("create table blocked(value integer)")
        connection.commit()
    finally:
        connection.close()
    return {"written": True}


def _fixturePolarsWrite(*, subject: str, outputPath: str):
    del subject
    pl.DataFrame({"value": [1]}).write_parquet(outputPath)
    return {"written": True}


def _fixturePolarsBuffer(*, subject: str, outputPath: str):
    del subject, outputPath
    pl.DataFrame({"value": [1]}).write_parquet(BytesIO())
    return {"written": True}


def _fixturePyArrowWrite(*, subject: str, outputPath: str):
    del subject
    pq.write_table(pa.table({"value": [1]}), outputPath)
    return {"written": True}


def _fixturePandasWrite(*, subject: str, outputPath: str):
    del subject
    pd.DataFrame({"value": [1]}).to_parquet(outputPath)
    return {"written": True}


def _fixtureNumpyWrite(*, subject: str, outputPath: str):
    del subject
    np.save(outputPath, np.array([1], dtype=np.int64))
    return {"written": True}


def _fixtureNumpyTofile(*, subject: str, outputPath: str):
    del subject
    np.array([1], dtype=np.int64).tofile(outputPath)
    return {"written": True}


def _fixtureSubprocessWrite(*, subject: str, outputPath: str):
    del subject
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('blocked')",
            outputPath,
        ],
        check=True,
    )
    return {"written": True}


def _descriptor(attribute: str) -> DataAssetDescriptor:
    return DataAssetDescriptor(
        assetId=f"analysis.eagerSandboxFixture.{attribute}",
        assetVersionId=f"analysis.eagerSandboxFixture.{attribute}:v1",
        owner="tests.data.test_eagerSandbox",
        layer="L2",
        kind="computed",
        label="Eager sandbox fixture",
        description="Fixture-only sandbox probe",
        sourceRef=f"python:tests.data.test_eagerSandbox:{attribute}",
        queryable=True,
        executorKind="callable",
        executorModule="tests.data.test_eagerSandbox",
        executorAttribute=attribute,
        subjectParam="subject",
        selectorKind="subject",
        selectorRequired=True,
        executionMode="subjectFanout",
    )


def _run(attribute: str, outputPath: Path):
    query = DataQuery(
        subjects=("AAPL",),
        params={"outputPath": str(outputPath)},
        budget=QueryBudget(
            maxRows=10,
            maxBytes=64 * 1024,
            timeoutMs=20_000,
            maxAssets=1,
            maxSubjects=1,
            maxConcurrency=1,
        ),
    )
    return runEagerSeal(
        _descriptor(attribute),
        query,
        ({"subject": "AAPL"},),
        requestId="fixture",
        snapshotId="catalog:fixture",
        contractHash=_CONTRACT_HASH,
        universeSnapshotId=None,
        publicDeadline=time.perf_counter() + 20,
        minimumWorkSeconds=0.05,
    )


@pytest.mark.parametrize(
    ("attribute", "expectedCode"),
    [
        ("_fixtureNetwork", "OFFLINE_NETWORK_BLOCKED"),
        ("_fixturePythonWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixtureSqliteWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixturePolarsWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixturePolarsBuffer", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixturePyArrowWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixturePandasWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixtureNumpyWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixtureNumpyTofile", "PAGEABLE_EAGER_WRITE_BLOCKED"),
        ("_fixtureSubprocessWrite", "PAGEABLE_EAGER_WRITE_BLOCKED"),
    ],
)
def testSandboxBlocksNetworkPythonNativeAndDescendantWrites(
    tmp_path,
    monkeypatch,
    attribute: str,
    expectedCode: str,
) -> None:
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path / "home"))
    outputPath = tmp_path / f"{attribute}.blocked"
    possibleResidues = (outputPath, Path(f"{outputPath}.npy"))

    try:
        outcome = _run(attribute, outputPath)
        observedResidues = tuple(path for path in possibleResidues if path.exists())
    finally:
        for path in possibleResidues:
            path.unlink(missing_ok=True)

    assert outcome.status == "childFailed", outcome
    assert outcome.errorCode == expectedCode
    assert outcome.spawned
    assert outcome.zeroLive
    assert not observedResidues
    artifactRoot = ownerProcessArtifactRoot()
    assert not artifactRoot.exists() or not tuple(artifactRoot.iterdir())
