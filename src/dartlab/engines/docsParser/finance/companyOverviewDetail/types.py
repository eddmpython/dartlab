"""회사의 개요 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CompanyOverviewDetailResult:
    """회사의 개요 분석 결과."""

    corpName: str | None = None
    nYears: int = 0
    foundedDate: str | None = None
    listedDate: str | None = None
    address: str | None = None
    ceo: str | None = None
    mainBusiness: str | None = None
    website: str | None = None
