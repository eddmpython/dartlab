"""DataEntry — notes 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.
"""

from __future__ import annotations

from dartlab.core.dataEntry import ColumnMeta, DataEntry  # noqa: F401

_NOTES_ENTRIES: list[DataEntry] = [
    # notes — K-IFRS 주석
    # ═══════════════════════════════════════════════════════
    # Q1.2 (2026-04-21): notes entry 에 notesDispatch + extractor 추가 — notes.py 의
    # _NOTES_DISPATCH 하드코딩 제거 목적. 이제 registry 가 dispatch 의 단일 출처.
    DataEntry(
        name="notes.receivables",
        label="매출채권",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 매출채권 주석. 채권 잔액 및 대손충당금 내역.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "매출채권"),
        requires="panel",
    ),
    DataEntry(
        name="notes.inventory",
        label="재고자산",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 재고자산 주석. 원재료/재공품/제품 내역별 금액.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "재고자산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.tangibleAsset",
        label="유형자산(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 유형자산 변동 주석. 토지, 건물, 기계 등 항목별 변동.",
        extractor=lambda r: r.movementDf,
        notesDispatch=("tangibleAsset", "유형자산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.intangibleAsset",
        label="무형자산",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 무형자산 주석. 영업권, 개발비 등 항목별 변동.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "무형자산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.investmentProperty",
        label="투자부동산",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 투자부동산 주석. 공정가치 및 변동 내역.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "투자부동산"),
        requires="panel",
    ),
    DataEntry(
        name="notes.affiliates",
        label="관계기업(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 관계기업 투자 주석. 지분법 적용 내역.",
        extractor=lambda r: r.movementDf,
        notesDispatch=("affiliate", "관계기업"),
        requires="panel",
    ),
    DataEntry(
        name="notes.borrowings",
        label="차입금",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 차입금 주석. 단기/장기 차입 잔액 및 이자율.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "차입금"),
        requires="panel",
    ),
    DataEntry(
        name="notes.provisions",
        label="충당부채",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 충당부채 주석. 판매보증, 소송, 복구 등.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "충당부채"),
        requires="panel",
    ),
    DataEntry(
        name="notes.eps",
        label="주당이익",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 주당이익 주석. 기본/희석 EPS 계산 내역.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "주당이익"),
        requires="panel",
    ),
    DataEntry(
        name="notes.lease",
        label="리스",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 리스 주석. 사용권자산, 리스부채 내역.",
        extractor=lambda r: r.tableDf,
        notesDispatch=("notesDetail", "리스"),
        requires="panel",
    ),
    DataEntry(
        name="notes.segments",
        label="부문정보(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 부문정보 주석. 사업부문별 상세 데이터.",
        extractor=lambda r: r.revenue,
        notesDispatch=("segments", "부문정보"),
        requires="panel",
    ),
    DataEntry(
        name="notes.costByNature",
        label="비용의성격별분류(주석)",
        category="notes",
        dataType="dataframe",
        description="K-IFRS 비용의 성격별 분류 주석.",
        extractor=lambda r: r.timeSeries,
        notesDispatch=("costByNature", "비용의성격별분류"),
        requires="panel",
    ),
    # ═══════════════════════════════════════════════════════
]
