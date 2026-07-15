"""Universe relation과 evidence-backed assertion의 이중 시간 identity를 검증한다.

Capabilities
    Relation identity, assertion revision, exact Ref, valid time, known time, append-only lineage를 분리한다.

AIContext
    AI 역할: current edge hint나 query cutoff를 assertion identity로 승격하지 않고 source revision을 보존한다.

Guide
    Synthetic assertion contract와 current ecosystem의 live admission readiness를 분리한다.

When
    U0-O01 assertion schema 또는 bitemporal query semantics를 검증할 때 사용한다.

How
    :func:`compileAssertion` 뒤 :func:`buildAssertionLedger`와 :func:`queryAssertionLedger`를 순서대로 호출한다.

Requires
    Production Ref, VintageRef, canonicalPayloadHash와 live census 실행 시 remote ecosystem JSON이 필요하다.

Raises
    ValueError: identity, exact evidence, timestamp, revision lineage 또는 query contract가 잘못됐을 때.

Example
    ``ledger = buildAssertionLedger([compileAssertion(seed)])``

See Also
    :mod:`tests._attempts.dartlabUniverse.snapshot.changeReplayProbe`.

결과
    Synthetic contract는 history와 cutoff 독립 identity를 보존한다. Current edge의 live assertion readiness는 별도 센서스한다.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Iterable
from urllib.request import urlopen

from dartlab.ai.contracts import Ref
from dartlab.simulate.vintage import (
    VintageRef,
    canonicalPayloadHash,
    isExactAsKnown,
    validateVintageRef,
)

DEFAULT_SOURCE = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/landing/map/ecosystem.json"
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EVIDENCE_ID_PATTERN = re.compile(r"^evidence:[0-9a-f]{64}$")
DOCUMENT_ID_PATTERN = re.compile(r"^(kr:dart:filing:\d{14}|us:sec:filing:\d{10}-\d{2}-\d{6})$")
ASSERTION_STATUSES = {"observed", "corroborated", "disputed", "retracted"}
DIRECTIONS = {"subjectToObject", "objectToSubject", "undirected"}


def _timestamp(value: str, label: str) -> str:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _digest(value: str, label: str) -> str:
    digest = str(value).removeprefix("sha256:")
    if not SHA256_PATTERN.fullmatch(str(value)):
        raise ValueError(f"{label} must contain a SHA-256 digest")
    return digest


def _refPayload(ref: Ref) -> dict[str, Any]:
    if not isinstance(ref, Ref) or ref.sourceType != "external":
        raise ValueError("assertion evidence must be an external Ref")
    if not EVIDENCE_ID_PATTERN.fullmatch(ref.id) or ref.kind not in {"docRef", "tableRef"}:
        raise ValueError("assertion evidence Ref identity or kind is invalid")
    payload = dict(ref.payload)
    required = (
        "docId",
        "sectionPath",
        "sectionOrder",
        "sourceRef",
        "sourcePath",
        "sourceVersion",
        "contentHash",
        "sourcePublishedAt",
        "availableAt",
        "locatorKind",
    )
    if any(payload.get(name) in (None, "") for name in required):
        raise ValueError("assertion evidence Ref exact fields are incomplete")
    if not DOCUMENT_ID_PATTERN.fullmatch(str(payload["docId"])):
        raise ValueError("assertion evidence document ID is invalid")
    if int(payload["sectionOrder"]) < 0:
        raise ValueError("assertion evidence section order is invalid")
    _digest(str(payload["sourceVersion"]), "sourceVersion")
    _digest(str(payload["contentHash"]), "contentHash")
    publishedAt = _timestamp(str(payload["sourcePublishedAt"]), "sourcePublishedAt")
    availableAt = _timestamp(str(payload["availableAt"]), "availableAt")
    if publishedAt > availableAt:
        raise ValueError("sourcePublishedAt cannot be newer than availableAt")
    payload["sourcePublishedAt"] = publishedAt
    payload["availableAt"] = availableAt

    locatorKind = str(payload["locatorKind"])
    if locatorKind == "text":
        if int(payload.get("charStart", -1)) < 0 or int(payload.get("charEnd", -1)) <= int(
            payload.get("charStart", -1)
        ):
            raise ValueError("text evidence boundary is invalid")
        _digest(str(payload.get("snippetHash", "")), "snippetHash")
    elif locatorKind == "table":
        if int(payload.get("rowIndex", -1)) < 0:
            raise ValueError("table evidence row index is invalid")
        _digest(str(payload.get("headerHash", "")), "headerHash")
        _digest(str(payload.get("rowHash", "")), "rowHash")
    else:
        raise ValueError(f"unsupported evidence locator kind: {locatorKind}")
    return payload


def _canonicalRef(ref: Ref) -> dict[str, Any]:
    return {
        "id": ref.id,
        "kind": ref.kind,
        "sourceType": ref.sourceType,
        "payload": _refPayload(ref),
    }


@dataclass(frozen=True)
class AssertionSeed:
    """ID 생성 전 relation semantics, source revision, exact evidence를 보존한다."""

    subjectId: str
    predicate: str
    objectId: str
    direction: str
    status: str
    sourceSnapshotSetId: str
    sourcePublishedAt: str
    availableAt: str
    validFrom: str
    evidenceRefs: tuple[Ref, ...]
    validTo: str = ""
    eventAt: str = ""
    supersedesAssertionId: str = ""


@dataclass(frozen=True)
class UniverseAssertion:
    """Relation과 분리된 immutable assertion revision과 exact evidence binding이다."""

    relationId: str
    assertionId: str
    subjectId: str
    predicate: str
    objectId: str
    direction: str
    status: str
    sourceSnapshotSetId: str
    sourcePublishedAt: str
    availableAt: str
    validFrom: str
    validTo: str
    eventAt: str
    supersedesAssertionId: str
    evidenceRefs: tuple[Ref, ...]
    evidenceBindingHash: str


def compileAssertion(seed: AssertionSeed) -> UniverseAssertion:
    """Exact evidence와 시간을 검증해 deterministic relation 및 assertion ID를 만든다.

    Capabilities
        Stable relation key와 filing, period, revision별 assertion key를 별도 계산한다.

    AIContext
        AI 역할: knownAt이나 입력 순서를 assertion identity에 섞지 않는다.

    Args
        seed: Relation semantics와 exact evidence를 가진 assertion 입력.

    Returns
        Canonical ID와 normalized UTC timestamp를 가진 immutable assertion.

    Example
        ``assertion = compileAssertion(seed)``

    Guide
        Evidence Ref는 U0-E01 exact pointer와 동일한 필드 경계를 가져야 한다.

    When
        Candidate relation을 observed assertion으로 승격하기 직전에 호출한다.

    How
        Relation payload, sorted evidence payload, revision payload 순으로 hash한다.

    Requires
        한 개 이상의 external exact Ref와 SourceSnapshotSet digest가 필요하다.

    See Also
        :func:`buildAssertionLedger`.

    Raises
        ValueError: relation, status, time, source snapshot 또는 evidence가 불완전할 때.
    """

    if not seed.subjectId or not seed.predicate or not seed.objectId:
        raise ValueError("assertion relation identity fields are required")
    if seed.subjectId == seed.objectId:
        raise ValueError("self-loop assertion is not admitted")
    if seed.direction not in DIRECTIONS:
        raise ValueError(f"unsupported assertion direction: {seed.direction}")
    if seed.status not in ASSERTION_STATUSES:
        raise ValueError(f"unsupported assertion status: {seed.status}")
    snapshotDigest = _digest(seed.sourceSnapshotSetId, "sourceSnapshotSetId")
    sourcePublishedAt = _timestamp(seed.sourcePublishedAt, "sourcePublishedAt")
    availableAt = _timestamp(seed.availableAt, "availableAt")
    validFrom = _timestamp(seed.validFrom, "validFrom")
    validTo = _timestamp(seed.validTo, "validTo") if seed.validTo else ""
    eventAt = _timestamp(seed.eventAt, "eventAt") if seed.eventAt else ""
    if sourcePublishedAt > availableAt:
        raise ValueError("sourcePublishedAt cannot be newer than availableAt")
    if validTo and validFrom > validTo:
        raise ValueError("validFrom cannot be newer than validTo")
    if seed.supersedesAssertionId and not re.fullmatch(r"assertion:[0-9a-f]{64}", seed.supersedesAssertionId):
        raise ValueError("supersedesAssertionId is invalid")

    refs = tuple(sorted(seed.evidenceRefs, key=lambda ref: ref.id))
    if not refs or len({ref.id for ref in refs}) != len(refs):
        raise ValueError("assertion requires unique exact evidence Refs")
    canonicalRefs = tuple(_canonicalRef(ref) for ref in refs)
    if any(payload["payload"]["sourcePublishedAt"] != sourcePublishedAt for payload in canonicalRefs):
        raise ValueError("assertion publication time differs from evidence")
    if any(payload["payload"]["availableAt"] != availableAt for payload in canonicalRefs):
        raise ValueError("assertion availability time differs from evidence")

    relationPayload = {
        "schemaVersion": "universeRelation.v1",
        "subjectId": seed.subjectId,
        "predicate": seed.predicate,
        "objectId": seed.objectId,
        "direction": seed.direction,
    }
    relationId = f"relation:{canonicalPayloadHash(relationPayload)}"
    evidenceBindingHash = canonicalPayloadHash(canonicalRefs)
    assertionPayload = {
        "schemaVersion": "universeAssertion.v1",
        "relationId": relationId,
        "status": seed.status,
        "sourceSnapshotSetId": f"sha256:{snapshotDigest}",
        "sourcePublishedAt": sourcePublishedAt,
        "availableAt": availableAt,
        "validFrom": validFrom,
        "validTo": validTo,
        "eventAt": eventAt,
        "supersedesAssertionId": seed.supersedesAssertionId,
        "evidenceBindingHash": evidenceBindingHash,
    }
    return UniverseAssertion(
        relationId=relationId,
        assertionId=f"assertion:{canonicalPayloadHash(assertionPayload)}",
        subjectId=seed.subjectId,
        predicate=seed.predicate,
        objectId=seed.objectId,
        direction=seed.direction,
        status=seed.status,
        sourceSnapshotSetId=f"sha256:{snapshotDigest}",
        sourcePublishedAt=sourcePublishedAt,
        availableAt=availableAt,
        validFrom=validFrom,
        validTo=validTo,
        eventAt=eventAt,
        supersedesAssertionId=seed.supersedesAssertionId,
        evidenceRefs=refs,
        evidenceBindingHash=evidenceBindingHash,
    )


@dataclass(frozen=True)
class AssertionLedger:
    """Append-only assertion history와 deterministic ledger hash를 보존한다."""

    assertions: tuple[UniverseAssertion, ...]
    relationCount: int
    historyCount: int
    ledgerHash: str


def buildAssertionLedger(assertions: Iterable[UniverseAssertion]) -> AssertionLedger:
    """Assertion revision을 삭제하지 않고 lineage와 deterministic order를 검증한다.

    Capabilities
        Unique assertion, same-relation supersedes, monotonic availability, branch-free lineage를 강제한다.

    AIContext
        AI 역할: correction을 current row overwrite로 축약하지 않는다.

    Args
        assertions: 이미 exact evidence admission을 통과한 assertion revisions.

    Returns
        Input order와 무관한 append-only ledger.

    Example
        ``ledger = buildAssertionLedger(assertions)``

    Guide
        Superseded assertion도 ledger assertions에서 제거하지 않는다.

    When
        Assertion batch를 snapshot 또는 query runtime에 넘기기 전에 호출한다.

    How
        Assertion ID index를 만든 뒤 lineage constraint와 canonical payload hash를 계산한다.

    Requires
        한 개 이상의 compiled UniverseAssertion이 필요하다.

    See Also
        :func:`queryAssertionLedger`.

    Raises
        ValueError: duplicate, missing predecessor, cross-relation correction, time reversal 또는 branch가 있을 때.
    """

    ordered = tuple(sorted(assertions, key=lambda item: (item.availableAt, item.assertionId)))
    if not ordered:
        raise ValueError("assertion ledger cannot be empty")
    index = {assertion.assertionId: assertion for assertion in ordered}
    if len(index) != len(ordered):
        raise ValueError("assertion ledger contains duplicate assertionId")
    successorCounts: dict[str, int] = {}
    for assertion in ordered:
        predecessorId = assertion.supersedesAssertionId
        if not predecessorId:
            continue
        predecessor = index.get(predecessorId)
        if predecessor is None:
            raise ValueError("assertion predecessor is missing")
        if predecessor.relationId != assertion.relationId:
            raise ValueError("assertion correction crosses relation identity")
        if predecessor.availableAt >= assertion.availableAt:
            raise ValueError("assertion correction availability must increase")
        successorCounts[predecessorId] = successorCounts.get(predecessorId, 0) + 1
        if successorCounts[predecessorId] > 1:
            raise ValueError("assertion revision lineage cannot branch")
    ledgerPayload = tuple(
        {
            "relationId": item.relationId,
            "assertionId": item.assertionId,
            "supersedesAssertionId": item.supersedesAssertionId,
            "evidenceBindingHash": item.evidenceBindingHash,
        }
        for item in ordered
    )
    return AssertionLedger(
        assertions=ordered,
        relationCount=len({item.relationId for item in ordered}),
        historyCount=len(ordered),
        ledgerHash=canonicalPayloadHash(ledgerPayload),
    )


def _lineageRoot(assertion: UniverseAssertion, index: dict[str, UniverseAssertion]) -> str:
    current = assertion
    visited = {current.assertionId}
    while current.supersedesAssertionId:
        predecessorId = current.supersedesAssertionId
        if predecessorId in visited:
            raise ValueError("assertion revision lineage contains a cycle")
        visited.add(predecessorId)
        current = index[predecessorId]
    return current.assertionId


@dataclass(frozen=True)
class AssertionQueryResult:
    """Independent validAt, knownAt query와 exact as-known VintageRef를 반환한다."""

    validAt: str
    knownAt: str
    assertions: tuple[UniverseAssertion, ...]
    visibleHistoryCount: int
    lookAheadCount: int
    viewHash: str
    vintageRef: VintageRef


def queryAssertionLedger(
    ledger: AssertionLedger,
    *,
    validAt: str,
    knownAt: str,
    sourceSnapshotSetId: str,
) -> AssertionQueryResult:
    """Valid time과 knowledge time을 독립 적용해 lineage별 latest known revision을 반환한다.

    Capabilities
        Future effective event 허용, future knowledge 차단, visible revision collapse, exact VintageRef를 제공한다.

    AIContext
        AI 역할: 현재 최신 correction을 과거 knownAt에 역주입하지 않는다.

    Args
        ledger: Append-only assertion ledger.
        validAt: Claim 효력을 조회할 timezone-aware timestamp.
        knownAt: 당시 알 수 있었던 source를 제한할 timezone-aware timestamp.
        sourceSnapshotSetId: Query가 소비한 immutable source set digest.

    Returns
        Lineage별 visible assertion과 deterministic view hash 및 VintageRef.

    Example
        ``view = queryAssertionLedger(ledger, validAt=cut, knownAt=cut, sourceSnapshotSetId=snapshot)``

    Guide
        knownAt은 assertionId 계산에 사용하지 않고 view에만 적용한다.

    When
        변화 우주, evidence drawer, shared URL의 point-in-time scene을 만들 때 호출한다.

    How
        Availability와 validity를 필터한 뒤 visible lineage의 latest revision만 선택한다.

    Requires
        Exact evidence를 가진 non-empty ledger와 SourceSnapshotSet digest가 필요하다.

    See Also
        :func:`compileAssertion`.

    Raises
        ValueError: timestamp, snapshot digest 또는 visible assertion이 없을 때.
    """

    normalizedValidAt = _timestamp(validAt, "validAt")
    normalizedKnownAt = _timestamp(knownAt, "knownAt")
    snapshotDigest = _digest(sourceSnapshotSetId, "sourceSnapshotSetId")
    history = tuple(
        assertion
        for assertion in ledger.assertions
        if assertion.availableAt <= normalizedKnownAt
        and assertion.validFrom <= normalizedValidAt
        and (not assertion.validTo or normalizedValidAt < assertion.validTo)
    )
    if not history:
        raise ValueError("assertion query has no visible evidence")
    index = {assertion.assertionId: assertion for assertion in ledger.assertions}
    latest: dict[str, UniverseAssertion] = {}
    for assertion in history:
        root = _lineageRoot(assertion, index)
        selected = latest.get(root)
        if selected is None or (assertion.availableAt, assertion.assertionId) > (
            selected.availableAt,
            selected.assertionId,
        ):
            latest[root] = assertion
    visible = tuple(sorted(latest.values(), key=lambda item: (item.relationId, item.assertionId)))
    viewPayload = {
        "schemaVersion": "assertionView.v1",
        "validAt": normalizedValidAt,
        "knownAt": normalizedKnownAt,
        "assertionIds": tuple(item.assertionId for item in visible),
        "evidenceBindingHashes": tuple(item.evidenceBindingHash for item in visible),
    }
    viewHash = canonicalPayloadHash(viewPayload)
    evidenceIds = tuple(sorted({ref.id for item in visible for ref in item.evidenceRefs}))
    latestAvailableAt = max(item.availableAt for item in visible)
    vintage = VintageRef(
        artifactKind="universeAssertionView",
        provider="dartlabUniverse",
        artifactId=f"assertion-view:{viewHash}",
        artifactHash=viewHash,
        payloadHash=viewHash,
        knowledgeAsOf=normalizedKnownAt[:10].replace("-", ""),
        availableAt=latestAvailableAt[:10].replace("-", ""),
        revisionPolicy="asKnown",
        coverage="asOfExact",
        contractHash=snapshotDigest,
        sourceRefs=evidenceIds,
    )
    validateVintageRef(
        vintage,
        decisionAsOf=normalizedKnownAt[:10].replace("-", ""),
        expectedArtifactKind="universeAssertionView",
        expectedPayloadHash=viewHash,
    )
    if not isExactAsKnown(vintage):
        raise ValueError("assertion view vintage is not exact as-known")
    return AssertionQueryResult(
        validAt=normalizedValidAt,
        knownAt=normalizedKnownAt,
        assertions=visible,
        visibleHistoryCount=len(history),
        lookAheadCount=sum(item.availableAt > normalizedKnownAt for item in visible),
        viewHash=viewHash,
        vintageRef=vintage,
    )


@dataclass(frozen=True)
class GraphAssertionReadiness:
    """Current ecosystem relation hint와 live assertion field coverage를 분리한다."""

    schemaVersion: str
    sourceVersion: str
    edgeCount: int
    uniqueRelationCandidateCount: int
    selfLoopCount: int
    assertionIdCount: int
    supersedesCount: int
    exactEvidenceCount: int
    sourcePublishedAtCount: int
    availableAtCount: int
    validFromCount: int
    validToCount: int
    admittedStatusCount: int
    assertionReadyCount: int
    liveReady: bool
    blockerReasons: tuple[str, ...]

    def toDict(self) -> dict[str, Any]:
        """JSON compatible current graph assertion census를 반환한다.

        Returns
            Census dataclass를 mapping으로 바꾼 값.

        Example
            ``payload = census.toDict()``

        Requires
            Dataclass fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def inspectGraphAssertionReadiness(payload: dict[str, Any]) -> GraphAssertionReadiness:
    """Current ecosystem edge의 relation candidate와 exact assertion readiness를 전수 센서스한다.

    Capabilities
        Relation key, self-loop, assertion ID, revision, evidence, bitemporal field와 status를 계수한다.

    AIContext
        AI 역할: deterministic relation hash 가능성을 assertion history 가용성으로 과대 해석하지 않는다.

    Args
        payload: Ecosystem nodes와 links를 가진 mapping.

    Returns
        Field coverage와 live blocker를 가진 graph assertion census.

    Example
        ``census = inspectGraphAssertionReadiness(payload)``

    Guide
        assertionReadyCount만 live assertion admission 분자로 사용한다.

    When
        Current map artifact schema가 바뀐 뒤 U0-O01 live gate를 재검사할 때 호출한다.

    How
        Edge의 presentation relation key를 만들고 exact assertion field 논리곱을 센다.

    Requires
        모든 edge에 source, target, type이 필요하다.

    See Also
        :func:`compileAssertion`.

    Raises
        ValueError: links가 없거나 edge relation identity가 불완전할 때.
    """

    edges = payload.get("links")
    if not isinstance(edges, list):
        raise ValueError("ecosystem payload must contain a links list")
    relationKeys: set[tuple[str, str, str]] = set()
    counts = {
        "selfLoop": 0,
        "assertionId": 0,
        "supersedes": 0,
        "evidence": 0,
        "published": 0,
        "available": 0,
        "validFrom": 0,
        "validTo": 0,
        "status": 0,
        "ready": 0,
    }
    for edge in edges:
        sourceId = str(edge.get("source", ""))
        targetId = str(edge.get("target", ""))
        predicate = str(edge.get("type", ""))
        if not sourceId or not targetId or not predicate:
            raise ValueError("every edge must have source, target, and type")
        relationKeys.add((sourceId, predicate, targetId))
        counts["selfLoop"] += int(sourceId == targetId)
        counts["assertionId"] += int(bool(edge.get("assertionId")))
        counts["supersedes"] += int(bool(edge.get("supersedesAssertionId")))
        counts["evidence"] += int(bool(edge.get("evidencePointerIds")))
        counts["published"] += int(bool(edge.get("sourcePublishedAt")))
        counts["available"] += int(bool(edge.get("availableAt")))
        counts["validFrom"] += int(bool(edge.get("validFrom")))
        counts["validTo"] += int(bool(edge.get("validTo")))
        counts["status"] += int(str(edge.get("status", "")).casefold() in ASSERTION_STATUSES)
        required = (
            sourceId != targetId,
            bool(edge.get("assertionId")),
            bool(edge.get("evidencePointerIds")),
            bool(edge.get("sourcePublishedAt")),
            bool(edge.get("availableAt")),
            bool(edge.get("validFrom")),
            str(edge.get("status", "")).casefold() in ASSERTION_STATUSES,
        )
        counts["ready"] += int(all(required))
    blockers = []
    for label, count in (
        ("assertionIdMissing", counts["assertionId"]),
        ("exactEvidenceMissing", counts["evidence"]),
        ("sourcePublishedAtMissing", counts["published"]),
        ("availableAtMissing", counts["available"]),
        ("validFromMissing", counts["validFrom"]),
        ("admittedStatusMissing", counts["status"]),
    ):
        if count != len(edges):
            blockers.append(label)
    if counts["selfLoop"]:
        blockers.append("selfLoopPresent")
    if counts["ready"] != len(edges):
        blockers.append("assertionAdmissionIncomplete")
    return GraphAssertionReadiness(
        schemaVersion="graphAssertionReadiness.v1",
        sourceVersion=str(payload.get("version", "unknown")),
        edgeCount=len(edges),
        uniqueRelationCandidateCount=len(relationKeys),
        selfLoopCount=counts["selfLoop"],
        assertionIdCount=counts["assertionId"],
        supersedesCount=counts["supersedes"],
        exactEvidenceCount=counts["evidence"],
        sourcePublishedAtCount=counts["published"],
        availableAtCount=counts["available"],
        validFromCount=counts["validFrom"],
        validToCount=counts["validTo"],
        admittedStatusCount=counts["status"],
        assertionReadyCount=counts["ready"],
        liveReady=not blockers,
        blockerReasons=tuple(blockers),
    )


def _loadGraphPayload(source: str) -> dict[str, Any]:
    with urlopen(source, timeout=60) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("ecosystem payload must be a JSON object")
    return payload


def main() -> int:
    """Current remote ecosystem의 assertion readiness를 JSON으로 출력한다.

    Capabilities
        U0-O01 live relation candidate와 assertion field gap을 재측정한다.

    AIContext
        AI 역할: relation candidate 수와 admitted assertion 수를 분리한다.

    Returns
        성공 시 0.

    Example
        ``python assertionContract.py``

    Guide
        Stdout JSON을 원장에 기록하고 current edge를 자동 compile하지 않는다.

    When
        Public ecosystem artifact가 갱신된 뒤 실행한다.

    How
        Remote JSON을 읽어 :func:`inspectGraphAssertionReadiness`에 전달한다.

    Requires
        Network와 current public ecosystem JSON이 필요하다.

    See Also
        :func:`inspectGraphAssertionReadiness`.

    Raises
        OSError: Remote source를 읽지 못할 때.
        ValueError: Ecosystem schema가 잘못됐을 때.
    """

    report = inspectGraphAssertionReadiness(_loadGraphPayload(DEFAULT_SOURCE))
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
