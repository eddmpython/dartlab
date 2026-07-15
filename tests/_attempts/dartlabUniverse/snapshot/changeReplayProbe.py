"""Universe 변화 재생의 이중 시간, revision, evidence 계약을 검증한다.

Capabilities
    append-only assertion history를 두 replay cut에서 독립 계산하고 다섯 변화 유형을 만든다.

AIContext
    AI 역할: 현재값의 과거 역주입 없이 변화 우주의 exact as-known 가능성을 판정한다.

Guide
    synthetic contract 결과와 DART deterministic schema sample의 live readiness를 분리한다.

When
    U0-W01 변화 재생을 검증하거나 source schema drift를 다시 측정할 때 사용한다.

How
    :func:`replayChanges`로 fixture를 검증하고 :func:`inspectDartReplayReadiness`로 live gap을 센서스한다.

Requires
    production VintageRef와 live census 실행 시 Polars 및 local DART finance parquet가 필요하다.

Raises
    ValueError: timestamp, revision chain, snapshot identity 또는 assertion 계약이 잘못됐을 때.

Example
    ``report = replayChanges(assertions, beforeCut, afterCut, snapshotSetId)``

See Also
    :mod:`tests._attempts.dartlabUniverse.snapshot.sourceSnapshotSetProbe`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from dartlab.simulate.vintage import (
    VintageRef,
    canonicalPayloadHash,
    isExactAsKnown,
    validateVintageRef,
)

ASSERTION_STATUSES = {"observed", "corroborated", "disputed", "retracted"}
CHANGE_TYPES = {"created", "corrected", "retracted", "newlyKnown", "stale"}
EXACT_REPLAY_FIELDS = (
    "rcept_no",
    "sourcePublishedAt",
    "availableAt",
    "revisionId",
    "rowKey",
)
REVISION_GROUP_FIELDS = ("bsns_year", "reprt_code", "fs_div", "sj_div", "account_id")


def _parseTimestamp(value: str, label: str) -> datetime:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC)


def _timestampText(value: str, label: str) -> str:
    return _parseTimestamp(value, label).isoformat().replace("+00:00", "Z")


def _snapshotContractHash(snapshotSetId: str) -> str:
    digest = snapshotSetId.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest.lower()):
        raise ValueError("snapshotSetId must contain a SHA-256 digest")
    return digest.lower()


@dataclass(frozen=True)
class ReplayCut:
    """변화 재생의 효력 시점과 지식 시점을 함께 고정한다."""

    cutId: str
    validAt: str
    knownAt: str

    def __post_init__(self) -> None:
        if not self.cutId:
            raise ValueError("cutId is required")
        object.__setattr__(self, "validAt", _timestampText(self.validAt, "validAt"))
        object.__setattr__(self, "knownAt", _timestampText(self.knownAt, "knownAt"))


@dataclass(frozen=True)
class ReplayAssertion:
    """Query cutoff와 독립적인 한 claim revision과 exact evidence를 보존한다."""

    assertionId: str
    claimKey: str
    revisionId: str
    subjectId: str
    predicate: str
    status: str
    sourcePublishedAt: str
    availableAt: str
    validFrom: str
    evidenceRefs: tuple[str, ...]
    supersedesRevisionId: str = ""
    objectId: str = ""
    literal: Any = None
    validTo: str = ""
    staleAfter: str = ""

    def __post_init__(self) -> None:
        identityValues = (
            self.assertionId,
            self.claimKey,
            self.revisionId,
            self.subjectId,
            self.predicate,
        )
        if not all(identityValues):
            raise ValueError("assertion identity fields are incomplete")
        if self.status not in ASSERTION_STATUSES:
            raise ValueError(f"unsupported assertion status: {self.status}")
        if bool(self.objectId) == (self.literal is not None):
            raise ValueError("assertion must have exactly one objectId or literal")

        sourcePublishedAt = _timestampText(self.sourcePublishedAt, "sourcePublishedAt")
        availableAt = _timestampText(self.availableAt, "availableAt")
        validFrom = _timestampText(self.validFrom, "validFrom")
        if _parseTimestamp(sourcePublishedAt, "sourcePublishedAt") > _parseTimestamp(availableAt, "availableAt"):
            raise ValueError("sourcePublishedAt cannot be newer than availableAt")

        validTo = _timestampText(self.validTo, "validTo") if self.validTo else ""
        if validTo and _parseTimestamp(validFrom, "validFrom") > _parseTimestamp(validTo, "validTo"):
            raise ValueError("validFrom cannot be newer than validTo")
        staleAfter = _timestampText(self.staleAfter, "staleAfter") if self.staleAfter else ""
        evidenceRefs = tuple(sorted(set(self.evidenceRefs)))
        if any(not reference for reference in evidenceRefs):
            raise ValueError("evidenceRefs cannot contain an empty reference")

        object.__setattr__(self, "sourcePublishedAt", sourcePublishedAt)
        object.__setattr__(self, "availableAt", availableAt)
        object.__setattr__(self, "validFrom", validFrom)
        object.__setattr__(self, "validTo", validTo)
        object.__setattr__(self, "staleAfter", staleAfter)
        object.__setattr__(self, "evidenceRefs", evidenceRefs)


@dataclass(frozen=True)
class ReplayChange:
    """두 replay cut 사이의 변화와 before, after evidence를 결속한다."""

    changeId: str
    changeType: str
    claimKey: str
    beforeAssertionId: str
    afterAssertionId: str
    beforeEvidenceRefs: tuple[str, ...]
    afterEvidenceRefs: tuple[str, ...]
    evidenceComplete: bool


@dataclass(frozen=True)
class ChangeReplayReport:
    """변화 diff, 보존율, 무선견성, evidence coverage와 VintageRef를 함께 반환한다."""

    snapshotSetId: str
    beforeCut: ReplayCut
    afterCut: ReplayCut
    revisionCount: int
    preservedRevisionCount: int
    revisionPreservationCoverage: float
    beforeVisibleCount: int
    afterVisibleCount: int
    changeCounts: tuple[tuple[str, int], ...]
    lookAheadCount: int
    evidenceBindingCoverage: float
    replayHash: str
    changes: tuple[ReplayChange, ...]
    vintageRef: VintageRef

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화가 가능한 변화 재생 report를 반환한다.

        Returns
            Dataclass와 tuple을 JSON compatible mapping으로 바꾼 값.

        Example
            ``payload = report.toDict()``

        Requires
            Dataclass fields가 canonical scalar와 collection만 포함해야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 json encoder가 발생시킬 수 있다.
        """

        return asdict(self)


