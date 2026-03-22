"""타법인출자 현황 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class InvestmentInOtherResult:
    """타법인출자 현황 분석 결과."""

    corpName: str | None = None
    nYears: int = 0
    investments: list[dict] = field(default_factory=list)
    noData: bool = False
    investmentDf: pl.DataFrame | None = None
