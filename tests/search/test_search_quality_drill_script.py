"""Search quality toolchain drill tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/runSearchQualityDrill.py")


def test_run_search_quality_drill_writes_non_release_report(tmp_path: Path) -> None:
    out = tmp_path / "qualityDrill.json"
    gold = tmp_path / "gold.jsonl"
    labels = tmp_path / "labels.jsonl"
    miss = tmp_path / "miss.jsonl"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--out",
            str(out),
            "--canonical-gold",
            str(gold),
            "--label-template",
            str(labels),
            "--miss-ledger",
            str(miss),
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
    assert report["valid"] is True
    assert report["releaseEvidence"] is False
    assert report["summary"]["releaseEligible"] is True
    assert report["quality"]["releaseEligible"] is True
    assert report["quality"]["coverageByKind"]["edgar"] == 1
    assert gold.exists()
    goldRows = [json.loads(line) for line in gold.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert {row["goldOrigin"] for row in goldRows} == {"drillSynthetic"}
    assert {row["reviewStatus"] for row in goldRows} == {"drillReviewed"}
    assert labels.exists()
    assert miss.exists()
