"""자본금 변동 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class CapitalChangeResult:
    """자본금 변동 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        capitalDf: 자본금 변동 시계열 DataFrame
            year | commonShares | preferredShares | commonParValue | preferredParValue | commonCapital | preferredCapital
        shareTotalDf: 주식의 총수 시계열 DataFrame
            year | referenceDate | authorizedCommon | authorizedPreferred | authorizedTotal
            | issuedCommon | issuedPreferred | issuedTotal
            | reducedCommon | reducedPreferred | reducedTotal
            | outstandingCommon | outstandingPreferred | outstandingTotal
        treasuryDf: 자기주식 변동 시계열 DataFrame
            year | totalBegin | totalEnd
    """

    corpName: str | None = None
    nYears: int = 0
    capitalDf: pl.DataFrame | None = None
    shareTotalDf: pl.DataFrame | None = None
    treasuryDf: pl.DataFrame | None = None
