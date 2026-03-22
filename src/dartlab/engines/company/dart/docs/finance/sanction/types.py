"""제재 현황 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class SanctionResult:
    """제재 현황 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        sanctionDf: 제재 현황 DataFrame
            year | date | agency | subject | action | amount | reason
    """

    corpName: str | None = None
    nYears: int = 0
    sanctionDf: pl.DataFrame | None = None
