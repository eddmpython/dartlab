from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class StatementsResult:
    corpName: str | None
    period: str  # "y" | "q" | "h"
    scope: str = "consolidated"  # "consolidated" | "separate"
    nYears: int = 0
    BS: pl.DataFrame | None = None  # 재무상태표
    IS: pl.DataFrame | None = None  # 손익계산서
    CF: pl.DataFrame | None = None  # 현금흐름표
