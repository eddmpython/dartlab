"""Universe의 bounded, deterministic, lane-safe scene projection을 검증한다.

Capabilities
    Atlas, industry, company graph를 hard bound 안에서 stable priority로 잘라 SceneReceipt와 omission을 만든다.

AIContext
    AI 역할: 전체 데이터를 복제하거나 candidate를 fact로 승격하지 않고 질문에 필요한 scene만 투영한다.

Guide
    Synthetic compiler contract와 current public map artifact 3종의 live projection을 분리한다.

When
    U0-P01 bounded projection 또는 public runtime scene contract를 검증할 때 사용한다.

How
    Artifact adapter로 node와 edge를 만든 뒤 :func:`compileBoundedProjection`을 호출한다.

Requires
    Live 실행 시 public atlas, industry, company JSON과 network가 필요하다.

Raises
    ValueError: spec, graph identity, lane admission, bounds 또는 source snapshot이 잘못됐을 때.

Example
    ``scene = compileBoundedProjection(spec, nodes, edges)``

See Also
    :mod:`tests._attempts.dartlabUniverse.ontology.assertionContract`.

결과
    Current relation은 candidate, aggregate flow는 derived로 보존하고 scene 밖 항목은 omission receipt로 남긴다.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable
from urllib.request import urlopen

from dartlab.simulate.vintage import canonicalPayloadHash

BASE_URL = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/landing/map/"
LANES = {"fact", "candidate", "derived", "scenario"}
LANE_RANK = {"fact": 0, "candidate": 1, "derived": 2, "scenario": 3}
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ASSERTION_ID_PATTERN = re.compile(r"^assertion:[0-9a-f]{64}$")
EVIDENCE_ID_PATTERN = re.compile(r"^evidence:[0-9a-f]{64}$")


@dataclass(frozen=True)
class ProjectionSpec:
    """Question seed, source snapshot, graph bounds와 traversal depth를 고정한다."""

    projectionId: str
    query: str
    seedIds: tuple[str, ...]
    sourceSnapshotSetId: str
    maxDepth: int
    maxNodes: int
    maxEdges: int

    def __post_init__(self) -> None:
        seeds = tuple(sorted(set(self.seedIds)))
        if not self.projectionId or not self.query or not seeds:
            raise ValueError("projection identity, query, and seeds are required")
        if not SHA256_PATTERN.fullmatch(self.sourceSnapshotSetId):
            raise ValueError("projection requires a SourceSnapshotSet SHA-256 digest")
        if self.maxDepth < 0 or self.maxDepth > 6:
            raise ValueError("projection maxDepth must be between 0 and 6")
        if self.maxNodes <= 0 or self.maxNodes > 500:
            raise ValueError("projection maxNodes must be between 1 and 500")
        if self.maxEdges < 0 or self.maxEdges > 2000:
            raise ValueError("projection maxEdges must be between 0 and 2000")
        if len(seeds) > self.maxNodes:
            raise ValueError("projection seed count exceeds maxNodes")
        object.__setattr__(self, "seedIds", seeds)


@dataclass(frozen=True)
class ProjectionNode:
    """Scene 후보 node의 stable identity, lane, priority와 source locator를 보존한다."""

    nodeId: str
    label: str
    lane: str
    priority: float
    sourceKind: str
    sourceRef: str


@dataclass(frozen=True)
class ProjectionEdge:
    """Scene 후보 edge의 lane과 fact, derived, scenario admission proof를 보존한다."""

    edgeId: str
    sourceId: str
    targetId: str
    predicate: str
    lane: str
    priority: float
    sourceRef: str
    assertionId: str = ""
    evidenceRefs: tuple[str, ...] = ()
    derivationRefs: tuple[str, ...] = ()
    scenarioReceiptId: str = ""


@dataclass(frozen=True)
class OmissionReceipt:
    """Scene에서 생략된 node와 edge 수를 이유 및 lane별로 보존한다."""

    omittedNodeCount: int
    omittedEdgeCount: int
    nodeReasonCounts: tuple[tuple[str, int], ...]
    edgeReasonCounts: tuple[tuple[str, int], ...]
    omittedNodeLaneCounts: tuple[tuple[str, int], ...]
    omittedEdgeLaneCounts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class SceneReceipt:
    """Projection spec, input, output, hard bound와 omission을 재현 가능하게 결속한다."""

    specHash: str
    sourceSnapshotSetId: str
    inputNodeCount: int
    inputEdgeCount: int
    outputNodeCount: int
    outputEdgeCount: int
    seedCount: int
    retainedSeedCount: int
    maxDepthObserved: int
    omission: OmissionReceipt


@dataclass(frozen=True)
class BoundedScene:
    """Renderer와 무관한 logical node, edge, receipt와 deterministic scene hash다."""

    nodes: tuple[ProjectionNode, ...]
    edges: tuple[ProjectionEdge, ...]
    receipt: SceneReceipt
    sceneHash: str

    def toDict(self) -> dict[str, Any]:
        """JSON compatible logical scene payload를 반환한다.

        Returns
            Scene dataclass를 nested mapping으로 바꾼 값.

        Example
            ``payload = scene.toDict()``

        Requires
            Dataclass fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def _validateGraph(
    spec: ProjectionSpec,
    nodes: tuple[ProjectionNode, ...],
    edges: tuple[ProjectionEdge, ...],
) -> tuple[dict[str, ProjectionNode], dict[str, ProjectionEdge]]:
    nodeIndex = {node.nodeId: node for node in nodes}
    edgeIndex = {edge.edgeId: edge for edge in edges}
    if len(nodeIndex) != len(nodes) or any(not node.nodeId or not node.label for node in nodes):
        raise ValueError("projection nodes require unique non-empty identity")
    if len(edgeIndex) != len(edges):
        raise ValueError("projection edges require unique edgeId")
    if any(seedId not in nodeIndex for seedId in spec.seedIds):
        raise ValueError("projection seed is missing from nodes")
    for node in nodes:
        if node.lane not in LANES or not node.sourceKind or not node.sourceRef:
            raise ValueError("projection node lane or source is invalid")
    for edge in edges:
        if (
            not edge.edgeId
            or not edge.predicate
            or not edge.sourceRef
            or edge.lane not in LANES
            or edge.sourceId not in nodeIndex
            or edge.targetId not in nodeIndex
        ):
            raise ValueError("projection edge identity, lane, or endpoint is invalid")
        if edge.sourceId == edge.targetId:
            raise ValueError("projection does not admit self-loop edges")
        if edge.lane == "fact":
            if not ASSERTION_ID_PATTERN.fullmatch(edge.assertionId):
                raise ValueError("fact edge requires an exact assertionId")
            if not edge.evidenceRefs or any(not EVIDENCE_ID_PATTERN.fullmatch(ref) for ref in edge.evidenceRefs):
                raise ValueError("fact edge requires exact evidenceRefs")
        elif edge.assertionId or edge.evidenceRefs:
            raise ValueError("non-fact edge cannot carry fact admission fields")
        if edge.lane == "derived" and not edge.derivationRefs:
            raise ValueError("derived edge requires derivationRefs")
        if edge.lane == "scenario" and not edge.scenarioReceiptId:
            raise ValueError("scenario edge requires scenarioReceiptId")
    return nodeIndex, edgeIndex


