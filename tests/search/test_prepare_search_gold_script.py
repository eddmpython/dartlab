"""prepareSearchGold script tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_prepare_search_gold_script_merges_labels_and_writes_summary(tmp_path) -> None:
    raw = tmp_path / "raw.jsonl"
    labels = tmp_path / "labels.jsonl"
    out = tmp_path / "queryLogGold.real.jsonl"
    summary = tmp_path / "summary.json"
    raw.write_text(
        "\n".join(
            [
                json.dumps({"queryId": "a", "q": "뉴스 원문"}, ensure_ascii=False),
                json.dumps({"queryId": "b", "q": "없는 공시"}, ensure_ascii=False),
            ]
        ),
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "queryId": "a",
                        "target": "news",
                        "expectedSourceRef": "news:a",
                        "goldOrigin": "real",
                        "reviewStatus": "reviewed",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "queryId": "b",
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

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/prepareSearchGold.py",
            "--input",
            str(raw),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
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
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert rows[0]["expectedSourceRef"] == "news:a"
    assert rows[1]["expectedAnswerable"] is False
    assert data["releaseEligible"] is True


def test_prepare_search_gold_script_writes_label_template(tmp_path) -> None:
    raw = tmp_path / "raw.jsonl"
    out = tmp_path / "gold.jsonl"
    template = tmp_path / "labels.todo.jsonl"
    raw.write_text(
        json.dumps(
            {
                "queryId": "a",
                "query": "뉴스 원문",
                "topSourceRefs": ["news:a"],
                "goldOrigin": "userLog",
                "reviewStatus": "candidate",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/prepareSearchGold.py",
            "--input",
            str(raw),
            "--out",
            str(out),
            "--label-template",
            str(template),
            "--allow-proxy-query-log",
            "--allow-missing-source-ref",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    labels = [json.loads(line) for line in template.read_text(encoding="utf-8").splitlines()]
    assert labels[0]["candidateSourceRefs"] == ["news:a"]
    assert labels[0]["expectedSourceRef"] == ""
    assert labels[0]["reviewStatus"] == "draft"


def test_prepare_search_gold_script_fails_on_unreviewed_missing_source_ref(tmp_path) -> None:
    raw = tmp_path / "raw.jsonl"
    out = tmp_path / "gold.jsonl"
    summary = tmp_path / "summary.json"
    raw.write_text(
        json.dumps({"query": "뉴스 원문", "target": "news", "goldOrigin": "proxy"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/prepareSearchGold.py",
            "--input",
            str(raw),
            "--out",
            str(out),
            "--summary",
            str(summary),
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
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["invalidRows"][0]["reasons"] == [
        "missingExpectedSourceRef",
        "proxyGoldOrigin",
        "unreviewedGold",
    ]
