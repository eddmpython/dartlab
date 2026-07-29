"""providers/dart/accessor/reportAccessor.py mirror smoke — P6."""

from types import SimpleNamespace

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    import dartlab.providers.dart.accessor.reportAccessor  # noqa: F401


def test_report_frame_inner_callable() -> None:
    """reportFrameInner() callable smoke."""
    from dartlab.providers.dart.accessor.reportAccessor import reportFrameInner

    assert callable(reportFrameInner)


def test_report_pivot_by_se_callable() -> None:
    """reportPivotBySe() callable smoke."""
    from dartlab.providers.dart.accessor.reportAccessor import reportPivotBySe

    assert callable(reportPivotBySe)


def test_report_frame_keeps_period_for_multi_measure_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """se가 있어도 thstrm 없는 정형표는 기간과 여러 측정값을 보존한다."""
    from dartlab.providers.dart.accessor.reportAccessor import reportFrameInner
    from dartlab.providers.dart.report import extract as reportExtract

    raw = pl.DataFrame(
        {
            "se": ["합계", "합계"],
            "year": [2023, 2024],
            "quarterNum": [4, 4],
            "quarter": ["사업보고서", "사업보고서"],
            "stockCode": ["005930", "005930"],
            "apiType": ["stockTotal", "stockTotal"],
            "stlm_dt": ["2023-12-31", "2024-12-31"],
            "isu_stock_totqy": [100.0, 110.0],
            "distb_stock_co": [90.0, 98.0],
        }
    )
    monkeypatch.setattr(reportExtract, "extractClean", lambda *_args, **_kwargs: raw)

    result = reportFrameInner("005930", "stockTotal", "stockTotal")

    assert result is not None
    assert result.columns == ["구분", "발행할주식총수", "유통주식수", "period"]
    assert result["period"].to_list() == ["2024Q4", "2023Q4"]
    assert result["유통주식수"].to_list() == [98.0, 90.0]


def test_extract_preserves_report_artifact_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """손상 report를 정상 무데이터 None으로 캐시하지 않는다."""
    import dartlab.providers.dart.report as reportModule
    from dartlab.providers.dart.accessor.reportAccessor import _ReportAccessor

    calls = 0

    def failExtract(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise OSError("report parquet corrupt")

    monkeypatch.setattr(reportModule, "extractClean", failExtract)
    company = SimpleNamespace(stockCode="005930", rawReport=pl.DataFrame({"apiType": ["dividend"]}))
    accessor = _ReportAccessor(company)

    for _ in range(2):
        with pytest.raises(OSError, match="report parquet corrupt"):
            accessor.extract("dividend")

    assert calls == 2
