"""Universe U3 recovery receipt의 CAS, lineage, rebind mutation을 검증한다."""

from __future__ import annotations

import io
import tarfile
import zipfile
from dataclasses import replace
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tests._attempts.dartlabUniverse.canonical import canonicalDigest
from tests._attempts.dartlabUniverse.catalog.descriptorCrawler import (
    DESCRIPTOR_SCHEMA_VERSION,
    ResourceDescriptor,
)
from tests._attempts.dartlabUniverse.catalog.models import CatalogCoverage, CatalogResource, CatalogState
from tests._attempts.dartlabUniverse.catalog.recovery import (
    buildResourceRecovery,
    rebindResourceRecovery,
    validateRecoverySet,
)
from tests._attempts.dartlabUniverse.catalog.recoveryStore import (
    ResourceRecoveryStore,
    ResourceRecoveryStoreIntegrityError,
)
from tests._attempts.dartlabUniverse.catalog.snapshot import buildCatalogSnapshot
from tests._attempts.dartlabUniverse.contracts import Visibility
from tests._attempts.dartlabUniverse.controlPlane.cas import ContentAddressedStore
from tests._attempts.dartlabUniverse.u3Recovery import (
    SAMCHULLY_RECOVERY,
    loadPinnedTransformSources,
    rebuildParquetFromTar,
)
from tests._attempts.dartlabUniverse.validation.c2 import validateC2

_OBSERVED_AT = "2026-07-19T00:00:00+00:00"


def _resource(
    name: str,
    *,
    sourceRef: str,
    revision: str,
    path: str,
    oid: str,
    byteSize: int,
    formatKind: str,
) -> CatalogResource:
    return CatalogResource(
        resourceId=f"du:v1:hf-file:{name}",
        resourceVersionId=f"du:v1:hf-file-version:{canonicalDigest((name, revision, oid))}",
        resourceKind="HF_FILE",
        label=path,
        namespace=sourceRef,
        sourceKind="HF_FILE",
        sourceRef=sourceRef,
        sourceRevision=revision,
        locator=(("repo", sourceRef), ("revision", revision), ("path", path), ("oid", oid)),
        contentSelector=(),
        contentDigest=oid,
        mediaType="application/vnd.apache.parquet" if formatKind == "PARQUET" else None,
        schemaFingerprint=None,
        byteSize=byteSize,
        rowCount=None,
        visibility=Visibility.PRIVATE,
        licenseRef=None,
        status="DISCOVERED",
        discoveredAt=_OBSERVED_AT,
        observedAt=_OBSERVED_AT,
        attributes=(("formatKind", formatKind),),
    )


def _catalog(target: CatalogResource, source: CatalogResource) -> CatalogState:
    coverage = CatalogCoverage(
        discoveredCount=2,
        resourceCount=2,
        objectCount=0,
        evidenceCount=0,
        sourcePayloadCopies=0,
        duplicateLogicalIds=0,
        duplicateVersionIds=0,
        missingLocatorCount=0,
        coverageRatio=1.0,
    )
    return CatalogState(
        schemaVersion="fixture",
        censusSnapshotDigest="a" * 64,
        resources=(target, source),
        objects=(),
        evidence=(),
        coverage=coverage,
        digest="b" * 64,
    )


def _failedDescriptor(target: CatalogResource) -> ResourceDescriptor:
    base = ResourceDescriptor(
        descriptorId=canonicalDigest((target.resourceVersionId, "PARQUET", DESCRIPTOR_SCHEMA_VERSION)),
        schemaVersion=DESCRIPTOR_SCHEMA_VERSION,
        resourceVersionId=target.resourceVersionId,
        sourceRevision=target.sourceRevision,
        formatKind="PARQUET",
        status="PARSE_ERROR",
        schemaFingerprint=None,
        rowCount=None,
        rowCountUnavailableReason="INVALID_PARQUET_FOOTER",
        metadata=(("detail", "terminal magic mismatch"),),
        magicHex=None,
        rangeRequestCount=1,
        rangeBytesRead=256 * 1024,
        responseDigest="c" * 64,
        errorCode="INVALID_PARQUET_FOOTER",
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))


