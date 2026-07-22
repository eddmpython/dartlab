"""Runtime-only scene tile hierarchy와 immutable envelope compiler."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from ..canonical import canonicalDigest
from ..ids import logicalId
from .contracts import (
    COORDINATE_SYSTEM_VERSION,
    LOD_POLICY_VERSION,
    SCENE_MANIFEST_SCHEMA_VERSION,
    SCENE_PAYLOAD_SCHEMA_VERSION,
    STYLE_SCHEMA_VERSION,
    Bounds3d,
    CommunityVersion,
    ProjectionRequest,
    ProjectionState,
    SceneEdge,
    SceneManifest,
    SceneNode,
    SceneProxy,
    SceneTile,
    SceneTileEnvelope,
)
from .digest import scenePayloadDigestAndSize
from .lod import LodCompilation


def _bounds(proxies: tuple[SceneProxy, ...], nodes: tuple[SceneNode, ...], halfExtent: int) -> Bounds3d:
    points = tuple((item.positionQ, item.radiusQ) for item in (*proxies, *nodes))
    if not points:
        return Bounds3d((-halfExtent, -halfExtent, -halfExtent), (halfExtent, halfExtent, halfExtent))
    minimum = tuple(min(position[index] - radius for position, radius in points) for index in range(3))
    maximum = tuple(max(position[index] + radius for position, radius in points) for index in range(3))
    return Bounds3d(minimum, maximum)  # type: ignore[arg-type]


def _origin(bounds: Bounds3d) -> tuple[int, int, int]:
    return tuple(round((bounds.minimumQ[index] + bounds.maximumQ[index]) / 2) for index in range(3))  # type: ignore[return-value]


def _tileId(projectionDigest: str, lodLevel: int, semanticKey: str) -> str:
    return logicalId("scene-tile", (projectionDigest, lodLevel, semanticKey))


def _buildTile(
    *,
    sceneId: str,
    state: ProjectionState,
    request: ProjectionRequest,
    tileId: str,
    parentTileId: str | None,
    childTileIds: tuple[str, ...],
    lodLevel: int,
    proxies: tuple[SceneProxy, ...],
    nodes: tuple[SceneNode, ...],
    edges: tuple[SceneEdge, ...],
) -> SceneTile:
    if len(proxies) + len(nodes) > request.budget.maxNodesPerTile or len(edges) > request.budget.maxEdgesPerTile:
        raise ValueError(f"scene tile element budget 초과 tile={tileId}")
    contentDigest, byteSize = scenePayloadDigestAndSize(proxies, nodes, edges)
    if byteSize > request.budget.maxTileBytes:
        raise ValueError(f"scene tile byte budget 초과 tile={tileId} bytes={byteSize}")
    bounds = _bounds(proxies, nodes, request.budget.rootHalfExtentQ)
    envelope = SceneTileEnvelope(
        sceneId=sceneId,
        snapshotId=state.snapshotId,
        projectionVersion=state.projectionVersion,
        projectionDigest=state.outputDigest,
        lodPolicyVersion=LOD_POLICY_VERSION,
        payloadSchemaVersion=SCENE_PAYLOAD_SCHEMA_VERSION,
        visibilityScopeDigest=state.visibilityScopeDigest,
        generation=request.generation,
        tileId=tileId,
        parentTileId=parentTileId,
        childTileIds=childTileIds,
        bounds3d=bounds,
        coordinateOriginQ=_origin(bounds),
        encoding="DU_MSGPACK_RUNTIME_V1",
        screenSpaceError=round(1024.0 / (2**lodLevel), 6),
        lodLevel=lodLevel,
        nodeCount=len(proxies) + len(nodes),
        edgeCount=len(edges),
        clusterSummaries=tuple(item.communityLogicalId for item in proxies),
        contentRef=f"runtime://{sceneId}/{tileId}",
        contentDigest=contentDigest,
        byteSize=byteSize,
        nextCursor=None,
    )
    return SceneTile(envelope, proxies, nodes, edges)


def compileSceneTiles(
    state: ProjectionState,
    communities: tuple[CommunityVersion, ...],
    lod: LodCompilation,
    request: ProjectionRequest,
    *,
    relationCount: int,
) -> tuple[SceneManifest, tuple[SceneTile, ...]]:
    """L0 root, L1 overview, L2 family, L3 object tile을 runtime memory에 만든다."""
    sceneId = logicalId(
        "scene",
        (state.snapshotId, state.outputDigest, state.visibilityScopeDigest, request.generation),
    )
    root = next(item for item in communities if item.level == 0)
    levelOne = tuple(item for item in communities if item.level == 1)
    levelTwo = tuple(item for item in communities if item.level == 2)
    childrenByParent = {}
    for item in levelTwo:
        childrenByParent.setdefault(item.parentCommunityLogicalId, []).append(item)
    rootTileId = _tileId(state.outputDigest, 0, root.communityLogicalId)
    overviewTileId = _tileId(state.outputDigest, 1, "OVERVIEW")
    clusterTileByCommunity = {
        item.communityLogicalId: _tileId(state.outputDigest, 3, item.communityLogicalId) for item in levelTwo
    }
    familyPages = {}
    clusterParentTile = {}
    pageSize = min(256, request.budget.maxNodesPerTile)
    for family in levelOne:
        children = tuple(
            sorted(childrenByParent.get(family.communityLogicalId, ()), key=lambda item: item.communityLogicalId)
        )
        pages = []
        for offset in range(0, len(children), pageSize):
            page = children[offset : offset + pageSize]
            pageId = _tileId(state.outputDigest, 2, f"{family.communityLogicalId}:{offset // pageSize}")
            pages.append((pageId, page))
            for cluster in page:
                clusterParentTile[cluster.communityLogicalId] = pageId
        familyPages[family.communityLogicalId] = tuple(pages)
    proxies = []
    for item in lod.proxies:
        community = next(value for value in communities if value.communityLogicalId == item.communityLogicalId)
        if community.level == 0:
            target = overviewTileId
        elif community.level == 1:
            target = familyPages[community.communityLogicalId][0][0]
        else:
            target = clusterTileByCommunity[community.communityLogicalId]
        proxies.append(replace(item, drillTargetTileId=target))
    proxyByCommunity = {item.communityLogicalId: item for item in proxies}
    nodeByCluster = {}
    for node in lod.nodes:
        nodeByCluster.setdefault(node.clusterId, []).append(node)
    levelOneEdges = tuple(item for item in lod.edges if item.lodLevel == 1)
    levelTwoEdges = tuple(item for item in lod.edges if item.lodLevel == 2)
    levelThreeEdges = tuple(item for item in lod.edges if item.lodLevel == 3)
    tiles = []
    tiles.append(
        _buildTile(
            sceneId=sceneId,
            state=state,
            request=request,
            tileId=rootTileId,
            parentTileId=None,
            childTileIds=(overviewTileId,),
            lodLevel=0,
            proxies=(proxyByCommunity[root.communityLogicalId],),
            nodes=(),
            edges=(),
        )
    )
    tiles.append(
        _buildTile(
            sceneId=sceneId,
            state=state,
            request=request,
            tileId=overviewTileId,
            parentTileId=rootTileId,
            childTileIds=tuple(pageId for item in levelOne for pageId, _page in familyPages[item.communityLogicalId]),
            lodLevel=1,
            proxies=tuple(proxyByCommunity[item.communityLogicalId] for item in levelOne),
            nodes=(),
            edges=levelOneEdges,
        )
    )
    for family in levelOne:
        for pageId, children in familyPages[family.communityLogicalId]:
            childIds = frozenset(item.communityLogicalId for item in children)
            familyEdges = tuple(item for item in levelTwoEdges if item.fromNodeId in childIds)
            tiles.append(
                _buildTile(
                    sceneId=sceneId,
                    state=state,
                    request=request,
                    tileId=pageId,
                    parentTileId=overviewTileId,
                    childTileIds=tuple(clusterTileByCommunity[item.communityLogicalId] for item in children),
                    lodLevel=2,
                    proxies=tuple(proxyByCommunity[item.communityLogicalId] for item in children),
                    nodes=(),
                    edges=familyEdges,
                )
            )
    clusterByObject = {item.targetId: item.clusterId for item in lod.nodes}
    internalEdgesByCluster: dict[str, list[SceneEdge]] = defaultdict(list)
    for edge in levelThreeEdges:
        fromCluster = clusterByObject.get(edge.fromNodeId)
        if fromCluster is not None and fromCluster == clusterByObject.get(edge.toNodeId):
            internalEdgesByCluster[fromCluster].append(edge)
    for cluster in levelTwo:
        members = tuple(sorted(nodeByCluster.get(cluster.communityLogicalId, ()), key=lambda item: item.nodeId))
        internalEdges = tuple(internalEdgesByCluster.get(cluster.communityLogicalId, ()))
        tiles.append(
            _buildTile(
                sceneId=sceneId,
                state=state,
                request=request,
                tileId=clusterTileByCommunity[cluster.communityLogicalId],
                parentTileId=clusterParentTile[cluster.communityLogicalId],
                childTileIds=(),
                lodLevel=3,
                proxies=(),
                nodes=members,
                edges=internalEdges,
            )
        )
    ordered = tuple(sorted(tiles, key=lambda item: (item.envelope.lodLevel, item.envelope.tileId)))
    if len(ordered) > request.budget.maxTiles:
        raise ValueError("scene tile count budget 초과")
    manifestBase = SceneManifest(
        schemaVersion=SCENE_MANIFEST_SCHEMA_VERSION,
        sceneId=sceneId,
        snapshotId=state.snapshotId,
        projectionVersion=state.projectionVersion,
        projectionDigest=state.outputDigest,
        visibilityScopeDigest=state.visibilityScopeDigest,
        generation=request.generation,
        coordinateSystem=COORDINATE_SYSTEM_VERSION,
        rootTileId=rootTileId,
        bounds=Bounds3d(
            (-request.budget.rootHalfExtentQ,) * 3,
            (request.budget.rootHalfExtentQ,) * 3,
        ),
        objectCount=len(lod.nodes),
        relationCount=relationCount,
        tileCount=len(ordered),
        lodPolicyVersion=LOD_POLICY_VERSION,
        payloadSchemaVersion=SCENE_PAYLOAD_SCHEMA_VERSION,
        styleSchemaVersion=STYLE_SCHEMA_VERSION,
        createdFrom=state.projectionStateId,
        digest="",
    )
    manifest = replace(manifestBase, digest=canonicalDigest(manifestBase))
    return manifest, ordered


def validateSceneTileGraph(
    manifest: SceneManifest,
    tiles: tuple[SceneTile, ...],
    *,
    verifyContent: bool = True,
) -> tuple[str, ...]:
    """Tile identity, parent advertisement, runtime-only content, digest를 fail-closed 검사한다."""
    failures = []
    tileById = {item.envelope.tileId: item for item in tiles}
    if len(tileById) != len(tiles) or manifest.rootTileId not in tileById or manifest.tileCount != len(tiles):
        failures.append("TILE_CARDINALITY_INVALID")
    for tile in tiles:
        envelope = tile.envelope
        if (
            envelope.sceneId != manifest.sceneId
            or envelope.snapshotId != manifest.snapshotId
            or envelope.projectionDigest != manifest.projectionDigest
            or envelope.visibilityScopeDigest != manifest.visibilityScopeDigest
            or envelope.generation != manifest.generation
        ):
            failures.append("TILE_MANIFEST_BINDING_INVALID")
        if not envelope.contentRef.startswith("runtime://"):
            failures.append("PERSISTENT_TILE_FORBIDDEN")
        if verifyContent:
            contentDigest, byteSize = scenePayloadDigestAndSize(tile.proxies, tile.nodes, tile.edges)
            if contentDigest != envelope.contentDigest or byteSize != envelope.byteSize:
                failures.append("TILE_CONTENT_DIGEST_INVALID")
        if envelope.parentTileId is None:
            if envelope.tileId != manifest.rootTileId:
                failures.append("TILE_ROOT_INVALID")
        else:
            parent = tileById.get(envelope.parentTileId)
            if parent is None or envelope.tileId not in parent.envelope.childTileIds:
                failures.append("TILE_PARENT_ADVERTISEMENT_INVALID")
        if any(child not in tileById for child in envelope.childTileIds):
            failures.append("TILE_CHILD_MISSING")
    return tuple(sorted(set(failures)))
