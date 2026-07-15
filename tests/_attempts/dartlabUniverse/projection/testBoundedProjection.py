"""boundedProjection의 hard bound, lane, determinism, omission contract를 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.projection import (
    ProjectionEdge,
    ProjectionNode,
    ProjectionSpec,
    adaptAtlas,
    adaptCompany,
    adaptIndustry,
    compileBoundedProjection,
)

SNAPSHOT_ID = "sha256:" + "a" * 64


def _node(index: int, *, lane: str = "candidate") -> ProjectionNode:
    return ProjectionNode(
        nodeId=f"n{index}",
        label=f"Node {index}",
        lane=lane,
        priority=float(100 - index),
        sourceKind="fixture",
        sourceRef=f"fixture:node:{index}",
    )


def _edge(
    index: int,
    source: int,
    target: int,
    *,
    lane: str = "candidate",
    priority: float | None = None,
) -> ProjectionEdge:
    kwargs = {}
    if lane == "fact":
        kwargs = {
            "assertionId": "assertion:" + f"{index + 1:064x}",
            "evidenceRefs": ("evidence:" + f"{index + 1:064x}",),
        }
    elif lane == "derived":
        kwargs = {"derivationRefs": (f"fixture:derive:{index}",)}
    elif lane == "scenario":
        kwargs = {"scenarioReceiptId": f"scenario:{index}"}
    return ProjectionEdge(
        edgeId=f"e{index}",
        sourceId=f"n{source}",
        targetId=f"n{target}",
        predicate="related",
        lane=lane,
        priority=float(priority if priority is not None else 100 - index),
        sourceRef=f"fixture:edge:{index}",
        **kwargs,
    )


def _spec(**changes) -> ProjectionSpec:
    values = {
        "projectionId": "fixture",
        "query": "bounded fixture",
        "seedIds": ("n0",),
        "sourceSnapshotSetId": SNAPSHOT_ID,
        "maxDepth": 3,
        "maxNodes": 5,
        "maxEdges": 5,
    }
    values.update(changes)
    return ProjectionSpec(**values)


def _fixture():
    nodes = tuple(_node(index) for index in range(8))
    edges = (
        _edge(0, 0, 1, lane="fact"),
        _edge(1, 0, 2),
        _edge(2, 1, 3, lane="derived"),
        _edge(3, 2, 4, lane="scenario"),
        _edge(4, 3, 5),
        _edge(5, 4, 6),
    )
    return nodes, edges


def _assertHardBoundsAndSeedRetention() -> None:
    nodes, edges = _fixture()
    scene = compileBoundedProjection(_spec(maxNodes=4, maxEdges=3), nodes, edges)
    assert len(scene.nodes) <= 4
    assert len(scene.edges) <= 3
    assert scene.nodes[0].nodeId == "n0"
    assert scene.receipt.retainedSeedCount == scene.receipt.seedCount == 1
    assert scene.receipt.omission.omittedNodeCount == 4
    assert scene.receipt.omission.omittedEdgeCount == 3


def _assertInputOrderDoesNotChangeSceneHash() -> None:
    nodes, edges = _fixture()
    first = compileBoundedProjection(_spec(), nodes, edges)
    second = compileBoundedProjection(_spec(), reversed(nodes), reversed(edges))
    assert first.sceneHash == second.sceneHash
    assert first.receipt == second.receipt


def _assertLaneIsolation() -> None:
    nodes, edges = _fixture()
    scene = compileBoundedProjection(_spec(), nodes, edges)
    assert {edge.edgeId: edge.lane for edge in scene.edges}["e1"] == "candidate"
    fact = next(edge for edge in scene.edges if edge.edgeId == "e0")
    assert fact.lane == "fact"
    assert fact.assertionId and fact.evidenceRefs


def _assertInvalidFactAndLaneProofFailClosed() -> None:
    nodes, edges = _fixture()
    invalidFact = replace(edges[1], lane="fact")
    with pytest.raises(ValueError, match="exact assertionId"):
        compileBoundedProjection(_spec(), nodes, (edges[0], invalidFact))
    with pytest.raises(ValueError, match="derivationRefs"):
        compileBoundedProjection(_spec(), nodes, (replace(edges[1], lane="derived"),))
    with pytest.raises(ValueError, match="scenarioReceiptId"):
        compileBoundedProjection(_spec(), nodes, (replace(edges[1], lane="scenario"),))


def _assertDepthAndOmissionReceipt() -> None:
    nodes, edges = _fixture()
    scene = compileBoundedProjection(_spec(maxDepth=1, maxNodes=8, maxEdges=10), nodes, edges)
    assert {node.nodeId for node in scene.nodes} == {"n0", "n1", "n2"}
    assert dict(scene.receipt.omission.edgeReasonCounts)["depthLimit"] == 2
    assert scene.receipt.maxDepthObserved == 1


def _assertNoDanglingEdgesUnderEdgeBudget() -> None:
    nodes, edges = _fixture()
    scene = compileBoundedProjection(_spec(maxNodes=8, maxEdges=1), nodes, edges)
    nodeIds = {node.nodeId for node in scene.nodes}
    assert len(scene.edges) == 1
    assert all(edge.sourceId in nodeIds and edge.targetId in nodeIds for edge in scene.edges)
    assert dict(scene.receipt.omission.edgeReasonCounts)["edgeBudget"] >= 1


def _assertSourceSnapshotChangesSceneIdentity() -> None:
    nodes, edges = _fixture()
    first = compileBoundedProjection(_spec(), nodes, edges)
    secondSpec = _spec(sourceSnapshotSetId="sha256:" + "b" * 64)
    second = compileBoundedProjection(secondSpec, nodes, edges)
    assert first.receipt.specHash != second.receipt.specHash
    assert first.sceneHash != second.sceneHash


def _assertArtifactAdaptersPreserveLanes() -> None:
    atlas = {
        "industries": [
            {"id": "a", "name": "A", "revenue": 2},
            {"id": "b", "name": "B", "revenue": 1},
        ],
        "flows": [{"fromIndustry": "a", "toIndustry": "b", "edgeCount": 3}],
    }
    atlasNodes, atlasEdges = adaptAtlas(atlas)
    assert len(atlasNodes) == 2 and atlasEdges[0].lane == "derived"
    industry = {
        "industryId": "a",
        "stages": [
            {
                "nodes": [
                    {"stockCode": "n0", "corpName": "N0", "revenue": 2},
                    {"stockCode": "n1", "corpName": "N1", "revenue": 1},
                ]
            }
        ],
        "unclassified": [],
        "edges": [{"from": "n0", "to": "n1", "type": "supplier", "confidence": 0.9}],
    }
    industryNodes, industryEdges = adaptIndustry(industry)
    assert len(industryNodes) == 2 and industryEdges[0].lane == "candidate"
    company = {
        "ego": {"stockCode": "n0", "corpName": "N0", "revenue": 2},
        "neighbors": [{"stockCode": "n1", "corpName": "N1", "revenue": 1}],
        "edges": [{"from": "n0", "to": "n1", "type": "supplier", "confidence": 0.9}],
    }
    companyNodes, companyEdges = adaptCompany(company)
    assert len(companyNodes) == 2 and companyEdges[0].lane == "candidate"


def testHardBoundsAndSeedRetention() -> None:
    """Node와 edge hard bound 안에서 seed가 항상 보존되는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Bound 초과, seed 손실 또는 omission count drift가 있을 때.
    """

    _assertHardBoundsAndSeedRetention()


def testInputOrderDoesNotChangeSceneHash() -> None:
    """같은 graph의 입력 순서가 logical scene hash를 바꾸지 않음을 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Projection이 input order에 의존할 때.
    """

    _assertInputOrderDoesNotChangeSceneHash()


def testLaneIsolation() -> None:
    """Candidate와 admitted fact lane이 scene에서 그대로 분리되는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Candidate가 fact로 이동하거나 fact proof가 소실될 때.
    """

    _assertLaneIsolation()


def testInvalidFactAndLaneProofFailClosed() -> None:
    """Fact, derived, scenario proof가 없을 때 compile을 거부하는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Lane admission proof 결손이 수용될 때.
    """

    _assertInvalidFactAndLaneProofFailClosed()


def testDepthAndOmissionReceipt() -> None:
    """Depth limit 밖 node와 edge가 receipt reason으로 남는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Depth omission 또는 observed depth가 틀릴 때.
    """

    _assertDepthAndOmissionReceipt()


def testNoDanglingEdgesUnderEdgeBudget() -> None:
    """Edge budget truncation 뒤 dangling edge가 생기지 않는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Selected edge endpoint 또는 omission reason이 잘못될 때.
    """

    _assertNoDanglingEdgesUnderEdgeBudget()


def testSourceSnapshotChangesSceneIdentity() -> None:
    """SourceSnapshotSet 변경이 spec과 scene identity에 반영되는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: 다른 source snapshot이 같은 scene identity를 만들 때.
    """

    _assertSourceSnapshotChangesSceneIdentity()


def testArtifactAdaptersPreserveLanes() -> None:
    """Atlas, industry, company adapter가 semantic lane을 보존하는지 검증한다.

    Example
        ``pytest testBoundedProjection.py``

    Raises
        AssertionError: Aggregate와 current relation lane이 혼합될 때.
    """

    _assertArtifactAdaptersPreserveLanes()
