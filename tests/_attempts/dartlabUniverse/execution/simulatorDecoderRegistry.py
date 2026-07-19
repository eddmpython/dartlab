"""Allowlisted decoder로 receipt tree를 의미 bundle로 변환하고 SIMULATED 불변식을 검증한다."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..canonical import canonicalDigest
from ..contracts import ValidationIssue, ValidationReport
from .simulatorArtifactSchema import (
    SimulatorArtifactSchemaDescriptor,
    SimulatorArtifactSchemaRegistry,
    resolveSimulatorArtifactDescriptor,
)
from .simulatorReceiptSource import RegistrationResult

_JSON_DECODER_ID = "dartlab-universe-json-v1"
_JSON_DECODER_DIGEST = hashlib.sha256(b"dartlab-universe-json-decoder-v1").hexdigest()


@dataclass(frozen=True, slots=True)
class SafeDecoder:
    decoderId: str
    decoderDigest: str
    mediaType: str
    decode: Callable[[bytes], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class SimulatorSemanticNode:
    receiptId: str
    parentReceiptIds: tuple[str, ...]
    descriptorId: str
    artifactRole: str
    subjectHash: str
    artifactHash: str
    knowledgeAsOf: str
    revisionPolicy: str
    coverage: str
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    seedPolicy: str
    semantics: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class SimulatorSemanticBundle:
    rootReceiptId: str
    nodes: tuple[SimulatorSemanticNode, ...]
    epistemicClass: str
    status: str
    issues: tuple[str, ...]
    digest: str


def _decodeJson(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("simulator JSON artifact root는 object여야 함")
    return value


class SimulatorDecoderRegistry:
    def __init__(self, decoders: tuple[SafeDecoder, ...] | None = None) -> None:
        items = decoders or (
            SafeDecoder(
                decoderId=_JSON_DECODER_ID,
                decoderDigest=_JSON_DECODER_DIGEST,
                mediaType="application/json",
                decode=_decodeJson,
            ),
        )
        self._decoders = {item.decoderId: item for item in items}
        if len(self._decoders) != len(items):
            raise ValueError("safe decoder ID 중복")

    def resolve(self, descriptor: SimulatorArtifactSchemaDescriptor) -> SafeDecoder | None:
        decoder = self._decoders.get(descriptor.decoderId)
        if (
            decoder is None
            or decoder.decoderDigest != descriptor.decoderDigest
            or decoder.mediaType != descriptor.mediaType
        ):
            return None
        return decoder


def jsonDecoderContract() -> tuple[str, str]:
    return _JSON_DECODER_ID, _JSON_DECODER_DIGEST


def _valueAt(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for token in path.split("."):
        if not isinstance(current, dict) or token not in current:
            raise KeyError(path)
        current = current[token]
    return current


def _schemaRegistry(
    descriptors: SimulatorArtifactSchemaRegistry | tuple[SimulatorArtifactSchemaDescriptor, ...],
) -> SimulatorArtifactSchemaRegistry:
    return (
        descriptors
        if isinstance(descriptors, SimulatorArtifactSchemaRegistry)
        else SimulatorArtifactSchemaRegistry(descriptors)
    )


def decodeSimulatorReceiptTree(
    rootReceipt: RegistrationResult,
    descriptors: SimulatorArtifactSchemaRegistry | tuple[SimulatorArtifactSchemaDescriptor, ...],
) -> SimulatorSemanticBundle:
    """Verified receipt tree 전부를 exact descriptor와 safe decoder로 해석한다."""
    issues = []
    semanticNodes = []
    registry = _schemaRegistry(descriptors)
    decoders = SimulatorDecoderRegistry()
    if rootReceipt.status != "VERIFIED_ADMISSION_RECEIPT" or rootReceipt.root is None:
        issues.append("REJECTED_INVALID_ADMISSION_RECEIPT")
    else:
        nodeById = {item.receipt.receiptId: item for item in rootReceipt.receiptTree}
        for node in rootReceipt.receiptTree:
            receipt = node.receipt
            descriptor = resolveSimulatorArtifactDescriptor(receipt, registry)
            if descriptor is None:
                issues.append(f"SIMULATOR_SCHEMA_DESCRIPTOR_MISSING:{receipt.receiptId}")
                continue
            decoder = decoders.resolve(descriptor)
            if decoder is None:
                issues.append(f"SIMULATOR_DECODER_STALE:{receipt.receiptId}")
                continue
            raw = Path(node.artifactPath).read_bytes()
            if hashlib.sha256(raw).hexdigest() != receipt.artifactHash:
                issues.append(f"SIMULATOR_ARTIFACT_HASH_MISMATCH:{receipt.receiptId}")
                continue
            try:
                payload = decoder.decode(raw)
                if payload.get("schemaVersion") != descriptor.schemaVersion:
                    issues.append(f"SIMULATOR_ARTIFACT_SCHEMA_MISMATCH:{receipt.receiptId}:schemaVersion")
                    continue
                semantics = []
                for canonicalName, sourcePath in descriptor.fieldBindings:
                    semantics.append((canonicalName, _valueAt(payload, sourcePath)))
                semanticMap = dict(semantics)
                missing = [name for name in descriptor.requiredSemanticFields if name not in semanticMap]
                if missing:
                    issues.append(f"SIMULATOR_REQUIRED_SEMANTICS_MISSING:{receipt.receiptId}:{','.join(missing)}")
                    continue
                if descriptor.subjectHashRule == "ARTIFACT_HASH" and receipt.subjectHash != receipt.artifactHash:
                    issues.append(f"SIMULATOR_SUBJECT_MISMATCH:{receipt.receiptId}")
                    continue
                if descriptor.subjectHashRule == "FIELD_VALUE":
                    if (
                        descriptor.subjectBinding is None
                        or semanticMap.get(descriptor.subjectBinding) != receipt.subjectHash
                    ):
                        issues.append(f"SIMULATOR_SUBJECT_MISMATCH:{receipt.receiptId}")
                        continue
                parentRoles = []
                for parentId in receipt.parentReceiptIds:
                    parent = nodeById.get(parentId)
                    parentDescriptor = (
                        resolveSimulatorArtifactDescriptor(parent.receipt, registry) if parent is not None else None
                    )
                    parentRoles.append(parentDescriptor.artifactRole if parentDescriptor is not None else "UNKNOWN")
                if tuple(parentRoles) != descriptor.parentRoles:
                    issues.append(f"SIMULATOR_PARENT_ROLE_MISMATCH:{receipt.receiptId}")
                    continue
                semanticNodes.append(
                    SimulatorSemanticNode(
                        receiptId=receipt.receiptId,
                        parentReceiptIds=receipt.parentReceiptIds,
                        descriptorId=descriptor.descriptorId,
                        artifactRole=descriptor.artifactRole,
                        subjectHash=receipt.subjectHash,
                        artifactHash=receipt.artifactHash,
                        knowledgeAsOf=receipt.knowledgeAsOf,
                        revisionPolicy=receipt.revisionPolicy,
                        coverage=receipt.coverage,
                        frequency=receipt.frequency,
                        stepSpan=receipt.stepSpan,
                        maxAdmittedStep=receipt.maxAdmittedStep,
                        seedPolicy=descriptor.seedPolicy,
                        semantics=tuple(sorted(semantics, key=lambda item: item[0])),
                    )
                )
            except Exception as exc:
                issues.append(f"SIMULATOR_ARTIFACT_SCHEMA_MISMATCH:{receipt.receiptId}:{type(exc).__name__}")
    if issues:
        status = "VERIFIED_ARTIFACT_UNINTERPRETED"
    elif len(semanticNodes) != len(rootReceipt.receiptTree):
        status = "VERIFIED_ARTIFACT_UNINTERPRETED"
        issues.append("SIMULATOR_RECEIPT_TREE_INCOMPLETE")
    else:
        status = "DECODED_SIMULATED"
    orderedNodes = tuple(sorted(semanticNodes, key=lambda item: item.receiptId))
    orderedIssues = tuple(sorted(issues))
    digest = canonicalDigest(
        {
            "rootReceiptId": rootReceipt.receiptId,
            "nodes": orderedNodes,
            "epistemicClass": "SIMULATED",
            "status": status,
            "issues": orderedIssues,
        }
    )
    return SimulatorSemanticBundle(
        rootReceiptId=rootReceipt.receiptId,
        nodes=orderedNodes,
        epistemicClass="SIMULATED",
        status=status,
        issues=orderedIssues,
        digest=digest,
    )


def _dateText(value: Any) -> str:
    return str(value).replace("-", "")[:8]


def validateSimulatorSemanticBundle(bundle: SimulatorSemanticBundle, snapshot: Any) -> ValidationReport:
    """Simulator result가 snapshot, assumption, vintage, seed, version을 완전 보유하는지 검사한다."""
    issues = []
    if bundle.status != "DECODED_SIMULATED" or bundle.epistemicClass != "SIMULATED":
        issues.append(ValidationIssue("SIMULATOR_BUNDLE_NOT_ADMISSIBLE", "status", bundle.status))
    snapshotId = snapshot.get("snapshotId") if isinstance(snapshot, dict) else getattr(snapshot, "snapshotId", None)
    for node in bundle.nodes:
        values = dict(node.semantics)
        if node.receiptId != bundle.rootReceiptId:
            if "asOf" in values and _dateText(values["asOf"]) != _dateText(node.knowledgeAsOf):
                issues.append(ValidationIssue("SIMULATOR_VINTAGE_MISMATCH", node.receiptId, node.knowledgeAsOf))
            continue
        required = (
            "sourceSnapshotId",
            "targetRefs",
            "assumptionRefs",
            "asOf",
            "simulatorVersion",
            "codeRevision",
            "dependencyFingerprint",
            "outputSchema",
            "outputDigest",
            "revisionPolicy",
            "coverage",
            "frequency",
            "stepSpan",
            "maxAdmittedStep",
        )
        for name in required:
            value = values.get(name)
            if value is None or value == "" or value == () or value == []:
                issues.append(ValidationIssue("SIMULATION_SEMANTIC_REQUIRED", f"{node.receiptId}.{name}", "누락"))
        if values.get("sourceSnapshotId") != snapshotId:
            issues.append(ValidationIssue("SIMULATION_SNAPSHOT_MISMATCH", node.receiptId, str(snapshotId)))
        if node.seedPolicy == "REQUIRED" and values.get("seed") is None:
            issues.append(ValidationIssue("NONDETERMINISTIC_WITHOUT_SEED", node.receiptId, "seed"))
        if _dateText(node.knowledgeAsOf) != _dateText(values.get("asOf")):
            issues.append(ValidationIssue("SIMULATOR_VINTAGE_MISMATCH", node.receiptId, node.knowledgeAsOf))
        if node.revisionPolicy != "asKnown" or node.coverage != "asOfExact":
            issues.append(ValidationIssue("SIMULATOR_VINTAGE_NOT_EXACT", node.receiptId, node.revisionPolicy))
        for name, receiptValue in (
            ("revisionPolicy", node.revisionPolicy),
            ("coverage", node.coverage),
            ("frequency", node.frequency),
            ("stepSpan", node.stepSpan),
            ("maxAdmittedStep", node.maxAdmittedStep),
        ):
            if values.get(name) != receiptValue:
                issues.append(
                    ValidationIssue(
                        "SIMULATOR_RECEIPT_SEMANTIC_MISMATCH", f"{node.receiptId}.{name}", str(receiptValue)
                    )
                )
        if values.get("epistemicClass") not in {None, "SIMULATED"}:
            issues.append(ValidationIssue("SIMULATED_CLASS_LEAKAGE", node.receiptId, str(values.get("epistemicClass"))))
    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.path, item.detail)))
    return ValidationReport(valid=not ordered, issues=ordered, digest=canonicalDigest(ordered))
