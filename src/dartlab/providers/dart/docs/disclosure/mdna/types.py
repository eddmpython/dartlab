"""이사의 경영진단 및 분석의견(MD&A) 타입 정의."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MdnaSection:
    """MD&A 개별 섹션."""

    title: str
    category: str
    text: str
    textLines: int = 0
    tableLines: int = 0


@dataclass
class MdnaResult:
    """이사의 경영진단 및 분석의견 분석 결과."""

    corpName: str | None
    nYears: int
    sections: list[MdnaSection] = field(default_factory=list)
    overview: str | None = None
