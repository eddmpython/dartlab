"""C2 crawl 재시작을 위한 descriptor receipt 전용 local control-plane."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from ..canonical import canonicalDigest, canonicalJson
from .descriptorCrawler import DESCRIPTOR_SCHEMA_VERSION, DescriptorPolicy, ResourceDescriptor, descriptorFormatKind
from .models import CatalogResource

_TERMINAL_DESCRIPTOR_STATES = frozenset(
    {"DESCRIBED", "UNSUPPORTED_FORMAT", "DESCRIPTOR_BLOCKED_RANGE", "PARSE_ERROR", "ACCESS_DENIED"}
)
_REUSABLE_DESCRIPTOR_STATES = frozenset({"DESCRIBED", "UNSUPPORTED_FORMAT"})
_TRANSIENT_ERROR_CODES = frozenset({"RATE_LIMITED", "SOURCE_HTTP_ERROR", "TIMEOUT"})


class DescriptorCheckpointIntegrityError(RuntimeError):
    """Checkpoint byte가 receipt와 다르거나 immutable key가 충돌했다."""


@dataclass(frozen=True, slots=True)
class DescriptorSnapshotPin:
    """C2가 통과한 descriptor 집합과 exact source revision의 원자적 경계."""

    schemaVersion: str
    observedAtUtc: str
    sourceRevisions: tuple[tuple[str, str], ...]
    hfRepoFileCounts: tuple[tuple[str, int], ...]
    hfCandidateCount: int
    catalogDigest: str
    u0SnapshotDigest: str
    descriptorPolicyDigest: str
    c2Digest: str
    digest: str


def buildDescriptorSnapshotPin(
    *,
    observedAtUtc: str,
    sourceRevisions: tuple[tuple[str, str], ...],
    hfRepoFileCounts: tuple[tuple[str, int], ...],
    hfCandidateCount: int,
    catalogDigest: str,
    u0SnapshotDigest: str,
    policy: DescriptorPolicy,
    c2Digest: str,
) -> DescriptorSnapshotPin:
    """검증된 C2 실행을 U3가 exact replay할 수 있는 digest 결박 pin으로 만든다."""
    orderedRevisions = tuple(sorted(sourceRevisions))
    orderedCounts = tuple(sorted(hfRepoFileCounts))
    if (
        not observedAtUtc
        or len(orderedRevisions) != len({repoId for repoId, _revision in orderedRevisions})
        or tuple(repoId for repoId, _revision in orderedRevisions) != tuple(repoId for repoId, _count in orderedCounts)
        or any(not repoId or re.fullmatch(r"[0-9a-f]{40}", revision) is None for repoId, revision in orderedRevisions)
        or any(count < 0 for _repoId, count in orderedCounts)
        or hfCandidateCount != sum(count for _repoId, count in orderedCounts)
        or any(re.fullmatch(r"[0-9a-f]{64}", value) is None for value in (catalogDigest, u0SnapshotDigest, c2Digest))
    ):
        raise ValueError("descriptor snapshot pin 입력이 유효하지 않음")
    base = DescriptorSnapshotPin(
        schemaVersion="du-descriptor-snapshot-pin-v1",
        observedAtUtc=observedAtUtc,
        sourceRevisions=orderedRevisions,
        hfRepoFileCounts=orderedCounts,
        hfCandidateCount=hfCandidateCount,
        catalogDigest=catalogDigest,
        u0SnapshotDigest=u0SnapshotDigest,
        descriptorPolicyDigest=descriptorPolicyDigest(policy),
        c2Digest=c2Digest,
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))


def _decodeSnapshotPin(payload: bytes) -> DescriptorSnapshotPin:
    try:
        value = json.loads(payload)
        value["sourceRevisions"] = tuple(tuple(item) for item in value["sourceRevisions"])
        value["hfRepoFileCounts"] = tuple((str(item[0]), int(item[1])) for item in value["hfRepoFileCounts"])
        pin = DescriptorSnapshotPin(**value)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DescriptorCheckpointIntegrityError("descriptor snapshot pin decode failure") from exc
    if pin.schemaVersion != "du-descriptor-snapshot-pin-v1" or pin.digest != canonicalDigest(replace(pin, digest="")):
        raise DescriptorCheckpointIntegrityError("descriptor snapshot pin digest mismatch")
    return pin


class DescriptorLeaseHeartbeat:
    """긴 quota wait 중에도 crawl lease를 별도 SQLite connection으로 유지한다."""

    def __init__(self, path: Path, ownerId: str, *, ttlSeconds: float = 120.0, intervalSeconds: float = 30.0):
        if intervalSeconds <= 0 or ttlSeconds <= intervalSeconds:
            raise ValueError("lease heartbeat interval은 TTL보다 짧은 양수여야 함")
        self.path = path
        self.ownerId = ownerId
        self.ttlSeconds = ttlSeconds
        self.intervalSeconds = intervalSeconds
        self.stopEvent = threading.Event()
        self.error: Exception | None = None
        self.thread = threading.Thread(target=self._run, name="universe-c2-lease", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            connection = sqlite3.connect(self.path, timeout=30.0)
            try:
                while not self.stopEvent.wait(self.intervalSeconds):
                    with connection:
                        cursor = connection.execute(
                            "UPDATE crawl_lease SET expires_at = ? WHERE singleton = 1 AND owner_id = ?",
                            (time.time() + self.ttlSeconds, self.ownerId),
                        )
                    if cursor.rowcount != 1:
                        raise RuntimeError("descriptor crawl lease heartbeat가 owner를 잃음")
            finally:
                connection.close()
        except Exception as exc:
            self.error = exc
            self.stopEvent.set()

    def check(self) -> None:
        if self.error is not None:
            raise RuntimeError("descriptor crawl lease heartbeat 실패") from self.error

    def close(self) -> None:
        self.stopEvent.set()
        self.thread.join(timeout=self.intervalSeconds + 5.0)
        if self.thread.is_alive():
            raise RuntimeError("descriptor crawl lease heartbeat 종료 실패")
        self.check()


def descriptorPolicyDigest(policy: DescriptorPolicy) -> str:
    return _fastCanonicalDigest(
        {
            "descriptorSchemaVersion": DESCRIPTOR_SCHEMA_VERSION,
            "maxWholeObjectBytes": policy.maxWholeObjectBytes,
            "maxRangeRequests": policy.maxRangeRequests,
            "maxRangeBytes": policy.maxRangeBytes,
        }
    )


def descriptorContentKey(resource: CatalogResource) -> str | None:
    """동일 source byte와 format을 revision을 넘어 재사용할 stable key로 만든다."""
    if resource.resourceKind != "HF_FILE" or resource.byteSize is None or resource.byteSize < 0:
        return None
    locator = dict(resource.locator)
    sourceObjectId = locator.get("oid") or resource.contentDigest
    if not resource.sourceRef or not sourceObjectId or not re.fullmatch(r"[0-9a-f]{40,64}", sourceObjectId):
        return None
    return _fastCanonicalDigest(
        {
            "schemaVersion": "du-descriptor-content-key-v1",
            "sourceRef": resource.sourceRef,
            "sourceObjectId": sourceObjectId,
            "byteSize": resource.byteSize,
            "formatKind": descriptorFormatKind(resource),
            "descriptorSchemaVersion": DESCRIPTOR_SCHEMA_VERSION,
        }
    )


def _descriptorSemanticDigest(descriptor: ResourceDescriptor) -> str:
    return canonicalDigest(
        {
            "schemaVersion": descriptor.schemaVersion,
            "formatKind": descriptor.formatKind,
            "status": descriptor.status,
            "schemaFingerprint": descriptor.schemaFingerprint,
            "rowCount": descriptor.rowCount,
            "rowCountUnavailableReason": descriptor.rowCountUnavailableReason,
            "metadata": descriptor.metadata,
            "magicHex": descriptor.magicHex,
            "responseDigest": descriptor.responseDigest,
            "errorCode": descriptor.errorCode,
        }
    )


def _fastCanonicalDigest(value: object) -> str:
    """이미 canonical payload에서 decode된 JSON 호환 값의 SHA-256을 계산한다."""
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _fastDescriptorSemanticDigest(descriptor: ResourceDescriptor) -> str:
    """Checkpoint canonical payload에서 복원한 descriptor의 semantic digest fast path."""
    return _fastCanonicalDigest(
        {
            "schemaVersion": descriptor.schemaVersion,
            "formatKind": descriptor.formatKind,
            "status": descriptor.status,
            "schemaFingerprint": descriptor.schemaFingerprint,
            "rowCount": descriptor.rowCount,
            "rowCountUnavailableReason": descriptor.rowCountUnavailableReason,
            "metadata": descriptor.metadata,
            "magicHex": descriptor.magicHex,
            "responseDigest": descriptor.responseDigest,
            "errorCode": descriptor.errorCode,
        }
    )


def _fastDescriptorDigest(descriptor: ResourceDescriptor) -> str:
    """Canonical payload field를 명시해 범용 dataclass 재귀 없이 digest를 계산한다."""
    return _fastCanonicalDigest(
        {
            "descriptorId": descriptor.descriptorId,
            "schemaVersion": descriptor.schemaVersion,
            "resourceVersionId": descriptor.resourceVersionId,
            "sourceRevision": descriptor.sourceRevision,
            "formatKind": descriptor.formatKind,
            "status": descriptor.status,
            "schemaFingerprint": descriptor.schemaFingerprint,
            "rowCount": descriptor.rowCount,
            "rowCountUnavailableReason": descriptor.rowCountUnavailableReason,
            "metadata": descriptor.metadata,
            "magicHex": descriptor.magicHex,
            "rangeRequestCount": descriptor.rangeRequestCount,
            "rangeBytesRead": descriptor.rangeBytesRead,
            "responseDigest": descriptor.responseDigest,
            "errorCode": descriptor.errorCode,
            "digest": "",
        }
    )


def _rebindDescriptor(descriptor: ResourceDescriptor, resource: CatalogResource) -> ResourceDescriptor:
    formatKind = descriptorFormatKind(resource)
    base = replace(
        descriptor,
        descriptorId=_fastCanonicalDigest((resource.resourceVersionId, formatKind, DESCRIPTOR_SCHEMA_VERSION)),
        resourceVersionId=resource.resourceVersionId,
        sourceRevision=resource.sourceRevision,
        formatKind=formatKind,
        rangeRequestCount=0,
        rangeBytesRead=0,
        digest="",
    )
    return replace(base, digest=_fastDescriptorDigest(base))


def _decode(payload: bytes) -> ResourceDescriptor:
    value = json.loads(payload)
    claimedDigest = value.get("digest")
    if not isinstance(claimedDigest, str) or not re.fullmatch(r"[0-9a-f]{64}", claimedDigest):
        raise DescriptorCheckpointIntegrityError("descriptor digest missing")
    needle = b',"digest":"' + claimedDigest.encode("ascii") + b'","errorCode":'
    if payload.count(needle) != 1:
        raise DescriptorCheckpointIntegrityError("descriptor canonical digest slot mismatch")
    digestPayload = payload.replace(
        needle,
        b',"digest":"","errorCode":',
        1,
    )
    if claimedDigest != hashlib.sha256(digestPayload).hexdigest():
        raise DescriptorCheckpointIntegrityError("descriptor digest mismatch")
    value["metadata"] = tuple(tuple(item) for item in value["metadata"])
    descriptor = ResourceDescriptor(**value)
    return descriptor


class DescriptorCheckpointStore:
    """Source payload 없이 재사용 가능한 descriptor receipt만 durable하게 저장한다."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=30.0)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute("PRAGMA cache_size=-65536")
        self.connection.execute("PRAGMA mmap_size=536870912")
        integrity = self.connection.execute("PRAGMA quick_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            self.connection.close()
            raise DescriptorCheckpointIntegrityError(f"descriptor checkpoint integrity failure: {integrity}")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS descriptor_receipts (
                resource_version_id TEXT NOT NULL,
                source_revision TEXT NOT NULL,
                format_kind TEXT NOT NULL,
                policy_digest TEXT NOT NULL,
                descriptor_digest TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                payload BLOB NOT NULL,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (resource_version_id, policy_digest)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS descriptor_content_cache (
                policy_digest TEXT NOT NULL,
                content_key TEXT NOT NULL,
                format_kind TEXT NOT NULL,
                semantic_digest TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                payload BLOB NOT NULL,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (policy_digest, content_key)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS descriptor_terminal_attempts (
                resource_version_id TEXT NOT NULL,
                source_revision TEXT NOT NULL,
                format_kind TEXT NOT NULL,
                policy_digest TEXT NOT NULL,
                descriptor_digest TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                payload BLOB NOT NULL,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (resource_version_id, policy_digest, descriptor_digest)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS crawl_lease (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                owner_id TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS descriptor_snapshot_pin (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                payload_digest TEXT NOT NULL,
                payload BLOB NOT NULL,
                completed_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()
        self.lastLoadReusedCount = 0

    def acquireLease(self, *, ttlSeconds: float = 120.0) -> str:
        """동시에 하나의 crawler만 checkpoint를 갱신하도록 만료 lease를 잡는다."""
        if ttlSeconds <= 0:
            raise ValueError("lease TTL은 양수여야 함")
        ownerId = uuid.uuid4().hex
        now = time.time()
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            current = self.connection.execute(
                "SELECT owner_id, expires_at FROM crawl_lease WHERE singleton = 1"
            ).fetchone()
            if current is not None and float(current[1]) > now:
                raise RuntimeError("descriptor crawl lease가 이미 활성 상태임")
            self.connection.execute(
                "INSERT OR REPLACE INTO crawl_lease VALUES (1, ?, ?)",
                (ownerId, now + ttlSeconds),
            )
        return ownerId

    def renewLease(self, ownerId: str, *, ttlSeconds: float = 120.0) -> None:
        """현재 owner만 lease heartbeat를 연장할 수 있다."""
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE crawl_lease SET expires_at = ? WHERE singleton = 1 AND owner_id = ?",
                (time.time() + ttlSeconds, ownerId),
            )
        if cursor.rowcount != 1:
            raise RuntimeError("descriptor crawl lease를 잃음")

    def startLeaseHeartbeat(
        self,
        ownerId: str,
        *,
        ttlSeconds: float = 120.0,
        intervalSeconds: float = 30.0,
    ) -> DescriptorLeaseHeartbeat:
        """별도 connection heartbeat를 시작한다."""
        return DescriptorLeaseHeartbeat(
            self.path,
            ownerId,
            ttlSeconds=ttlSeconds,
            intervalSeconds=intervalSeconds,
        )

    def releaseLease(self, ownerId: str) -> None:
        """현재 owner의 lease만 해제한다."""
        with self.connection:
            self.connection.execute(
                "DELETE FROM crawl_lease WHERE singleton = 1 AND owner_id = ?",
                (ownerId,),
            )

    def assertNoActiveLease(self) -> None:
        """완성 gate가 진행 중 checkpoint를 읽지 못하게 한다."""
        current = self.connection.execute("SELECT expires_at FROM crawl_lease WHERE singleton = 1").fetchone()
        if current is not None and float(current[0]) > time.time():
            raise RuntimeError("descriptor crawl이 진행 중이므로 final gate를 실행할 수 없음")

    def assertLeaseOwner(self, ownerId: str) -> None:
        """현재 유효한 crawler lease가 지정 owner에 속하는지 확인한다."""
        current = self.connection.execute("SELECT owner_id, expires_at FROM crawl_lease WHERE singleton = 1").fetchone()
        if current is None or str(current[0]) != ownerId or float(current[1]) <= time.time():
            raise RuntimeError("descriptor crawl lease owner가 유효하지 않음")

    def loadSnapshotPin(self) -> DescriptorSnapshotPin:
        """가장 최근에 원자적으로 봉인한 C2 source revision 경계를 읽는다."""
        row = self.connection.execute(
            "SELECT payload_digest, payload FROM descriptor_snapshot_pin WHERE singleton = 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("통과한 C2 descriptor snapshot pin이 없음")
        payloadDigest, rawPayload = row
        payload = bytes(rawPayload)
        if hashlib.sha256(payload).hexdigest() != payloadDigest:
            raise DescriptorCheckpointIntegrityError("descriptor snapshot pin checksum mismatch")
        return _decodeSnapshotPin(payload)

    def put(
        self,
        descriptor: ResourceDescriptor,
        policy: DescriptorPolicy,
        *,
        resourcesByVersion: Mapping[str, CatalogResource] | None = None,
    ) -> None:
        """성공 descriptor를 immutable key로 기록하고 재시도 상태는 저장하지 않는다."""
        self.putMany((descriptor,), policy, resourcesByVersion=resourcesByVersion)

    def putMany(
        self,
        descriptors: tuple[ResourceDescriptor, ...],
        policy: DescriptorPolicy,
        *,
        resourcesByVersion: Mapping[str, CatalogResource] | None = None,
    ) -> None:
        """여러 terminal 결과를 검증하고 재사용 가능한 receipt만 checkpoint한다."""
        if not descriptors:
            return
        policyDigest = descriptorPolicyDigest(policy)
        seen = set()
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            for descriptor in descriptors:
                if descriptor.resourceVersionId in seen:
                    raise DescriptorCheckpointIntegrityError("descriptor batch duplicate")
                seen.add(descriptor.resourceVersionId)
                if (
                    descriptor.schemaVersion != DESCRIPTOR_SCHEMA_VERSION
                    or descriptor.status not in _TERMINAL_DESCRIPTOR_STATES
                    or descriptor.errorCode in _TRANSIENT_ERROR_CODES
                    or not descriptor.resourceVersionId
                    or not descriptor.sourceRevision
                    or descriptor.digest != canonicalDigest(ResourceDescriptor(**{**asdict(descriptor), "digest": ""}))
                ):
                    raise DescriptorCheckpointIntegrityError("terminal descriptor integrity mismatch")
                payload = canonicalJson(descriptor)
                payloadDigest = hashlib.sha256(payload).hexdigest()
                if descriptor.status not in _REUSABLE_DESCRIPTOR_STATES:
                    self.connection.execute(
                        "INSERT OR IGNORE INTO descriptor_terminal_attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            descriptor.resourceVersionId,
                            descriptor.sourceRevision,
                            descriptor.formatKind,
                            policyDigest,
                            descriptor.digest,
                            payloadDigest,
                            payload,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                    continue
                existing = self.connection.execute(
                    "SELECT payload, payload_digest FROM descriptor_receipts "
                    "WHERE resource_version_id = ? AND policy_digest = ?",
                    (descriptor.resourceVersionId, policyDigest),
                ).fetchone()
                if existing is not None:
                    if bytes(existing[0]) != payload or existing[1] != payloadDigest:
                        existingPayload = bytes(existing[0])
                        if hashlib.sha256(existingPayload).hexdigest() != existing[1]:
                            raise DescriptorCheckpointIntegrityError("descriptor payload checksum mismatch")
                        if _decode(existingPayload).status in _REUSABLE_DESCRIPTOR_STATES:
                            raise DescriptorCheckpointIntegrityError("immutable descriptor receipt conflict")
                        self.connection.execute(
                            "UPDATE descriptor_receipts SET source_revision = ?, format_kind = ?, "
                            "descriptor_digest = ?, payload_digest = ?, payload = ?, completed_at = ? "
                            "WHERE resource_version_id = ? AND policy_digest = ?",
                            (
                                descriptor.sourceRevision,
                                descriptor.formatKind,
                                descriptor.digest,
                                payloadDigest,
                                payload,
                                datetime.now(timezone.utc).isoformat(),
                                descriptor.resourceVersionId,
                                policyDigest,
                            ),
                        )
                else:
                    self.connection.execute(
                        "INSERT INTO descriptor_receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            descriptor.resourceVersionId,
                            descriptor.sourceRevision,
                            descriptor.formatKind,
                            policyDigest,
                            descriptor.digest,
                            payloadDigest,
                            payload,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                if resourcesByVersion is not None and descriptor.status in _REUSABLE_DESCRIPTOR_STATES:
                    resource = resourcesByVersion.get(descriptor.resourceVersionId)
                    if resource is None:
                        raise DescriptorCheckpointIntegrityError("descriptor content resource missing")
                    if (
                        resource.sourceRevision != descriptor.sourceRevision
                        or descriptorFormatKind(resource) != descriptor.formatKind
                    ):
                        raise DescriptorCheckpointIntegrityError("descriptor content subject mismatch")
                    contentKey = descriptorContentKey(resource)
                    if contentKey is None:
                        continue
                    semanticDigest = _descriptorSemanticDigest(descriptor)
                    cached = self.connection.execute(
                        "SELECT semantic_digest, payload_digest, payload FROM descriptor_content_cache "
                        "WHERE policy_digest = ? AND content_key = ?",
                        (policyDigest, contentKey),
                    ).fetchone()
                    if cached is not None:
                        cachedPayload = bytes(cached[2])
                        if (
                            cached[0] != semanticDigest
                            or hashlib.sha256(cachedPayload).hexdigest() != cached[1]
                            or _descriptorSemanticDigest(_decode(cachedPayload)) != semanticDigest
                        ):
                            raise DescriptorCheckpointIntegrityError("descriptor content cache conflict")
                    else:
                        self.connection.execute(
                            "INSERT INTO descriptor_content_cache VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                policyDigest,
                                contentKey,
                                descriptor.formatKind,
                                semanticDigest,
                                payloadDigest,
                                payload,
                                datetime.now(timezone.utc).isoformat(),
                            ),
                        )

    def load(
        self,
        resources: tuple[CatalogResource, ...],
        policy: DescriptorPolicy,
    ) -> tuple[ResourceDescriptor, ...]:
        """현재 revision exact match와 동일 content의 성공 descriptor만 복원한다."""
        policyDigest = descriptorPolicyDigest(policy)
        resourceByVersion = {item.resourceVersionId: item for item in resources if item.resourceKind == "HF_FILE"}
        descriptors = []
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS temp.load_descriptor_versions")
            self.connection.execute("CREATE TEMP TABLE load_descriptor_versions (resource_version_id TEXT PRIMARY KEY)")
            self.connection.executemany(
                "INSERT INTO load_descriptor_versions VALUES (?)",
                ((item,) for item in resourceByVersion),
            )
        try:
            rows = self.connection.execute(
                "SELECT receipt.resource_version_id, receipt.source_revision, receipt.format_kind, "
                "receipt.descriptor_digest, receipt.payload_digest, receipt.payload "
                "FROM descriptor_receipts receipt "
                "JOIN load_descriptor_versions live "
                "ON live.resource_version_id = receipt.resource_version_id "
                "WHERE receipt.policy_digest = ? ORDER BY receipt.resource_version_id",
                (policyDigest,),
            )
            for resourceVersionId, sourceRevision, formatKind, descriptorDigest, payloadDigest, rawPayload in rows:
                resource = resourceByVersion[resourceVersionId]
                payload = bytes(rawPayload)
                if hashlib.sha256(payload).hexdigest() != payloadDigest:
                    raise DescriptorCheckpointIntegrityError("descriptor payload checksum mismatch")
                if sourceRevision != resource.sourceRevision or formatKind != descriptorFormatKind(resource):
                    continue
                descriptor = _decode(payload)
                if (
                    descriptor.resourceVersionId != resourceVersionId
                    or descriptor.sourceRevision != sourceRevision
                    or descriptor.formatKind != formatKind
                    or descriptor.digest != descriptorDigest
                ):
                    raise DescriptorCheckpointIntegrityError("descriptor receipt column mismatch")
                if descriptor.status in _REUSABLE_DESCRIPTOR_STATES:
                    descriptors.append(descriptor)
        finally:
            with self.connection:
                self.connection.execute("DROP TABLE IF EXISTS temp.load_descriptor_versions")
        loadedVersions = {item.resourceVersionId for item in descriptors}
        resourcesByContentKey: dict[str, list[CatalogResource]] = {}
        for resource in resourceByVersion.values():
            if resource.resourceVersionId in loadedVersions:
                continue
            contentKey = descriptorContentKey(resource)
            if contentKey is not None:
                resourcesByContentKey.setdefault(contentKey, []).append(resource)
        reusedCount = 0
        if resourcesByContentKey:
            with self.connection:
                self.connection.execute("DROP TABLE IF EXISTS temp.load_descriptor_content_keys")
                self.connection.execute("CREATE TEMP TABLE load_descriptor_content_keys (content_key TEXT PRIMARY KEY)")
                self.connection.executemany(
                    "INSERT INTO load_descriptor_content_keys VALUES (?)",
                    ((item,) for item in resourcesByContentKey),
                )
            try:
                cacheCursor = self.connection.execute(
                    "SELECT cache.content_key, cache.format_kind, cache.semantic_digest, "
                    "cache.payload_digest, cache.payload "
                    "FROM descriptor_content_cache cache "
                    "JOIN load_descriptor_content_keys live ON live.content_key = cache.content_key "
                    "WHERE cache.policy_digest = ? ORDER BY cache.content_key",
                    (policyDigest,),
                )
                for rawContentKey, rawFormatKind, rawSemanticDigest, rawPayloadDigest, rawPayload in cacheCursor:
                    targets = resourcesByContentKey[str(rawContentKey)]
                    formatKind = str(rawFormatKind)
                    semanticDigest = str(rawSemanticDigest)
                    payloadDigest = str(rawPayloadDigest)
                    payload = bytes(rawPayload)
                    if hashlib.sha256(payload).hexdigest() != payloadDigest:
                        raise DescriptorCheckpointIntegrityError("descriptor content cache checksum mismatch")
                    cachedDescriptor = _decode(payload)
                    if _fastDescriptorSemanticDigest(cachedDescriptor) != semanticDigest:
                        raise DescriptorCheckpointIntegrityError("descriptor content cache semantic mismatch")
                    if cachedDescriptor.status not in _REUSABLE_DESCRIPTOR_STATES:
                        continue
                    for resource in targets:
                        if formatKind != descriptorFormatKind(resource):
                            raise DescriptorCheckpointIntegrityError("descriptor content cache format mismatch")
                        descriptors.append(_rebindDescriptor(cachedDescriptor, resource))
                        reusedCount += 1
            finally:
                with self.connection:
                    self.connection.execute("DROP TABLE IF EXISTS temp.load_descriptor_content_keys")
        self.lastLoadReusedCount = reusedCount
        return tuple(sorted(descriptors, key=lambda item: item.resourceVersionId))

    def pruneObsolete(
        self,
        resources: tuple[CatalogResource, ...],
        policy: DescriptorPolicy,
        *,
        snapshotPin: DescriptorSnapshotPin | None = None,
        leaseOwner: str | None = None,
    ) -> int:
        """Gate 통과 후 receipt 정리와 C2 snapshot pin 교체를 원자적으로 수행한다."""
        if leaseOwner is None:
            self.assertNoActiveLease()
        else:
            self.assertLeaseOwner(leaseOwner)
        policyDigest = descriptorPolicyDigest(policy)
        liveVersions = tuple(sorted(item.resourceVersionId for item in resources if item.resourceKind == "HF_FILE"))
        if snapshotPin is not None:
            if (
                snapshotPin.descriptorPolicyDigest != policyDigest
                or snapshotPin.hfCandidateCount != len(liveVersions)
                or snapshotPin.digest != canonicalDigest(replace(snapshotPin, digest=""))
            ):
                raise ValueError("descriptor snapshot pin과 live catalog가 일치하지 않음")
            currentRow = self.connection.execute(
                "SELECT payload FROM descriptor_snapshot_pin WHERE singleton = 1"
            ).fetchone()
            if currentRow is not None:
                currentPin = _decodeSnapshotPin(bytes(currentRow[0]))
                if currentPin.observedAtUtc > snapshotPin.observedAtUtc:
                    return 0
        before = int(self.connection.execute("SELECT count(*) FROM descriptor_receipts").fetchone()[0])
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            self.connection.execute("DROP TABLE IF EXISTS temp.live_descriptor_versions")
            self.connection.execute("CREATE TEMP TABLE live_descriptor_versions (resource_version_id TEXT PRIMARY KEY)")
            self.connection.executemany(
                "INSERT INTO live_descriptor_versions VALUES (?)",
                ((item,) for item in liveVersions),
            )
            self.connection.execute(
                "DELETE FROM descriptor_receipts WHERE policy_digest != ? OR NOT EXISTS ("
                "SELECT 1 FROM live_descriptor_versions live "
                "WHERE live.resource_version_id = descriptor_receipts.resource_version_id)",
                (policyDigest,),
            )
            self.connection.execute(
                "DELETE FROM descriptor_content_cache WHERE policy_digest != ?",
                (policyDigest,),
            )
            self.connection.execute(
                "DELETE FROM descriptor_terminal_attempts WHERE policy_digest != ? OR NOT EXISTS ("
                "SELECT 1 FROM live_descriptor_versions live "
                "WHERE live.resource_version_id = descriptor_terminal_attempts.resource_version_id) "
                "OR EXISTS (SELECT 1 FROM descriptor_receipts receipt "
                "WHERE receipt.resource_version_id = descriptor_terminal_attempts.resource_version_id "
                "AND receipt.policy_digest = descriptor_terminal_attempts.policy_digest)",
                (policyDigest,),
            )
            self.connection.execute("DROP TABLE live_descriptor_versions")
            if snapshotPin is not None:
                payload = canonicalJson(snapshotPin)
                self.connection.execute(
                    "INSERT OR REPLACE INTO descriptor_snapshot_pin VALUES (1, ?, ?, ?)",
                    (
                        hashlib.sha256(payload).hexdigest(),
                        payload,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        after = int(self.connection.execute("SELECT count(*) FROM descriptor_receipts").fetchone()[0])
        return before - after

    def loadTerminalAttempts(
        self,
        resources: tuple[CatalogResource, ...],
        policy: DescriptorPolicy,
    ) -> tuple[ResourceDescriptor, ...]:
        """Resume에는 쓰지 않는 현재 resource별 최신 non-success terminal attempt를 복원한다."""
        policyDigest = descriptorPolicyDigest(policy)
        resourceByVersion = {item.resourceVersionId: item for item in resources if item.resourceKind == "HF_FILE"}
        rows = self.connection.execute(
            "SELECT resource_version_id, source_revision, format_kind, descriptor_digest, "
            "payload_digest, payload, completed_at FROM descriptor_terminal_attempts "
            "WHERE policy_digest = ? ORDER BY resource_version_id, completed_at DESC",
            (policyDigest,),
        )
        attempts = []
        seen = set()
        for resourceVersionId, sourceRevision, formatKind, descriptorDigest, payloadDigest, rawPayload, _at in rows:
            resource = resourceByVersion.get(resourceVersionId)
            if resource is None or resourceVersionId in seen:
                continue
            payload = bytes(rawPayload)
            if hashlib.sha256(payload).hexdigest() != payloadDigest:
                raise DescriptorCheckpointIntegrityError("descriptor attempt payload checksum mismatch")
            descriptor = _decode(payload)
            if (
                descriptor.status in _REUSABLE_DESCRIPTOR_STATES
                or descriptor.resourceVersionId != resourceVersionId
                or descriptor.sourceRevision != sourceRevision
                or descriptor.sourceRevision != resource.sourceRevision
                or descriptor.formatKind != formatKind
                or descriptor.formatKind != descriptorFormatKind(resource)
                or descriptor.digest != descriptorDigest
            ):
                raise DescriptorCheckpointIntegrityError("descriptor terminal attempt column mismatch")
            attempts.append(descriptor)
            seen.add(resourceVersionId)
        return tuple(sorted(attempts, key=lambda item: item.resourceVersionId))

    def terminalAttemptCount(self, policy: DescriptorPolicy) -> int:
        """현재 policy의 non-success terminal attempt cardinality를 반환한다."""
        return int(
            self.connection.execute(
                "SELECT count(*) FROM descriptor_terminal_attempts WHERE policy_digest = ?",
                (descriptorPolicyDigest(policy),),
            ).fetchone()[0]
        )

    def receiptCounts(self, policy: DescriptorPolicy) -> tuple[int, int]:
        """현재 policy의 exact receipt와 content-addressed cache cardinality를 반환한다."""
        policyDigest = descriptorPolicyDigest(policy)
        exact = int(
            self.connection.execute(
                "SELECT count(*) FROM descriptor_receipts WHERE policy_digest = ?",
                (policyDigest,),
            ).fetchone()[0]
        )
        content = int(
            self.connection.execute(
                "SELECT count(*) FROM descriptor_content_cache WHERE policy_digest = ?",
                (policyDigest,),
            ).fetchone()[0]
        )
        return exact, content

    def liveExactReceiptCount(
        self,
        resources: tuple[CatalogResource, ...],
        policy: DescriptorPolicy,
    ) -> int:
        """현재 HF catalog version과 exact match하는 성공 receipt 수만 센다."""
        liveVersions = {item.resourceVersionId for item in resources if item.resourceKind == "HF_FILE"}
        policyDigest = descriptorPolicyDigest(policy)
        reusableStates = tuple(sorted(_REUSABLE_DESCRIPTOR_STATES))
        rows = self.connection.execute(
            "SELECT resource_version_id FROM descriptor_receipts WHERE policy_digest = ? "
            "AND json_extract(payload, '$.status') IN (?, ?)",
            (policyDigest, *reusableStates),
        )
        return sum(str(resourceVersionId) in liveVersions for (resourceVersionId,) in rows)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DescriptorCheckpointStore":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
