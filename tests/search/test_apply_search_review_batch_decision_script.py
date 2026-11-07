"""applySearchReviewBatchDecision script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


BATCH_SCRIPT = Path(".github/scripts/search/applySearchReviewBatchDecision.py")
FINALIZE_SCRIPT = Path(".github/scripts/search/finalizeSearchReviewLabels.py")


def test_apply_search_review_batch_decision_dry_run_validates_ready_rows(tmp_path: Path) -> None:
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    quality = tmp_path / "searchProposalQualityCeiling.json"
    evidence = tmp_path / "queryLogDecisionSheet.evidencePacket.json"
    summary = tmp_path / "batch.summary.json"
    sheet.write_text(_sheetRowsText(), encoding="utf-8")
    quality.write_text(
        json.dumps(
            {
                "releaseEvidence": False,
                "invalidProposalRows": 0,
                "proxyRows": 2,
                "qualityReport": {
                    "metricEligible": True,
                    "blockers": ["proposalProxyNotReleaseEvidence"],
                    "metrics": {"docHit10": 1.0},
                },
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
            str(BATCH_SCRIPT),
            "--sheet",
            str(sheet),
            "--summary",
            str(summary),
            "--quality-ceiling",
            str(quality),
            "--require-metric-eligible",
            "--evidence-packet",
            str(evidence),
            "--require-evidence-ready",
            "--accept-suggested",
            "--dry-run",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(summary.read_text(encoding="utf-8"))
    assert data["valid"] is True
    assert data["releaseEvidence"] is False
    assert data["dryRun"] is True
    assert data["readyRows"] == 2
    assert data["wouldDecideRows"] == 2
    assert data["qualityCeiling"]["metricEligible"] is True
    assert data["evidencePacket"]["ready"] is True


def test_apply_search_review_batch_decision_blocks_unready_evidence_packet(tmp_path: Path) -> None:
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    evidence = tmp_path / "queryLogDecisionSheet.evidencePacket.json"
    summary = tmp_path / "batch.summary.json"
    sheet.write_text(_sheetRowsText(), encoding="utf-8")
    evidence.write_text(
        json.dumps(
            _evidencePacket(
                totalRows=2,
                readyRows=1,
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
            str(BATCH_SCRIPT),
            "--sheet",
            str(sheet),
            "--summary",
            str(summary),
            "--evidence-packet",
            str(evidence),
            "--require-evidence-ready",
            "--accept-suggested",
            "--dry-run",
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
    assert data["valid"] is False
    assert "evidencePacketInvalid" in data["blockers"]
    assert "evidencePacketReadyRows:1/2" in data["blockers"]
    assert "evidencePacketMissingEvidenceRows:1" in data["blockers"]


def test_apply_search_review_batch_decision_outputs_finalizer_ready_sheet(tmp_path: Path) -> None:
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    reviewed = tmp_path / "decisionSheet.reviewed.jsonl"
    summary = tmp_path / "batch.summary.json"
    finalized = tmp_path / "labels.reviewed.jsonl"
    finalizeSummary = tmp_path / "labels.reviewed.summary.json"
    sheet.write_text(_sheetRowsText(), encoding="utf-8")

    batchProc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(BATCH_SCRIPT),
            "--sheet",
            str(sheet),
            "--out",
            str(reviewed),
            "--summary",
            str(summary),
            "--reviewer",
            "qa-operator",
            "--reviewed-at",
            "2026-06-16T00:00:00Z",
            "--accept-suggested",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    assert batchProc.returncode == 0, batchProc.stderr + batchProc.stdout

    finalizeProc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(FINALIZE_SCRIPT),
            "--labels",
            str(reviewed),
            "--out",
            str(finalized),
            "--summary",
            str(finalizeSummary),
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

    assert finalizeProc.returncode == 0, finalizeProc.stderr + finalizeProc.stdout
    batch = json.loads(summary.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in finalized.read_text(encoding="utf-8").splitlines()]
    assert batch["valid"] is True
    assert rows[0]["targetKind"] == "filing"
    assert rows[0]["expectedSourceRefs"] == ["dart:allFilings:1#section=0", "dart:allFilings:2#section=0"]
    assert rows[0]["labeler"] == "qa-operator"
    assert rows[1]["targetKind"] == "noAnswer"
    assert rows[1]["expectedAnswerable"] is False


def test_apply_search_review_batch_decision_blocks_rows_needing_inspection(tmp_path: Path) -> None:
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    summary = tmp_path / "batch.summary.json"
    row = json.loads(_sheetRowsText().splitlines()[0])
    row["suggestedReviewDecision"] = ""
    row["proposedReviewAction"] = "inspectSourceIntentBeforeLabeling"
    sheet.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(BATCH_SCRIPT),
            "--sheet",
            str(sheet),
            "--summary",
            str(summary),
            "--accept-suggested",
            "--dry-run",
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
    assert data["blockers"] == ["batchRowsNotReady:1"]
    assert data["rowIssues"][0]["reason"] == "missingSuggestedReviewDecision,proposalNeedsInspection"


def _sheetRowsText() -> str:
    rows = [
        {
            "queryId": "q1",
            "query": "유상증자 공시",
            "targetKindHint": "filing",
            "reviewDecision": "",
            "suggestedReviewDecision": "acceptProposal",
            "reviewer": "",
            "reviewerNote": "",
            "targetKind": "",
            "expectedAnswerable": "",
            "expectedSourceRef": "",
            "expectedSourceRefs": "",
            "proposedTargetKind": "filing",
            "proposedExpectedAnswerable": True,
            "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
            "proposedExpectedSourceRefs": ["dart:allFilings:1#section=0", "dart:allFilings:2#section=0"],
            "proposedReviewAction": "useSourceRefProposal",
            "candidateSourceRefs": ["dart:allFilings:1#section=0", "dart:allFilings:2#section=0"],
        },
        {
            "queryId": "q2",
            "query": "없는 공시",
            "targetKindHint": "noAnswer",
            "reviewDecision": "",
            "suggestedReviewDecision": "verifiedNoAnswer",
            "reviewer": "",
            "reviewerNote": "",
            "targetKind": "",
            "expectedAnswerable": "",
            "expectedSourceRef": "",
            "expectedSourceRefs": "",
            "proposedTargetKind": "noAnswer",
            "proposedExpectedAnswerable": False,
            "proposedReviewAction": "useNoAnswerProposal",
        },
    ]
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"


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
