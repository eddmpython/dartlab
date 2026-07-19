"""손상된 derived authority를 원문과 transform lineage로 복구하는 U3 계약."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace

import pyarrow as pa
import pyarrow.parquet as pq

from ..canonical import canonicalDigest
from ..controlPlane.cas import CasIntegrityError, ContentAddressedStore
from ..temporal import parseInstant
from .descriptorCrawler import ResourceDescriptor
from .models import CatalogResource, CatalogState

RECOVERY_SCHEMA_VERSION = "du-resource-recovery-v1"
REQUIRED_RECOVERY_VERIFICATIONS = (
    "ARTIFACT_CAS_DIGEST_VERIFIED",
    "ARTIFACT_FOOTER_VERIFIED",
    "ARTIFACT_FULL_READ_VERIFIED",
    "INPUT_OBJECTS_PINNED",
    "TARGET_FAILURE_REPRODUCED",
    "TRANSFORM_SOURCE_DIGEST_VERIFIED",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_ID_RE = re.compile(r"^[0-9a-f]{40,64}$")


@dataclass(frozen=True, slots=True)
class RecoverySourceObject:
    """Recovery recipe가 실제로 읽은 immutable source object."""

    role: str
    sourceRef: str
    path: str
    sourceObjectId: str
    byteSize: int
    payloadDigest: str


@dataclass(frozen=True, slots=True)
class ResourceRecovery:
    """손상 target, 원문, transform byte, 로컬 CAS artifact의 완전한 결박."""

    recoveryId: str
    schemaVersion: str
    targetResourceVersionId: str
    targetSourceRevision: str
    targetSourceRef: str
    targetPath: str
    targetSourceObjectId: str
    targetByteSize: int
    targetPayloadDigest: str
    targetDescriptorDigest: str
    targetErrorCode: str
    inputSources: tuple[RecoverySourceObject, ...]
    transformRef: str
    transformSourceDigest: str
    artifactObjectRef: str
    artifactContentDigest: str
    artifactByteSize: int
    artifactMediaType: str
    artifactSchemaFingerprint: str
    artifactRowCount: int
    artifactRowGroupCount: int
    artifactMetadata: tuple[tuple[str, str], ...]
    verificationCodes: tuple[str, ...]
    createdAt: str
    digest: str


@dataclass(frozen=True, slots=True)
class RecoveryValidationReport:
    valid: bool
    acceptedTargetVersionIds: tuple[str, ...]
    issueCodes: tuple[str, ...]
    recoverySetDigest: str
    digest: str


def _sourceIdentity(resource: CatalogResource, *, role: str, payloadDigest: str) -> RecoverySourceObject:
    locator = dict(resource.locator)
    path = locator.get("path", "")
    sourceObjectId = locator.get("oid", "")
    if (
        resource.resourceKind != "HF_FILE"
        or not path
        or not sourceObjectId
        or resource.byteSize is None
        or not _SHA256_RE.fullmatch(payloadDigest)
    ):
        raise ValueError("recovery input은 oid와 byteSize가 있는 HF_FILE이어야 함")
    return RecoverySourceObject(
        role=role,
        sourceRef=resource.sourceRef,
        path=path,
        sourceObjectId=sourceObjectId,
        byteSize=resource.byteSize,
        payloadDigest=payloadDigest,
    )


def _recoveryIdentity(recovery: ResourceRecovery) -> object:
    return {
        "schemaVersion": recovery.schemaVersion,
        "targetSourceRef": recovery.targetSourceRef,
        "targetPath": recovery.targetPath,
        "targetSourceObjectId": recovery.targetSourceObjectId,
        "targetByteSize": recovery.targetByteSize,
        "targetPayloadDigest": recovery.targetPayloadDigest,
        "targetErrorCode": recovery.targetErrorCode,
        "inputSources": recovery.inputSources,
        "transformRef": recovery.transformRef,
        "transformSourceDigest": recovery.transformSourceDigest,
        "artifactContentDigest": recovery.artifactContentDigest,
        "artifactByteSize": recovery.artifactByteSize,
        "artifactMediaType": recovery.artifactMediaType,
        "artifactSchemaFingerprint": recovery.artifactSchemaFingerprint,
        "artifactRowCount": recovery.artifactRowCount,
        "artifactRowGroupCount": recovery.artifactRowGroupCount,
        "artifactMetadata": recovery.artifactMetadata,
        "verificationCodes": recovery.verificationCodes,
    }


def buildResourceRecovery(
    target: CatalogResource,
    failedDescriptor: ResourceDescriptor,
    *,
    targetPayloadDigest: str,
    inputResources: tuple[tuple[str, CatalogResource, str], ...],
    transformRef: str,
    transformSourceDigest: str,
    artifactObjectRef: str,
    artifactByteSize: int,
    artifactMediaType: str,
    artifactSchemaFingerprint: str,
    artifactRowCount: int,
    artifactRowGroupCount: int,
    artifactMetadata: tuple[tuple[str, str], ...],
    createdAt: str,
) -> ResourceRecovery:
    """검증을 끝낸 artifact를 현재 target descriptor에 결박한다."""
    locator = dict(target.locator)
    if (
        target.resourceKind != "HF_FILE"
        or failedDescriptor.resourceVersionId != target.resourceVersionId
        or failedDescriptor.sourceRevision != target.sourceRevision
        or failedDescriptor.status not in {"PARSE_ERROR", "DESCRIPTOR_BLOCKED_RANGE"}
        or not failedDescriptor.errorCode
        or not locator.get("path")
        or not locator.get("oid")
        or target.byteSize is None
        or not _SHA256_RE.fullmatch(targetPayloadDigest)
    ):
        raise ValueError("recovery target은 재현된 terminal descriptor failure여야 함")
    artifactContentDigest = ContentAddressedStore.digestFromRef(artifactObjectRef)
    inputs = tuple(
        sorted(
            (
                _sourceIdentity(resource, role=role, payloadDigest=payloadDigest)
                for role, resource, payloadDigest in inputResources
            ),
            key=lambda item: (item.role, item.sourceRef, item.path, item.sourceObjectId),
        )
    )
    base = ResourceRecovery(
        recoveryId="",
        schemaVersion=RECOVERY_SCHEMA_VERSION,
        targetResourceVersionId=target.resourceVersionId,
        targetSourceRevision=target.sourceRevision,
        targetSourceRef=target.sourceRef,
        targetPath=locator["path"],
        targetSourceObjectId=locator["oid"],
        targetByteSize=target.byteSize,
        targetPayloadDigest=targetPayloadDigest,
        targetDescriptorDigest=failedDescriptor.digest,
        targetErrorCode=failedDescriptor.errorCode,
        inputSources=inputs,
        transformRef=transformRef,
        transformSourceDigest=transformSourceDigest,
        artifactObjectRef=artifactObjectRef,
        artifactContentDigest=artifactContentDigest,
        artifactByteSize=artifactByteSize,
        artifactMediaType=artifactMediaType,
        artifactSchemaFingerprint=artifactSchemaFingerprint,
        artifactRowCount=artifactRowCount,
        artifactRowGroupCount=artifactRowGroupCount,
        artifactMetadata=tuple(sorted(artifactMetadata)),
        verificationCodes=REQUIRED_RECOVERY_VERIFICATIONS,
        createdAt=createdAt,
        digest="",
    )
    recoveryId = f"du:v1:recovery:{canonicalDigest(_recoveryIdentity(base))}"
    bound = replace(base, recoveryId=recoveryId)
    return replace(bound, digest=canonicalDigest(bound))


def rebindResourceRecovery(
    recovery: ResourceRecovery,
    target: CatalogResource,
    failedDescriptor: ResourceDescriptor,
) -> ResourceRecovery:
    """동일 HF object가 새 repository HEAD에 나타나면 exact target만 다시 결박한다."""
    locator = dict(target.locator)
    if (
        target.sourceRef != recovery.targetSourceRef
        or locator.get("path") != recovery.targetPath
        or locator.get("oid") != recovery.targetSourceObjectId
        or target.byteSize != recovery.targetByteSize
        or failedDescriptor.resourceVersionId != target.resourceVersionId
        or failedDescriptor.errorCode != recovery.targetErrorCode
    ):
        raise ValueError("recovery content subject mismatch")
    rebound = replace(
        recovery,
        targetResourceVersionId=target.resourceVersionId,
        targetSourceRevision=target.sourceRevision,
        targetDescriptorDigest=failedDescriptor.digest,
        digest="",
    )
    return replace(rebound, digest=canonicalDigest(rebound))


def _matchesSource(resource: CatalogResource, source: RecoverySourceObject) -> bool:
    locator = dict(resource.locator)
    return (
        resource.resourceKind == "HF_FILE"
        and resource.sourceRef == source.sourceRef
        and locator.get("path") == source.path
        and locator.get("oid") == source.sourceObjectId
        and resource.byteSize == source.byteSize
    )


def _validateOne(
    recovery: ResourceRecovery,
    *,
    resourceByVersion: dict[str, CatalogResource],
    resources: tuple[CatalogResource, ...],
    descriptorByVersion: dict[str, ResourceDescriptor],
    cas: ContentAddressedStore | None,
) -> tuple[str, ...]:
    issues = []
    target = resourceByVersion.get(recovery.targetResourceVersionId)
    descriptor = descriptorByVersion.get(recovery.targetResourceVersionId)
    if recovery.schemaVersion != RECOVERY_SCHEMA_VERSION:
        issues.append("RECOVERY_SCHEMA_VERSION_MISMATCH")
    if target is None or descriptor is None:
        issues.append("RECOVERY_TARGET_MISSING")
    else:
        locator = dict(target.locator)
        if (
            target.sourceRevision != recovery.targetSourceRevision
            or target.sourceRef != recovery.targetSourceRef
            or locator.get("path") != recovery.targetPath
            or locator.get("oid") != recovery.targetSourceObjectId
            or target.byteSize != recovery.targetByteSize
        ):
            issues.append("RECOVERY_TARGET_SUBJECT_MISMATCH")
        if (
            descriptor.digest != recovery.targetDescriptorDigest
            or descriptor.errorCode != recovery.targetErrorCode
            or descriptor.status not in {"PARSE_ERROR", "DESCRIPTOR_BLOCKED_RANGE"}
        ):
            issues.append("RECOVERY_FAILURE_BINDING_MISMATCH")
    if not _SHA256_RE.fullmatch(recovery.targetPayloadDigest):
        issues.append("RECOVERY_TARGET_PAYLOAD_DIGEST_INVALID")
    if (
        not recovery.inputSources
        or recovery.inputSources
        != tuple(
            sorted(
                recovery.inputSources,
                key=lambda item: (item.role, item.sourceRef, item.path, item.sourceObjectId),
            )
        )
        or len(recovery.inputSources) != len(set(recovery.inputSources))
    ):
        issues.append("RECOVERY_INPUT_SET_INVALID")
    for source in recovery.inputSources:
        matches = sum(_matchesSource(resource, source) for resource in resources)
        if (
            not source.role
            or not source.sourceRef
            or not source.path
            or not _OBJECT_ID_RE.fullmatch(source.sourceObjectId)
            or isinstance(source.byteSize, bool)
            or source.byteSize <= 0
            or matches != 1
        ):
            issues.append("RECOVERY_INPUT_OBJECT_MISSING")
        if not _SHA256_RE.fullmatch(source.payloadDigest):
            issues.append("RECOVERY_INPUT_PAYLOAD_DIGEST_INVALID")
    if (
        not recovery.transformRef
        or not _SHA256_RE.fullmatch(recovery.transformSourceDigest)
        or recovery.artifactMediaType != "application/vnd.apache.parquet"
        or not _SHA256_RE.fullmatch(recovery.artifactContentDigest)
        or not _SHA256_RE.fullmatch(recovery.artifactSchemaFingerprint)
        or isinstance(recovery.artifactByteSize, bool)
        or recovery.artifactByteSize <= 12
        or isinstance(recovery.artifactRowCount, bool)
        or recovery.artifactRowCount < 0
        or isinstance(recovery.artifactRowGroupCount, bool)
        or recovery.artifactRowGroupCount <= 0
    ):
        issues.append("RECOVERY_ARTIFACT_CONTRACT_INVALID")
    try:
        objectDigest = ContentAddressedStore.digestFromRef(recovery.artifactObjectRef)
    except ValueError:
        objectDigest = ""
    if objectDigest != recovery.artifactContentDigest:
        issues.append("RECOVERY_ARTIFACT_REF_MISMATCH")
    if cas is None:
        issues.append("RECOVERY_ARTIFACT_CAS_UNVERIFIED")
    else:
        try:
            payload = cas.readBytes(recovery.artifactObjectRef)
        except CasIntegrityError:
            issues.append("RECOVERY_ARTIFACT_CAS_INVALID")
        else:
            if len(payload) != recovery.artifactByteSize or hashlib.sha256(payload).hexdigest() != objectDigest:
                issues.append("RECOVERY_ARTIFACT_CAS_INVALID")
            if not payload.startswith(b"PAR1") or not payload.endswith(b"PAR1"):
                issues.append("RECOVERY_ARTIFACT_FOOTER_INVALID")
            else:
                try:
                    parquet = pq.ParquetFile(pa.BufferReader(payload))
                    metadata = parquet.metadata
                    readRows = sum(batch.num_rows for batch in parquet.iter_batches(batch_size=8192))
                except (OSError, ValueError, pa.ArrowException):
                    issues.append("RECOVERY_ARTIFACT_FULL_READ_INVALID")
                else:
                    schemaFingerprint = canonicalDigest(str(parquet.schema_arrow))
                    if (
                        metadata.num_rows != recovery.artifactRowCount
                        or readRows != recovery.artifactRowCount
                        or metadata.num_row_groups != recovery.artifactRowGroupCount
                        or schemaFingerprint != recovery.artifactSchemaFingerprint
                    ):
                        issues.append("RECOVERY_ARTIFACT_METADATA_MISMATCH")
    if (
        recovery.artifactMetadata != tuple(sorted(recovery.artifactMetadata))
        or len(recovery.artifactMetadata) != len(dict(recovery.artifactMetadata))
        or any(not key for key, _value in recovery.artifactMetadata)
    ):
        issues.append("RECOVERY_ARTIFACT_METADATA_INVALID")
    if recovery.verificationCodes != REQUIRED_RECOVERY_VERIFICATIONS:
        issues.append("RECOVERY_VERIFICATION_INCOMPLETE")
    try:
        parseInstant(recovery.createdAt)
    except ValueError:
        issues.append("RECOVERY_CREATED_AT_INVALID")
    if recovery.recoveryId != f"du:v1:recovery:{canonicalDigest(_recoveryIdentity(recovery))}":
        issues.append("RECOVERY_ID_MISMATCH")
    if recovery.digest != canonicalDigest(replace(recovery, digest="")):
        issues.append("RECOVERY_DIGEST_MISMATCH")
    return tuple(sorted(set(issues)))


def validateRecoverySet(
    catalog: CatalogState,
    descriptors: tuple[ResourceDescriptor, ...],
    recoveries: tuple[ResourceRecovery, ...],
    *,
    cas: ContentAddressedStore | None,
) -> RecoveryValidationReport:
    """Recovery receipt를 current catalog, failure descriptor, CAS byte와 대조한다."""
    resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
    descriptorByVersion = {item.resourceVersionId: item for item in descriptors}
    issues = []
    accepted = []
    targetIds = tuple(item.targetResourceVersionId for item in recoveries)
    if len(targetIds) != len(set(targetIds)):
        issues.append("RECOVERY_TARGET_DUPLICATE")
    if len(recoveries) != len({item.recoveryId for item in recoveries}):
        issues.append("RECOVERY_ID_DUPLICATE")
    for recovery in recoveries:
        itemIssues = _validateOne(
            recovery,
            resourceByVersion=resourceByVersion,
            resources=catalog.resources,
            descriptorByVersion=descriptorByVersion,
            cas=cas,
        )
        issues.extend(itemIssues)
        if not itemIssues:
            accepted.append(recovery.targetResourceVersionId)
    base = RecoveryValidationReport(
        valid=not issues,
        acceptedTargetVersionIds=tuple(sorted(accepted)),
        issueCodes=tuple(sorted(set(issues))),
        recoverySetDigest=canonicalDigest(tuple(sorted(item.digest for item in recoveries))),
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))
