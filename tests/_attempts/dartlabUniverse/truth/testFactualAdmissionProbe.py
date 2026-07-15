"""factualAdmissionProbe의 fail-closed factual admission을 검증한다."""

from __future__ import annotations

import pytest

from tests._attempts.dartlabUniverse import inspectFactualAdmission


def admittedEdge(**overrides: object) -> dict[str, object]:
    """모든 factual field를 가진 edge fixture를 만든다.

    Args
        overrides: 기본 edge를 덮을 필드.

    Returns
        factual admission 기본 edge.

    Example
        ``edge = admittedEdge(validFrom="2027-01-01")``

    Raises
        고정 dict 조합이므로 예외를 발생시키지 않는다.
    """

    edge: dict[str, object] = {
        "source": "a",
        "target": "b",
        "type": "suppliesTo",
        "source_tag": "panel_text",
        "sourceRef": "kr:dart:filing:202601010001",
        "rceptNo": "202601010001",
        "sectionPath": "III. 사업의 내용 > 원재료",
        "charStart": 10,
        "charEnd": 32,
        "directionStatus": "verified",
        "sourcePublishedAt": "2026-01-01T09:00:00+09:00",
        "availableAt": "2026-01-01T09:05:00+09:00",
        "validFrom": "2026-01-01",
        "validTo": None,
        "redistributionReceiptId": "policy:dart:v1",
        "status": "observed",
    }
    edge.update(overrides)
    return edge


def fixturePayload() -> dict[str, object]:
    """admission 성공과 실패 경계를 가진 payload를 만든다.

    Args
        없음.

    Returns
        여섯 edge의 ecosystem payload.

    Example
        ``payload = fixturePayload()``

    Raises
        고정 literal만 사용하므로 예외를 발생시키지 않는다.
    """

    return {
        "version": "fixture-v2",
        "nodes": [],
        "links": [
            admittedEdge(),
            admittedEdge(source="b", target="c", validFrom="2027-01-01"),
            admittedEdge(source="c", target="d", sectionPath=None),
            admittedEdge(
                source="d",
                target="e",
                sourcePublishedAt="2026-01-02T09:00:00+09:00",
                availableAt="2026-01-01T09:00:00+09:00",
            ),
            admittedEdge(source="e", target="e"),
            admittedEdge(source="f", target="g", status="candidate"),
        ],
    }


def testFactualAdmissionRequiresEveryEvidenceTimeAndPolicyField() -> None:
    """모든 factual field와 시간 검증을 동시에 요구한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 admitted edge 2건과 reason을 확인한다.

    Raises
        AssertionError: admission policy가 느슨해졌을 때.
    """

    report = inspectFactualAdmission(fixturePayload())
    assert report.edgeCount == 6
    assert report.admittedEdgeCount == 2
    assert report.stableSourceRefCount == 6
    assert report.sectionPathCount == 5
    assert report.invalidSourceTimeCount == 1
    assert report.selfLoopCount == 1
    assert report.rejectionReasonCounts == {
        "invalidSourceTime": 1,
        "missingSectionPath": 1,
        "selfLoop": 1,
        "statusNotObserved": 1,
    }
    assert report.predicateAdmissionCounts == {"suppliesTo": 2}
    assert report.sourceTagAdmissionCounts == {"panel_text": 2}


def testFactualAdmissionAllowsFutureEffectiveDate() -> None:
    """미리 공시된 미래 효력일을 시간 오류로 차단하지 않는다.

    Args
        없음.

    Returns
        없음.

    Example
        availableAt 뒤의 validFrom이 admitted인지 검증한다.

    Raises
        AssertionError: 잘못된 eventAt 부등식이 재도입될 때.
    """

    payload = {"version": "future-validity", "nodes": [], "links": [admittedEdge(validFrom="2027-01-01")]}
    report = inspectFactualAdmission(payload)
    assert report.invalidSourceTimeCount == 0
    assert report.invalidValidityCount == 0
    assert report.admittedEdgeCount == 1


def testFactualAdmissionRejectsMalformedEdges() -> None:
    """presentation identity가 없는 edge를 조용히 수용하지 않는다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 missing type의 ValueError를 확인한다.

    Raises
        AssertionError: malformed edge가 통과할 때.
    """

    with pytest.raises(ValueError, match="source, target, and type"):
        inspectFactualAdmission({"version": "bad", "nodes": [], "links": [{"source": "a", "target": "b"}]})
