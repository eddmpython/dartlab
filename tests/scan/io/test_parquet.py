"""scan 프리빌드 읽기 헬퍼 계약 (`scan.io.parquet`).

브라우저(pyodide)의 polars WASM 에는 ``scan_parquet`` 도 streaming 엔진도 없다(실측).
그래서 축 모듈이 ``pl.scan_parquet`` + ``collect(engine="streaming")`` 을 직접 부르면
브라우저에서 전부 죽거나 조용히 빈 결과가 된다. 세 헬퍼가 그 분기를 한 곳에 가둔다.

- ``financeScanPath``: 데스크톱 전량본 / 브라우저 경량본 중 무엇을 읽을지
- ``lazyParquet``: LazyFrame 을 얻는 법
- ``collectScan``: LazyFrame 을 수집하는 법
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from dartlab.scan.io import parquet as parquetIo

pytestmark = [pytest.mark.unit]


@pytest.fixture(scope="module")
def sampleParquet(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """축 모듈이 읽는 finance 프리빌드와 같은 최소 스키마."""
    path = tmp_path_factory.mktemp("scanIo") / "finance.parquet"
    pl.DataFrame(
        {
            "stockCode": ["005930", "000660"],
            "sj_div": ["IS", "IS"],
            "thstrm_amount": [300, 200],
        }
    ).write_parquet(path)
    return path


def test_financeScanPath_desktop_usesFullPrebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    """데스크톱은 전량 finance.parquet."""
    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", False)
    assert parquetIo.financeScanPath(Path("/scan")).name == "finance.parquet"


def test_financeScanPath_pyodide_usesLitePrebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    """브라우저는 경량본 finance-lite.parquet (전량본은 브라우저에 존재하지 않는다)."""
    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", True)
    assert parquetIo.financeScanPath(Path("/scan")).name == "finance-lite.parquet"


def test_lazyParquet_desktop_and_pyodide_agree(monkeypatch: pytest.MonkeyPatch, sampleParquet: Path) -> None:
    """두 경로가 같은 프레임을 준다 (WASM 우회가 결과를 바꾸지 않는다)."""
    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", False)
    desktop = parquetIo.lazyParquet(sampleParquet).collect()

    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", True)
    browser = parquetIo.lazyParquet(sampleParquet).collect()

    assert desktop.equals(browser)


def test_collectScan_pyodide_omitsStreamingEngine(monkeypatch: pytest.MonkeyPatch, sampleParquet: Path) -> None:
    """polars WASM 은 engine='streaming' 을 ValueError 로 거부한다. 그 인자를 넘기면 안 된다."""
    seen: list[dict] = []
    original = pl.LazyFrame.collect

    def spy(self, *args, **kwargs):
        seen.append(dict(kwargs))
        return original(self, *args)

    monkeypatch.setattr(pl.LazyFrame, "collect", spy)

    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", True)
    parquetIo.collectScan(pl.scan_parquet(sampleParquet))
    assert seen[-1] == {}

    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", False)
    parquetIo.collectScan(pl.scan_parquet(sampleParquet))
    assert seen[-1] == {"engine": "streaming"}


def test_parquetColumns_readsNamesWithoutBody(monkeypatch: pytest.MonkeyPatch, sampleParquet: Path) -> None:
    """열 이름만 필요할 때 본문을 읽지 않는다 (브라우저 20MB 재독 회피)."""
    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", True)
    assert parquetIo.parquetColumns(sampleParquet) == ["stockCode", "sj_div", "thstrm_amount"]

    monkeypatch.setattr("dartlab.core.dataLoader._IS_PYODIDE", False)
    assert parquetIo.parquetColumns(sampleParquet) == ["stockCode", "sj_div", "thstrm_amount"]


def test_scanParquets_existing_corrupt_prebuild_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """존재하는 report prebuild 손상을 raw 데이터 부재로 바꾸지 않는다."""

    scanDir = tmp_path / "scan"
    reportDir = scanDir / "report"
    reportDir.mkdir(parents=True)
    (reportDir / "majorHolder.parquet").write_bytes(b"not parquet")
    monkeypatch.setattr(parquetIo, "_ensureScanData", lambda **_kwargs: scanDir)

    with pytest.raises(parquetIo.ScanDataError, match="stage=report_prebuild_read"):
        parquetIo.scanParquets(
            "majorHolder",
            ["stockCode", "year", "name"],
        )


def test_scanFinanceParquets_existing_corrupt_prebuild_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """존재하는 finance prebuild 손상을 빈 계정 map으로 바꾸지 않는다."""

    scanDir = tmp_path / "scan"
    scanDir.mkdir()
    (scanDir / "finance.parquet").write_bytes(b"not parquet")
    monkeypatch.setattr(parquetIo, "_ensureScanData", lambda **_kwargs: scanDir)

    with pytest.raises(parquetIo.ScanDataError, match="stage=finance_prebuild_read"):
        parquetIo.scanFinanceParquets("IS", {"Revenue"}, {"매출액"})


def test_scan_latest_account_values_wide_latest_period(tmp_path) -> None:
    """scanLatestAccountValues: 최신 연도만 남기고 spec 이름의 wide 컬럼으로 집계한다."""
    import polars as pl

    from dartlab.scan.io.parquet import ScanDataError, scanLatestAccountValues

    path = tmp_path / "finance.parquet"
    pl.DataFrame(
        {
            "stockCode": ["005930", "005930"],
            "bsns_year": ["2024", "2025"],
            "sj_div": ["IS", "IS"],
            "fs_nm": ["연결재무제표", "연결재무제표"],
            "account_id": ["ifrs-full_Revenue", "ifrs-full_Revenue"],
            "account_nm": ["매출액", "매출액"],
            "thstrm_amount": ["1,000", "2,000"],
        }
    ).write_parquet(str(path))

    out = scanLatestAccountValues(path, {"revenue": ({"ifrs-full_Revenue"}, {"매출액"}, {"IS"})})
    assert out.height == 1
    row = out.to_dicts()[0]
    assert row["bsns_year"] == "2025"
    assert row["revenue"] == 2000.0

    with pytest.raises(ValueError, match="accountSpecs"):
        scanLatestAccountValues(path, {})

    bad = tmp_path / "bad.parquet"
    pl.DataFrame({"stockCode": ["005930"]}).write_parquet(str(bad))
    with pytest.raises(ScanDataError, match="finance_schema"):
        scanLatestAccountValues(bad, {"revenue": ({"x"}, {"y"}, None)})
