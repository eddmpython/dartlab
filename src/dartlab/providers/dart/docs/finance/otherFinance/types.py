"""기타 재무에 관한 사항 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class OtherFinanceResult:
    """기타 재무에 관한 사항 분석 결과."""

    corpName: str | None = None
    nYears: int = 0
    badDebt: list[dict] = field(default_factory=list)
    inventory: list[dict] = field(default_factory=list)
    noData: bool = False
    badDebtDf: pl.DataFrame | None = None
    inventoryDf: pl.DataFrame | None = None
