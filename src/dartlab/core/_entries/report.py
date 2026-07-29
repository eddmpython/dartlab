"""DataEntry — report 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.

docs 농장 은퇴 — 정형 비재무 report 토픽(fsSummary/segments/dividend/majorHolder/employee/
executive/audit/boardOfDirectors/sanction/relatedPartyTx/… ~35종)은 panel(c.panel raw 공시
검색)이 단일 표면(§영구소실). finance 통계표(BS/IS/CF, requires="finance") 만 생존.
"""

from __future__ import annotations

from dartlab.core.dataEntry import DataEntry

_REPORT_ENTRIES: tuple[DataEntry, ...] = (
    # ═══════════════════════════════════════════════════════
    # report — 재무제표 (finance XBRL — docs 농장 은퇴 후 단일 소스)
    # ═══════════════════════════════════════════════════════
    DataEntry(
        name="BS",
        label="재무상태표",
        category="report",
        dataType="dataframe",
        description="K-IFRS 연결 재무상태표. finance XBRL 정규화(snakeId) 기반, 회사간 비교 가능.",
        extractor=None,
        requires="finance",
        unit="원",
    ),
    DataEntry(
        name="IS",
        label="손익계산서",
        category="report",
        dataType="dataframe",
        description="K-IFRS 연결 손익계산서. finance XBRL 정규화 기반. 매출액, 영업이익, 순이익 등 전체 계정 포함.",
        extractor=None,
        requires="finance",
        unit="원",
    ),
    DataEntry(
        name="CF",
        label="현금흐름표",
        category="report",
        dataType="dataframe",
        description="K-IFRS 연결 현금흐름표. finance XBRL 정규화 기반. 영업/투자/재무활동 현금흐름.",
        extractor=None,
        requires="finance",
        unit="원",
    ),
)
