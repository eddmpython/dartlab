"""finalizeSearchReviewLabels script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


FINALIZE_SCRIPT = Path(".github/scripts/search/finalizeSearchReviewLabels.py")
PREPARE_SCRIPT = Path(".github/scripts/search/prepareSearchGold.py")


def test_finalize_search_review_labels_requires_decision(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    out = tmp_path / "labels.reviewed.jsonl"
    summary = tmp_path / "summary.json"
    labels.write_text(
        json.dumps(
            {
                "queryId": "q1",
                "query": "유상증자 공시 원문",
                "proposedTargetKind": "filing",
                "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
                "reviewStatus": "draft",
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
            str(FINALIZE_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--reviewer",
            "qa-operator",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["blockers"] == ["undecidedRows:1"]
    assert data["reviewedRows"] == 0


def test_finalize_search_review_labels_materializes_explicit_proposals(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    out = tmp_path / "labels.reviewed.jsonl"
    summary = tmp_path / "summary.json"
    labels.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "queryId": "q1",
                        "query": "유상증자 공시 원문",
                        "proposedTargetKind": "filing",
                        "proposedExpectedAnswerable": True,
                        "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
                        "proposedExpectedSourceRefs": [
                            "dart:allFilings:1#section=0",
                            "dart:allFilings:2#section=0",
                        ],
                        "reviewDecision": "acceptProposal",
                        "reviewer": "qa-operator",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "queryId": "q2",
                        "query": "없는회사 2099년 합병 공시",
                        "proposedTargetKind": "noAnswer",
                        "proposedExpectedAnswerable": False,
                        "reviewDecision": "verifiedNoAnswer",
                        "reviewer": "qa-operator",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(FINALIZE_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--reviewed-at",
            "2026-06-16T00:00:00Z",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["valid"] is True
    assert data["reviewedRows"] == 2
    assert rows[0]["targetKind"] == "filing"
    assert rows[0]["expectedAnswerable"] is True
    assert rows[0]["expectedSourceRef"] == "dart:allFilings:1#section=0"
    assert rows[0]["expectedSourceRefs"] == [
        "dart:allFilings:1#section=0",
        "dart:allFilings:2#section=0",
    ]
    assert rows[0]["reviewStatus"] == "reviewed"
    assert rows[0]["labeler"] == "qa-operator"
    assert rows[1]["targetKind"] == "noAnswer"
    assert rows[1]["expectedAnswerable"] is False
    assert "expectedSourceRef" not in rows[1]


def test_finalized_review_labels_feed_prepare_search_gold(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    labels = tmp_path / "labels.todo.jsonl"
    reviewed = tmp_path / "labels.reviewed.jsonl"
    gold = tmp_path / "queryLogGold.real.jsonl"
    summary = tmp_path / "queryLogGold.summary.json"
    raw.write_text(
        "\n".join(
            [
                json.dumps({"queryId": "q1", "query": "뉴스 원문"}, ensure_ascii=False),
                json.dumps({"queryId": "q2", "query": "없는 공시"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "queryId": "q1",
                        "query": "뉴스 원문",
                        "proposedTargetKind": "news",
                        "proposedExpectedAnswerable": True,
                        "proposedExpectedSourceRef": "news:a",
                        "reviewDecision": "acceptProposal",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "queryId": "q2",
                        "query": "없는 공시",
                        "proposedTargetKind": "noAnswer",
                        "proposedExpectedAnswerable": False,
                        "reviewDecision": "verifiedNoAnswer",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    finalizeProc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(FINALIZE_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(reviewed),
            "--reviewer",
            "qa-operator",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    assert finalizeProc.returncode == 0, finalizeProc.stderr + finalizeProc.stdout

    prepareProc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(PREPARE_SCRIPT),
            "--input",
            str(raw),
            "--labels",
            str(reviewed),
            "--out",
            str(gold),
            "--summary",
            str(summary),
            "--min-rows",
            "2",
            "--required-targets",
            "news,noAnswer",
            "--fail-on-ineligible",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert prepareProc.returncode == 0, prepareProc.stderr + prepareProc.stdout
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["releaseEligible"] is True
    assert data["realReviewedRows"] == 2
