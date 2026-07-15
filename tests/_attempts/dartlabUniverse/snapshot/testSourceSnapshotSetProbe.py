"""sourceSnapshotSetProbe의 canonical replay 경계를 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.snapshot import (
    SnapshotSource,
    assessReplayRequest,
    buildSourceSnapshotSet,
)


def fixtureSources() -> list[SnapshotSource]:
    """Canonical hash 검증용 source 두 개를 만든다.

    Args
        없음.

    Returns
        서로 다른 sourceId와 version을 가진 list.

    Example
        ``sources = fixtureSources()``

    Requires
        없음.

    Raises
        고정 literal만 사용하므로 예외를 발생시키지 않는다.
    """

    return [
        SnapshotSource(
            sourceId="map",
            origin="hfDataset",
            path="dataset@commit/map.json",
            versionOrEtag="hfCommit:c1;etag:e1",
            dataAsOf="2026-01-01T00:00:00Z",
            contentLength=100,
        ),
        SnapshotSource(
            sourceId="catalog",
            origin="runtimeCatalog",
            path="catalog",
            versionOrEtag="sha256:abc",
            payloadHash="sha256:abc",
            dataAsOf="2026-01-02T00:00:00Z",
        ),
    ]


def buildFixture(sources: list[SnapshotSource], createdAt: str = "2026-01-03T00:00:00Z"):
    """공통 catalog version으로 fixture snapshot을 만든다.

    Args
        sources: snapshot source list.
        createdAt: hash에서 제외될 관측 시각.

    Returns
        SourceSnapshotSet fixture.

    Example
        ``snapshot = buildFixture(fixtureSources())``

    Requires
        buildSourceSnapshotSet.

    Raises
        buildSourceSnapshotSet의 validation error를 그대로 전달한다.
    """

    return buildSourceSnapshotSet(
        sources,
        mapBuildId="build-1",
        capabilityCatalogVersion="sha256:abc",
        recipeCatalogVersion="sha256:def",
        createdAt=createdAt,
    )


def testSnapshotHashIgnoresOrderAndObservationMetadata() -> None:
    """입력 순서와 관측 metadata가 canonical identity를 바꾸지 않는다.

    Capabilities
        canonical hash의 순서, 시각, OS path 독립성을 회귀 검증한다.

    AIContext
        AI 역할: 동일 source set의 false mismatch를 막는다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 두 snapshotSetId의 일치를 검증한다.

    Guide
        source identity는 유지하고 비정체성 metadata만 바꾼다.

    When
        snapshot canonicalization을 변경할 때 실행한다.

    How
        순서와 metadata가 다른 두 fixture의 ID를 비교한다.

    Requires
        fixtureSources와 buildFixture.

    See Also
        :func:`buildSourceSnapshotSet`.

    Raises
        AssertionError: 비정체성 metadata가 hash에 들어갔을 때.
    """

    sources = fixtureSources()
    changedMetadata = [
        replace(sources[1], dataAsOf="2030-01-01T00:00:00Z", contentLength=999),
        replace(
            sources[0],
            path="dataset@commit\\map.json",
            dataAsOf=None,
            contentLength=None,
        ),
    ]
    first = buildFixture(sources)
    second = buildFixture(changedMetadata, createdAt="2035-01-01T00:00:00Z")
    assert first.snapshotSetId == second.snapshotSetId
    assert [source.sourceId for source in first.sources] == ["catalog", "map"]


def testSnapshotHashChangesWithAnySourceVersion() -> None:
    """Source 하나의 version 변화가 snapshot identity를 바꾼다.

    Capabilities
        source version 변화의 hash 민감도를 회귀 검증한다.

    AIContext
        AI 역할: 다른 source set의 false match를 막는다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 서로 다른 snapshotSetId를 검증한다.

    Guide
        한 source의 version만 바꾸고 나머지 입력은 고정한다.

    When
        canonical source field를 변경할 때 실행한다.

    How
        baseline과 changed fixture의 ID 불일치를 확인한다.

    Requires
        fixtureSources와 buildFixture.

    See Also
        :func:`buildSourceSnapshotSet`.

    Raises
        AssertionError: source version 변화가 hash에 반영되지 않을 때.
    """

    sources = fixtureSources()
    changed = [replace(sources[0], versionOrEtag="hfCommit:c2;etag:e2"), sources[1]]
    assert buildFixture(sources).snapshotSetId != buildFixture(changed).snapshotSetId


def testMissingVersionIsExplicitlyUnreplayable() -> None:
    """Version 결손을 current replay 성공처럼 표시하지 않는다.

    Capabilities
        missing source version의 fail-closed 정규화를 검증한다.

    AIContext
        AI 역할: 재현 불가 source를 성공으로 표시하지 못하게 한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 unreplayable source ID와 exact replay false를 검증한다.

    Guide
        versionOrEtag만 제거한 fixture를 사용한다.

    When
        replay status 또는 source validation을 변경할 때 실행한다.

    How
        normalized source와 snapshot summary를 함께 확인한다.

    Requires
        fixtureSources와 buildFixture.

    See Also
        :class:`SnapshotSource`.

    Raises
        AssertionError: missing version이 replayable로 남을 때.
    """

    sources = fixtureSources()
    sources[0] = replace(sources[0], versionOrEtag=None)
    snapshot = buildFixture(sources)
    assert snapshot.exactReplayReady is False
    assert snapshot.unreplayableSourceIds == ("map",)
    mapSource = next(source for source in snapshot.sources if source.sourceId == "map")
    assert mapSource.replayStatus == "unreplayable"
    assert mapSource.unreplayableReason == "missingSourceVersion"


def testPolicyReceiptDoesNotMasqueradeAsContentVersion() -> None:
    """Policy receipt 결손과 content version 결손을 서로 다른 gate로 보존한다.

    Capabilities
        content replay와 redistribution policy의 독립 판정을 검증한다.

    AIContext
        AI 역할: policy gap이 source identity 결과를 덮지 못하게 한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 exact replay와 receipt gap을 동시에 검증한다.

    Guide
        version은 채우고 receipt만 비운 fixture를 사용한다.

    When
        U0-P02 연계 필드나 replay summary를 변경할 때 실행한다.

    How
        exactReplayReady와 missing receipt 목록을 함께 확인한다.

    Requires
        fixtureSources와 buildFixture.

    See Also
        :func:`buildSourceSnapshotSet`.

    Raises
        AssertionError: policy 결손이 content replay 상태를 덮을 때.
    """

    snapshot = buildFixture(fixtureSources())
    assert snapshot.exactReplayReady is True
    assert snapshot.unreplayableSourceIds == ()
    assert snapshot.missingRedistributionReceiptSourceIds == ("catalog", "map")


def testDuplicateSourceIdIsRejected() -> None:
    """같은 sourceId 두 개가 canonical set에 들어가지 못하게 한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 duplicate source의 ValueError를 검증한다.

    Raises
        AssertionError: duplicate sourceId가 조용히 수용될 때.
    """

    source = fixtureSources()[0]
    with pytest.raises(ValueError, match="duplicate sourceId"):
        buildFixture([source, source])


def testLegacyBuildIdOnlyCannotClaimExactReplay() -> None:
    """Legacy map buildId만 있는 share를 current rerun으로 강등한다.

    Capabilities
        legacy share의 exact replay 오표시를 회귀 검증한다.

    AIContext
        AI 역할: map buildId와 전체 source identity를 구분한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 legacy replay assessment를 검증한다.

    Guide
        requestedSnapshotSetId 없이 legacyBuildId만 전달한다.

    When
        share URL compatibility 판정을 변경할 때 실행한다.

    How
        반환 mode와 reason code를 함께 검증한다.

    Requires
        assessReplayRequest와 replayable fixture.

    See Also
        :func:`assessReplayRequest`.

    Raises
        AssertionError: legacy buildId가 exact replay를 허용할 때.
    """

    snapshot = buildFixture(fixtureSources())
    assessment = assessReplayRequest(
        snapshot,
        requestedSnapshotSetId=None,
        legacyBuildId="build-1",
    )
    assert assessment.exactReplayAllowed is False
    assert assessment.mode == "currentRerun"
    assert assessment.reason == "legacyBuildIdOnly"


def testMatchingReplayStillRejectsUnreplayableSource() -> None:
    """Snapshot ID가 같아도 source 결손이 있으면 exact replay를 차단한다.

    Capabilities
        ID 일치보다 source replayability가 우선함을 회귀 검증한다.

    AIContext
        AI 역할: 식별 가능하지만 복원 불가능한 set을 차단한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 matching unavailable assessment를 검증한다.

    Guide
        missing version을 포함한 snapshot 자신의 ID로 요청한다.

    When
        replay admission 순서를 변경할 때 실행한다.

    How
        exactReplayAllowed, mode, reason을 모두 확인한다.

    Requires
        assessReplayRequest와 unreplayable fixture.

    See Also
        :func:`assessReplayRequest`.

    Raises
        AssertionError: unreplayable source가 exact로 표시될 때.
    """

    sources = fixtureSources()
    sources[0] = replace(sources[0], versionOrEtag=None)
    snapshot = buildFixture(sources)
    assessment = assessReplayRequest(
        snapshot,
        requestedSnapshotSetId=snapshot.snapshotSetId,
        legacyBuildId=snapshot.mapBuildId,
    )
    assert assessment.exactReplayAllowed is False
    assert assessment.mode == "unavailable"
    assert assessment.reason == "snapshotContainsUnreplayableSources"


def testMatchingReplayableSnapshotAllowsExactReplay() -> None:
    """Canonical ID와 모든 source version이 맞을 때만 exact replay를 허용한다.

    Capabilities
        complete source snapshot의 positive replay 경로를 회귀 검증한다.

    AIContext
        AI 역할: fail-closed 판정이 정상 exact replay까지 막지 않게 한다.

    Args
        없음.

    Returns
        없음.

    Example
        pytest가 exact replay assessment를 검증한다.

    Guide
        replayable fixture의 실제 snapshotSetId를 그대로 요청한다.

    When
        replay assessment의 positive branch를 변경할 때 실행한다.

    How
        exactReplay mode와 matched reason을 검증한다.

    Requires
        assessReplayRequest와 replayable fixture.

    See Also
        :func:`assessReplayRequest`.

    Raises
        AssertionError: 완전한 snapshot이 exact replay를 통과하지 못할 때.
    """

    snapshot = buildFixture(fixtureSources())
    assessment = assessReplayRequest(
        snapshot,
        requestedSnapshotSetId=snapshot.snapshotSetId,
        legacyBuildId=None,
    )
    assert assessment.exactReplayAllowed is True
    assert assessment.mode == "exactReplay"
    assert assessment.reason == "sourceSnapshotMatched"
