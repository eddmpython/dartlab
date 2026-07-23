"""Universe U3 C2 format descriptor와 range mutation을 검증한다."""

from __future__ import annotations

import hashlib
import json
import struct
import time
from dataclasses import replace
from pathlib import Path

import httpx
import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq
import pytest

from tests._attempts.dartlabUniverse.canonical import canonicalDigest, canonicalJson
from tests._attempts.dartlabUniverse.catalog.descriptorCheckpoint import (
    DescriptorCheckpointIntegrityError,
    DescriptorCheckpointStore,
    _decode,
    _fastCanonicalDigest,
    buildDescriptorSnapshotPin,
)
from tests._attempts.dartlabUniverse.catalog.descriptorCrawler import (
    DESCRIPTOR_SCHEMA_VERSION,
    MIB,
    DescriptorPolicy,
    DescriptorReadError,
    HfPinnedRangeReader,
    HfRangeReaderFactory,
    LocalRangeReader,
    RangeChunk,
    crawlCatalogDescriptors,
    crawlDescriptor,
)
from tests._attempts.dartlabUniverse.catalog.models import CatalogResource
from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.ids import hfFileIds


def _resource(path: str, size: int, oid: str = "a" * 64) -> CatalogResource:
    resourceId, resourceVersionId = hfFileIds("fixture/data", path, "b" * 40, oid)
    return CatalogResource(
        resourceId=resourceId,
        resourceVersionId=resourceVersionId,
        resourceKind="HF_FILE",
        label=path,
        namespace="fixture/data",
        sourceKind="HF_FILE",
        sourceRef="fixture/data",
        sourceRevision="b" * 40,
        locator=(("repo", "fixture/data"), ("revision", "b" * 40), ("path", path), ("oid", oid)),
        contentSelector=(),
        contentDigest=oid,
        mediaType=None,
        schemaFingerprint=None,
        byteSize=size,
        rowCount=None,
        visibility=Visibility.PRIVATE,
        licenseRef=None,
        status="DISCOVERED",
        discoveredAt="2026-07-19T00:00:00Z",
        observedAt="2026-07-19T00:00:00Z",
    )


def _writeFixtures(root: Path) -> dict[str, Path]:
    table = pa.table({"corpCode": ["001", "002", "003"], "assets": [10, 20, 30]})
    paths = {
        "PARQUET": root / "facts.parquet",
        "ARROW": root / "facts.arrow",
        "JSON": root / "facts.json",
        "JSONL": root / "facts.jsonl",
        "CSV": root / "facts.csv",
        "NPZ": root / "facts.npz",
        "MARKDOWN": root / "post.md",
        "YAML": root / "facts.yaml",
        "IMAGE": root / "pixel.png",
    }
    pq.write_table(table, paths["PARQUET"], row_group_size=2)
    with paths["ARROW"].open("wb") as stream:
        with ipc.new_file(stream, table.schema) as writer:
            writer.write_table(table)
    paths["JSON"].write_text(
        json.dumps([{"corpCode": "001", "assets": 10}, {"corpCode": "002", "assets": 20}]), encoding="utf-8"
    )
    paths["JSONL"].write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")
    paths["CSV"].write_text("corpCode,assets\n001,10\n002,20\n", encoding="utf-8")
    np.savez(paths["NPZ"], x=np.arange(6).reshape(3, 2), y=np.arange(3))
    paths["MARKDOWN"].write_text("# 우주\n\n원본 근거 문서\n", encoding="utf-8")
    paths["YAML"].write_text("- corpCode: '001'\n  assets: 10\n- corpCode: '002'\n  assets: 20\n", encoding="utf-8")
    png = (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", 7, 11)
        + b"\x08\x02\x00\x00\x00"
        + b"\x00" * 4
    )
    paths["IMAGE"].write_bytes(png)
    return paths


