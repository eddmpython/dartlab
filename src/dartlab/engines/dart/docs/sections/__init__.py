"""사업보고서 섹션 구조화 모듈."""

from dartlab.engines.dart.docs.sections.extractors import (
    ParsedSubtopicTable,
    TopicSubtables,
    parseSubtopicTable,
    topicSubtables,
)
from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.types import (
    SectionChunk,
    SectionResult,
    YearSections,
)
from dartlab.engines.dart.docs.sections._common import sortPeriods
from dartlab.engines.dart.docs.sections.views import (
    buildMarkdownBlocks,
    buildMarkdownWide,
    contextSlices,
    retrievalBlocks,
)

__all__ = [
    "sections",
    "retrievalBlocks",
    "contextSlices",
    "buildMarkdownBlocks",
    "buildMarkdownWide",
    "topicSubtables",
    "TopicSubtables",
    "parseSubtopicTable",
    "ParsedSubtopicTable",
    "sortPeriods",
    "SectionChunk",
    "SectionResult",
    "YearSections",
]
