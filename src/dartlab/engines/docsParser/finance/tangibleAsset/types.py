"""유형자산 변동표 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import polars as pl


@dataclass
class TangibleMovement:
    """한 기간(당기/전기)의 유형자산 변동표."""

    period: str  # "당기" | "전기"
    categories: list[str]  # ["토지", "건물", ..., "합계"]
    rows: list[dict[str, Any]]  # [{"label": "기초", "values": {cat: float|None}}]
    unit: float = 1.0


@dataclass
class TangibleAssetResult:
    """유형자산 변동표 분석 결과.

    reliability:
        "high" — 합계 컬럼이 있어 정확도 검증 가능
        "low"  — 합계 컬럼 없음. 개별 열 합산값은 취득원가일 수 있음

    warnings:
        신뢰도 관련 경고 메시지 리스트.
        예: ["합계 컬럼 없음 — 개별 열 합산값은 취득원가일 수 있음"]
    """

    corpName: str | None
    nYears: int
    reliability: str = "high"
    warnings: list[str] = field(default_factory=list)
    movements: dict[str, list[TangibleMovement]] | None = None
    movementDf: pl.DataFrame | None = None
