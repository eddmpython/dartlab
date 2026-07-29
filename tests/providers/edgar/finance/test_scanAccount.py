"""providers/edgar/finance/scanAccount.py unit and source-native regression."""

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.finance.scanAccount  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_scan_account_callable() -> None:
    """scanAccount() callable smoke."""
    from dartlab.providers.edgar.finance.scanAccount import scanAccount

    assert callable(scanAccount)


def test_scan_ratio_callable() -> None:
    """scanRatio() callable smoke."""
    from dartlab.providers.edgar.finance.scanAccount import scanRatio

    assert callable(scanRatio)


@pytest.fixture
def syntheticScan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """filename CIK와 production 분기 규칙을 담은 작은 runtime source를 만든다."""
    import dartlab.core.dataLoader as dataLoader
    import dartlab.core.edgarClient as edgarClient
    import dartlab.providers.edgar.finance.scanAccount as scanModule

    edgarDir = tmp_path / "edgar"
    edgarDir.mkdir()
    pl.DataFrame(
        {
            "cik": ["0000000001"] * 11,
            "namespace": ["us-gaap"] * 10 + ["ifrs-full"],
            "tag": ["Revenues"] * 10 + ["Revenue"],
            "unit": ["USD"] * 11,
            "fy": [2024, 2024, 2023, 2023, 2023, 2023, 2023, 2023, 2022, 2022, 2023],
            "fp": ["FY", "FY", "Q1", "Q1", "Q2", "Q3", "FY", "FY", "Q1", "FY", "FY"],
            "val": [None, 123.0, 30.0, -20.0, 40.0, 50.0, 200.0, 999.0, 10.0, 80.0, 900.0],
        }
    ).write_parquet(edgarDir / "0000000001.parquet")
    pl.DataFrame(
        {
            "cik": ["0000000002"] * 5,
            "namespace": ["ifrs-full"] * 5,
            "tag": ["Revenue"] * 5,
            "unit": ["USD"] * 5,
            "fy": [2024, 2023, 2023, 2023, 2023],
            "fp": ["FY", "Q1", "Q2", "Q3", "FY"],
            "val": [140.0, 10.0, 20.0, 30.0, 100.0],
        }
    ).write_parquet(edgarDir / "0000000002.parquet")
    (edgarDir / "9999999999.parquet").write_bytes(b"unlisted invalid parquet")

    tickerFrame = pl.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "cik": ["0000000001", "0000000002"],
            "title": ["Alpha Corp", "Beta IFRS"],
        }
    )
    monkeypatch.setattr(dataLoader, "_dataDir", lambda _name: edgarDir)
    monkeypatch.setattr(edgarClient, "loadTickers", lambda: tickerFrame)
    return scanModule


def _failFileLoop(*_args, **_kwargs):
    pytest.fail("source-native success must not enter file-loop fallback")


def test_scan_account_duckdb_quarterly_exact(syntheticScan, monkeypatch: pytest.MonkeyPatch) -> None:
    """listed filename CIK pruning과 기존 quarterly 값 선택을 exact 보존한다."""
    monkeypatch.setattr(syntheticScan, "_scanAccountFileLoop", _failFileLoop)

    result = syntheticScan.scanAccount("sales", freq="Q")

    assert result.columns == [
        "stockCode",
        "corpName",
        "2023Q4",
        "2023Q3",
        "2023Q2",
        "2023Q1",
        "2022Q1",
    ]
    rows = {row["stockCode"]: row for row in result.iter_rows(named=True)}
    assert rows["AAA"]["corpName"] == "Alpha Corp"
    assert rows["AAA"]["2023Q1"] == -20.0
    assert rows["AAA"]["2023Q4"] == 130.0
    assert rows["BBB"]["corpName"] == "Beta IFRS"
    assert rows["BBB"]["2023Q1"] == 10.0
    assert rows["BBB"]["2023Q4"] == 40.0


def test_scan_account_duckdb_annual_exact(syntheticScan, monkeypatch: pytest.MonkeyPatch) -> None:
    """annual은 각 fiscal year의 첫 non-null FY 값을 유지한다."""
    monkeypatch.setattr(syntheticScan, "_scanAccountFileLoop", _failFileLoop)

    result = syntheticScan.scanAccount("sales", freq="Y")

    assert result.columns == ["stockCode", "corpName", "2024", "2023", "2022"]
    rows = {row["stockCode"]: row for row in result.iter_rows(named=True)}
    assert rows["AAA"]["2023"] == 200.0
    assert rows["AAA"]["2022"] == 80.0
    assert rows["BBB"]["2024"] == 140.0
    assert rows["BBB"]["2023"] == 100.0


