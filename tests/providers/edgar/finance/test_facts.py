"""EDGAR companyfacts local-only owner reader tests."""

from __future__ import annotations

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
