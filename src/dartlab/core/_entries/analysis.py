"""DataEntry — analysis 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.
"""

from __future__ import annotations

from dartlab.core.dataEntry import DataEntry

_ANALYSIS_ENTRIES: tuple[DataEntry, ...] = (
    # analysis — L2 분석 엔진
    # ═══════════════════════════════════════════════════════
    DataEntry(
        name="ratios",
        label="재무비율",
        category="analysis",
        dataType="ratios",
        description="financeEngine이 자동계산한 수익성·안정성·밸류에이션 비율.",
        requires="finance",
        unit="%",
    ),
    DataEntry(
        name="insight",
        label="인사이트",
        category="analysis",
        dataType="custom",
        description="7영역 A~F 등급 분석 (실적, 수익성, 건전성, 현금흐름, 지배구조, 리스크, 기회).",
        requires="finance",
    ),
    DataEntry(
        name="sector",
        label="섹터분류",
        category="analysis",
        dataType="custom",
        description="WICS 11대 섹터 분류. 대분류/중분류 + 섹터별 파라미터.",
    ),
    DataEntry(
        name="rank",
        label="시장순위",
        category="analysis",
        dataType="custom",
        description="전체 시장 및 섹터 내 매출/자산/성장률 순위.",
        requires="finance",
    ),
    DataEntry(
        name="keywordTrend",
        label="키워드 트렌드",
        category="analysis",
        dataType="dataframe",
        description="공시 텍스트 키워드 빈도 추이 (topic × period × keyword). 54개 내장 키워드 또는 사용자 지정.",
        requires="panel",
    ),
    DataEntry(
        name="news",
        label="뉴스",
        category="analysis",
        dataType="dataframe",
        description="최근 뉴스 수집 (KR: Google News 한국어, US: Google News 영어). 날짜/제목/출처/URL.",
    ),
)
