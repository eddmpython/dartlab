from __future__ import annotations

from tests._attempts.dartlabUniverse.spatial.projectionState import compileSpatialProjection
from tests._attempts.dartlabUniverse.spatialTestSupport import spatialFixture, spatialRequest


def testSemanticLodPreservesEveryConservationDimension() -> None:
    fixture = spatialFixture()
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=spatialRequest(fixture),
        statements=fixture.statements,
    )
    report = projection.meaningReport
    assert report.passed
    assert report.meaningPreservation == 1.0
    assert report.assertionCount > 0
    assert report.passedAssertionCount == report.assertionCount
    assertedKinds = {item.assertionKind for item in report.assertions}
    assert {
        "PRIMARY_MEMBER_SET",
        "KIND_HISTOGRAM",
        "SOURCE_HISTOGRAM",
        "EPISTEMIC_HISTOGRAM",
        "VERIFICATION_HISTOGRAM",
        "PERIOD_RANGE",
        "STATEMENT_REF_SET",
        "EVIDENCE_REF_SET",
        "RELATION_REF_SET",
        "RELATION_TYPE_DIRECTION",
    } <= assertedKinds


def testEveryObjectHasExactlyOnePrimaryHomeCluster() -> None:
    fixture = spatialFixture()
    projection = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=spatialRequest(fixture),
        statements=fixture.statements,
    )
    coordinates = projection.state.coordinates
    levelTwoIds = {item.communityLogicalId for item in projection.state.communities if item.level == 2}
    assert len({item.objectId for item in coordinates}) == len(coordinates)
    assert all(item.clusterId in levelTwoIds for item in coordinates)
