"""내부통제 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class InternalControlResult:
    """내부통제 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        controlDf: 내부회계관리제도 시계열 DataFrame
            year | opinion | auditor | hasWeakness
    """

    corpName: str | None = None
    nYears: int = 0
    controlDf: pl.DataFrame | None = None
