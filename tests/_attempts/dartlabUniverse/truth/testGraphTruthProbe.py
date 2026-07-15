"""graphTruthProbe의 deterministic admission 경계를 검증한다."""

from __future__ import annotations

import pytest

from tests._attempts.dartlabUniverse import inspectGraphTruth


def fixtureGraph() -> dict:
    """작은 graph truth fixture를 만든다.

    Args
        없음.

    Returns
        nodes와 links를 가진 ecosystem 형태의 dict.

    Example
        ``payload = fixtureGraph()``

    Raises
        고정 literal만 사용하므로 예외를 발생시키지 않는다.
    """

    return {
        "version": "fixture-v1",
        "nodes": [
            {"id": "a", "label": "Alpha"},
            {"id": "b", "label": "Beta"},
            {"id": "oci", "label": "OCI"},
            {"id": "isolated", "label": "Isolated"},
        ],
        "links": [
            {"source": "a", "target": "b", "type": "supplier", "source_tag": "panel_text"},
            {
                "source": "b",
                "target": "a",
                "type": "customer",
                "source_tag": "panel_table",
                "sourceRef": "kr:dart:filing:1",
                "availableAt": "2026-01-01T00:00:00Z",
            },
            {"source": "oci", "target": "a", "type": "affiliate", "source_tag": "panel_text"},
            {"source": "oci", "target": "oci", "type": "affiliate", "source_tag": "panel_text"},
            {"source": "a", "target": "b", "type": "supplier", "source_tag": "network"},
        ],
    }


def testGraphTruthReportSeparatesCandidateFromObservedEligibleEdges() -> None:
    """Source와 시간이 있는 edge만 observed 적격으로 센다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 fixture report의 admission count를 검증한다.

    Raises
        AssertionError: fact admission 또는 anomaly count가 바뀌었을 때.
    """

    report = inspectGraphTruth(fixtureGraph())
    assert report.edgeCount == 5
    assert report.exactSourceRefEdgeCount == 1
    assert report.exactAvailableAtEdgeCount == 1
    assert report.observedEligibleEdgeCount == 1
    assert report.selfLoopCount == 1
    assert report.incidentEdgeCount == 2
    assert report.isolatedNodeCount == 1
    assert report.duplicatePresentationEdgeCount == 1


def testGraphTruthReportRejectsMalformedEdges() -> None:
    """Predicate가 없는 edge를 조용히 수용하지 않는다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 malformed edge의 ValueError를 검증한다.

    Raises
        AssertionError: malformed edge가 오류 없이 통과할 때.
    """

    payload = fixtureGraph()
    payload["links"] = [{"source": "a", "target": "b"}]
    with pytest.raises(ValueError, match="source, target, and type"):
        inspectGraphTruth(payload)