def _unsupportedDescriptor(source: CatalogResource) -> ResourceDescriptor:
    base = ResourceDescriptor(
        descriptorId=canonicalDigest((source.resourceVersionId, "UNSUPPORTED", DESCRIPTOR_SCHEMA_VERSION)),
        schemaVersion=DESCRIPTOR_SCHEMA_VERSION,
        resourceVersionId=source.resourceVersionId,
        sourceRevision=source.sourceRevision,
        formatKind="UNSUPPORTED",
        status="UNSUPPORTED_FORMAT",
        schemaFingerprint=None,
        rowCount=None,
        rowCountUnavailableReason="UNSUPPORTED_FORMAT",
        metadata=(
            ("declaredFormatKind", "TAR"),
            ("reason", "NO_SAFE_DESCRIPTOR_PARSER"),
            ("sourceMeaning", "HF_FILE"),
        ),
        magicHex="7573746172",
        rangeRequestCount=1,
        rangeBytesRead=512,
        responseDigest="d" * 64,
        errorCode=None,
        digest="",
    )
    return replace(base, digest=canonicalDigest(base))


def _artifact() -> tuple[bytes, str, int, int]:
    table = pa.table({"year": [2025, 2026], "value": [10.0, 20.0]})
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink, compression="snappy", version="1.0")
    payload = sink.getvalue().to_pybytes()
    parquet = pq.ParquetFile(pa.BufferReader(payload))
    return (
        payload,
        canonicalDigest(str(parquet.schema_arrow)),
        parquet.metadata.num_rows,
        parquet.metadata.num_row_groups,
    )


