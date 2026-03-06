"""관계기업/공동기업 투자 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class AffiliateProfile:
    """관계기업 투자현황."""

    name: str
    ownership: float | None = None  # 지분율 (%)
    bookValue: float | None = None  # 장부금액
    acquisitionCost: float | None = None  # 취득원가
    location: str | None = None  # 소재지
    activity: str | None = None  # 주요 영업활동
    category: str | None = None  # 관계기업/공동기업


@dataclass
class AffiliateMovement:
    """관계기업 변동내역."""

    name: str
    opening: float | None = None  # 기초
    closing: float | None = None  # 기말
    acquisition: float | None = None  # 취득
    disposal: float | None = None  # 처분
    equityIncome: float | None = None  # 지분법손익
    equityCapChange: float | None = None  # 지분법자본변동
    dividend: float | None = None  # 배당
    impairment: float | None = None  # 손상
    other: float | None = None  # 기타


@dataclass
class AffiliatesResult:
    """관계기업 분석 결과."""

    corpName: str | None
    nYears: int
    period: str = "y"  # "y" | "q" | "h"
    profiles: dict[str, list[AffiliateProfile]] | None = None  # {year: [profiles]}
    movements: dict[str, list[AffiliateMovement]] | None = None  # {year: [movements]}
    movementDf: pl.DataFrame | None = None  # 기업별 변동 시계열