def _specPayload(spec: ProjectionSpec) -> dict[str, Any]:
    return {
        "schemaVersion": "projectionSpec.v1",
        "projectionId": spec.projectionId,
        "query": spec.query,
        "seedIds": spec.seedIds,
        "sourceSnapshotSetId": spec.sourceSnapshotSetId,
        "maxDepth": spec.maxDepth,
        "maxNodes": spec.maxNodes,
        "maxEdges": spec.maxEdges,
    }


def compileBoundedProjection(
    spec: ProjectionSpec,
    nodes: Iterable[ProjectionNode],
    edges: Iterable[ProjectionEdge],
) -> BoundedScene:
    """Seed 중심 graph를 hard bound와 stable priority로 deterministic logical scene에 투영한다.

    Capabilities
        Depth, node, edge bound, lane isolation, seed retention, stable truncation, omission receipt를 제공한다.

    AIContext
        AI 역할: 그래프 전체를 화면에 복제하거나 confidence로 candidate를 fact로 바꾸지 않는다.

    Args
        spec: Seed와 hard bound를 가진 projection contract.
        nodes: Renderer-neutral node candidates.
        edges: Explicit lane과 provenance를 가진 edge candidates.

    Returns
        Bounded logical scene과 deterministic hash 및 receipt.

    Example
        ``scene = compileBoundedProjection(spec, nodes, edges)``

    Guide
        Omission은 오류가 아니며 receipt의 reason과 lane count로 공개한다.

    When
        Universe route가 atlas, industry, company scene을 요청할 때 호출한다.

    How
        Seed에서 incident edge를 priority queue로 순회하고 새 endpoint가 bound 안일 때만 선택한다.

    Requires
        SourceSnapshotSet과 unique node, edge identity가 필요하다.

    See Also
        :class:`SceneReceipt`.

    Raises
        ValueError: Spec, graph, lane admission 또는 seed contract가 잘못됐을 때.
    """

    nodeItems = tuple(nodes)
    edgeItems = tuple(edges)
    nodeIndex, edgeIndex = _validateGraph(spec, nodeItems, edgeItems)
    adjacency: defaultdict[str, list[str]] = defaultdict(list)
    for edge in edgeItems:
        adjacency[edge.sourceId].append(edge.edgeId)
        adjacency[edge.targetId].append(edge.edgeId)
    for edgeIds in adjacency.values():
        edgeIds.sort()

    selectedNodeIds = set(spec.seedIds)
    selectedEdgeIds: set[str] = set()
    depthByNode = {seedId: 0 for seedId in spec.seedIds}
    queued: set[str] = set()
    considered: set[str] = set()
    edgeReasons: dict[str, str] = {}
    nodeReasonHints: defaultdict[str, set[str]] = defaultdict(set)
    queue: list[tuple[int, int, float, str]] = []

    def _enqueue(nodeId: str) -> None:
        baseDepth = depthByNode[nodeId]
        for edgeId in adjacency[nodeId]:
            if edgeId in queued or edgeId in considered:
                continue
            edge = edgeIndex[edgeId]
            heapq.heappush(
                queue,
                (baseDepth, LANE_RANK[edge.lane], -float(edge.priority), edge.edgeId),
            )
            queued.add(edgeId)

    for seedId in spec.seedIds:
        _enqueue(seedId)

    while queue:
        _, _, _, edgeId = heapq.heappop(queue)
        considered.add(edgeId)
        edge = edgeIndex[edgeId]
        selectedEndpoints = [endpoint for endpoint in (edge.sourceId, edge.targetId) if endpoint in selectedNodeIds]
        if not selectedEndpoints:
            edgeReasons[edgeId] = "disconnected"
            continue
        newEndpoints = [endpoint for endpoint in (edge.sourceId, edge.targetId) if endpoint not in selectedNodeIds]
        nextDepth = min(depthByNode[endpoint] for endpoint in selectedEndpoints) + int(bool(newEndpoints))
        if nextDepth > spec.maxDepth:
            edgeReasons[edgeId] = "depthLimit"
            for endpoint in newEndpoints:
                nodeReasonHints[endpoint].add("depthLimit")
            continue
        if len(selectedEdgeIds) >= spec.maxEdges:
            edgeReasons[edgeId] = "edgeBudget"
            for endpoint in newEndpoints:
                nodeReasonHints[endpoint].add("edgeBudget")
            continue
        if len(selectedNodeIds) + len(set(newEndpoints)) > spec.maxNodes:
            edgeReasons[edgeId] = "nodeBudget"
            for endpoint in newEndpoints:
                nodeReasonHints[endpoint].add("nodeBudget")
            continue
        selectedEdgeIds.add(edgeId)
        for endpoint in newEndpoints:
            selectedNodeIds.add(endpoint)
            depthByNode[endpoint] = nextDepth
            _enqueue(endpoint)

    for edge in edgeItems:
        if edge.edgeId not in selectedEdgeIds and edge.edgeId not in edgeReasons:
            edgeReasons[edge.edgeId] = "disconnected"
    nodeReasonPriority = ("nodeBudget", "edgeBudget", "depthLimit")
    nodeReasons: dict[str, str] = {}
    for node in nodeItems:
        if node.nodeId in selectedNodeIds:
            continue
        hints = nodeReasonHints[node.nodeId]
        nodeReasons[node.nodeId] = next(
            (reason for reason in nodeReasonPriority if reason in hints),
            "disconnected",
        )

    selectedNodes = tuple(
        sorted(
            (nodeIndex[nodeId] for nodeId in selectedNodeIds),
            key=lambda node: (
                depthByNode[node.nodeId],
                0 if node.nodeId in spec.seedIds else 1,
                LANE_RANK[node.lane],
                -float(node.priority),
                node.nodeId,
            ),
        )
    )
    selectedEdges = tuple(
        sorted(
            (edgeIndex[edgeId] for edgeId in selectedEdgeIds),
            key=lambda edge: (
                max(depthByNode[edge.sourceId], depthByNode[edge.targetId]),
                LANE_RANK[edge.lane],
                -float(edge.priority),
                edge.edgeId,
            ),
        )
    )
    omittedNodes = [nodeIndex[nodeId] for nodeId in nodeReasons]
    omittedEdges = [edgeIndex[edgeId] for edgeId in edgeReasons]
    omission = OmissionReceipt(
        omittedNodeCount=len(omittedNodes),
        omittedEdgeCount=len(omittedEdges),
        nodeReasonCounts=tuple(sorted(Counter(nodeReasons.values()).items())),
        edgeReasonCounts=tuple(sorted(Counter(edgeReasons.values()).items())),
        omittedNodeLaneCounts=tuple(sorted(Counter(node.lane for node in omittedNodes).items())),
        omittedEdgeLaneCounts=tuple(sorted(Counter(edge.lane for edge in omittedEdges).items())),
    )
    receipt = SceneReceipt(
        specHash=canonicalPayloadHash(_specPayload(spec)),
        sourceSnapshotSetId=spec.sourceSnapshotSetId,
        inputNodeCount=len(nodeItems),
        inputEdgeCount=len(edgeItems),
        outputNodeCount=len(selectedNodes),
        outputEdgeCount=len(selectedEdges),
        seedCount=len(spec.seedIds),
        retainedSeedCount=sum(seedId in selectedNodeIds for seedId in spec.seedIds),
        maxDepthObserved=max(depthByNode.values()),
        omission=omission,
    )
    scenePayload = {
        "schemaVersion": "boundedScene.v1",
        "nodes": tuple(asdict(node) for node in selectedNodes),
        "edges": tuple(asdict(edge) for edge in selectedEdges),
        "receipt": asdict(receipt),
    }
    sceneHash = canonicalPayloadHash(scenePayload)
    if len(selectedNodes) > spec.maxNodes or len(selectedEdges) > spec.maxEdges:
        raise ValueError("projection exceeded a hard bound")
    if receipt.retainedSeedCount != receipt.seedCount:
        raise ValueError("projection lost a seed")
    if any(edge.sourceId not in selectedNodeIds or edge.targetId not in selectedNodeIds for edge in selectedEdges):
        raise ValueError("projection created a dangling edge")
    return BoundedScene(selectedNodes, selectedEdges, receipt, sceneHash)


