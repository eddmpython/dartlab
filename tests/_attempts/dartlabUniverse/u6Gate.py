"""Current U5 projection 전체를 GPU transport와 독립 3D GUI 계약으로 검증한다."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import struct
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .canonical import canonicalJson
from .catalog.models import CatalogState
from .catalog.recoveryStore import defaultRecoveryRoot
from .spatial.contracts import SpatialProjection
from .u3C2 import defaultCheckpointPath
from .u3Gate import defaultControlRoot
from .u5Gate import defaultU5ControlRoot, runLiveU5Observed
from .u6Harness import _STATIC_TYPES, _displayObjectLabels
from .u6Transport import EDGE_RECORD, GPU_TILE_MAGIC, NODE_RECORD, UniverseGpuTransport
from .validation.u6 import U6Measurements, validateU6

_DIRECT_ROUTE = Path("landing/src/routes/universe")
_PUBLIC_ENTRY_PATTERN = re.compile(
    r"""(?:href\s*=|goto\s*\(|pushState\s*\(|replaceState\s*\(|["'])[^\r\n]{0,240}(?<![.\w-])/universe(?:[/?"'#)]|$)""",
    re.IGNORECASE,
)


def defaultU6ControlRoot() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".dartlab"))
    return root / "DartLab" / "universe" / "control" / "u6"


def _stage(stage: str, **values) -> None:
    print(json.dumps({"stage": stage, **values}, ensure_ascii=False), file=sys.stderr, flush=True)


def _decodeTile(payload: bytes) -> tuple[dict[str, object], bytes]:
    if payload[:8] != GPU_TILE_MAGIC or len(payload) < 12:
        raise ValueError("U6 GPU tile magic 또는 길이가 잘못됨")
    headerLength = struct.unpack_from("<I", payload, 8)[0]
    headerEnd = 12 + headerLength
    if headerEnd > len(payload):
        raise ValueError("U6 GPU tile header가 payload 경계를 벗어남")
    return json.loads(payload[12:headerEnd]), payload[headerEnd:]


def _publicSurfaceReferenceCount(repoRoot: Path) -> int:
    """승인된 직접 라우트 밖의 공개 진입 링크를 센다."""

    count = 0
    for relative in ("landing/src", "ui/apps", "ui/packages"):
        root = repoRoot / relative
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".svelte", ".ts", ".js", ".html"}:
                continue
            resolved = path.resolve()
            routeRoot = (repoRoot / _DIRECT_ROUTE).resolve()
            if resolved == routeRoot or routeRoot in resolved.parents:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            count += len(_PUBLIC_ENTRY_PATTERN.findall(text))
    return count


def _directRouteConnected(repoRoot: Path) -> bool:
    page = repoRoot / _DIRECT_ROUTE / "+page.svelte"
    load = repoRoot / _DIRECT_ROUTE / "+page.ts"
    if not page.is_file() or not load.is_file():
        return False
    pageText = page.read_text(encoding="utf-8", errors="ignore")
    loadText = load.read_text(encoding="utf-8", errors="ignore")
    return (
        "bootUniverse" in pageText
        and 'content="noindex,nofollow"' in pageText
        and "export const prerender = true" in loadText
        and "export const ssr = false" in loadText
    )


def _writeReport(path: Path, metrics: dict[str, object]) -> bytes:
    payload = canonicalJson(metrics) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return payload


def _auditProjection(
    projection: SpatialProjection,
    catalog: CatalogState,
    *,
    repoRoot: Path,
) -> dict[str, object]:
    """U5가 측정 중인 동일 projection을 GPU transport로 전수 변환한다."""

    transport = UniverseGpuTransport(projection, objectLabels=_displayObjectLabels(catalog))
    manifestPayload = transport.manifestPayload()
    manifest = json.loads(manifestPayload)
    tileCount = len(transport.tileById)
    encodedTileCount = 0
    sourceDigestPassed = 0
    recordDigestPassed = 0
    metadataPassed = 0
    childClosurePassed = 0
    labelCount = 0
    nonemptyLabelCount = 0
    rawLocatorLabelCount = 0
    maxTileBundleBytes = 0
    encodedBytes = 0
    encodeStarted = time.perf_counter()
    allTileIds = set(transport.tileById)
    for index, tileId in enumerate(sorted(allTileIds), start=1):
        payload = transport.encodeTile(tileId)
        header, records = _decodeTile(payload)
        source = transport.tileById[tileId]
        encodedTileCount += 1
        encodedBytes += len(payload)
        maxTileBundleBytes = max(maxTileBundleBytes, len(payload))
        sourceDigestPassed += header.get("sourceContentDigest") == source.envelope.contentDigest
        recordBytesValid = (
            len(records) == int(header["nodeBytes"]) + int(header["edgeBytes"])
            and hashlib.sha256(records).hexdigest() == header.get("recordDigest")
            and int(header["nodeStride"]) == NODE_RECORD.size
            and int(header["edgeStride"]) == EDGE_RECORD.size
        )
        recordDigestPassed += recordBytesValid
        metadata = tuple(header.get("nodeMetadata", ()))
        metadataPassed += len(metadata) == int(header["nodeCount"])
        childClosurePassed += set(header.get("childTileIds", ())) <= allTileIds
        for item in metadata:
            label = str(item.get("label", "")).strip()
            labelCount += 1
            nonemptyLabelCount += bool(label)
            rawLocatorLabelCount += label.startswith("du:v1:") or "/sha256/" in label.casefold()
        if index % 250 == 0 or index == tileCount:
            _stage("u6-live-transport-progress", encodedTileCount=index, tileCount=tileCount)
    encodeAllTilesSeconds = time.perf_counter() - encodeStarted

    root = transport.tileById[manifest["rootTileId"]]
    overviewId = root.envelope.childTileIds[0]
    overview = transport.tileById[overviewId]
    initialIds = {root.envelope.tileId, overviewId, *overview.envelope.childTileIds}
    initialPayloadBytes = sum(len(transport.encodeTile(tileId)) for tileId in initialIds)

    guiRoot = Path(__file__).with_name("gui")
    guiAssets = tuple(sorted(path for path in guiRoot.iterdir() if path.is_file()))
    guiTexts = {path.name: path.read_text(encoding="utf-8") for path in guiAssets}
    guiAssetBytes = sum(path.stat().st_size for path in guiAssets)
    externalAssetReferenceCount = sum(text.count("http://") + text.count("https://") for text in guiTexts.values())
    appSource = guiTexts.get("app.js", "")
    cssSource = guiTexts.get("universe.css", "")
    webGpuSource = guiTexts.get("webgpu-renderer.js", "")
    webGlSource = guiTexts.get("webgl2-renderer.js", "")
    harnessSource = Path(__file__).with_name("u6Harness.py").read_text(encoding="utf-8")
    appSource = guiTexts.get("app.js", "")
    tileCodecSource = guiTexts.get("tile-codec.js", "")
    publicEntryPointCount = _publicSurfaceReferenceCount(repoRoot)
    return {
        "projectionStateId": projection.state.projectionStateId,
        "coordinateMapDigest": projection.state.logicalCoordinateMapDigest,
        "snapshotId": projection.manifest.snapshotId,
        "objectCount": projection.manifest.objectCount,
        "relationCount": projection.manifest.relationCount,
        "persistenceMode": projection.state.persistenceMode,
        "tileCount": tileCount,
        "encodedTileCount": encodedTileCount,
        "tileCoverage": encodedTileCount / tileCount,
        "sourceDigestCoverage": sourceDigestPassed / tileCount,
        "recordDigestCoverage": recordDigestPassed / tileCount,
        "metadataCoverage": metadataPassed / tileCount,
        "childClosureCoverage": childClosurePassed / tileCount,
        "labelCoverage": nonemptyLabelCount / max(1, labelCount),
        "rawLocatorLabelCount": rawLocatorLabelCount,
        "styleFamilyCount": len(transport.styleKeys),
        "manifestBytes": len(manifestPayload),
        "initialPayloadBytes": initialPayloadBytes,
        "maxTileBundleBytes": maxTileBundleBytes,
        "encodeAllTilesSeconds": round(encodeAllTilesSeconds, 6),
        "guiAssetCount": len(guiAssets) if set(guiTexts) == set(_STATIC_TYPES) else 0,
        "guiAssetBytes": guiAssetBytes,
        "webGpuRendererPresent": "navigator.gpu" in webGpuSource and "WebGpuUniverseRenderer" in appSource,
        "webGlFallbackPresent": "WebGlUniverseRenderer" in appSource and "webgl2" in webGlSource.casefold(),
        "pixelProbePresent": "probeFrame" in webGpuSource and "verifyRendererFrame" in appSource,
        "responsiveContractPresent": ("@media (max-width: 720px)" in cssSource and "calc(100% - 24px)" in cssSource),
        "sessionTokenContractPresent": (
            "X-DartLab-Universe-Token" in harnessSource
            and "secrets.compare_digest" in harnessSource
            and "127.0.0.1" in harnessSource
            and "Access-Control-Allow-Private-Network" in harnessSource
            and "loopbackHosts" in appSource
            and "targetAddressSpace" in tileCodecSource
        ),
        "externalAssetReferenceCount": externalAssetReferenceCount,
        "publicSurfaceReferenceCount": publicEntryPointCount,
        "publicRouteConnected": _directRouteConnected(repoRoot),
        "publicButtonConnected": bool(publicEntryPointCount),
        "encodedPayloadBytes": encodedBytes,
    }


def runLiveU6(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
    u3ControlRoot: Path,
    u5ReportPath: Path,
    repoRoot: Path,
):
    started = time.perf_counter()
    _stage("u5-u6-combined-start")
    upstreamPassed, u5, auditResult = runLiveU5Observed(
        checkpointPath=checkpointPath,
        recoveryRoot=recoveryRoot,
        u3ControlRoot=u3ControlRoot,
        projectionObserver=lambda projection, catalog: _auditProjection(
            projection,
            catalog,
            repoRoot=repoRoot,
        ),
    )
    if not isinstance(auditResult, dict):
        raise TypeError("U6 projection observer 결과가 없음")
    _writeReport(u5ReportPath, u5)
    u5Report = u5["report"]
    u5Measurements = u5Report["measurements"]
    measurements = U6Measurements(
        upstreamU5Passed=upstreamPassed,
        u5ProjectionStateId=str(u5Measurements["projectionStateId"]),
        projectionStateId=str(auditResult["projectionStateId"]),
        u5CoordinateMapDigest=str(u5Measurements["coordinateMapDigest"]),
        coordinateMapDigest=str(auditResult["coordinateMapDigest"]),
        u5SnapshotId=str(u5Measurements["snapshotId"]),
        snapshotId=str(auditResult["snapshotId"]),
        u5ObjectCount=int(u5Measurements["objectCount"]),
        objectCount=int(auditResult["objectCount"]),
        u5RelationCount=int(u5Measurements["relationCount"]),
        relationCount=int(auditResult["relationCount"]),
        u5TileCount=int(u5Measurements["tileCount"]),
        persistenceMode=str(auditResult["persistenceMode"]),
        tileCount=int(auditResult["tileCount"]),
        encodedTileCount=int(auditResult["encodedTileCount"]),
        tileCoverage=float(auditResult["tileCoverage"]),
        sourceDigestCoverage=float(auditResult["sourceDigestCoverage"]),
        recordDigestCoverage=float(auditResult["recordDigestCoverage"]),
        metadataCoverage=float(auditResult["metadataCoverage"]),
        childClosureCoverage=float(auditResult["childClosureCoverage"]),
        labelCoverage=float(auditResult["labelCoverage"]),
        rawLocatorLabelCount=int(auditResult["rawLocatorLabelCount"]),
        styleFamilyCount=int(auditResult["styleFamilyCount"]),
        manifestBytes=int(auditResult["manifestBytes"]),
        initialPayloadBytes=int(auditResult["initialPayloadBytes"]),
        maxTileBundleBytes=int(auditResult["maxTileBundleBytes"]),
        encodeAllTilesSeconds=float(auditResult["encodeAllTilesSeconds"]),
        guiAssetCount=int(auditResult["guiAssetCount"]),
        guiAssetBytes=int(auditResult["guiAssetBytes"]),
        webGpuRendererPresent=bool(auditResult["webGpuRendererPresent"]),
        webGlFallbackPresent=bool(auditResult["webGlFallbackPresent"]),
        pixelProbePresent=bool(auditResult["pixelProbePresent"]),
        responsiveContractPresent=bool(auditResult["responsiveContractPresent"]),
        sessionTokenContractPresent=bool(auditResult["sessionTokenContractPresent"]),
        externalAssetReferenceCount=int(auditResult["externalAssetReferenceCount"]),
        publicSurfaceReferenceCount=int(auditResult["publicSurfaceReferenceCount"]),
        publicRouteConnected=bool(auditResult["publicRouteConnected"]),
        publicButtonConnected=bool(auditResult["publicButtonConnected"]),
        persistentArtifactCount=0,
    )
    report = validateU6(measurements)
    metrics = {
        "schemaVersion": "du-u6-gate-live-v1",
        "passed": report.passed,
        "durationSeconds": round(time.perf_counter() - started, 6),
        "runtimeEnvironment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "logicalCpuCount": os.cpu_count(),
            "transportPersistence": "EPHEMERAL",
            "rendererPolicy": "WEBGPU_WITH_WEBGL2_AND_PIXEL_PROBE",
        },
        "u5Digest": str(u5Report["digest"]),
        "encodedPayloadBytes": int(auditResult["encodedPayloadBytes"]),
        "report": asdict(report),
    }
    return report.passed, metrics


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe U6 live GPU transport와 3D GUI gate")
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    parser.add_argument("--u3-control-root", type=Path, default=defaultControlRoot())
    parser.add_argument("--u5-report", type=Path, default=defaultU5ControlRoot() / "latest.json")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path, default=defaultU6ControlRoot() / "latest.json")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    passed, metrics = runLiveU6(
        checkpointPath=args.checkpoint,
        recoveryRoot=args.recovery_root,
        u3ControlRoot=args.u3_control_root,
        u5ReportPath=args.u5_report,
        repoRoot=args.repo_root.resolve(),
    )
    payload = canonicalJson(metrics) + b"\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.report.with_suffix(args.report.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(args.report)
    sys.stdout.buffer.write(payload)
    return 2 if args.strict and not passed else 0


if __name__ == "__main__":
    raise SystemExit(main())
