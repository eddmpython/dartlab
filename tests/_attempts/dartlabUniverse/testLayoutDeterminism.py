from __future__ import annotations

import math

from tests._attempts.dartlabUniverse.spatial.projectionState import compileSpatialProjection
from tests._attempts.dartlabUniverse.spatialTestSupport import spatialFixture, spatialRequest


def testSameInputProducesByteIdenticalQuantizedCoordinates() -> None:
    fixture = spatialFixture()
    request = spatialRequest(fixture)
    first = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=request,
        statements=fixture.statements,
    )
    second = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=request,
        statements=fixture.statements,
    )
    assert first.state.coordinates == second.state.coordinates
    assert first.state.logicalCoordinateMapDigest == second.state.logicalCoordinateMapDigest
    assert first.state.outputDigest == second.state.outputDigest
    assert first.digest == second.digest


def testActiveLensNeverChangesBaseCoordinates() -> None:
    fixture = spatialFixture()
    first = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=spatialRequest(fixture, activeLens="finance"),
        statements=fixture.statements,
    )
    second = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=spatialRequest(fixture, activeLens="filing"),
        statements=fixture.statements,
    )
    assert first.state.coordinates == second.state.coordinates
    assert first.state.outputDigest == second.state.outputDigest


def testQuantizedCoordinatesKeepNodeCollisionClearance() -> None:
    fixture = spatialFixture()
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=spatialRequest(fixture),
        statements=fixture.statements,
    )
    coordinates = projection.state.coordinates
    for index, left in enumerate(coordinates):
        for right in coordinates[index + 1 :]:
            assert math.dist(left.positionQ, right.positionQ) >= (left.radiusQ + right.radiusQ) * 1.05
