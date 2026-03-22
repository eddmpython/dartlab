"""EDGAR docs sections 구조화 모듈."""

from dartlab.engines.company.edgar.docs.sections.artifacts import (
    loadCanonicalRows,
    loadCoverageSnapshot,
    loadTopicDrafts,
)
from dartlab.engines.company.edgar.docs.sections.pipeline import sections
from dartlab.engines.company.edgar.docs.sections.runtime import (
    FALLBACK_TOPIC_ID,
    SUPPORTED_FORM_TYPES,
    fallbackTopic,
    topicNamespace,
)
from dartlab.engines.company.edgar.docs.sections.views import buildMarkdownWide, sortPeriods, sortTopics

__all__ = [
    "sections",
    "sortPeriods",
    "sortTopics",
    "buildMarkdownWide",
    "topicNamespace",
    "fallbackTopic",
    "FALLBACK_TOPIC_ID",
    "SUPPORTED_FORM_TYPES",
    "loadCanonicalRows",
    "loadCoverageSnapshot",
    "loadTopicDrafts",
]
