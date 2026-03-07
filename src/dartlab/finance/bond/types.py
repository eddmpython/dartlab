"""채무증권 발행실적 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class BondIssuance:
    """개별 채무증권 발행 항목."""

    issuer: str
    bondType: str | None = None
    method: str | None = None
    issueDate: str | None = None
    amount: float | None = None
    interestRate: str | None = None
    rating: str | None = None
    maturityDate: str | None = None
    redeemed: str | None = None
    underwriter: str | None = None


@dataclass
class BondResult:
    """채무증권 발행실적 분석 결과."""

    corpName: str | None
    nYears: int
    issuances: list[BondIssuance] = field(default_factory=list)
    timeSeries: pl.DataFrame | None = None
