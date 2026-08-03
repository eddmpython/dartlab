"""설치형 런타임 답변을 공개하기 전 적용하는 결정론 품질 파이프라인."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

from .answerQualityParser import (
    _compactNumberText,
    _compactSemantic,
    _compactText,
    _coversQuestionMetrics,
    _dateCandidates,
    _evidencePeriods,
    _financialAmounts,
    _isConcreteScalar,
    _metricId,
    _payload,
    _qualitativeValueBinds,
    _questionPeriods,
    _questionTargetLabels,
    _requestedMetrics,
    _targetCodes,
    _targetLabels,
    _valueCandidates,
)

EvidenceContract = Literal["quantitative", "documentary"]

_QUANTITATIVE_HINTS = (
    "%",
    "amount",
    "cagr",
    "eps",
    "growth",
    "margin",
    "per",
    "revenue",
    "roe",
    "value",
    "가격",
    "금액",
    "매출",
    "부채",
    "비교",
    "비율",
    "수익",
    "얼마",
    "영업이익",
    "증가",
    "추이",
    "현금",
)
_DOCUMENTARY_HINTS = (
    "audit opinion",
    "contract",
    "disclosure",
    "governance",
    "lawsuit",
    "risk factor",
    "감사의견",
    "핵심감사사항",
    "계약 내용",
    "공시 내용",
    "소송",
    "위험 요인",
    "주석 내용",
    "지배구조",
)

_TABLE_CONTENT_KEYS = ("rows", "records", "timeseries", "matrix", "table", "data", "items", "values", "axes")


@dataclass(frozen=True)
class AnswerQualityReport:
    """공개 가능 여부와 실패 원인을 담는 content-free 품질 결과."""

    passed: bool
    contract: EvidenceContract
    score: int
    issues: tuple[str, ...]
    citedRefIds: tuple[str, ...]
    contractIds: tuple[str, ...]
    requiredEvidence: tuple[str, ...]
    readSkillCalls: int | None
    requiredClaimCells: int
    coveredClaimCells: int

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화 가능한 공개 품질 요약을 반환한다."""
        return asdict(self)


def classifyEvidenceContract(question: str) -> EvidenceContract:
    """질문이 수치 근거와 문서 근거 중 무엇을 요구하는지 보수적으로 분류한다."""
    normalized = question.casefold()
    if any(hint in normalized for hint in _QUANTITATIVE_HINTS):
        return "quantitative"
    if any(hint in normalized for hint in _DOCUMENTARY_HINTS):
        return "documentary"
    return "quantitative"


def evaluateAnswerQuality(
    question: str,
    answer: str,
    refs: list[dict[str, Any]],
    *,
    completionSucceeded: bool,
    failed: bool,
    readSkillCalls: int | None = None,
) -> AnswerQualityReport:
    """종료 상태, exact citation, 값과 시점 binding을 모두 검사한다."""
    from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion

    contract = classifyEvidenceContract(question)
    coverage = coveragePacketForQuestion(question)
    contractIds = tuple(str(value) for value in coverage.get("contractIds") or ())
    requiredEvidence = tuple(str(value) for value in coverage.get("requiredEvidence") or ())
    issues: list[str] = []
    cleanAnswer = answer.strip()
    canonicalRefs = [ref for ref in refs if isinstance(ref, dict) and ref.get("id") and ref.get("kind")]
    cited = _citedRefs(cleanAnswer, canonicalRefs)
    evidenceIssues = _evidenceIssues(cited)
    usableCited = [ref for ref in cited if _isUsableEvidence(ref)]
    citedKinds = {str(ref["kind"]) for ref in usableCited}
    prose = _withoutCitations(cleanAnswer, cited)
    documentaryRequired = contract == "documentary" or "docRef" in requiredEvidence

    issues.extend(
        _completionIssues(
            cleanAnswer,
            completionSucceeded=completionSucceeded,
            failed=failed,
            readSkillCalls=readSkillCalls,
            coverageRequired=bool(contractIds or coverage.get("candidateCapabilityRefs")),
        )
    )
    issues.extend(evidenceIssues)
    issues.extend(
        _sourceContractIssues(
            question,
            prose,
            usableCited,
            citedKinds,
            contract=contract,
            documentaryRequired=documentaryRequired,
        )
    )
    issues.extend(_bindingContractIssues(question, prose, usableCited, citedKinds, contract=contract))
    issues.extend(
        _coverageContractIssues(
            question,
            canonicalRefs,
            usableCited,
            coverage,
            contract=contract,
            documentaryRequired=documentaryRequired,
        )
    )

    requiredClaimCells, coveredClaimCells = _claimCellCoverage(question, usableCited)

    uniqueIssues = tuple(dict.fromkeys(issues))
    score = max(0, 100 - 20 * len(uniqueIssues))
    return AnswerQualityReport(
        passed=not uniqueIssues,
        contract=contract,
        score=score,
        issues=uniqueIssues,
        citedRefIds=tuple(str(ref["id"]) for ref in cited),
        contractIds=contractIds,
        requiredEvidence=requiredEvidence,
        readSkillCalls=readSkillCalls,
        requiredClaimCells=requiredClaimCells,
        coveredClaimCells=coveredClaimCells,
    )


