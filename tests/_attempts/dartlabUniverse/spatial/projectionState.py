"""Catalog snapshot과 relation graph를 runtime-only SpatialProjection으로 컴파일한다."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from itertools import pairwise

from ..canonical import canonicalDigest
from ..catalog.models import CatalogState
from ..catalog.snapshot import CatalogSnapshot
from ..contracts import VerificationState
from ..graph.relations import GraphRelation
from ..graph.statements import GraphStatement
from ..ids import logicalId
from ..temporal import parseInstant
from .community import buildCommunityCandidates, clearCommunityRuntimeCaches
from .communityLineage import compileCommunityLineage
from .contracts import (
    COORDINATE_SYSTEM_VERSION,
    PROJECTION_COMPILER_VERSION,
    PROJECTION_SCHEMA_VERSION,
    PROJECTION_STATE_SCHEMA_VERSION,
    QUANTIZATION_VERSION,
    ProjectionRequest,
    ProjectionState,
    SpatialProjection,
)
from .digest import spatialPackedDigest
from .layout import compileCoordinates
from .lod import compileSemanticLod
from .tiles import compileSceneTiles, validateSceneTileGraph


@lru_cache(maxsize=16_384)
def _parseInstant(value: str):
    return parseInstant(value)


def clearSpatialRuntimeCaches() -> None:
    """Cold replay benchmark 전에 spatial temporal cache만 비운다."""
    _parseInstant.cache_clear()
    clearCommunityRuntimeCaches()


def _visibleRelation(
    relation: GraphRelation,
    request: ProjectionRequest,
    objectIds: frozenset[str],
    *,
    validAt,
    knownAt,
    relationScope: frozenset[str],
) -> bool:
    start = _parseInstant(relation.validTime.start) if relation.validTime.start else None
    end = _parseInstant(relation.validTime.end) if relation.validTime.end else None
    known = _parseInstant(relation.systemTime.knownAt)
    retracted = _parseInstant(relation.systemTime.retractedAt) if relation.systemTime.retractedAt else None
    return (
        relation.visibility in request.allowedVisibility
        and (not relationScope or relation.relationType in relationScope or relation.relationId in relationScope)
        and (relation.fromRef in objectIds or relation.toRef in objectIds)
        and (start is None or start <= validAt)
        and (end is None or validAt < end)
        and known <= knownAt
        and (retracted is None or knownAt < retracted)
        and relation.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )


def _validatePrior(prior: ProjectionState | None, request: ProjectionRequest, visibilityDigest: str) -> None:
    if prior is None:
        if request.stabilityBaseProjectionId is not None:
            raise ValueError("stability base ID가 있지만 prior ProjectionState가 없음")
        return
    if (
        request.stabilityBaseProjectionId != prior.projectionStateId
        or prior.projectionVersion != request.projectionVersion
        or prior.compilerVersion != PROJECTION_COMPILER_VERSION
        or prior.schemaVersion != PROJECTION_STATE_SCHEMA_VERSION
        or prior.visibilityScopeDigest != visibilityDigest
        or prior.persistenceMode not in {"EPHEMERAL", "APPROVED_DERIVED"}
    ):
        raise ValueError("prior ProjectionState binding이 잘못됨")


def compileSpatialProjection(
    catalog: CatalogState,
    snapshot: CatalogSnapshot,
    relations: tuple[GraphRelation, ...],
    *,
    request: ProjectionRequest,
    statements: tuple[GraphStatement, ...] = (),
    priorState: ProjectionState | None = None,
) -> SpatialProjection:
    """지식 ID와 원본 byte를 복제하지 않고 deterministic 3D scene을 만든다."""
    if request.snapshotId != snapshot.snapshotId or snapshot.catalogDigest != catalog.digest:
        raise ValueError("projection request와 catalog snapshot binding이 잘못됨")
    visibilityDigest = canonicalDigest(tuple(sorted(item.value for item in request.allowedVisibility)))
    _validatePrior(priorState, request, visibilityDigest)
    candidates = buildCommunityCandidates(catalog, request)
    objectIds = frozenset(item.objectId for item in candidates.objects)
    validAt = parseInstant(request.validAt)
    knownAt = parseInstant(request.knownAt)
    relationScope = frozenset(request.relationScope)
    activeRelations = tuple(
        item
        for item in relations
        if _visibleRelation(
            item,
            request,
            objectIds,
            validAt=validAt,
            knownAt=knownAt,
            relationScope=relationScope,
        )
    )
    if any(left.relationId >= right.relationId for left, right in pairwise(activeRelations)):
        activeRelations = tuple(sorted(activeRelations, key=lambda item: item.relationId))
    activeStatements = tuple(
        item
        for item in statements
        if item.visibility in request.allowedVisibility
        and (item.subjectRef in objectIds or item.objectRef in objectIds)
        and _visibleStatement(item, request, validAt=validAt, knownAt=knownAt)
    )
    inputGraphDigest = spatialPackedDigest(
        PROJECTION_SCHEMA_VERSION,
        snapshot.snapshotId,
        catalog.digest,
        tuple((item.objectId, item.objectVersionId) for item in candidates.objects),
        tuple((item.relationId, item.digest) for item in activeRelations),
        tuple((item.statementId, item.digest) for item in activeStatements),
        request.objectScope,
        request.relationScope,
        request.validAt,
        request.knownAt,
        visibilityDigest,
        request.seed,
    )
    communities, lineageEvents = compileCommunityLineage(
        candidates.candidates,
        projectionVersion=request.projectionVersion,
        priorCommunities=priorState.communities if priorState else (),
    )
    communityBySemantic = {item.semanticKey: item.communityLogicalId for item in communities}
    homeCommunityByObject = {
        objectId: communityBySemantic[semanticKey] for objectId, semanticKey in candidates.homeSemanticKeyByObject
    }
    coordinates = compileCoordinates(
        candidates.objects,
        activeRelations,
        communities,
        homeCommunityByObject,
        budget=request.budget,
        seed=request.seed,
        priorState=priorState,
    )
    coordinateDigest = spatialPackedDigest(
        "COORDINATE_MAP",
        tuple((item.objectId, item.clusterId, item.positionQ, item.radiusQ) for item in coordinates),
    )
    lineageDigest = spatialPackedDigest(
        "COMMUNITY_LINEAGE",
        tuple(
            (
                item.communityLogicalId,
                item.communityVersionId,
                item.parentCommunityLogicalId,
                item.memberDigest,
                item.lineageKind,
                item.predecessorRefs,
            )
            for item in communities
        ),
        tuple(item.digest for item in lineageEvents),
    )
    outputDigest = spatialPackedDigest(
        inputGraphDigest,
        request.projectionVersion,
        PROJECTION_COMPILER_VERSION,
        COORDINATE_SYSTEM_VERSION,
        QUANTIZATION_VERSION,
        coordinateDigest,
        lineageDigest,
    )
    stateId = logicalId(
        "projection-state",
        (snapshot.snapshotId, request.projectionVersion, visibilityDigest, outputDigest),
    )
    state = ProjectionState(
        schemaVersion=PROJECTION_STATE_SCHEMA_VERSION,
        projectionStateId=stateId,
        baseProjectionStateId=priorState.projectionStateId if priorState else None,
        snapshotId=snapshot.snapshotId,
        projectionVersion=request.projectionVersion,
        compilerVersion=PROJECTION_COMPILER_VERSION,
        inputGraphDigest=inputGraphDigest,
        visibilityScopeDigest=visibilityDigest,
        coordinateSystemVersion=COORDINATE_SYSTEM_VERSION,
        quantizationVersion=QUANTIZATION_VERSION,
        coordinates=coordinates,
        communities=communities,
        lineageEvents=lineageEvents,
        logicalCoordinateMapDigest=coordinateDigest,
        communityLineageDigest=lineageDigest,
        outputDigest=outputDigest,
        createdAt=request.knownAt,
        persistenceMode="EPHEMERAL",
        rollbackProjectionStateId=priorState.projectionStateId if priorState else None,
    )
    lod = compileSemanticLod(
        catalog,
        candidates.objects,
        activeRelations,
        activeStatements,
        communities,
        coordinates,
        request,
    )
    if not lod.meaningReport.passed:
        raise ValueError("semantic LOD meaning preservation 실패")
    manifest, tiles = compileSceneTiles(
        state,
        communities,
        lod,
        request,
        relationCount=len(activeRelations),
    )
    tileFailures = validateSceneTileGraph(manifest, tiles, verifyContent=False)
    if tileFailures:
        raise ValueError(f"scene tile validation 실패: {','.join(tileFailures)}")
    selected = tuple(sorted(set(request.selectedObjectIds)))
    if selected:
        coordinateIds = frozenset(item.objectId for item in coordinates)
        drillIds = frozenset(item.targetId for item in lod.drillPaths if item.targetKind == "OBJECT")
        if any(item not in coordinateIds or item not in drillIds for item in selected):
            raise ValueError("selected object가 projection 또는 drill path에서 유실됨")
    digest = spatialPackedDigest(
        state.outputDigest,
        manifest.digest,
        tuple(item.envelope.contentDigest for item in tiles),
        tuple(item.digest for item in lod.drillPaths),
        lod.meaningReport.digest,
        selected,
    )
    return SpatialProjection(
        state=state,
        manifest=manifest,
        tiles=tiles,
        drillPaths=lod.drillPaths,
        meaningReport=lod.meaningReport,
        selectedObjectIds=selected,
        digest=digest,
    )


def _visibleStatement(statement: GraphStatement, request: ProjectionRequest, *, validAt, knownAt) -> bool:
    start = _parseInstant(statement.validTime.start) if statement.validTime.start else None
    end = _parseInstant(statement.validTime.end) if statement.validTime.end else None
    known = _parseInstant(statement.systemTime.knownAt)
    retracted = _parseInstant(statement.systemTime.retractedAt) if statement.systemTime.retractedAt else None
    return (
        (start is None or start <= validAt)
        and (end is None or validAt < end)
        and known <= knownAt
        and (retracted is None or knownAt < retracted)
        and statement.verificationState not in {VerificationState.RETRACTED, VerificationState.TOMBSTONED}
    )
