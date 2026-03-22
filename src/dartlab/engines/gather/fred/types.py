"""FRED 엔진 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass

# ── 예외 ──


class FredError(Exception):
    """FRED API 기본 예외."""


class RateLimitError(FredError):
    """API 요청 한도 초과 (120 RPM)."""


class SeriesNotFoundError(FredError):
    """존재하지 않는 시리즈 ID."""


class AuthenticationError(FredError):
    """API 키 누락 또는 무효."""


# ── 데이터 타입 ──


@dataclass(frozen=True)
class SeriesMeta:
    """FRED 시계열 메타데이터."""

    id: str
    title: str
    frequency: str  # "Daily", "Monthly", "Quarterly", "Annual"
    units: str
    seasonal_adjustment: str
    observation_start: str
    observation_end: str
    last_updated: str
    notes: str = ""


@dataclass(frozen=True)
class CatalogEntry:
    """카탈로그 시리즈 정의."""

    id: str
    label: str
    group: str
    frequency: str
    unit: str
    description: str
