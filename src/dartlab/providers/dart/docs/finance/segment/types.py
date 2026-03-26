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

    def toDataFrame(self) -> pl.DataFrame:
        """테이블 → DataFrame (행=항목명, 열=부문/지역/제품)."""
        import polars as pl

        nCols = min(len(self.columns), min(len(v) for v in self.rows.values()) if self.rows else 0)
        if nCols == 0:
            return pl.DataFrame()

        data: dict[str, list] = {"계정명": []}
        for i in range(nCols):
            data[self.columns[i]] = []

        for name in self.order:
            vals = self.rows.get(name)
            if vals is None:
                continue
            data["계정명"].append(name)
            for i in range(nCols):
                data[self.columns[i]].append(vals[i] if i < len(vals) else None)

        return pl.DataFrame(data)


@dataclass
class SegmentsResult:
    """부문별 보고 분석 결과."""

    corpName: str | None
    nYears: int
    period: str = "y"  # "y" | "q" | "h"
    tables: dict[str, list[SegmentTable]] | None = None  # {year: [tables]}
    revenue: pl.DataFrame | None = None

    def latestTable(self, tableType: str = "segment") -> SegmentTable | None:
        """최신 연도의 당기 aligned 테이블 반환."""
        if self.tables is None:
            return None
        for year in sorted(self.tables.keys(), reverse=True):
            for t in self.tables[year]:
                if t.tableType == tableType and t.period == "당기" and t.aligned:
                    return t
        return None
