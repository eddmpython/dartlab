"""U3 catalog root를 source revision과 descriptor receipt에 결박한다."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from ..canonical import canonicalDigest
from ..contracts import Visibility
from ..temporal import parseInstant
from .descriptorCrawler import ResourceDescriptor
from .models import CatalogState


@dataclass(frozen=True, slots=True)
class SnapshotResourceRef:
    resourceId: str
    resourceVersionId: str
    sourceKind: str
    sourceRef: str
    sourceRevision: str
    locator: tuple[tuple[str, str], ...]
    contentSelector: tuple[tuple[str, str], ...]
    contentDigest: str
    visibility: Visibility
    licenseRef: str | None
    status: str
    descriptorDigest: str | None


@dataclass(frozen=True, slots=True)
class CatalogSnapshot:
    snapshotId: str
    schemaVersion: str
    universeSnapshotId: str
    catalogDigest: str
    descriptorSetDigest: str
    capabilityRegistryVersion: str
    identityLedgerVersion: str
    relationTaxonomyVersion: str
    resources: tuple[SnapshotResourceRef, ...]
    previousSnapshotId: str | None
    rootInputsDigest: str
    createdAt: str


def _rootInputs(snapshot: CatalogSnapshot) -> object:
    return {
        "schemaVersion": snapshot.schemaVersion,
        "universeSnapshotId": snapshot.universeSnapshotId,
        "catalogDigest": snapshot.catalogDigest,
        "descriptorSetDigest": snapshot.descriptorSetDigest,
        "capabilityRegistryVersion": snapshot.capabilityRegistryVersion,
        "identityLedgerVersion": snapshot.identityLedgerVersion,
        "relationTaxonomyVersion": snapshot.relationTaxonomyVersion,
        "resources": snapshot.resources,
        "previousSnapshotId": snapshot.previousSnapshotId,
    }


_DIGEST_BUFFER_BYTES = 1 << 20


class _DigestWriter:
    """대형 snapshot을 중간 object tree 없이 canonical SHA-256으로 흘린다."""

    def __init__(self) -> None:
        self._hasher = hashlib.sha256()
        self._buffer = bytearray()

    def write(self, value: bytes) -> None:
        self._buffer.extend(value)
        if len(self._buffer) >= _DIGEST_BUFFER_BYTES:
            self._hasher.update(self._buffer)
            self._buffer.clear()

    def hexdigest(self) -> str:
        if self._buffer:
            self._hasher.update(self._buffer)
            self._buffer.clear()
        return self._hasher.hexdigest()


def _appendJsonString(buffer: bytearray, value: str) -> None:
    normalized = unicodedata.normalize("NFC", value)
    buffer.extend(json.encoder.encode_basestring(normalized).encode("utf-8"))


def _appendOptionalJsonString(buffer: bytearray, value: str | None) -> None:
    if value is None:
        buffer.extend(b"null")
    else:
        _appendJsonString(buffer, value)


def _appendStringPairs(buffer: bytearray, values: tuple[tuple[str, str], ...]) -> None:
    buffer.extend(b"[")
    for index, (key, value) in enumerate(values):
        if index:
            buffer.extend(b",")
        buffer.extend(b"[")
        _appendJsonString(buffer, key)
        buffer.extend(b",")
        _appendJsonString(buffer, value)
        buffer.extend(b"]")
    buffer.extend(b"]")


def _snapshotResourceJson(item: SnapshotResourceRef) -> bytes:
    """SnapshotResourceRef 한 건을 canonical key 순서로 직렬화한다."""
    buffer = bytearray(b'{"contentDigest":')
    _appendJsonString(buffer, item.contentDigest)
    buffer.extend(b',"contentSelector":')
    _appendStringPairs(buffer, item.contentSelector)
    buffer.extend(b',"descriptorDigest":')
    _appendOptionalJsonString(buffer, item.descriptorDigest)
    buffer.extend(b',"licenseRef":')
    _appendOptionalJsonString(buffer, item.licenseRef)
    buffer.extend(b',"locator":')
    _appendStringPairs(buffer, item.locator)
    buffer.extend(b',"resourceId":')
    _appendJsonString(buffer, item.resourceId)
    buffer.extend(b',"resourceVersionId":')
    _appendJsonString(buffer, item.resourceVersionId)
    buffer.extend(b',"sourceKind":')
    _appendJsonString(buffer, item.sourceKind)
    buffer.extend(b',"sourceRef":')
    _appendJsonString(buffer, item.sourceRef)
    buffer.extend(b',"sourceRevision":')
    _appendJsonString(buffer, item.sourceRevision)
    buffer.extend(b',"status":')
    _appendJsonString(buffer, item.status)
    buffer.extend(b',"visibility":')
    _appendJsonString(buffer, item.visibility.value)
    buffer.extend(b"}")
    return bytes(buffer)


def catalogSnapshotRootDigest(snapshot: CatalogSnapshot) -> str:
    """기존 canonicalDigest와 byte 동일한 snapshot root를 bounded memory로 계산한다."""
    writer = _DigestWriter()
    prefix = bytearray(b'{"capabilityRegistryVersion":')
    _appendJsonString(prefix, snapshot.capabilityRegistryVersion)
    prefix.extend(b',"catalogDigest":')
    _appendJsonString(prefix, snapshot.catalogDigest)
    prefix.extend(b',"descriptorSetDigest":')
    _appendJsonString(prefix, snapshot.descriptorSetDigest)
    prefix.extend(b',"identityLedgerVersion":')
    _appendJsonString(prefix, snapshot.identityLedgerVersion)
    prefix.extend(b',"previousSnapshotId":')
    _appendOptionalJsonString(prefix, snapshot.previousSnapshotId)
    prefix.extend(b',"relationTaxonomyVersion":')
    _appendJsonString(prefix, snapshot.relationTaxonomyVersion)
    prefix.extend(b',"resources":[')
    writer.write(bytes(prefix))
    for index, item in enumerate(snapshot.resources):
        if index:
            writer.write(b",")
        writer.write(_snapshotResourceJson(item))
    suffix = bytearray(b'],"schemaVersion":')
    _appendJsonString(suffix, snapshot.schemaVersion)
    suffix.extend(b',"universeSnapshotId":')
    _appendJsonString(suffix, snapshot.universeSnapshotId)
    suffix.extend(b"}")
    writer.write(bytes(suffix))
    return writer.hexdigest()


def buildCatalogSnapshot(
    catalog: CatalogState,
    *,
    universeSnapshotId: str,
    descriptors: tuple[ResourceDescriptor, ...] = (),
    capabilityRegistryVersion: str,
    identityLedgerVersion: str,
    relationTaxonomyVersion: str,
    previousSnapshotId: str | None = None,
    createdAt: str | None = None,
) -> CatalogSnapshot:
    """Catalog과 C2 descriptor ref만 가진 immutable snapshot을 만든다."""
    descriptorByResource = {item.resourceVersionId: item for item in descriptors}
    if len(descriptorByResource) != len(descriptors):
        raise ValueError("resource version당 descriptor는 하나여야 함")
    resourceVersions = {item.resourceVersionId for item in catalog.resources}
    unknown = sorted(set(descriptorByResource) - resourceVersions)
    if unknown:
        raise ValueError(f"catalog 밖 descriptor: {unknown[0]}")
    refs = tuple(
        SnapshotResourceRef(
            resourceId=item.resourceId,
            resourceVersionId=item.resourceVersionId,
            sourceKind=item.sourceKind,
            sourceRef=item.sourceRef,
            sourceRevision=item.sourceRevision,
            locator=item.locator,
            contentSelector=item.contentSelector,
            contentDigest=item.contentDigest,
            visibility=item.visibility,
            licenseRef=item.licenseRef,
            status=item.status,
            descriptorDigest=descriptorByResource[item.resourceVersionId].digest
            if item.resourceVersionId in descriptorByResource
            else None,
        )
        for item in catalog.resources
    )
    base = CatalogSnapshot(
        snapshotId="",
        schemaVersion="du-catalog-snapshot-v2",
        universeSnapshotId=universeSnapshotId,
        catalogDigest=catalog.digest,
        descriptorSetDigest=canonicalDigest(tuple(sorted(item.digest for item in descriptors))),
        capabilityRegistryVersion=capabilityRegistryVersion,
        identityLedgerVersion=identityLedgerVersion,
        relationTaxonomyVersion=relationTaxonomyVersion,
        resources=refs,
        previousSnapshotId=previousSnapshotId,
        rootInputsDigest="",
        createdAt=createdAt or datetime.now(timezone.utc).isoformat(),
    )
    digest = catalogSnapshotRootDigest(base)
    return replace(base, snapshotId=f"du:v1:catalog-snapshot:{digest}", rootInputsDigest=digest)


def validateCatalogSnapshot(snapshot: CatalogSnapshot) -> tuple[str, ...]:
    """Snapshot root와 resource logical uniqueness를 fail-closed 검증한다."""
    issues = []
    if snapshot.schemaVersion != "du-catalog-snapshot-v2":
        issues.append("SNAPSHOT_SCHEMA_VERSION_MISMATCH")
    if (
        not snapshot.snapshotId
        or not snapshot.catalogDigest
        or not snapshot.descriptorSetDigest
        or not snapshot.rootInputsDigest
        or not snapshot.createdAt
    ):
        issues.append("SNAPSHOT_REQUIRED_FIELD_MISSING")
    if any(
        not re.fullmatch(r"[0-9a-f]{64}", value)
        for value in (snapshot.catalogDigest, snapshot.descriptorSetDigest, snapshot.rootInputsDigest)
    ):
        issues.append("SNAPSHOT_DIGEST_FORMAT_INVALID")
    digest = catalogSnapshotRootDigest(snapshot)
    if snapshot.rootInputsDigest != digest or snapshot.snapshotId != f"du:v1:catalog-snapshot:{digest}":
        issues.append("SNAPSHOT_ROOT_MISMATCH")
    logicalIds: set[str] = set()
    versionIds: set[str] = set()
    previousKey: tuple[str, str] | None = None
    orderMismatch = False
    duplicateLogicalId = False
    duplicateVersionId = False
    publicLicenseMissing = False
    provenanceMissing = False
    integrityInvalid = False
    for item in snapshot.resources:
        key = (item.resourceId, item.resourceVersionId)
        orderMismatch = orderMismatch or previousKey is not None and key < previousKey
        previousKey = key
        duplicateLogicalId = duplicateLogicalId or item.resourceId in logicalIds
        duplicateVersionId = duplicateVersionId or item.resourceVersionId in versionIds
        logicalIds.add(item.resourceId)
        versionIds.add(item.resourceVersionId)
        publicLicenseMissing = publicLicenseMissing or (item.visibility is Visibility.PUBLIC and not item.licenseRef)
        provenanceMissing = provenanceMissing or not (
            item.sourceKind and item.sourceRef and item.sourceRevision and item.locator
        )
        integrityInvalid = integrityInvalid or (
            not re.fullmatch(r"[0-9a-f]{64}", item.contentDigest)
            or item.descriptorDigest is not None
            and not re.fullmatch(r"[0-9a-f]{64}", item.descriptorDigest)
            or len(item.locator) != len(dict(item.locator))
            or len(item.contentSelector) != len(dict(item.contentSelector))
        )
    if orderMismatch:
        issues.append("SNAPSHOT_RESOURCE_ORDER_MISMATCH")
    if duplicateLogicalId:
        issues.append("DUPLICATE_RESOURCE_ID")
    if duplicateVersionId:
        issues.append("DUPLICATE_RESOURCE_VERSION_ID")
    if (
        not snapshot.universeSnapshotId
        or not snapshot.capabilityRegistryVersion
        or not snapshot.identityLedgerVersion
        or not snapshot.relationTaxonomyVersion
    ):
        issues.append("CONTROL_VERSION_MISSING")
    if publicLicenseMissing:
        issues.append("PUBLIC_SNAPSHOT_RESOURCE_LICENSE_MISSING")
    if provenanceMissing:
        issues.append("SNAPSHOT_RESOURCE_PROVENANCE_MISSING")
    if integrityInvalid:
        issues.append("SNAPSHOT_RESOURCE_INTEGRITY_INVALID")
    try:
        parseInstant(snapshot.createdAt)
    except ValueError:
        issues.append("SNAPSHOT_CREATED_AT_INVALID")
    return tuple(sorted(issues))
