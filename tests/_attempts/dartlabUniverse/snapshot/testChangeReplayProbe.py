"""changeReplayProbe의 이중 시간과 live readiness 경계를 검증한다."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import polars as pl
import pytest

from tests._attempts.dartlabUniverse.snapshot import (
    ReplayAssertion,
    ReplayCut,
    inspectDartReplayReadiness,
    replayChanges,
)

SNAPSHOT_SET_ID = "sha256:" + "a" * 64


def _assertion(
    assertionId: str,
    claimKey: str,
    revisionId: str,
    *,
    sourcePublishedAt: str,
    availableAt: str,
    validFrom: str = "2026-01-01T00:00:00Z",
    evidenceRefs: tuple[str, ...] = ("evidence:exact",),
    supersedesRevisionId: str = "",
    status: str = "observed",
    staleAfter: str = "",
) -> ReplayAssertion:
    return ReplayAssertion(
        assertionId=assertionId,
        claimKey=claimKey,
        revisionId=revisionId,
        subjectId="kr:dart:corp:00126380",
        predicate="reportsValue",
        status=status,
        sourcePublishedAt=sourcePublishedAt,
        availableAt=availableAt,
        validFrom=validFrom,
        evidenceRefs=evidenceRefs,
        supersedesRevisionId=supersedesRevisionId,
        literal={"value": revisionId, "unit": "KRW"},
        staleAfter=staleAfter,
    )


def _fixtureCuts() -> tuple[ReplayCut, ReplayCut]:
    return (
        ReplayCut(
            cutId="cutA",
            validAt="2026-01-15T00:00:00Z",
            knownAt="2026-01-15T00:00:00Z",
        ),
        ReplayCut(
            cutId="cutB",
            validAt="2026-02-15T00:00:00Z",
            knownAt="2026-02-20T00:00:00Z",
        ),
    )


def _fixtureHistory() -> list[ReplayAssertion]:
    return [
        _assertion(
            "assertion:corrected:1",
            "claim:corrected",
            "revision:corrected:1",
            sourcePublishedAt="2026-01-02T00:00:00Z",
            availableAt="2026-01-03T00:00:00Z",
            evidenceRefs=("evidence:corrected:before",),
        ),
        _assertion(
            "assertion:corrected:2",
            "claim:corrected",
            "revision:corrected:2",
            sourcePublishedAt="2026-02-01T00:00:00Z",
            availableAt="2026-02-02T00:00:00Z",
            supersedesRevisionId="revision:corrected:1",
            evidenceRefs=("evidence:corrected:after",),
        ),
        _assertion(
            "assertion:retracted:1",
            "claim:retracted",
            "revision:retracted:1",
            sourcePublishedAt="2026-01-04T00:00:00Z",
            availableAt="2026-01-05T00:00:00Z",
            evidenceRefs=("evidence:retracted:before",),
        ),
        _assertion(
            "assertion:retracted:2",
            "claim:retracted",
            "revision:retracted:2",
            sourcePublishedAt="2026-02-03T00:00:00Z",
            availableAt="2026-02-04T00:00:00Z",
            supersedesRevisionId="revision:retracted:1",
            status="retracted",
            evidenceRefs=("evidence:retracted:after",),
        ),
        _assertion(
            "assertion:newly-known:1",
            "claim:newly-known",
            "revision:newly-known:1",
            sourcePublishedAt="2026-02-05T00:00:00Z",
            availableAt="2026-02-06T00:00:00Z",
            evidenceRefs=("evidence:newly-known:after",),
        ),
        _assertion(
            "assertion:created:1",
            "claim:created",
            "revision:created:1",
            sourcePublishedAt="2026-02-07T00:00:00Z",
            availableAt="2026-02-08T00:00:00Z",
            validFrom="2026-02-01T00:00:00Z",
            evidenceRefs=("evidence:created:after",),
        ),
        _assertion(
            "assertion:stale:1",
            "claim:stale",
            "revision:stale:1",
            sourcePublishedAt="2026-01-06T00:00:00Z",
            availableAt="2026-01-07T00:00:00Z",
            staleAfter="2026-02-01T00:00:00Z",
            evidenceRefs=("evidence:stale",),
        ),
        _assertion(
            "assertion:future:1",
            "claim:future",
            "revision:future:1",
            sourcePublishedAt="2026-03-01T00:00:00Z",
            availableAt="2026-03-02T00:00:00Z",
            evidenceRefs=("evidence:future",),
        ),
    ]


def _report(history: list[ReplayAssertion] | None = None):
    beforeCut, afterCut = _fixtureCuts()
    return replayChanges(history or _fixtureHistory(), beforeCut, afterCut, SNAPSHOT_SET_ID)


def _assertFiveChangeTypesAndNoLookAhead() -> None:
    report = _report()
    assert dict(report.changeCounts) == {
        "corrected": 1,
        "created": 1,
        "newlyKnown": 1,
        "retracted": 1,
        "stale": 1,
    }
    assert report.lookAheadCount == 0
    assert report.revisionCount == report.preservedRevisionCount == 8
    assert report.revisionPreservationCoverage == 1.0
    assert report.beforeVisibleCount == 3
    assert report.afterVisibleCount == 4


def _assertEvidenceAndVintage() -> None:
    report = _report()
    assert report.evidenceBindingCoverage == 1.0
    assert all(change.evidenceComplete for change in report.changes)
    assert report.vintageRef.revisionPolicy == "asKnown"
    assert report.vintageRef.coverage == "asOfExact"
    assert report.vintageRef.contractHash == "a" * 64
    assert report.vintageRef.payloadHash == report.replayHash


def _assertOrderIndependentReplayHash() -> None:
    history = _fixtureHistory()
    assert _report(history).replayHash == _report(list(reversed(history))).replayHash


def _assertCutDoesNotRewriteAssertionIdentity() -> None:
    history = _fixtureHistory()
    beforeCut, afterCut = _fixtureCuts()
    laterCut = ReplayCut(
        cutId="cutC",
        validAt="2026-02-16T00:00:00Z",
        knownAt="2026-02-21T00:00:00Z",
    )
    first = replayChanges(history, beforeCut, afterCut, SNAPSHOT_SET_ID)
    second = replayChanges(history, beforeCut, laterCut, SNAPSHOT_SET_ID)
    firstCorrected = next(change for change in first.changes if change.changeType == "corrected")
    secondCorrected = next(change for change in second.changes if change.changeType == "corrected")
    assert firstCorrected.afterAssertionId == "assertion:corrected:2"
    assert secondCorrected.afterAssertionId == "assertion:corrected:2"


def _assertFutureRevisionExcluded() -> None:
    history = _fixtureHistory()
    report = _report(history)
    withoutFuture = _report(history[:-1])
    assert all(change.claimKey != "claim:future" for change in report.changes)
    assert "evidence:future" not in report.vintageRef.sourceRefs
    assert report.lookAheadCount == 0
    assert report.replayHash == withoutFuture.replayHash
    assert report.vintageRef.artifactHash == withoutFuture.vintageRef.artifactHash
    assert report.vintageRef.sourceRefs == withoutFuture.vintageRef.sourceRefs


def _assertMissingEvidenceVisible() -> None:
    history = _fixtureHistory()
    createdIndex = next(index for index, item in enumerate(history) if item.claimKey == "claim:created")
    history[createdIndex] = replace(history[createdIndex], evidenceRefs=())
    report = _report(history)
    assert report.evidenceBindingCoverage == pytest.approx(0.8)
    created = next(change for change in report.changes if change.changeType == "created")
    assert created.evidenceComplete is False


def _assertMalformedTimeRejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _assertion(
            "assertion:bad",
            "claim:bad",
            "revision:bad",
            sourcePublishedAt="2026-01-01T00:00:00",
            availableAt="2026-01-01T01:00:00Z",
        )
    with pytest.raises(ValueError, match="newer than availableAt"):
        _assertion(
            "assertion:bad-order",
            "claim:bad-order",
            "revision:bad-order",
            sourcePublishedAt="2026-01-02T00:00:00Z",
            availableAt="2026-01-01T00:00:00Z",
        )


def _completeFrame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "bsns_year": ["2025", "2025"],
            "reprt_code": ["11011", "11011"],
            "fs_div": ["CFS", "CFS"],
            "sj_div": ["BS", "BS"],
            "account_id": ["ifrs-full_Assets", "ifrs-full_Assets"],
            "rcept_no": ["20260101000001", "20260201000002"],
            "sourcePublishedAt": ["2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"],
            "availableAt": ["2026-01-01T01:00:00Z", "2026-02-01T01:00:00Z"],
            "revisionId": ["revision:1", "revision:2"],
            "rowKey": ["row:1", "row:2"],
        }
    )


def _assertDartReadinessFailsClosed(tmpPath: Path) -> None:
    readyPath = tmpPath / "ready"
    readyPath.mkdir()
    _completeFrame().write_parquet(readyPath / "000001.parquet")
    ready = inspectDartReplayReadiness(readyPath, maxFiles=1)
    assert ready.exactFieldCoverageReady is True
    assert ready.observedRevisionHistoryReady is True
    assert ready.exactReplayReady is True

    blockedPath = tmpPath / "blocked"
    blockedPath.mkdir()
    _completeFrame().drop("availableAt", "rowKey").write_parquet(blockedPath / "000001.parquet")
    blocked = inspectDartReplayReadiness(blockedPath, maxFiles=1)
    assert blocked.exactReplayReady is False
    assert dict(blocked.fieldFileCounts)["availableAt"] == 0
    assert dict(blocked.fieldFileCounts)["rowKey"] == 0
    assert blocked.representative is False


def testFiveChangeTypesAndNoLookAhead() -> None:
    """다섯 변화 유형, revision 보존, look-ahead 0을 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Synthetic replay fixture.

    Raises
        AssertionError: 변화 유형 또는 시간 경계가 깨졌을 때.
    """

    _assertFiveChangeTypesAndNoLookAhead()


def testEvidenceAndVintageAreBound() -> None:
    """모든 변화의 evidence와 exact as-known VintageRef를 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Synthetic replay fixture.

    Raises
        AssertionError: evidence 또는 VintageRef 결속이 깨졌을 때.
    """

    _assertEvidenceAndVintage()


def testReplayHashIgnoresInputOrder() -> None:
    """같은 history의 입력 순서가 replay hash를 바꾸지 않음을 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Synthetic replay fixture.

    Raises
        AssertionError: canonical replay hash가 순서에 의존할 때.
    """

    _assertOrderIndependentReplayHash()


def testCutDoesNotRewriteAssertionIdentity() -> None:
    """Query cutoff 변경이 assertionId를 다시 만들지 않음을 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Synthetic replay fixture.

    Raises
        AssertionError: cutoff가 assertion identity에 섞였을 때.
    """

    _assertCutDoesNotRewriteAssertionIdentity()


def testFutureRevisionIsExcluded() -> None:
    """After knownAt보다 늦은 revision이 diff에 보이지 않음을 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Future revision을 포함한 fixture.

    Raises
        AssertionError: 미래 filing이 현재 변화로 역주입됐을 때.
    """

    _assertFutureRevisionExcluded()


def testMissingEvidenceLowersCoverage() -> None:
    """증거 결손을 성공으로 숨기지 않고 coverage를 낮추는지 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Evidence가 제거된 created fixture.

    Raises
        AssertionError: evidence gap이 coverage에 반영되지 않을 때.
    """

    _assertMissingEvidenceVisible()


def testMalformedTimeIsRejected() -> None:
    """Naive timestamp와 잘못된 publication 순서를 거부하는지 검증한다.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        ReplayAssertion validation.

    Raises
        AssertionError: 잘못된 시간이 수용됐을 때.
    """

    _assertMalformedTimeRejected()


def testDartReadinessFailsClosed(tmp_path: Path) -> None:
    """DART exact field와 revision 결손의 fail-closed 판정을 검증한다.

    Args
        tmp_path: pytest temporary directory.

    Returns
        없음.

    Example
        ``pytest testChangeReplayProbe.py``

    Requires
        Polars parquet writer.

    Raises
        AssertionError: 결손 schema가 exact replay로 승인됐을 때.
    """

    _assertDartReadinessFailsClosed(tmp_path)
