"""review 섹션."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from dartlab.review.blocks import Block

if TYPE_CHECKING:
    from dartlab.review.narrative import NarrativeThread


@dataclass
class Section:
    """분석 리뷰의 한 섹션 (목차 1항목 = 1섹션)."""

    key: str  # "수익구조", "자금구조" 등
    partId: str  # "1-1", "1-2" 등
    title: str  # 표시용 제목
    blocks: list[Block] = field(default_factory=list)
    helper: str = ""  # 이 섹션에서 봐야 할 것 (헬퍼 텍스트)
    aiOpinion: str = ""  # AI 종합의견 (reviewer에서 섹션별로 채움)
    aiGuide: str = ""  # AI에게 전달할 섹션별 분석 관점
    threads: list[NarrativeThread] = field(default_factory=list)  # 섹션 간 인과 연결
    summary: str = ""  # 이 섹션의 1-2줄 핵심 요약 (detail=False 시 이것만 표시)