@pytest.mark.parametrize(
    ("formatKind", "expectedRows"),
    (("PARQUET", 3), ("ARROW", 3), ("JSON", 2), ("JSONL", 2), ("CSV", 2), ("NPZ", 3), ("YAML", 2)),
)
def testStructuredFormatsHaveSchemaAndExactRows(tmp_path: Path, formatKind: str, expectedRows: int):
    path = _writeFixtures(tmp_path)[formatKind]
    descriptor = crawlDescriptor(
        _resource(path.name, path.stat().st_size),
        LocalRangeReader(path),
        formatKind=formatKind,
    )

    assert descriptor.status == "DESCRIBED", descriptor
    assert descriptor.schemaFingerprint
    assert descriptor.rowCount == expectedRows
    assert descriptor.rowCountUnavailableReason is None
    assert descriptor.rangeRequestCount >= 1
    assert descriptor.rangeBytesRead > 0
    assert descriptor.responseDigest


@pytest.mark.parametrize("formatKind", ("MARKDOWN", "IMAGE"))
def testDocumentAndImageHaveSchemaWithExplicitNoRowReason(tmp_path: Path, formatKind: str):
    path = _writeFixtures(tmp_path)[formatKind]
    descriptor = crawlDescriptor(
        _resource(path.name, path.stat().st_size),
        LocalRangeReader(path),
        formatKind=formatKind,
    )

    assert descriptor.status == "DESCRIBED"
    assert descriptor.schemaFingerprint
    assert descriptor.rowCount is None
    assert descriptor.rowCountUnavailableReason in {"NON_TABULAR_DOCUMENT", "NON_TABULAR_MEDIA"}


def testLargeParquetUsesRangeInsteadOfWholePayload(tmp_path: Path):
    path = tmp_path / "wide.parquet"
    pq.write_table(pa.table({"value": list(range(100_000))}), path, row_group_size=1000)
    descriptor = crawlDescriptor(_resource(path.name, path.stat().st_size), LocalRangeReader(path))

    assert descriptor.status == "DESCRIBED"
    assert descriptor.rowCount == 100_000
    assert descriptor.rangeBytesRead < path.stat().st_size
    assert descriptor.rangeRequestCount == 1
    assert dict(descriptor.metadata)["descriptorRead"] == "footer-range"


def testParquetFooterLengthMutationIsRejectedBeforeSchemaTrust(tmp_path: Path):
    path = _writeFixtures(tmp_path)["PARQUET"]
    payload = bytearray(path.read_bytes())
    payload[-8:-4] = len(payload).to_bytes(4, "little")
    path.write_bytes(payload)

    descriptor = crawlDescriptor(_resource(path.name, path.stat().st_size), LocalRangeReader(path))

    assert descriptor.status == "PARSE_ERROR"
    assert descriptor.errorCode == "INVALID_PARQUET_FOOTER"


def testWebpLossyHeaderProvidesDimensionsWithoutPixelDecode(tmp_path: Path):
    path = tmp_path / "sample.webp"
    payload = bytearray(30)
    payload[0:4] = b"RIFF"
    payload[4:8] = (22).to_bytes(4, "little")
    payload[8:12] = b"WEBP"
    payload[12:16] = b"VP8 "
    payload[16:20] = (10).to_bytes(4, "little")
    payload[23:26] = b"\x9d\x01\x2a"
    payload[26:28] = (640).to_bytes(2, "little")
    payload[28:30] = (360).to_bytes(2, "little")
    path.write_bytes(payload)

    descriptor = crawlDescriptor(_resource(path.name, len(payload)), LocalRangeReader(path))

    assert descriptor.status == "DESCRIBED"
    assert dict(descriptor.metadata)["format"] == "WEBP"
    assert "dimensionStatus" not in dict(descriptor.metadata)


class _SyntheticReader:
    def __init__(self, size: int, *, rangeUnsupported: bool = False):
        self.size = size
        self.rangeUnsupported = rangeUnsupported

    def read(self, start: int, endExclusive: int) -> RangeChunk:
        if self.rangeUnsupported and (start != 0 or endExclusive != self.size):
            raise DescriptorReadError("RANGE_UNSUPPORTED")
        payload = b" " * (endExclusive - start)
        return RangeChunk(start, endExclusive, payload, "f" * 64)


