"""Current Universe graph와 two-snapshot fixture를 한 process에서 검증하는 U5 gate."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import psutil

from .canonical import canonicalJson
from .catalog.models import CatalogState
from .catalog.recoveryStore import defaultRecoveryRoot
from .contracts import Visibility
from .spatial.contracts import ProjectionRequest, SpatialProjection
from .spatial.projectionState import clearSpatialRuntimeCaches, compileSpatialProjection
from .spatial.stability import evaluateProjectionStability
from .spatialTestSupport import spatialFixture, spatialRequest
from .u3C2 import defaultCheckpointPath
from .u3Gate import buildLiveU3Artifacts, defaultControlRoot
from .validation.slo import benchmarkU3Runtime
from .validation.u5 import U5Measurements, validateU5


def defaultU5ControlRoot() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".dartlab"))
    return root / "DartLab" / "universe" / "control" / "u5"


def _fullRequest(snapshotId: str) -> ProjectionRequest:
    return ProjectionRequest(
        snapshotId=snapshotId,
        projectionVersion="du-projection-live-v1",
        objectScope=(),
        relationScope=(),
        validAt="9999-12-30T00:00:00Z",
        knownAt="9999-12-30T00:00:00Z",
        activeLens="overview",
        allowedVisibility=(Visibility.PUBLIC, Visibility.LOCAL, Visibility.PRIVATE, Visibility.RESTRICTED),
        seed=20260722,
    )


def _stage(stage: str, **values) -> None:
    print(json.dumps({"stage": stage, **values}, ensure_ascii=False), file=sys.stderr, flush=True)


def _loadSample() -> tuple[float, int]:
    totalCpu = psutil.cpu_percent(interval=1.0)
    return totalCpu, psutil.virtual_memory().available


def _waitForMeasurementWindow(*, timeoutSeconds: float = 3600.0) -> None:
    started = time.perf_counter()
    stable = 0
    while time.perf_counter() - started < timeoutSeconds:
        totalCpu, available = _loadSample()
        if totalCpu <= 25.0 and available >= 6 * 1024 * 1024 * 1024:
            stable += 1
            if stable >= 3:
                return
        else:
            stable = 0
        if int(time.perf_counter() - started) % 30 < 2:
            _stage(
                "measurement-window-wait",
                totalCpuPercent=round(totalCpu, 3),
                availableMemoryBytes=available,
            )
    raise TimeoutError("reference measurement window를 3600초 안에 확보하지 못함")


def _measureProjection(
    *,
    label: str,
    process: psutil.Process,
    catalog,
    snapshot,
    relations,
    request: ProjectionRequest,
    statements=(),
    priorState=None,
    maxAttempts: int = 3,
):
    last = None
    for attempt in range(1, maxAttempts + 1):
        _waitForMeasurementWindow()
        clearSpatialRuntimeCaches()
        rssBefore = process.memory_info().rss
        cpuStarted = time.process_time()
        wallStarted = time.perf_counter()
        projection = compileSpatialProjection(
            catalog,
            snapshot,
            relations,
            request=request,
            statements=statements,
            priorState=priorState,
        )
        wallSeconds = time.perf_counter() - wallStarted
        cpuSeconds = time.process_time() - cpuStarted
        contentionRatio = wallSeconds / max(cpuSeconds, 0.001)
        rssBytes = max(rssBefore, process.memory_info().rss)
        _stage(
            f"{label}-measured",
            attempt=attempt,
            wallSeconds=round(wallSeconds, 6),
            cpuSeconds=round(cpuSeconds, 6),
            contentionRatio=round(contentionRatio, 6),
            rssBytes=rssBytes,
        )
        last = (projection, wallSeconds, cpuSeconds, contentionRatio, rssBytes, attempt)
        if contentionRatio <= 1.15:
            return last
        del projection
        gc.collect()
    return last


def _refreshU3Slo(artifacts, process: psutil.Process):
    report = artifacts.slo
    for attempt in range(1, 4):
        if report.passed:
            return report, attempt - 1
        if any(not code.endswith("SLO_EXCEEDED") for code in report.failureCodes):
            return report, attempt - 1
        _waitForMeasurementWindow()
        report = benchmarkU3Runtime(artifacts.catalog, artifacts.relations, artifacts.snapshot)
        _stage(
            "u3-slo-remeasured",
            attempt=attempt,
            passed=report.passed,
            failureCodes=report.failureCodes,
            snapshotReplayMs=report.snapshotReplayMs,
        )
    return report, 3


def _runLiveU5(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
    u3ControlRoot: Path,
    projectionObserver: Callable[[SpatialProjection, CatalogState], object] | None = None,
):
    """현재 full replay와 1% two-snapshot 전이를 runtime-only로 실행한다."""
    started = time.perf_counter()
    process = psutil.Process(os.getpid())
    _stage("u3-build-start")
    artifacts = buildLiveU3Artifacts(
        checkpointPath=checkpointPath,
        recoveryRoot=recoveryRoot,
        controlRoot=u3ControlRoot,
    )
    activeU3Slo, u3SloRetryCount = _refreshU3Slo(artifacts, process)
    _stage(
        "u3-build-complete",
        reportPassed=artifacts.report.passed,
        reportFailureCodes=artifacts.report.failureCodes,
        sloPassed=activeU3Slo.passed,
        sloFailureCodes=activeU3Slo.failureCodes,
    )
    catalog = artifacts.catalog
    snapshot = artifacts.snapshot
    relations = artifacts.relations
    upstreamPassed = artifacts.report.passed and activeU3Slo.passed
    upstreamFailureCodes = tuple((*artifacts.report.failureCodes, *activeU3Slo.failureCodes))
    u3Digest = artifacts.report.digest
    del artifacts
    gc.collect()
    request = _fullRequest(snapshot.snapshotId)
    projection, fullSeconds, fullCpuSeconds, fullContentionRatio, fullProjectionRss, fullAttemptCount = (
        _measureProjection(
            label="full-projection",
            process=process,
            catalog=catalog,
            snapshot=snapshot,
            relations=relations,
            request=request,
        )
    )
    coordinateDigest = projection.state.logicalCoordinateMapDigest
    projectionStateId = projection.state.projectionStateId
    projectionDigest = projection.digest
    persistenceMode = projection.state.persistenceMode
    objectCount = len(projection.state.coordinates)
    relationCount = projection.manifest.relationCount
    communityCount = len(projection.state.communities)
    tileCount = len(projection.tiles)
    meaning = projection.meaningReport
    zZeroRatio = sum(item.positionQ[2] == 0 for item in projection.state.coordinates) / objectCount
    xyzValid = sum(
        len(item.positionQ) == 3 and all(isinstance(value, int) for value in item.positionQ)
        for item in projection.state.coordinates
    )
    maxTileBytes = max(item.envelope.byteSize for item in projection.tiles)
    maxTileNodeCount = max(item.envelope.nodeCount for item in projection.tiles)
    maxTileEdgeCount = max(item.envelope.edgeCount for item in projection.tiles)
    runtimeTileCount = sum(item.envelope.contentRef.startswith("runtime://") for item in projection.tiles)
    objectDrillCount = sum(item.targetKind == "OBJECT" for item in projection.drillPaths)
    observerResult = projectionObserver(projection, catalog) if projectionObserver is not None else None
    del projection
    gc.collect()
    replay, replaySeconds, replayCpuSeconds, replayContentionRatio, _replayRss, replayAttemptCount = _measureProjection(
        label="projection-replay",
        process=process,
        catalog=catalog,
        snapshot=snapshot,
        relations=relations,
        request=request,
    )
    replayCoordinateDigest = replay.state.logicalCoordinateMapDigest
    del replay
    gc.collect()

    fixture = spatialFixture()
    currentCount = len(fixture.catalog.objects)
    deltaCount = max(1, round(currentCount * 0.01))
    priorRequest = spatialRequest(fixture, count=currentCount - deltaCount)
    prior = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=priorRequest,
        statements=fixture.statements,
    )
    selected = priorRequest.objectScope[0]
    currentRequest = spatialRequest(
        fixture,
        count=currentCount,
        stabilityBaseProjectionId=prior.state.projectionStateId,
        selectedObjectIds=(selected,),
    )
    incrementalRssBefore = process.memory_info().rss
    (
        current,
        incrementalSeconds,
        incrementalCpuSeconds,
        incrementalContentionRatio,
        _incrementalRss,
        incrementalAttempts,
    ) = _measureProjection(
        label="incremental-one-percent",
        process=process,
        catalog=fixture.catalog,
        snapshot=fixture.snapshot,
        relations=fixture.graph.relations,
        request=currentRequest,
        statements=fixture.statements,
        priorState=prior.state,
    )
    incrementalRssGrowth = max(0, process.memory_info().rss - incrementalRssBefore)
    stability = evaluateProjectionStability(
        prior.state,
        current.state,
        selectedObjectIds=(selected,),
    )
    measurements = U5Measurements(
        upstreamPassed=upstreamPassed,
        snapshotId=snapshot.snapshotId,
        projectionStateId=projectionStateId,
        projectionDigest=projectionDigest,
        coordinateMapDigest=coordinateDigest,
        replayCoordinateMapDigest=replayCoordinateDigest,
        persistenceMode=persistenceMode,
        objectCount=objectCount,
        relationCount=relationCount,
        communityCount=communityCount,
        tileCount=tileCount,
        fullProjectionSeconds=round(fullSeconds, 6),
        replaySeconds=round(replaySeconds, 6),
        incrementalOnePercentSeconds=round(incrementalSeconds, 6),
        incrementalFixtureObjectCount=currentCount,
        processPeakRssBytes=fullProjectionRss,
        incrementalRssGrowthBytes=incrementalRssGrowth,
        coordinateDeterminism=stability.coordinateDeterminism if coordinateDigest == replayCoordinateDigest else 0.0,
        normalizedDisplacementP95=stability.normalizedDisplacementP95,
        clusterContinuity=stability.clusterContinuity,
        selectedObjectLossCount=stability.selectedObjectLossCount,
        meaningPreservation=meaning.meaningPreservation,
        conservationAssertionCount=meaning.assertionCount,
        passedConservationAssertionCount=meaning.passedAssertionCount,
        zZeroRatio=round(zZeroRatio, 9),
        xyzValidRatio=xyzValid / objectCount,
        maxTileBytes=maxTileBytes,
        maxTileNodeCount=maxTileNodeCount,
        maxTileEdgeCount=maxTileEdgeCount,
        runtimeTileRefRatio=runtimeTileCount / tileCount,
        objectDrillPathRatio=objectDrillCount / objectCount,
        persistentArtifactCount=0,
    )
    report = validateU5(measurements)
    metrics = {
        "schemaVersion": "du-u5-gate-live-v1",
        "passed": report.passed,
        "durationSeconds": round(time.perf_counter() - started, 6),
        "runtimeEnvironment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "logicalCpuCount": os.cpu_count(),
            "projectionPersistence": "EPHEMERAL",
            "networkProfile": "METADATA_CENSUS_ONLY",
            "measurementWindow": "TOTAL_CPU_LE_25_AVAILABLE_MEMORY_GE_6GB_AND_WALL_CPU_RATIO_LE_1.15",
        },
        "measurementDiagnostics": {
            "u3SloRetryCount": u3SloRetryCount,
            "fullAttemptCount": fullAttemptCount,
            "fullCpuSeconds": round(fullCpuSeconds, 6),
            "fullContentionRatio": round(fullContentionRatio, 6),
            "replayAttemptCount": replayAttemptCount,
            "replayCpuSeconds": round(replayCpuSeconds, 6),
            "replayContentionRatio": round(replayContentionRatio, 6),
            "incrementalAttemptCount": incrementalAttempts,
            "incrementalCpuSeconds": round(incrementalCpuSeconds, 6),
            "incrementalContentionRatio": round(incrementalContentionRatio, 6),
        },
        "u3Digest": u3Digest,
        "u3FailureCodes": tuple(sorted(set(upstreamFailureCodes))),
        "report": asdict(report),
    }
    return report.passed, metrics, observerResult


def runLiveU5(*, checkpointPath: Path, recoveryRoot: Path, u3ControlRoot: Path):
    passed, metrics, _observerResult = _runLiveU5(
        checkpointPath=checkpointPath,
        recoveryRoot=recoveryRoot,
        u3ControlRoot=u3ControlRoot,
    )
    return passed, metrics


def runLiveU5Observed(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
    u3ControlRoot: Path,
    projectionObserver: Callable[[SpatialProjection, CatalogState], object],
):
    """U5가 측정한 바로 그 full projection을 후속 runtime gate에 한 번 노출한다."""

    return _runLiveU5(
        checkpointPath=checkpointPath,
        recoveryRoot=recoveryRoot,
        u3ControlRoot=u3ControlRoot,
        projectionObserver=projectionObserver,
    )


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe U5 live spatial projection gate")
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    parser.add_argument("--u3-control-root", type=Path, default=defaultControlRoot())
    parser.add_argument("--report", type=Path, default=defaultU5ControlRoot() / "latest.json")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    passed, metrics = runLiveU5(
        checkpointPath=args.checkpoint,
        recoveryRoot=args.recovery_root,
        u3ControlRoot=args.u3_control_root,
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
