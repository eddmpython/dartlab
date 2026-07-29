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


def test_scan_accounts_callable() -> None:
    """scanAccounts() batch primitive callable smoke."""
    from dartlab.providers.edgar.finance.scanAccount import scanAccounts

    assert callable(scanAccounts)


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

    def withDates(frame: pl.DataFrame) -> pl.DataFrame:
        """합성 filing에 source context 날짜를 추가한다."""

        return frame.with_columns(pl.col("fy").cast(pl.Utf8).str.strptime(pl.Date, "%Y").alias("end")).with_columns(
            pl.col("end").dt.offset_by("-1y").alias("start"),
            pl.col("end").dt.offset_by("1mo").alias("filed"),
        )

    withDates(
        pl.DataFrame(
            {
                "cik": ["0000000001"] * 12,
                "namespace": ["us-gaap"] * 11 + ["ifrs-full"],
                "tag": ["SegmentReportingInformationRevenue", *(["Revenues"] * 10), "Revenue"],
                "unit": ["USD"] * 12,
                "fy": [2024, 2024, 2024, 2023, 2023, 2023, 2023, 2023, 2023, 2022, 2022, 2023],
                "fp": ["FY", "FY", "FY", "Q1", "Q1", "Q2", "Q3", "FY", "FY", "Q1", "FY", "FY"],
                "val": [9999.0, None, 123.0, 30.0, -20.0, 40.0, 50.0, 200.0, 999.0, 10.0, 80.0, 900.0],
            }
        )
    ).write_parquet(edgarDir / "0000000001.parquet")
    withDates(
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
        )
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
    assert rows["AAA"]["2023Q1"] == 30.0
    assert rows["AAA"]["2023Q4"] == 80.0
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


def test_scan_account_prefers_current_full_year_context_over_old_preferred_tag(
    syntheticScan,
) -> None:
    """FY filing 안의 과거 비교값보다 현재 full-year context를 선택한다."""

    from dartlab.core.dataLoader import _dataDir

    path = Path(_dataDir("edgar")) / "0000000001.parquet"
    current = pl.read_parquet(path)
    extra = (
        pl.DataFrame(
            {
                "cik": ["0000000001", "0000000001"],
                "namespace": ["us-gaap", "us-gaap"],
                "tag": [
                    "Revenues",
                    "RevenueFromContractWithCustomerExcludingAssessedTax",
                ],
                "unit": ["USD", "USD"],
                "fy": [2025, 2025],
                "fp": ["FY", "FY"],
                "val": [100.0, 1000.0],
                "start": ["2022-01-01", "2024-01-01"],
                "end": ["2022-12-31", "2024-12-31"],
                "filed": ["2025-02-01", "2025-02-01"],
            }
        )
        .with_columns(
            pl.col("start").str.to_date(),
            pl.col("end").str.to_date(),
            pl.col("filed").str.to_date(),
        )
        .select(current.columns)
    )
    pl.concat([current, extra]).write_parquet(path)

    result = syntheticScan.scanAccount("sales", freq="Y")
    alpha = result.filter(pl.col("stockCode") == "AAA").row(0, named=True)

    assert alpha["2025"] == 1000.0


def test_scan_accounts_duckdb_reads_multiple_accounts_in_one_batch(syntheticScan) -> None:
    """여러 계정의 연간 결과를 batch SQL 한 번으로 분리 반환한다."""

    from dartlab.core.dataLoader import _dataDir

    edgarDir = Path(_dataDir("edgar"))
    additions = {
        "0000000001": ("us-gaap", "OperatingIncomeLoss", [50.0, 40.0]),
        "0000000002": (
            "ifrs-full",
            "ProfitLossFromOperatingActivities",
            [55.0, 44.0],
        ),
    }
    for cik, (namespace, tag, values) in additions.items():
        path = edgarDir / f"{cik}.parquet"
        current = pl.read_parquet(path)
        extra = (
            pl.DataFrame(
                {
                    "cik": [cik, cik],
                    "namespace": [namespace, namespace],
                    "tag": [tag, tag],
                    "unit": ["USD", "USD"],
                    "fy": [2024, 2023],
                    "fp": ["FY", "FY"],
                    "val": values,
                }
            )
            .with_columns(pl.col("fy").cast(pl.Utf8).str.strptime(pl.Date, "%Y").alias("end"))
            .with_columns(
                pl.col("end").dt.offset_by("-1y").alias("start"),
                pl.col("end").dt.offset_by("1mo").alias("filed"),
            )
        )
        extra = extra.select(current.columns)
        pl.concat([current, extra]).write_parquet(path)

    results = syntheticScan.scanAccounts(["sales", "operating_profit"], freq="Y")

    assert list(results) == ["sales", "operating_profit"]
    sales = {row["stockCode"]: row for row in results["sales"].iter_rows(named=True)}
    operating = {row["stockCode"]: row for row in results["operating_profit"].iter_rows(named=True)}
    assert sales["AAA"]["2024"] == 123.0
    assert sales["BBB"]["2024"] == 140.0
    assert operating["AAA"]["2024"] == 50.0
    assert operating["BBB"]["2024"] == 55.0


