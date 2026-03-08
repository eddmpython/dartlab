"""위험관리 및 파생거래 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class RiskDerivativeResult:
    """위험관리 및 파생거래 분석 결과.

    Attributes:
        corpName: 기업명
        nYears: 시계열 연도 수
        unit: 단위 (백만원 등)
        fxSensitivity: 환율 민감도 [{currency, upImpact, downImpact}, ...]
        derivatives: 파생상품 계약 [{label, values}, ...]
        noData: 해당사항 없음 여부
        textOnly: 서술형만 존재 (테이블 없음)
        fxDf: 환율 민감도 DataFrame (currency | upImpact | downImpact)
        derivativeDf: 파생상품 DataFrame (label | v1 | v2 | ...)
    """

    corpName: str | None = None
    nYears: int = 0
    unit: str = "백만원"
    fxSensitivity: list[dict] = field(default_factory=list)
    derivatives: list[dict] = field(default_factory=list)
    noData: bool = False
    textOnly: bool = False
    fxDf: pl.DataFrame | None = None
    derivativeDf: pl.DataFrame | None = None
