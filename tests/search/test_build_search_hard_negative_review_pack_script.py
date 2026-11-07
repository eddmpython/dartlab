"""buildSearchHardNegativeReviewPack script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/buildSearchHardNegativeReviewPack.py")
BATCH_SCRIPT = Path(".github/scripts/search/applySearchReviewBatchDecision.py")


def test_build_search_hard_negative_review_pack_creates_batch_ready_artifacts(tmp_path: Path) -> None:
    gold = tmp_path / "hardNegative.candidate.jsonl"
    results = tmp_path / "results.json"
    outDir = tmp_path / "reviewPack"
    gold.write_text(_goldRowsText(), encoding="utf-8")
    results.write_text(json.dumps(_resultsRows(), ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--gold",
            str(gold),
            "--out-dir",
            str(outDir),
            "--results-json",
            str(results),
            "--max-candidates",
            "2",
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
    report = json.loads((outDir / "hardNegativeReviewPack.json").read_text(encoding="utf-8"))
    decision = json.loads((outDir / "queryLogDecisionSheet.hardNegative.summary.json").read_text(encoding="utf-8"))
    evidence = json.loads(
        (outDir / "queryLogDecisionSheet.hardNegative.evidencePacket.json").read_text(encoding="utf-8")
    )
    labels = [
        json.loads(line)
        for line in (outDir / "queryLogLabels.hardNegative.todo.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert report["valid"] is True
    assert report["batchReady"] is True
    assert report["releaseEvidence"] is False
    assert report["coverageByKind"] == {"filing": 1, "noAnswer": 1}
    assert decision["proposalIntegrityAudit"]["valid"] is True
    assert decision["suggestedDecisionCounts"] == {"acceptProposal": 1, "verifiedNoAnswer": 1}
    assert evidence["valid"] is True
    assert evidence["evidenceReadyRows"] == 2
    assert labels[0]["goldOrigin"] == "userLog"
    assert labels[0]["reviewStatus"] == "draft"
    assert labels[0]["proposedExpectedSourceRef"] == "dart:allFilings:1#section=0"
    assert labels[0]["forbiddenSourceRefs"] == ["dart:allFilings:2#section=0"]
    assert labels[1]["proposedExpectedAnswerable"] is False

    dryRunSummary = tmp_path / "batch.summary.json"
    dryRun = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(BATCH_SCRIPT),
            "--sheet",
            str(outDir / "queryLogDecisionSheet.hardNegative.todo.jsonl"),
            "--summary",
            str(dryRunSummary),
            "--evidence-packet",
            str(outDir / "queryLogDecisionSheet.hardNegative.evidencePacket.json"),
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
    assert dryRun.returncode == 0, dryRun.stderr + dryRun.stdout
    summary = json.loads(dryRunSummary.read_text(encoding="utf-8"))
    assert summary["valid"] is True
    assert summary["wouldDecideRows"] == 2


def _goldRowsText() -> str:
    rows = [
        {
            "queryId": "hardneg:1",
            "query": "삼성전자 2026 유상증자 공시 원문",
            "targetKind": "filing",
            "expectedAnswerable": True,
            "expectedSourceRef": "dart:allFilings:1#section=0",
            "expectedSourceRefs": ["dart:allFilings:1#section=0"],
            "forbiddenSourceRefs": ["dart:allFilings:2#section=0"],
            "hardNegativeType": "same-company-sibling-filing",
            "goldOrigin": "currentDataHardNegative",
            "reviewStatus": "candidate",
            "sourceDataAsOf": "20260618",
        },
        {
            "queryId": "hardneg:2",
            "query": "없는회사 2099 유상증자 공시 원문",
            "targetKind": "noAnswer",
            "expectedAnswerable": False,
            "hardNegativeType": "no-answer-missing-company-year-event",
            "goldOrigin": "currentDataHardNegative",
            "reviewStatus": "candidate",
            "sourceDataAsOf": "20260618",
        },
    ]
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"


def _resultsRows() -> list[dict[str, object]]:
    return [
        {
            "queryId": "hardneg:1",
            "query": "삼성전자 2026 유상증자 공시 원문",
            "results": [
                {
                    "source": "allFilings",
                    "sourceRef": "dart:allFilings:1#section=0",
                    "corp_name": "삼성전자",
                    "stock_code": "005930",
                    "report_nm": "유상증자결정",
                    "answerable": True,
                    "dataAsOf": "20260618",
                    "score": 1.0,
                },
                {
                    "source": "allFilings",
                    "sourceRef": "dart:allFilings:2#section=0",
                    "corp_name": "삼성전자",
                    "stock_code": "005930",
                    "report_nm": "주주총회소집결의",
                    "answerable": True,
                    "dataAsOf": "20260618",
                    "score": 0.5,
                },
            ],
        },
        {
            "queryId": "hardneg:2",
            "query": "없는회사 2099 유상증자 공시 원문",
            "results": [
                {
                    "source": "allFilings",
                    "sourceRef": "dart:allFilings:other#section=0",
                    "corp_name": "다른회사",
                    "answerable": False,
                    "notAnswerableReason": "constraintMismatch:topic",
                    "dataAsOf": "20260618",
                    "score": 0.1,
                }
            ],
        },
    ]
