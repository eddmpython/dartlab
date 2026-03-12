from __future__ import annotations

import json
from pathlib import Path

import polars as pl


def _outputDir() -> Path:
    return Path(__file__).resolve().parents[6] / "experiments" / "057_edgarSectionMap" / "output"


def loadCanonicalRows() -> pl.DataFrame | None:
    path = _outputDir() / "canonicalRows.parquet"
    if not path.exists():
        return None
    return pl.read_parquet(path)


def loadCoverageSnapshot() -> dict[str, object] | None:
    path = _outputDir() / "mappingCoverage.latest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def loadTopicDrafts() -> dict[str, object] | None:
    path = _outputDir() / "formTopicDrafts.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
