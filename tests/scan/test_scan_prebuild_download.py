"""scan prebuild auto-download contract."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _patchScanRoot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    import dartlab.core.dataLoader as dataLoader
    import dartlab.scan.io.parquet as parquet

    scanDir = tmp_path / "scan"
    monkeypatch.setattr(dataLoader, "_dataDir", lambda category="scan": scanDir)
    monkeypatch.setattr(dataLoader, "_IS_PYODIDE", False, raising=False)
    monkeypatch.setattr(parquet, "_scanDownloaded", False, raising=False)
    return scanDir


def test_ensureScanData_downloads_missing_root_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import dartlab.scan.io.parquet as parquet

    scanDir = _patchScanRoot(monkeypatch, tmp_path)
    downloaded: list[str] = []

    def fakeDownload(targetDir: Path, relativePath: str) -> None:
        downloaded.append(relativePath)
        path = targetDir / relativePath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"parquet")

    monkeypatch.setattr(parquet, "_downloadScanFile", fakeDownload)

    assert parquet._ensureScanData() == scanDir
    assert set(downloaded) == set(parquet._REQUIRED_SCAN_ROOT_FILES)
    assert parquet._isScanRootComplete(scanDir)


def test_ensureScanData_downloads_report_files_when_required(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import dartlab.scan.io.parquet as parquet

    scanDir = _patchScanRoot(monkeypatch, tmp_path)
    downloaded: list[str] = []

    def fakeDownload(targetDir: Path, relativePath: str) -> None:
        downloaded.append(relativePath)
        path = targetDir / relativePath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"parquet")

    monkeypatch.setattr(parquet, "_downloadScanFile", fakeDownload)

    assert parquet._ensureScanData(requireReports=True) == scanDir
    assert set(downloaded) == {
        *parquet._REQUIRED_SCAN_ROOT_FILES,
        *(f"report/{name}" for name in parquet._REQUIRED_REPORT_FILES),
    }
    assert parquet._isScanComplete(scanDir)


def test_ensureScanData_propagates_download_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """필수 prebuild 조달 실패를 사용 가능한 빈 디렉토리로 위장하지 않는다."""

    import dartlab.scan.io.parquet as parquet

    _patchScanRoot(monkeypatch, tmp_path)

    def failDownload(_targetDir: Path, relativePath: str) -> None:
        raise OSError(f"cannot download {relativePath}")

    monkeypatch.setattr(parquet, "_downloadScanFile", failDownload)

    with pytest.raises(parquet.ScanDataError, match="stage=prebuild_download"):
        parquet._ensureScanData()


def test_ensureScanData_revalidates_cached_artifacts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """process cache가 켜진 뒤 삭제된 필수 artifact도 다시 조달한다."""

    import dartlab.scan.io.parquet as parquet

    scanDir = _patchScanRoot(monkeypatch, tmp_path)
    for name in parquet._REQUIRED_SCAN_ROOT_FILES:
        path = scanDir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"parquet")
    monkeypatch.setattr(parquet, "_scanDownloaded", True)
    missing = scanDir / parquet._REQUIRED_SCAN_ROOT_FILES[0]
    missing.unlink()
    downloaded: list[str] = []

    def fakeDownload(targetDir: Path, relativePath: str) -> None:
        downloaded.append(relativePath)
        (targetDir / relativePath).write_bytes(b"parquet")

    monkeypatch.setattr(parquet, "_downloadScanFile", fakeDownload)

    assert parquet._ensureScanData() == scanDir
    assert downloaded == [parquet._REQUIRED_SCAN_ROOT_FILES[0]]


def test_ensureScanArtifact_downloads_only_requested_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import dartlab.scan.io.parquet as parquet

    scanDir = tmp_path / "scan"
    downloaded: list[str] = []
    monkeypatch.setattr(parquet, "_ensureScanData", lambda: scanDir)

    def fakeDownload(targetDir: Path, relativePath: str) -> None:
        downloaded.append(relativePath)
        destination = targetDir / relativePath
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"parquet")

    monkeypatch.setattr(parquet, "_downloadScanFile", fakeDownload)

    result = parquet.ensureScanArtifact("network/affiliateDocs.parquet")

    assert result == scanDir / "network" / "affiliateDocs.parquet"
    assert downloaded == ["network/affiliateDocs.parquet"]


def test_prepareRealdataScanCache_builds_from_fixture_sources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import importlib.util

    import dartlab.scan.builders.kr.common as common
    import dartlab.scan.builders.kr.core as core
    import dartlab.scan.builders.kr.shares as shares
    import dartlab.scan.io.parquet as parquet

    script_path = Path(".github/scripts/ops/prepareRealdataScanCache.py").resolve()
    spec = importlib.util.spec_from_file_location("prepare_realdata_scan_cache", script_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    calls: list[str] = []
    scan_dir = tmp_path / "dart" / "scan"

    def write_required_outputs() -> None:
        for name in parquet._REQUIRED_SCAN_ROOT_FILES:
            (scan_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (scan_dir / name).write_bytes(b"parquet")
        for name in parquet._REQUIRED_REPORT_FILES:
            path = scan_dir / "report" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"parquet")

    monkeypatch.setattr(common, "scanDir", lambda: scan_dir)
    monkeypatch.setattr(core, "buildChanges", lambda **_kwargs: calls.append("changes") or scan_dir / "changes.parquet")
    monkeypatch.setattr(core, "buildFinance", lambda **_kwargs: calls.append("finance") or scan_dir / "finance.parquet")
    monkeypatch.setattr(
        core, "buildFinanceLite", lambda **_kwargs: calls.append("finance-lite") or scan_dir / "finance-lite.parquet"
    )
    monkeypatch.setattr(core, "buildReport", lambda **_kwargs: calls.append("report") or [])
    monkeypatch.setattr(
        core,
        "buildAffiliateDocs",
        lambda **_kwargs: calls.append("affiliate-docs") or scan_dir / "network" / "affiliateDocs.parquet",
    )
    monkeypatch.setattr(
        shares,
        "buildSharesOutstandingSafe",
        lambda **_kwargs: calls.append("shares") or scan_dir / "sharesOutstanding.parquet",
    )
    monkeypatch.setattr(parquet, "_ensureScanData", lambda **_kwargs: pytest.fail("_ensureScanData must not be called"))
    monkeypatch.setattr(parquet, "_missingScanFiles", lambda *_args, **_kwargs: write_required_outputs() or [])

    assert mod.main() == 0
    assert calls == ["changes", "finance", "finance-lite", "report", "shares", "affiliate-docs"]


def test_prepareRealdataScanCache_preserves_existing_report_prebuilds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import importlib.util

    import dartlab.scan.builders.kr.common as common
    import dartlab.scan.builders.kr.core as core
    import dartlab.scan.builders.kr.shares as shares
    import dartlab.scan.io.parquet as parquet

    script_path = Path(".github/scripts/ops/prepareRealdataScanCache.py").resolve()
    spec = importlib.util.spec_from_file_location("prepare_realdata_scan_cache", script_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    scan_dir = tmp_path / "dart" / "scan"
    report_dir = scan_dir / "report"
    report_dir.mkdir(parents=True)
    for name in parquet._REQUIRED_SCAN_ROOT_FILES:
        (scan_dir / name).write_bytes(b"parquet")
    (scan_dir / "finance-lite.parquet").write_bytes(b"parquet")
    affiliate_docs = scan_dir / "network" / "affiliateDocs.parquet"
    affiliate_docs.parent.mkdir(parents=True)
    import polars as pl

    from dartlab.scan.network.affiliates import (
        AFFILIATE_DOCS_SCHEMA,
        AFFILIATE_DOCS_SCHEMA_VERSION,
    )

    pl.DataFrame(
        {
            "sourceStockCode": ["000001"],
            "affiliateStockCode": ["000001"],
            "sourcePeriod": ["2024Q4"],
            "sourceRceptNo": ["20250319000001"],
            "groupName": [None],
            "datasetAsOf": ["20250319"],
            "schemaVersion": [AFFILIATE_DOCS_SCHEMA_VERSION],
        },
        schema=AFFILIATE_DOCS_SCHEMA,
    ).write_parquet(affiliate_docs)
    missing_report = "commercialPaper.parquet"
    for name in parquet._REQUIRED_REPORT_FILES:
        if name != missing_report:
            (report_dir / name).write_bytes(b"preserve")

    built_report_api_types: list[tuple[str, ...]] = []

    def build_missing_reports(**kwargs) -> list[Path]:
        api_types = tuple(kwargs.get("apiTypes") or ())
        built_report_api_types.append(api_types)
        for api_type in api_types:
            (report_dir / f"{api_type}.parquet").write_bytes(b"built")
        return [report_dir / f"{api_type}.parquet" for api_type in api_types]

    monkeypatch.setattr(common, "scanDir", lambda: scan_dir)
    monkeypatch.setattr(core, "buildChanges", lambda **_kwargs: pytest.fail("existing changes must be preserved"))
    monkeypatch.setattr(core, "buildFinance", lambda **_kwargs: pytest.fail("existing finance must be preserved"))
    monkeypatch.setattr(
        core, "buildFinanceLite", lambda **_kwargs: pytest.fail("existing finance-lite must be preserved")
    )
    monkeypatch.setattr(core, "buildReport", build_missing_reports)
    monkeypatch.setattr(
        core,
        "buildAffiliateDocs",
        lambda **_kwargs: pytest.fail("current affiliateDocs must be preserved"),
    )
    monkeypatch.setattr(
        shares,
        "buildSharesOutstandingSafe",
        lambda **_kwargs: pytest.fail("existing sharesOutstanding must be preserved"),
    )

    assert mod.main() == 0
    assert built_report_api_types == [("commercialPaper",)]
    assert (report_dir / missing_report).read_bytes() == b"built"
    assert (report_dir / "majorHolder.parquet").read_bytes() == b"preserve"

    legacy = pl.read_parquet(affiliate_docs).with_columns(pl.lit(1, dtype=pl.Int16).alias("schemaVersion"))
    legacy.write_parquet(affiliate_docs)
    affiliate_rebuilds: list[bool] = []

    def rebuild_affiliates(**_kwargs) -> Path:
        affiliate_rebuilds.append(True)
        legacy.with_columns(pl.lit(AFFILIATE_DOCS_SCHEMA_VERSION, dtype=pl.Int16).alias("schemaVersion")).write_parquet(
            affiliate_docs
        )
        return affiliate_docs

    monkeypatch.setattr(core, "buildAffiliateDocs", rebuild_affiliates)

    assert mod.main() == 0
    assert affiliate_rebuilds == [True]


# ---------------------------------------------------------------------------
# freshness 재검증 (TTL + ETag) — HF 일일 갱신 추적 배선
# ---------------------------------------------------------------------------


def _freshnessSandbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """freshness 테스트 공용 격리: scanDir + 세션 메모 리셋 + 실네트워크 차단."""
    import dartlab.core.dataLoader as dataLoader
    import dartlab.scan.io.parquet as parquet

    scanDir = _patchScanRoot(monkeypatch, tmp_path)
    scanDir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(parquet, "_scanFreshnessCheckedAt", {}, raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)

    def _noNetwork(*_args, **_kwargs):
        raise AssertionError("network call not expected in this test")

    monkeypatch.setattr(dataLoader, "_checkRemoteFreshness", _noNetwork)
    monkeypatch.setattr(parquet, "_downloadScanFile", _noNetwork)
    return scanDir


def _writeArtifact(scanDir: Path, rel: str, *, etagAgeHours: float | None) -> Path:
    """rel parquet 더미 + (선택) 백데이트된 etag 사이드카를 만든다."""
    import os
    import time

    dest = scanDir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"parquet")
    if etagAgeHours is not None:
        etag = dest.with_suffix(".parquet.etag")
        etag.write_text("local-etag", encoding="utf-8")
        old = time.time() - etagAgeHours * 3600
        os.utime(etag, (old, old))
    return dest


def test_maybeRefresh_skips_within_ttl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """etag 사이드카가 TTL(12h) 이내면 원격 확인 0회."""
    import dartlab.scan.io.parquet as parquet

    scanDir = _freshnessSandbox(monkeypatch, tmp_path)
    _writeArtifact(scanDir, "finance.parquet", etagAgeHours=1)

    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")  # _noNetwork 트랩이 안 걸려야 통과


def test_maybeRefresh_fresh_remote_touches_etag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """TTL 만료 후 원격이 동일(fresh)하면 etag mtime 만 갱신하고 다운로드 없음."""
    import dartlab.core.dataLoader as dataLoader
    import dartlab.scan.io.parquet as parquet

    scanDir = _freshnessSandbox(monkeypatch, tmp_path)
    dest = _writeArtifact(scanDir, "finance.parquet", etagAgeHours=13)
    etag = dest.with_suffix(".parquet.etag")
    oldMtime = etag.stat().st_mtime

    monkeypatch.setattr(dataLoader, "_checkRemoteFreshness", lambda *_a, **_k: False)

    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")
    assert etag.stat().st_mtime > oldMtime, "fresh 판정 후 etag touch 로 TTL 리셋해야 함"


def test_maybeRefresh_stale_redownloads(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """TTL 만료 + 원격 ETag 불일치(stale)면 재다운로드."""
    import dartlab.core.dataLoader as dataLoader
    import dartlab.scan.io.parquet as parquet

    scanDir = _freshnessSandbox(monkeypatch, tmp_path)
    _writeArtifact(scanDir, "finance.parquet", etagAgeHours=13)
    downloaded: list[str] = []

    monkeypatch.setattr(dataLoader, "_checkRemoteFreshness", lambda *_a, **_k: True)
    monkeypatch.setattr(parquet, "_downloadScanFile", lambda _d, rel: downloaded.append(rel))

    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")
    assert downloaded == ["finance.parquet"]


def test_maybeRefresh_check_failure_keeps_local(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """신선도 확인 실패(None)면 다운로드 없이 로컬 유지."""
    import dartlab.core.dataLoader as dataLoader
    import dartlab.scan.io.parquet as parquet

    scanDir = _freshnessSandbox(monkeypatch, tmp_path)
    dest = _writeArtifact(scanDir, "finance.parquet", etagAgeHours=13)

    monkeypatch.setattr(dataLoader, "_checkRemoteFreshness", lambda *_a, **_k: None)

    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")  # _downloadScanFile 트랩 미발동이 곧 검증
    assert dest.read_bytes() == b"parquet"


def test_maybeRefresh_respects_no_refresh_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """DARTLAB_NO_REFRESH=1 이면 TTL 만료여도 network 0회 (eager sandbox 계약)."""
    import dartlab.scan.io.parquet as parquet

    scanDir = _freshnessSandbox(monkeypatch, tmp_path)
    _writeArtifact(scanDir, "finance.parquet", etagAgeHours=48)
    monkeypatch.setenv("DARTLAB_NO_REFRESH", "1")

    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")  # _noNetwork 트랩 미발동이 곧 검증


def test_maybeRefresh_session_memo_limits_attempts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """같은 프로세스에서 재확인 시도는 memo 간격(15분) 내 1회로 제한."""
    import dartlab.core.dataLoader as dataLoader
    import dartlab.scan.io.parquet as parquet

    scanDir = _freshnessSandbox(monkeypatch, tmp_path)
    _writeArtifact(scanDir, "finance.parquet", etagAgeHours=13)
    calls: list[int] = []

    def _countCheck(*_a, **_k):
        calls.append(1)
        return None  # 확인 실패: etag mtime 미갱신 → memo 없으면 매번 재시도됐을 상황

    monkeypatch.setattr(dataLoader, "_checkRemoteFreshness", _countCheck)

    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")
    parquet._maybeRefreshScanFile(scanDir, "finance.parquet")
    assert len(calls) == 1


def test_ensureScanData_complete_runs_freshness_sweep(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """필수 파일이 모두 있어도 존재 확인으로 끝내지 않고 freshness 스윕을 태운다."""
    import dartlab.scan.io.parquet as parquet

    scanDir = _patchScanRoot(monkeypatch, tmp_path)
    scanDir.mkdir(parents=True, exist_ok=True)
    for name in parquet._REQUIRED_SCAN_ROOT_FILES:
        (scanDir / name).write_bytes(b"parquet")
    swept: list[str] = []
    monkeypatch.setattr(parquet, "_maybeRefreshScanFile", lambda _d, rel: swept.append(rel))

    assert parquet._ensureScanData() == scanDir
    assert swept == list(parquet._REQUIRED_SCAN_ROOT_FILES)


def test_downloadScanFile_validates_and_saves_etag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """다운로드 후 canonical 계약(무결성 검증 + etag 사이드카)을 지킨다."""
    import polars as pl

    import dartlab.core.dataLoader as dataLoader
    import dartlab.core.hfRetry as hfRetry
    import dartlab.scan.io.parquet as parquet

    scanDir = tmp_path / "scan"
    scanDir.mkdir()
    valid = tmp_path / "hub" / "finance.parquet"
    valid.parent.mkdir()
    pl.DataFrame({"stockCode": ["005930"]}).write_parquet(str(valid))

    monkeypatch.setattr(hfRetry, "retryHfCall", lambda _fn, **_k: str(valid))
    savedEtags: list[tuple[str, str]] = []
    monkeypatch.setattr(dataLoader, "_saveEtag", lambda stem, dest, category: savedEtags.append((stem, category)))

    parquet._downloadScanFile(scanDir, "finance.parquet")
    assert (scanDir / "finance.parquet").exists()
    assert savedEtags == [("finance", "scan")]


def test_downloadScanFile_rejects_corrupt_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """손상 payload 는 canonical 확정 전에 거부한다 (기존 파일 미교체)."""
    import dartlab.core.hfRetry as hfRetry
    import dartlab.scan.io.parquet as parquet

    scanDir = tmp_path / "scan"
    scanDir.mkdir()
    corrupt = tmp_path / "hub" / "finance.parquet"
    corrupt.parent.mkdir()
    corrupt.write_bytes(b"not a parquet")

    monkeypatch.setattr(hfRetry, "retryHfCall", lambda _fn, **_k: str(corrupt))

    with pytest.raises(OSError):
        parquet._downloadScanFile(scanDir, "finance.parquet")
    assert not (scanDir / "finance.parquet").exists()