def claimCellContractForQuestion(
    question: str,
    *,
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """질문의 대상 x 지표 x 기간 완결 조건을 런타임용 구조로 반환한다."""
    metrics = [name for name, _aliases in _requestedMetrics(question)]
    explicitPeriods = sorted(_questionPeriods(question))
    recentMatch = re.search(r"최근\s*(\d{1,2})\s*(?:개\s*)?(분기|년|연도)", question.casefold())
    if not metrics or (not explicitPeriods and recentMatch is None):
        return {}

    comparisonPolicy = comparison or {}
    comparisonRequired = _requiresMultipleTargets(question, comparisonPolicy)
    targetCodes = sorted(set(re.findall(r"(?<!\d)\d{6}(?!\d)", question)))
    targetLabels = sorted(_questionTargetLabels(question)) if not targetCodes and comparisonRequired else []
    requestedMinimum = max(1, int(comparisonPolicy.get("minTargets") or 1)) if comparisonRequired else 1
    targetCount = max(len(targetCodes), len(targetLabels), requestedMinimum)
    targets = targetCodes or targetLabels or [f"questionTarget:{index + 1}" for index in range(targetCount)]
    if len(targets) < targetCount:
        targets.extend(f"questionTarget:{index + 1}" for index in range(len(targets), targetCount))

    if explicitPeriods:
        periodContract: dict[str, Any] = {"kind": "explicit", "periods": explicitPeriods}
        periodCount = len(explicitPeriods)
    else:
        assert recentMatch is not None
        periodCount = int(recentMatch.group(1))
        periodContract = {
            "kind": "recent",
            "count": periodCount,
            "unit": "fiscal_quarter" if recentMatch.group(2) == "분기" else "fiscal_year",
        }

    return {
        "targets": targets,
        "targetCount": targetCount,
        "metrics": metrics,
        "period": periodContract,
        "requiredCells": targetCount * len(metrics) * periodCount,
        "completionRule": "every_target_metric_period_requires_canonical_value_ref",
    }


def _completionIssues(
    cleanAnswer: str,
    *,
    completionSucceeded: bool,
    failed: bool,
    readSkillCalls: int | None,
    coverageRequired: bool,
) -> list[str]:
    """native 완료와 질문별 Skill 탐색 계약의 실패를 모은다."""
    issues: list[str] = []
    if failed or not completionSucceeded:
        issues.append("runtime_not_completed")
    if readSkillCalls is not None and coverageRequired:
        if readSkillCalls == 0:
            issues.append("read_skill_missing")
        elif readSkillCalls > 1:
            issues.append("read_skill_repeated")
    if not cleanAnswer:
        issues.append("empty_answer")
    return issues


def _sourceContractIssues(
    question: str,
    prose: str,
    cited: list[dict[str, Any]],
    citedKinds: set[str],
    *,
    contract: EvidenceContract,
    documentaryRequired: bool,
) -> list[str]:
    """질문 유형에 필요한 표·문서·값·기준일 근거의 존재를 검사한다."""
    issues: list[str] = []
    if not ({"tableRef", "docRef"} & citedKinds):
        issues.append("source_ref_missing")
    if documentaryRequired and "docRef" not in citedKinds:
        issues.append("document_ref_missing")
    if documentaryRequired and "docRef" in citedKinds and not _coversDocumentaryClaims(question, prose, cited):
        issues.append("document_claim_mismatch")
    if "dateRef" not in citedKinds:
        issues.append("date_ref_missing")
    if contract == "quantitative" and "valueRef" not in citedKinds:
        issues.append("value_ref_missing")
    return issues


def _bindingContractIssues(
    question: str,
    prose: str,
    cited: list[dict[str, Any]],
    citedKinds: set[str],
    *,
    contract: EvidenceContract,
) -> list[str]:
    """답변 산문이 인용한 값과 기준일 payload를 실제로 말하는지 검사한다."""
    issues: list[str] = []
    if contract == "quantitative" and "valueRef" in citedKinds and not _hasBoundValue(prose, cited):
        issues.append("value_binding_mismatch")
    if "dateRef" in citedKinds and not _hasBoundDate(prose, cited, question=question):
        issues.append("date_binding_mismatch")
    return issues


def _coverageContractIssues(
    question: str,
    canonicalRefs: list[dict[str, Any]],
    cited: list[dict[str, Any]],
    coverage: dict[str, Any],
    *,
    contract: EvidenceContract,
    documentaryRequired: bool,
) -> list[str]:
    """질문의 기간·비교 대상·지표가 cited evidence에 모두 포함됐는지 검사한다."""
    issues: list[str] = []
    if (contract == "quantitative" or documentaryRequired) and not _coversQuestionPeriods(question, cited):
        issues.append("period_coverage_incomplete")
    comparison = coverage.get("comparisonCompleteness") or {}
    minimumTargets = int(comparison.get("minTargets") or 2)
    if _requiresMultipleTargets(question, comparison) and _targetCount(cited) < minimumTargets:
        issues.append("comparison_target_incomplete")
    if contract == "quantitative" and not _coversQuestionTargets(question, canonicalRefs, cited, comparison):
        issues.append("target_evidence_mismatch")
    if contract == "quantitative" and not _coversQuestionMetrics(question, cited):
        issues.append("metric_evidence_mismatch")
    requiredCells, coveredCells = _claimCellCoverage(question, cited)
    if contract == "quantitative" and requiredCells and coveredCells < requiredCells:
        issues.append("claim_cell_coverage_incomplete")
    return issues


def _claimCellCoverage(question: str, cited: list[dict[str, Any]]) -> tuple[int, int]:
    """질문이 요구한 대상 x 지표 x 기간 셀을 valueRef 단위로 대조한다."""
    metrics = [name for name, _aliases in _requestedMetrics(question)]
    if not metrics:
        return 0, 0
    explicitPeriods = _questionPeriods(question)
    recentMatch = re.search(r"최근\s*(\d{1,2})\s*(?:개\s*)?(분기|년|연도)", question.casefold())
    if not explicitPeriods and recentMatch is None:
        return 0, 0

    requestedTargets = set(re.findall(r"(?<!\d)\d{6}(?!\d)", question))
    targets: tuple[str | None, ...] = tuple(sorted(requestedTargets)) if requestedTargets else (None,)
    valueRefs = [ref for ref in cited if ref.get("kind") == "valueRef"]

    def _matchingPeriods(metric: str, target: str | None) -> set[str]:
        """하나의 대상과 지표를 증명하는 canonical 기간 집합을 반환한다."""
        periods: set[str] = set()
        for ref in valueRefs:
            if _metricId(ref) != metric:
                continue
            if target is not None and target not in _targetCodes(ref):
                continue
            periods.update(_evidencePeriods([ref]))
        return periods

    if explicitPeriods:
        required = len(targets) * len(metrics) * len(explicitPeriods)
        covered = sum(
            1
            for target in targets
            for metric in metrics
            for period in explicitPeriods
            if period in _matchingPeriods(metric, target)
        )
        return required, covered

    assert recentMatch is not None
    requiredCount = int(recentMatch.group(1))
    wantsQuarters = recentMatch.group(2) == "분기"
    required = len(targets) * len(metrics) * requiredCount
    covered = 0
    for target in targets:
        for metric in metrics:
            periods = _matchingPeriods(metric, target)
            relevant = {period for period in periods if ("Q" in period) == wantsQuarters}
            covered += min(requiredCount, len(relevant))
    return required, covered


def _hasBoundValue(prose: str, cited: list[dict[str, Any]]) -> bool:
    """각 cited value가 원값 또는 표시 단위의 정당한 반올림으로 본문에 있는지 확인한다."""
    payloads = [
        _payload(ref)
        for ref in cited
        if ref.get("kind") == "valueRef" and _isConcreteScalar(_payload(ref).get("value"))
    ]
    if not payloads:
        return False
    compact = _compactNumberText(prose)
    normalized = _compactText(prose)
    amounts = _financialAmounts(prose)

    def binds(payload: dict[str, Any]) -> bool:
        """하나의 value payload가 답변의 숫자 또는 표시값과 결합됐는지 판정한다."""
        value = payload["value"]
        if any(candidate and candidate in compact for candidate in _valueCandidates(value)):
            return True
        if isinstance(value, str) and payload.get("label") and _qualitativeValueBinds(prose, value):
            return True
        formatted = payload.get("formatted")
        if isinstance(formatted, str) and _compactText(formatted) in normalized:
            return True
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            expected = float(value)
            return any(abs(amount - expected) <= tolerance for amount, tolerance in amounts)
        return False

    bound = [binds(payload) for payload in payloads]
    if all(bound):
        return True

    # bear/base/bull 전체 ref를 함께 인용하면서 본문에는 범위의 양 끝값만 쓰는
    # 정상적인 투자 문장을 허용한다. 동일 target·period의 canonical matrix가 실제
    # 세 시나리오를 담고 있고 두 끝값이 결합된 경우에만 생략된 중간값을 인정한다.
    families: dict[tuple[str, str, str, str], list[int]] = {}
    for index, payload in enumerate(payloads):
        family = _scenarioFamilyKey(payload)
        if family is not None:
            families.setdefault(family, []).append(index)
    for family, indexes in families.items():
        if len(indexes) < 3 or sum(bound[index] for index in indexes) < 2:
            continue
        if not _hasScenarioMatrix(cited, family, payloads, indexes):
            continue
        for index in indexes:
            bound[index] = True
    return all(bound)


def _scenarioFamilyKey(payload: dict[str, Any]) -> tuple[str, str, str, str] | None:
    """하나의 가치평가 시나리오 군을 식별하는 보수적 키를 반환한다."""
    if not _scenarioName(payload) or not isinstance(payload.get("value"), (int, float)):
        return None
    target = str(payload.get("stockCode") or payload.get("target") or "")
    period = str(payload.get("period") or "")
    axis = str(payload.get("axis") or "")
    unit = str(payload.get("unit") or payload.get("currency") or "")
    if not target or not period or axis != "valuation":
        return None
    return target, period, axis, unit


def _scenarioName(payload: dict[str, Any]) -> str:
    """명시 scenario 또는 canonical valuation metric suffix를 읽는다."""
    direct = str(payload.get("scenario") or "").casefold()
    if direct in {"bear", "base", "bull"}:
        return direct
    metric = str(payload.get("metric") or payload.get("canonicalMetricId") or "").casefold()
    match = re.search(r"(?:^|_)(bear|base|bull)$", metric)
    return match.group(1) if match else ""


def _hasScenarioMatrix(
    cited: list[dict[str, Any]],
    family: tuple[str, str, str, str],
    payloads: list[dict[str, Any]],
    indexes: list[int],
) -> bool:
    """cited tableRef가 같은 시나리오 군의 행을 실제로 포함하는지 확인한다."""
    target, period, _axis, unit = family
    expected = {_scenarioName(payloads[index]) for index in indexes}
    for ref in cited:
        if ref.get("kind") != "tableRef":
            continue
        payload = _payload(ref)
        if str(payload.get("stockCode") or payload.get("target") or "") != target:
            continue
        if str(payload.get("period") or "") != period:
            continue
        if unit and str(payload.get("unit") or payload.get("currency") or "") != unit:
            continue
        rows = payload.get("rows")
        if not isinstance(rows, list):
            continue
        observed = {
            str(row.get("scenario") or "")
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("perShareValue") or row.get("value"), (int, float))
        }
        if expected.issubset(observed):
            return True
    return False