@dataclass(frozen=True)
class DartReplayReadinessReport:
    """Local DART finance deterministic schema sample의 exact replay 준비도를 기록한다."""

    sourcePath: str
    samplePolicy: str
    representative: bool
    requestedFileCount: int
    fileCount: int
    rowCount: int
    fieldFileCounts: tuple[tuple[str, int], ...]
    revisionGroupCount: int
    exactFieldCoverageReady: bool
    observedRevisionHistoryReady: bool
    exactReplayReady: bool
    gapReasons: tuple[str, ...]

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화가 가능한 DART readiness report를 반환한다.

        Returns
            Census 결과의 JSON compatible mapping.

        Example
            ``payload = report.toDict()``

        Requires
            Dataclass fields가 canonical scalar와 collection만 포함해야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 json encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def _assertionPayload(assertion: ReplayAssertion) -> dict[str, Any]:
    return asdict(assertion)


def _cutPayload(cut: ReplayCut) -> dict[str, str]:
    return asdict(cut)


def _coversValidAt(assertion: ReplayAssertion, cut: ReplayCut) -> bool:
    validAt = _parseTimestamp(cut.validAt, "validAt")
    if _parseTimestamp(assertion.validFrom, "validFrom") > validAt:
        return False
    return not assertion.validTo or validAt < _parseTimestamp(assertion.validTo, "validTo")


