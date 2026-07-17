"""Search canary pack CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_ref_resolution_uses_effective_main_and_delta_segments(tmp_path) -> None:
    from dartlab.providers.dart.search.fieldIndex import buildContentSegment
    from dartlab.providers.dart.search.fieldIndexRebuild import saveSegmentWithSidecar

    mainIdx, mainMeta = buildContentSegment(
        [
            {
                "section_content": "기존 공시",
                "rcept_no": "OLD",
                "source": "allFilings",
                "sourceRef": "dart:allFilings:OLD#section=0",
            }
        ],
        showProgress=False,
    )
    deltaIdx, deltaMeta = buildContentSegment(
        [
            {
                "section_content": "새 공시",
                "rcept_no": "NEW",
                "source": "allFilings",
                "sourceRef": "dart:allFilings:NEW#section=0",
            }
        ],
        showProgress=False,
    )
    saveSegmentWithSidecar(mainIdx, mainMeta, "main", tmp_path)
    saveSegmentWithSidecar(deltaIdx, deltaMeta, "delta", tmp_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    scriptPath = Path(".github/scripts/search/evaluateSearchCanary.py")
    spec = spec_from_file_location("evaluateSearchCanaryDeltaTest", scriptPath)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module._injectRefResolution(
        [
            {
                "query": "새 공시",
                "expectedSource": "allFilings",
                "expectedSourceRef": "dart:allFilings:NEW#section=0",
            }
        ],
        str(manifest),
    )

    assert rows[0]["_sourceResolved"] is True
    assert rows[0]["_refResolved"] is True


def test_evaluate_search_canary_script_with_precomputed_results(tmp_path) -> None:
    canary = tmp_path / "canary.jsonl"
    results = tmp_path / "results.json"
    out = tmp_path / "report.json"
    canary.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "query": "뉴스 원문",
                        "target": "news",
                        "expectedSource": "news",
                        "expectedSourceRef": "news:a",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "query": "없는 공시",
                        "target": "noAnswer",
                        "expectedAnswerable": False,
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
            ".github/scripts/search/evaluateSearchCanary.py",
            "--canary",
            str(canary),
            "--results-json",
            str(results),
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is True


def test_evaluate_search_canary_script_fails_on_false_accept(tmp_path) -> None:
    canary = tmp_path / "canary.jsonl"
    results = tmp_path / "results.json"
    out = tmp_path / "report.json"
    canary.write_text(
        json.dumps({"query": "없는 공시", "target": "noAnswer", "expectedAnswerable": False}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    results.write_text(
        json.dumps({"없는 공시": [{"source": "allFilings", "sourceRef": "dart:x", "answerable": True}]}),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/evaluateSearchCanary.py",
            "--canary",
            str(canary),
            "--results-json",
            str(results),
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["failures"][0]["failureType"] == "falseAccept"


def test_evaluate_search_canary_script_loads_pack_from_manifest(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    results = tmp_path / "results.json"
    out = tmp_path / "report.json"
    manifest.write_text(
        json.dumps(
            {
                "sourceCanaryPack": [
                    {
                        "query": "뉴스 원문",
                        "target": "news",
                        "expectedSource": "news",
                        "expectedSourceRef": "news:a",
                    }
                ]
            },
            ensure_ascii=False,
        ),
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
            ".github/scripts/search/evaluateSearchCanary.py",
            "--manifest",
            str(manifest),
            "--results-json",
            str(results),
            "--out",
            str(out),
            "--fail-on-error",
        ],
        cwd=Path.cwd(),
        env=os.environ,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["valid"] is True
    assert report["totalRows"] == 1