def _hasBoundDate(prose: str, cited: list[dict[str, Any]], *, question: str = "") -> bool:
    """payload가 제공된 cited date 각각의 기간 또는 기준일이 본문에 있는지 확인한다."""
    candidateGroups: list[set[str]] = []
    requestedPeriods = _questionPeriods(question)
    for ref in cited:
        if ref.get("kind") != "dateRef":
            continue
        payload = _payload(ref)
        candidates: set[str] = set()
        for key in ("period", "dataAsOf", "asOf", "knowledgeBoundary", "requestedAsOf", "value"):
            value = payload.get(key)
            if _isConcreteScalar(value):
                text = str(value)
                candidates.update(_dateCandidates(text))
                quarter = re.fullmatch(r"(\d{4})Q[1-4]", text.upper())
                if quarter and quarter.group(1) in requestedPeriods and text.upper() not in requestedPeriods:
                    candidates.update(_dateCandidates(quarter.group(1)))
        if candidates:
            candidateGroups.append(candidates)
    if not candidateGroups:
        return False
    normalized = _compactText(prose)
    return all(any(candidate in normalized for candidate in candidates) for candidates in candidateGroups)


def _coversQuestionPeriods(question: str, cited: list[dict[str, Any]]) -> bool:
    """명시 기간과 최근 N개 기간 요구를 cited evidence가 모두 충족하는지 확인한다."""
    requested = _questionPeriods(question)
    available = _evidencePeriods(cited)
    if requested and not requested.issubset(available):
        return False
    recentMatch = re.search(r"최근\s*(\d{1,2})\s*(?:개\s*)?(분기|년|연도)", question.casefold())
    if recentMatch is None:
        return True
    requiredCount = int(recentMatch.group(1))
    unit = recentMatch.group(2)
    relevant = {period for period in available if ("Q" in period) == (unit == "분기")}
    return len(relevant) >= requiredCount


