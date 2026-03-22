"""증권 발행(증자/감자) 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class FundraisingResult:
    """증권 발행(증자/감자) 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        issuances: 발행 이력 [{date, issueType, stockType, quantity, parValue, issuePrice, note}, ...]
        noData: 발행 실적 없음 여부
        issuanceDf: 발행 이력 DataFrame
            date | issueType | stockType | quantity | parValue | issuePrice | note
    """

    corpName: str | None = None
    nYears: int = 0
    issuances: list[dict] = field(default_factory=list)
    noData: bool = False
    issuanceDf: pl.DataFrame | None = None