def testLargeWholeObjectFormatIsBlockedWithoutAllocation():
    reader = _SyntheticReader(33 * MIB)
    descriptor = crawlDescriptor(_resource("large.json", reader.size), reader, formatKind="JSON")

    assert descriptor.status == "DESCRIPTOR_BLOCKED_RANGE"
    assert descriptor.errorCode == "DESCRIPTOR_BLOCKED_RANGE"
    assert descriptor.rangeBytesRead == 0


def testUnsupportedBinaryRecordsMagicAndMeaning():
    reader = _SyntheticReader(64)
    descriptor = crawlDescriptor(_resource("opaque.bin", reader.size), reader, formatKind="BINARY")

    assert descriptor.status == "UNSUPPORTED_FORMAT"
    assert descriptor.magicHex == (b" " * 32).hex()
    assert dict(descriptor.metadata)["reason"] == "NO_SAFE_DESCRIPTOR_PARSER"
    assert dict(descriptor.metadata)["sourceMeaning"] == "HF_FILE"


def testParserFailureAndAccessDeniedAreTerminal():
    malformed = _SyntheticReader(4)
    parsed = crawlDescriptor(_resource("bad.json", 4), malformed, formatKind="JSON")

    class DeniedReader(_SyntheticReader):
        def read(self, start: int, endExclusive: int) -> RangeChunk:
            raise DescriptorReadError("ACCESS_DENIED")

    denied = crawlDescriptor(_resource("private.parquet", 100), DeniedReader(100), formatKind="PARQUET")
    assert parsed.status == "PARSE_ERROR"
    assert denied.status == "ACCESS_DENIED"


def testDescriptorDigestChangesWithSourceRevision(tmp_path: Path):
    path = _writeFixtures(tmp_path)["JSON"]
    resource = _resource(path.name, path.stat().st_size)
    first = crawlDescriptor(resource, LocalRangeReader(path), formatKind="JSON")
    changed = replace(resource, sourceRevision="c" * 40)
    second = crawlDescriptor(changed, LocalRangeReader(path), formatKind="JSON")

    assert first.digest != second.digest


def testCheckpointResumeDoesNotReprocessCompletedDescriptors(tmp_path: Path):
    firstPath = tmp_path / "first.json"
    secondPath = tmp_path / "second.json"
    firstPath.write_text('[{"a":1}]', encoding="utf-8")
    secondPath.write_text('[{"b":2}]', encoding="utf-8")
    resources = (
        _resource(firstPath.name, firstPath.stat().st_size, "1" * 64),
        _resource(secondPath.name, secondPath.stat().st_size, "2" * 64),
    )
    paths = {firstPath.name: firstPath, secondPath.name: secondPath}
    calls = []
    policy = DescriptorPolicy()

    def readerFactory(resource):
        path = paths[dict(resource.locator)["path"]]
        calls.append(path.name)
        return LocalRangeReader(path)

    with DescriptorCheckpointStore(tmp_path / "control" / "descriptor.sqlite") as checkpoint:
        first = crawlCatalogDescriptors(
            resources,
            readerFactory,
            policy=policy,
            onDescriptor=lambda item: checkpoint.put(item, policy),
        )
        resumed = checkpoint.load(resources, policy)
        second = crawlCatalogDescriptors(
            resources,
            lambda _resource: pytest.fail("completed descriptor가 재처리됨"),
            policy=policy,
            resumeDescriptors=resumed,
        )

    assert len(calls) == 2
    assert first == second