def _coversDocumentaryClaims(question: str, prose: str, cited: list[dict[str, Any]]) -> bool:
    """감사의견과 핵심감사사항 질문은 cited 원문 필드와 답변 문구를 직접 대조한다."""
    normalizedQuestion = _compactSemantic(question)
    normalizedProse = _compactSemantic(prose)
    documentPayloads = [_payload(ref) for ref in cited if ref.get("kind") == "docRef"]

    def values(keys: tuple[str, ...]) -> list[str]:
        """문서 payload와 구조화 fields에서 지정 claim 값을 모은다."""
        found: list[str] = []
        for payload in documentPayloads:
            fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
            for key in keys:
                value = fields.get(key) or payload.get(key)
                if isinstance(value, str) and value.strip():
                    found.append(value)
        return found

    if "감사의견" in normalizedQuestion or "auditopinion" in normalizedQuestion:
        opinions = values(("adt_opinion", "auditOpinion", "opinion"))
        if not opinions:
            return False
        statedOpinion = _auditOpinionClass(prose)
        evidenceOpinions = {_auditOpinionClass(opinion) for opinion in opinions}
        evidenceOpinions.discard(None)
        if statedOpinion is None or statedOpinion not in evidenceOpinions:
            return False

    if "핵심감사" in normalizedQuestion or "keyauditmatter" in normalizedQuestion:
        matters = values(("core_adt_matter", "keyAuditMatter", "keyAuditMatters"))
        if not matters:
            return False
        if not any(_documentValueMatches(normalizedProse, matter) for matter in matters):
            return False
    return True


