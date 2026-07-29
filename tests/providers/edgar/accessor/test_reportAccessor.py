"""providers/edgar/accessor/reportAccessor.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.accessor.reportAccessor  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_extract_preserves_report_artifact_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """extractor 장애를 정상 무데이터 None으로 캐시하지 않는다."""
    from types import SimpleNamespace

    from dartlab.providers.edgar.accessor import reportAccessor
    from dartlab.providers.edgar.accessor.reportAccessor import _ReportAccessor

    calls = 0

    def failExtract(_company):
        nonlocal calls
        calls += 1
        raise OSError("EDGAR report artifact corrupt")

    monkeypatch.setitem(reportAccessor._SUPPORTED, "dividend", failExtract)
    accessor = _ReportAccessor(SimpleNamespace())

    for _ in range(2):
        with pytest.raises(OSError, match="EDGAR report artifact corrupt"):
            accessor.extract("dividend")

    assert calls == 2
