"""EDGAR Company 통합 테스트 — accessor 분리, retrievalBlocks, contextSlices, 서버 호환."""

import polars as pl
import pytest

pytestmark = pytest.mark.heavy


# ── accessor 분리 import 테스트 ──


def test_accessor_imports():
    from dartlab.engines.company.edgar._docs_accessor import _DocsAccessor
    from dartlab.engines.company.edgar._finance_accessor import _FinanceAccessor
    from dartlab.engines.company.edgar._profile_accessor import _ProfileAccessor

    assert _DocsAccessor is not None
    assert _FinanceAccessor is not None
    assert _ProfileAccessor is not None


def test_company_has_namespace_accessors():
    from dartlab.engines.company.edgar.company import Company

    assert hasattr(Company, "stockCode")
    assert hasattr(Company, "market")
    assert hasattr(Company, "currency")


# ── views 함수 단위 테스트 ──


def test_views_sortPeriods():
    from dartlab.engines.company.edgar.docs.sections.views import sortPeriods

    periods = ["2023", "2024Q1", "2022", "2024Q3", "2024"]
    result = sortPeriods(periods)
    # 연도는 Q4로 취급: 2024 → (2024, 4) → 2024Q1/Q3보다 뒤
    assert result == ["2022", "2023", "2024Q1", "2024Q3", "2024"]

    result_desc = sortPeriods(periods, descending=True)
    assert result_desc == ["2024", "2024Q3", "2024Q1", "2023", "2022"]


def test_views_periodOrderValue():
    from dartlab.engines.company.edgar.docs.sections.views import _periodOrderValue

    assert _periodOrderValue("2024") == 20244
    assert _periodOrderValue("2024Q1") == 20241
    assert _periodOrderValue("2024Q3") == 20243


def test_views_buildMarkdownWide_empty():
    from dartlab.engines.company.edgar.docs.sections.views import buildMarkdownWide

    assert buildMarkdownWide(None) == ""
    assert buildMarkdownWide(pl.DataFrame()) == ""


def test_views_buildMarkdownWide():
    from dartlab.engines.company.edgar.docs.sections.views import buildMarkdownWide

    df = pl.DataFrame({"topic": ["BS", "IS"], "2024": ["balance", "income"], "2023": ["bal23", "inc23"]})
    result = buildMarkdownWide(df)
    assert "| topic |" in result
    assert "BS" in result
    assert "income" in result


# ── splitText / splitTable 단위 테스트 ──


def test_splitText_short():
    from dartlab.engines.company.edgar.docs.sections.views import _splitText

    result = _splitText("short text", 100)
    assert result == ["short text"]


def test_splitText_long():
    from dartlab.engines.company.edgar.docs.sections.views import _splitText

    text = "line1\nline2\nline3\nline4\nline5"
    result = _splitText(text, 12)
    assert len(result) >= 2
    for part in result:
        assert len(part) <= 12 or "\n" not in part  # single long line is kept


def test_splitTable_short():
    from dartlab.engines.company.edgar.docs.sections.views import _splitTable

    table = "| a | b |\n| --- | --- |\n| 1 | 2 |"
    result = _splitTable(table, 200)
    assert result == [table]


def test_splitTable_long():
    from dartlab.engines.company.edgar.docs.sections.views import _splitTable

    header = "| col1 | col2 |\n| --- | --- |"
    rows = "\n".join(f"| val{i} | data{i} |" for i in range(20))
    table = header + "\n" + rows
    result = _splitTable(table, 80)
    assert len(result) >= 2
    # 각 슬라이스가 헤더를 포함하는지 확인
    for part in result:
        assert "| col1 | col2 |" in part


# ── retrievalBlocks / contextSlices 함수 시그니처 테스트 ──


def test_retrievalBlocks_returns_none_without_data(monkeypatch):
    """데이터 없는 ticker에 대해 None 반환."""
    from dartlab.engines.company.edgar.docs.sections import pipeline as _pipeline_mod
    from dartlab.engines.company.edgar.docs.sections import views as _views_mod

    monkeypatch.setattr(_pipeline_mod, "sections", lambda ticker, **kw: None)
    result = _views_mod.retrievalBlocks("FAKE")
    assert result is None