def _auditOpinionClass(value: str) -> str | None:
    normalized = _compactSemantic(value)
    if "부적정" in normalized or "adverse" in normalized:
        return "adverse"
    if "의견거절" in normalized or "disclaimer" in normalized:
        return "disclaimer"
    if "한정" in normalized or "qualified" in normalized:
        return "qualified"
    if "적정" in normalized or "unqualified" in normalized:
        return "unqualified"
    return None


def _documentValueMatches(normalizedProse: str, value: str) -> bool:
    candidates: list[str] = []
    for line in value.splitlines() or [value]:
        candidate = re.sub(r"^(?:\([^)]*\)|\d+[.)])", "", line.strip())
        normalized = _compactSemantic(candidate)
        if len(normalized) >= 2:
            candidates.append(normalized)
    return any(candidate in normalizedProse for candidate in candidates)


def _citedRefs(answer: str, canonicalRefs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """canonical ref ID가 독립된 토큰으로 쓰인 경우에만 citation으로 인정한다."""
    return [ref for ref in canonicalRefs if _citationPattern(str(ref["id"])).search(answer)]


def _withoutCitations(answer: str, cited: list[dict[str, Any]]) -> str:
    """값과 날짜가 ref ID 자체에만 들어 있어 binding을 가장하지 못하게 제거한다."""
    prose = answer
    for ref in sorted(cited, key=lambda item: len(str(item["id"])), reverse=True):
        prose = _citationPattern(str(ref["id"])).sub(" ", prose)
    return prose


def _citationPattern(refId: str) -> re.Pattern[str]:
    """콜론이나 영숫자를 덧붙인 forged ID를 거부하는 exact-token 패턴을 만든다."""
    return re.compile(rf"(?<![\w.:/@%+\-=]){re.escape(refId)}(?![\w.:/@%+\-=])")


def _evidenceIssues(cited: list[dict[str, Any]]) -> list[str]:
    """인용됐지만 실제 내용을 증명하지 못하는 ref의 실패 사유를 반환한다."""
    issues: list[str] = []
    for ref in cited:
        kind = str(ref.get("kind") or "")
        if kind not in {"tableRef", "docRef", "valueRef", "dateRef"}:
            continue
        payload = _payload(ref)
        if not payload:
            issues.append("evidence_payload_empty")
            continue
        if kind in {"tableRef", "valueRef", "dateRef"} and not _hasGroundedLineage(ref):
            issues.append("derived_evidence_lineage_missing")
            continue
        if kind == "tableRef" and not _hasTableContent(payload):
            issues.append("table_evidence_empty")
        elif kind == "valueRef" and not _isConcreteScalar(payload.get("value")):
            issues.append("value_evidence_unavailable")
        elif kind == "dateRef" and not _hasConcreteDate(payload):
            issues.append("date_evidence_unavailable")
    return issues


def _isUsableEvidence(ref: dict[str, Any]) -> bool:
    kind = str(ref.get("kind") or "")
    if kind not in {"tableRef", "docRef", "valueRef", "dateRef"}:
        return True
    payload = _payload(ref)
    if not payload:
        return False
    if kind in {"tableRef", "valueRef", "dateRef"} and not _hasGroundedLineage(ref):
        return False
    if kind == "tableRef":
        return _hasTableContent(payload)
    if kind == "valueRef":
        return _isConcreteScalar(payload.get("value"))
    if kind == "dateRef":
        return _hasConcreteDate(payload)
    return True


def _hasGroundedLineage(ref: dict[str, Any]) -> bool:
    """RunPython 실행에서 파생된 ref는 canonical upstream lineage가 있어야 한다."""
    source = str(ref.get("source") or "").casefold()
    refId = str(ref.get("id") or "").casefold()
    isExecutionDerived = source.startswith("execution:") or ":local:" in refId or source == "run_python"
    if not isExecutionDerived:
        return True
    provenance = _payload(ref).get("provenance")
    if not isinstance(provenance, list):
        return False
    return any(
        isinstance(item, str)
        and item.startswith(("table:", "doc:", "value:", "date:", "dataset:"))
        and ":local:" not in item
        for item in provenance
    )


def _hasTableContent(payload: dict[str, Any]) -> bool:
    """행 수 또는 bounded table data가 실제로 하나 이상 있어야 한다."""
    rowCount = payload.get("rowCount")
    if isinstance(rowCount, (int, float)) and not isinstance(rowCount, bool):
        if rowCount <= 0:
            return False
        return True
    return any(key in payload and _hasContent(payload.get(key)) for key in _TABLE_CONTENT_KEYS)


def _hasContent(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_hasContent(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_hasContent(item) for item in value)
    return _isConcreteScalar(value)


def _hasConcreteDate(payload: dict[str, Any]) -> bool:
    if payload.get("specified") is False:
        return False
    return any(
        _isConcreteScalar(payload.get(key))
        for key in ("period", "dataAsOf", "asOf", "knowledgeBoundary", "requestedAsOf", "value")
    )


def _coversQuestionTargets(
    question: str,
    canonicalRefs: list[dict[str, Any]],
    cited: list[dict[str, Any]],
    comparison: dict[str, Any],
) -> bool:
    """질문에 명시된 종목 코드와 ref 메타데이터의 대상을 대조한다."""
    requestedCodes = set(re.findall(r"(?<!\d)\d{6}(?!\d)", question))
    citedCodes = {code for ref in cited for code in _targetCodes(ref)}
    if requestedCodes and not requestedCodes.issubset(citedCodes):
        return False

    # 6자리 종목코드는 회사명보다 강한 식별자다. 코드가 정확히 결합된 질문에서
    # 긴 한국어 문장을 회사명으로 오인해 다시 실패시키지 않는다.
    requestedLabels: set[str] = set()
    if not requestedCodes:
        metadataLabels = {
            label
            for ref in canonicalRefs
            for label in _targetLabels(ref)
            if label and label in _compactSemantic(question)
        }
        # canonical evidence가 질문 속 회사명을 이미 식별했다면 그 값을 우선한다.
        # 그렇지 않을 때만 한국어 조사 기반 휴리스틱으로 보완한다.
        requestedLabels = metadataLabels or _questionTargetLabels(question)
    citedLabels = {label for ref in cited for label in _targetLabels(ref)}
    if requestedLabels and not all(
        any(requested == citedLabel or requested in citedLabel or citedLabel in requested for citedLabel in citedLabels)
        for requested in requestedLabels
    ):
        return False

    if not _requiresMultipleTargets(question, comparison) and len(citedCodes) > 1:
        return False
    return True


def _requiresMultipleTargets(question: str, comparison: dict[str, Any]) -> bool:
    if int(comparison.get("minTargets") or 0) < 2:
        return False
    normalized = question.casefold()
    timeComparison = any(
        hint in normalized
        for hint in ("전년", "전분기", "전월", "기간", "연도별", "분기별", "year over year", "quarter over quarter")
    )
    return not timeComparison


def _targetCount(cited: list[dict[str, Any]]) -> int:
    targets: set[str] = set()
    targetKeys = {"stockCode", "target", "code", "ticker", "corpCode"}

    def collect(value: Any) -> None:
        """중첩 payload를 순회해 비교 대상 식별자를 누적한다."""
        if isinstance(value, dict):
            for key, item in value.items():
                if key in targetKeys and isinstance(item, (str, int)) and str(item).strip():
                    targets.add(str(item).strip())
                elif isinstance(item, (dict, list, tuple)):
                    collect(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                collect(item)

    for ref in cited:
        collect(_payload(ref))
        targets.update(_targetCodes(ref))
    return len(targets)
