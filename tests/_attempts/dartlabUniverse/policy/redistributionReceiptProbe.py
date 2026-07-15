"""Universe public projection의 source와 field 정책을 fail-closed로 판정한다.

Capabilities
    source별 redistribution receipt를 canonical ID로 만들고 expiry, decision,
    allowed field, prohibited field, attribution, upstream lineage를 검증한다.

Args
    CLI 인자는 없다. U0-S01 source ID 전체를 receipt 없는 현재 상태로 센서스한다.

Returns
    :class:`ReceiptCoverageReport`를 stdout JSON으로 출력한다.

Example
    ``uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/redistributionReceiptProbe.py``

Guide
    dataset card의 license label은 evidence candidate일 뿐 receipt가 아니다. 사람이
    검토한 source와 field만 명시적으로 public 또는 metadataOnly로 승인한다.

When
    public scene admission과 share export 전에 source policy를 검증할 때 사용한다.

How
    receipt 자체를 먼저 검증하고 projection field의 모든 upstream ref를 순회한다.

Requires
    Python 표준 라이브러리와 U0-S01 currentSourceIds 계약을 사용한다.

See Also
    ``mainPlan/dartlab-universe/12-innovation-validation-scorecard.md`` 7절.

AIContext
    AI 역할: unknown, localOnly, expired, prohibited, blocked upstream을 public에서
    차단한다. 법률 판단이나 운영자 검토를 대신하지 않는다.

Raises
    malformed receipt, duplicate source receipt, invalid asOf를 숨기지 않는다.

결과
    2026-07-15 U0-S01 source 10개에 reviewed receipt registry가 없어 receipt
    coverage는 0/10, publicReady는 false, missingReceipt는 10이었다. HF README의
    CC BY 4.0 표기와 OpenDART 활용 안내는 upstream field receipt를 대체하지 않는다.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

if __package__:
    from ..snapshot import currentSourceIds
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from tests._attempts.dartlabUniverse.snapshot import currentSourceIds

SCHEMA_VERSION = "redistributionReceipt.v1"
DECISIONS = frozenset({"public", "metadataOnly", "localOnly", "blocked"})
PUBLIC_DECISIONS = frozenset({"public", "metadataOnly"})
PROJECTION_CLASSES = frozenset({"metadata", "content", "derived"})


@dataclass(frozen=True)
class RedistributionReceipt:
    """Source의 field 단위 공개 정책 검토 결과다."""

    receiptId: str
    sourceId: str
    allowedFields: tuple[str, ...]
    prohibitedFields: tuple[str, ...]
    attributionText: str | None
    attributionUrl: str | None
    policyVersion: str
    reviewedAt: str
    expiresAt: str
    reviewer: str
    decision: str
    schemaVersion: str = SCHEMA_VERSION

    def toDict(self) -> dict[str, Any]:
        """Receipt를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            dataclass 선언 순서를 보존한 dict.

        Example
            ``receipt.toDict()``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


@dataclass(frozen=True)
class ReceiptValidation:
    """단일 receipt의 구조, 무결성, 시간 판정이다."""

    valid: bool
    reason: str


@dataclass(frozen=True)
class SourceFieldRef:
    """Projection output이 의존한 source field 한 개다."""

    sourceId: str
    fieldPath: str


@dataclass(frozen=True)
class ProjectionField:
    """Public scene 후보 field와 upstream lineage다."""

    fieldId: str
    projectionClass: str
    lineage: tuple[SourceFieldRef, ...]
    expectedPublic: bool | None = None


@dataclass(frozen=True)
class FieldAdmission:
    """Projection field 하나의 public admission 결과다."""

    fieldId: str
    admitted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PublicAdmissionReport:
    """여러 projection field의 public admission 결과를 요약한다."""

    fieldCount: int
    admittedFieldCount: int
    blockedFieldCount: int
    reviewedExpectationCount: int
    falseAcceptCount: int
    falseRejectCount: int
    reasonCounts: dict[str, int]
    fields: tuple[FieldAdmission, ...]

    def toDict(self) -> dict[str, Any]:
        """Admission report를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            dataclass 선언 순서를 보존한 dict.

        Example
            ``report.toDict()``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


@dataclass(frozen=True)
class ReceiptCoverageReport:
    """Source set 전체의 reviewed receipt coverage를 요약한다."""

    asOf: str
    sourceCount: int
    receiptCount: int
    validPublicReceiptCount: int
    publicReady: bool
    admittedSourceIds: tuple[str, ...]
    blockedSourceIds: tuple[str, ...]
    reasonCounts: dict[str, int]

    def toDict(self) -> dict[str, Any]:
        """Coverage report를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            dataclass 선언 순서를 보존한 dict.

        Example
            ``report.toDict()``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


