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
class EnrichedFlag:
    """정밀도·기저율 등 진단 메타를 포함하는 구조화된 플래그."""

    code: str  # "BENEISH_MANIPULATOR", "ALTMAN_DISTRESS" 등
    message: str  # 사용자 표시 메시지
    precision: float | None = None  # 모델 정밀도 (0~1)
    baseRate: str = ""  # 모델 학습 표본 설명
    reference: str = ""  # 학술 출처
    sectorNote: str = ""  # 업종별 주의사항


@dataclass
class FlagBlock:
    """경고/기회 플래그 블록."""

    flags: list[str]
    kind: str = "warning"  # warning | opportunity
    enrichedFlags: list[EnrichedFlag] | None = None  # 구조화된 플래그 (하위호환)

    @property
    def icon(self) -> str:
        """플래그 아이콘 (warning=⚠, opportunity=✦)."""
        return "\u26a0" if self.kind == "warning" else "\u2726"


@dataclass
class MetricBlock:
    """핵심 지표 블록 (라벨: 값 형태)."""

    metrics: list[tuple[str, str]]  # [(라벨, 값), ...]


Block = TextBlock | HeadingBlock | TableBlock | FlagBlock | MetricBlock
