"""Search remote evidence audit CLI tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit


def _writeJson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_check_search_remote_evidence_script_with_complete_local_remote(tmp_path) -> None:
    remote = tmp_path / "remote"
    out = tmp_path / "remoteEvidence.json"
    for source in ("allFilings", "dartPanel"):
        _writeJson(
            remote / f"dart/searchCatalog/{source}/{source}.source_manifest.json",
            {
                "source": source,
                "snapshotScope": "full",
                "dataAsOf": "20260615",
                "builtAt": "2026-06-15T00:00:00",
                "files": [{"path": f"{source}.parquet", "rowCount": 1}],
                "totalRows": 1,
                "changedRows": 1,
                "deletedRows": 0,
                "producer": "test",
                "producerRun": _producerRun(source),
            },
        )
        (remote / f"dart/searchCatalog/{source}/{source}.catalog_snapshot.parquet").write_bytes(b"parquet")

    _writeJson(
        remote / "dart/contentIndex/manifest.json",
        {
            "artifactVersion": "search-content-index-v1",
            "schemaVersion": 2,
            "builtAt": "2026-06-15T00:00:00",
            "publishMode": "manifestPointer",
            "requiredFiles": ["main.npz", "source_manifest_set.json", "entityGraphCatalog.parquet"],
            "fileSources": {
                "main.npz": "dart/contentIndex/_staging/run/main.npz",
                "source_manifest_set.json": "dart/contentIndex/_staging/run/source_manifest_set.json",
                "entityGraphCatalog.parquet": "dart/contentIndex/_staging/run/entityGraphCatalog.parquet",
            },
            "entityGraphCatalog": {
                "schemaVersion": "searchEntityGraphCatalog.v1",
                "nEntities": 3,
                "stockCodeCount": 3,
                "dataAsOf": "20260616",
            },
            "sourceDataAsOf": {"allFilings": "20260615"},
            "nDocsBySource": {"allFilings": 1},
        },
    )
    (remote / "dart/contentIndex/_staging/run").mkdir(parents=True, exist_ok=True)
    (remote / "dart/contentIndex/_staging/run/main.npz").write_bytes(b"main")
    (remote / "dart/contentIndex/_staging/run/entityGraphCatalog.parquet").write_bytes(b"graph")
    _writeJson(
        remote / "dart/contentIndex/_staging/run/source_manifest_set.json",
        {
            "schemaVersion": "searchSourceManifestSet.v1",
            "sourceManifestSetId": "manifest-set-1",
            "sources": [
                {"source": "allFilings", "producerRun": _producerRun("allFilings")},
                {"source": "dartPanel", "producerRun": _producerRun("dartPanel")},
            ],
        },
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/checkSearchRemoteEvidence.py",
            "--remote-root",
            str(remote),
            "--expected-sources",
            "allFilings,dartPanel",
            "--content-tiers",
            "full",
            "--out",
            str(out),
            "--fail-on-missing",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["sourceCatalog"]["missingSources"] == []
    assert report["sourceCatalog"]["sources"]["allFilings"]["manifest"]["totalRows"] == 1
    assert (
        report["sourceCatalog"]["sources"]["allFilings"]["manifest"]["producerRun"]["artifactName"]
        == "search-catalog-allFilings-allFilings-job-12345"
    )
    assert report["contentIndex"]["manifests"]["full"]["manifest"]["publishMode"] == "manifestPointer"
    assert report["contentIndex"]["manifests"]["full"]["manifest"]["sourceManifestSetSources"] == [
        "allFilings",
        "dartPanel",
    ]
    assert report["contentIndex"]["manifests"]["full"]["manifest"]["sourceManifestSetProducerRunMissingSources"] == []
    assert report["contentIndex"]["manifests"]["full"]["manifest"]["entityGraphCatalog"] == {
        "present": True,
        "required": True,
        "repoPath": "dart/contentIndex/_staging/run/entityGraphCatalog.parquet",
        "fileSourceExists": True,
        "schemaVersion": "searchEntityGraphCatalog.v1",
        "nEntities": 3,
        "stockCodeCount": 3,
        "dataAsOf": "20260616",
    }


def test_check_search_remote_evidence_script_uses_targeted_hf_file_probes(tmp_path, monkeypatch) -> None:
    payloads: dict[str, dict] = {}

    def addJson(repoPath: str, payload: dict) -> None:
        payloads[repoPath] = payload

    for source in ("allFilings", "dartPanel"):
        addJson(
            f"dart/searchCatalog/{source}/{source}.source_manifest.json",
            {
                "source": source,
                "snapshotScope": "full",
                "dataAsOf": "20260615",
                "builtAt": "2026-06-15T00:00:00",
                "files": [{"path": f"{source}.parquet", "rowCount": 1}],
                "totalRows": 1,
                "changedRows": 1,
                "deletedRows": 0,
                "producer": "test",
                "producerRun": _producerRun(source),
            },
        )
    addJson(
        "dart/contentIndex/manifest.json",
        {
            "artifactVersion": "search-content-index-v1",
            "schemaVersion": 2,
            "builtAt": "2026-06-15T00:00:00",
            "publishMode": "manifestPointer",
            "requiredFiles": ["main.npz", "source_manifest_set.json", "entityGraphCatalog.parquet"],
            "fileSources": {
                "main.npz": "dart/contentIndex/_staging/run/main.npz",
                "source_manifest_set.json": "dart/contentIndex/_staging/run/source_manifest_set.json",
                "entityGraphCatalog.parquet": "dart/contentIndex/_staging/run/entityGraphCatalog.parquet",
            },
            "entityGraphCatalog": {
                "schemaVersion": "searchEntityGraphCatalog.v1",
                "nEntities": 3,
                "stockCodeCount": 3,
                "dataAsOf": "20260616",
            },
            "sourceDataAsOf": {"allFilings": "20260615", "dartPanel": "20260615"},
            "nDocsBySource": {"allFilings": 1, "dartPanel": 1},
        },
    )
    addJson(
        "dart/contentIndex/_staging/run/source_manifest_set.json",
        {
            "schemaVersion": "searchSourceManifestSet.v1",
            "sourceManifestSetId": "manifest-set-1",
            "sources": [
                {"source": "allFilings", "producerRun": _producerRun("allFilings")},
                {"source": "dartPanel", "producerRun": _producerRun("dartPanel")},
            ],
        },
    )
    existing = set(payloads) | {
        "dart/searchCatalog/allFilings/allFilings.catalog_snapshot.parquet",
        "dart/searchCatalog/dartPanel/dartPanel.catalog_snapshot.parquet",
        "dart/contentIndex/_staging/run/main.npz",
        "dart/contentIndex/_staging/run/entityGraphCatalog.parquet",
    }
    fileExistsCalls: list[str] = []

    class FakeHfApi:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def file_exists(self, repo_id, filename, *, repo_type=None, revision=None, token=None) -> bool:
            fileExistsCalls.append(filename)
            return filename in existing

        def list_repo_files(self, *args, **kwargs):
            raise AssertionError("remote evidence audit must not recursively list HF dataset files")

    def fakeDownload(repo_id, repo_type, filename, local_dir, token=None):
        assert filename in payloads
        path = Path(local_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payloads[filename]), encoding="utf-8")
        return str(path)

    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(HfApi=FakeHfApi, hf_hub_download=fakeDownload),
    )
    module = _loadRemoteEvidenceScript()

    report = module.auditRemoteEvidence(
        repoId="test/repo",
        expectedSources=["allFilings", "dartPanel"],
        contentTiers=["full"],
        remoteRoot=None,
    )

    assert report["valid"] is True
    assert report["inventoryMode"] == "targetedProbe"
    assert report["fileCount"] is None
    assert report["checkedFileCount"] == len(set(fileExistsCalls))
    assert "dart/contentIndex/_staging/run/main.npz" in fileExistsCalls
    assert "dart/contentIndex/_staging/run/source_manifest_set.json" in fileExistsCalls


def test_check_search_remote_evidence_script_reports_missing_file_sources(tmp_path) -> None:
    remote = tmp_path / "remote"
    out = tmp_path / "remoteEvidence.json"
    _writeJson(
        remote / "dart/contentIndex/manifest.json",
        {
            "artifactVersion": "search-content-index-v1",
            "schemaVersion": 2,
            "builtAt": "2026-06-15T00:00:00",
            "publishMode": "manifestPointer",
            "requiredFiles": ["main.npz"],
            "fileSources": {"main.npz": "dart/contentIndex/_staging/run/main.npz"},
            "sourceDataAsOf": {},
            "nDocsBySource": {},
        },
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/checkSearchRemoteEvidence.py",
            "--remote-root",
            str(remote),
            "--expected-sources",
            "",
            "--content-tiers",
            "full",
            "--out",
            str(out),
            "--fail-on-missing",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert "contentIndexFileSourceMissing" in report["blockers"]
    assert "missingContentFileSource:full:main.npz" in report["errors"]


def test_check_search_remote_evidence_script_reports_missing_blockers(tmp_path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    out = tmp_path / "remoteEvidence.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/checkSearchRemoteEvidence.py",
            "--remote-root",
            str(remote),
            "--expected-sources",
            "allFilings",
            "--content-tiers",
            "full,lite",
            "--out",
            str(out),
            "--fail-on-missing",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert "sourceCatalogMissing" in report["blockers"]
    assert "contentIndexManifestMissing" in report["blockers"]
    assert "missingSourceManifest:allFilings" in report["errors"]
    assert "missingContentManifest:lite" in report["errors"]


def _producerRun(source: str) -> dict[str, str]:
    return {
        "system": "githubActions",
        "workflow": "test workflow",
        "job": f"{source}-job",
        "runId": "12345",
        "runAttempt": "1",
        "sha": "abc123",
        "ref": "master",
        "artifactName": f"search-catalog-{source}-{source}-job-12345",
    }


def _loadRemoteEvidenceScript():
    path = Path(".github/scripts/search/checkSearchRemoteEvidence.py")
    spec = importlib.util.spec_from_file_location("_dartlab_check_search_remote_evidence_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
