"""우발부채 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class ContingentLiabilityResult:
    """우발부채·채무보증·소송 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        guaranteeDf: 채무보증 시계열 DataFrame
            year | totalGuaranteeAmount | lineCount
        lawsuitDf: 소송 현황 DataFrame
            year | filingDate | parties | description | amount | amountValue | status
    """

    corpName: str | None = None
    nYears: int = 0
    guaranteeDf: pl.DataFrame | None = None
    lawsuitDf: pl.DataFrame | None = None
