"""현재 공개 edge의 factual admission 필드를 독립적으로 검증한다.

Capabilities
    ecosystem edge에서 stable source ref, document ID, section, exact locator,
    direction proof, source time, validity, public policy receipt, status를 각각
    계수하고 모든 조건을 통과한 edge만 admitted로 센다.

Args
    CLI의 ``source``는 HTTP(S) URL 또는 ecosystem JSON 파일 경로다.

Returns
    :class:`FactualAdmissionReport`를 stdout JSON으로 출력한다.

Example
    ``uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/factualAdmissionProbe.py``

Guide
    count가 높은 단일 필드로 사실성을 추정하지 않는다. ``admittedEdgeCount``는
    모든 필수 필드와 시간 검증을 동시에 통과한 edge만 포함한다.

SeeAlso
    ``mainPlan/dartlab-universe/08-attempts-evidence-matrix.md`` U0-T02.

Requires
    Python 표준 라이브러리와 U0-T01의 ecosystem loader만 사용한다.

AIContext
    AI 역할: 현재 map edge를 factual graph로 승격할 수 있는지 fail-closed로
    검증한다. relation 추출이나 evidence 보강은 수행하지 않는다.

LLM Specifications
    AntiPatterns: rceptNo 또는 confidence 하나만으로 observed를 승인하지 않는다.
    OutputSchema: FactualAdmissionReport의 JSON 직렬화 형태다.
    Prerequisites: ecosystem schema에 nodes와 links가 있어야 한다.
    Freshness: 실행 시점의 remote artifact 또는 명시 fixture 기준이다.
    Dataflow: source -> ecosystem edge -> field admission -> stdout JSON.
    TargetMarkets: 현재 KR map, 이후 같은 edge contract의 시장.

결과
    2026-07-15 live ecosystem 20,560 edge에서 document ID, sectionPath, exact
    locator, direction proof, sourcePublishedAt, availableAt, validFrom, policy
    receipt, observed status와 admitted edge가 모두 0건이었다. self-loop은 13건이다.
    따라서 기존 edge를 candidate topology로 유지한다.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

if __package__:
    from .graphTruthProbe import DEFAULT_SOURCE, loadGraphPayload
else:
    from graphTruthProbe import DEFAULT_SOURCE, loadGraphPayload

DOCUMENT_ID_FIELDS = ("docId", "rceptNo", "accessionNo")
TABLE_ROW_FIELDS = ("rowKey", "rowIndex", "cellRef")
ADMITTED_STATUSES = frozenset({"observed", "corroborated"})


@dataclass(frozen=True)
class FactualAdmissionReport:
    """Edge factual admission coverage를 요약한다.

    Capabilities
        필수 factual field별 coverage와 rejection reason을 보존한다.

    Args
        모든 count는 입력 edge 전체를 분모로 하는 정수다.

    Returns
        JSON 직렬화 가능한 immutable report.

    Example
        ``report.toDict()``

    Guide
        ``admittedEdgeCount`` 이외의 단일 coverage를 사실 수로 사용하지 않는다.

    SeeAlso
        :func:`inspectFactualAdmission`.

    Requires
        없음.

    AIContext
        AI 역할: factual admission의 필드별 결손을 설명한다.

    LLM Specifications
        AntiPatterns: rejection reason count 합을 rejected edge 수로 해석하지 않는다.
        OutputSchema: 선언된 dataclass 필드.
        Prerequisites: 없음.
        Freshness: 입력 payload 기준.
        Dataflow: report -> asdict.
        TargetMarkets: market neutral.
    """

    sourceVersion: str
    edgeCount: int
    stableSourceRefCount: int
    documentIdCount: int
    sectionPathCount: int
    exactLocatorCount: int
    directionVerifiedCount: int
    sourcePublishedAtCount: int
    availableAtCount: int
    validFromCount: int
    policyReceiptCount: int
    observedStatusCount: int
    invalidSourceTimeCount: int
    invalidValidityCount: int
    selfLoopCount: int
    admittedEdgeCount: int
    rejectionReasonCounts: dict[str, int]
    predicateAdmissionCounts: dict[str, int]
    sourceTagAdmissionCounts: dict[str, int]

    def toDict(self) -> dict[str, Any]:
        """Report를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            dataclass 선언 순서를 보존한 dict.

        Example
            ``json.dumps(report.toDict())``

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


