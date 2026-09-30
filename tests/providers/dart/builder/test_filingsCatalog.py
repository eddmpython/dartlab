"""providers/dart/builder/filingsCatalog.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    import dartlab.providers.dart.builder.filingsCatalog  # noqa: F401


def test_build_disclosure_callable() -> None:
    """buildDisclosure() callable smoke."""
    from dartlab.providers.dart.builder.filingsCatalog import buildDisclosure

    assert callable(buildDisclosure)


def test_build_filings_callable() -> None:
    """buildFilings() callable smoke."""
    from dartlab.providers.dart.builder.filingsCatalog import buildFilings

    assert callable(buildFilings)


def testFilingsReadOnlyMetadataAndKeepExactPeriod(monkeypatch, tmp_path):
    from types import SimpleNamespace

    import polars as pl

    from dartlab.core import dataLoader
    from dartlab.providers.dart.builder.filingsCatalog import buildFilings
    from dartlab.providers.dart.panel import read

    path = tmp_path / "005930.parquet"
    pl.DataFrame({"period": ["2025Q4"], "rceptNo": ["20260310002820"], "contentRaw": ["large body"]}).write_parquet(
        path
    )
    monkeypatch.setattr(read, "ensurePanelFromHf", lambda *args: True)
    monkeypatch.setattr(read, "_panelDir", lambda *args: tmp_path / "005930")
    original = dataLoader.readParquetSafe

    def projected(paths, *, columns):
        assert columns == ["period", "rceptNo"]
        return original(paths, columns=columns)

    monkeypatch.setattr(dataLoader, "readParquetSafe", projected)
    result = buildFilings(SimpleNamespace(_hasPanel=True, stockCode="005930"))
    assert result["period"].to_list() == ["2025Q4"]
    assert result["reportType"].to_list() == ["사업보고서"]


def test_build_live_filings_callable() -> None:
    """buildLiveFilings() callable smoke."""
    from dartlab.providers.dart.builder.filingsCatalog import buildLiveFilings

    assert callable(buildLiveFilings)


def test_build_read_filing_callable() -> None:
    """buildReadFiling() callable smoke."""
    from dartlab.providers.dart.builder.filingsCatalog import buildReadFiling

    assert callable(buildReadFiling)


def test_build_update_callable() -> None:
    """buildUpdate() callable smoke."""
    from dartlab.providers.dart.builder.filingsCatalog import buildUpdate

    assert callable(buildUpdate)