def _edgeId(payload: dict[str, Any]) -> str:
    return f"edge:{canonicalPayloadHash(payload)}"


def adaptAtlas(payload: dict[str, Any]) -> tuple[tuple[ProjectionNode, ...], tuple[ProjectionEdge, ...]]:
    """Current atlas industry와 aggregate flow를 candidate node 및 derived edge로 바꾼다.

    Capabilities
        34개 industry identity와 aggregate flow derivation을 generic projection input으로 만든다.

    AIContext
        AI 역할: Atlas aggregate를 observed company relation으로 오인하지 않는다.

    Args
        payload: industries와 flows를 가진 atlas JSON.

    Returns
        Projection node와 derived edge tuple.

    Example
        ``nodes, edges = adaptAtlas(atlas)``

    Guide
        Flow는 artifact aggregation이므로 derived lane을 유지한다.

    When
        Universe 첫 화면 또는 industry transition scene을 만들 때 호출한다.

    How
        Industry ID와 flow endpoints를 stable sourceRef에 결속한다.

    Requires
        Atlas industries와 flows list가 필요하다.

    See Also
        :func:`adaptIndustry`.

    Raises
        ValueError: Atlas schema 또는 endpoint가 잘못됐을 때.
    """

    industries = payload.get("industries")
    flows = payload.get("flows")
    if not isinstance(industries, list) or not isinstance(flows, list):
        raise ValueError("atlas requires industries and flows")
    nodes = tuple(
        ProjectionNode(
            nodeId=str(item["id"]),
            label=str(item["name"]),
            lane="candidate",
            priority=float(item.get("revenue") or 0),
            sourceKind="atlas",
            sourceRef=f"map:atlas#industry={item['id']}",
        )
        for item in industries
    )
    edges = []
    for index, item in enumerate(flows):
        edgePayload = {
            "sourceId": str(item["fromIndustry"]),
            "targetId": str(item["toIndustry"]),
            "predicate": "aggregateFlow",
            "index": index,
        }
        edges.append(
            ProjectionEdge(
                edgeId=_edgeId(edgePayload),
                sourceId=edgePayload["sourceId"],
                targetId=edgePayload["targetId"],
                predicate="aggregateFlow",
                lane="derived",
                priority=float(item.get("edgeCount") or 0),
                sourceRef=f"map:atlas#flow={index}",
                derivationRefs=(f"map:atlas#flow={index}",),
            )
        )
    return nodes, tuple(edges)


