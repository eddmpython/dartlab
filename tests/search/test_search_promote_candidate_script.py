"""Search candidate promotion CLI tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

SCRIPT = Path(".github/scripts/search/promoteSearchCandidate.py")


def test_promote_search_candidate_script_with_local_remote(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    candidate = remote / "dart/contentIndex/_staging/full-run/manifest.json"
    candidate.parent.mkdir(parents=True)
    candidate.write_text(
        json.dumps({"publishMode": "manifestPointer", "fileSources": {"main.npz": "staged/main.npz"}}),
        encoding="utf-8",
    )
    out = tmp_path / "promote.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--remote-root",
            str(remote),
            "--candidate-manifest-path",
            "dart/contentIndex/_staging/full-run/manifest.json",
            "--out",
            str(out),
            "--fail-on-error",
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
    current = remote / "dart/contentIndex/manifest.json"
    assert report["promoted"] is True
    assert report["candidateManifestPath"] == "dart/contentIndex/_staging/full-run/manifest.json"
    assert current.exists()
