"""사업보고서 섹션 구조화 모듈."""

from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.types import (
    SectionChunk,
    SectionResult,
    YearSections,
)
from dartlab.engines.dart.docs.sections.views import (
    buildMarkdownBlocks,
    buildMarkdownWide,
    contextSlices,
    retrievalBlocks,
    sortPeriods,
)

__all__ = [
    "sections",
    "retrievalBlocks",
    "contextSlices",
    "buildMarkdownBlocks",
    "buildMarkdownWide",
    "sortPeriods",
    "SectionChunk",
    "SectionResult",
    "YearSections",
]
