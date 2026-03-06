"""부문별 보고 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class SegmentTable:
    """파싱된 세그먼트 테이블 1개."""

    period: str  # "당기" | "전기"
    tableType: str  # "segment" | "product" | "region"
    columns: list[str]
    rows: dict[str, list[float | None]]
    order: list[str]
    aligned: bool


@dataclass
class SegmentsResult:
    """부문별 보고 분석 결과."""

    corpName: str | None
    nYears: int
    period: str = "y"  # "y" | "q" | "h"
    tables: dict[str, list[SegmentTable]] | None = None  # {year: [tables]}
    revenue: pl.DataFrame | None = None