def testCheckpointRebindsUnchangedContentAcrossPinnedRevisions(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size, "1" * 64)
    descriptor = crawlDescriptor(resource, LocalRangeReader(path))
    nextRevision = "c" * 40
    resourceId, resourceVersionId = hfFileIds(
        resource.sourceRef,
        path.name,
        nextRevision,
        dict(resource.locator)["oid"],
    )
    reboundResource = replace(
        resource,
        resourceId=resourceId,
        resourceVersionId=resourceVersionId,
        sourceRevision=nextRevision,
        locator=tuple((key, nextRevision if key == "revision" else value) for key, value in resource.locator),
    )
    policy = DescriptorPolicy()

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(
            descriptor,
            policy,
            resourcesByVersion={resource.resourceVersionId: resource},
        )
        resumed = checkpoint.load((reboundResource,), policy)
        recrawled = crawlCatalogDescriptors(
            (reboundResource,),
            lambda _resource: pytest.fail("동일 content descriptor가 재처리됨"),
            policy=policy,
            resumeDescriptors=resumed,
        )

        assert checkpoint.lastLoadReusedCount == 1
        assert checkpoint.receiptCounts(policy) == (1, 1)
        assert checkpoint.liveExactReceiptCount((reboundResource,), policy) == 0

    expectedBase = replace(
        descriptor,
        descriptorId=canonicalDigest(
            (reboundResource.resourceVersionId, descriptor.formatKind, DESCRIPTOR_SCHEMA_VERSION)
        ),
        resourceVersionId=reboundResource.resourceVersionId,
        sourceRevision=reboundResource.sourceRevision,
        rangeRequestCount=0,
        rangeBytesRead=0,
        digest="",
    )
    expected = replace(expectedBase, digest=canonicalDigest(expectedBase))
    assert recrawled == resumed
    assert resumed == (expected,)
    assert resumed[0].resourceVersionId == reboundResource.resourceVersionId
    assert resumed[0].sourceRevision == nextRevision
    assert resumed[0].descriptorId != descriptor.descriptorId
    assert resumed[0].schemaFingerprint == descriptor.schemaFingerprint
    assert resumed[0].rowCount == descriptor.rowCount
    assert resumed[0].rangeRequestCount == 0
    assert resumed[0].rangeBytesRead == 0


def testCheckpointFastCanonicalDigestMatchesCanonicalContract():
    value = {
        "integer": 42,
        "korean": "지식우주",
        "metadata": (("escaped", '따옴표"와 역슬래시\\'), ("line", "첫째\n둘째")),
        "none": None,
    }

    assert _fastCanonicalDigest(value) == canonicalDigest(value)


@pytest.mark.parametrize("mutation", ("unknown_field", "wrong_type", "missing_field"))
def testCheckpointStrictWireDecodeRejectsSchemaMutation(tmp_path: Path, mutation: str):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size)
    descriptor = crawlDescriptor(resource, LocalRangeReader(path))
    value = json.loads(canonicalJson(descriptor))
    if mutation == "unknown_field":
        value["unexpected"] = "forbidden"
    elif mutation == "wrong_type":
        value["rangeRequestCount"] = "0"
    else:
        del value["status"]
    value["digest"] = ""
    value["digest"] = canonicalDigest(value)
    payload = canonicalJson(value)

    with pytest.raises(DescriptorCheckpointIntegrityError, match="decode failure"):
        _decode(payload)


def testCheckpointRetriesAccessAndTransportDependentTerminalStates(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size, "1" * 64)
    policy = DescriptorPolicy()

    class DeniedReader:
        size = resource.byteSize or 0

        def read(self, _start: int, _endExclusive: int):
            raise DescriptorReadError("ACCESS_DENIED")

    denied = crawlDescriptor(resource, DeniedReader(), policy=policy)
    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(
            denied,
            policy,
            resourcesByVersion={resource.resourceVersionId: resource},
        )
        assert checkpoint.receiptCounts(policy) == (0, 0)
        assert checkpoint.load((resource,), policy) == ()
        assert checkpoint.loadTerminalAttempts((resource,), policy) == (denied,)
        assert checkpoint.terminalAttemptCount(policy) == 1
        recrawled = crawlCatalogDescriptors(
            (resource,),
            lambda _resource: LocalRangeReader(path),
            policy=policy,
            resumeDescriptors=checkpoint.load((resource,), policy),
        )
        checkpoint.put(
            recrawled[0],
            policy,
            resourcesByVersion={resource.resourceVersionId: resource},
        )
        assert checkpoint.receiptCounts(policy) == (1, 1)
        assert checkpoint.load((resource,), policy) == recrawled
        assert checkpoint.liveExactReceiptCount((resource,), policy) == 1
        checkpoint.pruneObsolete((resource,), policy)
        assert checkpoint.terminalAttemptCount(policy) == 0

    assert recrawled[0].status == "DESCRIBED"


