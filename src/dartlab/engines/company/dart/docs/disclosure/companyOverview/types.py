"""회사의 개요 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CreditRating:
    """개별 신용등급."""

    agency: str
    grade: str


@dataclass
class OverviewResult:
    """회사의 개요 분석 결과.

    각 필드가 None인 이유를 구분하기 위해 missing/failed 리스트를 제공한다.
    - missing: 원문에 해당 항목 자체가 없는 필드
    - failed: 항목은 존재하지만 파싱에 실패한 필드
    - 필드에 값이 있으면 정상 추출
    """

    corpName: str | None
    year: int
    founded: str | None = None
    address: str | None = None
    homepage: str | None = None
    subsidiaryCount: int | None = None
    isSME: bool | None = None
    isVenture: bool | None = None
    creditRatings: list[CreditRating] = field(default_factory=list)
    listedDate: str | None = None
    missing: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
