"""DataEntry — finance 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.
"""

from __future__ import annotations

from dartlab.core.dataEntry import DataEntry

_FINANCE_ENTRIES: tuple[DataEntry, ...] = (
    # ═══════════════════════════════════════════════════════
    # finance — 시계열 재무제표
    # ═══════════════════════════════════════════════════════
    DataEntry(
        name="annual.IS",
        label="손익계산서(연도별)",
        category="finance",
        dataType="timeseries",
        description="연도별 손익계산서 시계열. 매출액, 영업이익, 순이익 등 전체 계정.",
        requires="finance",
    ),
    DataEntry(
        name="annual.BS",
        label="재무상태표(연도별)",
        category="finance",
        dataType="timeseries",
        description="연도별 재무상태표 시계열. 자산, 부채, 자본 전체 계정.",
        requires="finance",
    ),
    DataEntry(
        name="annual.CF",
        label="현금흐름표(연도별)",
        category="finance",
        dataType="timeseries",
        description="연도별 현금흐름표 시계열. 영업/투자/재무활동 현금흐름.",
        requires="finance",
    ),
    DataEntry(
        name="timeseries.IS",
        label="손익계산서(분기별)",
        category="finance",
        dataType="timeseries",
        description="분기별 손익계산서 standalone 시계열.",
        requires="finance",
    ),
    DataEntry(
        name="timeseries.BS",
        label="재무상태표(분기별)",
        category="finance",
        dataType="timeseries",
        description="분기별 재무상태표 시점잔액 시계열.",
        requires="finance",
    ),
    DataEntry(
        name="timeseries.CF",
        label="현금흐름표(분기별)",
        category="finance",
        dataType="timeseries",
        description="분기별 현금흐름표 standalone 시계열.",
        requires="finance",
    ),
)
