"""연구개발활동 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class RndResult:
    """연구개발활동 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        rndDf: R&D 비용 시계열 DataFrame
            year | rndExpense | revenueRatio
    """

    corpName: str | None = None
    nYears: int = 0
    rndDf: pl.DataFrame | None = None