def test_scan_account_duckdb_failure_uses_file_loop(
    syntheticScan,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DuckDB import 또는 실행 실패 시 기존 file-loop 결과를 반환한다."""

    def failDuckDb(*_args, **_kwargs):
        raise syntheticScan.EdgarScanExecutionError("duckdb_query", "forced DuckDB failure")

    monkeypatch.setattr(syntheticScan, "_scanAccountDuckDb", failDuckDb)
    caplog.set_level("WARNING")

    result = syntheticScan.scanAccount("sales", freq="Q")

    rows = {row["stockCode"]: row for row in result.iter_rows(named=True)}
    assert rows["AAA"]["2023Q1"] == -20.0
    assert rows["AAA"]["2023Q4"] == 130.0
    assert rows["BBB"]["2023Q1"] == 10.0
    assert rows["BBB"]["2023Q4"] == 40.0
    assert "forced DuckDB failure" in caplog.text


def test_tag_keys_include_ifrs_concepts() -> None:
    from dartlab.providers.edgar.finance.scanAccount import _buildEdgarTagKeys

    sales = _buildEdgarTagKeys("sales")
    profit = _buildEdgarTagKeys("net_profit")

    assert "revenues" in sales.usGaap
    assert "revenue" in sales.ifrsFull
    assert "profitloss" in profit.ifrsFull


def test_listed_corrupt_shard_raises_with_duckdb_and_file_provenance(
    syntheticScan,
) -> None:
    import dartlab.core.dataLoader as dataLoader

    edgarDir = Path(dataLoader._dataDir("edgar"))
    damaged = edgarDir / "0000000002.parquet"
    damaged.write_bytes(b"listed corrupt parquet")

    with pytest.raises(syntheticScan.EdgarScanExecutionError) as excInfo:
        syntheticScan.scanAccount("sales", freq="Q")

    error = excInfo.value
    assert error.stage == "fallback"
    assert isinstance(error.primaryError, syntheticScan.EdgarScanExecutionError)
    assert error.primaryError.stage == "duckdb_query"
    assert isinstance(error.__cause__, syntheticScan.EdgarScanStorageError)
    assert error.__cause__.source == str(damaged)


def test_ticker_mapping_failure_is_not_empty_data(syntheticScan, monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab.core.edgarClient as edgarClient

    def _failTickerLoad():
        raise OSError("ticker source unavailable")

    monkeypatch.setattr(edgarClient, "loadTickers", _failTickerLoad)

    with pytest.raises(syntheticScan.EdgarScanMappingError, match="ticker universe load failed") as excInfo:
        syntheticScan.scanAccount("sales", freq="Y")

    assert isinstance(excInfo.value.__cause__, OSError)


def test_no_local_shards_is_normal_empty_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab.core.dataLoader as dataLoader
    import dartlab.core.edgarClient as edgarClient
    import dartlab.providers.edgar.finance.scanAccount as scanModule

    monkeypatch.setattr(dataLoader, "_dataDir", lambda _name: tmp_path)
    monkeypatch.setattr(edgarClient, "loadTickers", lambda: pytest.fail("empty source must not load ticker universe"))

    result = scanModule.scanAccount("sales", freq="Q")

    assert result.to_dict(as_series=False) == {"stockCode": []}


def test_ifrs_instant_account_uses_fy_as_q4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab.core.dataLoader as dataLoader
    import dartlab.core.edgarClient as edgarClient
    import dartlab.providers.edgar.finance.scanAccount as scanModule

    edgarDir = tmp_path / "edgar"
    edgarDir.mkdir()
    pl.DataFrame(
        {
            "namespace": ["ifrs-full"],
            "tag": ["Assets"],
            "unit": ["USD"],
            "fy": [2024],
            "fp": ["FY"],
            "val": [500.0],
        }
    ).write_parquet(edgarDir / "0000000003.parquet")
    monkeypatch.setattr(dataLoader, "_dataDir", lambda _name: edgarDir)
    monkeypatch.setattr(
        edgarClient,
        "loadTickers",
        lambda: pl.DataFrame(
            {
                "ticker": ["CCC"],
                "cik": ["3"],
                "title": ["Gamma IFRS"],
            }
        ),
    )

    result = scanModule.scanAccount("assets", freq="Q")

    assert result.to_dicts() == [
        {
            "stockCode": "CCC",
            "corpName": "Gamma IFRS",
            "2024Q4": 500.0,
        }
    ]
