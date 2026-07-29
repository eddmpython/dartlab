"""DataEntry — report 카테고리 진입점 (Cut 8 분할).

단일 진실의 원천은 list 자체. 로직은 ``core/registry.py``.

docs 농장 은퇴 — 정형 비재무 report 토픽(fsSummary/segments/dividend/majorHolder/employee/
executive/audit/boardOfDirectors/sanction/relatedPartyTx/… ~35종)은 panel(c.panel raw 공시
검색)이 단일 표면(§영구소실). finance 통계표(BS/IS/CF, requires="finance") 만 생존.
"""

from __future__ import annotations

from dartlab.core.dataEntry import ColumnMeta, DataEntry  # noqa: F401

_REPORT_ENTRIES: list[DataEntry] = [
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
        columns=(ColumnMeta("항목", "K-IFRS 재무상태표 계정과목 (snakeId → 한글명)"),),
        analysisHints=(
            "부채비율(부채총계/자본총계) 추이",
            "유동비율(유동자산/유동부채) 확인",
            "자산 구성 변화 (유형 vs 무형 비중)",
            "IFRS 16 리스부채 영향 고려",
        ),
        relatedModules=("IS", "CF"),
        maxRows=50,
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
        columns=(ColumnMeta("항목", "K-IFRS 손익계산서 계정과목 (snakeId → 한글명)"),),
        analysisHints=(
            "매출 성장률(YoY) 계산",
            "영업이익률(영업이익/매출액) 추이",
            "순이익률(당기순이익/매출액) 추이",
            "매출원가율 변동 확인",
        ),
        relatedModules=("BS", "CF"),
        maxRows=50,
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
        columns=(ColumnMeta("항목", "K-IFRS 현금흐름표 계정과목 (snakeId → 한글명)"),),
        analysisHints=(
            "영업활동CF가 양수인지 확인 (음수 = 위험)",
            "FCF = 영업활동CF - 자본적지출",
            "재무활동CF로 차입/상환 패턴 파악",
            "영업CF > 순이익이면 이익의 질 양호",
        ),
        relatedModules=("BS", "IS"),
        maxRows=50,
    ),
]
