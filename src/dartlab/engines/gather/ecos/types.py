"""ECOS 엔진 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass

# ── 예외 ──


class EcosError(Exception):
    """ECOS API 기본 예외."""


class RateLimitError(EcosError):
    """API 요청 한도 초과."""


class SeriesNotFoundError(EcosError):
    """존재하지 않는 지표 ID."""


class AuthenticationError(EcosError):
    """API 키 누락 또는 무효."""


# ── 데이터 타입 ──


@dataclass(frozen=True)
class CatalogEntry:
    """ECOS 카탈로그 지표 정의."""

    id: str  # "GDP", "CPI" 등
    label: str  # "실질GDP", "소비자물가지수" 등
    group: str  # "국민계정", "물가" 등
    frequency: str  # "D", "M", "Q", "A"
    unit: str  # "십억원", "%", "2020=100" 등
    description: str
    tableCode: str  # ECOS 통계표코드
    itemCode: str  # ECOS 항목코드
