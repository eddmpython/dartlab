from __future__ import annotations

import json
from pathlib import Path

from tests._attempts.dartlabUniverse.spatial.community import CommunityCandidate
from tests._attempts.dartlabUniverse.spatial.communityLineage import compileCommunityLineage
from tests._attempts.dartlabUniverse.spatial.projectionState import compileSpatialProjection
from tests._attempts.dartlabUniverse.spatial.stability import evaluateProjectionStability
from tests._attempts.dartlabUniverse.spatialTestSupport import spatialFixture, spatialRequest


def _candidate(value: dict[str, object]) -> CommunityCandidate:
    members = tuple(str(item) for item in value["members"])
    return CommunityCandidate(
        2, str(value["semanticKey"]), None, members, tuple((item, 1) for item in members), "".join(members)
    )


def testIncrementalProjectionPinsExistingCoordinatesAndSelection() -> None:
    fixture = spatialFixture()
    priorRequest = spatialRequest(fixture, count=127)
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
        count=128,
        stabilityBaseProjectionId=prior.state.projectionStateId,
        selectedObjectIds=(selected,),
    )
    current = compileSpatialProjection(
        fixture.catalog,
        fixture.snapshot,
        fixture.graph.relations,
        request=currentRequest,
        statements=fixture.statements,
        priorState=prior.state,
    )
    report = evaluateProjectionStability(prior.state, current.state, selectedObjectIds=(selected,))
    assert report.passed
    assert report.coordinateDeterminism == 1.0
    assert report.normalizedDisplacementP95 <= 0.02
    assert report.clusterContinuity >= 0.98
    assert report.selectedObjectLossCount == 0


def testCommunityLineageRetainsAndSplitsDeterministically() -> None:
    path = Path(__file__).parent / "fixtures" / "projectionSmall.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    old, _events = compileCommunityLineage(
        tuple(_candidate(item) for item in fixture["old"]),
        projectionVersion="v1",
    )
    current, events = compileCommunityLineage(
        tuple(_candidate(item) for item in fixture["next"]),
        projectionVersion="v1",
        priorCommunities=old,
    )
    retained = {item.semanticKey: item for item in current}
    oldByKey = {item.semanticKey: item for item in old}
    assert retained["L2:ENTITY:alpha"].communityLogicalId == oldByKey["L2:ENTITY:alpha"].communityLogicalId
    assert retained["L2:DATA:beta"].lineageKind == "SPLIT_FROM"
    assert any(item.eventKind == "SPLIT_FROM" for item in events)