def adaptIndustry(payload: dict[str, Any]) -> tuple[tuple[ProjectionNode, ...], tuple[ProjectionEdge, ...]]:
    """Industry detail의 stage node와 unverified relation을 candidate projection input으로 바꾼다.

    Capabilities
        Stage별 company를 deduplicate하고 current edge lane을 candidate로 고정한다.

    AIContext
        AI 역할: Confidence와 source label을 fact admission proof로 사용하지 않는다.

    Args
        payload: stages, unclassified, edges를 가진 industry JSON.

    Returns
        Projection node와 candidate edge tuple.

    Example
        ``nodes, edges = adaptIndustry(industry)``

    Guide
        Exact assertion source가 없으므로 모든 relation edge는 candidate다.

    When
        Industry drilldown scene을 만들 때 호출한다.

    How
        Stage nodes와 unclassified nodes를 stockCode로 합치고 edge index를 sourceRef에 보존한다.

    Requires
        Industry stages와 edges list가 필요하다.

    See Also
        :func:`adaptCompany`.

    Raises
        ValueError: Industry schema 또는 duplicate node label이 충돌할 때.
    """

    stages = payload.get("stages")
    edgeRows = payload.get("edges")
    if not isinstance(stages, list) or not isinstance(edgeRows, list):
        raise ValueError("industry requires stages and edges")
    nodeRows = [node for stage in stages for node in stage.get("nodes", [])]
    nodeRows.extend(payload.get("unclassified") or [])
    nodeMap: dict[str, ProjectionNode] = {}
    for item in nodeRows:
        nodeId = str(item["stockCode"])
        candidate = ProjectionNode(
            nodeId=nodeId,
            label=str(item.get("corpName") or nodeId),
            lane="candidate",
            priority=float(item.get("revenue") or 0),
            sourceKind="industry",
            sourceRef=f"map:industry:{payload.get('industryId', 'unknown')}#node={nodeId}",
        )
        if nodeId in nodeMap and nodeMap[nodeId].label != candidate.label:
            raise ValueError("industry contains conflicting node labels")
        nodeMap[nodeId] = candidate
    edges = []
    for index, item in enumerate(edgeRows):
        edgePayload = {
            "sourceId": str(item["from"]),
            "targetId": str(item["to"]),
            "predicate": str(item.get("type") or "related"),
            "index": index,
        }
        edges.append(
            ProjectionEdge(
                edgeId=_edgeId(edgePayload),
                sourceId=edgePayload["sourceId"],
                targetId=edgePayload["targetId"],
                predicate=edgePayload["predicate"],
                lane="candidate",
                priority=float(item.get("confidence") or 0),
                sourceRef=f"map:industry:{payload.get('industryId', 'unknown')}#edge={index}",
            )
        )
    return tuple(nodeMap.values()), tuple(edges)


