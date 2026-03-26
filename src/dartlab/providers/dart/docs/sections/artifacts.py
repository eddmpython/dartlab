"""패키지에 포함된 sections 학습 산출물 로더."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from importlib.resources import as_file, files
from pathlib import Path

import polars as pl

_PROFILE_PACKAGE = "dartlab.providers.dart.docs.sections.profileData"


@contextmanager
def packagedArtifactPath(name: str) -> Iterator[Path]:
    """패키지 리소스를 filesystem path로 노출."""
    ref = files(_PROFILE_PACKAGE) / name
    with as_file(ref) as path:
        yield path


@lru_cache(maxsize=4)
def loadProjectionRules(chapter: str) -> dict[str, list[str]]:
    filename = f"projectionRules.{chapter}.json"
    try:
        ref = files(_PROFILE_PACKAGE) / filename
        return json.loads(ref.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def loadSectionProfileTable() -> pl.DataFrame | None:
    try:
        with packagedArtifactPath("sectionProfileTable.parquet") as path:
            return pl.read_parquet(path)
    except FileNotFoundError:
        return None
