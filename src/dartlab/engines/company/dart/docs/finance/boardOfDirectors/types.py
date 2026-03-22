"""이사회 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class BoardResult:
    """이사회 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        boardDf: 이사회 시계열 DataFrame
            year | totalDirectors | outsideDirectors | meetingCount | avgAttendanceRate
        committeeDf: 위원회 구성 DataFrame
            year | committeeName | composition | members
    """

    corpName: str | None = None
    nYears: int = 0
    boardDf: pl.DataFrame | None = None
    committeeDf: pl.DataFrame | None = None
