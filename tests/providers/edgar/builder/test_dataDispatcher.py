"""providers/edgar/builder/dataDispatcher.py mirror smoke — P6."""

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.builder.dataDispatcher  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_apply_period_filter_callable() -> None:
    """applyPeriodFilter() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import applyPeriodFilter

    assert callable(applyPeriodFilter)


def test_apply_period_filter_rejects_missing_wide_period() -> None:
    """없는 기간 요청이 전체 재무표로 되돌아가지 않는다."""
    from dartlab.providers.edgar.builder.dataDispatcher import applyPeriodFilter

    wide = pl.DataFrame({"snakeId": ["sales"], "2024": [100.0], "2023": [90.0]})

    assert applyPeriodFilter(wide, "1900") is None


def test_build_block_index_callable() -> None:
    """buildBlockIndex() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import buildBlockIndex

    assert callable(buildBlockIndex)


def test_build_finance_series_callable() -> None:
    """buildFinanceSeries() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import buildFinanceSeries

    assert callable(buildFinanceSeries)


def test_build_ratios_callable() -> None:
    """buildRatios() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import buildRatios

    assert callable(buildRatios)


def test_periods_str_callable() -> None:
    """periodsStr() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import periodsStr

    assert callable(periodsStr)


def test_preview_docs_cell_callable() -> None:
    """previewDocsCell() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import previewDocsCell

    assert callable(previewDocsCell)


def test_preview_finance_callable() -> None:
    """previewFinance() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import previewFinance

    assert callable(previewFinance)


def test_shape_str_callable() -> None:
    """shapeStr() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import shapeStr

    assert callable(shapeStr)


def test_show_impl_callable() -> None:
    """showImpl() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import showImpl

    assert callable(showImpl)


def test_transpose_to_vertical_callable() -> None:
    """transposeToVertical() callable smoke."""
    from dartlab.providers.edgar.builder.dataDispatcher import transposeToVertical

    assert callable(transposeToVertical)
