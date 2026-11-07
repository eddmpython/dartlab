"""Search HF round-trip verification CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


class FakeHfApi:
    def __init__(self, remoteRoot: Path) -> None:
        self.remoteRoot = remoteRoot

    def upload_file(self, *, path_or_fileobj: str, path_in_repo: str, repo_id: str, repo_type: str) -> None:
        dst = self.remoteRoot / path_in_repo
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(Path(path_or_fileobj).read_bytes())

    def delete_file(self, *, path_in_repo: str, repo_id: str, repo_type: str) -> None:
        path = self.remoteRoot / path_in_repo
        if path.exists():
            path.unlink()


def test_verify_search_hf_roundtrip_script_with_local_remote(tmp_path) -> None:
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar, writeIndexManifest
    from dartlab.providers.dart.search.publishIndex import publishContentIndexFiles

    artifact = tmp_path / "artifact"
    remote = tmp_path / "remote"
    out = tmp_path / "roundtrip.json"
    base = tmp_path / "localContentIndex"
    rows = [
        {
            "section_content": "유상증자 자금조달 계획",
            "rcept_no": "20260615000001",
            "section_order": 0,
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "rcept_dt": "20260615",
            "report_nm": "주요사항보고서",
            "section_title": "",
            "source": "allFilings",
        }
    ]
    idx, meta = buildContentSegment(rows, showProgress=False)
    saveSegmentWithSidecar(idx, meta, "main", artifact)
    manifest = writeIndexManifest(artifact, tier="full", buildCommand="test.verifySearchHfRoundTrip")

    publishContentIndexFiles(
        token=None,
        indexDir=artifact,
        files=[*manifest["requiredFiles"], "manifest.json"],
        tier="full",
        runId="roundtrip-test",
        api=FakeHfApi(remote),
        repoId="repo",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/verifySearchHfRoundTrip.py",
            "--remote-root",
            str(remote),
            "--base-dir",
            str(base),
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["activation"]["activated"] is True
    assert report["rollback"]["rolledBack"] is True
    assert report["activatedManifest"]["publishMode"] == "manifestPointer"
    assert report["activatedManifest"]["fileSourcesCount"] >= 4
    assert report["restoredManifest"]["builtAt"] == "1900-01-01T00:00:00"


def test_verify_search_hf_roundtrip_script_accepts_staged_candidate_manifest(tmp_path) -> None:
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar, writeIndexManifest
    from dartlab.providers.dart.search.publishIndex import publishContentIndexFiles

    artifact = tmp_path / "artifact"
    remote = tmp_path / "remote"
    out = tmp_path / "roundtrip.json"
    base = tmp_path / "localContentIndex"
    rows = [
        {
            "section_content": "유상증자 자금조달 계획",
            "rcept_no": "20260615000001",
            "section_order": 0,
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "rcept_dt": "20260615",
            "report_nm": "주요사항보고서",
            "section_title": "",
            "source": "allFilings",
        }
    ]
    idx, meta = buildContentSegment(rows, showProgress=False)
    saveSegmentWithSidecar(idx, meta, "main", artifact)
    manifest = writeIndexManifest(artifact, tier="full", buildCommand="test.verifySearchHfRoundTrip.stage")

    summary = publishContentIndexFiles(
        token=None,
        indexDir=artifact,
        files=[*manifest["requiredFiles"], "manifest.json"],
        tier="full",
        runId="roundtrip-stage",
        api=FakeHfApi(remote),
        repoId="repo",
        promoteCurrent=False,
    )

    assert not (remote / "dart/contentIndex/manifest.json").exists()
    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/verifySearchHfRoundTrip.py",
            "--remote-root",
            str(remote),
            "--base-dir",
            str(base),
            "--manifest-repo-path",
            summary["candidateManifestPath"],
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["manifestRepoPath"] == summary["candidateManifestPath"]
    assert report["activation"]["activated"] is True
    assert report["rollback"]["rolledBack"] is True
