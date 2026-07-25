"""EDGAR companyfacts local-only owner reader tests."""

from __future__ import annotations

import hashlib

import polars as pl
import pytest

import dartlab.core.dataLoader as dataLoader
from dartlab.providers.edgar.finance.facts import readCompanyFactsLocal


def testLocalReaderProjectsColumnsWithoutRefreshOrNetwork(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    frame = pl.DataFrame(
        {
            "namespace": ["us-gaap"],
            "tag": ["Assets"],
            "unit": ["USD"],
            "val": [100.0],
            "form": ["10-Q"],
            "filed": ["2025-01-30"],
            "start": [None],
            "end": ["2024-12-31"],
            "accn": ["a"],
            "unused": ["not-read"],
        }
    )
    frame.write_parquet(tmp_path / "0000320193.parquet")
    monkeypatch.setattr(dataLoader, "_dataDir", lambda _category: tmp_path)

    result = readCompanyFactsLocal("320193", columns=("namespace", "tag", "val"))

    assert result.to_dicts() == [{"namespace": "us-gaap", "tag": "Assets", "val": 100.0}]


def testLocalReaderFailsClosedWhenShardOrRequiredColumnIsMissing(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dataLoader, "_dataDir", lambda _category: tmp_path)

    with pytest.raises(FileNotFoundError, match="0000320193"):
        readCompanyFactsLocal("320193")

    pl.DataFrame({"namespace": ["us-gaap"]}).write_parquet(tmp_path / "0000320193.parquet")
    with pytest.raises(ValueError, match="필수 columns"):
        readCompanyFactsLocal("320193", columns=("namespace", "tag"))


def testVerifiedPayloadParsesTheHashedBytesWithoutReopeningPath(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "0000320193.parquet"
    pl.DataFrame(
        {
            "namespace": ["us-gaap"],
            "tag": ["Assets"],
            "val": [100.0],
        }
    ).write_parquet(path)
    verifiedBytes = path.read_bytes()
    digest = hashlib.sha256(verifiedBytes).hexdigest()
    path.unlink()
    monkeypatch.setattr(
        dataLoader,
        "_dataDir",
        lambda _category: pytest.fail("verified payload 경로를 다시 열면 안 됩니다"),
    )

    result = readCompanyFactsLocal(
        "320193",
        columns=("namespace", "tag", "val"),
        sourcePayload=verifiedBytes,
        expectedIntegrityDigest=digest,
    )

    assert result.to_dicts() == [{"namespace": "us-gaap", "tag": "Assets", "val": 100.0}]
    with pytest.raises(ValueError, match="RESOURCE_SOURCE_DRIFT"):
        readCompanyFactsLocal(
            "320193",
            columns=("namespace",),
            sourcePayload=verifiedBytes,
            expectedIntegrityDigest="0" * 64,
        )
