"""사업보고서 섹션 구조화 모듈."""

from dartlab.engines.dart.docs.sections._common import (
    displayPeriod,
    formatPeriodRange,
    periodColumns,
    rawPeriod,
    reorderPeriodColumns,
    sortPeriods,
)
from dartlab.engines.dart.docs.sections.extractors import (
    ParsedSubtopicTable,
    TopicSubtables,
    parseSubtopicTable,
    topicSubtables,
)
from dartlab.engines.dart.docs.sections.pipeline import (
    projectCadenceRows,
    sections,
    semanticCollisions,
    semanticRegistry,
    structureCollisions,
    structureEvents,
    structureRegistry,
)
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
)

__all__ = [
    "sections",
    "projectCadenceRows",
    "structureRegistry",
    "structureCollisions",
    "structureEvents",
    "semanticRegistry",
    "semanticCollisions",
    "retrievalBlocks",
    "contextSlices",
    "buildMarkdownBlocks",
    "buildMarkdownWide",
    "topicSubtables",
    "TopicSubtables",
    "parseSubtopicTable",
    "ParsedSubtopicTable",
    "sortPeriods",
    "rawPeriod",
    "displayPeriod",
    "periodColumns",
    "formatPeriodRange",
    "reorderPeriodColumns",
    "SectionChunk",
    "SectionResult",
    "YearSections",
]
