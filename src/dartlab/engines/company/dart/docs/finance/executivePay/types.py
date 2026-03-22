"""임원 보수 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class ExecutivePayResult:
    """임원 보수 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        payByTypeDf: 유형별 보수 시계열 DataFrame
            year | category | headcount | totalPay | avgPay
            (category: 등기이사, 사외이사, 감사위원 등)
        topPayDf: 5억 초과 개인별 보수 DataFrame
            year | name | position | totalPay
    """

    corpName: str | None = None
    nYears: int = 0
    payByTypeDf: pl.DataFrame | None = None
    topPayDf: pl.DataFrame | None = None
