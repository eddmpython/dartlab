"""임원 현황 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class ExecutiveResult:
    """임원 현황 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        executiveDf: 등기임원 집계 시계열
            year | totalRegistered | insideDirectors | outsideDirectors |
            otherNonexec | fullTimeCount | partTimeCount | maleCount | femaleCount
        unregPayDf: 미등기임원 보수 시계열
            year | headcount | totalSalary | avgSalary
    """

    corpName: str | None = None
    nYears: int = 0
    executiveDf: pl.DataFrame | None = None
    unregPayDf: pl.DataFrame | None = None
