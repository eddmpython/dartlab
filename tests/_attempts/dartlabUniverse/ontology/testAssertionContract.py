"""assertionContract의 identity, lineage, 이중 시간, evidence binding을 검증한다."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from dartlab.ai.contracts import Ref
from tests._attempts.dartlabUniverse.ontology import (
    AssertionSeed,
    buildAssertionLedger,
    compileAssertion,
    inspectGraphAssertionReadiness,
    queryAssertionLedger,
)

SNAPSHOT_SET_ID = "sha256:" + "a" * 64
SUBJECT_ID = "kr:dart:corp:00126380"
OBJECT_ID = "kr:dart:corp:00164779"


def _evidence(
    suffix: str,
    *,
    documentId: str,
    publishedAt: str,
    availableAt: str,
    locatorKind: str = "text",
) -> Ref:
    payload = {
        "docId": documentId,
        "sectionPath": "사업의 내용/주요 거래처",
        "sectionOrder": 17,
        "sourceRef": f"dart:panel:{documentId.rsplit(':', 1)[-1]}#section=17",
        "sourcePath": "dart/panel/00126380.parquet",
        "sourceVersion": "sha256:" + "1" * 64,
        "contentHash": "sha256:" + "2" * 64,
        "sourcePublishedAt": publishedAt,
        "availableAt": availableAt,
        "locatorKind": locatorKind,
    }
    if locatorKind == "text":
        payload.update({"charStart": 10, "charEnd": 31, "snippetHash": "sha256:" + "3" * 64})
        kind = "docRef"
    else:
        payload.update(
            {
                "rowIndex": 2,
                "headerHash": "sha256:" + "4" * 64,
                "rowHash": "sha256:" + "5" * 64,
            }
        )
        kind = "tableRef"
    digest = hashlib.sha256(suffix.encode("utf-8")).hexdigest()
    return Ref(
        id=f"evidence:{digest}",
        kind=kind,
        title=f"evidence {suffix}",
        source="DART",
        sourceType="external",
        payload=payload,
    )


def _seed(
    suffix: str,
    *,
    documentId: str = "kr:dart:filing:20260105000001",
    publishedAt: str = "2026-01-05T08:00:00Z",
    availableAt: str = "2026-01-05T08:03:00Z",
    validFrom: str = "2026-01-01T00:00:00Z",
    validTo: str = "",
    eventAt: str = "",
    status: str = "observed",
    supersedesAssertionId: str = "",
    evidenceRefs: tuple[Ref, ...] | None = None,
) -> AssertionSeed:
    refs = evidenceRefs or (
        _evidence(
            suffix,
            documentId=documentId,
            publishedAt=publishedAt,
            availableAt=availableAt,
        ),
    )
    return AssertionSeed(
        subjectId=SUBJECT_ID,
        predicate="suppliesTo",
        objectId=OBJECT_ID,
        direction="subjectToObject",
        status=status,
        sourceSnapshotSetId=SNAPSHOT_SET_ID,
        sourcePublishedAt=publishedAt,
        availableAt=availableAt,
        validFrom=validFrom,
        validTo=validTo,
        eventAt=eventAt,
        supersedesAssertionId=supersedesAssertionId,
        evidenceRefs=refs,
    )


def _assertRelationAndAssertionIdentityDiffer() -> None:
    first = compileAssertion(_seed("first"))
    second = compileAssertion(
        _seed(
            "second",
            documentId="kr:dart:filing:20260401000002",
            publishedAt="2026-04-01T08:00:00Z",
            availableAt="2026-04-01T08:04:00Z",
            validFrom="2026-04-01T00:00:00Z",
        )
    )
    assert first.relationId == second.relationId
    assert first.assertionId != second.assertionId


def _assertEvidenceOrderDoesNotChangeIdentity() -> None:
    firstRef = _evidence(
        "a",
        documentId="kr:dart:filing:20260105000001",
        publishedAt="2026-01-05T08:00:00Z",
        availableAt="2026-01-05T08:03:00Z",
    )
    secondRef = _evidence(
        "b",
        documentId="kr:dart:filing:20260105000001",
        publishedAt="2026-01-05T08:00:00Z",
        availableAt="2026-01-05T08:03:00Z",
        locatorKind="table",
    )
    first = compileAssertion(_seed("order", evidenceRefs=(firstRef, secondRef)))
    second = compileAssertion(_seed("order", evidenceRefs=(secondRef, firstRef)))
    assert first.assertionId == second.assertionId
    assert first.evidenceBindingHash == second.evidenceBindingHash


def _revisionLedger():
    original = compileAssertion(_seed("original"))
    corrected = compileAssertion(
        _seed(
            "corrected",
            documentId="kr:dart:filing:20260210000002",
            publishedAt="2026-02-10T08:00:00Z",
            availableAt="2026-02-10T08:05:00Z",
            status="corroborated",
            supersedesAssertionId=original.assertionId,
        )
    )
    return original, corrected, buildAssertionLedger([corrected, original])


def _assertAppendOnlyAsKnownQuery() -> None:
    original, corrected, ledger = _revisionLedger()
    assert ledger.historyCount == 2
    assert {item.assertionId for item in ledger.assertions} == {original.assertionId, corrected.assertionId}
    before = queryAssertionLedger(
        ledger,
        validAt="2026-01-20T00:00:00Z",
        knownAt="2026-01-20T00:00:00Z",
        sourceSnapshotSetId=SNAPSHOT_SET_ID,
    )
    after = queryAssertionLedger(
        ledger,
        validAt="2026-01-20T00:00:00Z",
        knownAt="2026-02-20T00:00:00Z",
        sourceSnapshotSetId=SNAPSHOT_SET_ID,
    )
    assert tuple(item.assertionId for item in before.assertions) == (original.assertionId,)
    assert tuple(item.assertionId for item in after.assertions) == (corrected.assertionId,)
    assert before.lookAheadCount == after.lookAheadCount == 0
    assert before.vintageRef.revisionPolicy == after.vintageRef.revisionPolicy == "asKnown"
    assert before.vintageRef.coverage == after.vintageRef.coverage == "asOfExact"


def _assertQueryCutoffDoesNotRewriteAssertionId() -> None:
    original, _, ledger = _revisionLedger()
    views = [
        queryAssertionLedger(
            ledger,
            validAt="2026-01-20T00:00:00Z",
            knownAt=knownAt,
            sourceSnapshotSetId=SNAPSHOT_SET_ID,
        )
        for knownAt in ("2026-01-20T00:00:00Z", "2026-01-21T00:00:00Z")
    ]
    assert all(view.assertions[0].assertionId == original.assertionId for view in views)
    assert views[0].viewHash != views[1].viewHash


def _assertFutureEffectiveEventIsAllowed() -> None:
    planned = compileAssertion(
        _seed(
            "planned",
            validFrom="2027-01-01T00:00:00Z",
            eventAt="2027-01-01T00:00:00Z",
        )
    )
    ledger = buildAssertionLedger([planned])
    view = queryAssertionLedger(
        ledger,
        validAt="2027-01-02T00:00:00Z",
        knownAt="2026-01-20T00:00:00Z",
        sourceSnapshotSetId=SNAPSHOT_SET_ID,
    )
    assert view.assertions[0].assertionId == planned.assertionId
    assert planned.eventAt > planned.availableAt


def _assertFutureKnowledgeDoesNotLeak() -> None:
    original = compileAssertion(_seed("known"))
    future = compileAssertion(
        _seed(
            "future",
            documentId="kr:dart:filing:20260301000003",
            publishedAt="2026-03-01T08:00:00Z",
            availableAt="2026-03-01T08:01:00Z",
            supersedesAssertionId=original.assertionId,
        )
    )
    beforeLedger = buildAssertionLedger([original])
    fullLedger = buildAssertionLedger([future, original])
    kwargs = {
        "validAt": "2026-01-20T00:00:00Z",
        "knownAt": "2026-01-20T00:00:00Z",
        "sourceSnapshotSetId": SNAPSHOT_SET_ID,
    }
    before = queryAssertionLedger(beforeLedger, **kwargs)
    full = queryAssertionLedger(fullLedger, **kwargs)
    assert before.viewHash == full.viewHash
    assert before.vintageRef.artifactHash == full.vintageRef.artifactHash
    assert future.evidenceRefs[0].id not in full.vintageRef.sourceRefs


def _assertMalformedEvidenceAndTimeFailClosed() -> None:
    with pytest.raises(ValueError, match="exact evidence"):
        compileAssertion(replace(_seed("missing"), evidenceRefs=()))
    ref = _evidence(
        "mutable",
        documentId="kr:dart:filing:20260105000001",
        publishedAt="2026-01-05T08:00:00Z",
        availableAt="2026-01-05T08:03:00Z",
    )
    mutableRef = replace(ref, payload={**ref.payload, "sourceVersion": "dartPanel.v1"})
    with pytest.raises(ValueError, match="sourceVersion"):
        compileAssertion(_seed("mutable", evidenceRefs=(mutableRef,)))
    with pytest.raises(ValueError, match="timezone-aware"):
        compileAssertion(_seed("naive", publishedAt="2026-01-05T08:00:00"))
    with pytest.raises(ValueError, match="newer than availableAt"):
        compileAssertion(
            _seed(
                "reverse",
                publishedAt="2026-01-06T08:00:00Z",
                availableAt="2026-01-05T08:00:00Z",
            )
        )


def _assertInvalidRevisionLineageFailsClosed() -> None:
    first = compileAssertion(_seed("lineage"))
    otherRelation = compileAssertion(
        replace(
            _seed(
                "other",
                documentId="kr:dart:filing:20260201000004",
                publishedAt="2026-02-01T08:00:00Z",
                availableAt="2026-02-01T08:01:00Z",
                supersedesAssertionId=first.assertionId,
            ),
            objectId="kr:dart:corp:00000001",
        )
    )
    with pytest.raises(ValueError, match="crosses relation"):
        buildAssertionLedger([first, otherRelation])


def _assertGraphAssertionReadinessCensus() -> None:
    complete = {
        "source": "a",
        "target": "b",
        "type": "suppliesTo",
        "assertionId": "assertion:1",
        "evidencePointerIds": ["evidence:1"],
        "sourcePublishedAt": "2026-01-01T00:00:00Z",
        "availableAt": "2026-01-01T00:01:00Z",
        "validFrom": "2026-01-01T00:00:00Z",
        "status": "observed",
    }
    payload = {
        "version": "fixture",
        "links": [complete, {"source": "b", "target": "b", "type": "peer"}],
    }
    census = inspectGraphAssertionReadiness(payload)
    assert census.edgeCount == census.uniqueRelationCandidateCount == 2
    assert census.selfLoopCount == 1
    assert census.assertionReadyCount == 1
    assert census.assertionIdCount == census.exactEvidenceCount == 1
    assert census.liveReady is False


def testRelationAndAssertionIdentityDiffer() -> None:
    """같은 relation의 다른 filing과 period가 다른 assertion ID를 만드는지 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Relation과 assertion identity가 혼합될 때.
    """

    _assertRelationAndAssertionIdentityDiffer()


def testEvidenceOrderDoesNotChangeIdentity() -> None:
    """Evidence 입력 순서가 assertion ID와 binding hash를 바꾸지 않는지 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Canonical evidence identity가 입력 순서에 의존할 때.
    """

    _assertEvidenceOrderDoesNotChangeIdentity()


def testAppendOnlyAsKnownQuery() -> None:
    """Correction 전후 assertion history와 as-known view를 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: History가 덮어써지거나 correction이 과거에 역주입될 때.
    """

    _assertAppendOnlyAsKnownQuery()


def testQueryCutoffDoesNotRewriteAssertionId() -> None:
    """KnownAt query cutoff 변경이 assertion ID를 다시 만들지 않음을 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Query metadata가 assertion identity에 섞일 때.
    """

    _assertQueryCutoffDoesNotRewriteAssertionId()


def testFutureEffectiveEventIsAllowed() -> None:
    """AvailableAt보다 미래인 validFrom과 eventAt이 허용되는지 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Future effective assertion이 잘못 차단될 때.
    """

    _assertFutureEffectiveEventIsAllowed()


def testFutureKnowledgeDoesNotLeak() -> None:
    """KnownAt 이후 revision이 view hash와 VintageRef에 들어오지 않음을 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Future source metadata가 과거 view에 누출될 때.
    """

    _assertFutureKnowledgeDoesNotLeak()


def testMalformedEvidenceAndTimeFailClosed() -> None:
    """Missing evidence, mutable version, malformed time을 거부하는지 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Incomplete assertion seed가 수용될 때.
    """

    _assertMalformedEvidenceAndTimeFailClosed()


def testInvalidRevisionLineageFailsClosed() -> None:
    """다른 relation으로 넘어가는 correction lineage를 거부하는지 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Cross-relation supersedes가 수용될 때.
    """

    _assertInvalidRevisionLineageFailsClosed()


def testGraphAssertionReadinessCensus() -> None:
    """Current edge schema census가 partial assertion을 ready로 세지 않는지 검증한다.

    Example
        ``pytest testAssertionContract.py``

    Raises
        AssertionError: Field 논리곱과 self-loop blocker가 깨질 때.
    """

    _assertGraphAssertionReadinessCensus()