def test_scan_accounts_batch_failure_uses_single_account_fallback(
    syntheticScan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """batch query 실패 시 각 계정의 검증된 단일 경로로 복구한다."""

    calls: list[tuple[str, str]] = []

    def failBatch(*_args, **_kwargs):
        raise syntheticScan.EdgarScanExecutionError(
            "duckdb_batch_query",
            "forced batch failure",
        )

    def fakeScanAccount(snakeId: str, *, freq: str = "Q") -> pl.DataFrame:
        calls.append((snakeId, freq))
        return pl.DataFrame({"stockCode": [snakeId.upper()]})

    monkeypatch.setattr(syntheticScan, "_scanAccountsDuckDb", failBatch)
    monkeypatch.setattr(syntheticScan, "scanAccount", fakeScanAccount)

    results = syntheticScan.scanAccounts(["sales", "net_profit"], freq="Y")

    assert calls == [("sales", "Y"), ("net_profit", "Y")]
    assert list(results) == ["sales", "net_profit"]


def test_scan_accounts_splits_large_request_into_bounded_batches(
    syntheticScan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """대규모 계정 요청은 메모리 상한을 지키는 3계정 이하 batch로 나눈다."""

    calls: list[list[str]] = []

    def fakeBatch(
        _paths,
        tagKeysBySnakeId,
        _tickerUniverse,
        *,
        freq: str,
        instantBySnakeId,
    ):
        assert freq == "Y"
        assert set(instantBySnakeId).issuperset(tagKeysBySnakeId)
        calls.append(list(tagKeysBySnakeId))
        return {snakeId: pl.DataFrame({"stockCode": [snakeId.upper()]}) for snakeId in tagKeysBySnakeId}

    monkeypatch.setattr(syntheticScan, "_scanAccountsDuckDb", fakeBatch)
    snakeIds = [
        "sales",
        "operating_profit",
        "net_profit",
        "total_assets",
        "total_stockholders_equity",
    ]

    results = syntheticScan.scanAccounts(snakeIds, freq="Y")

    assert calls == [snakeIds[:3], snakeIds[3:]]
    assert list(results) == snakeIds


def test_simple_ratio_uses_account_batch_once(
    syntheticScan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """분자와 분모를 따로 source scan하지 않는다."""

    calls: list[tuple[list[str], str]] = []

    def fakeScanAccounts(snakeIds: list[str], *, freq: str = "Q"):
        calls.append((snakeIds, freq))
        return {
            "net_profit": pl.DataFrame(
                {
                    "stockCode": ["AAA"],
                    "corpName": ["Alpha"],
                    "2024": [20.0],
                }
            ),
            "total_assets": pl.DataFrame(
                {
                    "stockCode": ["AAA"],
                    "corpName": ["Alpha"],
                    "2024": [100.0],
                }
            ),
        }

    monkeypatch.setattr(syntheticScan, "scanAccounts", fakeScanAccounts)

    result = syntheticScan._calcSimpleRatio(
        {
            "numer": "net_profit",
            "denom": "total_assets",
            "pct": True,
        },
        freq="Y",
    )

    assert calls == [(["net_profit", "total_assets"], "Y")]
    assert result.item(0, "2024") == 20.0


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
    assert rows["AAA"]["2023Q1"] == 30.0
    assert rows["AAA"]["2023Q4"] == 80.0
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
    ).with_columns(
        pl.lit(None, dtype=pl.Date).alias("start"),
        pl.lit("2024-12-31").str.to_date().alias("end"),
        pl.lit("2025-02-01").str.to_date().alias("filed"),
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
