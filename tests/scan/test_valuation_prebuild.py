"""scan valuation prebuild 로더·fallback 단위 테스트.

외부 API (네이버) · HF 접근 없이 검증. `_ensureScanData` 를 monkeypatch 로
tmp_path 로 리다이렉트해 격리.
"""

from __future__ import annotations

from datetime import datetime

import polars as pl
import pytest

pytestmark = pytest.mark.unit


_SCHEMA = {
    "stockCode": pl.Utf8,
    "marketCap": pl.Float64,
    "per": pl.Float64,
    "pbr": pl.Float64,
    "dividendYield": pl.Float64,
    "current": pl.Int64,
    "snapshotAt": pl.Datetime("ms"),
}


def _writeMockParquet(path, snapshotAt: datetime) -> None:
    rows = [
        {
            "stockCode": "005930",
            "marketCap": 4.5e14,
            "per": 12.3,
            "pbr": 1.5,
            "dividendYield": 2.1,
            "current": 75000,
            "snapshotAt": snapshotAt,
        },
        {
            "stockCode": "000660",
            "marketCap": 1.2e14,
            "per": 8.9,
            "pbr": 1.1,
            "dividendYield": 1.5,
            "current": 180000,
            "snapshotAt": snapshotAt,
        },
    ]
    pl.DataFrame(rows, schema=_SCHEMA).write_parquet(str(path))


@pytest.fixture(autouse=True)
def _isolateScanDir(monkeypatch, tmp_path):
    """모든 테스트에서 scan parquet 경로를 tmp_path 로 리다이렉트."""
    scanDir = tmp_path / "scan"
    scanDir.mkdir()
    from dartlab.scan.io import parquet

    monkeypatch.setattr(parquet, "_ensureScanData", lambda: scanDir)
    # 전역 플래그·freshness 세션 메모 리셋 (다른 테스트 간 간섭 방지)
    monkeypatch.setattr(parquet, "_scanDownloaded", False, raising=False)
    monkeypatch.setattr(parquet, "_scanFreshnessCheckedAt", {}, raising=False)

    # 부재 시 콜드스타트 HF 다운로드 배선이 실네트워크를 타지 않게 기본 차단.
    # (성공 경로는 개별 테스트가 쓰기 스텁으로 override)
    def _failDownload(_scanDir, relativePath):
        raise OSError(f"HF unavailable in unit test: {relativePath}")

    monkeypatch.setattr(parquet, "_downloadScanFile", _failDownload)
    return scanDir


def test_loadValuationSnapshot_missing_returns_none(_isolateScanDir):
    from dartlab.scan.io.parquet import loadValuationSnapshot

    frame, snapshotAt = loadValuationSnapshot()
    assert frame is None
    assert snapshotAt is None


def test_loadValuationSnapshot_cold_start_downloads_from_hf(_isolateScanDir, monkeypatch):
    """로컬 부재 시 HF snapshot 을 먼저 시도한다 (콜드스타트 배선)."""
    from dartlab.scan.io import parquet

    ts = datetime(2026, 4, 23, 19, 0, 0)

    def _writeDownload(scanDir, relativePath):
        assert relativePath == "valuation.parquet"
        _writeMockParquet(scanDir / relativePath, ts)

    monkeypatch.setattr(parquet, "_downloadScanFile", _writeDownload)

    frame, snapshotAt = parquet.loadValuationSnapshot()
    assert frame is not None
    assert frame.height == 2
    assert snapshotAt == ts


def test_loadValuationSnapshot_reads_valid_parquet(_isolateScanDir):
    from dartlab.scan.io.parquet import loadValuationSnapshot

    ts = datetime(2026, 4, 23, 19, 0, 0)  # tzinfo 없음 — parquet read 후 동일 타입
    _writeMockParquet(_isolateScanDir / "valuation.parquet", ts)

    frame, snapshotAt = loadValuationSnapshot()
    assert frame is not None
    assert frame.height == 2
    assert set(["stockCode", "marketCap", "per", "pbr", "dividendYield", "current", "snapshotAt"]).issubset(
        set(frame.columns)
    )
    assert snapshotAt == ts


def test_loadValuationSnapshot_missing_required_column_raises(_isolateScanDir):
    """존재하는 snapshot의 schema 손상을 정상 부재로 위장하지 않는다."""
    from dartlab.scan.io.parquet import ScanDataError, loadValuationSnapshot

    # current 컬럼 누락
    bad = pl.DataFrame(
        {"stockCode": ["005930"], "marketCap": [1.0], "per": [1.0], "pbr": [1.0], "dividendYield": [1.0]}
    )
    bad.write_parquet(str(_isolateScanDir / "valuation.parquet"))

    with pytest.raises(ScanDataError, match="stage=valuation_snapshot_schema"):
        loadValuationSnapshot()


