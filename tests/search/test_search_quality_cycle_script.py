"""runSearchQualityCycle script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/runSearchQualityCycle.py")


def test_search_quality_cycle_stops_on_undecided_review_rows(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    labels = tmp_path / "labels.todo.jsonl"
    outDir = tmp_path / "cycle"
    raw.write_text(json.dumps({"queryId": "q1", "query": "유상증자 공시"}, ensure_ascii=False) + "\n", encoding="utf-8")
    labels.write_text(
        json.dumps(
            {
                "queryId": "q1",
                "query": "유상증자 공시",
                "proposedTargetKind": "filing",
                "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
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
            str(SCRIPT),
            "--raw",
            str(raw),
            "--labels",
            str(labels),
            "--out-dir",
            str(outDir),
            "--reviewer",
            "qa-operator",
            "--min-rows",
            "1",
            "--required-targets",
            "filing",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads((outDir / "searchQualityCycle.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert report["failedPhase"] == "finalizeLabels"
    assert report["phases"][0]["returncode"] == 1


def test_search_quality_cycle_runs_reviewed_gold_to_quality_report(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    labels = tmp_path / "labels.todo.jsonl"
    results = tmp_path / "results.json"
    outDir = tmp_path / "cycle"
    raw.write_text(
        "\n".join(
            [
                json.dumps({"queryId": "q1", "query": "유상증자 공시"}, ensure_ascii=False),
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
                        "query": "유상증자 공시",
                        "proposedTargetKind": "filing",
                        "proposedExpectedAnswerable": True,
                        "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
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
    results.write_text(
        json.dumps(
            {
                "q1": [
                    {
                        "source": "allFilings",
                        "sourceRef": "dart:allFilings:1#section=0",
                        "answerable": True,
                    }
                ],
                "q2": [
                    {
                        "source": "allFilings",
                        "sourceRef": "dart:allFilings:other#section=0",
                        "answerable": False,
                    }
                ],
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
            str(SCRIPT),
            "--raw",
            str(raw),
            "--labels",
            str(labels),
            "--out-dir",
            str(outDir),
            "--reviewer",
            "qa-operator",
            "--results-json",
            str(results),
            "--min-rows",
            "2",
            "--required-targets",
            "filing,noAnswer",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads((outDir / "searchQualityCycle.json").read_text(encoding="utf-8"))
    quality = json.loads((outDir / "qualityReport.json").read_text(encoding="utf-8"))
    gold = [json.loads(line) for line in (outDir / "queryLogGold.real.jsonl").read_text(encoding="utf-8").splitlines()]
    assert report["valid"] is True
    assert report["failedPhase"] == ""
    assert [phase["name"] for phase in report["phases"]] == ["finalizeLabels", "prepareGold", "evaluateGold"]
    assert quality["releaseEligible"] is True
    assert quality["realReviewedRows"] == 2
    assert {row["reviewStatus"] for row in gold} == {"reviewed"}


def test_search_quality_cycle_can_batch_accept_suggested_decisions(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    results = tmp_path / "results.json"
    ceiling = tmp_path / "searchProposalQualityCeiling.json"
    evidence = tmp_path / "queryLogDecisionSheet.evidencePacket.json"
    outDir = tmp_path / "cycle"
    raw.write_text(
        "\n".join(
            [
                json.dumps({"queryId": "q1", "query": "유상증자 공시"}, ensure_ascii=False),
                json.dumps({"queryId": "q2", "query": "없는 공시"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    sheet.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "queryId": "q1",
                        "query": "유상증자 공시",
                        "targetKindHint": "filing",
                        "suggestedReviewDecision": "acceptProposal",
                        "proposedTargetKind": "filing",
                        "proposedExpectedAnswerable": True,
                        "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "queryId": "q2",
                        "query": "없는 공시",
                        "targetKindHint": "noAnswer",
                        "suggestedReviewDecision": "verifiedNoAnswer",
                        "proposedTargetKind": "noAnswer",
                        "proposedExpectedAnswerable": False,
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    results.write_text(
        json.dumps(
            {
                "q1": [{"source": "allFilings", "sourceRef": "dart:allFilings:1#section=0", "answerable": True}],
                "q2": [{"source": "allFilings", "sourceRef": "dart:allFilings:other#section=0", "answerable": False}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    ceiling.write_text(
        json.dumps(
            {
                "releaseEvidence": False,
                "invalidProposalRows": 0,
                "proxyRows": 2,
                "qualityReport": {"metricEligible": True, "blockers": ["proposalProxyNotReleaseEvidence"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    evidence.write_text(json.dumps(_evidencePacket(totalRows=2, readyRows=2), ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--raw",
            str(raw),
            "--labels",
            str(sheet),
            "--out-dir",
            str(outDir),
            "--reviewer",
            "qa-operator",
            "--reviewed-at",
            "2026-06-16T00:00:00Z",
            "--batch-accept-suggested",
            "--batch-quality-ceiling",
            str(ceiling),
            "--batch-require-metric-eligible",
            "--batch-evidence-packet",
            str(evidence),
            "--batch-require-evidence-ready",
            "--results-json",
            str(results),
            "--min-rows",
            "2",
            "--required-targets",
            "filing,noAnswer",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads((outDir / "searchQualityCycle.json").read_text(encoding="utf-8"))
    batch = json.loads((outDir / "queryLogDecisionSheet.batchReviewed.summary.json").read_text(encoding="utf-8"))
    quality = json.loads((outDir / "qualityReport.json").read_text(encoding="utf-8"))
    assert [phase["name"] for phase in report["phases"]] == [
        "batchReviewDecisions",
        "finalizeLabels",
        "prepareGold",
        "evaluateGold",
    ]
    assert report["valid"] is True
    assert batch["readyRows"] == 2
    assert batch["evidencePacket"]["ready"] is True
    assert quality["releaseEligible"] is True


def test_search_quality_cycle_stops_when_batch_evidence_packet_is_unready(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    evidence = tmp_path / "queryLogDecisionSheet.evidencePacket.json"
    outDir = tmp_path / "cycle"
    raw.write_text(json.dumps({"queryId": "q1", "query": "유상증자 공시"}, ensure_ascii=False) + "\n", encoding="utf-8")
    sheet.write_text(
        json.dumps(
            {
                "queryId": "q1",
                "query": "유상증자 공시",
                "targetKindHint": "filing",
                "suggestedReviewDecision": "acceptProposal",
                "proposedTargetKind": "filing",
                "proposedExpectedAnswerable": True,
                "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    evidence.write_text(
        json.dumps(
            _evidencePacket(
                totalRows=1,
                readyRows=0,
                valid=False,
                missingRows=1,
                blockers=["evidenceRowsNotReady:1"],
            ),
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--raw",
            str(raw),
            "--labels",
            str(sheet),
            "--out-dir",
            str(outDir),
            "--reviewer",
            "qa-operator",
            "--batch-accept-suggested",
            "--batch-evidence-packet",
            str(evidence),
            "--batch-require-evidence-ready",
            "--min-rows",
            "1",
            "--required-targets",
            "filing",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads((outDir / "searchQualityCycle.json").read_text(encoding="utf-8"))
    batch = json.loads((outDir / "queryLogDecisionSheet.batchReviewed.summary.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert report["failedPhase"] == "batchReviewDecisions"
    assert "evidencePacketReadyRows:0/1" in batch["blockers"]


def _evidencePacket(
    *,
    totalRows: int,
    readyRows: int,
    valid: bool = True,
    missingRows: int = 0,
    falseAcceptRows: int = 0,
    blockers: list[str] | None = None,
) -> dict[str, object]:
    return {
        "valid": valid,
        "releaseEvidence": False,
        "totalRows": totalRows,
        "evidenceReadyRows": readyRows,
        "missingEvidenceRows": missingRows,
        "falseAcceptRows": falseAcceptRows,
        "sourceCounts": {"allFilings": 2},
        "blockers": blockers or [],
    }
