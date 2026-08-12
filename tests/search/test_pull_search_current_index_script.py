"""pullSearchCurrentIndex script tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _writeJson(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def test_pull_search_current_index_follows_manifest_file_sources(tmp_path) -> None:
    remote = tmp_path / "remote"
    outDir = tmp_path / "contentIndex"
    previous = outDir / "previous_manifest.json"
    _writeJson(
        remote / "dart/contentIndex/manifest.json",
        {
            "publishMode": "manifestPointer",
            "requiredFiles": ["main.npz", "main_stems.json"],
            "fileSources": {
                "main.npz": "dart/contentIndex/_staging/full-run/main.npz",
                "main_stems.json": "dart/contentIndex/_staging/full-run/main_stems.json",
                "catalog_snapshot.parquet": "dart/contentIndex/_staging/full-run/catalog_snapshot.parquet",
            },
        },
    )
    stage = remote / "dart/contentIndex/_staging/full-run"
    stage.mkdir(parents=True)
    (stage / "main.npz").write_bytes(b"main")
    (stage / "main_stems.json").write_bytes(b"{}")
    (stage / "catalog_snapshot.parquet").write_bytes(b"PAR1")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/pullSearchCurrentIndex.py",
            "--remote-root",
            str(remote),
            "--out-dir",
            str(outDir),
            "--previous-manifest",
            str(previous),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert (outDir / "main.npz").read_bytes() == b"main"
    assert (outDir / "main_stems.json").read_bytes() == b"{}"
    assert (outDir / "catalog_snapshot.parquet").read_bytes() == b"PAR1"
    assert json.loads(previous.read_text(encoding="utf-8"))["fileSources"]["main.npz"].endswith("main.npz")


def test_pull_search_current_index_allows_manifest_already_in_target_dir(tmp_path) -> None:
    remote = tmp_path / "remote"
    outDir = remote / "dart/contentIndex"
    previous = outDir / "previous_manifest.json"
    _writeJson(
        outDir / "manifest.json",
        {
            "publishMode": "manifestPointer",
            "requiredFiles": ["main.npz"],
            "fileSources": {"main.npz": "dart/contentIndex/_staging/full-run/main.npz"},
        },
    )
    stage = remote / "dart/contentIndex/_staging/full-run"
    stage.mkdir(parents=True)
    (stage / "main.npz").write_bytes(b"main")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/pullSearchCurrentIndex.py",
            "--remote-root",
            str(remote),
            "--out-dir",
            str(outDir),
            "--previous-manifest",
            str(previous),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert (outDir / "main.npz").read_bytes() == b"main"
    assert previous.exists()


def test_pull_search_current_index_fails_on_missing_required_file(tmp_path) -> None:
    remote = tmp_path / "remote"
    outDir = tmp_path / "contentIndex"
    _writeJson(
        remote / "dart/contentIndex/manifest.json",
        {
            "publishMode": "manifestPointer",
            "requiredFiles": ["main.npz"],
            "fileSources": {"main.npz": "dart/contentIndex/_staging/full-run/main.npz"},
        },
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/pullSearchCurrentIndex.py",
            "--remote-root",
            str(remote),
            "--out-dir",
            str(outDir),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 1
    assert "required:main.npz:FileNotFoundError" in proc.stdout


def test_pull_search_current_index_activates_main_and_delta_from_one_manifest(tmp_path) -> None:
    """Regression for #107: hasDelta manifest의 전체 파일을 같은 pointer에서 가져온다."""
    remote = tmp_path / "remote"
    outDir = tmp_path / "contentIndex"
    stage = remote / "dart/contentIndex/_staging/full-run"
    stage.mkdir(parents=True)
    payloads = {
        "main_info.json": b'{"nDocs":1}',
        "main_meta.parquet": b"main-meta",
        "delta_info.json": b'{"nDocs":1}',
        "delta_meta.parquet": b"delta-meta",
    }
    for name, payload in payloads.items():
        (stage / name).write_bytes(payload)
    _writeJson(
        remote / "dart/contentIndex/manifest.json",
        {
            "publishMode": "manifestPointer",
            "hasDelta": True,
            "requiredFiles": list(payloads),
            "fileSources": {name: f"dart/contentIndex/_staging/full-run/{name}" for name in payloads},
            "fileHashes": {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
        },
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/pullSearchCurrentIndex.py",
            "--remote-root",
            str(remote),
            "--out-dir",
            str(outDir),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(proc.stdout)
    assert report["valid"] is True
    assert report["activationMode"] == "stagedManifestLast"
    assert set(report["verifiedHashes"]) == set(payloads)
    assert all((outDir / name).read_bytes() == payload for name, payload in payloads.items())


def test_pull_search_current_index_failure_preserves_active_manifest_and_segments(tmp_path) -> None:
    """Regression for #107: delta pull 실패 중 기존 활성 쌍을 절반만 교체하지 않는다."""
    remote = tmp_path / "remote"
    outDir = tmp_path / "contentIndex"
    outDir.mkdir(parents=True)
    _writeJson(outDir / "manifest.json", {"builtAt": "old", "requiredFiles": ["main_meta.parquet"]})
    (outDir / "main_meta.parquet").write_bytes(b"old-main")

    stage = remote / "dart/contentIndex/_staging/new-run"
    stage.mkdir(parents=True)
    (stage / "main_meta.parquet").write_bytes(b"new-main")
    _writeJson(
        remote / "dart/contentIndex/manifest.json",
        {
            "builtAt": "new",
            "publishMode": "manifestPointer",
            "hasDelta": True,
            "requiredFiles": ["main_meta.parquet", "delta_info.json", "delta_meta.parquet"],
            "fileSources": {
                "main_meta.parquet": "dart/contentIndex/_staging/new-run/main_meta.parquet",
                "delta_info.json": "dart/contentIndex/_staging/new-run/delta_info.json",
                "delta_meta.parquet": "dart/contentIndex/_staging/new-run/delta_meta.parquet",
            },
        },
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/pullSearchCurrentIndex.py",
            "--remote-root",
            str(remote),
            "--out-dir",
            str(outDir),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )

    assert proc.returncode == 1
    assert json.loads((outDir / "manifest.json").read_text(encoding="utf-8"))["builtAt"] == "old"
    assert (outDir / "main_meta.parquet").read_bytes() == b"old-main"
    assert not (outDir / "delta_meta.parquet").exists()
