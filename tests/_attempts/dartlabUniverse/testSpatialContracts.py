from __future__ import annotations

from dataclasses import replace

from tests._attempts.dartlabUniverse.spatial.projectionState import compileSpatialProjection
from tests._attempts.dartlabUniverse.spatial.tiles import validateSceneTileGraph
from tests._attempts.dartlabUniverse.spatialTestSupport import spatialFixture, spatialRequest


def testSceneManifestBindsRuntimeTilesAndStableTargets() -> None:
    fixture = spatialFixture()
    request = spatialRequest(fixture)
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=request,
        statements=fixture.statements,
    )
    assert projection.manifest.objectCount == len(request.objectScope)
    assert projection.manifest.tileCount == len(projection.tiles)
    assert validateSceneTileGraph(projection.manifest, projection.tiles) == ()
    assert all(item.envelope.contentRef.startswith("runtime://") for item in projection.tiles)
    assert len({node.pickId for tile in projection.tiles for node in tile.nodes}) == projection.manifest.objectCount
    assert (
        sum(item.positionQ[2] == 0 for item in projection.state.coordinates) / len(projection.state.coordinates) < 0.01
    )


def testSelectedObjectAndEveryObjectKeepL0ToL5DrillPath() -> None:
    fixture = spatialFixture()
    selected = spatialRequest(fixture).objectScope[0]
    request = spatialRequest(fixture, selectedObjectIds=(selected,))
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=request,
        statements=fixture.statements,
    )
    pathByObject = {item.targetId: item for item in projection.drillPaths if item.targetKind == "OBJECT"}
    assert set(pathByObject) == set(request.objectScope)
    assert tuple(level for level, _ref in pathByObject[selected].levelRefs) == ("L0", "L1", "L2", "L3", "L4", "L5")
    assert pathByObject[selected].evidenceRefs
    assert projection.selectedObjectIds == (selected,)
    statementPaths = {item.targetId: item for item in projection.drillPaths if item.targetKind == "STATEMENT"}
    assert {item.statementId for item in fixture.statements} <= set(statementPaths)
    assert all(path.evidenceRefs for path in statementPaths.values())


def testTileMutationAndScopeMutationAreRejected() -> None:
    fixture = spatialFixture()
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=spatialRequest(fixture),
        statements=fixture.statements,
    )
    first = projection.tiles[0]
    mutatedEnvelope = replace(first.envelope, visibilityScopeDigest="0" * 64)
    failures = validateSceneTileGraph(
        projection.manifest, (replace(first, envelope=mutatedEnvelope), *projection.tiles[1:])
    )
    assert "TILE_MANIFEST_BINDING_INVALID" in failures
    nodeTileIndex = next(index for index, tile in enumerate(projection.tiles) if tile.nodes)
    nodeTile = projection.tiles[nodeTileIndex]
    mutatedNode = replace(nodeTile.nodes[0], styleToken="mutated")
    mutatedTile = replace(nodeTile, nodes=(mutatedNode, *nodeTile.nodes[1:]))
    mutatedTiles = (*projection.tiles[:nodeTileIndex], mutatedTile, *projection.tiles[nodeTileIndex + 1 :])
    assert "TILE_CONTENT_DIGEST_INVALID" in validateSceneTileGraph(projection.manifest, mutatedTiles)
