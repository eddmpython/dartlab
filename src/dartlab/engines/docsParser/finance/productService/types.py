"""주요 제품 및 서비스 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class ProductServiceResult:
    """주요 제품 및 서비스 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        unit: 단위 (억원, 백만원 등)
        products: 제품/서비스 목록 [{label, amount, ratio}, ...]
        noData: 해당사항 없음 여부
        productDf: 제품/서비스 DataFrame (label | amount | ratio)
    """

    corpName: str | None = None
    nYears: int = 0
    unit: str = "백만원"
    products: list[dict] = field(default_factory=list)
    noData: bool = False
    productDf: pl.DataFrame | None = None
