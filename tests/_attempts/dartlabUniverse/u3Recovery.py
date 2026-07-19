"""Pinned raw DART archive로 손상된 U3 derived authority를 재현하는 전용 빌더."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import io
import os
import re
import subprocess
import sys
import tarfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import MappingProxyType

import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download

from .canonical import canonicalDigest, canonicalJson
from .catalog.compiler import compileCatalog
from .catalog.descriptorCheckpoint import DescriptorCheckpointStore
from .catalog.descriptorCrawler import DescriptorPolicy, ResourceDescriptor
from .catalog.models import CatalogResource, CatalogState
from .catalog.recovery import ResourceRecovery, buildResourceRecovery, validateRecoverySet
from .catalog.recoveryStore import ResourceRecoveryStore, defaultRecoveryRoot
from .census import defaultRepoRoot, runFullCensus
from .u3C2 import defaultCheckpointPath

TRANSFORM_COMMIT = "3cf27ba98a20511e2c8803c0061e6509d06a9f89"
TRANSFORM_PATHS = (
    "src/dartlab/providers/dart/docs/sections/xmlAdapter.py",
    "src/dartlab/providers/dart/openapi/zipCollector.py",
    "src/dartlab/providers/dart/openapi/zipDocsXml.py",
)
RECIPE_VERSION = "du-u3-dart-docs-recovery-v1"
_RECEIPT_RE = re.compile(r"^[0-9]{14}$")


@dataclass(frozen=True, slots=True)
class RecoveryRecipe:
    targetSourceRef: str
    targetPath: str
    targetSourceObjectId: str
    targetSourcePayloadDigest: str
    targetByteSize: int
    targetErrorCode: str
    inputSourceRef: str
    inputPath: str
    inputSourceObjectId: str
    inputSourcePayloadDigest: str
    inputByteSize: int
    stockCode: str
    corpCode: str
    corpName: str
    expectedArchiveMemberCount: int
    expectedArtifactRowCount: int
    expectedNonemptyMixedCount: int
    expectedFirstReceipt: str
    expectedLastReceipt: str


@dataclass(frozen=True, slots=True)
class RebuiltArtifact:
    payload: bytes
    schemaFingerprint: str
    rowCount: int
    rowGroupCount: int
    archiveMemberCount: int
    nonemptyMixedCount: int
    firstReceipt: str
    lastReceipt: str
    transformSourceDigest: str


SAMCHULLY_RECOVERY = RecoveryRecipe(
    targetSourceRef="eddmpython/dartlab-data",
    targetPath="dart/docs/024950.parquet",
    targetSourceObjectId="bf34d862b95469a76ff807717885dd08abdafd76",
    targetSourcePayloadDigest="ef01e197ac634261e711ed8f8a62feb5b5d8556e605937534471f513ce3e77f6",
    targetByteSize=4_777_778,
    targetErrorCode="INVALID_PARQUET_FOOTER",
    inputSourceRef="eddmpython/dartlab-dart-original",
    inputPath="docs/024950.tar",
    inputSourceObjectId="b154fed12616ce56cd423e8593e6006a5b7489b4",
    inputSourcePayloadDigest="16d26ad0c4160a30a0afa203c40a29b8e7f0c59d4db3625bf25daba5a8c81aa2",
    inputByteSize=8_243_200,
    stockCode="024950",
    corpCode="00128607",
    corpName="삼천리자전거",
    expectedArchiveMemberCount=44,
    expectedArtifactRowCount=751,
    expectedNonemptyMixedCount=585,
    expectedFirstReceipt="20160330003535",
    expectedLastReceipt="20260513000393",
)

_REBUILD_SCHEMA = pa.schema(
    [
        ("corp_code", pa.string()),
        ("corp_name", pa.string()),
        ("stock_code", pa.string()),
        ("year", pa.string()),
        ("rcept_date", pa.string()),
        ("rcept_no", pa.string()),
        ("report_type", pa.string()),
        ("section_order", pa.int64()),
        ("section_title", pa.string()),
        ("section_url", pa.string()),
        ("section_content", pa.string()),
        ("section_content_mixed", pa.string()),
        ("atocid", pa.string()),
        ("assocnote", pa.string()),
    ]
)
_RE_DOC_NAME = re.compile(r'<DOCUMENT-NAME\s+ACODE="(\d+)"[^>]*>([^<]+)</DOCUMENT-NAME>')
_REPORT_ACODE_MAP = {
    "11011": ("사업보고서", "12"),
    "11012": ("반기보고서", "06"),
    "11013": ("분기보고서", "03"),
    "11014": ("분기보고서", "09"),
}


def loadPinnedTransformSources(repoRoot: Path) -> MappingProxyType[str, bytes]:
    """현재 working tree가 아니라 exact historical git object byte를 읽는다."""
    sources = {}
    for path in TRANSFORM_PATHS:
        result = subprocess.run(
            ["git", "show", f"{TRANSFORM_COMMIT}:{path}"],
            cwd=repoRoot,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0 or not result.stdout:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"transform source missing: {path}: {detail}")
        sources[path] = result.stdout
    return MappingProxyType(sources)


def _transformSourceDigest(sources: MappingProxyType[str, bytes]) -> str:
    recipeSources = (
        _loadFunctions,
        _extractMetaFromXml,
        _decodeLargestXml,
        _safeArchiveMembers,
        rebuildParquetFromTar,
    )
    recipeDigest = canonicalDigest(
        {
            "schema": str(_REBUILD_SCHEMA),
            "reportAcodeMap": _REPORT_ACODE_MAP,
            "sources": tuple(inspect.getsource(function) for function in recipeSources),
        }
    )
    return canonicalDigest(
        (
            RECIPE_VERSION,
            ("recipeSource", recipeDigest),
            tuple((path, hashlib.sha256(sources[path]).hexdigest()) for path in sorted(sources)),
        )
    )


def _loadFunctions(sources: MappingProxyType[str, bytes]):
    namespaces = {}
    for path in (
        "src/dartlab/providers/dart/openapi/zipDocsXml.py",
        "src/dartlab/providers/dart/docs/sections/xmlAdapter.py",
    ):
        namespace = {"__name__": f"_dartlab_universe_recovery_{Path(path).stem}"}
        exec(compile(sources[path], f"{TRANSFORM_COMMIT}:{path}", "exec"), namespace)
        namespaces[path] = namespace
    zipFunctions = namespaces["src/dartlab/providers/dart/openapi/zipDocsXml.py"]
    xmlFunctions = namespaces["src/dartlab/providers/dart/docs/sections/xmlAdapter.py"]
    return (
        zipFunctions["parseSectionsByTitle"],
        zipFunctions["splitLargeContent"],
        int(zipFunctions["MAX_CELL_BYTES"]),
        xmlFunctions["xmlChunkToMixed"],
    )


def _extractMetaFromXml(xml: str, receiptNo: str) -> tuple[str, str, str]:
    receiptDate = receiptNo[:8] if len(receiptNo) >= 8 and receiptNo[:8].isdigit() else ""
    receiptYear = receiptDate[:4] if receiptDate else ""
    match = _RE_DOC_NAME.search(xml[:2000])
    acode = match.group(1) if match else ""
    kindFiscal = _REPORT_ACODE_MAP.get(acode)
    if not kindFiscal:
        return receiptYear, receiptDate, ""
    kind, fiscalMonth = kindFiscal
    if acode == "11013" and receiptDate and receiptDate[4:6] >= "10":
        fiscalMonth = "09"
    year = str(int(receiptYear) - 1) if kind == "사업보고서" and receiptYear else receiptYear
    reportType = f"{kind} ({year}.{fiscalMonth})" if year else kind
    return year, receiptDate, reportType


def _decodeLargestXml(zipPayload: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(zipPayload)) as archive:
            names = archive.namelist()
            if not names:
                raise ValueError("empty DART document zip")
            largest = max(names, key=lambda name: archive.getinfo(name).file_size)
            content = archive.read(largest)
    except zipfile.BadZipFile as exc:
        raise ValueError("invalid DART document zip") from exc
    for encoding in ("utf-8", "euc-kr", "cp949"):
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


def _safeArchiveMembers(archive: tarfile.TarFile) -> tuple[tarfile.TarInfo, ...]:
    members = []
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or not member.isfile() or path.suffix.lower() != ".zip":
            raise ValueError(f"unsafe or unsupported recovery tar member: {member.name}")
        if not _RECEIPT_RE.fullmatch(path.stem):
            raise ValueError(f"invalid DART receipt member: {member.name}")
        members.append(member)
    if not members:
        raise ValueError("recovery tar has no document zip")
    return tuple(sorted(members, key=lambda item: PurePosixPath(item.name).stem))


def rebuildParquetFromTar(
    rawTar: bytes,
    sources: MappingProxyType[str, bytes],
    recipe: RecoveryRecipe,
    *,
    enforceExpectedAttestation: bool = True,
) -> RebuiltArtifact:
    """Raw tar의 모든 receipt를 historical transform으로 streaming Parquet에 쓴다."""
    parseSections, splitLargeContent, maxCellBytes, xmlChunkToMixed = _loadFunctions(sources)
    sink = pa.BufferOutputStream()
    written = 0
    nonemptyMixed = 0
    receipts = []
    with tarfile.open(fileobj=io.BytesIO(rawTar), mode="r:*") as archive:
        members = _safeArchiveMembers(archive)
        with pq.ParquetWriter(sink, _REBUILD_SCHEMA, compression="snappy", version="1.0") as writer:
            for member in members:
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ValueError(f"unreadable recovery tar member: {member.name}")
                receiptNo = PurePosixPath(member.name).stem
                xml = _decodeLargestXml(extracted.read())
                rows = parseSections(xml)
                if not rows:
                    raise ValueError(f"DART transform produced no rows: {receiptNo}")
                expanded = []
                for row in rows:
                    content = row.get("content", "") or ""
                    if len(content) <= maxCellBytes:
                        expanded.append(row)
                    else:
                        expanded.extend({**row, "content": part} for part in splitLargeContent(content))
                year, receiptDate, reportType = _extractMetaFromXml(xml, receiptNo)
                rawContents = [row.get("content", "") or "" for row in expanded]
                mixedContents = [xmlChunkToMixed(content) for content in rawContents]
                nonemptyMixed += sum(bool(content) for content in mixedContents)
                count = len(expanded)
                table = pa.Table.from_pydict(
                    {
                        "corp_code": [recipe.corpCode] * count,
                        "corp_name": [recipe.corpName] * count,
                        "stock_code": [recipe.stockCode] * count,
                        "year": [year] * count,
                        "rcept_date": [receiptDate] * count,
                        "rcept_no": [receiptNo] * count,
                        "report_type": [reportType] * count,
                        "section_order": list(range(count)),
                        "section_title": [row.get("title", "") or "" for row in expanded],
                        "section_url": [""] * count,
                        "section_content": rawContents,
                        "section_content_mixed": mixedContents,
                        "atocid": [row.get("atocid", "") or "" for row in expanded],
                        "assocnote": [row.get("assocnote", "") or "" for row in expanded],
                    },
                    schema=_REBUILD_SCHEMA,
                )
                writer.write_table(table)
                written += count
                receipts.append(receiptNo)
    payload = sink.getvalue().to_pybytes()
    parquet = pq.ParquetFile(pa.BufferReader(payload))
    readRows = sum(batch.num_rows for batch in parquet.iter_batches(batch_size=8192))
    if readRows != written or parquet.metadata.num_rows != written:
        raise RuntimeError("recovery artifact full read row mismatch")
    artifact = RebuiltArtifact(
        payload=payload,
        schemaFingerprint=canonicalDigest(str(parquet.schema_arrow)),
        rowCount=written,
        rowGroupCount=parquet.metadata.num_row_groups,
        archiveMemberCount=len(receipts),
        nonemptyMixedCount=nonemptyMixed,
        firstReceipt=receipts[0],
        lastReceipt=receipts[-1],
        transformSourceDigest=_transformSourceDigest(sources),
    )
    if enforceExpectedAttestation and (
        artifact.archiveMemberCount != recipe.expectedArchiveMemberCount
        or artifact.rowCount != recipe.expectedArtifactRowCount
        or artifact.nonemptyMixedCount != recipe.expectedNonemptyMixedCount
        or artifact.firstReceipt != recipe.expectedFirstReceipt
        or artifact.lastReceipt != recipe.expectedLastReceipt
    ):
        raise RuntimeError("recovery artifact attestation mismatch")
    return artifact


def _findPinnedResource(
    catalog: CatalogState,
    *,
    sourceRef: str,
    path: str,
    sourceObjectId: str,
    byteSize: int,
) -> CatalogResource:
    matches = tuple(
        resource
        for resource in catalog.resources
        if resource.resourceKind == "HF_FILE"
        and resource.sourceRef == sourceRef
        and dict(resource.locator).get("path") == path
        and dict(resource.locator).get("oid") == sourceObjectId
        and resource.byteSize == byteSize
    )
    if len(matches) != 1:
        raise RuntimeError(f"pinned recovery resource cardinality mismatch: {sourceRef}/{path}")
    return matches[0]


def _downloadPinnedResource(
    resource: CatalogResource,
    *,
    expectedPayloadDigest: str,
    token: str | None,
) -> bytes:
    locator = dict(resource.locator)
    path = hf_hub_download(
        repo_id=resource.sourceRef,
        filename=locator["path"],
        repo_type="dataset",
        revision=resource.sourceRevision,
        token=token,
    )
    payload = Path(path).read_bytes()
    if len(payload) != resource.byteSize or hashlib.sha256(payload).hexdigest() != expectedPayloadDigest:
        raise RuntimeError("pinned recovery input byte mismatch")
    return payload


def _assertTargetFailure(payload: bytes, errorCode: str) -> None:
    if errorCode != "INVALID_PARQUET_FOOTER" or not payload.startswith(b"PAR1") or payload.endswith(b"PAR1"):
        raise RuntimeError("recovery target failure byte shape mismatch")
    try:
        pq.ParquetFile(pa.BufferReader(payload))
    except (OSError, ValueError, pa.ArrowException):
        return
    raise RuntimeError("recovery target unexpectedly became readable")


def buildPinnedRecovery(
    catalog: CatalogState,
    descriptors: tuple[ResourceDescriptor, ...],
    *,
    repoRoot: Path,
    store: ResourceRecoveryStore,
    token: str | None,
    recipe: RecoveryRecipe = SAMCHULLY_RECOVERY,
) -> tuple[ResourceRecovery, RebuiltArtifact]:
    target = _findPinnedResource(
        catalog,
        sourceRef=recipe.targetSourceRef,
        path=recipe.targetPath,
        sourceObjectId=recipe.targetSourceObjectId,
        byteSize=recipe.targetByteSize,
    )
    source = _findPinnedResource(
        catalog,
        sourceRef=recipe.inputSourceRef,
        path=recipe.inputPath,
        sourceObjectId=recipe.inputSourceObjectId,
        byteSize=recipe.inputByteSize,
    )
    descriptorByVersion = {item.resourceVersionId: item for item in descriptors}
    failed = descriptorByVersion.get(target.resourceVersionId)
    if (
        failed is None
        or failed.status not in {"PARSE_ERROR", "DESCRIPTOR_BLOCKED_RANGE"}
        or failed.errorCode != recipe.targetErrorCode
    ):
        raise RuntimeError("target descriptor failure was not reproduced")
    corruptTarget = _downloadPinnedResource(
        target,
        expectedPayloadDigest=recipe.targetSourcePayloadDigest,
        token=token,
    )
    _assertTargetFailure(corruptTarget, recipe.targetErrorCode)
    rawTar = _downloadPinnedResource(
        source,
        expectedPayloadDigest=recipe.inputSourcePayloadDigest,
        token=token,
    )
    sources = loadPinnedTransformSources(repoRoot)
    artifact = rebuildParquetFromTar(rawTar, sources, recipe)
    objectRef = store.cas.putBytes(artifact.payload)
    createdAt = datetime.now(timezone.utc).isoformat()
    recovery = buildResourceRecovery(
        target,
        failed,
        targetPayloadDigest=recipe.targetSourcePayloadDigest,
        inputResources=(("RAW_DART_TAR", source, recipe.inputSourcePayloadDigest),),
        transformRef=f"git:dartlab@{TRANSFORM_COMMIT}+recipe:{RECIPE_VERSION}",
        transformSourceDigest=artifact.transformSourceDigest,
        artifactObjectRef=objectRef,
        artifactByteSize=len(artifact.payload),
        artifactMediaType="application/vnd.apache.parquet",
        artifactSchemaFingerprint=artifact.schemaFingerprint,
        artifactRowCount=artifact.rowCount,
        artifactRowGroupCount=artifact.rowGroupCount,
        artifactMetadata=(
            ("archiveMemberCount", str(artifact.archiveMemberCount)),
            ("corpCode", recipe.corpCode),
            ("corpName", recipe.corpName),
            ("firstReceipt", artifact.firstReceipt),
            ("lastReceipt", artifact.lastReceipt),
            ("nonemptyMixedCount", str(artifact.nonemptyMixedCount)),
            ("recipeVersion", RECIPE_VERSION),
            ("stockCode", recipe.stockCode),
        ),
        createdAt=createdAt,
    )
    report = validateRecoverySet(catalog, descriptors, (recovery,), cas=store.cas)
    if not report.valid:
        raise RuntimeError(f"rebuilt recovery validation failed: {report.issueCodes}")
    recovery = store.put(recovery, catalog, descriptors)
    return recovery, artifact


def runRecoveryBuild(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
) -> tuple[ResourceRecovery, dict[str, object]]:
    repoRoot = defaultRepoRoot()
    load_dotenv(repoRoot / ".env", override=False)
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    started = time.perf_counter()
    census = runFullCensus(repoRoot, token=token, protectExisting=False)
    catalog = compileCatalog(census)
    policy = DescriptorPolicy()
    with DescriptorCheckpointStore(checkpointPath) as checkpoint:
        checkpoint.assertNoActiveLease()
        descriptorsByVersion = {item.resourceVersionId: item for item in checkpoint.load(catalog.resources, policy)}
        for attempt in checkpoint.loadTerminalAttempts(catalog.resources, policy):
            descriptorsByVersion.setdefault(attempt.resourceVersionId, attempt)
    descriptors = tuple(sorted(descriptorsByVersion.values(), key=lambda item: item.resourceVersionId))
    with ResourceRecoveryStore(recoveryRoot) as store:
        recovery, artifact = buildPinnedRecovery(
            catalog,
            descriptors,
            repoRoot=repoRoot,
            store=store,
            token=token,
        )
        receiptCount = store.receiptCount()
    metrics = {
        "schemaVersion": "du-u3-recovery-build-v1",
        "passed": True,
        "durationSeconds": round(time.perf_counter() - started, 6),
        "catalogDigest": catalog.digest,
        "u0SnapshotDigest": census.snapshotDigest,
        "recoveryId": recovery.recoveryId,
        "recoveryDigest": recovery.digest,
        "targetSourceRef": recovery.targetSourceRef,
        "targetSourceRevision": recovery.targetSourceRevision,
        "targetPath": recovery.targetPath,
        "targetSourceObjectId": recovery.targetSourceObjectId,
        "targetErrorCode": recovery.targetErrorCode,
        "artifactObjectRef": recovery.artifactObjectRef,
        "artifactContentDigest": recovery.artifactContentDigest,
        "artifactByteSize": recovery.artifactByteSize,
        "artifactRowCount": artifact.rowCount,
        "artifactRowGroupCount": artifact.rowGroupCount,
        "archiveMemberCount": artifact.archiveMemberCount,
        "nonemptyMixedCount": artifact.nonemptyMixedCount,
        "transformSourceDigest": artifact.transformSourceDigest,
        "storedReceiptCount": receiptCount,
    }
    return recovery, metrics


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe U3 pinned resource recovery builder")
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    _recovery, metrics = runRecoveryBuild(checkpointPath=args.checkpoint, recoveryRoot=args.recovery_root)
    sys.stdout.buffer.write(canonicalJson(metrics) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
