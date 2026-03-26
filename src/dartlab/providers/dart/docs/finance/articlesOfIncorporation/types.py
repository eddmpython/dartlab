"""정관에 관한 사항 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class ArticlesResult:
    """정관에 관한 사항 분석 결과."""

    corpName: str | None = None
    nYears: int = 0
    changes: list[dict] = field(default_factory=list)
    purposes: list[dict] = field(default_factory=list)
    noData: bool = False
    changesDf: pl.DataFrame | None = None
    purposesDf: pl.DataFrame | None = None
