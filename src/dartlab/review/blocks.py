"""review 블록 타입."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TextBlock:
    """서술형 텍스트 블록."""

    text: str
    style: str = ""
    indent: str = "body"  # "body" (6칸) | "h2" (3칸)


@dataclass
class HeadingBlock:
    """섹션 제목 블록."""

    title: str
    level: int = 1
    helper: str = ""  # 이 소제목에서 봐야 할 것

    @property
    def htmlTag(self) -> str:
        """HTML 태그명 (h3 또는 h4)."""
        return "h3" if self.level == 1 else "h4"

    @property
    def markdownPrefix(self) -> str:
        """마크다운 heading prefix (### 또는 ####)."""
        return "###" if self.level == 1 else "####"


@dataclass
class TableBlock:
    """Polars DataFrame 테이블 블록."""

    label: str
    df: object  # pl.DataFrame
    caption: str = ""


@dataclass
class FlagBlock:
    """경고/기회 플래그 블록."""

    flags: list[str]
    kind: str = "warning"  # warning | opportunity

    @property
    def icon(self) -> str:
        """플래그 아이콘 (warning=⚠, opportunity=✦)."""
        return "\u26a0" if self.kind == "warning" else "\u2726"


@dataclass
class MetricBlock:
    """핵심 지표 블록 (라벨: 값 형태)."""

    metrics: list[tuple[str, str]]  # [(라벨, 값), ...]


Block = TextBlock | HeadingBlock | TableBlock | FlagBlock | MetricBlock
