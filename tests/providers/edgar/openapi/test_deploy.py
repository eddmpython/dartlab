"""providers/edgar/openapi/deploy.py mirror smoke — P6."""

import hashlib
import json
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _writeScanManifest(scanDir: Path, parquets: list[Path]) -> None:
    """배포 테스트용 validator-sealed 8-artifact manifest를 기록한다."""

    artifacts = [
        {
            "path": path.relative_to(scanDir).as_posix(),
            "rows": 1,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in parquets
    ]
    (scanDir / "prebuild-manifest.json").write_text(
        json.dumps(
            {
                "kind": "dartlab.edgar.scan.prebuild",
                "schemaVersion": 1,
                "artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )


def test_imports():
    try:
        import dartlab.providers.edgar.openapi.deploy  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_deploy_edgar_to_h_f_callable() -> None:
    """deployEdgarToHF() callable smoke."""
    from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF

    assert callable(deployEdgarToHF)


def test_scan_deploy_uses_one_cas_commit_for_parquet_and_aggregates(tmp_path: Path, monkeypatch):
    """scan parquet와 US JSON 두 개를 같은 parent_commit 기반 HF commit으로 발행한다."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF

    scanDir = tmp_path / "data" / "edgar" / "scan"
    scanDir.mkdir(parents=True)
    parquets = []
    for index in range(8):
        path = scanDir / f"artifact-{index}.parquet"
        pl.DataFrame({"value": [index]}).write_parquet(path)
        parquets.append(path)
    _writeScanManifest(scanDir, parquets)
    financeJson = tmp_path / "landing" / "static" / "dashboards" / "finance-us.json"
    searchJson = tmp_path / "landing" / "static" / "map" / "search-index-us.json"
    financeJson.parent.mkdir(parents=True)
    searchJson.parent.mkdir(parents=True)
    financeJson.write_text("{}", encoding="utf-8")
    searchJson.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path / "data"))
    monkeypatch.setenv("HF_TOKEN", "test-token")

    calls: list[dict] = []

    class FakeApi:
        def __init__(self, **kwargs):
            pass

        def repo_info(self, **kwargs):
            return type("Info", (), {"sha": "parent-sha"})()

        def create_commit(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(huggingface_hub, "HfApi", FakeApi)
    result = deployEdgarToHF(categories=["scan"])

    assert result == {"scan": 11}
    assert len(calls) == 1
    assert calls[0]["parent_commit"] == "parent-sha"
    paths = {operation.path_in_repo for operation in calls[0]["operations"]}
    assert paths == {
        *(f"edgar/scan/artifact-{index}.parquet" for index in range(8)),
        "edgar/scan/prebuild-manifest.json",
        "landing/dashboards/finance-us.json",
        "landing/map/search-index-us.json",
    }


def test_scan_deploy_does_not_swallow_commit_failure(tmp_path: Path, monkeypatch):
    """HF commit 실패를 0건 성공으로 바꾸지 않는다."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF

    scanDir = tmp_path / "data" / "edgar" / "scan"
    scanDir.mkdir(parents=True)
    parquets = []
    for index in range(8):
        path = scanDir / f"artifact-{index}.parquet"
        pl.DataFrame({"value": [index]}).write_parquet(path)
        parquets.append(path)
    _writeScanManifest(scanDir, parquets)
    for relative in ("landing/static/dashboards/finance-us.json", "landing/static/map/search-index-us.json"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path / "data"))
    monkeypatch.setenv("HF_TOKEN", "test-token")

    class FailingApi:
        def __init__(self, **kwargs):
            pass

        def repo_info(self, **kwargs):
            return type("Info", (), {"sha": "parent-sha"})()

        def create_commit(self, **kwargs):
            raise RuntimeError("commit failed")

    monkeypatch.setattr(huggingface_hub, "HfApi", FailingApi)
    with pytest.raises(RuntimeError, match="commit failed"):
        deployEdgarToHF(categories=["scan"])


def test_scan_deploy_rejects_manifest_digest_drift(tmp_path: Path, monkeypatch):
    """manifest 봉인 뒤 바뀐 scan artifact는 HF 호출 전에 차단한다."""

    import dartlab.config as cfg
    from dartlab.providers.edgar.openapi.deploy import deployEdgarToHF

    scanDir = tmp_path / "data" / "edgar" / "scan"
    scanDir.mkdir(parents=True)
    parquets = []
    for index in range(8):
        path = scanDir / f"artifact-{index}.parquet"
        pl.DataFrame({"value": [index]}).write_parquet(path)
        parquets.append(path)
    _writeScanManifest(scanDir, parquets)
    pl.DataFrame({"value": [999]}).write_parquet(parquets[0])
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path / "data"))
    monkeypatch.setenv("HF_TOKEN", "test-token")

    with pytest.raises(ValueError, match="digest 불일치"):
        deployEdgarToHF(categories=["scan"])
