"""Search productization proof bundle CLI tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


SCRIPT = Path(".github/scripts/search/buildSearchProofBundle.py")


def test_build_search_proof_bundle_accepts_complete_evidence(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    _writeCompleteRemote(remote)
    localInfo = _writeJson(
        tmp_path / "localIndexInfo.json",
        {
            "available": True,
            "compatible": True,
            "manifestValid": True,
            "nDocs": 400,
            "nDocsBySource": {"allFilings": 100, "panel": 100, "edgar-panel": 100, "news": 100},
            "sourceDataAsOf": {
                "allFilings": "20260616",
                "panel": "20260616",
                "edgar-panel": "20260616",
                "news": "20260616",
            },
        },
    )
    resultContract = _writeJson(tmp_path / "resultContract.json", {"valid": True, "totalRows": 30, "invalidRows": []})
    canary = _writeJson(
        tmp_path / "canary.json",
        {
            "valid": True,
            "totalRows": 4,
            "passedRows": 4,
            "failures": [],
            "rows": [
                {"query": "공시 원문", "expectedSource": "allFilings", "passed": True},
                {"query": "DART panel", "expectedSource": "panel", "passed": True},
                {"query": "EDGAR 10-K", "expectedSource": "edgar-panel", "passed": True},
                {"query": "뉴스", "expectedSource": "news", "passed": True},
            ],
        },
    )
    quality = _writeJson(
        tmp_path / "quality.json",
        {
            "releaseEligible": True,
            "totalRows": 320,
            "realReviewedRows": 320,
            "coverageByKind": {"filing": 140, "news": 60, "noAnswer": 20, "edgar": 100},
            "goldOriginCounts": {"userLog": 320},
            "reviewStatusCounts": {"reviewed": 320},
            "metrics": {
                "overallReadyRate": 0.95,
                "hardNegativeRows": 300,
                "hardNegativeExactDocHit10": 0.96,
                "hardNegativeWinRate": 0.96,
                "forbiddenTop3Rate": 0.0,
                "forbiddenTop10Rate": 0.0,
                "sourceIntentLeakRate": 0.0,
                "constraintViolationRate": 0.0,
            },
            "blockers": [],
        },
    )
    roundTripFull = _writeJson(
        tmp_path / "roundTrip.full.json",
        {"valid": True, "tier": "full", "activation": {"activated": True}, "rollback": {"rolledBack": True}},
    )
    roundTripLite = _writeJson(
        tmp_path / "roundTrip.lite.json",
        {"valid": True, "tier": "lite", "activation": {"activated": True}, "rollback": {"rolledBack": True}},
    )
    outDir = tmp_path / "bundle"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--remote-root",
            str(remote),
            "--local-index-info",
            str(localInfo),
            "--result-contract-report",
            str(resultContract),
            "--canary-report",
            str(canary),
            "--quality-report",
            str(quality),
            "--hf-round-trip",
            str(roundTripFull),
            "--hf-round-trip",
            str(roundTripLite),
            "--out-dir",
            str(outDir),
            "--fail-on-release-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    status = json.loads((outDir / "searchProductizationStatus.json").read_text(encoding="utf-8"))
    bundle = json.loads((outDir / "searchProofBundle.json").read_text(encoding="utf-8"))
    assert status["opsReady"] is True
    assert status["releaseReady"] is True
    assert bundle["missingEvidence"] == []
    assert Path(bundle["reports"]["remoteEvidence"]).exists()
    assert "bootstrapPlan" not in bundle["reports"]
    assert bundle["nextActions"] == {}


def test_build_search_proof_bundle_keeps_missing_evidence_as_blockers(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    localInfo = _writeJson(
        tmp_path / "localIndexInfo.json",
        {
            "available": True,
            "compatible": True,
            "manifestValid": True,
            "nDocs": 1,
            "nDocsBySource": {"allFilings": 1},
            "sourceDataAsOf": {"allFilings": "20260616"},
        },
    )
    outDir = tmp_path / "bundle"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--remote-root",
            str(remote),
            "--local-index-info",
            str(localInfo),
            "--skip-result-contract",
            "--skip-canary",
            "--skip-quality",
            "--out-dir",
            str(outDir),
            "--fail-on-ops-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    status = json.loads((outDir / "searchProductizationStatus.json").read_text(encoding="utf-8"))
    bundle = json.loads((outDir / "searchProofBundle.json").read_text(encoding="utf-8"))
    assert status["opsReady"] is False
    assert "sourceCatalogMissing" in status["blockers"]
    assert "contentIndexManifestMissing" in status["blockers"]
    assert "hfRoundTrip" in bundle["missingEvidence"]
    assert "resultContract" in bundle["missingEvidence"]
    bootstrapPlan = Path(bundle["reports"]["bootstrapPlan"])
    assert bootstrapPlan.exists()
    plan = json.loads(bootstrapPlan.read_text(encoding="utf-8"))
    assert plan["missingSources"] == ["allFilings", "dartPanel", "edgarPanel", "newsPublic"]
    assert plan["missingContentTiers"] == ["full", "lite"]
    assert "bootstrapPlan" in bundle["nextActions"]
    assert "buildContentIndex:mainCatalog" in bundle["nextActions"]["bootstrapPlan"]["actionIds"]


def _writeCompleteRemote(remote: Path) -> None:
    for source in ("allFilings", "dartPanel", "edgarPanel", "newsPublic"):
        sourceDir = remote / "dart" / "searchCatalog" / source
        sourceDir.mkdir(parents=True, exist_ok=True)
        _writeJson(
            sourceDir / f"{source}.source_manifest.json",
            {
                "source": source,
                "snapshotScope": "full",
                "dataAsOf": "20260616",
                "builtAt": "2026-06-16T00:00:00Z",
                "totalRows": 100,
                "files": [{"path": f"{source}.parquet"}],
                "producer": "test",
                "producerRun": _producerRun(source),
            },
        )
        (sourceDir / f"{source}.catalog_snapshot.parquet").write_bytes(b"PAR1")
    _writeContentManifest(
        remote / "dart" / "contentIndex",
        sourceCounts={"allFilings": 100, "panel": 100, "edgar-panel": 100, "news": 100},
        run="run-full",
    )
    _writeContentManifest(
        remote / "dart" / "contentIndex" / "lite",
        sourceCounts={"allFilings": 20, "panel": 20, "edgar-panel": 20, "news": 20},
        run="run-lite",
    )


def _writeContentManifest(base: Path, *, sourceCounts: dict[str, int], run: str) -> None:
    fileSources = {"main.npz": f"_staging/{run}/main.npz"}
    _writeJson(
        base / "manifest.json",
        {
            "valid": True,
            "artifactVersion": f"test-{run}",
            "schemaVersion": 2,
            "builtAt": "2026-06-16T00:00:00Z",
            "publishMode": "manifestPointer",
            "nDocsBySource": sourceCounts,
            "sourceDataAsOf": {source: "20260616" for source in sourceCounts},
            "sourceManifestSetId": "manifest-set-1",
            "sourceManifestSet": {
                "sources": [
                    {"source": "allFilings"},
                    {"source": "dartPanel"},
                    {"source": "edgarPanel"},
                    {"source": "newsPublic"},
                ]
            },
            "requiredFiles": ["main.npz"],
            "fileSources": fileSources,
        },
    )
    stage = base / "_staging" / run
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "main.npz").write_bytes(b"main")


def _writeJson(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _producerRun(source: str) -> dict[str, str]:
    return {
        "system": "githubActions",
        "workflow": "test workflow",
        "job": f"{source}-job",
        "runId": "12345",
        "runAttempt": "1",
        "sha": "abc123",
        "ref": "master",
        "artifactName": f"search-catalog-{source}-{source}-job-12345",
    }
