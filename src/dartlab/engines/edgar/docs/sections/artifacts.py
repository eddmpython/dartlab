from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path

import polars as pl

_ARTIFACT_PACKAGE = "dartlab.engines.edgar.docs.sections.artifactData"


@contextmanager
def packagedArtifactPath(name: str) -> Iterator[Path]:
    ref = files(_ARTIFACT_PACKAGE) / name
    with as_file(ref) as path:
        yield path


def _outputDir() -> Path:
    return Path(__file__).resolve().parents[6] / "experiments" / "057_edgarSectionMap" / "output"


def loadCanonicalRows() -> pl.DataFrame | None:
    try:
        with packagedArtifactPath("canonicalRows.parquet") as path:
            return pl.read_parquet(path)
    except FileNotFoundError:
        path = _outputDir() / "canonicalRows.parquet"
        if not path.exists():
            return None
        return pl.read_parquet(path)


def loadCoverageSnapshot() -> dict[str, object] | None:
    try:
        ref = files(_ARTIFACT_PACKAGE) / "mappingCoverage.latest.json"
        return json.loads(ref.read_text(encoding="utf-8"))
    except FileNotFoundError:
        path = _outputDir() / "mappingCoverage.latest.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


def loadTopicDrafts() -> dict[str, object] | None:
    try:
        ref = files(_ARTIFACT_PACKAGE) / "formTopicDrafts.json"
        return json.loads(ref.read_text(encoding="utf-8"))
    except FileNotFoundError:
        path = _outputDir() / "formTopicDrafts.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
