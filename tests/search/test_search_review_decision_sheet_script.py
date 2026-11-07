"""buildSearchReviewDecisionSheet script tests."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SHEET_SCRIPT = Path(".github/scripts/search/buildSearchReviewDecisionSheet.py")
FINALIZE_SCRIPT = Path(".github/scripts/search/finalizeSearchReviewLabels.py")


def test_build_search_review_decision_sheet_compacts_labels(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    out = tmp_path / "decisionSheet.todo.jsonl"
    summary = tmp_path / "decisionSheet.summary.json"
    labels.write_text(_labelRowsText(), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--max-candidates",
            "2",
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
    assert data["releaseEvidence"] is False
    assert data["totalRows"] == 3
    assert data["proposedAnswerableRows"] == 1
    assert data["proposedNoAnswerRows"] == 1
    assert data["needsInspectionRows"] == 1
    assert data["decisionAudit"]["reviewComplete"] is False
    assert data["decisionAudit"]["blockers"] == ["undecidedRows:3"]
    assert data["proposalIntegrityAudit"]["valid"] is True
    assert data["suggestedDecisionCounts"] == {"": 1, "acceptProposal": 1, "verifiedNoAnswer": 1}

    answerable = rows[0]
    assert answerable["targetKind"] == ""
    assert answerable["expectedAnswerable"] == ""
    assert answerable["expectedSourceRef"] == ""
    assert answerable["reviewDecision"] == ""
    assert answerable["suggestedReviewDecision"] == "acceptProposal"
    assert answerable["candidateSourceRefs"] == ["dart:allFilings:1#section=0", "dart:allFilings:2#section=0"]
    assert len(answerable["candidateSummaries"]) == 2
    assert answerable["topSourceRef"] == "dart:allFilings:1#section=0"
    assert answerable["topCompanyName"] == "삼성전자"

    noAnswer = rows[1]
    assert noAnswer["suggestedReviewDecision"] == "verifiedNoAnswer"
    assert noAnswer["proposedExpectedAnswerable"] is False
    assert noAnswer["targetKind"] == ""

    inspect = rows[2]
    assert inspect["suggestedReviewDecision"] == ""
    assert inspect["proposedReviewAction"] == "inspectSourceIntentBeforeLabeling"


def test_decision_sheet_csv_can_feed_finalize_after_explicit_review(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    sheet = tmp_path / "decisionSheet.todo.jsonl"
    csvPath = tmp_path / "decisionSheet.todo.csv"
    reviewedCsv = tmp_path / "decisionSheet.reviewed.csv"
    finalized = tmp_path / "labels.reviewed.jsonl"
    summary = tmp_path / "labels.reviewed.summary.json"
    labels.write_text(_labelRowsText(includeInspection=False), encoding="utf-8")

    sheetProc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(sheet),
            "--csv-out",
            str(csvPath),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    assert sheetProc.returncode == 0, sheetProc.stderr + sheetProc.stdout

    rows = _readCsv(csvPath)
    rows[0]["reviewDecision"] = "acceptProposal"
    rows[0]["reviewer"] = "qa-operator"
    rows[1]["reviewDecision"] = "verifiedNoAnswer"
    rows[1]["reviewer"] = "qa-operator"
    _writeCsv(reviewedCsv, rows)

    finalizeProc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(FINALIZE_SCRIPT),
            "--labels",
            str(reviewedCsv),
            "--out",
            str(finalized),
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

    assert finalizeProc.returncode == 0, finalizeProc.stderr + finalizeProc.stdout
    finalRows = [json.loads(line) for line in finalized.read_text(encoding="utf-8").splitlines()]
    assert finalRows[0]["targetKind"] == "filing"
    assert finalRows[0]["expectedSourceRefs"] == ["dart:allFilings:1#section=0", "dart:allFilings:2#section=0"]
    assert finalRows[1]["targetKind"] == "noAnswer"
    assert finalRows[1]["expectedAnswerable"] is False


def test_decision_sheet_fail_on_incomplete_blocks_missing_decisions(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    out = tmp_path / "decisionSheet.todo.jsonl"
    summary = tmp_path / "decisionSheet.summary.json"
    labels.write_text(_labelRowsText(includeInspection=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--fail-on-incomplete",
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
    assert data["blockers"] == ["undecidedRows:2"]
    assert data["decisionAudit"]["reviewComplete"] is False


def test_decision_sheet_fail_on_incomplete_passes_reviewed_rows(tmp_path: Path) -> None:
    labels = tmp_path / "labels.reviewed.jsonl"
    out = tmp_path / "decisionSheet.reviewed.jsonl"
    summary = tmp_path / "decisionSheet.summary.json"
    rows = [json.loads(line) for line in _labelRowsText(includeInspection=False).splitlines()]
    rows[0]["reviewDecision"] = "acceptProposal"
    rows[0]["reviewer"] = "qa-operator"
    rows[1]["reviewDecision"] = "verifiedNoAnswer"
    rows[1]["reviewer"] = "qa-operator"
    labels.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--fail-on-incomplete",
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
    assert data["decisionAudit"]["reviewComplete"] is True
    assert data["decisionAudit"]["decidedRows"] == 2
    assert data["decisionAudit"]["decisionCounts"] == {
        "acceptProposal": 1,
        "verifiedNoAnswer": 1,
    }


def test_decision_sheet_fail_on_proposal_errors_blocks_source_mismatch(tmp_path: Path) -> None:
    labels = tmp_path / "labels.bad.jsonl"
    out = tmp_path / "decisionSheet.bad.jsonl"
    summary = tmp_path / "decisionSheet.summary.json"
    row = json.loads(_labelRowsText(includeInspection=False).splitlines()[0])
    row["targetKindHint"] = "news"
    row["proposedTargetKind"] = "news"
    row["proposedExpectedSourceRef"] = "dart:allFilings:1#section=0"
    row["proposedExpectedSourceRefs"] = ["dart:allFilings:1#section=0"]
    labels.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--fail-on-proposal-errors",
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
    assert data["blockers"] == ["proposalInvalidRows:1"]
    assert data["proposalIntegrityAudit"]["examples"][0]["reasons"] == ["proposalSourceRefTargetMismatch"]


def test_decision_sheet_fail_on_proposal_errors_blocks_no_answer_with_answerable_hit(tmp_path: Path) -> None:
    labels = tmp_path / "labels.bad.jsonl"
    out = tmp_path / "decisionSheet.bad.jsonl"
    summary = tmp_path / "decisionSheet.summary.json"
    row = json.loads(_labelRowsText(includeInspection=False).splitlines()[1])
    row["topResults"] = [{"source": "allFilings", "sourceRef": "dart:answer", "answerable": True}]
    labels.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--summary",
            str(summary),
            "--fail-on-proposal-errors",
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
    assert data["blockers"] == ["proposalInvalidRows:1"]
    assert data["proposalIntegrityAudit"]["examples"][0]["reasons"] == ["noAnswerProposalHasAnswerableTopResult"]


def test_decision_sheet_writes_review_evidence_packet(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    results = tmp_path / "queryResults.json"
    out = tmp_path / "decisionSheet.todo.jsonl"
    evidence = tmp_path / "reviewEvidence.json"
    markdown = tmp_path / "reviewEvidence.md"
    labels.write_text(_labelRowsText(includeInspection=False), encoding="utf-8")
    results.write_text(
        json.dumps(
            [
                {
                    "query": "유상증자 공시 원문",
                    "results": [
                        {
                            "source": "allFilings",
                            "sourceRef": "dart:allFilings:1#section=0",
                            "corp_name": "삼성전자",
                            "stock_code": "005930",
                            "report_nm": "유상증자 결정",
                            "snippet": "유상증자 결정 본문 일부",
                            "url": "https://dart.example/1",
                            "answerable": True,
                            "score": 1.0,
                            "dataAsOf": "20260616",
                        },
                        {
                            "source": "allFilings",
                            "sourceRef": "dart:allFilings:2#section=0",
                            "snippet": "두 번째 후보",
                            "answerable": True,
                        },
                    ],
                },
                {
                    "query": "없는회사 2099년 합병 공시",
                    "results": [
                        {
                            "source": "allFilings",
                            "sourceRef": "dart:allFilings:x#section=0",
                            "snippet": "facet mismatch",
                            "answerable": False,
                            "notAnswerableReason": "facetMismatch:date",
                        }
                    ],
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--results-json",
            str(results),
            "--evidence-out",
            str(evidence),
            "--evidence-md-out",
            str(markdown),
            "--max-candidates",
            "2",
            "--fail-on-evidence-issues",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    packet = json.loads(evidence.read_text(encoding="utf-8"))
    md = markdown.read_text(encoding="utf-8")
    assert packet["valid"] is True
    assert packet["releaseEvidence"] is False
    assert packet["evidenceReadyRows"] == 2
    assert packet["rows"][0]["proposedEvidence"][0]["snippet"] == "유상증자 결정 본문 일부"
    assert packet["rows"][1]["topEvidence"][0]["notAnswerableReason"] == "facetMismatch:date"
    assert "Search Review Evidence Packet" in md
    assert "유상증자 결정 본문 일부" in md


def test_decision_sheet_evidence_packet_blocks_no_answer_false_accept(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    results = tmp_path / "queryResults.json"
    out = tmp_path / "decisionSheet.todo.jsonl"
    evidence = tmp_path / "reviewEvidence.json"
    row = json.loads(_labelRowsText(includeInspection=False).splitlines()[1])
    labels.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    results.write_text(
        json.dumps(
            [{"query": row["query"], "results": [{"sourceRef": "dart:allFilings:x#section=0", "answerable": True}]}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--results-json",
            str(results),
            "--evidence-out",
            str(evidence),
            "--fail-on-evidence-issues",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    packet = json.loads(evidence.read_text(encoding="utf-8"))
    assert packet["valid"] is False
    assert packet["blockers"] == ["evidenceRowsNotReady:1"]
    assert packet["examples"][0]["reason"] == "noAnswerEvidenceHasAnswerableTopResult"


def test_decision_sheet_evidence_packet_accepts_empty_no_answer_results(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    results = tmp_path / "queryResults.json"
    out = tmp_path / "decisionSheet.todo.jsonl"
    evidence = tmp_path / "reviewEvidence.json"
    row = json.loads(_labelRowsText(includeInspection=False).splitlines()[1])
    labels.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    results.write_text(json.dumps([{"query": row["query"], "results": []}], ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SHEET_SCRIPT),
            "--labels",
            str(labels),
            "--out",
            str(out),
            "--results-json",
            str(results),
            "--evidence-out",
            str(evidence),
            "--fail-on-evidence-issues",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    packet = json.loads(evidence.read_text(encoding="utf-8"))
    assert packet["valid"] is True
    assert packet["evidenceReadyRows"] == 1
    assert packet["rows"][0]["topEvidence"] == []


def _labelRowsText(*, includeInspection: bool = True) -> str:
    rows = [
        {
            "queryId": "q1",
            "query": "유상증자 공시 원문",
            "targetKind": "",
            "expectedAnswerable": "",
            "expectedSourceRef": "",
            "targetKindHint": "filing",
            "proposedTargetKind": "filing",
            "proposedExpectedAnswerable": True,
            "proposedExpectedSourceRef": "dart:allFilings:1#section=0",
            "proposedExpectedSourceRefs": [
                "dart:allFilings:1#section=0",
                "dart:allFilings:2#section=0",
            ],
            "proposedReviewAction": "verifyProposalThenCopyToExpectedFields",
            "proposedLabelReason": "topAnswerableResult",
            "candidateSourceRefs": [
                "dart:allFilings:1#section=0",
                "dart:allFilings:2#section=0",
            ],
            "topResults": [
                {
                    "source": "allFilings",
                    "sourceRef": "dart:allFilings:1#section=0",
                    "companyName": "삼성전자",
                    "stockCode": "005930",
                    "reportName": "유상증자결정",
                    "title": "유상증자결정",
                    "dataAsOf": "20260616",
                    "url": "https://example.com/1",
                    "answerable": True,
                    "score": 0.9,
                },
                {
                    "source": "allFilings",
                    "sourceRef": "dart:allFilings:2#section=0",
                    "companyName": "현대차",
                    "stockCode": "005380",
                    "reportName": "유상증자결정",
                    "title": "유상증자결정",
                    "dataAsOf": "20260616",
                    "url": "https://example.com/2",
                    "answerable": True,
                    "score": 0.7,
                },
            ],
        },
        {
            "queryId": "q2",
            "query": "없는회사 2099년 합병 공시",
            "targetKind": "",
            "expectedAnswerable": "",
            "expectedSourceRef": "",
            "targetKindHint": "noAnswer",
            "proposedTargetKind": "noAnswer",
            "proposedExpectedAnswerable": False,
            "proposedReviewAction": "verifyNoAnswerThenSetExpectedAnswerableFalse",
            "proposedLabelReason": "noAnswerHintNoAnswerableTopResults",
            "topResults": [
                {
                    "source": "allFilings",
                    "sourceRef": "dart:other",
                    "answerable": False,
                    "notAnswerableReason": "facetMismatch:literal",
                }
            ],
        },
    ]
    if includeInspection:
        rows.append(
            {
                "queryId": "q3",
                "query": "공시 말고 뉴스로 환율 기사",
                "targetKindHint": "news",
                "proposedTargetKind": "news",
                "proposedReviewAction": "inspectSourceIntentBeforeLabeling",
                "proposedLabelReason": "sourceHintMismatchNoProposal",
                "topResults": [{"source": "allFilings", "sourceRef": "dart:wrong", "answerable": True}],
            }
        )
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"


def _readCsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _writeCsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