def _canonicalJson(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _receiptPayload(receipt: RedistributionReceipt) -> dict[str, Any]:
    return {
        "schemaVersion": receipt.schemaVersion,
        "sourceId": receipt.sourceId,
        "allowedFields": sorted(receipt.allowedFields),
        "prohibitedFields": sorted(receipt.prohibitedFields),
        "attributionText": receipt.attributionText,
        "attributionUrl": receipt.attributionUrl,
        "policyVersion": receipt.policyVersion,
        "reviewedAt": receipt.reviewedAt,
        "expiresAt": receipt.expiresAt,
        "reviewer": receipt.reviewer,
        "decision": receipt.decision,
    }


def _expectedReceiptId(receipt: RedistributionReceipt) -> str:
    digest = hashlib.sha256(_canonicalJson(_receiptPayload(receipt))).hexdigest()
    return f"sha256:{digest}"


def _parseDatetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _requiredDatetime(value: str, fieldName: str) -> datetime:
    parsed = _parseDatetime(value)
    if parsed is None:
        raise ValueError(f"{fieldName} must be an ISO datetime with timezone")
    return parsed


def _uniqueSorted(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({value.strip() for value in values if value.strip()}))


def buildRedistributionReceipt(
    *,
    sourceId: str,
    allowedFields: Iterable[str],
    prohibitedFields: Iterable[str],
    attributionText: str | None,
    attributionUrl: str | None,
    policyVersion: str,
    reviewedAt: str,
    expiresAt: str,
    reviewer: str,
    decision: str,
) -> RedistributionReceipt:
    """Canonical field policy로 RedistributionReceipt를 만든다.

    Capabilities
        field 순서와 중복에 독립적인 receiptId를 계산하고 기본 정책 모순을 차단한다.

    Args
        sourceId: U0-S01 source ID.
        allowedFields: public projection에서 허용한 exact field path.
        prohibitedFields: 항상 차단할 exact field path.
        attributionText: public 표면의 출처 문구.
        attributionUrl: 원 source 또는 정책 URL.
        policyVersion: 검토에 사용한 정책 버전.
        reviewedAt: 운영자 검토 ISO datetime.
        expiresAt: 재검토가 필요한 만료 ISO datetime.
        reviewer: 책임 있는 reviewer ID.
        decision: public, metadataOnly, localOnly, blocked 중 하나.

    Returns
        canonical :class:`RedistributionReceipt`.

    Example
        ``buildRedistributionReceipt(sourceId="map", allowedFields=["node.id"], ...)``

    Guide
        public과 metadataOnly는 최소 한 field를 명시한다. localOnly와 blocked는
        allowedFields를 가질 수 없다.

    When
        source owner와 운영자가 field 정책 검토를 완료한 뒤 호출한다.

    How
        field registry를 정렬하고 semantic payload의 SHA-256을 receiptId로 쓴다.

    Requires
        reviewer와 policy evidence는 호출자가 확보해야 한다.

    See Also
        :func:`validateRedistributionReceipt`.

    AIContext
        AI 역할: 검토 결과를 결정적으로 직렬화한다. reviewer를 대신하지 않는다.

    Raises
        ValueError: decision, source, field 집합이 기본 계약을 위반할 때.
    """

    normalizedSourceId = sourceId.strip()
    normalizedAllowed = _uniqueSorted(allowedFields)
    normalizedProhibited = _uniqueSorted(prohibitedFields)
    if not normalizedSourceId:
        raise ValueError("sourceId is required")
    if decision not in DECISIONS:
        raise ValueError(f"unsupported decision: {decision}")
    overlap = set(normalizedAllowed) & set(normalizedProhibited)
    if overlap:
        raise ValueError(f"allowed and prohibited fields overlap: {sorted(overlap)}")
    if decision in PUBLIC_DECISIONS and not normalizedAllowed:
        raise ValueError("public decision requires allowedFields")
    if decision not in PUBLIC_DECISIONS and normalizedAllowed:
        raise ValueError("blocked decision cannot have allowedFields")

    draft = RedistributionReceipt(
        receiptId="",
        sourceId=normalizedSourceId,
        allowedFields=normalizedAllowed,
        prohibitedFields=normalizedProhibited,
        attributionText=attributionText.strip() if attributionText else None,
        attributionUrl=attributionUrl.strip() if attributionUrl else None,
        policyVersion=policyVersion.strip(),
        reviewedAt=reviewedAt.strip(),
        expiresAt=expiresAt.strip(),
        reviewer=reviewer.strip(),
        decision=decision,
    )
    return RedistributionReceipt(**{**asdict(draft), "receiptId": _expectedReceiptId(draft)})


def validateRedistributionReceipt(
    receipt: RedistributionReceipt,
    *,
    asOf: str,
) -> ReceiptValidation:
    """Receipt 구조, canonical ID, review window를 fail-closed로 검증한다.

    Capabilities
        malformed time, future review, expiry, attribution, policy version, field 모순,
        receipt tampering을 reason code로 판정한다.

    Args
        receipt: 검증할 receipt.
        asOf: admission을 평가할 timezone 포함 ISO datetime.

    Returns
        :class:`ReceiptValidation`.

    Example
        ``validateRedistributionReceipt(receipt, asOf="2026-07-15T00:00:00Z")``

    Guide
        첫 실패 reason을 반환한다. localOnly와 blocked receipt도 유효한 차단 증거가
        될 수 있지만 public admission은 별도 함수에서 거부한다.

    When
        receipt load 직후와 public projection 실행 직전에 호출한다.

    How
        시간과 필수 metadata를 검사한 뒤 canonical receiptId를 다시 계산한다.

    Requires
        asOf는 timezone을 포함해야 한다.

    See Also
        :func:`assessPublicProjection`.

    AIContext
        AI 역할: 낡거나 변조된 정책 결정을 public admission에서 제거한다.

    Raises
        ValueError: asOf 자체가 유효한 timezone datetime이 아닐 때.
    """

    cutoff = _requiredDatetime(asOf, "asOf")
    if receipt.schemaVersion != SCHEMA_VERSION:
        return ReceiptValidation(False, "unsupportedSchemaVersion")
    if not receipt.sourceId:
        return ReceiptValidation(False, "missingSourceId")
    if receipt.decision not in DECISIONS:
        return ReceiptValidation(False, "unsupportedDecision")
    if not receipt.policyVersion:
        return ReceiptValidation(False, "missingPolicyVersion")
    if not receipt.reviewer:
        return ReceiptValidation(False, "missingReviewer")
    reviewedAt = _parseDatetime(receipt.reviewedAt)
    if reviewedAt is None:
        return ReceiptValidation(False, "invalidReviewedAt")
    if reviewedAt > cutoff:
        return ReceiptValidation(False, "reviewInFuture")
    expiresAt = _parseDatetime(receipt.expiresAt)
    if expiresAt is None:
        return ReceiptValidation(False, "invalidExpiresAt")
    if expiresAt <= reviewedAt:
        return ReceiptValidation(False, "expiryBeforeReview")
    if cutoff >= expiresAt:
        return ReceiptValidation(False, "expiredReceipt")
    if receipt.decision in PUBLIC_DECISIONS:
        if not receipt.allowedFields:
            return ReceiptValidation(False, "missingAllowedFields")
        if not receipt.attributionText or not receipt.attributionUrl:
            return ReceiptValidation(False, "missingAttribution")
    elif receipt.allowedFields:
        return ReceiptValidation(False, "blockedDecisionHasAllowedFields")
    if set(receipt.allowedFields) & set(receipt.prohibitedFields):
        return ReceiptValidation(False, "fieldPolicyOverlap")
    if receipt.receiptId != _expectedReceiptId(receipt):
        return ReceiptValidation(False, "receiptIdMismatch")
    return ReceiptValidation(True, "valid")


def _receiptMap(receipts: Iterable[RedistributionReceipt]) -> dict[str, RedistributionReceipt]:
    bySource: dict[str, RedistributionReceipt] = {}
    for receipt in receipts:
        if receipt.sourceId in bySource:
            raise ValueError(f"duplicate receipt sourceId: {receipt.sourceId}")
        bySource[receipt.sourceId] = receipt
    return bySource


def _sourceRefReasons(
    sourceRef: SourceFieldRef,
    projectionClass: str,
    receipts: dict[str, RedistributionReceipt],
    asOf: str,
) -> list[str]:
    if not sourceRef.sourceId or not sourceRef.fieldPath:
        return ["invalidLineageRef"]
    receipt = receipts.get(sourceRef.sourceId)
    if receipt is None:
        return ["missingReceipt"]
    validation = validateRedistributionReceipt(receipt, asOf=asOf)
    if not validation.valid:
        return [validation.reason]
    if receipt.decision == "localOnly":
        return ["localOnlySource"]
    if receipt.decision == "blocked":
        return ["blockedSource"]
    if sourceRef.fieldPath in receipt.prohibitedFields:
        return ["prohibitedField"]
    if sourceRef.fieldPath not in receipt.allowedFields:
        return ["fieldNotAllowed"]
    if receipt.decision == "metadataOnly" and projectionClass != "metadata":
        return ["metadataOnlySource"]
    return []


def assessPublicProjection(
    fields: Iterable[ProjectionField],
    receipts: Iterable[RedistributionReceipt],
    *,
    asOf: str,
) -> PublicAdmissionReport:
    """Projection field의 모든 upstream source policy를 검증한다.

    Capabilities
        missing lineage, unknown receipt, expired policy, localOnly, metadataOnly,
        prohibited field와 mixed upstream을 field 단위로 차단한다.

    Args
        fields: public scene 후보 projection fields.
        receipts: sourceId별 receipt iterable.
        asOf: policy admission cutoff.

    Returns
        deterministic :class:`PublicAdmissionReport`.

    Example
        ``assessPublicProjection(fields, receipts, asOf="2026-07-15T00:00:00Z")``

    Guide
        derived field의 upstream 하나라도 차단되면 output 전체를 차단한다. 허용
        upstream만 남겨 같은 field를 부분 승인하지 않는다.

    When
        projection compiler가 publicOnly scene을 반환하기 직전에 호출한다.

    How
        receipt를 sourceId로 결속하고 각 SourceFieldRef를 전수 검사한다.

    Requires
        모든 derived output은 정확한 source field lineage를 가져야 한다.

    See Also
        :func:`validateRedistributionReceipt`.

    AIContext
        AI 역할: 금지 upstream의 파생값 public leak을 0으로 유지한다.

    Raises
        ValueError: duplicate receipt, duplicate fieldId, invalid asOf일 때.
    """

    _requiredDatetime(asOf, "asOf")
    receiptBySource = _receiptMap(receipts)
    fieldItems = tuple(fields)
    admissions: list[FieldAdmission] = []
    reasonCounts: Counter[str] = Counter()
    seenFieldIds: set[str] = set()
    for field in fieldItems:
        if not field.fieldId:
            raise ValueError("fieldId is required")
        if field.fieldId in seenFieldIds:
            raise ValueError(f"duplicate fieldId: {field.fieldId}")
        seenFieldIds.add(field.fieldId)
        reasons: list[str] = []
        if field.projectionClass not in PROJECTION_CLASSES:
            reasons.append("invalidProjectionClass")
        if not field.lineage:
            reasons.append("missingLineage")
        for sourceRef in field.lineage:
            reasons.extend(
                _sourceRefReasons(
                    sourceRef,
                    field.projectionClass,
                    receiptBySource,
                    asOf,
                )
            )
        uniqueReasons = tuple(sorted(set(reasons)))
        admitted = not uniqueReasons
        admissions.append(FieldAdmission(field.fieldId, admitted, uniqueReasons))
        reasonCounts.update(uniqueReasons)

    orderedAdmissions = tuple(sorted(admissions, key=lambda item: item.fieldId))
    admittedCount = sum(admission.admitted for admission in orderedAdmissions)
    expectedByField = {field.fieldId: field.expectedPublic for field in fieldItems}
    reviewedExpectationCount = sum(expected is not None for expected in expectedByField.values())
    falseAcceptCount = sum(
        admission.admitted and expectedByField[admission.fieldId] is False for admission in orderedAdmissions
    )
    falseRejectCount = sum(
        not admission.admitted and expectedByField[admission.fieldId] is True for admission in orderedAdmissions
    )
    return PublicAdmissionReport(
        fieldCount=len(orderedAdmissions),
        admittedFieldCount=admittedCount,
        blockedFieldCount=len(orderedAdmissions) - admittedCount,
        reviewedExpectationCount=reviewedExpectationCount,
        falseAcceptCount=falseAcceptCount,
        falseRejectCount=falseRejectCount,
        reasonCounts=dict(sorted(reasonCounts.items())),
        fields=orderedAdmissions,
    )


def inspectReceiptCoverage(
    sourceIds: Iterable[str],
    receipts: Iterable[RedistributionReceipt],
    *,
    asOf: str,
) -> ReceiptCoverageReport:
    """Source set 전체의 valid public receipt coverage를 센서스한다.

    Capabilities
        missing, invalid, localOnly, blocked receipt를 source별로 계수한다.

    Args
        sourceIds: U0-S01 source ID iterable.
        receipts: 현재 reviewed receipt registry.
        asOf: coverage cutoff.

    Returns
        :class:`ReceiptCoverageReport`.

    Example
        ``inspectReceiptCoverage(currentSourceIds(), [], asOf=now)``

    Guide
        source가 없다고 receipt를 자동 생성하지 않는다. publicReady는 모든 source가
        valid public 또는 metadataOnly receipt를 가질 때만 true다.

    When
        release gate와 policy registry maintenance audit에서 호출한다.

    How
        sourceId를 정렬하고 receipt validity와 decision을 각각 판정한다.

    Requires
        source ID는 SourceSnapshotSet과 같은 namespace를 사용해야 한다.

    See Also
        :func:`assessPublicProjection`.

    AIContext
        AI 역할: public policy coverage의 honest gap을 정량화한다.

    Raises
        ValueError: duplicate sourceId, duplicate receipt, invalid asOf일 때.
    """

    _requiredDatetime(asOf, "asOf")
    normalizedSourceIds = tuple(sorted(sourceId.strip() for sourceId in sourceIds))
    if any(not sourceId for sourceId in normalizedSourceIds):
        raise ValueError("sourceId is required")
    if len(set(normalizedSourceIds)) != len(normalizedSourceIds):
        raise ValueError("duplicate sourceId in source census")
    receiptBySource = _receiptMap(receipts)
    admittedSourceIds: list[str] = []
    blockedSourceIds: list[str] = []
    reasonCounts: Counter[str] = Counter()
    for sourceId in normalizedSourceIds:
        receipt = receiptBySource.get(sourceId)
        if receipt is None:
            reason = "missingReceipt"
        else:
            validation = validateRedistributionReceipt(receipt, asOf=asOf)
            if not validation.valid:
                reason = validation.reason
            elif receipt.decision == "localOnly":
                reason = "localOnlySource"
            elif receipt.decision == "blocked":
                reason = "blockedSource"
            else:
                admittedSourceIds.append(sourceId)
                continue
        blockedSourceIds.append(sourceId)
        reasonCounts[reason] += 1

    return ReceiptCoverageReport(
        asOf=asOf,
        sourceCount=len(normalizedSourceIds),
        receiptCount=sum(sourceId in receiptBySource for sourceId in normalizedSourceIds),
        validPublicReceiptCount=len(admittedSourceIds),
        publicReady=not blockedSourceIds,
        admittedSourceIds=tuple(admittedSourceIds),
        blockedSourceIds=tuple(blockedSourceIds),
        reasonCounts=dict(sorted(reasonCounts.items())),
    )


def main() -> int:
    """현재 U0 source set의 reviewed receipt coverage를 출력한다.

    Capabilities
        live source ID에 receipt가 없는 현재 policy gap을 JSON으로 보여준다.

    Args
        없음.

    Returns
        성공 시 0.

    Example
        ``python redistributionReceiptProbe.py``

    Guide
        자동 승인 없이 empty registry를 측정한다.

    When
        U0-P02와 분기별 policy maintenance audit에서 실행한다.

    How
        currentSourceIds와 empty receipt registry를 coverage inspector에 전달한다.

    Requires
        없음.

    See Also
        :func:`inspectReceiptCoverage`.

    AIContext
        AI 역할: 운영자 검토 전 publicReady가 false인지 확인한다.

    Raises
        내부 source ID 또는 timestamp 계약 오류를 숨기지 않는다.
    """

    asOf = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = inspectReceiptCoverage(currentSourceIds(), [], asOf=asOf)
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
