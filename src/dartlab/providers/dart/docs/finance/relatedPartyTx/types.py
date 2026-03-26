"""대주주 거래 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class RelatedPartyTxResult:
    """대주주 등과의 거래내용 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        guaranteeDf: 채무보증 시계열 DataFrame
            year | entity | relationship | amount
        assetTxDf: 자산 거래 시계열 DataFrame
            year | entity | txType | amount
        revenueTxDf: 매출입 거래 시계열 DataFrame
            year | entity | sales | purchases
    """

    corpName: str | None = None
    nYears: int = 0
    guaranteeDf: pl.DataFrame | None = None
    assetTxDf: pl.DataFrame | None = None
    revenueTxDf: pl.DataFrame | None = None