def adaptCompany(payload: dict[str, Any]) -> tuple[tuple[ProjectionNode, ...], tuple[ProjectionEdge, ...]]:
    """Company egograph의 ego, neighbor와 current relation을 bounded projection input으로 바꾼다.

    Capabilities
        Ego seed와 1-hop neighbor identity를 보존하고 relation을 candidate lane으로 고정한다.

    AIContext
        AI 역할: Evidence title과 confidence를 assertion-grade fact로 확대하지 않는다.

    Args
        payload: ego, neighbors, edges를 가진 company egograph JSON.

    Returns
        Projection node와 candidate edge tuple.

    Example
        ``nodes, edges = adaptCompany(company)``

    Guide
        Hop2와 narrative payload는 U0-P01 graph input에 자동 혼합하지 않는다.

    When
        Company focus scene을 만들 때 호출한다.

    How
        Ego와 1-hop neighbor를 stockCode로 합치고 edge array locator를 보존한다.

    Requires
        Company ego, neighbors, edges가 필요하다.

    See Also
        :func:`compileBoundedProjection`.

    Raises
        ValueError: Company graph schema 또는 endpoint가 잘못됐을 때.
    """

    ego = payload.get("ego")
    neighbors = payload.get("neighbors")
    edgeRows = payload.get("edges")
    if not isinstance(ego, dict) or not isinstance(neighbors, list) or not isinstance(edgeRows, list):
        raise ValueError("company graph requires ego, neighbors, and edges")
    nodeRows = [ego, *neighbors]
    nodeMap: dict[str, ProjectionNode] = {}
    egoId = str(ego["stockCode"])
    for item in nodeRows:
        nodeId = str(item["stockCode"])
        nodeMap[nodeId] = ProjectionNode(
            nodeId=nodeId,
            label=str(item.get("corpName") or nodeId),
            lane="candidate",
            priority=float(item.get("revenue") or 0) + (1e18 if nodeId == egoId else 0),
            sourceKind="company",
            sourceRef=f"map:company:{egoId}#node={nodeId}",
        )
    edges = []
    for index, item in enumerate(edgeRows):
        edgePayload = {
            "sourceId": str(item["from"]),
            "targetId": str(item["to"]),
            "predicate": str(item.get("type") or "related"),
            "index": index,
        }
        edges.append(
            ProjectionEdge(
                edgeId=_edgeId(edgePayload),
                sourceId=edgePayload["sourceId"],
                targetId=edgePayload["targetId"],
                predicate=edgePayload["predicate"],
                lane="candidate",
                priority=float(item.get("confidence") or 0),
                sourceRef=f"map:company:{egoId}#edge={index}",
            )
        )
    return tuple(nodeMap.values()), tuple(edges)


