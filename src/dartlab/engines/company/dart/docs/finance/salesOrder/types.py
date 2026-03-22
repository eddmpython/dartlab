"""매출 및 수주상황 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class SalesOrderResult:
    """매출 및 수주상황 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        unit: 단위 (억원, 백만원 등)
        sales: 매출실적 [{label, values}, ...]
        orders: 수주상황 [{label, values}, ...]
        noData: 해당사항 없음 여부
        salesDf: 매출실적 DataFrame (label | v1 | v2 | v3)
        orderDf: 수주상황 DataFrame (label | v1 | v2 | ...)
    """

    corpName: str | None = None
    nYears: int = 0
    unit: str = "백만원"
    sales: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    noData: bool = False
    salesDf: pl.DataFrame | None = None
    orderDf: pl.DataFrame | None = None
