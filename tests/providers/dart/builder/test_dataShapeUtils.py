"""providers/dart/builder/dataShapeUtils.py mirror smoke — P6."""

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    import dartlab.providers.dart.builder.dataShapeUtils  # noqa: F401


def test_apply_period_filter_callable() -> None:
    """applyPeriodFilter() callable smoke."""
    from dartlab.providers.dart.builder.dataShapeUtils import applyPeriodFilter

    assert callable(applyPeriodFilter)


def test_apply_period_filter_rejects_missing_wide_period() -> None:
    """없는 기간 요청이 전체 재무표로 되돌아가지 않는다."""
    from dartlab.providers.dart.builder.dataShapeUtils import applyPeriodFilter

    wide = pl.DataFrame({"항목": ["매출액"], "2024": [100.0], "2023": [90.0]})

    assert applyPeriodFilter(wide, "1900") is None


def test_apply_period_filter_uses_q4_for_annual_report_rows() -> None:
    """행 기반 정형 report의 연도 요청은 해당 연도 Q4로 해소한다."""
    from dartlab.providers.dart.builder.dataShapeUtils import applyPeriodFilter

    rows = pl.DataFrame({"period": ["2024Q4", "2024Q2", "2023Q4"], "value": [100.0, 50.0, 90.0]})

    result = applyPeriodFilter(rows, "2024")

    assert result is not None
    assert result.to_dicts() == [{"period": "2024Q4", "value": 100.0}]


def test_clean_finance_data_frame_callable() -> None:
    """cleanFinanceDataFrame() callable smoke."""
    from dartlab.providers.dart.builder.dataShapeUtils import cleanFinanceDataFrame

    assert callable(cleanFinanceDataFrame)


def test_transpose_to_vertical_callable() -> None:
    """transposeToVertical() callable smoke."""
    from dartlab.providers.dart.builder.dataShapeUtils import transposeToVertical

    assert callable(transposeToVertical)


def test_warn_unknown_topic_callable() -> None:
    """warnUnknownTopic() callable smoke."""
    from dartlab.providers.dart.builder.dataShapeUtils import warnUnknownTopic

    assert callable(warnUnknownTopic)