def testCheckpointRejectsCorruptContentReuseReceipt(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size, "1" * 64)
    descriptor = crawlDescriptor(resource, LocalRangeReader(path))
    nextRevision = "c" * 40
    _resourceId, resourceVersionId = hfFileIds(
        resource.sourceRef,
        path.name,
        nextRevision,
        dict(resource.locator)["oid"],
    )
    reboundResource = replace(
        resource,
        resourceVersionId=resourceVersionId,
        sourceRevision=nextRevision,
        locator=tuple((key, nextRevision if key == "revision" else value) for key, value in resource.locator),
    )
    policy = DescriptorPolicy()

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(
            descriptor,
            policy,
            resourcesByVersion={resource.resourceVersionId: resource},
        )
        with checkpoint.connection:
            checkpoint.connection.execute(
                "UPDATE descriptor_content_cache SET payload_digest = ?",
                ("f" * 64,),
            )
        with pytest.raises(DescriptorCheckpointIntegrityError, match="checksum"):
            checkpoint.load((reboundResource,), policy)


def testCheckpointImmutableConflictIsRejected(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size)
    policy = DescriptorPolicy()
    descriptor = crawlDescriptor(resource, LocalRangeReader(path), policy=policy)
    changedBase = replace(descriptor, rowCount=99, digest="")
    changed = replace(changedBase, digest=canonicalDigest(changedBase))

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(descriptor, policy)
        with pytest.raises(DescriptorCheckpointIntegrityError, match="immutable"):
            checkpoint.put(changed, policy)


def testCheckpointMigratesLegacyRetryableReceiptToSuccess(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size)
    policy = DescriptorPolicy()
    described = crawlDescriptor(resource, LocalRangeReader(path), policy=policy)
    deniedBase = replace(
        described,
        status="ACCESS_DENIED",
        schemaFingerprint=None,
        rowCount=None,
        rowCountUnavailableReason="ACCESS_DENIED",
        errorCode="ACCESS_DENIED",
        digest="",
    )
    denied = replace(deniedBase, digest=canonicalDigest(deniedBase))
    deniedPayload = canonicalJson(denied)

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(described, policy)
        with checkpoint.connection:
            checkpoint.connection.execute(
                "UPDATE descriptor_receipts SET descriptor_digest = ?, payload_digest = ?, payload = ?",
                (denied.digest, hashlib.sha256(deniedPayload).hexdigest(), deniedPayload),
            )
        checkpoint.put(described, policy)
        assert checkpoint.load((resource,), policy) == (described,)


def testCheckpointLoadRejectsReceiptColumnMutation(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size)
    policy = DescriptorPolicy()
    descriptor = crawlDescriptor(resource, LocalRangeReader(path), policy=policy)

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(descriptor, policy)
        with checkpoint.connection:
            checkpoint.connection.execute(
                "UPDATE descriptor_receipts SET descriptor_digest = ?",
                ("f" * 64,),
            )
        with pytest.raises(DescriptorCheckpointIntegrityError, match="column mismatch"):
            checkpoint.load((resource,), policy)


def testCheckpointPrunesOldPolicyOnlyAfterNoActiveLease(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size)
    descriptor = crawlDescriptor(resource, LocalRangeReader(path))
    currentPolicy = DescriptorPolicy()
    oldPolicy = DescriptorPolicy(maxWholeObjectBytes=1024)

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(descriptor, currentPolicy)
        checkpoint.put(descriptor, oldPolicy)
        owner = checkpoint.acquireLease()
        with pytest.raises(RuntimeError, match="진행 중"):
            checkpoint.pruneObsolete((resource,), currentPolicy)
        checkpoint.releaseLease(owner)
        assert checkpoint.pruneObsolete((resource,), currentPolicy) == 1
        assert checkpoint.load((resource,), currentPolicy) == (descriptor,)


