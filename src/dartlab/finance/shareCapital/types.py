"""주식의 총수 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class ShareCapitalResult:
    """주식의 총수 분석 결과."""

    corpName: str | None
    nYears: int
    authorizedShares: float | None = None
    issuedShares: float | None = None
    retiredShares: float | None = None
    outstandingShares: float | None = None
    treasuryShares: float | None = None
    floatingShares: float | None = None
    treasuryRatio: float | None = None
    timeSeries: pl.DataFrame | None = None
