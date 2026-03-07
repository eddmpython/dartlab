"""직원 현황 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class EmployeeResult:
    """직원 현황 분석 결과."""

    corpName: str | None
    nYears: int
    timeSeries: pl.DataFrame | None = None
