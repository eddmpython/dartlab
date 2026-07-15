"""Human review decision을 Universe release gold record로 fail-closed 승격한다.

Capabilities
    Machine queue, original source binding, human decision을 결합해 positive 및 hard-negative gold를 만든다.

AIContext
    AI 역할: reviewer identity, exact locator, time, predicate confirmation이 없는 candidate를 절대 승격하지 않는다.

Guide
    Decision은 ``acceptPositive``, ``confirmNegative``, ``defer`` 중 하나다. Machine record 수정은 review가 아니다.

When
    U0-G02 및 U0-G03 자산에 운영자 review receipt가 생긴 뒤 release gold JSONL을 만들 때 사용한다.

How
    :func:`promoteReviewedDecisions`에 queue, source binding, decision을 전달하고 결과를 admission probe로 검증한다.

Requires
    Standard library, content-addressed source binding, 사람이 original document를 연 review decision.

Raises
    ValueError: Decision identity, review receipt, locator, entity triple 또는 time contract가 잘못됐을 때.

Example
    ``positive, negative, report = promoteReviewedDecisions(queue, bindings, decisions)``

See Also
    :mod:`tests._attempts.dartlabUniverse.fixtures.releaseGoldProbe`.

결과
    빈 decision input은 빈 gold와 명시적 blocker receipt를 반환한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DECISIONS = {"acceptPositive", "confirmNegative", "defer"}
NEGATIVE_TYPES = {
    "shortEnglishCommonWord",
    "sameNameDifferentEntity",
    "affiliateEntityCollision",
    "selfLoopMention",
    "reversedDirection",
    "industryPeerAsTradeRelation",
    "preCorrectionConflict",
    "privateListedAliasCollision",
    "sectionTitleOnly",
    "tableHeaderDrift",
    "historicalTickerCollision",
    "crossMarketFuzzyCollision",
}
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
REVIEW_RECEIPT_PATTERN = re.compile(r"^review:[a-z0-9][a-z0-9._-]*$")
DEFAULT_QUEUE = Path("tests/_attempts/dartlabUniverse/fixtures/releaseGoldReviewQueue.machine.jsonl")
DEFAULT_BINDINGS = Path("tests/_attempts/dartlabUniverse/fixtures/releaseGoldSourceBinding.machine.jsonl")
DEFAULT_DECISIONS = Path("tests/_attempts/dartlabUniverse/fixtures/reviewedDecisions.jsonl")


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _requiredText(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _optionalTimestamp(value: Any, field: str) -> str | None:
    return None if value is None else _timestamp(value, field)


def _caseId(lane: str, candidateId: str) -> str:
    digest = _canonicalHash(candidateId).removeprefix("sha256:")[:24]
    return f"universe:{lane}:{digest}"


def _reviewFields(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("schemaVersion") != "releaseGoldReviewDecision.v1":
        raise ValueError("invalid review decision schema")
    if decision.get("origin") != "humanReviewed":
        raise ValueError("origin must be humanReviewed")
    if decision.get("reviewMethod") != "documentOpened":
        raise ValueError("reviewMethod must be documentOpened")
    reviewer = _requiredText(decision, "reviewer")
    reviewedAt = _timestamp(decision.get("reviewedAt"), "reviewedAt")
    receiptId = _requiredText(decision, "reviewReceiptId")
    if not REVIEW_RECEIPT_PATTERN.fullmatch(receiptId):
        raise ValueError("invalid reviewReceiptId")
    return {
        "origin": "humanReviewed",
        "reviewMethod": "documentOpened",
        "reviewer": reviewer,
        "reviewedAt": reviewedAt,
        "reviewReceiptId": receiptId,
    }


def _confirmedTriple(queueRecord: Mapping[str, Any], decision: Mapping[str, Any]) -> tuple[str, str, str]:
    confirmed = tuple(_requiredText(decision, field) for field in ("subjectId", "predicate", "objectId"))
    expected = tuple(_requiredText(queueRecord, field) for field in ("subjectId", "predicate", "objectId"))
    if confirmed != expected:
        raise ValueError(f"confirmed triple differs from candidate {queueRecord.get('candidateId')}")
    return confirmed


def _selectedLocator(binding: Mapping[str, Any], decision: Mapping[str, Any]) -> Mapping[str, Any]:
    if not binding.get("sourceArtifactReady"):
        raise ValueError(f"source binding is not ready: {binding.get('candidateId')}")
    selectedId = _requiredText(decision, "selectedLocatorId")
    matches = [locator for locator in binding.get("locatorCandidates", []) if locator.get("locatorId") == selectedId]
    if len(matches) != 1:
        raise ValueError(f"selectedLocatorId is not a returned exact locator: {selectedId}")
    locator = matches[0]
    if not SHA256_PATTERN.fullmatch(str(binding.get("originalSourceVersion") or "")):
        raise ValueError("originalSourceVersion must be sha256 digest")
    for field in ("contentHash", "snippetHash"):
        if not SHA256_PATTERN.fullmatch(str(locator.get(field) or "")):
            raise ValueError(f"locator {field} must be sha256 digest")
    evidenceText = _requiredText(locator, "evidenceText")
    charStart = locator.get("charStart")
    charEnd = locator.get("charEnd")
    if (
        not isinstance(charStart, int)
        or not isinstance(charEnd, int)
        or charStart < 0
        or charEnd <= charStart
        or charEnd - charStart != len(evidenceText)
    ):
        raise ValueError("selected locator has invalid text boundary")
    return locator


def _promotePositive(
    queueRecord: Mapping[str, Any], binding: Mapping[str, Any], decision: Mapping[str, Any]
) -> dict[str, Any]:
    if queueRecord.get("lane") != "positiveCandidate":
        raise ValueError("acceptPositive requires positiveCandidate lane")
    subjectId, predicate, objectId = _confirmedTriple(queueRecord, decision)
    locator = _selectedLocator(binding, decision)
    if locator["evidenceText"] != _requiredText(queueRecord, "evidenceText"):
        raise ValueError("selected locator evidence differs from candidate")
    eventAt = _timestamp(decision.get("eventAt"), "eventAt")
    validFrom = _timestamp(decision.get("validFrom"), "validFrom")
    validTo = _optionalTimestamp(decision.get("validTo"), "validTo")
    publishedAt = _timestamp(decision.get("sourcePublishedAt"), "sourcePublishedAt")
    availableAt = _timestamp(decision.get("availableAt"), "availableAt")
    if validTo is not None and validFrom > validTo:
        raise ValueError("validFrom must not be later than validTo")
    if publishedAt > availableAt:
        raise ValueError("sourcePublishedAt must not be later than availableAt")
    evidenceClass = decision.get("evidenceClass")
    if evidenceClass not in {"A", "B"}:
        raise ValueError("evidenceClass must be A or B")
    sourceKind = decision.get("sourceKind")
    if sourceKind not in {"DART", "SEC"}:
        raise ValueError("sourceKind must be DART or SEC")
    candidateId = _requiredText(queueRecord, "candidateId")
    return {
        "caseId": _caseId("positive", candidateId),
        "subjectId": subjectId,
        "predicate": predicate,
        "objectId": objectId,
        "docId": _requiredText(queueRecord, "docId"),
        "sectionPath": str(locator.get("sectionPath") or queueRecord.get("sectionPath") or "original/raw"),
        "sourceRef": _requiredText(decision, "reviewedSourceRef"),
        "sourceVersion": binding["originalSourceVersion"],
        "contentHash": locator["contentHash"],
        "locatorKind": "text",
        "evidenceText": locator["evidenceText"],
        "charStart": locator["charStart"],
        "charEnd": locator["charEnd"],
        "snippetHash": locator["snippetHash"],
        "eventAt": eventAt,
        "validFrom": validFrom,
        "validTo": validTo,
        "sourcePublishedAt": publishedAt,
        "availableAt": availableAt,
        "expectedStatus": "fact",
        "market": queueRecord.get("market"),
        "language": queueRecord.get("language"),
        "evidenceClass": evidenceClass,
        "sourceKind": sourceKind,
        **_reviewFields(decision),
    }


def _promoteNegative(queueRecord: Mapping[str, Any], decision: Mapping[str, Any]) -> dict[str, Any]:
    subjectId, predicate, objectId = _confirmedTriple(queueRecord, decision)
    negativeType = _requiredText(decision, "negativeType")
    if negativeType not in NEGATIVE_TYPES:
        raise ValueError("unsupported negativeType")
    plannedType = queueRecord.get("negativeType")
    if plannedType is not None and plannedType != negativeType:
        raise ValueError("confirmed negativeType differs from challenge")
    candidateId = _requiredText(queueRecord, "candidateId")
    return {
        "caseId": _caseId("negative", candidateId),
        "subjectId": subjectId,
        "predicate": predicate,
        "objectId": objectId,
        "negativeType": negativeType,
        "expectedStatus": "reject",
        "reviewReason": _requiredText(decision, "reviewReason"),
        "candidateSourceRef": _requiredText(decision, "reviewedSourceRef"),
        "market": queueRecord.get("market"),
        "language": queueRecord.get("language"),
        **_reviewFields(decision),
    }


def promoteReviewedDecisions(
    queueRecords: Sequence[Mapping[str, Any]],
    sourceBindings: Sequence[Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Validated human decisions만 positive 및 hard-negative gold record로 승격한다.

    Capabilities
        Exact locator selection, confirmed triple, bitemporal fields, reviewer receipt를 fail-closed 검증한다.

    AIContext
        AI 역할: machine queue와 binding을 provenance로 사용하되 사람 decision이 없는 record는 출력하지 않는다.

    Guide
        Corrected triple은 기존 candidate를 조용히 수정하지 말고 새 review candidate로 다시 작성한다.

    When
        Reviewer decision batch를 release gold JSONL로 materialize하거나 dry-run coverage를 볼 때 호출한다.

    How
        Candidate ID로 queue, binding, decision을 join하고 decision 종류별 promotion 함수를 실행한다.

    Requires
        Queue와 binding candidate ID 1:1, unique human review receipt, timezone-aware decision timestamps.

    Args:
        queueRecords: Machine review queue records.
        sourceBindings: Original source binding records.
        decisions: Human review decision records.

    Returns:
        Promoted positive list, negative list, review promotion report tuple.

    Raises:
        ValueError: Duplicate, unknown, mismatched, incomplete 또는 machine-authored decision일 때.

    Example:
        ``positive, negative, report = promoteReviewedDecisions(queue, bindings, decisions)``

    SeeAlso:
        :func:`tests._attempts.dartlabUniverse.fixtures.releaseGoldProbe.evaluateReleaseGold`.
    """

    queueById: dict[str, Mapping[str, Any]] = {}
    for record in queueRecords:
        candidateId = _requiredText(record, "candidateId")
        if candidateId in queueById:
            raise ValueError("duplicate queue candidateId")
        if record.get("reviewState") != "unreviewed" or record.get("goldEligible") is not False:
            raise ValueError("machine queue must remain unreviewed and gold-ineligible")
        queueById[candidateId] = record
    bindingById: dict[str, Mapping[str, Any]] = {}
    for binding in sourceBindings:
        candidateId = _requiredText(binding, "candidateId")
        if candidateId in bindingById:
            raise ValueError("duplicate source binding candidateId")
        if candidateId not in queueById:
            raise ValueError(f"binding candidate is not in queue: {candidateId}")
        bindingById[candidateId] = binding
    if set(bindingById) != set(queueById):
        raise ValueError("source binding coverage must match queue")
    decisionById: dict[str, Mapping[str, Any]] = {}
    receiptIds: set[str] = set()
    for decision in decisions:
        candidateId = _requiredText(decision, "candidateId")
        if candidateId in decisionById:
            raise ValueError("duplicate decision candidateId")
        if candidateId not in queueById:
            raise ValueError(f"decision candidate is not in queue: {candidateId}")
        decisionKind = decision.get("decision")
        if decisionKind not in DECISIONS:
            raise ValueError("decision must be acceptPositive, confirmNegative, or defer")
        reviewFields = _reviewFields(decision)
        receiptId = str(reviewFields["reviewReceiptId"])
        if receiptId in receiptIds:
            raise ValueError("duplicate reviewReceiptId")
        receiptIds.add(receiptId)
        decisionById[candidateId] = decision
    positives: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    deferredCount = 0
    for candidateId in sorted(decisionById):
        decision = decisionById[candidateId]
        decisionKind = decision["decision"]
        if decisionKind == "acceptPositive":
            positives.append(_promotePositive(queueById[candidateId], bindingById[candidateId], decision))
        elif decisionKind == "confirmNegative":
            selectedLocatorId = decision.get("selectedLocatorId")
            if selectedLocatorId:
                _selectedLocator(bindingById[candidateId], decision)
            negatives.append(_promoteNegative(queueById[candidateId], decision))
        else:
            _requiredText(decision, "reviewReason")
            deferredCount += 1
    decisionKinds = Counter(str(decision["decision"]) for decision in decisions)
    report = {
        "schemaVersion": "releaseGoldReviewPromotionReceipt.v1",
        "queueRecordCount": len(queueRecords),
        "sourceBindingCount": len(sourceBindings),
        "decisionCount": len(decisions),
        "decisionCounts": dict(sorted(decisionKinds.items())),
        "promotedPositiveCount": len(positives),
        "promotedHardNegativeCount": len(negatives),
        "deferredCount": deferredCount,
        "unreviewedQueueCount": len(queueRecords) - len(decisions),
        "uniqueReviewReceiptCount": len(receiptIds),
        "allPromotedRowsHumanReviewed": bool(positives or negatives)
        and all(record["origin"] == "humanReviewed" for record in positives + negatives),
        "reviewPromotionReady": len(positives) == 300 and len(negatives) == 300,
        "goldAdmissionReady": False,
        "blockers": [
            blocker
            for blocker, blocked in (
                ("reviewedPositiveCountIncomplete", len(positives) != 300),
                ("reviewedHardNegativeCountIncomplete", len(negatives) != 300),
                ("predictionCountIncomplete", True),
                ("samplingQuotaNotEvaluated", True),
            )
            if blocked
        ],
    }
    return positives, negatives, report


