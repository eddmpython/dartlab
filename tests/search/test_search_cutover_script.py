"""Search cutover state CLI tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

SCRIPT = Path(".github/scripts/search/evaluateSearchCutover.py")
REPLACEMENT_SCRIPT = Path(".github/scripts/search/buildSearchReplacementEvidence.py")


def test_cutover_report_keeps_ops_blockers_and_next_actions(tmp_path: Path) -> None:
    status = _writeJson(
        tmp_path / "status.json",
        {
            "designReady": True,
            "opsReady": False,
            "releaseReady": False,
            "blockers": ["sourceCatalogMissing", "contentIndexManifestMissing"],
        },
    )
    proof = _writeJson(
        tmp_path / "searchProofBundle.json",
        {
            "opsReady": False,
            "releaseReady": False,
            "missingEvidence": ["hfRoundTrip"],
            "blockers": ["sourceCatalogMissing", "contentIndexManifestMissing"],
            "reports": {"productizationStatus": str(status)},
            "nextActions": {"bootstrapPlan": {"path": "searchBootstrapPlan.json"}},
        },
    )
    out = tmp_path / "cutover.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--proof-bundle",
            str(proof),
            "--out",
            str(out),
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
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["state"] == "S1_DESIGN_READY"
    assert report["opsReady"] is False
    assert report["defaultReplacement"] is False
    assert "sourceCatalogMissing" in report["blockers"]
    assert "missingOpsEvidence:hfRoundTrip" in report["blockers"]
    assert report["nextActions"]["bootstrapPlan"]["path"] == "searchBootstrapPlan.json"


def test_cutover_report_treats_quality_as_release_only_evidence(tmp_path: Path) -> None:
    status = _writeJson(
        tmp_path / "status.json",
        {"designReady": True, "opsReady": True, "releaseReady": False, "blockers": ["missingQualityReport"]},
    )
    proof = _writeJson(
        tmp_path / "searchProofBundle.json",
        {
            "opsReady": True,
            "releaseReady": False,
            "missingEvidence": ["quality"],
            "blockers": ["missingQualityReport"],
            "reports": {"productizationStatus": str(status)},
        },
    )
    out = tmp_path / "cutover.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--proof-bundle",
            str(proof),
            "--out",
            str(out),
            "--fail-on-release-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["state"] == "S2_OPS_READY"
    assert report["opsReady"] is True
    assert report["releaseReady"] is False
    assert report["missingOpsEvidence"] == []
    assert report["missingReleaseEvidence"] == ["quality"]
    assert "missingReleaseEvidence:quality" in report["blockers"]


def test_cutover_report_requires_replacement_evidence_for_default(tmp_path: Path) -> None:
    status = _writeJson(
        tmp_path / "status.json",
        {"designReady": True, "opsReady": True, "releaseReady": True, "blockers": []},
    )
    proof = _writeJson(
        tmp_path / "searchProofBundle.json",
        {
            "opsReady": True,
            "releaseReady": True,
            "missingEvidence": [],
            "blockers": [],
            "reports": {"productizationStatus": str(status)},
        },
    )
    out = tmp_path / "cutover.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--proof-bundle",
            str(proof),
            "--out",
            str(out),
            "--fail-on-default-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["state"] == "S3_RELEASE_READY"
    assert report["releaseReady"] is True
    assert report["defaultReplacement"] is False
    assert "missingReplacementEvidence" in report["blockers"]


def test_cutover_report_accepts_default_replacement_evidence(tmp_path: Path) -> None:
    status = _writeJson(
        tmp_path / "status.json",
        {"designReady": True, "opsReady": True, "releaseReady": True, "blockers": []},
    )
    proof = _writeJson(
        tmp_path / "searchProofBundle.json",
        {
            "opsReady": True,
            "releaseReady": True,
            "missingEvidence": [],
            "blockers": [],
            "reports": {"productizationStatus": str(status)},
        },
    )
    replacement = _writeJson(
        tmp_path / "replacement.json",
        {
            "proofBundle": str(proof),
            "singleEngineDefault": True,
            "defaultBuildMode": "catalog",
            "scheduledBuildMode": "catalog",
            "legacyFallbackOperatorOnly": True,
            "failClosedPublish": True,
            "activeManifestId": "manifest-current",
            "previousManifestId": "manifest-previous",
            "rollbackCommand": 'uv run python -X utf8 -c "rollback"',
            "rollbackVerified": True,
            "runEvidenceRecorded": True,
            "surfaceNamingReviewed": True,
        },
    )
    out = tmp_path / "cutover.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--proof-bundle",
            str(proof),
            "--replacement-evidence",
            str(replacement),
            "--out",
            str(out),
            "--fail-on-default-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["state"] == "S4_DEFAULT_REPLACEMENT"
    assert report["defaultReplacement"] is True
    assert report["blockers"] == []


def test_replacement_evidence_builder_promotes_release_bundle_to_s4(tmp_path: Path) -> None:
    status = _writeJson(
        tmp_path / "status.json",
        {"designReady": True, "opsReady": True, "releaseReady": True, "blockers": []},
    )
    proof = _writeJson(
        tmp_path / "searchProofBundle.json",
        {
            "opsReady": True,
            "releaseReady": True,
            "missingEvidence": [],
            "blockers": [],
            "reports": {"productizationStatus": str(status)},
        },
    )
    remote = _writeJson(tmp_path / "remote.json", _remoteEvidence())
    full = _writeJson(tmp_path / "full.json", _roundTrip("full"))
    lite = _writeJson(tmp_path / "lite.json", _roundTrip("lite"))
    replacement = tmp_path / "replacement.json"
    cutover = tmp_path / "cutover.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(REPLACEMENT_SCRIPT),
            "--proof-bundle",
            str(proof),
            "--remote-evidence",
            str(remote),
            "--round-trip",
            str(full),
            "--round-trip",
            str(lite),
            "--workflow",
            ".github/workflows/searchIndexBuild.yml",
            "--out",
            str(replacement),
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

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--proof-bundle",
            str(proof),
            "--replacement-evidence",
            str(replacement),
            "--out",
            str(cutover),
            "--fail-on-default-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(cutover.read_text(encoding="utf-8"))
    evidence = json.loads(replacement.read_text(encoding="utf-8"))
    assert evidence["valid"] is True
    assert evidence["defaultBuildMode"] == "catalog"
    assert evidence["scheduledBuildMode"] == "catalog"
    assert evidence["legacyFallbackOperatorOnly"] is True
    assert evidence["failClosedPublish"] is True
    assert report["state"] == "S4_DEFAULT_REPLACEMENT"
    assert report["defaultReplacement"] is True


def test_cutover_report_rejects_ambiguous_default_replacement_evidence(tmp_path: Path) -> None:
    status = _writeJson(
        tmp_path / "status.json",
        {"designReady": True, "opsReady": True, "releaseReady": True, "blockers": []},
    )
    proof = _writeJson(
        tmp_path / "searchProofBundle.json",
        {
            "opsReady": True,
            "releaseReady": True,
            "missingEvidence": [],
            "blockers": [],
            "reports": {"productizationStatus": str(status)},
        },
    )
    replacement = _writeJson(
        tmp_path / "replacement.json",
        {
            "proofBundle": str(proof),
            "singleEngineDefault": True,
            "defaultBuildMode": "auto",
            "scheduledBuildMode": "auto",
            "activeManifestId": "manifest-current",
            "previousManifestId": "manifest-previous",
            "rollbackCommand": 'uv run python -X utf8 -c "rollback"',
            "rollbackVerified": True,
            "runEvidenceRecorded": True,
            "surfaceNamingReviewed": True,
        },
    )
    out = tmp_path / "cutover.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--proof-bundle",
            str(proof),
            "--replacement-evidence",
            str(replacement),
            "--out",
            str(out),
            "--fail-on-default-not-ready",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["state"] == "S3_RELEASE_READY"
    assert "replacementEvidenceInvalid:defaultBuildMode" in report["blockers"]
    assert "replacementEvidenceInvalid:scheduledBuildMode" in report["blockers"]
    assert "replacementEvidenceMissing:legacyFallbackOperatorOnly" in report["blockers"]
    assert "replacementEvidenceMissing:failClosedPublish" in report["blockers"]


def _writeJson(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _remoteEvidence() -> dict:
    producer = {
        "workflow": "Search Index Build",
        "job": "build",
        "runId": "123",
        "sha": "abcdef",
        "artifactName": "search-catalog-test",
    }
    sources = {
        source: {
            "manifest": {
                "source": source,
                "producerRun": producer,
                "totalRows": 1,
            }
        }
        for source in ("allFilings", "dartPanel", "edgarPanel", "newsPublic")
    }
    return {
        "valid": True,
        "sourceCatalog": {"sources": sources},
        "contentIndex": {
            "manifests": {
                "full": {
                    "manifest": {
                        "artifactVersion": 1,
                        "schemaVersion": 2,
                        "builtAt": "2026-06-16T00:00:00",
                        "sourceManifestSetId": "source-set",
                        "stagingPrefix": "dart/contentIndex/_staging/full",
                    }
                }
            }
        },
    }


def _roundTrip(tier: str) -> dict:
    return {
        "valid": True,
        "tier": tier,
        "activation": {"activated": True},
        "rollback": {"rolledBack": True},
        "activatedManifest": {
            "artifactVersion": 1,
            "schemaVersion": 2,
            "builtAt": f"2026-06-16T00:00:00-{tier}",
            "stagingPrefix": f"dart/contentIndex/_staging/{tier}",
        },
        "restoredManifest": {
            "artifactVersion": 1,
            "schemaVersion": 2,
            "builtAt": "2026-06-15T00:00:00",
            "stagingPrefix": f"dart/contentIndex/_staging/previous-{tier}",
        },
    }
