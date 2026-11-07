"""Search pipeline local drill CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_run_search_pipeline_drill_script(tmp_path) -> None:
    out = tmp_path / "drillReport.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/runSearchPipelineDrill.py",
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
    assert report["delta"]["valid"] is True
    assert report["preflight"]["valid"] is True
    assert report["sourceManifestSet"]["id"]
    assert set(report["sourceManifestSet"]["sources"]) == {"allFilings", "dartPanel", "edgarPanel", "newsPublic"}
    assert report["activation"]["activated"] is True
    assert report["rollback"]["rolledBack"] is True
    assert report["publish"]["publishMode"] == "manifestPointer"
    assert report["publish"]["uploaded"][-1] == "dart/contentIndex/manifest.json"