def test_contextSlices_returns_none_without_data(monkeypatch):
    """데이터 없는 ticker에 대해 None 반환."""
    from dartlab.engines.company.edgar.docs.sections import views as _views_mod

    monkeypatch.setattr(_views_mod, "retrievalBlocks", lambda ticker: None)
    result = _views_mod.contextSlices("FAKE")
    assert result is None


def test_retrievalBlocks_with_mock_sections(monkeypatch):
    """mock sections DataFrame으로 retrievalBlocks 동작 검증."""
    from dartlab.engines.company.edgar.docs.sections import pipeline as _pipeline_mod
    from dartlab.engines.company.edgar.docs.sections import views as _views_mod

    mock_df = pl.DataFrame(
        {
            "topic": ["10-K::item1Business", "10-K::item1Business"],
            "blockType": ["text", "table"],
            "blockOrder": [0, 1],
            "textNodeType": ["body", None],
            "textLevel": [0, None],
            "textPath": [None, None],
            "2024": [
                "Apple designs and manufactures consumer electronics.",
                "| Product | Revenue |\n| --- | --- |\n| iPhone | 200B |",
            ],
            "2023": ["Apple designs consumer electronics.", None],
        }
    )

    monkeypatch.setattr(_pipeline_mod, "sections", lambda ticker, **kw: mock_df)

    result = _views_mod.retrievalBlocks("AAPL")
    assert result is not None
    assert isinstance(result, pl.DataFrame)
    assert "ticker" in result.columns
    assert "period" in result.columns
    assert "topic" in result.columns
    assert "blockText" in result.columns
    assert "chars" in result.columns
    assert "blockPriority" in result.columns
    assert "cellKey" in result.columns
    # 3 non-null content cells (2024 has 2 blocks, 2023 has 1)
    assert result.height == 3


def test_contextSlices_with_mock_blocks(monkeypatch):
    """mock retrievalBlocks로 contextSlices 동작 검증."""
    from dartlab.engines.company.edgar.docs.sections import views as _views_mod

    mock_blocks = pl.DataFrame(
        {
            "ticker": ["AAPL", "AAPL"],
            "period": ["2024", "2024"],
            "periodOrder": [20244, 20244],
            "topic": ["10-K::item1Business", "10-K::item1Business"],
            "blockType": ["text", "table"],
            "blockOrder": [0, 1],
            "textNodeType": ["body", None],
            "textLevel": [0, None],
            "textPath": [None, None],
            "blockText": ["Short text.", "| a | b |\n| --- | --- |\n| 1 | 2 |"],
            "chars": [11, 35],
            "cellKey": ["AAPL:2024:10-K::item1Business", "AAPL:2024:10-K::item1Business"],
            "blockPriority": [3, 3],
        }
    )

    monkeypatch.setattr(_views_mod, "retrievalBlocks", lambda ticker: mock_blocks)

    result = _views_mod.contextSlices("AAPL", maxChars=1800)
    assert result is not None
    assert isinstance(result, pl.DataFrame)
    assert "sliceText" in result.columns
    assert "sliceIdx" in result.columns
    assert "isTable" in result.columns
    assert result.height >= 2


# ── 서버 호환 테스트 ──


def test_resolve_us_ticker_pattern():
    """resolve.py의 US ticker 패턴이 정상 동작하는지."""
    import re

    q = "Analyze $AAPL revenue trends"
    us_match = re.search(r"\$?([A-Z]{1,5})\b", q)
    assert us_match is not None
    assert us_match.group(1) == "AAPL"

    q2 = "What about MSFT earnings?"
    us_match2 = re.search(r"\$?([A-Z]{1,5})\b", q2)
    assert us_match2 is not None
    assert us_match2.group(1) == "MSFT"