def _loadJsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _fileReceipt(path: Path, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.as_posix(),
        "size": len(payload),
        "sha256": f"sha256:{hashlib.sha256(payload).hexdigest()}",
        "rowCount": len(records),
    }


def _writeJsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    path.write_text(body, encoding="utf-8")


def _parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote reviewed Universe candidates to release gold")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--bindings", type=Path, default=DEFAULT_BINDINGS)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--positive-output", type=Path)
    parser.add_argument("--negative-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    return parser.parse_args()


def _main() -> int:
    args = _parseArgs()
    queue = _loadJsonl(args.queue)
    bindings = _loadJsonl(args.bindings)
    decisions = _loadJsonl(args.decisions)
    positive, negative, report = promoteReviewedDecisions(queue, bindings, decisions)
    report["queueFile"] = _fileReceipt(args.queue, queue)
    report["bindingFile"] = _fileReceipt(args.bindings, bindings)
    report["decisionFile"] = _fileReceipt(args.decisions, decisions) if args.decisions.is_file() else None
    if args.positive_output:
        _writeJsonl(args.positive_output, positive)
        report["positiveFile"] = _fileReceipt(args.positive_output, positive)
    if args.negative_output:
        _writeJsonl(args.negative_output, negative)
        report["negativeFile"] = _fileReceipt(args.negative_output, negative)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
