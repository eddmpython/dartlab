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
        shares,
        "buildSharesOutstandingSafe",
        lambda **_kwargs: calls.append("shares") or scan_dir / "sharesOutstanding.parquet",
    )
    monkeypatch.setattr(parquet, "_ensureScanData", lambda **_kwargs: pytest.fail("_ensureScanData must not be called"))
    monkeypatch.setattr(parquet, "_missingScanFiles", lambda *_args, **_kwargs: write_required_outputs() or [])

    assert mod.main() == 0
    assert calls == ["changes", "finance", "finance-lite", "report", "shares"]


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
        shares,
        "buildSharesOutstandingSafe",
        lambda **_kwargs: pytest.fail("existing sharesOutstanding must be preserved"),
    )

    assert mod.main() == 0
    assert built_report_api_types == [("commercialPaper",)]
    assert (report_dir / missing_report).read_bytes() == b"built"
    assert (report_dir / "majorHolder.parquet").read_bytes() == b"preserve"
