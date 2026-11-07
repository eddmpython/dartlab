"""Search quality review pack script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/buildSearchQualityReviewPack.py")


def test_build_search_quality_review_pack_with_precomputed_results(tmp_path: Path) -> None:
    querySpec = tmp_path / "queries.json"
    results = tmp_path / "results.json"
    outDir = tmp_path / "pack"
    querySpec.write_text(
        json.dumps(
            {
                "queries": [
                    {"query": "유상증자 공시 원문", "targetKindHint": "filing"},
                    {"query": "공시 말고 뉴스로 환율 기사", "targetKindHint": "news", "scope": "news"},
                    {"query": "EDGAR 10-K risk factors", "targetKindHint": "edgar"},
                    {"query": "없는회사 2099년 합병 공시", "targetKindHint": "noAnswer"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    results.write_text(
        json.dumps(
            {
                "유상증자 공시 원문": [
                    {
                        "source": "allFilings",
                        "sourceRef": "dart:allFilings:1#section=0",
                        "answerable": True,
                        "dataAsOf": "20260616",
                    }
                ],
                "공시 말고 뉴스로 환율 기사": [
                    {
                        "source": "news",
                        "sourceRef": "news:1",
                        "answerable": True,
                        "dataAsOf": "20260616",
                    }
                ],
                "EDGAR 10-K risk factors": [
                    {
                        "source": "edgar-panel",
                        "sourceRef": "edgar:panel:1#section=0",
                        "answerable": True,
                        "dataAsOf": "20260616",
                    }
                ],
                "없는회사 2099년 합병 공시": [
                    {
                        "source": "allFilings",
                        "sourceRef": "dart:allFilings:other#section=0",
                        "answerable": False,
                        "notAnswerableReason": "facetMismatch:company",
                        "dataAsOf": "20260616",
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
            "--out-dir",
            str(outDir),
            "--query-spec",
            str(querySpec),
            "--results-json",
            str(results),
            "--no-default-queries",
            "--min-queries",
            "4",
            "--required-targets",
            "filing,news,noAnswer,edgar",
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
    report = json.loads((outDir / "qualityReviewPack.json").read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["releaseEvidence"] is False
    assert report["coverageByTargetHint"] == {
        "edgar": 1,
        "filing": 1,
        "news": 1,
        "noAnswer": 1,
    }
    assert report["labelProposalCounts"] == {
        "needsInspection": 0,
        "total": 4,
        "withProposedNoAnswer": 1,
        "withProposedSourceRef": 3,
    }
    assert report["paths"]["rawLog"].endswith("queryLogRaw.reviewPack.jsonl")
    assert report["paths"]["labelTemplate"].endswith("queryLogLabels.todo.jsonl")
    labels = [
        json.loads(line)
        for line in (outDir / "queryLogLabels.todo.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert {row["reviewStatus"] for row in labels} == {"draft"}
    assert all("reviewInstruction" in row for row in labels)
    labelsByQuery = {row["query"]: row for row in labels}
    filingLabel = labelsByQuery["유상증자 공시 원문"]
    assert filingLabel["targetKind"] == ""
    assert filingLabel["expectedSourceRef"] == ""
    assert filingLabel["expectedAnswerable"] == ""
    assert filingLabel["proposedTargetKind"] == "filing"
    assert filingLabel["proposedExpectedAnswerable"] is True
    assert filingLabel["proposedExpectedSourceRef"] == "dart:allFilings:1#section=0"
    assert filingLabel["proposedExpectedSourceRefs"] == ["dart:allFilings:1#section=0"]
    assert filingLabel["proposedReviewAction"] == "verifyProposalThenCopyToExpectedFields"
    noAnswerLabel = labelsByQuery["없는회사 2099년 합병 공시"]
    assert noAnswerLabel["targetKind"] == ""
    assert noAnswerLabel["expectedSourceRef"] == ""
    assert noAnswerLabel["expectedAnswerable"] == ""
    assert noAnswerLabel["proposedTargetKind"] == "noAnswer"
    assert noAnswerLabel["proposedExpectedAnswerable"] is False
    assert noAnswerLabel["proposedReviewAction"] == "verifyNoAnswerThenSetExpectedAnswerableFalse"


def test_build_search_quality_review_pack_blocks_source_hint_miss(tmp_path: Path) -> None:
    querySpec = tmp_path / "queries.json"
    results = tmp_path / "results.json"
    outDir = tmp_path / "pack"
    querySpec.write_text(
        json.dumps({"queries": [{"query": "공시 말고 뉴스로 환율 기사", "targetKindHint": "news"}]}),
        encoding="utf-8",
    )
    results.write_text(
        json.dumps(
            {"공시 말고 뉴스로 환율 기사": [{"source": "allFilings", "sourceRef": "dart:wrong", "answerable": True}]},
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
            "--out-dir",
            str(outDir),
            "--query-spec",
            str(querySpec),
            "--results-json",
            str(results),
            "--no-default-queries",
            "--min-queries",
            "1",
            "--required-targets",
            "news",
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads((outDir / "qualityReviewPack.json").read_text(encoding="utf-8"))
    assert "sourceHintMisses:1" in report["blockers"]


def test_build_search_quality_review_pack_keeps_filing_proposal_source_family(tmp_path: Path) -> None:
    querySpec = tmp_path / "queries.json"
    results = tmp_path / "results.json"
    outDir = tmp_path / "pack"
    querySpec.write_text(
        json.dumps({"queries": [{"query": "배터리 소재 투자 사업의 내용", "targetKindHint": "filing"}]}),
        encoding="utf-8",
    )
    results.write_text(
        json.dumps(
            {
                "배터리 소재 투자 사업의 내용": [
                    {"source": "allFilings", "sourceRef": "dart:allFilings:1#section=0", "answerable": True},
                    {"source": "news", "sourceRef": "news:1", "answerable": True},
                    {"source": "panel", "sourceRef": "dart:panel:1#section=0", "answerable": True},
                ]
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
            "--out-dir",
            str(outDir),
            "--query-spec",
            str(querySpec),
            "--results-json",
            str(results),
            "--no-default-queries",
            "--min-queries",
            "1",
            "--required-targets",
            "filing",
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
    labels = [
        json.loads(line)
        for line in (outDir / "queryLogLabels.todo.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert labels[0]["proposedExpectedSourceRefs"] == [
        "dart:allFilings:1#section=0",
        "dart:panel:1#section=0",
    ]
