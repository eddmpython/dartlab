"""buildSearchReviewQuerySpecs script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/buildSearchReviewQuerySpecs.py")


def test_build_search_review_query_specs_default_pack(tmp_path: Path) -> None:
    out = tmp_path / "querySpecs.json"

    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(SCRIPT), "--out", str(out)],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(out.read_text(encoding="utf-8"))
    specs = data["queries"]
    assert data["summary"]["releaseEvidence"] is False
    assert data["summary"]["queryCount"] >= 100
    assert data["summary"]["coverageByTargetHint"] == {
        "edgar": 20,
        "filing": 56,
        "news": 20,
        "noAnswer": 12,
    }
    assert {row["scope"] for row in specs if row["targetKindHint"] == "news"} == {"news"}
    assert {row["scope"] for row in specs if row["reviewBucket"] == "filingContent"} == {"content"}


def test_build_search_review_query_specs_custom_counts_jsonl(tmp_path: Path) -> None:
    out = tmp_path / "querySpecs.jsonl"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--out",
            str(out),
            "--format",
            "jsonl",
            "--counts",
            "filingTitle=2,filingContent=1,news=1,edgar=1,noAnswer=1",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    specs = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(specs) == 6
    assert [row["reviewBucket"] for row in specs] == [
        "filingTitle",
        "filingTitle",
        "filingContent",
        "news",
        "edgar",
        "noAnswer",
    ]
