"""providers/dart/search/canaryPack.py mirror tests."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


def _canaries() -> list[dict[str, object]]:
    return [
        {
            "query": "뉴스 원문",
            "target": "news",
            "expectedSource": "news",
            "expectedSourceRef": "news:a",
        },
        {
            "query": "가짜회사 20990101 합병 공시",
            "target": "noAnswer",
            "expectedAnswerable": False,
        },
    ]


def test_evaluate_canary_pack_rows_accepts_source_ref_and_no_answer() -> None:
    from dartlab.providers.dart.search.canaryPack import evaluateCanaryPackRows

    report = evaluateCanaryPackRows(
        _canaries(),
        {
            "뉴스 원문": [{"source": "news", "sourceRef": "news:a", "answerable": True}],
            "가짜회사 20990101 합병 공시": [{"source": "allFilings", "sourceRef": "dart:x", "answerable": False}],
        },
    )

    assert report["valid"] is True
    assert report["metrics"]["passRate"] == 1.0
    assert report["metrics"]["noAnswerFalseAcceptRate"] == 0.0


def test_evaluate_canary_pack_rows_reports_source_and_false_accept_failures() -> None:
    from dartlab.providers.dart.search.canaryPack import evaluateCanaryPackRows

    report = evaluateCanaryPackRows(
        _canaries(),
        {
            "뉴스 원문": [{"source": "allFilings", "sourceRef": "dart:a", "answerable": True}],
            "가짜회사 20990101 합병 공시": [{"source": "allFilings", "sourceRef": "dart:x", "answerable": True}],
        },
    )

    assert report["valid"] is False
    failures = {row["failureType"] for row in report["failures"]}
    assert failures >= {"sourceMiss", "sourceRefMiss", "falseAccept"}


def test_evaluate_canary_pack_rows_echoes_resolution_diagnostics() -> None:
    """Regression for #107: reports expose deterministic injection instead of silent fallback."""
    from dartlab.providers.dart.search.canaryPack import evaluateCanaryPackRows

    report = evaluateCanaryPackRows(
        [
            {
                "query": "유상증자결정 벡트",
                "expectedSource": "allFilings",
                "expectedSourceRef": "dart:allFilings:20260806000547#section=0",
                "_injectionMode": "deterministic",
                "_sourceResolved": True,
                "_refResolved": True,
            }
        ],
        {"유상증자결정 벡트": []},
    )

    assert report["rows"][0]["injectionMode"] == "deterministic"
    assert report["rows"][0]["_sourceResolved"] is True
    assert report["rows"][0]["_refResolved"] is True


def test_evaluate_canary_pack_rows_can_check_source_without_answerability() -> None:
    from dartlab.providers.dart.search.canaryPack import evaluateCanaryPackRows

    report = evaluateCanaryPackRows(
        [
            {
                "query": "edgar filing",
                "target": "edgar",
                "expectedSource": "edgar-panel",
                "expectedAnswerable": True,
                "requireAnswerable": False,
            }
        ],
        {"edgar filing": [{"source": "edgar-panel", "sourceRef": "edgar:panel:x", "answerable": False}]},
    )

    assert report["valid"] is True
    assert report["metrics"]["sourceHitRate"] == 1.0


def test_load_canary_pack_jsonl_and_write_report(tmp_path) -> None:
    from dartlab.providers.dart.search.canaryPack import evaluateCanaryPackRows, loadCanaryPack, writeCanaryReport

    path = tmp_path / "canary.jsonl"
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in _canaries()), encoding="utf-8")
    rows = loadCanaryPack(path)
    report = evaluateCanaryPackRows(rows, {})
    out = tmp_path / "report.json"
    writeCanaryReport(out, report)

    assert len(rows) == 2
    assert out.exists()