def _filled(edge: dict[str, Any], field: str) -> bool:
    return edge.get(field) not in (None, "", [])


def _hasAny(edge: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return any(_filled(edge, field) for field in fields)


def _hasExactLocator(edge: dict[str, Any]) -> bool:
    hasCharSpan = _filled(edge, "charStart") and _filled(edge, "charEnd")
    hasLineSpan = _filled(edge, "lineStart") and _filled(edge, "lineEnd")
    hasTableRow = _filled(edge, "tableRef") and _hasAny(edge, TABLE_ROW_FIELDS)
    return hasCharSpan or hasLineSpan or hasTableRow


def _parseDatetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _sourceTimeInvalid(edge: dict[str, Any]) -> bool:
    publishedAt = _parseDatetime(edge.get("sourcePublishedAt"))
    availableAt = _parseDatetime(edge.get("availableAt"))
    if publishedAt is None or availableAt is None:
        return False
    return publishedAt > availableAt


def _validityInvalid(edge: dict[str, Any]) -> bool:
    validFrom = _parseDatetime(edge.get("validFrom"))
    validTo = _parseDatetime(edge.get("validTo"))
    if validFrom is None or validTo is None:
        return False
    return validFrom > validTo


def _rejectionReasons(edge: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if str(edge.get("source", "")) == str(edge.get("target", "")):
        reasons.append("selfLoop")
    if not _filled(edge, "sourceRef"):
        reasons.append("missingSourceRef")
    if not _hasAny(edge, DOCUMENT_ID_FIELDS):
        reasons.append("missingDocumentId")
    if not _filled(edge, "sectionPath"):
        reasons.append("missingSectionPath")
    if not _hasExactLocator(edge):
        reasons.append("missingExactLocator")
    directionStatus = str(edge.get("directionStatus", "")).casefold()
    if edge.get("directionVerified") is not True and directionStatus != "verified":
        reasons.append("directionUnverified")
    if not _filled(edge, "sourcePublishedAt"):
        reasons.append("missingSourcePublishedAt")
    if not _filled(edge, "availableAt"):
        reasons.append("missingAvailableAt")
    if not _filled(edge, "validFrom"):
        reasons.append("missingValidFrom")
    if not _filled(edge, "redistributionReceiptId"):
        reasons.append("missingPolicyReceipt")
    if str(edge.get("status", "")).casefold() not in ADMITTED_STATUSES:
        reasons.append("statusNotObserved")
    if _sourceTimeInvalid(edge):
        reasons.append("invalidSourceTime")
    if _validityInvalid(edge):
        reasons.append("invalidValidity")
    return reasons


def inspectFactualAdmission(payload: dict[str, Any]) -> FactualAdmissionReport:
    """모든 필수 factual field를 동시에 적용해 edge admission을 측정한다.

    Capabilities
        field coverage, temporal 오류, predicate/source별 admitted count를 계산한다.

    Args
        payload: ecosystem ``nodes``와 ``links``를 가진 dict.

    Returns
        deterministic :class:`FactualAdmissionReport`.

    Example
        ``report = inspectFactualAdmission(payload)``

    Guide
        미래 validFrom은 허용한다. sourcePublishedAt이 availableAt보다 늦는 경우와
        validFrom이 validTo보다 늦는 경우만 시간 오류로 차단한다.

    SeeAlso
        :func:`_rejectionReasons`.

    Requires
        edge마다 source, target, type이 있어야 한다.

    AIContext
        AI 역할: candidate topology와 factual relation 사이의 admission gap을 센다.

    LLM Specifications
        AntiPatterns: confidence를 admission field로 사용하지 않는다.
        OutputSchema: FactualAdmissionReport.
        Prerequisites: links list.
        Freshness: payload 기준.
        Dataflow: links -> reasons -> counts.
        TargetMarkets: market neutral.

    Raises
        ValueError: payload 또는 edge의 필수 presentation field가 없을 때.
    """

    edges = payload.get("links")
    if not isinstance(edges, list):
        raise ValueError("ecosystem payload must contain a links list")

    coverage: Counter[str] = Counter()
    rejectionReasons: Counter[str] = Counter()
    predicateAdmission: Counter[str] = Counter()
    sourceTagAdmission: Counter[str] = Counter()
    admittedEdgeCount = 0
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("every edge must be a JSON object")
        sourceId = str(edge.get("source", ""))
        targetId = str(edge.get("target", ""))
        predicate = str(edge.get("type", ""))
        if not sourceId or not targetId or not predicate:
            raise ValueError("every edge must have source, target, and type")

        coverage["stableSourceRefCount"] += int(_filled(edge, "sourceRef"))
        coverage["documentIdCount"] += int(_hasAny(edge, DOCUMENT_ID_FIELDS))
        coverage["sectionPathCount"] += int(_filled(edge, "sectionPath"))
        coverage["exactLocatorCount"] += int(_hasExactLocator(edge))
        directionStatus = str(edge.get("directionStatus", "")).casefold()
        coverage["directionVerifiedCount"] += int(
            edge.get("directionVerified") is True or directionStatus == "verified"
        )
        coverage["sourcePublishedAtCount"] += int(_filled(edge, "sourcePublishedAt"))
        coverage["availableAtCount"] += int(_filled(edge, "availableAt"))
        coverage["validFromCount"] += int(_filled(edge, "validFrom"))
        coverage["policyReceiptCount"] += int(_filled(edge, "redistributionReceiptId"))
        coverage["observedStatusCount"] += int(str(edge.get("status", "")).casefold() in ADMITTED_STATUSES)
        coverage["invalidSourceTimeCount"] += int(_sourceTimeInvalid(edge))
        coverage["invalidValidityCount"] += int(_validityInvalid(edge))
        coverage["selfLoopCount"] += int(sourceId == targetId)

        reasons = _rejectionReasons(edge)
        rejectionReasons.update(reasons)
        if not reasons:
            admittedEdgeCount += 1
            predicateAdmission[predicate] += 1
            sourceTagAdmission[str(edge.get("source_tag", "unknown"))] += 1

    return FactualAdmissionReport(
        sourceVersion=str(payload.get("version", "unknown")),
        edgeCount=len(edges),
        stableSourceRefCount=coverage["stableSourceRefCount"],
        documentIdCount=coverage["documentIdCount"],
        sectionPathCount=coverage["sectionPathCount"],
        exactLocatorCount=coverage["exactLocatorCount"],
        directionVerifiedCount=coverage["directionVerifiedCount"],
        sourcePublishedAtCount=coverage["sourcePublishedAtCount"],
        availableAtCount=coverage["availableAtCount"],
        validFromCount=coverage["validFromCount"],
        policyReceiptCount=coverage["policyReceiptCount"],
        observedStatusCount=coverage["observedStatusCount"],
        invalidSourceTimeCount=coverage["invalidSourceTimeCount"],
        invalidValidityCount=coverage["invalidValidityCount"],
        selfLoopCount=coverage["selfLoopCount"],
        admittedEdgeCount=admittedEdgeCount,
        rejectionReasonCounts=dict(sorted(rejectionReasons.items())),
        predicateAdmissionCounts=dict(sorted(predicateAdmission.items())),
        sourceTagAdmissionCounts=dict(sorted(sourceTagAdmission.items())),
    )


def main() -> int:
    """CLI source를 검사하고 factual admission report를 출력한다.

    Args
        없음. argparse가 CLI 인자를 읽는다.

    Returns
        성공 시 0.

    Example
        ``python factualAdmissionProbe.py --source ecosystem.json``

    Raises
        source load와 schema 오류를 숨기지 않는다.
    """

    parser = argparse.ArgumentParser(description="Inspect factual admission fields in ecosystem edges")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    args = parser.parse_args()
    report = inspectFactualAdmission(loadGraphPayload(args.source))
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
