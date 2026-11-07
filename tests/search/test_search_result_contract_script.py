"""Search result contract CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _row(*, source_ref: str = "news:a", data_as_of: str = "20260615") -> dict[str, object]:
    return {
        "source": "news",
        "sourceRef": source_ref,
        "dataAsOf": data_as_of,
        "snippet": "뉴스 근거",
        "answerable": True,
        "fieldCards": [
            {
                "label": "sourceRef",
                "value": source_ref,
                "sourceRef": source_ref,
                "evidence": "뉴스 근거",
            }
        ],
    }


def test_evaluate_search_result_contract_script_accepts_precomputed_results(tmp_path) -> None:
    results = tmp_path / "results.json"
    out = tmp_path / "report.json"
    results.write_text(json.dumps({"뉴스": [_row()]}, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/evaluateSearchResultContract.py",
            "--results-json",
            str(results),
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is True


def test_evaluate_search_result_contract_script_fails_on_missing_source_ref(tmp_path) -> None:
    results = tmp_path / "results.json"
    out = tmp_path / "report.json"
    results.write_text(json.dumps({"뉴스": [_row(source_ref="", data_as_of="")]}, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/evaluateSearchResultContract.py",
            "--results-json",
            str(results),
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert set(report["invalidRows"][0]["reasons"]) >= {"missingSourceRef", "missingDataAsOf"}
