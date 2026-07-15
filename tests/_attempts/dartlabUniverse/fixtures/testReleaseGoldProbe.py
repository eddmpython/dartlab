"""releaseGoldProbe의 review, quota, precision, false acceptance gate를 검증한다."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.fixtures import (
    evaluateReleaseGold,
    inspectReleaseGoldFiles,
    loadSamplingPlan,
)

ROOT = Path(__file__).resolve().parent
HASH = f"sha256:{'a' * 64}"
PREDICATES = ("suppliesTo", "sellsTo", "ownsStakeIn", "affiliatedWith", "classifiedIn", "filed")
NEGATIVE_TYPES = (
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
)


def _positive(index: int) -> dict:
    market = "KR" if index < 150 else "US"
    language = "ko" if index % 2 == 0 else "en"
    evidenceClass = "A" if index < 150 else "B"
    sourceKind = "DART" if index < 150 else "SEC"
    text = f"exact evidence {index}"
    return {
        "caseId": f"universe:positive:case-{index:03d}",
        "subjectId": f"{market.lower()}:entity:{index:04d}",
        "predicate": PREDICATES[index % len(PREDICATES)],
        "objectId": f"{market.lower()}:entity:{index + 1000:04d}",
        "docId": f"{sourceKind.lower()}:filing:{index:06d}",
        "sectionPath": "사업/근거",
        "sourceRef": f"{sourceKind.lower()}:panel:{index:06d}#section=1",
        "sourceVersion": HASH,
        "contentHash": HASH,
        "locatorKind": "text",
        "evidenceText": text,
        "charStart": 10,
        "charEnd": 10 + len(text),
        "snippetHash": HASH,
        "eventAt": "2025-12-31T00:00:00Z",
        "validFrom": "2026-01-01T00:00:00Z",
        "validTo": None,
        "sourcePublishedAt": "2026-01-02T00:00:00Z",
        "availableAt": "2026-01-02T00:01:00Z",
        "expectedStatus": "fact",
        "market": market,
        "language": language,
        "evidenceClass": evidenceClass,
        "sourceKind": sourceKind,
        "origin": "humanReviewed",
        "reviewMethod": "documentOpened",
        "reviewer": "fixture-reviewer",
        "reviewedAt": "2026-07-16T00:00:00Z",
        "reviewReceiptId": f"review:positive-{index:03d}",
    }


def _negative(index: int) -> dict:
    market = "KR" if index < 150 else "US"
    return {
        "caseId": f"universe:negative:case-{index:03d}",
        "subjectId": f"{market.lower()}:entity:{index:04d}",
        "predicate": "suppliesTo",
        "objectId": f"{market.lower()}:entity:{index + 1000:04d}",
        "negativeType": NEGATIVE_TYPES[index % len(NEGATIVE_TYPES)],
        "expectedStatus": "reject",
        "reviewReason": "exact document를 열어 candidate가 predicate를 입증하지 않음을 확인",
        "candidateSourceRef": None,
        "market": market,
        "language": "ko" if index % 2 == 0 else "en",
        "origin": "humanReviewed",
        "reviewMethod": "documentOpened",
        "reviewer": "fixture-reviewer",
        "reviewedAt": "2026-07-16T00:00:00Z",
        "reviewReceiptId": f"review:negative-{index:03d}",
    }


def _goldSet() -> tuple[list[dict], list[dict], list[dict]]:
    positives = [_positive(index) for index in range(300)]
    negatives = [_negative(index) for index in range(300)]
    predictions = [
        {"caseId": record["caseId"], "admitted": True, "status": "fact", "sourceRef": record["sourceRef"]}
        for record in positives
    ]
    predictions.extend(
        {"caseId": record["caseId"], "admitted": False, "status": "reject", "sourceRef": None} for record in negatives
    )
    return positives, negatives, predictions


def _plan() -> dict:
    return loadSamplingPlan(ROOT / "releaseGoldSamplingPlan.json")


def testSamplingPlan은300대300과모든HardNegativeType을고정한다() -> None:
    """Sampling plan의 target과 negative taxonomy를 회귀 검증한다.

    Capabilities
        300 대 300 target과 10개 negative type을 확인한다.
    AIContext
        AI 역할: 표본 수 또는 어려운 negative 유형이 조용히 축소되는 것을 막는다.
    Returns
        None.
    Example
        ``pytest -k SamplingPlan``
    Guide
        Plan 자체만 검사하며 human review completion을 주장하지 않는다.
    When
        Sampling plan 변경 시 실행한다.
    How
        Canonical JSON을 읽고 exact set을 비교한다.
    Requires
        `releaseGoldSamplingPlan.json`.
    See Also
        :func:`loadSamplingPlan`.
    Raises
        AssertionError: target 또는 taxonomy가 drift한 경우.
    """

    plan = _plan()
    assert plan["positiveTargetCount"] == 300
    assert plan["hardNegativeTargetCount"] == 300
    assert set(plan["hardNegativeQuotas"]["negativeType"]) == set(NEGATIVE_TYPES)


def test균형잡힌600건과ExactPrediction은GraduationGate를통과한다() -> None:
    """완전한 contract fixture가 graduation metric을 통과함을 검증한다.

    Capabilities
        Count, quota, precision, false acceptance, sourceRef와 set hash를 함께 확인한다.
    AIContext
        AI 역할: machine contract의 합격 경로가 실제로 도달 가능한지 검증한다.
    Returns
        None.
    Example
        ``pytest -k GraduationGate``
    Guide
        In-memory fixture는 repository의 reviewed gold 수로 계수하지 않는다.
    When
        Admission 계산식 변경 시 실행한다.
    How
        균형 잡힌 600 record와 exact prediction을 평가한다.
    Requires
        Test helper와 canonical sampling plan.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: 완전한 contract fixture가 차단된 경우.
    """

    positives, negatives, predictions = _goldSet()
    report = evaluateReleaseGold(positives, negatives, predictions, _plan())
    assert report.reviewedPositiveCount == 300
    assert report.reviewedHardNegativeCount == 300
    assert report.predictionCount == 600
    assert report.quotaViolationCount == 0
    assert report.positivePrecision == 1
    assert report.falseAcceptanceRate == 0
    assert report.sourceRefCoverage == 1
    assert report.liveReady is True
    assert report.goldSetHash and report.goldSetHash.startswith("sha256:")


def testGoldSetHash는InputOrder와무관하다() -> None:
    """Gold set hash가 JSONL input order와 무관한지 검증한다.

    Capabilities
        Positive와 negative 순서를 뒤집어도 같은 canonical hash를 만든다.
    AIContext
        AI 역할: review asset 정렬만 바뀐 것을 gold 내용 변경으로 오판하지 않는다.
    Returns
        None.
    Example
        ``pytest -k GoldSetHash``
    Guide
        Prediction order가 아니라 reviewed gold content만 hash한다.
    When
        Canonicalization 변경 시 실행한다.
    How
        같은 600 record를 정방향과 역방향으로 평가한다.
    Requires
        Complete in-memory gold fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: input order가 hash를 바꾼 경우.
    """

    positives, negatives, predictions = _goldSet()
    forward = evaluateReleaseGold(positives, negatives, predictions, _plan())
    reverse = evaluateReleaseGold(list(reversed(positives)), list(reversed(negatives)), predictions, _plan())
    assert forward.goldSetHash == reverse.goldSetHash


def testTablePositive는Header와RowHash를모두요구한다() -> None:
    """Table positive의 exact header와 row locator 경계를 검증한다.

    Capabilities
        Text positive 한 건을 table locator로 바꾸고 header hash 결손을 거부한다.
    AIContext
        AI 역할: table header drift를 row-only positive로 숨기지 않는다.
    Returns
        None.
    Example
        ``pytest -k TablePositive``
    Guide
        Table locator는 rowIndex, headerHash, rowHash를 함께 요구한다.
    When
        Table evidence schema 변경 시 실행한다.
    How
        첫 positive의 locator kind를 바꿔 합격과 결손을 차례로 평가한다.
    Requires
        Complete in-memory gold fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: incomplete table locator가 admission된 경우.
    """

    positives, negatives, predictions = _goldSet()
    tableRecord = positives[0]
    tableRecord.update(locatorKind="table", rowIndex=0, headerHash=HASH, rowHash=HASH)
    for field in ("evidenceText", "charStart", "charEnd", "snippetHash"):
        tableRecord.pop(field)
    assert evaluateReleaseGold(positives, negatives, predictions, _plan()).liveReady is True
    tableRecord.pop("headerHash")
    with pytest.raises(ValueError, match="headerHash"):
        evaluateReleaseGold(positives, negatives, predictions, _plan())


def test지원하지않는HardNegativeType은거부한다() -> None:
    """Sampling plan 밖 hard negative type을 거부하는지 검증한다.

    Capabilities
        Unknown taxonomy value가 quota unexpected로만 남지 않고 schema 단계에서 실패한다.
    AIContext
        AI 역할: 쉬운 임의 negative로 필수 failure taxonomy를 희석하지 않는다.
    Returns
        None.
    Example
        ``pytest -k HardNegativeType``
    Guide
        Negative taxonomy 변경은 sampling plan과 code를 함께 바꿔야 한다.
    When
        Hard negative category 변경 시 실행한다.
    How
        첫 negative의 type을 unknown으로 바꾼다.
    Requires
        Complete in-memory gold fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: unknown type이 admission된 경우.
    """

    positives, negatives, predictions = _goldSet()
    negatives[0]["negativeType"] = "easyRandomNegative"
    with pytest.raises(ValueError, match="unsupported negativeType"):
        evaluateReleaseGold(positives, negatives, predictions, _plan())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("origin", "synthetic", "humanReviewed"),
        ("reviewMethod", "batchImported", "documentOpened"),
        ("reviewer", "", "reviewer"),
        ("reviewedAt", "2026-07-16", "timezone-aware"),
    ],
)
def testHumanReviewMetadata가없으면FailClosed한다(field: str, value, message: str) -> None:
    """Human review metadata 변조가 fail closed하는지 검증한다.

    Capabilities
        Origin, method, reviewer, timezone을 각각 변조한다.
    AIContext
        AI 역할: synthetic 또는 batch metadata를 human review로 위장하지 못하게 한다.
    Args
        field: 변조할 review field.
        value: 대체 값.
        message: 예상 오류 일부.
    Returns
        None.
    Example
        ``pytest -k HumanReviewMetadata``
    Guide
        Parametrize case 모두 ValueError를 요구한다.
    When
        Review receipt schema 변경 시 실행한다.
    How
        첫 positive를 변조하고 evaluator를 호출한다.
    Requires
        Complete in-memory gold fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: invalid review가 admission된 경우.
    """

    positives, negatives, predictions = _goldSet()
    positives[0][field] = value
    with pytest.raises(ValueError, match=message):
        evaluateReleaseGold(positives, negatives, predictions, _plan())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("sourceVersion", "adapter-v1", "sha256"),
        ("charEnd", 11, "length"),
        ("availableAt", "2025-01-01T00:00:00Z", "sourcePublishedAt"),
        ("expectedStatus", "candidate", "must be fact"),
    ],
)
def testPositiveExactEvidence가변조되면거부한다(field: str, value, message: str) -> None:
    """Positive exact evidence와 time 변조를 거부하는지 검증한다.

    Capabilities
        Source version, locator, time, status의 fail-closed 경계를 검사한다.
    AIContext
        AI 역할: section candidate를 exact positive로 과대 승격하지 못하게 한다.
    Args
        field: 변조할 positive field.
        value: 대체 값.
        message: 예상 오류 일부.
    Returns
        None.
    Example
        ``pytest -k PositiveExactEvidence``
    Guide
        각 mutation은 독립 record에서 실행한다.
    When
        Evidence admission 규칙 변경 시 실행한다.
    How
        첫 positive를 변조하고 ValueError를 확인한다.
    Requires
        Complete in-memory gold fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: invalid evidence가 admission된 경우.
    """

    positives, negatives, predictions = _goldSet()
    positives[0][field] = value
    with pytest.raises(ValueError, match=message):
        evaluateReleaseGold(positives, negatives, predictions, _plan())


def testFalseAcceptance1퍼센트경계를엄격히적용한다() -> None:
    """Hard negative false acceptance의 inclusive 1% 경계를 검증한다.

    Capabilities
        3/300은 허용하고 4/300은 차단한다.
    AIContext
        AI 역할: 반올림으로 1% 초과를 합격 처리하지 못하게 한다.
    Returns
        None.
    Example
        ``pytest -k FalseAcceptance``
    Guide
        Exact fraction을 사용하고 표시용 반올림을 사용하지 않는다.
    When
        Release threshold 계산 변경 시 실행한다.
    How
        Negative prediction 3개와 4개를 차례로 fact로 변조한다.
    Requires
        Complete 300 negative fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: threshold 경계가 바뀐 경우.
    """

    positives, negatives, predictions = _goldSet()
    for index in range(3):
        predictions[300 + index].update(admitted=True, status="fact")
    assert evaluateReleaseGold(positives, negatives, predictions, _plan()).liveReady is True
    predictions[303].update(admitted=True, status="fact")
    report = evaluateReleaseGold(positives, negatives, predictions, _plan())
    assert report.falseAcceptanceRate == pytest.approx(4 / 300)
    assert report.liveReady is False
    assert "falseAcceptanceAbove1Pct" in report.blockerReasons


def testPositivePrecision98퍼센트미만을차단한다() -> None:
    """Positive exact precision 98% 미만을 차단하는지 검증한다.

    Capabilities
        293/300 exact admission이 release blocker를 만드는지 확인한다.
    AIContext
        AI 역할: missing exact sourceRef를 단순 성공으로 계수하지 못하게 한다.
    Returns
        None.
    Example
        ``pytest -k PositivePrecision``
    Guide
        Positive prediction은 admitted와 fact와 exact sourceRef를 모두 만족해야 한다.
    When
        Positive metric 변경 시 실행한다.
    How
        7개 positive prediction을 candidate로 바꾼다.
    Requires
        Complete 300 positive fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: 98% 미만이 합격한 경우.
    """

    positives, negatives, predictions = _goldSet()
    for index in range(7):
        predictions[index].update(admitted=False, status="candidate")
    report = evaluateReleaseGold(positives, negatives, predictions, _plan())
    assert report.positivePrecision == pytest.approx(293 / 300)
    assert report.liveReady is False
    assert "positivePrecisionBelow98Pct" in report.blockerReasons


def testCount와Quota와PredictionCompleteness를모두요구한다() -> None:
    """Count, quota, prediction completeness가 독립 blocker인지 검증한다.

    Capabilities
        Positive 1건과 prediction 1건 결손을 세 blocker로 보존한다.
    AIContext
        AI 역할: 불완전 sample의 높은 비율로 graduation을 주장하지 못하게 한다.
    Returns
        None.
    Example
        ``pytest -k Completeness``
    Guide
        Count와 quota와 prediction을 각각 확인한다.
    When
        Completeness gate 변경 시 실행한다.
    How
        Positive와 대응 prediction 한 건을 제거한다.
    Requires
        Complete fixture에서 시작한다.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: 불완전 sample이 합격한 경우.
    """

    positives, negatives, predictions = _goldSet()
    positives.pop()
    predictions.pop(299)
    report = evaluateReleaseGold(positives, negatives, predictions, _plan())
    assert report.liveReady is False
    assert "reviewedPositiveCountIncomplete" in report.blockerReasons
    assert "predictionCountIncomplete" in report.blockerReasons
    assert "samplingQuotaViolation" in report.blockerReasons


def testDuplicateReviewReceipt와UnknownPrediction을거부한다() -> None:
    """Duplicate review receipt와 unknown prediction을 거부하는지 검증한다.

    Capabilities
        Review provenance uniqueness와 prediction case closure를 확인한다.
    AIContext
        AI 역할: 한 review를 여러 gold에 재사용하거나 extra prediction을 숨기지 못하게 한다.
    Returns
        None.
    Example
        ``pytest -k DuplicateReviewReceipt``
    Guide
        Duplicate와 unknown case를 별도 fresh fixture에서 검사한다.
    When
        Receipt 또는 prediction schema 변경 시 실행한다.
    How
        Receipt ID를 복제한 뒤 unknown case prediction을 추가한다.
    Requires
        Complete in-memory gold fixture.
    See Also
        :func:`evaluateReleaseGold`.
    Raises
        AssertionError: duplicate 또는 unknown case가 허용된 경우.
    """

    positives, negatives, predictions = _goldSet()
    positives[1]["reviewReceiptId"] = positives[0]["reviewReceiptId"]
    with pytest.raises(ValueError, match="duplicate reviewReceiptId"):
        evaluateReleaseGold(positives, negatives, predictions, _plan())
    positives, negatives, predictions = _goldSet()
    predictions.append({"caseId": "unknown", "admitted": False, "status": "reject", "sourceRef": None})
    with pytest.raises(ValueError, match="unknown caseId"):
        evaluateReleaseGold(positives, negatives, predictions, _plan())


def testMissingRepositoryReviewAsset은0대300으로보존한다(tmp_path: Path) -> None:
    """Missing review asset을 0/300 blocker로 보존하는지 검증한다.

    Capabilities
        Optional JSONL 부재와 canonical plan 존재를 분리한다.
    AIContext
        AI 역할: missing file을 empty-but-passing gold로 오판하지 않는다.
    Args
        tmp_path: Review JSONL이 없는 격리 directory.
    Returns
        None.
    Example
        ``pytest -k MissingRepositoryReviewAsset``
    Guide
        Contract ready와 live ready를 구분한다.
    When
        Repository census 동작 변경 시 실행한다.
    How
        존재하지 않는 세 JSONL path를 inspector에 전달한다.
    Requires
        Canonical sampling plan.
    See Also
        :func:`inspectReleaseGoldFiles`.
    Raises
        AssertionError: missing asset이 live ready가 된 경우.
    """

    report = inspectReleaseGoldFiles(
        tmp_path / "reviewedPositive.jsonl",
        tmp_path / "hardNegative.jsonl",
        tmp_path / "admissionPredictions.jsonl",
        ROOT / "releaseGoldSamplingPlan.json",
    )
    assert report.reviewedPositiveCount == 0
    assert report.reviewedHardNegativeCount == 0
    assert report.predictionCount == 0
    assert report.contractReady is True
    assert report.liveReady is False
    assert report.goldSetHash is None


def testMalformedExistingJsonl은조용히무시하지않는다(tmp_path: Path) -> None:
    """존재하는 malformed JSONL을 조용히 빈 파일로 취급하지 않는지 검증한다.

    Capabilities
        File absence와 file corruption의 다른 실패 의미를 고정한다.
    AIContext
        AI 역할: 깨진 review 자산을 0건 census로 숨기지 않는다.
    Args
        tmp_path: Malformed JSONL을 만드는 격리 directory.
    Returns
        None.
    Example
        ``pytest -k MalformedExistingJsonl``
    Guide
        Existing malformed file은 ValueError여야 한다.
    When
        JSONL loader 변경 시 실행한다.
    How
        Invalid JSON 한 줄을 쓰고 inspector를 호출한다.
    Requires
        Writable pytest tmp_path와 canonical sampling plan.
    See Also
        :func:`inspectReleaseGoldFiles`.
    Raises
        AssertionError: corruption이 무시된 경우.
    """

    malformed = tmp_path / "reviewedPositive.jsonl"
    malformed.write_text("{invalid}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSONL"):
        inspectReleaseGoldFiles(
            malformed,
            tmp_path / "hardNegative.jsonl",
            tmp_path / "admissionPredictions.jsonl",
            ROOT / "releaseGoldSamplingPlan.json",
        )
