"""show.py 공통 헬퍼 단위 테스트.

isPeriodColumn, transposeToVertical, normalizeItemKey,
selectFromShow, buildBlockIndex, _cascadeFilterRows.
데이터 로드 없음, Polars DataFrame mock 사용.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── isPeriodColumn ──


def test_is_period_column_year():
    from dartlab.core.show import isPeriodColumn

    assert isPeriodColumn("2024") is True
    assert isPeriodColumn("2023") is True
    assert isPeriodColumn("1999") is True


def test_is_period_column_quarter():
    from dartlab.core.show import isPeriodColumn

    assert isPeriodColumn("2024Q1") is True
    assert isPeriodColumn("2024Q4") is True
    assert isPeriodColumn("2023Q2") is True


def test_is_period_column_rejects_non_period():
    from dartlab.core.show import isPeriodColumn

    assert isPeriodColumn("계정명") is False
    assert isPeriodColumn("account") is False
    assert isPeriodColumn("2024Q5") is False
    assert isPeriodColumn("Q4") is False
    assert isPeriodColumn("") is False
    assert isPeriodColumn("20241") is False


def test_is_period_column_rejects_partial():
    from dartlab.core.show import isPeriodColumn

    assert isPeriodColumn("202") is False
    assert isPeriodColumn("20240") is False


# ── normalizeItemKey ──


def test_normalize_item_key_basic():
    from dartlab.core.show import normalizeItemKey

    assert normalizeItemKey("매출액") == "매출액"


def test_normalize_item_key_strips_whitespace():
    from dartlab.core.show import normalizeItemKey

    assert normalizeItemKey("매 출 액") == "매출액"
    assert normalizeItemKey("  매출액  ") == "매출액"


def test_normalize_item_key_html_entities():
    from dartlab.core.show import normalizeItemKey

    assert normalizeItemKey("매출&amp;이익") == "매출&이익"


def test_normalize_item_key_nfkc():
    from dartlab.core.show import normalizeItemKey

    # fullwidth A → normal A
    assert normalizeItemKey("Ａ") == "a"


def test_normalize_item_key_removes_cr_nbsp():
    from dartlab.core.show import normalizeItemKey

    assert normalizeItemKey("매출&cr;액") == "매출액"
    assert normalizeItemKey("매출&nbsp;액") == "매출액"


def test_normalize_item_key_lowercase():
    from dartlab.core.show import normalizeItemKey

    assert normalizeItemKey("Sales") == "sales"
    assert normalizeItemKey("ROE") == "roe"


# ── transposeToVertical ──


def test_transpose_to_vertical_basic():
    from dartlab.core.show import transposeToVertical

    wide = pl.DataFrame(
        {
            "계정명": ["매출액", "영업이익"],
            "2022": [100, 10],
            "2023": [200, 20],
            "2024": [300, 30],
        }
    )
    result = transposeToVertical(wide, ["2023", "2024"])
    assert result is not None
    assert result.columns == ["계정명", "2023", "2024"]
    assert result.height == 2


def test_transpose_to_vertical_q4_fallback():
    """연도 요청 시 Q4 컬럼으로 fallback."""
    from dartlab.core.show import transposeToVertical

    wide = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "2023Q4": [100],
            "2024Q4": [200],
        }
    )
    result = transposeToVertical(wide, ["2023", "2024"])
    assert result is not None
    assert "2023Q4" in result.columns
    assert "2024Q4" in result.columns


def test_transpose_to_vertical_no_match():
    from dartlab.core.show import transposeToVertical

    wide = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "2022": [100],
        }
    )
    result = transposeToVertical(wide, ["2025"])
    assert result is None


def test_transpose_to_vertical_preserves_meta():
    """meta 컬럼(비-기간)이 보존된다."""
    from dartlab.core.show import transposeToVertical

    wide = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "코드": ["S001"],
            "2023": [100],
            "2024": [200],
        }
    )
    result = transposeToVertical(wide, ["2024"])
    assert result is not None
    assert "계정명" in result.columns
    assert "코드" in result.columns
    assert "2024" in result.columns
    assert "2023" not in result.columns


# ── selectFromShow ──


def test_select_from_show_row_filter():
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame(
        {
            "계정명": ["매출액", "영업이익", "당기순이익"],
            "2023": [100, 10, 5],
            "2024": [200, 20, 10],
        }
    )
    result = selectFromShow(df, indList=["매출액", "영업이익"])
    assert result is not None
    assert result.height == 2
    assert "당기순이익" not in result["계정명"].to_list()


def test_select_from_show_col_filter():
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "2022": [50],
            "2023": [100],
            "2024": [200],
        }
    )
    result = selectFromShow(df, colList=["2024"])
    assert result is not None
    assert "2024" in result.columns
    assert "2022" not in result.columns
    assert "2023" not in result.columns


def test_select_from_show_row_and_col():
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame(
        {
            "계정명": ["매출액", "영업이익"],
            "2023": [100, 10],
            "2024": [200, 20],
        }
    )
    result = selectFromShow(df, indList=["매출액"], colList=["2024"])
    assert result is not None
    assert result.height == 1
    assert result.columns == ["계정명", "2024"]


def test_select_from_show_empty_df():
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame({"계정명": [], "2024": []}).cast({"계정명": pl.Utf8, "2024": pl.Int64})
    result = selectFromShow(df)
    assert result is None


def test_select_from_show_no_match_rows():
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "2024": [100],
        }
    )
    result = selectFromShow(df, indList=["존재하지않는계정"])
    assert result is None


def test_select_from_show_col_q4_fallback():
    """colList에 연도 지정 시 Q4 fallback."""
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "2024Q4": [100],
        }
    )
    result = selectFromShow(df, colList=["2024"])
    assert result is not None
    assert "2024Q4" in result.columns


def test_select_from_show_no_col_match():
    from dartlab.core.show import selectFromShow

    df = pl.DataFrame(
        {
            "계정명": ["매출액"],
            "2023": [100],
        }
    )
    result = selectFromShow(df, colList=["2099"])
    assert result is None


# ── _cascadeFilterRows ──


def test_cascade_exact_match():
    from dartlab.core.show import _cascadeFilterRows

    df = pl.DataFrame({"계정명": ["매출액", "영업이익", "순이익"]})
    result = _cascadeFilterRows(df, "계정명", ["매출액"])
    assert result is not None
    assert result.height == 1
    assert result["계정명"][0] == "매출액"


def test_cascade_normalized_match():
    """정규화 매칭 — 공백 차이를 무시한다."""
    from dartlab.core.show import _cascadeFilterRows

    df = pl.DataFrame({"계정명": ["매 출 액", "영업이익"]})
    result = _cascadeFilterRows(df, "계정명", ["매출액"])
    assert result is not None
    assert result.height == 1


def test_cascade_contains_match():
    """substring 포함 매칭."""
    from dartlab.core.show import _cascadeFilterRows

    df = pl.DataFrame({"계정명": ["연결매출액합계", "영업이익"]})
    result = _cascadeFilterRows(df, "계정명", ["매출액"])
    assert result is not None
    assert result.height == 1


def test_cascade_fuzzy_match():
    """fuzzy 매칭 (유사도 기반)."""
    from dartlab.core.show import _cascadeFilterRows

    df = pl.DataFrame({"계정명": ["매출총이익", "영업이익"]})
    # "매출총이" is close to "매출총이익"
    result = _cascadeFilterRows(df, "계정명", ["매출총이"])
    assert result is not None


def test_cascade_no_match():
    from dartlab.core.show import _cascadeFilterRows

    df = pl.DataFrame({"계정명": ["매출액"]})
    result = _cascadeFilterRows(df, "계정명", ["완전히다른계정명임"])
    assert result is None


# ── buildBlockIndex ──


def test_build_block_index_basic():
    from dartlab.core.show import buildBlockIndex

    df = pl.DataFrame(
        {
            "blockType": ["heading", "text", "table"],
            "source": ["docs", "docs", "finance"],
            "blockOrder": [0, 1, 2],
            "2024": ["제목", "내용", "숫자"],
        }
    )
    result = buildBlockIndex(df)
    assert result.height == 3
    assert "block" in result.columns
    assert "type" in result.columns
    assert "source" in result.columns
    assert "preview" in result.columns


def test_build_block_index_dedup_block_order():
    """같은 blockOrder는 한 번만 포함한다."""
    from dartlab.core.show import buildBlockIndex

    df = pl.DataFrame(
        {
            "blockType": ["text", "text"],
            "source": ["docs", "docs"],
            "blockOrder": [0, 0],
            "2024": ["a", "b"],
        }
    )
    result = buildBlockIndex(df)
    assert result.height == 1


def test_build_block_index_finance_preview():
    """finance source는 preview에 '(finance)' 표시."""
    from dartlab.core.show import buildBlockIndex

    df = pl.DataFrame(
        {
            "blockType": ["table"],
            "source": ["finance"],
            "blockOrder": [0],
            "2024": ["값"],
        }
    )
    result = buildBlockIndex(df)
    assert result["preview"][0] == "(finance)"


def test_build_block_index_report_preview():
    """report source는 preview에 '(report)' 표시."""
    from dartlab.core.show import buildBlockIndex

    df = pl.DataFrame(
        {
            "blockType": ["table"],
            "source": ["report"],
            "blockOrder": [0],
            "2024": ["값"],
        }
    )
    result = buildBlockIndex(df)
    assert result["preview"][0] == "(report)"


def test_build_block_index_without_block_order():
    """blockOrder 컬럼이 없으면 자동 인덱스 사용."""
    from dartlab.core.show import buildBlockIndex

    df = pl.DataFrame(
        {
            "blockType": ["heading", "text"],
            "source": ["docs", "docs"],
            "2024": ["제목", "내용"],
        }
    )
    result = buildBlockIndex(df)
    assert result.height == 2
    assert result["block"].to_list() == [0, 1]


def test_build_block_index_no_period_cols():
    """기간 컬럼이 없을 때도 동작한다."""
    from dartlab.core.show import buildBlockIndex

    df = pl.DataFrame(
        {
            "blockType": ["text"],
            "source": ["docs"],
            "blockOrder": [0],
        }
    )
    result = buildBlockIndex(df)
    assert result.height == 1
    assert result["preview"][0] == ""