def test_scanValuation_prebuild_path_skips_naver(_isolateScanDir, monkeypatch):
    """prebuild parquet 이 있으면 네이버 API (fetchValuationRaw) 는 호출되지 않아야 한다."""
    import dartlab.scan.financial.valuation as vmod  # subpackage 직접 import (dartlab.scan 는 Scan 인스턴스라 attr dispatch)

    ts = datetime(2026, 4, 23, 19, 0, 0)
    _writeMockParquet(_isolateScanDir / "valuation.parquet", ts)

    fetchCalls: list = []

    def _fakeFetch(*args, **kwargs):
        fetchCalls.append(args)
        return pl.DataFrame(schema=vmod._RAW_SCHEMA)

    monkeypatch.setattr(vmod, "fetchValuationRaw", _fakeFetch)
    monkeypatch.setattr(vmod, "scanFinanceParquets", lambda *a, **k: {"005930": 3e14, "000660": 5e13})

    result = vmod.scanValuation(refresh=False, verbose=False)

    assert len(fetchCalls) == 0, "prebuild 있으면 네이버 호출 0회여야 함"
    assert result.height == 2
    # snapshotAt 컬럼 보존 확인
    assert "snapshotAt" in result.columns
    assert result["snapshotAt"][0] == ts
    # PSR 계산됨 (마켓캡/매출)
    assert "psr" in result.columns
    assert result["psr"][0] is not None


def test_scanValuation_fallback_when_no_prebuild(_isolateScanDir, monkeypatch):
    """prebuild 없을 때 fetchValuationRaw 호출 경로로 빠져야 함."""
    import dartlab.scan.financial.valuation as vmod  # subpackage 직접 import (dartlab.scan 는 Scan 인스턴스라 attr dispatch)

    ts = datetime(2026, 4, 23, 20, 0, 0)

    def _fakeFetch(codes, *, verbose=True):
        rows = [
            {
                "stockCode": code,
                "marketCap": 1e12,
                "per": 10.0,
                "pbr": 1.0,
                "dividendYield": 2.0,
                "current": 10000,
                "snapshotAt": ts,
            }
            for code in codes[:3]
        ]
        return pl.DataFrame(rows, schema=vmod._RAW_SCHEMA)

    monkeypatch.setattr(vmod, "fetchValuationRaw", _fakeFetch)
    monkeypatch.setattr(vmod, "scanFinanceParquets", lambda *a, **k: {})

    # dartlab.listing() mocking
    import dartlab as _dl

    monkeypatch.setattr(_dl, "listing", lambda: pl.DataFrame({"종목코드": ["005930", "000660", "035720"]}))

    result = vmod.scanValuation(refresh=False, verbose=False)

    assert result.height == 3
    assert result["snapshotAt"][0] == ts


def test_scanValuation_refresh_true_bypasses_prebuild(_isolateScanDir, monkeypatch):
    """refresh=True 이면 prebuild 있어도 네이버 재수집 경로."""
    import dartlab.scan.financial.valuation as vmod  # subpackage 직접 import (dartlab.scan 는 Scan 인스턴스라 attr dispatch)

    ts_old = datetime(2026, 4, 20, 19, 0, 0)
    _writeMockParquet(_isolateScanDir / "valuation.parquet", ts_old)

    ts_new = datetime(2026, 4, 23, 21, 0, 0)
    fetchCalls: list = []

    def _fakeFetch(codes, *, verbose=True):
        fetchCalls.append(list(codes))
        return pl.DataFrame(
            [
                {
                    "stockCode": "005930",
                    "marketCap": 5e14,
                    "per": 13.0,
                    "pbr": 1.6,
                    "dividendYield": 2.2,
                    "current": 80000,
                    "snapshotAt": ts_new,
                }
            ],
            schema=vmod._RAW_SCHEMA,
        )

    monkeypatch.setattr(vmod, "fetchValuationRaw", _fakeFetch)
    monkeypatch.setattr(vmod, "scanFinanceParquets", lambda *a, **k: {})

    import dartlab as _dl

    monkeypatch.setattr(_dl, "listing", lambda: pl.DataFrame({"종목코드": ["005930"]}))

    result = vmod.scanValuation(refresh=True, verbose=False)

    assert len(fetchCalls) == 1, "refresh=True 이면 네이버 호출 정확히 1회"
    assert result.height == 1
    assert result["snapshotAt"][0] == ts_new  # 새로 수집된 시각


def test_fetchValuationRaw_all_failures_raise(monkeypatch):
    """전 종목 수집 실패를 정상적인 빈 snapshot으로 반환하지 않는다."""

    import dartlab.scan.financial.valuation as vmod

    async def failAll(_codes, _verbose):
        return {}, {"005930": "HTTPError: rate limited"}

    monkeypatch.setattr(vmod, "_fetchAll", failAll)

    with pytest.raises(vmod.ValuationFetchError, match="수집 결과가 없습니다"):
        vmod.fetchValuationRaw(["005930"], verbose=False)


def test_scanValuation_empty_listing_raises(_isolateScanDir, monkeypatch):
    """수집 대상 상장사 부재를 빈 밸류에이션 결과로 위장하지 않는다."""

    import dartlab as dartlabModule
    import dartlab.scan.financial.valuation as vmod

    monkeypatch.setattr(dartlabModule, "listing", lambda: pl.DataFrame())

    with pytest.raises(vmod.ValuationFetchError, match="수집 대상 종목"):
        vmod.scanValuation(refresh=True, verbose=False)
