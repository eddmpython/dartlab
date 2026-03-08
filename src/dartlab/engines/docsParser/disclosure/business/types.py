"""사업의 내용 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class BusinessSection:
    """사업의 내용 하위 섹션."""

    key: str
    title: str
    chars: int
    text: str


@dataclass
class BusinessChange:
    """연도별 변경 정보."""

    year: int
    changedPct: float
    added: int
    removed: int
    totalChars: int


@dataclass
class BusinessResult:
    """사업의 내용 분석 결과."""

    corpName: str | None
    year: int
    sections: list[BusinessSection] = field(default_factory=list)
    changes: list[BusinessChange] = field(default_factory=list)