def _statesAt(
    assertions: tuple[ReplayAssertion, ...],
    cut: ReplayCut,
) -> dict[str, ReplayAssertion]:
    knownAt = _parseTimestamp(cut.knownAt, "knownAt")
    states: dict[str, ReplayAssertion] = {}
    for assertion in assertions:
        if _parseTimestamp(assertion.availableAt, "availableAt") > knownAt or not _coversValidAt(assertion, cut):
            continue
        previous = states.get(assertion.claimKey)
        ordering = (assertion.availableAt, assertion.sourcePublishedAt, assertion.revisionId)
        previousOrdering = (previous.availableAt, previous.sourcePublishedAt, previous.revisionId) if previous else None
        if previousOrdering is None or ordering > previousOrdering:
            states[assertion.claimKey] = assertion
    return states


def _validateHistory(assertions: tuple[ReplayAssertion, ...]) -> None:
    byRevision: dict[str, ReplayAssertion] = {}
    for assertion in assertions:
        if assertion.revisionId in byRevision:
            raise ValueError(f"duplicate revisionId: {assertion.revisionId}")
        byRevision[assertion.revisionId] = assertion

    for assertion in assertions:
        if not assertion.supersedesRevisionId:
            continue
        previous = byRevision.get(assertion.supersedesRevisionId)
        if previous is None:
            raise ValueError(f"missing superseded revision: {assertion.supersedesRevisionId}")
        if previous.claimKey != assertion.claimKey:
            raise ValueError("revision cannot supersede another claimKey")
        if _parseTimestamp(previous.availableAt, "availableAt") > _parseTimestamp(assertion.availableAt, "availableAt"):
            raise ValueError("revision cannot supersede a later available revision")


def _evidenceComplete(
    changeType: str,
    before: ReplayAssertion | None,
    after: ReplayAssertion | None,
) -> bool:
    beforeEvidence = bool(before and before.evidenceRefs)
    afterEvidence = bool(after and after.evidenceRefs)
    if changeType in {"created", "newlyKnown"}:
        return afterEvidence
    return beforeEvidence and afterEvidence


def _buildChange(
    changeType: str,
    claimKey: str,
    before: ReplayAssertion | None,
    after: ReplayAssertion | None,
) -> ReplayChange:
    beforeEvidenceRefs = before.evidenceRefs if before else ()
    afterEvidenceRefs = after.evidenceRefs if after else ()
    payload = {
        "changeType": changeType,
        "claimKey": claimKey,
        "beforeAssertionId": before.assertionId if before else "",
        "afterAssertionId": after.assertionId if after else "",
        "beforeEvidenceRefs": beforeEvidenceRefs,
        "afterEvidenceRefs": afterEvidenceRefs,
    }
    return ReplayChange(
        changeId=canonicalPayloadHash(payload),
        changeType=changeType,
        claimKey=claimKey,
        beforeAssertionId=payload["beforeAssertionId"],
        afterAssertionId=payload["afterAssertionId"],
        beforeEvidenceRefs=beforeEvidenceRefs,
        afterEvidenceRefs=afterEvidenceRefs,
        evidenceComplete=_evidenceComplete(changeType, before, after),
    )


