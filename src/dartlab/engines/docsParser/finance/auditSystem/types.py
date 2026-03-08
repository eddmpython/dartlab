"""감사제도에 관한 사항 분석 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


@dataclass
class AuditSystemResult:
    """감사제도에 관한 사항 분석 결과."""

    corpName: str | None = None
    nYears: int = 0
    committee: list[dict] = field(default_factory=list)
    activity: list[dict] = field(default_factory=list)
    textOnly: bool = False
    committeeDf: pl.DataFrame | None = None
    activityDf: pl.DataFrame | None = None