def _singleReceiptTar() -> bytes:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<DOCUMENT><DOCUMENT-NAME ACODE="11011">annual</DOCUMENT-NAME><BODY>
<TITLE ATOC="Y" ATOCID="1" AASSOCNOTE="D-0-1">Business</TITLE>
<P>Verified source paragraph.</P></BODY></DOCUMENT>"""
    zipBuffer = io.BytesIO()
    with zipfile.ZipFile(zipBuffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("report.xml", xml)
    tarBuffer = io.BytesIO()
    with tarfile.open(fileobj=tarBuffer, mode="w") as archive:
        info = tarfile.TarInfo("20260330000001.zip")
        payload = zipBuffer.getvalue()
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    return tarBuffer.getvalue()


@pytest.fixture
def recoveryFixture(tmp_path):
    target = _resource(
        "target",
        sourceRef="fixture/data",
        revision="1" * 40,
        path="dart/docs/024950.parquet",
        oid="2" * 64,
        byteSize=4_777_778,
        formatKind="PARQUET",
    )
    source = _resource(
        "source",
        sourceRef="fixture/original",
        revision="3" * 40,
        path="docs/024950.tar",
        oid="4" * 64,
        byteSize=8_243_200,
        formatKind="TAR",
    )
    failed = _failedDescriptor(target)
    payload, schemaFingerprint, rowCount, rowGroupCount = _artifact()
    cas = ContentAddressedStore(tmp_path / "cas")
    objectRef = cas.putBytes(payload)
    recovery = buildResourceRecovery(
        target,
        failed,
        targetPayloadDigest="a" * 64,
        inputResources=(("RAW_DART_TAR", source, "b" * 64),),
        transformRef="git:dartlab@3cf27ba98",
        transformSourceDigest="5" * 64,
        artifactObjectRef=objectRef,
        artifactByteSize=len(payload),
        artifactMediaType="application/vnd.apache.parquet",
        artifactSchemaFingerprint=schemaFingerprint,
        artifactRowCount=rowCount,
        artifactRowGroupCount=rowGroupCount,
        artifactMetadata=(("generator", "fixture"),),
        createdAt=_OBSERVED_AT,
    )
    return target, source, failed, cas, recovery


def testRecoveryRequiresExactFailureInputTransformAndFullCasRead(recoveryFixture):
    target, source, failed, cas, recovery = recoveryFixture

    report = validateRecoverySet(_catalog(target, source), (failed,), (recovery,), cas=cas)

    assert report.valid, report.issueCodes
    assert report.acceptedTargetVersionIds == (target.resourceVersionId,)
    assert report.recoverySetDigest == canonicalDigest((recovery.digest,))
    assert report.digest


def testRecoveryRebindsSameCorruptObjectAcrossRepositoryHead(recoveryFixture):
    target, source, failed, cas, recovery = recoveryFixture
    revision = "6" * 40
    current = replace(
        target,
        resourceVersionId=f"du:v1:hf-file-version:{'7' * 64}",
        sourceRevision=revision,
        locator=tuple((key, revision if key == "revision" else value) for key, value in target.locator),
    )
    currentFailure = _failedDescriptor(current)

    rebound = rebindResourceRecovery(recovery, current, currentFailure)
    report = validateRecoverySet(_catalog(current, source), (currentFailure,), (rebound,), cas=cas)

    assert rebound.recoveryId == recovery.recoveryId
    assert rebound.targetResourceVersionId == current.resourceVersionId
    assert rebound.targetDescriptorDigest == currentFailure.digest
    assert report.valid, report.issueCodes


def testRecoveryCompletesC2WithoutRewritingOriginalFailure(recoveryFixture):
    target, source, failed, cas, recovery = recoveryFixture
    descriptors = (failed, _unsupportedDescriptor(source))

    failedC2 = validateC2(_catalog(target, source), descriptors)
    recoveredC2 = validateC2(
        _catalog(target, source),
        descriptors,
        recoveries=(recovery,),
        recoveryCas=cas,
    )
    snapshot = buildCatalogSnapshot(
        _catalog(target, source),
        universeSnapshotId="du:v1:snapshot:" + "e" * 64,
        descriptors=descriptors,
        recoveries=(recovery,),
        capabilityRegistryVersion="capability-v1",
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion="taxonomy-v1",
        createdAt=_OBSERVED_AT,
    )

    assert not failedC2.passed
    assert "DESCRIPTOR_ELIGIBLE_NOT_DESCRIBED" in failedC2.failureCodes
    assert recoveredC2.passed, recoveredC2.failureCodes
    assert recoveredC2.describedEligibleCount == recoveredC2.eligibleCount == 1
    assert recoveredC2.directlyDescribedEligibleCount == 0
    assert recoveredC2.recoveredEligibleCount == recoveredC2.recoveryReceiptCount == 1
    assert recoveredC2.recoverySetDigest == canonicalDigest((recovery.digest,))
    assert dict(recoveredC2.statusCounts)["PARSE_ERROR"] == 1
    assert snapshot.recoverySetDigest == canonicalDigest((recovery.digest,))


def testRecoveryRejectsMissingInputUnverifiedCasAndMetadataMutation(recoveryFixture):
    target, source, failed, cas, recovery = recoveryFixture

    missingInput = validateRecoverySet(
        replace(_catalog(target, source), resources=(target,)),
        (failed,),
        (recovery,),
        cas=cas,
    )
    unverified = validateRecoverySet(_catalog(target, source), (failed,), (recovery,), cas=None)
    mutated = replace(recovery, artifactRowCount=recovery.artifactRowCount + 1, digest="")
    mutated = replace(mutated, digest=canonicalDigest(mutated))
    metadataMismatch = validateRecoverySet(_catalog(target, source), (failed,), (mutated,), cas=cas)
    badTargetDigest = replace(recovery, targetPayloadDigest="short", digest="")
    badTargetDigest = replace(badTargetDigest, digest=canonicalDigest(badTargetDigest))
    badInput = replace(recovery.inputSources[0], payloadDigest="short")
    badInputDigest = replace(recovery, inputSources=(badInput,), digest="")
    badInputDigest = replace(badInputDigest, digest=canonicalDigest(badInputDigest))
    targetPayloadMismatch = validateRecoverySet(_catalog(target, source), (failed,), (badTargetDigest,), cas=cas)
    inputPayloadMismatch = validateRecoverySet(_catalog(target, source), (failed,), (badInputDigest,), cas=cas)

    assert "RECOVERY_INPUT_OBJECT_MISSING" in missingInput.issueCodes
    assert "RECOVERY_ARTIFACT_CAS_UNVERIFIED" in unverified.issueCodes
    assert "RECOVERY_ARTIFACT_METADATA_MISMATCH" in metadataMismatch.issueCodes
    assert "RECOVERY_ID_MISMATCH" in metadataMismatch.issueCodes
    assert "RECOVERY_TARGET_PAYLOAD_DIGEST_INVALID" in targetPayloadMismatch.issueCodes
    assert "RECOVERY_INPUT_PAYLOAD_DIGEST_INVALID" in inputPayloadMismatch.issueCodes


def testRecoveryRefusesRebindToDifferentSourceObject(recoveryFixture):
    target, _source, failed, _cas, recovery = recoveryFixture
    changed = replace(
        target,
        contentDigest="8" * 64,
        locator=tuple((key, "8" * 64 if key == "oid" else value) for key, value in target.locator),
    )

    with pytest.raises(ValueError, match="content subject mismatch"):
        rebindResourceRecovery(recovery, changed, failed)


def testRecoveryStorePersistsAndRebindsReceiptAcrossHead(tmp_path, recoveryFixture):
    target, source, failed, cas, recovery = recoveryFixture
    root = tmp_path / "recovery-control"
    with ResourceRecoveryStore(root, cas=cas) as store:
        stored = store.put(recovery, _catalog(target, source), (failed,))
        assert store.receiptCount() == 1
        later = replace(recovery, createdAt="2026-07-20T00:00:00+00:00", digest="")
        later = replace(later, digest=canonicalDigest(later))
        assert later.recoveryId == recovery.recoveryId
        assert store.put(later, _catalog(target, source), (failed,)) == stored
        assert store.receiptCount() == 1

    revision = "9" * 40
    current = replace(
        target,
        resourceVersionId=f"du:v1:hf-file-version:{'a' * 64}",
        sourceRevision=revision,
        locator=tuple((key, revision if key == "revision" else value) for key, value in target.locator),
    )
    currentFailure = _failedDescriptor(current)
    with ResourceRecoveryStore(root, cas=cas) as store:
        loaded = store.load(_catalog(current, source), (currentFailure,))

    assert len(loaded) == 1
    assert loaded[0].recoveryId == recovery.recoveryId
    assert loaded[0].targetResourceVersionId == current.resourceVersionId
    assert loaded[0].targetDescriptorDigest == currentFailure.digest


def testRecoveryStoreRejectsTamperedReceiptPayload(tmp_path, recoveryFixture):
    target, source, failed, cas, recovery = recoveryFixture
    with ResourceRecoveryStore(tmp_path / "recovery-control", cas=cas) as store:
        store.put(recovery, _catalog(target, source), (failed,))
        with store.connection:
            store.connection.execute(
                "UPDATE recovery_receipts SET payload = ? WHERE recovery_id = ?",
                (b"{}", recovery.recoveryId),
            )
        with pytest.raises(ResourceRecoveryStoreIntegrityError, match="payload digest mismatch"):
            store.load(_catalog(target, source), (failed,))


def testPinnedHistoricalTransformBuildsFullyReadableParquet():
    sources = loadPinnedTransformSources(Path(__file__).resolve().parents[3])
    artifact = rebuildParquetFromTar(
        _singleReceiptTar(),
        sources,
        SAMCHULLY_RECOVERY,
        enforceExpectedAttestation=False,
    )

    parquet = pq.ParquetFile(pa.BufferReader(artifact.payload))
    table = parquet.read()
    assert artifact.rowCount == artifact.rowGroupCount == artifact.archiveMemberCount == 1
    assert artifact.nonemptyMixedCount == 1
    assert artifact.firstReceipt == artifact.lastReceipt == "20260330000001"
    assert table["rcept_no"].to_pylist() == ["20260330000001"]
    assert table["section_content_mixed"].to_pylist() == ["Verified source paragraph."]
