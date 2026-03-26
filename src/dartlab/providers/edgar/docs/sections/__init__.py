"""EDGAR docs sections 구조화 모듈."""

from dartlab.providers.edgar.docs.sections.artifacts import (
    loadCanonicalRows,
    loadCoverageSnapshot,
    loadTopicDrafts,
)
from dartlab.providers.edgar.docs.sections.pipeline import sections
from dartlab.providers.edgar.docs.sections.runtime import (
    FALLBACK_TOPIC_ID,
    SUPPORTED_FORM_TYPES,
    fallbackTopic,
    topicNamespace,
)
from dartlab.providers.edgar.docs.sections.views import buildMarkdownWide, sortPeriods, sortTopics

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
