"""DART/EDGAR 공통 타입."""

from __future__ import annotations

from typing import NamedTuple

import polars as pl


class ShowResult(NamedTuple):
    """docs.show() 반환 — text와 table을 분리."""

    text: pl.DataFrame | None
    table: pl.DataFrame | None
