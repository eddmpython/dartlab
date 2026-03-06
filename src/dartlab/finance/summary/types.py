from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class YearAccounts:
    year: str  # "2024" 또는 "2024Q1"
    accounts: dict[str, list[float | None]]
    order: list[str]


@dataclass
class BridgeResult:
    curYear: str  # period key
    prevYear: str
    rate: float
    matched: int
    total: int
    yearGap: int  # annual: 연도차, quarterly: 분기차
    pairs: dict[str, str]


@dataclass
class Segment:
    startYear: str  # period key
    endYear: str
    nYears: int  # period 수
    matched: int
    total: int
    rate: float | None


@dataclass
class AnalysisResult:
    corpName: str | None
    nYears: int  # period 수
    nPairs: int
    nBreakpoints: int
    nSegments: int
    allRate: float | None
    allMatched: int
    allTotal: int
    contRate: float | None
    contMatched: int
    contTotal: int
    segments: list[Segment]
    breakpoints: list[BridgeResult]
    pairResults: list[BridgeResult]
    yearAccounts: dict[str, YearAccounts]
    period: str = "y"  # "y" | "q" | "h"
    FS: pl.DataFrame | None = None  # 전체 재무제표 (BS + IS)
    BS: pl.DataFrame | None = None  # 재무상태표
    IS: pl.DataFrame | None = None  # 손익계산서
