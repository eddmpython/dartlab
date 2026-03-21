import pytest

pytestmark = pytest.mark.unit

import importlib

import polars as pl

from dartlab.engines.dart.docs.sections.views import contextSlices


def test_sections_pipeline_preserves_markdown_tables_and_period_order(monkeypatch):
    pipeline = importlib.import_module("dartlab.engines.dart.docs.sections.pipeline")

    df = pl.DataFrame(
        {
            "year": ["2024", "2024", "2024", "2024", "2024", "2024"],
            "report_kind": ["annual", "annual", "annual", "Q1", "Q1", "Q1"],
            "section_order": [0, 1, 2, 0, 1, 2],
            "section_title": [
                "II. 사업의 내용",
                "4. 매출 및 수주상황",
                "6. 주요계약 및 연구개발활동",
                "II. 사업의 내용",
                "4. 매출 및 수주상황",
                "6. 주요계약 및 연구개발활동",
            ],
            "section_content": [
                "연간 사업의 내용",
                "| 구분 | 금액 |\n| --- | --- |\n| 국내 | 100 |",
                "연간 연구개발 설명",
                "분기 사업의 내용",
                "| 구분 | 금액 |\n| --- | --- |\n| 국내 | 25 |",
                "분기 연구개발 설명",
            ],
        }
    )

    def fakeLoadData(stockCode: str):
        return df

    def fakeSelectReport(frame: pl.DataFrame, year: str, reportKind: str):
        subset = frame.filter((pl.col("year") == year) & (pl.col("report_kind") == reportKind))
        return subset if subset.height > 0 else None

    monkeypatch.setattr(pipeline, "loadData", fakeLoadData)
    monkeypatch.setattr(pipeline, "selectReport", fakeSelectReport)

    result = pipeline.sections("TEST")

    assert result is not None
    assert "blockOrder" in result.columns
    periodCols = [c for c in result.columns if c.startswith("20")]
    assert periodCols == ["2024Q1", "2024"]
    sales = result.filter(pl.col("topic") == "salesOrder").row(0, named=True)
    assert "| 구분 | 금액 |" in sales["2024"]
    assert "| 국내 | 25 |" in sales["2024Q1"]


def test_sections_pipeline_preserves_multiple_blocks_within_same_topic(monkeypatch):
    pipeline = importlib.import_module("dartlab.engines.dart.docs.sections.pipeline")

    df = pl.DataFrame(
        {
            "year": ["2024", "2024", "2025", "2025"],
            "report_kind": ["annual", "annual", "annual", "annual"],
            "section_order": [0, 1, 0, 1],
            "section_title": [
                "II. 사업의 내용",
                "1. 회사의 개요",
                "II. 사업의 내용",
                "1. 회사의 개요",
            ],
            "section_content": [
                "사업 개요",
                "첫 문단\n| 구분 | 값 |\n| --- | --- |\n| A | 1 |\n둘째 문단",
                "사업 개요",
                "첫 문단 수정\n| 구분 | 값 |\n| --- | --- |\n| A | 2 |\n둘째 문단 수정",
            ],
        }
    )

    def fakeLoadData(stockCode: str):
        return df

    def fakeSelectReport(frame: pl.DataFrame, year: str, reportKind: str):
        subset = frame.filter((pl.col("year") == year) & (pl.col("report_kind") == reportKind))
        return subset if subset.height > 0 else None

    monkeypatch.setattr(pipeline, "loadData", fakeLoadData)
    monkeypatch.setattr(pipeline, "selectReport", fakeSelectReport)

    result = pipeline.sections("TEST")

    assert result is not None
    overview = result.filter(pl.col("topic") == "companyOverview").sort("blockOrder")
    assert overview.height >= 3
    types = overview["blockType"].to_list()
    assert "text" in types
    assert "table" in types
    tables = overview.filter(pl.col("blockType") == "table")
    assert tables.height >= 1
    assert "| A | 2 |" in tables.item(0, "2025")
    assert "둘째 문단 수정" in overview.item(2, "2025")


def test_sections_pipeline_hides_detail_topics_from_core_view(monkeypatch):
    pipeline = importlib.import_module("dartlab.engines.dart.docs.sections.pipeline")

    df = pl.DataFrame(
        {
            "year": ["2024", "2024", "2024"],
            "report_kind": ["annual", "annual", "annual"],
            "section_order": [0, 1, 2],
            "section_title": [
                "III. 재무에 관한 사항",
                "1. 재고자산명세서",
                "2. 개별재무제표에관한사항",
            ],
            "section_content": [
                "재무 개요",
                "| 항목 | 값 |\n| --- | --- |\n| 재고 | 100 |",
                "| 항목 | 값 |\n| --- | --- |\n| 자산 | 200 |",
            ],
        }
    )

    def fakeLoadData(stockCode: str):
        return df

    def fakeSelectReport(frame: pl.DataFrame, year: str, reportKind: str):
        subset = frame.filter((pl.col("year") == year) & (pl.col("report_kind") == reportKind))
        return subset if subset.height > 0 else None

    monkeypatch.setattr(pipeline, "loadData", fakeLoadData)
    monkeypatch.setattr(pipeline, "selectReport", fakeSelectReport)

    result = pipeline.sections("TEST")

    assert result is not None
    assert result.filter(pl.col("topic") == "재고자산명세서").height == 0
    assert result.filter(pl.col("topic") == "개별재무제표에관한사항").height == 0


def test_context_slices_skip_placeholder_blocks(monkeypatch):
    views = importlib.import_module("dartlab.engines.dart.docs.sections.views")
    fake = pl.DataFrame(
        {
            "stockCode": ["TEST", "TEST"],
            "period": ["2024Q1", "2024Q1"],
            "periodOrder": [20241, 20241],
            "sectionOrder": [1, 2],
            "rawTitle": ["companyOverview", "salesOrder"],
            "topic": ["companyOverview", "salesOrder"],
            "sourceTopic": ["companyOverview", "salesOrder"],
            "cellKey": ["TEST:2024Q1:companyOverview", "TEST:2024Q1:salesOrder"],
            "blockIdx": [0, 0],
            "blockType": ["text", "text"],
            "blockLabel": ["(root)", "(root)"],
            "blockText": [
                "기업공시서식 작성기준에 따라 분기보고서에 기재하지 않습니다.",
                "매출은 100입니다.",
            ],
            "chars": [30, 10],
            "tableLines": [0, 0],
            "semanticTopic": [None, None],
            "detailTopic": [None, None],
            "isBoilerplate": [False, False],
            "isPlaceholder": [True, False],
            "blockPriority": [0, 3],
        },
        strict=False,
    )

    def fakeRetrievalBlocks(stockCode: str):
        return fake

    monkeypatch.setattr(views, "retrievalBlocks", fakeRetrievalBlocks)

    result = contextSlices("TEST")

    assert result.height == 1
    assert result.get_column("topic").to_list() == ["salesOrder"]
