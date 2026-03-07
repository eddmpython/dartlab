"""비용의 성격별 분류 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class CostByNatureResult:
    """비용의 성격별 분류 분석 결과."""

    corpName: str | None
    nYears: int
    timeSeries: pl.DataFrame | None = None
    crossCheck: dict[str, dict[str, int]] = field(default_factory=dict)
    ratios: pl.DataFrame | None = None