def _classifyChanges(
    assertions: tuple[ReplayAssertion, ...],
    beforeCut: ReplayCut,
    afterCut: ReplayCut,
) -> tuple[tuple[ReplayChange, ...], dict[str, ReplayAssertion], dict[str, ReplayAssertion]]:
    beforeStates = _statesAt(assertions, beforeCut)
    afterStates = _statesAt(assertions, afterCut)
    changes: list[ReplayChange] = []
    beforeValidAt = _parseTimestamp(beforeCut.validAt, "validAt")
    beforeKnownAt = _parseTimestamp(beforeCut.knownAt, "knownAt")
    afterKnownAt = _parseTimestamp(afterCut.knownAt, "knownAt")

    for claimKey in sorted(set(beforeStates) | set(afterStates)):
        before = beforeStates.get(claimKey)
        after = afterStates.get(claimKey)
        beforeActive = before is not None and before.status != "retracted"
        afterActive = after is not None and after.status != "retracted"

        changeType = ""
        if beforeActive and afterActive and before.assertionId != after.assertionId:
            changeType = "corrected"
        elif beforeActive and not afterActive:
            changeType = "retracted"
        elif not beforeActive and afterActive:
            changeType = "newlyKnown" if _parseTimestamp(after.validFrom, "validFrom") <= beforeValidAt else "created"
        elif beforeActive and afterActive and before.assertionId == after.assertionId and after.staleAfter:
            staleAfter = _parseTimestamp(after.staleAfter, "staleAfter")
            if beforeKnownAt < staleAfter <= afterKnownAt:
                changeType = "stale"

        if changeType:
            changes.append(_buildChange(changeType, claimKey, before, after))
    return tuple(changes), beforeStates, afterStates


def replayChanges(
    assertions: Iterable[ReplayAssertion],
    beforeCut: ReplayCut,
    afterCut: ReplayCut,
    snapshotSetId: str,
) -> ChangeReplayReport:
    """Append-only assertion history를 두 cutoff에서 exact as-known diff로 재생한다.

    Capabilities
        created, corrected, retracted, newlyKnown, stale를 결정론적으로 분류하고 VintageRef를 결속한다.

    AIContext
        AI 역할: query cutoff가 assertion identity를 바꾸거나 미래 revision이 과거에 보이는 오류를 차단한다.

    Args
        assertions: 모든 revision을 보존한 assertion iterable.
        beforeCut: 비교 전 validAt과 knownAt.
        afterCut: 비교 후 validAt과 knownAt.
        snapshotSetId: U0-S01에서 만든 canonical source snapshot identity.

    Returns
        diff, coverage, hash와 exact as-known VintageRef를 가진 report.

    Example
        ``report = replayChanges(history, cutA, cutB, "sha256:" + "a" * 64)``

    Guide
        입력 순서는 의미가 없으며 same revisionId의 중복과 잘못된 supersedes chain은 거부한다.

    When
        변화 우주에서 두 시점 사이의 claim 변화를 만들 때 호출한다.

    How
        각 cutoff에서 availableAt과 valid interval로 state를 독립 계산한 뒤 diff를 canonical hash한다.

    Requires
        timezone-aware ISO timestamp와 SHA-256 snapshotSetId가 필요하다.

    See Also
        :func:`inspectDartReplayReadiness`.

    Raises
        ValueError: cutoff가 역행하거나 assertion history와 snapshot identity가 잘못됐을 때.
    """

    contractHash = _snapshotContractHash(snapshotSetId)
    if _parseTimestamp(beforeCut.validAt, "before validAt") > _parseTimestamp(afterCut.validAt, "after validAt"):
        raise ValueError("validAt cuts must be monotonic")
    if _parseTimestamp(beforeCut.knownAt, "before knownAt") > _parseTimestamp(afterCut.knownAt, "after knownAt"):
        raise ValueError("knownAt cuts must be monotonic")

    history = tuple(
        sorted(
            assertions,
            key=lambda assertion: (
                assertion.claimKey,
                assertion.availableAt,
                assertion.sourcePublishedAt,
                assertion.revisionId,
            ),
        )
    )
    _validateHistory(history)
    changes, beforeStates, afterStates = _classifyChanges(history, beforeCut, afterCut)
    changeCounts = tuple(
        (changeType, sum(change.changeType == changeType for change in changes)) for changeType in sorted(CHANGE_TYPES)
    )
    lookAheadCount = sum(
        _parseTimestamp(assertion.availableAt, "availableAt") > _parseTimestamp(beforeCut.knownAt, "knownAt")
        for assertion in beforeStates.values()
    ) + sum(
        _parseTimestamp(assertion.availableAt, "availableAt") > _parseTimestamp(afterCut.knownAt, "knownAt")
        for assertion in afterStates.values()
    )
    completeEvidenceCount = sum(change.evidenceComplete for change in changes)
    evidenceBindingCoverage = completeEvidenceCount / len(changes) if changes else 1.0
    replayPayload = {
        "schemaVersion": "universe-change-replay-v1",
        "snapshotSetId": snapshotSetId,
        "beforeCut": _cutPayload(beforeCut),
        "afterCut": _cutPayload(afterCut),
        "changes": [asdict(change) for change in changes],
    }
    replayHash = canonicalPayloadHash(replayPayload)
    knownHistory = tuple(
        assertion
        for assertion in history
        if _parseTimestamp(assertion.availableAt, "availableAt") <= _parseTimestamp(afterCut.knownAt, "after knownAt")
    )
    historyHash = canonicalPayloadHash([_assertionPayload(assertion) for assertion in knownHistory])
    sourceRefs = tuple(sorted({reference for assertion in knownHistory for reference in assertion.evidenceRefs}))
    vintageRef = VintageRef(
        artifactKind="universeChangeReplay",
        provider="dartlabUniverseAttempt",
        artifactId=replayHash,
        artifactHash=historyHash,
        payloadHash=replayHash,
        knowledgeAsOf=afterCut.knownAt,
        availableAt=afterCut.knownAt,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        contractHash=contractHash,
        sourceRefs=sourceRefs,
    )
    validateVintageRef(
        vintageRef,
        decisionAsOf=afterCut.knownAt,
        expectedArtifactKind="universeChangeReplay",
        expectedPayloadHash=replayHash,
    )
    if not isExactAsKnown(vintageRef):
        raise ValueError("change replay VintageRef is not exact as-known")

    return ChangeReplayReport(
        snapshotSetId=snapshotSetId,
        beforeCut=beforeCut,
        afterCut=afterCut,
        revisionCount=len(history),
        preservedRevisionCount=len(history),
        revisionPreservationCoverage=1.0,
        beforeVisibleCount=sum(state.status != "retracted" for state in beforeStates.values()),
        afterVisibleCount=sum(state.status != "retracted" for state in afterStates.values()),
        changeCounts=changeCounts,
        lookAheadCount=lookAheadCount,
        evidenceBindingCoverage=evidenceBindingCoverage,
        replayHash=replayHash,
        changes=changes,
        vintageRef=vintageRef,
    )


