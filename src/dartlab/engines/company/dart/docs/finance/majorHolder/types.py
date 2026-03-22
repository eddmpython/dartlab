"""최대주주 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class Holder:
    """개별 주주 정보."""

    name: str
    relation: str
    stockType: str
    sharesStart: float | None = None
    ratioStart: float | None = None
    sharesEnd: float | None = None
    ratioEnd: float | None = None


@dataclass
class MajorHolderResult:
    """최대주주 분석 결과."""

    corpName: str | None
    nYears: int
    majorHolder: str | None = None
    majorRatio: float | None = None
    totalRatio: float | None = None
    holders: list[Holder] = field(default_factory=list)
    timeSeries: pl.DataFrame | None = None


@dataclass
class BigHolder:
    """5% 이상 주주 정보."""

    name: str
    shares: float | None = None
    ratio: float | None = None


@dataclass
class Minority:
    """소액주주 현황."""

    holders: int
    totalHolders: int
    holderPct: float
    shares: int
    totalShares: int
    sharePct: float


@dataclass
class VotingRights:
    """의결권 현황."""

    issuedCommon: float | None = None
    issuedPref: float | None = None
    noVoteCommon: float | None = None
    noVotePref: float | None = None
    excludedCommon: float | None = None
    excludedPref: float | None = None
    restrictedCommon: float | None = None
    restrictedPref: float | None = None
    restoredCommon: float | None = None
    restoredPref: float | None = None
    votableCommon: float | None = None
    votablePref: float | None = None


@dataclass
class HolderOverview:
    """주주 종합 현황."""

    corpName: str | None
    year: int | None = None
    bigHolders: list[BigHolder] = field(default_factory=list)
    minority: Minority | None = None
    voting: VotingRights | None = None
