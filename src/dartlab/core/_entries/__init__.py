"""L0 DataEntry 메타데이터 카탈로그 — 카테고리별 분할.

단일 진실의 원천은 각 카테고리 모듈의 불변 tuple이다. 본 모듈은 합산만 하며
Company/API 라우팅과 런타임 변경 로직은 소유하지 않는다.
"""

from __future__ import annotations

from dartlab.core._entries.analysis import _ANALYSIS_ENTRIES
from dartlab.core._entries.disclosure import _DISCLOSURE_ENTRIES
from dartlab.core._entries.finance import _FINANCE_ENTRIES
from dartlab.core._entries.notes import _NOTES_ENTRIES
from dartlab.core._entries.raw import _RAW_ENTRIES
from dartlab.core._entries.report import _REPORT_ENTRIES
from dartlab.core.dataEntry import DataEntry

_ENTRIES: tuple[DataEntry, ...] = (
    *_FINANCE_ENTRIES,
    *_REPORT_ENTRIES,
    *_DISCLOSURE_ENTRIES,
    *_NOTES_ENTRIES,
    *_RAW_ENTRIES,
    *_ANALYSIS_ENTRIES,
)
