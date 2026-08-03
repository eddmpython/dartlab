"""Evaluate search cutover state from a productization proof bundle.

This script is intentionally non-mutating. It turns the evidence bundle into
the operator-facing S0-S4 cutover state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

RELEASE_ONLY_EVIDENCE = {"quality"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-bundle", required=True, help="searchProofBundle.json path.")
    parser.add_argument("--status", help="Optional searchProductizationStatus.json path.")
    parser.add_argument("--replacement-evidence", help="Optional default replacement evidence JSON.")
    parser.add_argument("--out", required=True, help="Output cutover report JSON path.")
    parser.add_argument("--fail-on-ops-not-ready", action="store_true")
    parser.add_argument("--fail-on-release-not-ready", action="store_true")
    parser.add_argument("--fail-on-default-not-ready", action="store_true")
    args = parser.parse_args(argv)

    report = evaluateCutover(
        proofBundlePath=Path(args.proof_bundle),
        statusPath=Path(args.status) if args.status else None,
        replacementEvidencePath=Path(args.replacement_evidence) if args.replacement_evidence else None,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "state": report["state"],
                "opsReady": report["opsReady"],
                "releaseReady": report["releaseReady"],
                "defaultReplacement": report["defaultReplacement"],
                "blockers": report["blockers"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if args.fail_on_default_not_ready and not report["defaultReplacement"]:
        return 1
    if args.fail_on_release_not_ready and not report["releaseReady"]:
        return 1
    if args.fail_on_ops_not_ready and not report["opsReady"]:
        return 1
    return 0


def evaluateCutover(
    *,
    proofBundlePath: Path,
    statusPath: Path | None = None,
    replacementEvidencePath: Path | None = None,
) -> dict[str, Any]:
    proof = _loadJson(proofBundlePath)
    status = _loadStatus(proof, proofBundlePath=proofBundlePath, statusPath=statusPath)
    replacementEvidence = _loadJson(replacementEvidencePath) if replacementEvidencePath else {}

    designReady = bool(status.get("designReady", True))
    opsMissingEvidence = _opsMissingEvidence(proof)
    releaseMissingEvidence = _releaseMissingEvidence(proof)
    opsReady = bool(status.get("opsReady")) and not opsMissingEvidence
    releaseReady = bool(status.get("releaseReady")) and opsReady and not releaseMissingEvidence
    replacementBlockers = _replacementBlockers(
        replacementEvidence,
        proofBundlePath=proofBundlePath,
        required=opsReady,
    )
    defaultReplacement = opsReady and not replacementBlockers
    state = _state(
        designReady=designReady,
        opsReady=opsReady,
        releaseReady=releaseReady,
        defaultReplacement=defaultReplacement,
    )
    blockers = _dedupe(
        [str(item) for item in status.get("blockers", []) if item]
        + [f"missingOpsEvidence:{item}" for item in opsMissingEvidence]
        + [f"missingReleaseEvidence:{item}" for item in releaseMissingEvidence]
        + replacementBlockers
    )
    return {
        "valid": defaultReplacement if replacementEvidence else opsReady,
        "state": state,
        "designReady": designReady,
        "opsReady": opsReady,
        "releaseReady": releaseReady,
        "defaultReplacement": defaultReplacement,
        "blockers": blockers,
        "proofBundle": str(proofBundlePath),
        "statusPath": str(_statusPath(proof, proofBundlePath, statusPath) or ""),
        "replacementEvidencePath": str(replacementEvidencePath or ""),
        "nextActions": proof.get("nextActions") if isinstance(proof.get("nextActions"), dict) else {},
        "missingEvidence": _missingEvidence(proof),
        "missingOpsEvidence": opsMissingEvidence,
        "missingReleaseEvidence": releaseMissingEvidence,
        "replacementEvidence": _replacementSummary(replacementEvidence),
    }


def _loadStatus(proof: dict[str, Any], *, proofBundlePath: Path, statusPath: Path | None) -> dict[str, Any]:
    path = _statusPath(proof, proofBundlePath, statusPath)
    if path and path.exists():
        return _loadJson(path)
    return {
        "designReady": True,
        "opsReady": bool(proof.get("opsReady")),
        "releaseReady": bool(proof.get("releaseReady")),
        "blockers": proof.get("blockers") or [],
    }


def _statusPath(proof: dict[str, Any], proofBundlePath: Path, statusPath: Path | None) -> Path | None:
    if statusPath:
        return statusPath
    reports = proof.get("reports") if isinstance(proof.get("reports"), dict) else {}
    raw = reports.get("productizationStatus") if isinstance(reports, dict) else None
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = proofBundlePath.parent / path
    return path


def _replacementBlockers(
    evidence: dict[str, Any],
    *,
    proofBundlePath: Path,
    required: bool,
) -> list[str]:
    if not required:
        return ["opsNotReadyForDefaultReplacement"]
    if not evidence:
        return ["missingReplacementEvidence"]
    blockers: list[str] = []
    truthyFields = (
        "singleEngineDefault",
        "legacyFallbackOperatorOnly",
        "failClosedPublish",
        "runEvidenceRecorded",
        "rollbackVerified",
        "surfaceNamingReviewed",
    )
    for field in truthyFields:
        if not bool(evidence.get(field)):
            blockers.append(f"replacementEvidenceMissing:{field}")
    if _lower(evidence.get("defaultBuildMode")) != "catalog":
        blockers.append("replacementEvidenceInvalid:defaultBuildMode")
    if _lower(evidence.get("scheduledBuildMode")) != "catalog":
        blockers.append("replacementEvidenceInvalid:scheduledBuildMode")
    for field in ("activeManifestId", "previousManifestId", "rollbackCommand"):
        if not str(evidence.get(field) or "").strip():
            blockers.append(f"replacementEvidenceMissing:{field}")
    proof = str(evidence.get("proofBundle") or "")
    if proof and Path(proof) != proofBundlePath:
        blockers.append("replacementEvidenceProofBundleMismatch")
    return blockers


def _state(
    *,
    designReady: bool,
    opsReady: bool,
    releaseReady: bool,
    defaultReplacement: bool,
) -> str:
    if defaultReplacement:
        return "S4_DEFAULT_REPLACEMENT"
    if releaseReady:
        return "S3_RELEASE_READY"
    if opsReady:
        return "S2_OPS_READY"
    if designReady:
        return "S1_DESIGN_READY"
    return "S0_EXPERIMENT"


def _missingEvidence(proof: dict[str, Any]) -> list[str]:
    items = proof.get("missingEvidence")
    if not isinstance(items, list):
        return []
    return [str(item) for item in items if str(item).strip()]


def _opsMissingEvidence(proof: dict[str, Any]) -> list[str]:
    return [item for item in _missingEvidence(proof) if item not in RELEASE_ONLY_EVIDENCE]


def _releaseMissingEvidence(proof: dict[str, Any]) -> list[str]:
    return [item for item in _missingEvidence(proof) if item in RELEASE_ONLY_EVIDENCE]


def _replacementSummary(evidence: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "singleEngineDefault",
        "defaultBuildMode",
        "scheduledBuildMode",
        "legacyFallbackOperatorOnly",
        "failClosedPublish",
        "activeManifestId",
        "previousManifestId",
        "rollbackVerified",
        "runEvidenceRecorded",
        "surfaceNamingReviewed",
    )
    return {key: evidence.get(key) for key in keys if key in evidence}


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _loadJson(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object JSON: {path}")
    return data


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
