"""Search query-log gold CLI gate tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_evaluate_search_gold_script_with_precomputed_results(tmp_path) -> None:
    gold = tmp_path / "gold.jsonl"
    report = tmp_path / "quality.json"
    miss = tmp_path / "miss.jsonl"
    results = tmp_path / "results.json"
    gold.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "query": "뉴스 원문",
                        "target": "news",
                        "expectedSourceRef": "news:a",
                        "goldOrigin": "real",
                        "reviewStatus": "reviewed",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "query": "없는 공시",
                        "target": "noAnswer",
                        "goldOrigin": "real",
                        "reviewStatus": "reviewed",
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )
    results.write_text(
        json.dumps(
            {
                "뉴스 원문": [{"source": "news", "sourceRef": "news:a", "answerable": True}],
                "없는 공시": [{"source": "allFilings", "sourceRef": "dart:x", "answerable": False}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/evaluateSearchGold.py",
            "--gold",
            str(gold),
            "--results-json",
            str(results),
            "--out",
            str(report),
            "--miss-ledger",
            str(miss),
            "--min-rows",
            "2",
            "--required-targets",
            "news,noAnswer",
            "--fail-on-ineligible",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["releaseEligible"] is True
    assert data["metrics"]["overallReadyRate"] == 1.0
    assert miss.read_text(encoding="utf-8") == ""


def test_evaluate_search_gold_script_fails_on_proxy_gold(tmp_path) -> None:
    gold = tmp_path / "gold.jsonl"
    report = tmp_path / "quality.json"
    results = tmp_path / "results.json"
    gold.write_text(
        json.dumps(
            {
                "query": "뉴스 원문",
                "target": "news",
                "expectedSourceRef": "news:a",
                "goldOrigin": "runtimeGenerated",
                "reviewStatus": "reviewed",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    results.write_text(
        json.dumps({"뉴스 원문": [{"source": "news", "sourceRef": "news:a", "answerable": True}]}),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/evaluateSearchGold.py",
            "--gold",
            str(gold),
            "--results-json",
            str(results),
            "--out",
            str(report),
            "--min-rows",
            "1",
            "--required-targets",
            "news",
            "--fail-on-ineligible",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    data = json.loads(report.read_text(encoding="utf-8"))
    assert "proxyGoldRows:1" in data["blockers"]
