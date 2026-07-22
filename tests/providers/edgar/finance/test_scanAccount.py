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
            "cik": ["0000000000"] * 10,
            "namespace": ["us-gaap"] * 10,
            "tag": ["Revenues"] * 10,
            "unit": ["USD"] * 10,
            "fy": [2024, 2024, 2023, 2023, 2023, 2023, 2023, 2023, 2022, 2022],
            "fp": ["FY", "FY", "Q1", "Q1", "Q2", "Q3", "FY", "FY", "Q1", "FY"],
            "val": [None, 123.0, 30.0, -20.0, 40.0, 50.0, 200.0, 999.0, 10.0, 80.0],
        }
    ).write_parquet(edgarDir / "0000000001.parquet")
    (edgarDir / "9999999999.parquet").write_bytes(b"unlisted invalid parquet")

    tickerFrame = pl.DataFrame(
        {
            "ticker": ["AAA"],
            "cik": ["0000000001"],
            "title": ["Alpha Corp"],
        }
    )
    monkeypatch.setattr(dataLoader, "_dataDir", lambda _name: edgarDir)
    monkeypatch.setattr(edgarClient, "loadTickers", lambda: tickerFrame)
    monkeypatch.setattr(scanModule, "_buildEdgarTagKeys", lambda _snakeId: {"revenues"})
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
        "2024Q4",
        "2023Q4",
        "2023Q3",
        "2023Q2",
        "2023Q1",
        "2022Q4",
        "2022Q1",
    ]
    row = result.row(0, named=True)
    assert row["stockCode"] == "AAA"
    assert row["corpName"] == "Alpha Corp"
    assert row["2024Q4"] == 123.0
    assert row["2023Q1"] == -20.0
    assert row["2023Q4"] == 130.0
    assert row["2022Q4"] == 80.0


def test_scan_account_duckdb_annual_exact(syntheticScan, monkeypatch: pytest.MonkeyPatch) -> None:
    """annual은 각 fiscal year의 첫 non-null FY 값을 유지한다."""
    monkeypatch.setattr(syntheticScan, "_scanAccountFileLoop", _failFileLoop)

    result = syntheticScan.scanAccount("sales", freq="Y")

    assert result.columns == ["stockCode", "corpName", "2023", "2022"]
    row = result.row(0, named=True)
    assert row["2023"] == 200.0
    assert row["2022"] == 80.0


def test_scan_account_duckdb_failure_uses_file_loop(syntheticScan, monkeypatch: pytest.MonkeyPatch) -> None:
    """DuckDB import 또는 실행 실패 시 기존 file-loop 결과를 반환한다."""

    def failDuckDb(*_args, **_kwargs):
        raise RuntimeError("forced DuckDB failure")

    monkeypatch.setattr(syntheticScan, "_scanAccountDuckDb", failDuckDb)

    result = syntheticScan.scanAccount("sales", freq="Q")

    row = result.row(0, named=True)
    assert row["stockCode"] == "AAA"
    assert row["2023Q1"] == -20.0
    assert row["2023Q4"] == 130.0
