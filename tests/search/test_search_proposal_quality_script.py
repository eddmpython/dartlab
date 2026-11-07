"""estimateSearchProposalQuality script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/estimateSearchProposalQuality.py")


def test_estimate_search_proposal_quality_writes_non_release_ceiling_report(tmp_path: Path) -> None:
    raw = tmp_path / "raw.jsonl"
    labels = tmp_path / "labels.todo.jsonl"
    results = tmp_path / "results.json"
    outDir = tmp_path / "proposalQuality"
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
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "queryId": "q2",
                        "query": "없는 공시",
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
            "--results-json",
            str(results),
            "--out-dir",
            str(outDir),
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
    summary = json.loads((outDir / "searchProposalQualityCeiling.json").read_text(encoding="utf-8"))
    quality = json.loads((outDir / "qualityCeilingReport.json").read_text(encoding="utf-8"))
    proxyGold = [
        json.loads(line)
        for line in (outDir / "queryLogGold.proposalProxy.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert summary["releaseEvidence"] is False
    assert summary["qualityReport"]["metricEligible"] is True
    assert quality["releaseEvidence"] is False
    assert quality["releaseEligible"] is False
    assert quality["metricEligible"] is True
    assert quality["blockers"] == ["proposalProxyNotReleaseEvidence"]
    assert quality["realReviewedRows"] == 0
    assert quality["goldOriginCounts"] == {"proposalProxy": 2}
    assert quality["reviewStatusCounts"] == {"proposalOnly": 2}
    assert {row["goldOrigin"] for row in proxyGold} == {"proposalProxy"}
    assert {row["reviewStatus"] for row in proxyGold} == {"proposalOnly"}


def test_estimate_search_proposal_quality_blocks_invalid_proposals(tmp_path: Path) -> None:
    labels = tmp_path / "labels.todo.jsonl"
    results = tmp_path / "results.json"
    outDir = tmp_path / "proposalQuality"
    labels.write_text(
        json.dumps(
            {
                "queryId": "q1",
                "query": "유상증자 공시",
                "proposedTargetKind": "filing",
                "proposedExpectedAnswerable": True,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    results.write_text(json.dumps({"q1": []}, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--labels",
            str(labels),
            "--results-json",
            str(results),
            "--out-dir",
            str(outDir),
            "--min-rows",
            "1",
            "--required-targets",
            "filing",
            "--fail-on-invalid-proposals",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    summary = json.loads((outDir / "searchProposalQualityCeiling.json").read_text(encoding="utf-8"))
    invalidRows = [
        json.loads(line) for line in (outDir / "invalidProposalRows.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert summary["valid"] is False
    assert summary["invalidProposalRows"] == 1
    assert invalidRows[0]["reasons"] == ["answerableProposalMissingSourceRef"]
