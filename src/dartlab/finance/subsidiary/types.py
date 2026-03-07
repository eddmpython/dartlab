"""타법인출자 현황 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class SubsidiaryInvestment:
    """개별 타법인 출자 항목."""

    name: str
    listed: str | None = None
    firstAcquired: str | None = None
    purpose: str | None = None
    firstAmount: float | None = None
    beginShares: float | None = None
    beginRatio: float | None = None
    beginBook: float | None = None
    acquiredShares: float | None = None
    acquiredAmount: float | None = None
    valuationGain: float | None = None
    endShares: float | None = None
    endRatio: float | None = None
    endBook: float | None = None
    totalAssets: float | None = None
    netIncome: float | None = None


@dataclass
class SubsidiaryResult:
    """타법인출자 현황 분석 결과."""

    corpName: str | None
    nYears: int
    investments: list[SubsidiaryInvestment] = field(default_factory=list)
    timeSeries: pl.DataFrame | None = None
