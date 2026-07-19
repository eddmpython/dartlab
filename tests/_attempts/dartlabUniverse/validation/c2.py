"""Universe U3 descriptor coverage 전용 machine gate."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from ..canonical import canonicalDigest
from ..catalog.descriptorCrawler import (
    DESCRIPTOR_SCHEMA_VERSION,
    DescriptorPolicy,
    ResourceDescriptor,
    descriptorFormatKind,
)
from ..catalog.models import CatalogState
from ..catalog.recovery import ResourceRecovery, validateRecoverySet
from ..controlPlane.cas import ContentAddressedStore

_TERMINAL_STATES = frozenset(
    {"DESCRIBED", "UNSUPPORTED_FORMAT", "DESCRIPTOR_BLOCKED_RANGE", "PARSE_ERROR", "ACCESS_DENIED"}
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX_RE = re.compile(r"^(?:[0-9a-f]{2})*$")


@dataclass(frozen=True, slots=True)
class C2Report:
    gate: str
    passed: bool
    candidateCount: int
    terminalCount: int
    eligibleCount: int
    describedEligibleCount: int
    directlyDescribedEligibleCount: int
    recoveredEligibleCount: int
    recoveryReceiptCount: int
    recoverySetDigest: str
    recoveryValidationDigest: str
    unsupportedCount: int
    rangeRequestCount: int
    rangeBytesRead: int
    schemaFingerprintCoverageRatio: float
    rowContractCoverageRatio: float
    statusCounts: tuple[tuple[str, int], ...]
    failureCodes: tuple[str, ...]
    digest: str


def validateC2(
    catalog: CatalogState,
    descriptors: tuple[ResourceDescriptor, ...],
    *,
    policy: DescriptorPolicy | None = None,
    recoveries: tuple[ResourceRecovery, ...] = (),
    recoveryCas: ContentAddressedStore | None = None,
) -> C2Report:
    """모든 HF candidate가 source와 format에 결박된 terminal descriptor인지 검사한다."""
    activePolicy = policy or DescriptorPolicy()
    failures = []
    candidates = tuple(item for item in catalog.resources if item.resourceKind == "HF_FILE")
    candidateVersions = {item.resourceVersionId for item in candidates}
    descriptorByVersion = {item.resourceVersionId: item for item in descriptors}
    if len(descriptorByVersion) != len(descriptors):
        failures.append("DUPLICATE_DESCRIPTOR")
    if set(descriptorByVersion) != candidateVersions:
        failures.append("DESCRIPTOR_CANDIDATE_MISMATCH")
    terminalCount = sum(item.status in _TERMINAL_STATES for item in descriptors)
    if terminalCount != len(candidates):
        failures.append("DESCRIPTOR_NONTERMINAL")
    recoveryValidation = validateRecoverySet(catalog, descriptors, recoveries, cas=recoveryCas)
    if not recoveryValidation.valid:
        failures.append("RECOVERY_SET_INVALID")
        failures.extend(recoveryValidation.issueCodes)
    recoveryByTarget = {item.targetResourceVersionId: item for item in recoveries} if recoveryValidation.valid else {}
    eligible = tuple(item for item in candidates if descriptorFormatKind(item) != "UNSUPPORTED")
    describedEligible = 0
    directlyDescribedEligible = 0
    recoveredEligible = 0
    schemaCovered = 0
    rowCovered = 0
    for resource in candidates:
        descriptor = descriptorByVersion.get(resource.resourceVersionId)
        if descriptor is None:
            continue
        expectedKind = descriptorFormatKind(resource)
        if descriptor.digest != canonicalDigest(replace(descriptor, digest="")):
            failures.append("DESCRIPTOR_DIGEST_MISMATCH")
        if descriptor.descriptorId != canonicalDigest(
            (resource.resourceVersionId, expectedKind, DESCRIPTOR_SCHEMA_VERSION)
        ):
            failures.append("DESCRIPTOR_ID_MISMATCH")
        if (
            isinstance(descriptor.rangeRequestCount, bool)
            or descriptor.rangeRequestCount < 0
            or descriptor.rangeRequestCount > activePolicy.maxRangeRequests
            or isinstance(descriptor.rangeBytesRead, bool)
            or descriptor.rangeBytesRead < 0
            or descriptor.rangeBytesRead > activePolicy.maxRangeBytes
        ):
            failures.append("DESCRIPTOR_RANGE_ACCOUNTING_INVALID")
        if not _SHA256_RE.fullmatch(descriptor.responseDigest):
            failures.append("DESCRIPTOR_RESPONSE_DIGEST_INVALID")
        if descriptor.rowCount is not None and (isinstance(descriptor.rowCount, bool) or descriptor.rowCount < 0):
            failures.append("DESCRIPTOR_ROW_COUNT_INVALID")
        if (
            descriptor.metadata != tuple(sorted(descriptor.metadata))
            or len(descriptor.metadata) != len(dict(descriptor.metadata))
            or any(not key for key, _value in descriptor.metadata)
        ):
            failures.append("DESCRIPTOR_METADATA_INVALID")
        if descriptor.magicHex is not None and not _HEX_RE.fullmatch(descriptor.magicHex):
            failures.append("DESCRIPTOR_MAGIC_INVALID")
        if descriptor.status in {"DESCRIPTOR_BLOCKED_RANGE", "PARSE_ERROR", "ACCESS_DENIED"} and (
            not descriptor.errorCode or descriptor.schemaFingerprint is not None
        ):
            failures.append("DESCRIPTOR_STATUS_SHAPE_INVALID")
        if (
            descriptor.schemaVersion != DESCRIPTOR_SCHEMA_VERSION
            or descriptor.sourceRevision != resource.sourceRevision
            or descriptor.formatKind != expectedKind
        ):
            failures.append("DESCRIPTOR_SOURCE_MISMATCH")
        if expectedKind == "UNSUPPORTED":
            metadata = dict(descriptor.metadata)
            if (
                descriptor.status != "UNSUPPORTED_FORMAT"
                or descriptor.schemaFingerprint is not None
                or descriptor.errorCode is not None
                or descriptor.magicHex is None
                or not metadata.get("reason")
                or not metadata.get("sourceMeaning")
                or not metadata.get("declaredFormatKind")
            ):
                failures.append("UNSUPPORTED_DESCRIPTOR_INCOMPLETE")
            continue
        recovery = recoveryByTarget.get(resource.resourceVersionId)
        if descriptor.status != "DESCRIBED" and recovery is None:
            failures.append("DESCRIPTOR_ELIGIBLE_NOT_DESCRIBED")
            continue
        describedEligible += 1
        if recovery is not None:
            recoveredEligible += 1
            schemaCovered += 1
            rowCovered += 1
            continue
        directlyDescribedEligible += 1
        if descriptor.errorCode is not None:
            failures.append("DESCRIPTOR_STATUS_SHAPE_INVALID")
        if descriptor.schemaFingerprint and _SHA256_RE.fullmatch(descriptor.schemaFingerprint):
            schemaCovered += 1
        else:
            failures.append("SCHEMA_FINGERPRINT_INVALID")
        if descriptor.rowCount is not None or descriptor.rowCountUnavailableReason:
            rowCovered += 1
        else:
            failures.append("ROW_CONTRACT_MISSING")
    statuses: dict[str, int] = {}
    for descriptor in descriptors:
        statuses[descriptor.status] = statuses.get(descriptor.status, 0) + 1
    eligibleCount = len(eligible)
    base = C2Report(
        gate="C2",
        passed=False,
        candidateCount=len(candidates),
        terminalCount=terminalCount,
        eligibleCount=eligibleCount,
        describedEligibleCount=describedEligible,
        directlyDescribedEligibleCount=directlyDescribedEligible,
        recoveredEligibleCount=recoveredEligible,
        recoveryReceiptCount=len(recoveries),
        recoverySetDigest=recoveryValidation.recoverySetDigest,
        recoveryValidationDigest=recoveryValidation.digest,
        unsupportedCount=sum(descriptorFormatKind(item) == "UNSUPPORTED" for item in candidates),
        rangeRequestCount=sum(item.rangeRequestCount for item in descriptors),
        rangeBytesRead=sum(item.rangeBytesRead for item in descriptors),
        schemaFingerprintCoverageRatio=schemaCovered / eligibleCount if eligibleCount else 1.0,
        rowContractCoverageRatio=rowCovered / eligibleCount if eligibleCount else 1.0,
        statusCounts=tuple(sorted(statuses.items())),
        failureCodes=tuple(sorted(set(failures))),
        digest="",
    )
    report = replace(base, passed=not base.failureCodes)
    return replace(report, digest=canonicalDigest(report))
