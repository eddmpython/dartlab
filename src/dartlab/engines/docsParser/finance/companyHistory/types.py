"""회사의 연혁 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class CompanyHistoryResult:
    """회사의 연혁 분석 결과."""

    corpName: str | None = None
    nYears: int = 0
    events: list[dict] = field(default_factory=list)
    eventsDf: pl.DataFrame | None = None