def testCheckpointAtomicallyPinsPassedC2SnapshotWithPrunedReceipts(tmp_path: Path):
    path = tmp_path / "facts.json"
    path.write_text('[{"a":1}]', encoding="utf-8")
    resource = _resource(path.name, path.stat().st_size)
    policy = DescriptorPolicy()
    descriptor = crawlDescriptor(resource, LocalRangeReader(path), policy=policy)
    pin = buildDescriptorSnapshotPin(
        observedAtUtc="2026-07-22T00:00:00+00:00",
        sourceRevisions=(("fixture/data", "b" * 40),),
        hfRepoFileCounts=(("fixture/data", 1),),
        hfCandidateCount=1,
        catalogDigest="c" * 64,
        u0SnapshotDigest="d" * 64,
        policy=policy,
        c2Digest="e" * 64,
    )

    with DescriptorCheckpointStore(tmp_path / "descriptor.sqlite") as checkpoint:
        checkpoint.put(descriptor, policy)
        owner = checkpoint.acquireLease()
        try:
            checkpoint.pruneObsolete(
                (resource,),
                policy,
                snapshotPin=pin,
                leaseOwner=owner,
            )
        finally:
            checkpoint.releaseLease(owner)

        assert checkpoint.loadSnapshotPin() == pin
        with checkpoint.connection:
            checkpoint.connection.execute(
                "UPDATE descriptor_snapshot_pin SET payload_digest = ?",
                ("f" * 64,),
            )
        with pytest.raises(DescriptorCheckpointIntegrityError, match="checksum"):
            checkpoint.loadSnapshotPin()


def testCheckpointLeasePreventsConcurrentCrawlAndHeartbeatKeepsOwnership(tmp_path: Path):
    path = tmp_path / "descriptor.sqlite"
    with (
        DescriptorCheckpointStore(path) as first,
        DescriptorCheckpointStore(path) as second,
    ):
        owner = first.acquireLease(ttlSeconds=0.2)
        heartbeat = first.startLeaseHeartbeat(owner, ttlSeconds=0.2, intervalSeconds=0.05)
        time.sleep(0.3)
        with pytest.raises(RuntimeError, match="진행 중"):
            second.assertNoActiveLease()
        with pytest.raises(RuntimeError, match="이미 활성"):
            second.acquireLease(ttlSeconds=0.2)
        heartbeat.close()
        first.releaseLease(owner)
        secondOwner = second.acquireLease(ttlSeconds=0.2)
        second.releaseLease(secondOwner)
        second.assertNoActiveLease()


def testHfRangeReaderRetriesRateLimitBeforeTerminalReceipt():
    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get(self, _url, *, headers):
            self.calls += 1
            if self.calls == 1:
                return httpx.Response(429, headers={"retry-after": "0"})
            return httpx.Response(
                206,
                headers={"content-range": "bytes 0-3/4"},
                content=b"data",
            )

    client = FakeClient()
    policy = DescriptorPolicy(maxTransientAttempts=2, maxRetryDelaySeconds=0, maxRequestsPerSecond=1000)
    reader = HfPinnedRangeReader(
        repoId="fixture/data",
        revision="a" * 40,
        path="facts.json",
        size=4,
        token=None,
        client=client,
        policy=policy,
    )

    chunk = reader.read(0, 4)

    assert chunk.payload == b"data"
    assert client.calls == 2


def testHfFactoryRejectsRepoOutsideConfiguredAuthority():
    resource = _resource("facts.json", 4)
    with HfRangeReaderFactory(token=None, allowedRepoIds=frozenset({"fixture/other"})) as factory:
        with pytest.raises(DescriptorReadError, match="REPOSITORY_NOT_ALLOWLISTED"):
            factory(resource)


def testHfReaderRejectsMutableRevisionAndUnsafePath():
    with pytest.raises(ValueError, match="exact commit"):
        HfPinnedRangeReader(
            repoId="fixture/data",
            revision="main",
            path="facts.json",
            size=4,
            token=None,
        )
    with pytest.raises(ValueError, match="안전한 POSIX"):
        HfPinnedRangeReader(
            repoId="fixture/data",
            revision="a" * 40,
            path="../secret",
            size=4,
            token=None,
        )