def _revisionGroupCount(path: Path, schemaNames: set[str]) -> int:
    required = set(REVISION_GROUP_FIELDS) | {"rcept_no"}
    if not required.issubset(schemaNames):
        return 0
    import polars as pl

    frame = pl.read_parquet(path, columns=sorted(required))
    grouped = (
        frame.group_by(list(REVISION_GROUP_FIELDS))
        .agg(pl.col("rcept_no").drop_nulls().n_unique().alias("revisionCount"))
        .filter(pl.col("revisionCount") > 1)
    )
    return grouped.height


def inspectDartReplayReadiness(
    financePath: str | Path,
    *,
    maxFiles: int = 30,
) -> DartReplayReadinessReport:
    """Local DART finance의 exact change replay 필드와 revision 표본을 센서스한다.

    Capabilities
        sorted parquet 앞 N개에서 row 수, exact time, revision, row locator와 multi-filing group을 계수한다.

    AIContext
        AI 역할: rcept_no 날짜를 임의 timestamp로 확대하지 않고 live replay의 실제 blocker를 남긴다.

    Args
        financePath: company별 DART finance parquet directory.
        maxFiles: 파일명 정렬 뒤 읽을 최대 parquet 수.

    Returns
        representative가 아닌 deterministic schema sample의 readiness report.

    Example
        ``report = inspectDartReplayReadiness("data/dart/finance", maxFiles=30)``

    Guide
        이 census는 schema와 revision 존재성만 측정하며 reviewed gold sample을 대신하지 않는다.

    When
        DART source가 U0-W01 live gate를 통과할 수 있는지 재측정할 때 호출한다.

    How
        Parquet metadata schema와 row count를 읽고 같은 claim key의 rcept_no 다양성을 센다.

    Requires
        Polars와 읽을 수 있는 local parquet directory가 필요하다.

    See Also
        :func:`replayChanges`.

    Raises
        ValueError: maxFiles가 양수가 아니거나 parquet 파일이 없을 때.
        OSError: parquet schema 또는 data를 읽지 못할 때.
    """

    if maxFiles <= 0:
        raise ValueError("maxFiles must be positive")
    sourcePath = Path(financePath)
    files = tuple(sorted(sourcePath.glob("*.parquet"), key=lambda path: path.name)[:maxFiles])
    if not files:
        raise ValueError(f"no parquet files found: {sourcePath}")

    import polars as pl

    fieldFileCounts = {field: 0 for field in EXACT_REPLAY_FIELDS}
    rowCount = 0
    revisionGroupCount = 0
    for path in files:
        schema = pl.scan_parquet(path).collect_schema()
        schemaNames = set(schema.names())
        rowCount += int(pl.scan_parquet(path).select(pl.len()).collect().item())
        for field in EXACT_REPLAY_FIELDS:
            fieldFileCounts[field] += int(field in schemaNames)
        revisionGroupCount += _revisionGroupCount(path, schemaNames)

    exactFieldCoverageReady = all(count == len(files) for count in fieldFileCounts.values())
    observedRevisionHistoryReady = revisionGroupCount > 0
    gapReasons = []
    for field, count in fieldFileCounts.items():
        if count != len(files):
            gapReasons.append(f"missingField:{field}:{len(files) - count}")
    if not observedRevisionHistoryReady:
        gapReasons.append("noObservedRevisionGroup")

    return DartReplayReadinessReport(
        sourcePath=sourcePath.as_posix(),
        samplePolicy="firstSortedParquetFiles",
        representative=False,
        requestedFileCount=maxFiles,
        fileCount=len(files),
        rowCount=rowCount,
        fieldFileCounts=tuple(sorted(fieldFileCounts.items())),
        revisionGroupCount=revisionGroupCount,
        exactFieldCoverageReady=exactFieldCoverageReady,
        observedRevisionHistoryReady=observedRevisionHistoryReady,
        exactReplayReady=exactFieldCoverageReady and observedRevisionHistoryReady,
        gapReasons=tuple(gapReasons),
    )


def main() -> int:
    """Local DART finance 30개 파일의 replay readiness를 JSON으로 출력한다.

    Capabilities
        U0-W01 live gate의 deterministic schema sample을 CLI에서 재측정한다.

    AIContext
        AI 역할: synthetic 성공과 live source 승인을 분리한 근거 JSON을 만든다.

    Returns
        성공 시 0.

    Example
        ``python changeReplayProbe.py``

    Guide
        stdout 결과를 원장에 기록하고 결손 timestamp를 추정해 채우지 않는다.

    When
        DART finance artifact가 갱신된 뒤 replay readiness를 다시 볼 때 사용한다.

    How
        Repository data/dart/finance를 찾아 :func:`inspectDartReplayReadiness`를 호출한다.

    Requires
        Local DART finance parquet와 Polars가 필요하다.

    See Also
        :func:`inspectDartReplayReadiness`.

    Raises
        ValueError: parquet source가 비었을 때.
        OSError: parquet를 읽지 못할 때.
    """

    repoRoot = Path(__file__).resolve().parents[4]
    report = inspectDartReplayReadiness(repoRoot / "data" / "dart" / "finance")
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
