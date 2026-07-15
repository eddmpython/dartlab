"""Universe reviewed release gold의 입장, 균형, 품질 gate를 검증한다.

Capabilities
    Positive 300건과 hard negative 300건의 exact evidence, human review, quota, prediction을 검증한다.

AIContext
    AI 역할: 자동 생성 candidate나 불완전 review를 gold로 꾸미지 않고 결손을 release blocker로 남긴다.

Guide
    Sampling plan은 목표 분포이고 JSONL gold만 실제 review 자산이다. Missing file은 0건으로 센서스한다.

When
    U0-G01 graduation, predicate 변경, source adapter 변경, release 전 quality gate에서 사용한다.

How
    :func:`evaluateReleaseGold`로 in-memory record를 평가하거나 :func:`inspectReleaseGoldFiles`로 JSONL을 읽는다.

Requires
    Standard library만 사용한다. 실제 gold 작성에는 사람이 exact document를 열고 review해야 한다.

Raises
    ValueError: sampling plan, JSONL, record schema, timestamp, locator, duplicate가 잘못됐을 때.

Example
    ``report = inspectReleaseGoldFiles(positivePath, negativePath, predictionPath, planPath)``

See Also
    :mod:`tests._attempts.dartlabUniverse.evidence.exactEvidenceProbe`.

결과
    Admission과 metric contract는 구현됐지만 repository의 Universe reviewed positive와 negative는 각각 0/300이다.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
POSITIVE_CASE_PATTERN = re.compile(r"^universe:positive:[a-z0-9][a-z0-9._-]*$")
NEGATIVE_CASE_PATTERN = re.compile(r"^universe:negative:[a-z0-9][a-z0-9._-]*$")
REVIEW_RECEIPT_PATTERN = re.compile(r"^review:[a-z0-9][a-z0-9._-]*$")
MARKETS = {"KR", "US"}
LANGUAGES = {"ko", "en"}
EVIDENCE_CLASSES = {"A", "B"}
SOURCE_KINDS = {"DART", "SEC"}
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


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _requiredText(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed.astimezone(UTC)


def _optionalTimestamp(value: Any, field: str) -> datetime | None:
    return None if value is None else _timestamp(value, field)


def _sha256(record: Mapping[str, Any], field: str) -> str:
    value = _requiredText(record, field)
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be sha256 digest")
    return value


def _validateReview(record: Mapping[str, Any]) -> None:
    if record.get("origin") != "humanReviewed":
        raise ValueError("origin must be humanReviewed")
    if record.get("reviewMethod") != "documentOpened":
        raise ValueError("reviewMethod must be documentOpened")
    _requiredText(record, "reviewer")
    _timestamp(record.get("reviewedAt"), "reviewedAt")
    receiptId = _requiredText(record, "reviewReceiptId")
    if not REVIEW_RECEIPT_PATTERN.fullmatch(receiptId):
        raise ValueError("invalid reviewReceiptId")


def _validateDimensions(record: Mapping[str, Any]) -> None:
    if record.get("market") not in MARKETS:
        raise ValueError("market must be KR or US")
    if record.get("language") not in LANGUAGES:
        raise ValueError("language must be ko or en")


def _validatePositive(record: Mapping[str, Any]) -> None:
    caseId = _requiredText(record, "caseId")
    if not POSITIVE_CASE_PATTERN.fullmatch(caseId):
        raise ValueError("invalid positive caseId")
    _validateReview(record)
    _validateDimensions(record)
    for field in ("subjectId", "predicate", "objectId", "docId", "sectionPath", "sourceRef"):
        _requiredText(record, field)
    if record["subjectId"] == record["objectId"]:
        raise ValueError("positive self loop is forbidden")
    if record.get("expectedStatus") != "fact":
        raise ValueError("positive expectedStatus must be fact")
    if record.get("evidenceClass") not in EVIDENCE_CLASSES:
        raise ValueError("positive evidenceClass must be A or B")
    if record.get("sourceKind") not in SOURCE_KINDS:
        raise ValueError("positive sourceKind must be DART or SEC")
    _sha256(record, "sourceVersion")
    _sha256(record, "contentHash")
    _timestamp(record.get("eventAt"), "eventAt")
    validFrom = _timestamp(record.get("validFrom"), "validFrom")
    validTo = _optionalTimestamp(record.get("validTo"), "validTo")
    publishedAt = _timestamp(record.get("sourcePublishedAt"), "sourcePublishedAt")
    availableAt = _timestamp(record.get("availableAt"), "availableAt")
    if validTo is not None and validFrom > validTo:
        raise ValueError("validFrom must not be later than validTo")
    if publishedAt > availableAt:
        raise ValueError("sourcePublishedAt must not be later than availableAt")
    locatorKind = record.get("locatorKind")
    if locatorKind == "text":
        evidenceText = _requiredText(record, "evidenceText")
        charStart = record.get("charStart")
        charEnd = record.get("charEnd")
        if not isinstance(charStart, int) or not isinstance(charEnd, int) or charStart < 0 or charEnd <= charStart:
            raise ValueError("invalid text locator boundary")
        if charEnd - charStart != len(evidenceText):
            raise ValueError("text locator length does not match evidenceText")
        _sha256(record, "snippetHash")
    elif locatorKind == "table":
        rowIndex = record.get("rowIndex")
        if not isinstance(rowIndex, int) or rowIndex < 0:
            raise ValueError("rowIndex must be a non-negative integer")
        _sha256(record, "headerHash")
        _sha256(record, "rowHash")
    else:
        raise ValueError("locatorKind must be text or table")


def _validateNegative(record: Mapping[str, Any]) -> None:
    caseId = _requiredText(record, "caseId")
    if not NEGATIVE_CASE_PATTERN.fullmatch(caseId):
        raise ValueError("invalid hard negative caseId")
    _validateReview(record)
    _validateDimensions(record)
    for field in ("subjectId", "predicate", "objectId", "reviewReason"):
        _requiredText(record, field)
    if record.get("negativeType") not in NEGATIVE_TYPES:
        raise ValueError("unsupported negativeType")
    if record.get("expectedStatus") != "reject":
        raise ValueError("hard negative expectedStatus must be reject")


def _validateUnique(records: Sequence[Mapping[str, Any]]) -> None:
    caseIds = [_requiredText(record, "caseId") for record in records]
    receiptIds = [_requiredText(record, "reviewReceiptId") for record in records]
    if len(caseIds) != len(set(caseIds)):
        raise ValueError("duplicate caseId")
    if len(receiptIds) != len(set(receiptIds)):
        raise ValueError("duplicate reviewReceiptId")


def loadSamplingPlan(path: Path) -> dict[str, Any]:
    """Release gold의 목표 수와 axis별 exact quota를 읽고 검증한다.

    Capabilities
        Positive와 hard negative count 및 dimension quota 합을 고정한다.

    AIContext
        AI 역할: 편한 predicate나 market에 치우친 표본을 release gold로 오판하지 않는다.

    Returns
        검증된 sampling plan dict.

    Example
        ``plan = loadSamplingPlan(Path('releaseGoldSamplingPlan.json'))``

    Guide
        각 dimension quota 합은 해당 target count와 정확히 같아야 한다.

    When
        Gold 작성 또는 predicate와 market scope 변경 전 사용한다.

    How
        JSON을 읽고 schema, target, quota 합, negative type coverage를 검증한다.

    Requires
        UTF-8 JSON file.

    See Also
        :func:`evaluateReleaseGold`.

    Raises
        ValueError: plan schema와 quota가 잘못됐을 때.
    """

    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("schemaVersion") != "releaseGoldSamplingPlan.v1":
        raise ValueError("invalid sampling plan schema")
    positiveTarget = plan.get("positiveTargetCount")
    negativeTarget = plan.get("hardNegativeTargetCount")
    if positiveTarget != 300 or negativeTarget != 300:
        raise ValueError("release gold target must be positive 300 and hard negative 300")
    for dimension, quota in plan.get("positiveQuotas", {}).items():
        if sum(quota.values()) != positiveTarget:
            raise ValueError(f"positive quota sum mismatch: {dimension}")
    for dimension, quota in plan.get("hardNegativeQuotas", {}).items():
        if sum(quota.values()) != negativeTarget:
            raise ValueError(f"hard negative quota sum mismatch: {dimension}")
    if set(plan["hardNegativeQuotas"]["negativeType"]) != NEGATIVE_TYPES:
        raise ValueError("hard negative type quota is incomplete")
    return plan


def _quotaViolations(
    records: Sequence[Mapping[str, Any]], quotas: Mapping[str, Mapping[str, int]], lane: str
) -> tuple[str, ...]:
    violations: list[str] = []
    for dimension, expected in quotas.items():
        actual = Counter(str(record.get(dimension)) for record in records)
        for value, count in expected.items():
            if actual[value] != count:
                violations.append(f"{lane}.{dimension}.{value}:{actual[value]}/{count}")
        unexpected = sorted(set(actual) - set(expected))
        violations.extend(f"{lane}.{dimension}.unexpected:{value}" for value in unexpected)
    return tuple(violations)


def _validatePredictions(predictions: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    byCase: dict[str, Mapping[str, Any]] = {}
    for prediction in predictions:
        caseId = _requiredText(prediction, "caseId")
        if caseId in byCase:
            raise ValueError("duplicate prediction caseId")
        if not isinstance(prediction.get("admitted"), bool):
            raise ValueError("prediction admitted must be boolean")
        status = prediction.get("status")
        if status not in {"fact", "candidate", "reject", "unknown"}:
            raise ValueError("unsupported prediction status")
        byCase[caseId] = prediction
    return byCase


@dataclass(frozen=True)
class GoldAdmissionReport:
    """Release gold completeness, balance, precision, false acceptance와 blocker를 보존한다."""

    schemaVersion: str
    positiveTargetCount: int
    hardNegativeTargetCount: int
    reviewedPositiveCount: int
    reviewedHardNegativeCount: int
    predictionCount: int
    quotaViolationCount: int
    quotaViolations: tuple[str, ...]
    exactPositiveCount: int
    falseAcceptedNegativeCount: int
    positivePrecision: float | None
    falseAcceptanceRate: float | None
    sourceRefCoverage: float | None
    reviewerMissingCount: int
    contractReady: bool
    liveReady: bool
    blockerReasons: tuple[str, ...]
    goldSetHash: str | None

    def toDict(self) -> dict[str, Any]:
        """Report를 JSON 직렬화 가능한 dict로 변환한다.

        Capabilities
            Frozen dataclass의 tuple과 scalar field를 새 dict로 복사한다.

        AIContext
            AI 역할: liveReady와 blocker를 누락하지 않고 stdout 원장에 전달한다.

        Returns
            Report 전체 필드 dict.

        Example
            ``payload = report.toDict()``

        Guide
            반환값 수정은 원본 report를 바꾸지 않는다.

        When
            CLI 또는 attempt 문서에서 JSON evidence를 출력할 때 사용한다.

        How
            :func:`dataclasses.asdict`를 호출한다.

        Requires
            유효한 :class:`GoldAdmissionReport` instance.

        See Also
            :func:`evaluateReleaseGold`.

        Raises
            TypeError: dataclass 안에 직렬화할 수 없는 custom object가 들어간 경우.
        """

        return asdict(self)


def evaluateReleaseGold(
    positives: Sequence[Mapping[str, Any]],
    hardNegatives: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    samplingPlan: Mapping[str, Any],
) -> GoldAdmissionReport:
    """Reviewed gold와 system prediction을 fail-closed release metric으로 평가한다.

    Capabilities
        Exact evidence, review receipt, quota, positive precision, false acceptance와 set hash를 계산한다.

    AIContext
        AI 역할: record 수나 prediction이 모자란 상태에서 비율만 좋아 보이게 만드는 오류를 막는다.

    Returns
        :class:`GoldAdmissionReport`.

    Example
        ``report = evaluateReleaseGold(positives, negatives, predictions, plan)``

    Guide
        Positive는 exact sourceRef까지 맞아야 정답이고 negative는 admitted 또는 fact면 false accept다.

    When
        U0 졸업과 relation admission 변경의 release gate에서 사용한다.

    How
        Record schema와 uniqueness를 검증하고 exact quota와 600개 prediction을 결합한다.

    Requires
        Positive 300, hard negative 300, 대응 prediction 600과 검증된 sampling plan.

    See Also
        :func:`loadSamplingPlan`.

    Raises
        ValueError: record, prediction, duplicate가 잘못됐을 때.
    """

    for record in positives:
        _validatePositive(record)
    for record in hardNegatives:
        _validateNegative(record)
    _validateUnique([*positives, *hardNegatives])
    predictionByCase = _validatePredictions(predictions)
    positiveTarget = int(samplingPlan["positiveTargetCount"])
    negativeTarget = int(samplingPlan["hardNegativeTargetCount"])
    quotaViolations = (
        *_quotaViolations(positives, samplingPlan["positiveQuotas"], "positive"),
        *_quotaViolations(hardNegatives, samplingPlan["hardNegativeQuotas"], "negative"),
    )
    expectedCaseIds = {record["caseId"] for record in [*positives, *hardNegatives]}
    unexpectedPredictions = set(predictionByCase) - expectedCaseIds
    if unexpectedPredictions:
        raise ValueError(f"prediction has unknown caseId: {sorted(unexpectedPredictions)[0]}")
    exactPositiveCount = 0
    for record in positives:
        prediction = predictionByCase.get(record["caseId"])
        if prediction and prediction["admitted"] and prediction["status"] == "fact":
            if prediction.get("sourceRef") == record["sourceRef"]:
                exactPositiveCount += 1
    falseAcceptedNegativeCount = sum(
        1
        for record in hardNegatives
        if (prediction := predictionByCase.get(record["caseId"]))
        and (prediction["admitted"] or prediction["status"] == "fact")
    )
    positivePrecision = exactPositiveCount / len(positives) if positives else None
    falseAcceptanceRate = falseAcceptedNegativeCount / len(hardNegatives) if hardNegatives else None
    sourceRefCoverage = (
        sum(1 for record in positives if record.get("sourceRef")) / len(positives) if positives else None
    )
    reviewerMissingCount = sum(
        1 for record in [*positives, *hardNegatives] if not record.get("reviewer") or not record.get("reviewedAt")
    )
    blockerReasons: list[str] = []
    if len(positives) != positiveTarget:
        blockerReasons.append("reviewedPositiveCountIncomplete")
    if len(hardNegatives) != negativeTarget:
        blockerReasons.append("reviewedHardNegativeCountIncomplete")
    if len(predictionByCase) != positiveTarget + negativeTarget:
        blockerReasons.append("predictionCountIncomplete")
    if quotaViolations:
        blockerReasons.append("samplingQuotaViolation")
    if positivePrecision is None or positivePrecision < 0.98:
        blockerReasons.append("positivePrecisionBelow98Pct")
    if falseAcceptanceRate is None or falseAcceptanceRate > 0.01:
        blockerReasons.append("falseAcceptanceAbove1Pct")
    if sourceRefCoverage is None or sourceRefCoverage < 1:
        blockerReasons.append("sourceRefCoverageBelow100Pct")
    if reviewerMissingCount:
        blockerReasons.append("reviewMetadataMissing")
    goldSetHash = (
        _canonicalHash(
            {
                "positive": sorted(positives, key=lambda record: record["caseId"]),
                "negative": sorted(hardNegatives, key=lambda record: record["caseId"]),
            }
        )
        if positives or hardNegatives
        else None
    )
    return GoldAdmissionReport(
        schemaVersion="releaseGoldAdmissionReport.v1",
        positiveTargetCount=positiveTarget,
        hardNegativeTargetCount=negativeTarget,
        reviewedPositiveCount=len(positives),
        reviewedHardNegativeCount=len(hardNegatives),
        predictionCount=len(predictionByCase),
        quotaViolationCount=len(quotaViolations),
        quotaViolations=tuple(quotaViolations),
        exactPositiveCount=exactPositiveCount,
        falseAcceptedNegativeCount=falseAcceptedNegativeCount,
        positivePrecision=positivePrecision,
        falseAcceptanceRate=falseAcceptanceRate,
        sourceRefCoverage=sourceRefCoverage,
        reviewerMissingCount=reviewerMissingCount,
        contractReady=True,
        liveReady=not blockerReasons,
        blockerReasons=tuple(blockerReasons),
        goldSetHash=goldSetHash,
    )


def _readJsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for lineNumber, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{lineNumber}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL record must be object at {path}:{lineNumber}")
        records.append(value)
    return records


def inspectReleaseGoldFiles(
    positivePath: Path, negativePath: Path, predictionPath: Path, samplingPlanPath: Path
) -> GoldAdmissionReport:
    """Repository의 optional reviewed JSONL을 읽어 current U0-G01 readiness를 센서스한다.

    Capabilities
        Missing review asset을 0건으로 보존하고 존재하는 JSONL은 동일 admission으로 검증한다.

    AIContext
        AI 역할: 파일 부재를 synthetic record로 메우지 않는다.

    Returns
        Current repository :class:`GoldAdmissionReport`.

    Example
        ``report = inspectReleaseGoldFiles(pos, neg, pred, plan)``

    Guide
        Missing file은 오류가 아니라 incomplete blocker다. Malformed existing file은 ValueError다.

    When
        Review batch 추가 후와 U1 entry 판단 전에 사용한다.

    How
        JSONL 세 개와 sampling plan을 읽어 :func:`evaluateReleaseGold`에 전달한다.

    Requires
        Sampling plan file. Review와 prediction JSONL은 optional이다.

    See Also
        :func:`evaluateReleaseGold`.

    Raises
        ValueError: existing JSONL 또는 sampling plan이 잘못됐을 때.
    """

    plan = loadSamplingPlan(samplingPlanPath)
    return evaluateReleaseGold(
        _readJsonl(positivePath),
        _readJsonl(negativePath),
        _readJsonl(predictionPath),
        plan,
    )


def main() -> int:
    """Current repository의 U0-G01 readiness report를 stdout JSON으로 출력한다.

    Capabilities
        Default sampling plan과 optional review asset 세 파일을 센서스한다.

    AIContext
        AI 역할: human-reviewed gold가 없으면 0/300과 blocker를 그대로 출력한다.

    Returns
        성공 시 0.

    Example
        ``python releaseGoldProbe.py``

    Guide
        출력의 contractReady와 liveReady를 구분한다.

    When
        U0-G01 checkpoint와 review batch 추가 뒤 실행한다.

    How
        Module directory의 canonical filenames를 :func:`inspectReleaseGoldFiles`에 전달한다.

    Requires
        `releaseGoldSamplingPlan.json`.

    See Also
        :func:`inspectReleaseGoldFiles`.

    Raises
        ValueError: 존재하는 review asset이 invalid할 때.
    """

    root = Path(__file__).resolve().parent
    report = inspectReleaseGoldFiles(
        root / "reviewedPositive.jsonl",
        root / "hardNegative.jsonl",
        root / "admissionPredictions.jsonl",
        root / "releaseGoldSamplingPlan.json",
    )
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
