import polars as pl

from dartlab.engines.dart.docs.sections.artifacts import (
    loadProjectionRules,
    loadSectionProfileTable,
)
from dartlab.engines.dart.docs.sections.runtime import (
    applyProjections,
    chapterTeacherTopics,
    detailTopicForBlock,
    detailTopicForTopic,
    extractSemanticUnits,
    semanticTopicForBlock,
    semanticTopicForLabel,
)
from dartlab.engines.dart.docs.sections._common import (
    periodOrderValue,
    periodSortKey,
    sortPeriods,
)
from dartlab.engines.dart.docs.sections.views import (
    blockPriority,
    isBoilerplateTopic,
    isPlaceholderBlock,
    splitContextText,
    splitMarkdownTable,
)


def test_load_projection_rules_from_packaged_data():
    rules = loadProjectionRules("chapterII")
    assert rules["매출에관한사항"] == ["salesOrder"]
    assert rules["연구개발활동"] == ["majorContractsAndRnd"]


def test_load_section_profile_table_from_packaged_data():
    df = loadSectionProfileTable()
    assert isinstance(df, pl.DataFrame)
    assert df is not None
    assert "topic" in df.columns
    assert df.height > 0


def test_apply_projections_direct_and_split_rules():
    teacher = chapterTeacherTopics(
        [
            {"chapter": "II", "topic": "salesOrder"},
            {"chapter": "II", "topic": "majorContractsAndRnd"},
            {"chapter": "II", "topic": "productService"},
            {"chapter": "II", "topic": "rawMaterial"},
        ]
    )
    rows = [
        {
            "chapter": "II",
            "topic": "매출에관한사항",
            "text": "매출실적 본문",
            "majorNum": 2,
            "orderSeq": 10,
        },
        {
            "chapter": "II",
            "topic": "연구개발활동",
            "text": "연구개발 본문",
            "majorNum": 2,
            "orderSeq": 11,
        },
        {
            "chapter": "II",
            "topic": "주요제품및원재료등",
            "text": "가. 주요 제품\n제품 설명\n나. 원재료\n원재료 설명",
            "majorNum": 2,
            "orderSeq": 12,
        },
    ]

    projected = applyProjections(rows, teacher)
    by_topic = {row["topic"]: row for row in projected}

    assert by_topic["salesOrder"]["text"] == "매출실적 본문"
    assert by_topic["majorContractsAndRnd"]["text"] == "연구개발 본문"
    assert "제품 설명" in by_topic["productService"]["text"]
    assert "원재료 설명" in by_topic["rawMaterial"]["text"]


def test_extract_semantic_units_for_segment_and_risk_topics():
    text = "가. 반도체\n설명 A\n나. 디스플레이\n설명 B"
    units = extractSemanticUnits("segmentOverview", text)
    assert units == [("가. 반도체", "설명 A"), ("나. 디스플레이", "설명 B")]
    assert extractSemanticUnits("companyOverview", text) == []


def test_semantic_topic_for_label_maps_segment_and_risk_labels():
    assert semanticTopicForLabel("segmentOverview", "가. 반도체") == "segmentSemiconductor"
    assert semanticTopicForLabel("segmentOverview", "나. 생활가전") == "segmentHomeAppliance"
    assert semanticTopicForLabel("riskDerivative", "가. 시장위험") == "marketRisk"
    assert semanticTopicForLabel("riskDerivative", "나. 환위험") == "fxRisk"
    assert semanticTopicForLabel("segmentSemiconductor", "(root)") == "segmentSemiconductor"


def test_semantic_topic_for_block_uses_table_row_labels():
    table = "| 구분 | 내용 |\n| --- | --- |\n| 시장위험 | 설명 |\n| 신용위험 | 설명 |"
    assert semanticTopicForBlock("riskDerivative", "(root)", "table", table) == "marketRisk"
    assert semanticTopicForBlock("auditSystem", "감사위원회", "text", "감사위원회 활동") == "auditSystem"
    assert detailTopicForTopic("재고자산명세서") == "noteInventoryDetail"
    assert detailTopicForTopic("법인세비용명세서") == "noteTaxDetail"
    assert detailTopicForTopic("개별재무제표에관한사항") == "noteSeparateFinancialStatementsDetail"
    assert detailTopicForBlock("financialNotes", "법인세등명세서", "법인세", "text", "법인세 비용 설명") == "noteTaxDetail"
    assert detailTopicForBlock("audit", "감사인의보수등에관한사항", "감사보수", "table", "| 항목 | 값 |\n| --- | --- |\n| 감사보수 | 1 |") == "auditFeeDetail"
    assert detailTopicForBlock("productService", "(하나은행)예금업무(상세)", "(root)", "text", "예금 상품 설명") == "bankDepositProductDetail"
    assert detailTopicForBlock("productService", "(하나은행)신탁업무(상세)", "(root)", "text", "신탁 상품 설명") == "trustBusinessDetail"
    assert detailTopicForBlock("productService", "(하나저축은행)상품및서비스개요(상세)", "(root)", "text", "상품 설명") == "financialProductOverviewDetail"
    assert detailTopicForBlock("riskDerivative", "(하나증권)신용파생상품상세명세(상세)", "(root)", "text", "파생 상품 설명") == "derivativeProductDetail"
    assert detailTopicForBlock("intellectualProperty", "지적재산권보유현황(에코프로머티리얼즈)", "(root)", "text", "특허 보유 현황") == "ipPortfolioDetail"
    assert detailTopicForBlock("salesOrder", "수주상황(상세)", "(root)", "text", "수주 잔고") == "orderBacklogDetail"
    assert detailTopicForBlock("majorContractsAndRnd", "연구개발실적(에코프로머티리얼즈)", "(root)", "text", "개발 내역") == "rndPortfolioDetail"
    assert detailTopicForBlock("majorContractsAndRnd", "경영상의주요계약(상세)", "(root)", "text", "계약 내역") == "majorContractDetail"
    assert detailTopicForTopic("salesOrder") is None


def test_period_sorting_orders_time_series_ascending():
    periods = ["2024Q1", "2025", "2024", "2025Q3", "2025Q1", "2025Q2"]
    assert sortPeriods(periods) == ["2024Q1", "2024", "2025Q1", "2025Q2", "2025Q3", "2025"]
    assert periodSortKey("2024") > periodSortKey("2024Q3")
    assert periodOrderValue("2025Q3") == 20253


def test_split_context_text_preserves_short_chunks():
    parts = splitContextText("a\nb\nc", 3)
    assert parts == ["a\nb", "c"]


def test_split_markdown_table_preserves_headers():
    text = "\n".join(
        [
            "| 항목 | 값 |",
            "| --- | --- |",
            "| A | 1 |",
            "| B | 2 |",
            "| C | 3 |",
        ]
    )
    parts = splitMarkdownTable(text, 28)
    assert len(parts) >= 2
    assert parts[0].startswith("| 항목 | 값 |")
    assert parts[1].startswith("| 항목 | 값 |")


def test_block_priority_and_boilerplate():
    assert isBoilerplateTopic("사업보고서") is True
    assert isBoilerplateTopic("salesOrder") is False
    assert isPlaceholderBlock("기업공시서식 작성기준에 따라 분기보고서에 기재하지 않습니다.") is True
    assert blockPriority("text", None, "noteTaxDetail", False, False) == 5
    assert blockPriority("text", "marketRisk", None, False, False) == 4
    assert blockPriority("text", None, None, False, False) == 3
    assert blockPriority("table", None, None, True, False) == 0
    assert blockPriority("text", None, None, False, True) == 0
