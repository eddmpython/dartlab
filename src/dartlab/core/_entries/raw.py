"""DataEntry — raw 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.
"""

from __future__ import annotations

from dartlab.core.dataEntry import DataEntry

_RAW_ENTRIES: tuple[DataEntry, ...] = (
    # raw — 원본 parquet
    # ═══════════════════════════════════════════════════════
    DataEntry(
        name="rawFinance",
        label="XBRL 원본",
        category="raw",
        dataType="dataframe",
        description="XBRL 재무제표 원본 parquet. 매핑/정규화 전 원본 데이터.",
        requires="finance",
    ),
    DataEntry(
        name="rawReport",
        label="보고서 원본",
        category="raw",
        dataType="dataframe",
        description="정기보고서 API 원본 parquet. 파싱 전 원본 데이터.",
        requires="report",
    ),
    # ═══════════════════════════════════════════════════════
)
