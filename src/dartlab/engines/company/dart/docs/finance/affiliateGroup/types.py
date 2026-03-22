"""계열회사 현황 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class AffiliateGroupResult:
    """계열회사 현황 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        groupName: 기업집단명 (예: "삼성", "현대자동차")
        listedCount: 상장 계열사 수
        unlistedCount: 비상장 계열사 수
        totalCount: 총 계열사 수
        affiliates: 계열사 목록 [{name, listed}, ...]
        affiliateDf: 계열사 목록 DataFrame
            name | listed
    """

    corpName: str | None = None
    nYears: int = 0
    groupName: str | None = None
    listedCount: int | None = None
    unlistedCount: int | None = None
    totalCount: int | None = None
    affiliates: list[dict] = field(default_factory=list)
    affiliateDf: pl.DataFrame | None = None
