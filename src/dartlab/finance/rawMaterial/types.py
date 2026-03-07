"""원재료 및 생산설비 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawMaterial:
    """개별 원재료 매입 항목."""

    segment: str | None = None
    item: str | None = None
    usage: str | None = None
    amount: float | None = None
    ratio: float | None = None
    supplier: str | None = None


@dataclass
class Equipment:
    """유형자산 기말잔액 — 자산 유형별 dict."""

    land: float | None = None
    buildings: float | None = None
    structures: float | None = None
    machinery: float | None = None
    construction: float | None = None
    vehicles: float | None = None
    fixtures: float | None = None
    rou: float | None = None
    undelivered: float | None = None
    other: float | None = None
    total: float | None = None
    depreciation: float | None = None
    capex: float | None = None


@dataclass
class CapexItem:
    """시설투자 항목."""

    segment: str
    amount: float


@dataclass
class RawMaterialResult:
    """원재료 및 생산설비 분석 결과."""

    corpName: str | None
    year: int | None = None
    materials: list[RawMaterial] = field(default_factory=list)
    equipment: Equipment | None = None
    capexItems: list[CapexItem] = field(default_factory=list)
