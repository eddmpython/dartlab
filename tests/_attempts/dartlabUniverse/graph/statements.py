"""원본 row와 cell까지 되돌아가는 U3 statement 계약."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from ..canonical import canonicalDigest
from ..catalog.models import CatalogEvidence, CatalogResource
from ..contracts import EpistemicClass, SystemTime, TimeRange, VerificationState, Visibility
from ..ids import cellId, logicalId, rowId, rowVersionId
from ..temporal import parseInstant

GRAPH_STATEMENT_SCHEMA_VERSION = "du-graph-statement-v2"


@dataclass(frozen=True, slots=True)
class VirtualRowRef:
    rowIdentity: str
    identityScope: str
    resourceVersionId: str
    tableId: str
    rowGroup: int
    rowOffset: int
    locator: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class VirtualCellRef:
    cellIdentity: str
    rowIdentity: str
    columnName: str
    locator: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class GraphStatement:
    schemaVersion: str
    statementId: str
    subjectRef: str
    predicate: str
    objectRef: str | None
    value: Any | None
    valueType: str | None
    unit: str | None
    currency: str | None
    scale: int | None
    scope: str
    periodStart: str | None
    periodEnd: str | None
    instant: str | None
    validTime: TimeRange
    systemTime: SystemTime
    epistemicClass: EpistemicClass
    verificationState: VerificationState
    evidenceRefs: tuple[str, ...]
    derivationRef: str | None
    assumptionRefs: tuple[str, ...]
    confidence: float | None
    conflictGroupId: str | None
    visibility: Visibility
    digest: str


def virtualRowRef(
    resource: CatalogResource,
    *,
    tableId: str,
    rowGroup: int,
    rowOffset: int,
    businessKey: Any | None = None,
) -> VirtualRowRef:
    """행을 미리 생성하지 않고 query 시점에 stable locator를 만든다."""
    if resource.resourceKind != "HF_FILE":
        raise ValueError("virtual row는 addressable HF file에만 허용함")
    if not tableId or rowGroup < 0 or rowOffset < 0:
        raise ValueError("virtual row locator가 잘못됨")
    if businessKey is None:
        identity = rowVersionId(resource.resourceVersionId, rowGroup, rowOffset)
        scope = "REVISION_SCOPED"
    else:
        identity = rowId(resource.resourceId, tableId, businessKey)
        scope = "BUSINESS_KEY"
    locator = resource.locator + (
        ("fileVersionId", resource.resourceVersionId),
        ("tableId", tableId),
        ("rowGroup", str(rowGroup)),
        ("rowOffset", str(rowOffset)),
    )
    return VirtualRowRef(identity, scope, resource.resourceVersionId, tableId, rowGroup, rowOffset, locator)


def virtualCellRef(row: VirtualRowRef, columnName: str) -> VirtualCellRef:
    """Virtual row와 column 이름으로 원본 cell locator를 만든다."""
    if not columnName or row.identityScope not in {"REVISION_SCOPED", "BUSINESS_KEY"}:
        raise ValueError("virtual cell locator가 잘못됨")
    revisionScoped = row.identityScope == "REVISION_SCOPED"
    identity = cellId(row.rowIdentity, columnName, revisionScoped=revisionScoped)
    return VirtualCellRef(
        cellIdentity=identity,
        rowIdentity=row.rowIdentity,
        columnName=columnName,
        locator=row.locator + (("column", columnName),),
    )


def buildStatement(
    *,
    subjectRef: str,
    predicate: str,
    objectRef: str | None = None,
    value: Any | None = None,
    valueType: str | None = None,
    unit: str | None = None,
    currency: str | None = None,
    scale: int | None = None,
    scope: str,
    periodStart: str | None = None,
    periodEnd: str | None = None,
    instant: str | None = None,
    validTime: TimeRange,
    systemTime: SystemTime,
    epistemicClass: EpistemicClass,
    verificationState: VerificationState,
    evidenceRefs: tuple[str, ...],
    evidenceById: dict[str, CatalogEvidence],
    derivationRef: str | None = None,
    assumptionRefs: tuple[str, ...] = (),
    confidence: float | None = None,
    conflictGroupId: str | None = None,
    visibility: Visibility = Visibility.LOCAL,
) -> GraphStatement:
    """Statement를 evidence와 epistemic invariant에 맞춰 fail-closed 생성한다."""
    if bool(objectRef) == (value is not None):
        raise ValueError("objectRef와 value 중 정확히 하나가 필요함")
    if not subjectRef or not predicate:
        raise ValueError("subjectRef와 predicate는 필수")
    if not scope:
        raise ValueError("statement scope는 필수")
    if scale is not None and (isinstance(scale, bool) or not isinstance(scale, int)):
        raise ValueError("statement scale은 정수여야 함")
    if conflictGroupId == "":
        raise ValueError("conflictGroupId는 빈 문자열일 수 없음")
    validStart = parseInstant(validTime.start) if validTime.start else None
    validEnd = parseInstant(validTime.end) if validTime.end else None
    if validStart is not None and validEnd is not None and validEnd <= validStart:
        raise ValueError("validTime은 비어 있지 않은 반개방 구간이어야 함")
    knownAt = parseInstant(systemTime.knownAt)
    for instantValue in (systemTime.observedAt, systemTime.ingestedAt):
        if instantValue:
            parseInstant(instantValue)
    if systemTime.retractedAt and parseInstant(systemTime.retractedAt) < knownAt:
        raise ValueError("retractedAt은 knownAt보다 이를 수 없음")
    if verificationState is VerificationState.RETRACTED and not systemTime.retractedAt:
        raise ValueError("RETRACTED statement에는 retractedAt이 필요함")
    hasPeriod = periodStart is not None or periodEnd is not None
    if hasPeriod and (periodStart is None or periodEnd is None):
        raise ValueError("periodStart와 periodEnd는 함께 필요함")
    if hasPeriod and instant is not None:
        raise ValueError("기간과 instant는 동시에 둘 수 없음")
    if periodStart is not None and periodEnd is not None:
        if date.fromisoformat(periodEnd) < date.fromisoformat(periodStart):
            raise ValueError("periodEnd는 periodStart보다 이를 수 없음")
    if instant is not None:
        date.fromisoformat(instant)
    if value is not None and not valueType:
        raise ValueError("literal value에는 valueType이 필요함")
    if objectRef is not None and valueType is not None:
        raise ValueError("objectRef statement에는 valueType을 둘 수 없음")
    missingEvidence = sorted(set(evidenceRefs) - set(evidenceById))
    if missingEvidence:
        raise ValueError(f"catalog evidence 누락: {missingEvidence[0]}")
    if epistemicClass is EpistemicClass.OBSERVED and not evidenceRefs:
        raise ValueError("OBSERVED statement에는 evidence가 필요함")
    if epistemicClass in {EpistemicClass.DERIVED, EpistemicClass.INFERRED, EpistemicClass.SIMULATED}:
        if not derivationRef:
            raise ValueError("파생 statement에는 derivationRef가 필요함")
    if epistemicClass is EpistemicClass.SIMULATED and not assumptionRefs:
        raise ValueError("SIMULATED statement에는 assumptionRefs가 필요함")
    if confidence is not None and (
        isinstance(confidence, bool) or not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0
    ):
        raise ValueError("confidence는 0과 1 사이여야 함")
    if currency and unit not in {None, "currency"}:
        raise ValueError("currency가 있으면 unit은 currency여야 함")
    if visibility is Visibility.UNKNOWN:
        raise ValueError("UNKNOWN visibility statement는 질의 그래프에 넣을 수 없음")
    if visibility is Visibility.PUBLIC and verificationState is VerificationState.UNRESOLVED:
        raise ValueError("UNRESOLVED statement는 공개할 수 없음")
    visibilityRank = {
        Visibility.PUBLIC: 0,
        Visibility.LOCAL: 1,
        Visibility.PRIVATE: 2,
        Visibility.RESTRICTED: 3,
        Visibility.UNKNOWN: 4,
    }
    requiredVisibilityRank = max(
        (visibilityRank[evidenceById[item].visibility] for item in evidenceRefs),
        default=0,
    )
    if visibilityRank[visibility] < requiredVisibilityRank:
        raise ValueError("statement visibility가 evidence보다 넓을 수 없음")
    base = GraphStatement(
        schemaVersion=GRAPH_STATEMENT_SCHEMA_VERSION,
        statementId="",
        subjectRef=subjectRef,
        predicate=predicate,
        objectRef=objectRef,
        value=value,
        valueType=valueType,
        unit=unit,
        currency=currency,
        scale=scale,
        scope=scope,
        periodStart=periodStart,
        periodEnd=periodEnd,
        instant=instant,
        validTime=validTime,
        systemTime=systemTime,
        epistemicClass=epistemicClass,
        verificationState=verificationState,
        evidenceRefs=tuple(sorted(set(evidenceRefs))),
        derivationRef=derivationRef,
        assumptionRefs=tuple(sorted(set(assumptionRefs))),
        confidence=confidence,
        conflictGroupId=conflictGroupId,
        visibility=visibility,
        digest="",
    )
    digest = canonicalDigest(base)
    return replace(base, statementId=logicalId("statement", (digest,)), digest=digest)