@dataclass(frozen=True)
class LiveProjectionReport:
    """Current artifact 3종의 input, bounded output, omission과 repeat hash를 요약한다."""

    sourceSnapshotSetId: str
    atlasInputNodes: int
    atlasInputEdges: int
    atlasOutputNodes: int
    atlasOutputEdges: int
    industryInputNodes: int
    industryInputEdges: int
    industryOutputNodes: int
    industryOutputEdges: int
    companyInputNodes: int
    companyInputEdges: int
    companyOutputNodes: int
    companyOutputEdges: int
    totalFactEdges: int
    totalCandidateEdges: int
    totalDerivedEdges: int
    boundViolationCount: int
    seedLossCount: int
    laneViolationCount: int
    repeatedSceneHashMatches: int
    repeatedSceneHashTotal: int
    liveReady: bool

    def toDict(self) -> dict[str, Any]:
        """JSON compatible live projection report를 반환한다.

        Returns
            Report dataclass를 mapping으로 바꾼 값.

        Example
            ``payload = report.toDict()``

        Requires
            Dataclass fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def _loadJson(name: str) -> tuple[dict[str, Any], str]:
    with urlopen(BASE_URL + name, timeout=60) as response:
        raw = response.read()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"map artifact is not an object: {name}")
    return payload, hashlib.sha256(raw).hexdigest()


def inspectLiveProjection() -> LiveProjectionReport:
    """Current atlas, semiconductor industry, Samsung egograph를 bounded scene으로 반복 투영한다.

    Capabilities
        Three seed archetype의 input, output, lane, bounds, seed retention, hash repeat를 측정한다.

    AIContext
        AI 역할: Artifact 전체를 새 graph bake로 복제하지 않고 runtime projection 가능성을 판정한다.

    Returns
        Current public artifact 기반 projection report.

    Example
        ``report = inspectLiveProjection()``

    Guide
        Fact edge 0은 실패가 아니라 current admission contract를 정직하게 반영한 값이다.

    When
        Public map artifact 또는 projection compiler가 바뀐 뒤 실행한다.

    How
        세 JSON bytes를 snapshot hash로 묶고 각각 같은 compiler를 두 번 실행한다.

    Requires
        Network와 public map artifact 3개가 필요하다.

    See Also
        :func:`compileBoundedProjection`.

    Raises
        OSError: Remote artifact를 읽지 못할 때.
        ValueError: Artifact schema 또는 projection contract가 잘못됐을 때.
    """

    atlas, atlasHash = _loadJson("atlas.json")
    industry, industryHash = _loadJson("industries/semiconductor.json")
    company, companyHash = _loadJson("companies/005930.json")
    snapshotPayload = (
        ("atlas.json", atlasHash),
        ("industries/semiconductor.json", industryHash),
        ("companies/005930.json", companyHash),
    )
    snapshotId = f"sha256:{canonicalPayloadHash(snapshotPayload)}"
    adapted = (
        ("atlas", "semiconductor", *adaptAtlas(atlas), 34, 50),
        ("industry", "005930", *adaptIndustry(industry), 50, 80),
        ("company", "005930", *adaptCompany(company), 50, 80),
    )
    records = []
    repeatMatches = 0
    laneViolationCount = 0
    boundViolationCount = 0
    seedLossCount = 0
    allEdges: list[ProjectionEdge] = []
    for kind, seedId, nodes, edges, maxNodes, maxEdges in adapted:
        spec = ProjectionSpec(
            projectionId=f"live:{kind}",
            query=f"current {kind} projection",
            seedIds=(seedId,),
            sourceSnapshotSetId=snapshotId,
            maxDepth=2,
            maxNodes=maxNodes,
            maxEdges=maxEdges,
        )
        first = compileBoundedProjection(spec, nodes, edges)
        second = compileBoundedProjection(spec, reversed(nodes), reversed(edges))
        repeatMatches += int(first.sceneHash == second.sceneHash)
        boundViolationCount += int(first.receipt.outputNodeCount > maxNodes or first.receipt.outputEdgeCount > maxEdges)
        seedLossCount += int(first.receipt.retainedSeedCount != first.receipt.seedCount)
        laneViolationCount += sum(
            edge.lane == "fact" and (not edge.assertionId or not edge.evidenceRefs) for edge in first.edges
        )
        records.append((nodes, edges, first))
        allEdges.extend(edges)
    laneCounts = Counter(edge.lane for edge in allEdges)
    return LiveProjectionReport(
        sourceSnapshotSetId=snapshotId,
        atlasInputNodes=len(records[0][0]),
        atlasInputEdges=len(records[0][1]),
        atlasOutputNodes=records[0][2].receipt.outputNodeCount,
        atlasOutputEdges=records[0][2].receipt.outputEdgeCount,
        industryInputNodes=len(records[1][0]),
        industryInputEdges=len(records[1][1]),
        industryOutputNodes=records[1][2].receipt.outputNodeCount,
        industryOutputEdges=records[1][2].receipt.outputEdgeCount,
        companyInputNodes=len(records[2][0]),
        companyInputEdges=len(records[2][1]),
        companyOutputNodes=records[2][2].receipt.outputNodeCount,
        companyOutputEdges=records[2][2].receipt.outputEdgeCount,
        totalFactEdges=laneCounts["fact"],
        totalCandidateEdges=laneCounts["candidate"],
        totalDerivedEdges=laneCounts["derived"],
        boundViolationCount=boundViolationCount,
        seedLossCount=seedLossCount,
        laneViolationCount=laneViolationCount,
        repeatedSceneHashMatches=repeatMatches,
        repeatedSceneHashTotal=len(adapted),
        liveReady=boundViolationCount == seedLossCount == laneViolationCount == 0 and repeatMatches == len(adapted),
    )


def main() -> int:
    """Current public map artifact 3종의 bounded projection report를 JSON으로 출력한다.

    Capabilities
        U0-P01의 atlas, industry, company hard bound와 deterministic hash를 재측정한다.

    AIContext
        AI 역할: Live artifact를 새 bake 없이 bounded scene으로 소비 가능한지 판정한다.

    Returns
        성공 시 0.

    Example
        ``python boundedProjection.py``

    Guide
        Stdout JSON을 원장에 기록하고 fact edge 0을 candidate 자동 승격으로 보정하지 않는다.

    When
        Map artifact 또는 compiler가 갱신된 뒤 실행한다.

    How
        :func:`inspectLiveProjection`을 호출해 세 scene 결과를 직렬화한다.

    Requires
        Network와 current public map artifact가 필요하다.

    See Also
        :func:`inspectLiveProjection`.

    Raises
        OSError: Remote artifact를 읽지 못할 때.
        ValueError: Artifact 또는 projection contract가 잘못됐을 때.
    """

    report = inspectLiveProjection()
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
