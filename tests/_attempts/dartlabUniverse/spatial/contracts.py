"""Renderer library와 분리된 Universe U5 projection, scene, LOD 계약."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts import EpistemicClass, VerificationState, Visibility

PROJECTION_SCHEMA_VERSION = "du-projection-v1"
PROJECTION_STATE_SCHEMA_VERSION = "du-projection-state-v1"
COMMUNITY_SCHEMA_VERSION = "du-projection-community-v1"
SCENE_MANIFEST_SCHEMA_VERSION = "du-scene-manifest-v1"
SCENE_PAYLOAD_SCHEMA_VERSION = "du-scene-payload-v1"
LOD_POLICY_VERSION = "du-semantic-lod-v1"
STYLE_SCHEMA_VERSION = "du-scene-style-v1"
COORDINATE_SYSTEM_VERSION = "du-rh-y-up-q-v1"
QUANTIZATION_VERSION = "du-round-half-even-q-v1"
PROJECTION_COMPILER_VERSION = "du-spatial-compiler-v2"


@dataclass(frozen=True, slots=True)
class ProjectionBudget:
    rootHalfExtentQ: int = 1_000_000
    clusterHashBits: int = 6
    maxNodesPerTile: int = 2_048
    maxEdgesPerTile: int = 16_384
    maxTileBytes: int = 2 * 1024 * 1024
    maxTiles: int = 4_096
    representativeCount: int = 8


@dataclass(frozen=True, slots=True)
class ProjectionRequest:
    snapshotId: str
    projectionVersion: str
    objectScope: tuple[str, ...]
    relationScope: tuple[str, ...]
    validAt: str
    knownAt: str
    activeLens: str
    allowedVisibility: tuple[Visibility, ...]
    selectedObjectIds: tuple[str, ...] = ()
    stabilityBaseProjectionId: str | None = None
    generation: int = 1
    budget: ProjectionBudget = ProjectionBudget()
    seed: int = 0


@dataclass(frozen=True, slots=True)
class LogicalCoordinate:
    objectId: str
    clusterId: str
    positionQ: tuple[int, int, int]
    radiusQ: int


@dataclass(frozen=True, slots=True)
class CommunityVersion:
    communityLogicalId: str
    communityVersionId: str
    level: int
    semanticKey: str
    parentCommunityLogicalId: str | None
    memberDigest: str
    memberCount: int
    memberObjectIds: tuple[str, ...]
    memberImportance: tuple[tuple[str, int], ...]
    lineageKind: str
    predecessorRefs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CommunityLineageEvent:
    eventKind: str
    level: int
    fromCommunityIds: tuple[str, ...]
    toCommunityIds: tuple[str, ...]
    overlapScores: tuple[tuple[str, str, float], ...]
    digest: str


@dataclass(frozen=True, slots=True)
class ProjectionState:
    schemaVersion: str
    projectionStateId: str
    baseProjectionStateId: str | None
    snapshotId: str
    projectionVersion: str
    compilerVersion: str
    inputGraphDigest: str
    visibilityScopeDigest: str
    coordinateSystemVersion: str
    quantizationVersion: str
    coordinates: tuple[LogicalCoordinate, ...]
    communities: tuple[CommunityVersion, ...]
    lineageEvents: tuple[CommunityLineageEvent, ...]
    logicalCoordinateMapDigest: str
    communityLineageDigest: str
    outputDigest: str
    createdAt: str
    persistenceMode: str
    rollbackProjectionStateId: str | None


@dataclass(frozen=True, slots=True)
class Bounds3d:
    minimumQ: tuple[int, int, int]
    maximumQ: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class SceneNode:
    nodeId: str
    targetKind: str
    targetId: str
    positionQ: tuple[int, int, int]
    radiusQ: int
    importance: int
    kind: str
    epistemicClass: EpistemicClass
    verificationState: VerificationState
    clusterId: str
    lodLevel: int
    labelPriority: int
    pickId: int
    styleToken: str
    detailRef: str


@dataclass(frozen=True, slots=True)
class SceneProxy:
    proxyId: str
    proxyVersionId: str
    communityLogicalId: str
    communityVersionId: str
    memberDigest: str
    memberCount: int
    representativeObjectIds: tuple[str, ...]
    representativeRuleVersion: str
    primaryHomeClusterId: str
    secondaryMemberships: tuple[str, ...]
    drillTargetTileId: str
    kindHistogram: tuple[tuple[str, int], ...]
    sourceHistogram: tuple[tuple[str, int], ...]
    epistemicHistogram: tuple[tuple[str, int], ...]
    verificationHistogram: tuple[tuple[str, int], ...]
    periodRange: tuple[str | None, str | None]
    statementCount: int
    statementRefSetDigest: str
    evidenceCount: int
    evidenceRefSetDigest: str
    relationTypeDirectionHistogram: tuple[tuple[str, int], ...]
    positionQ: tuple[int, int, int]
    radiusQ: int
    lodLevel: int
    pickId: int
    styleToken: str
    detailRef: str


@dataclass(frozen=True, slots=True)
class SceneEdge:
    edgeId: str
    relationType: str
    fromNodeId: str
    toNodeId: str
    weight: float
    epistemicClass: EpistemicClass
    verificationState: VerificationState
    evidenceCount: int
    lodLevel: int
    aggregateCount: int
    styleToken: str
    detailRef: str


@dataclass(frozen=True, slots=True)
class SceneTileEnvelope:
    sceneId: str
    snapshotId: str
    projectionVersion: str
    projectionDigest: str
    lodPolicyVersion: str
    payloadSchemaVersion: str
    visibilityScopeDigest: str
    generation: int
    tileId: str
    parentTileId: str | None
    childTileIds: tuple[str, ...]
    bounds3d: Bounds3d
    coordinateOriginQ: tuple[int, int, int]
    encoding: str
    screenSpaceError: float
    lodLevel: int
    nodeCount: int
    edgeCount: int
    clusterSummaries: tuple[str, ...]
    contentRef: str
    contentDigest: str
    byteSize: int
    nextCursor: str | None


@dataclass(frozen=True, slots=True)
class SceneTile:
    envelope: SceneTileEnvelope
    proxies: tuple[SceneProxy, ...]
    nodes: tuple[SceneNode, ...]
    edges: tuple[SceneEdge, ...]


@dataclass(frozen=True, slots=True)
class DrillPath:
    targetKind: str
    targetId: str
    levelRefs: tuple[tuple[str, str], ...]
    detailRef: str
    evidenceRefs: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class SceneManifest:
    schemaVersion: str
    sceneId: str
    snapshotId: str
    projectionVersion: str
    projectionDigest: str
    visibilityScopeDigest: str
    generation: int
    coordinateSystem: str
    rootTileId: str
    bounds: Bounds3d
    objectCount: int
    relationCount: int
    tileCount: int
    lodPolicyVersion: str
    payloadSchemaVersion: str
    styleSchemaVersion: str
    createdFrom: str
    digest: str


@dataclass(frozen=True, slots=True)
class ConservationAssertion:
    parentCommunityId: str
    assertionKind: str
    passed: bool
    expectedDigest: str
    actualDigest: str


@dataclass(frozen=True, slots=True)
class MeaningPreservationReport:
    passed: bool
    assertionCount: int
    passedAssertionCount: int
    meaningPreservation: float
    assertions: tuple[ConservationAssertion, ...]
    failureCodes: tuple[str, ...]
    digest: str


@dataclass(frozen=True, slots=True)
class SpatialProjection:
    state: ProjectionState
    manifest: SceneManifest
    tiles: tuple[SceneTile, ...]
    drillPaths: tuple[DrillPath, ...]
    meaningReport: MeaningPreservationReport
    selectedObjectIds: tuple[str, ...]
    digest: str
