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
        """테이블 → DataFrame (행=항목명, 열=부문/지역/제품).

        중복 컬럼명(연결/개별 반복) 처리: 접미사(_2, _3...) 부여.
        """
        import polars as pl

        nCols = min(len(self.columns), min(len(v) for v in self.rows.values()) if self.rows else 0)
        if nCols == 0:
            return pl.DataFrame()

        # 중복 컬럼명에 접미사 부여
        uniqueCols: list[str] = []
        seen: dict[str, int] = {}
        for i in range(nCols):
            name = self.columns[i]
            if name in seen:
                seen[name] += 1
                uniqueCols.append(f"{name}_{seen[name]}")
            else:
                seen[name] = 1
                uniqueCols.append(name)

        data: dict[str, list] = {"계정명": []}
        for col in uniqueCols:
            data[col] = []

        for name in self.order:
            vals = self.rows.get(name)
            if vals is None:
                continue
            data["계정명"].append(name)
            for i in range(nCols):
                data[uniqueCols[i]].append(vals[i] if i < len(vals) else None)

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
