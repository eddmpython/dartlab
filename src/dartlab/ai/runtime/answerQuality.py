"""설치형 런타임 답변을 공개하기 전 적용하는 결정론 품질 게이트."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

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

_UNAVAILABLE_MARKERS = frozenset(
    {"", "-", "n/a", "na", "nan", "none", "null", "unknown", "unavailable", "미상", "미지정", "없음"}
)
_TABLE_CONTENT_KEYS = ("rows", "records", "timeseries", "matrix", "table", "data", "items", "values", "axes")
_TARGET_KEYS = frozenset({"stockCode", "target", "code", "ticker", "corpCode", "companyName", "corpName", "targetName"})
_TARGET_LABEL_NOISE = frozenset(
    "값 결과 기업 대상 분기 사업보고서 실적 연도 재무제표 종목 질문 회사 answer company date document python result table".split()
)
_METRIC_SPECS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "operating_cash_flow",
        ("영업활동현금흐름", "영업현금흐름", "operating cash flow"),
        ("영업활동현금흐름", "영업현금흐름", "operating cash flow", "operatingcashflow"),
    ),
    (
        "free_cash_flow",
        ("잉여현금흐름", "free cash flow", "fcf"),
        ("잉여현금흐름", "free cash flow", "freecashflow", "fcf"),
    ),
    (
        "operating_margin",
        ("영업이익률", "영업마진", "operating margin"),
        ("영업이익률", "영업마진", "operating margin", "operatingmargin", "opm"),
    ),
    (
        "revenue_growth",
        ("매출성장률", "매출 성장률", "revenue growth", "sales growth"),
        ("매출성장률", "매출 성장률", "revenue growth", "sales growth", "salesgrowth", "revenuegrowth"),
    ),
    (
        "operating_profit",
        ("영업이익", "영업손익", "operating profit", "operating income"),
        ("영업이익", "영업손익", "operating profit", "operating income", "operatingprofit"),
    ),
    (
        "net_income",
        ("당기순이익", "순이익", "net income", "net profit"),
        ("당기순이익", "순이익", "net income", "net profit", "netincome", "netprofit"),
    ),
    (
        "revenue",
        ("매출액", "매출", "revenue", "sales"),
        ("매출액", "매출", "revenue", "sales"),
    ),
    (
        "total_assets",
        ("자산총계", "총자산", "total assets"),
        ("자산총계", "총자산", "total assets", "totalassets"),
    ),
    (
        "total_liabilities",
        ("부채총계", "총부채", "total liabilities"),
        ("부채총계", "총부채", "total liabilities", "totalliabilities"),
    ),
    (
        "total_equity",
        ("자본총계", "총자본", "total equity"),
        ("자본총계", "총자본", "total equity", "totalequity"),
    ),
    ("roe", ("roe", "자기자본이익률"), ("roe", "자기자본이익률")),
    ("eps", ("eps", "주당순이익"), ("eps", "주당순이익")),
    ("per", ("per", "주가수익비율"), ("per", "주가수익비율")),
    ("pbr", ("pbr", "주가순자산비율"), ("pbr", "주가순자산비율")),
)


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
    )


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
    return issues


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
        formatted = payload.get("formatted")
        if isinstance(formatted, str) and _compactText(formatted) in normalized:
            return True
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            expected = float(value)
            return any(abs(amount - expected) <= tolerance for amount, tolerance in amounts)
        return False

    return all(binds(payload) for payload in payloads)


def _hasBoundDate(prose: str, cited: list[dict[str, Any]], *, question: str = "") -> bool:
    """payload가 제공된 cited date 각각의 기간 또는 기준일이 본문에 있는지 확인한다."""
    candidateGroups: list[set[str]] = []
    requestedPeriods = _questionPeriods(question)
    for ref in cited:
        if ref.get("kind") != "dateRef":
            continue
        payload = _payload(ref)
        candidates: set[str] = set()
        for key in ("period", "dataAsOf", "value"):
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
    if kind == "tableRef":
        return _hasTableContent(payload)
    if kind == "valueRef":
        return _isConcreteScalar(payload.get("value"))
    if kind == "dateRef":
        return _hasConcreteDate(payload)
    return True


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
    return any(_isConcreteScalar(payload.get(key)) for key in ("period", "dataAsOf", "value"))


def _isConcreteScalar(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return value == value
    if not isinstance(value, str):
        return False
    return value.strip().casefold() not in _UNAVAILABLE_MARKERS


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

    metadataLabels = {
        label for ref in canonicalRefs for label in _targetLabels(ref) if label and label in _compactSemantic(question)
    }
    explicitLabels = _questionTargetLabels(question)
    requestedLabels = metadataLabels | explicitLabels
    citedLabels = {label for ref in cited for label in _targetLabels(ref)}
    if requestedLabels and not all(
        any(requested == citedLabel or requested in citedLabel or citedLabel in requested for citedLabel in citedLabels)
        for requested in requestedLabels
    ):
        return False

    if not _requiresMultipleTargets(question, comparison) and len(citedCodes) > 1:
        return False
    return True


def _targetCodes(ref: dict[str, Any]) -> set[str]:
    codes = set(re.findall(r"(?<!\d)\d{6}(?!\d)", " ".join(_refSemanticParts(ref))))
    return codes


def _targetLabels(ref: dict[str, Any]) -> set[str]:
    payload = _payload(ref)
    labels: set[str] = set()
    for key in _TARGET_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and not re.fullmatch(r"\d{6}", value.strip()):
            compact = _compactSemantic(value)
            if len(compact) >= 2:
                labels.add(compact)
    title = str(ref.get("title") or "").strip()
    titleHead = re.match(r"([A-Za-z가-힣][A-Za-z0-9가-힣&.]{1,40})(?=\s|\()", title)
    if titleHead:
        candidate = _compactSemantic(titleHead.group(1))
        if _isPlausibleTargetLabel(candidate):
            labels.add(candidate)
    return labels


def _questionTargetLabels(question: str) -> set[str]:
    """한국어 조사 앞의 명시적 회사명 후보를 추출하되 일반 재무 단어는 제외한다."""
    labels: set[str] = set()
    pattern = r"(?<![A-Za-z0-9가-힣])([A-Za-z가-힣][A-Za-z0-9가-힣&.]{1,40}?)(?:의|와|과|은|는|에서)"
    for match in re.finditer(pattern, question):
        candidate = _compactSemantic(match.group(1))
        if _isPlausibleTargetLabel(candidate):
            labels.add(candidate)
    return labels


def _isPlausibleTargetLabel(value: str) -> bool:
    if len(value) < 2 or value in _TARGET_LABEL_NOISE:
        return False
    metricAliases = tuple(
        alias for _name, questionAliases, _evidenceAliases in _METRIC_SPECS for alias in questionAliases
    )
    return not _matchesAnyAlias(value, metricAliases)


def _coversQuestionMetrics(question: str, cited: list[dict[str, Any]]) -> bool:
    """질문에 명시된 각 핵심 지표가 usable valueRef 하나 이상과 맞는지 확인한다."""
    requested = _requestedMetrics(question)
    if not requested:
        return True
    valueRefs = [ref for ref in cited if ref.get("kind") == "valueRef"]
    for _name, aliases in requested:
        if not any(_matchesAnyAlias(" ".join(_refSemanticParts(ref)), aliases) for ref in valueRefs):
            return False
    return True


def _requestedMetrics(question: str) -> list[tuple[str, tuple[str, ...]]]:
    requested: list[tuple[str, tuple[str, ...]]] = []
    matchedSpecific: set[str] = set()
    for name, questionAliases, evidenceAliases in _METRIC_SPECS:
        if not _matchesAnyAlias(question, questionAliases):
            continue
        if name == "revenue" and "revenue_growth" in matchedSpecific:
            continue
        if name == "operating_profit" and "operating_margin" in matchedSpecific:
            continue
        requested.append((name, evidenceAliases))
        matchedSpecific.add(name)
    return requested


def _matchesAnyAlias(value: str, aliases: tuple[str, ...]) -> bool:
    folded = value.casefold()
    compact = _compactSemantic(value)
    for alias in aliases:
        normalized = _compactSemantic(alias)
        if not normalized:
            continue
        if normalized.isascii() and len(normalized) <= 3:
            if re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", folded):
                return True
        elif normalized in compact:
            return True
    return False


def _refSemanticParts(ref: dict[str, Any]) -> list[str]:
    parts = [str(ref.get(key) or "") for key in ("id", "title", "source")]
    payload = _payload(ref)
    for key in ("metric", "key", "snakeId", "item", "label", "name"):
        value = payload.get(key)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            parts.append(str(value))
    for key in _TARGET_KEYS:
        value = payload.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            parts.append(str(value))
    return parts


def _compactSemantic(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", value.casefold())


def _questionPeriods(question: str) -> set[str]:
    periods: set[str] = set()
    for match in re.finditer(r"(?<!\d)(20\d{2})(?:\s*년)?(?:\s*(?:Q([1-4])|([1-4])\s*분기))?", question):
        year = match.group(1)
        quarter = match.group(2) or match.group(3)
        periods.add(f"{year}Q{quarter}" if quarter else year)
    return periods


def _evidencePeriods(cited: list[dict[str, Any]]) -> set[str]:
    periods: set[str] = set()
    for ref in cited:
        payload = _payload(ref)
        values: list[Any] = []
        for key in ("period", "periods", "basePeriod", "year"):
            value = payload.get(key)
            values.extend(value if isinstance(value, list) else [value])
        for value in values:
            if isinstance(value, int) and 1900 <= value <= 2200:
                periods.add(str(value))
            elif isinstance(value, str):
                parsed = _questionPeriods(value)
                periods.update(parsed)
                periods.update(period[:4] for period in parsed if re.fullmatch(r"20\d{2}Q[1-4]", period))
    return periods


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


def _payload(ref: dict[str, Any]) -> dict[str, Any]:
    value = ref.get("payload")
    return value if isinstance(value, dict) else {}


def _valueCandidates(value: str | int | float) -> set[str]:
    text = str(value).strip()
    candidates = {_compactNumberText(text)}
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return {candidate for candidate in candidates if candidate}
    if number.is_integer():
        integer = int(number)
        candidates.add(str(integer))
        candidates.add(f"{integer:,}".replace(",", ""))
    else:
        candidates.add(format(number, ".15g").replace(",", ""))
    return {candidate for candidate in candidates if candidate}


def _financialAmounts(prose: str) -> list[tuple[float, float]]:
    """한국 공시 답변의 원·만·억·조 표기를 값과 표시 반올림 허용폭으로 바꾼다."""
    scales = {"만": 10_000.0, "억": 100_000_000.0, "조": 1_000_000_000_000.0}
    amounts: list[tuple[float, float]] = []

    def parse(numberText: str, scale: float) -> tuple[float, float]:
        """표시 숫자를 원 단위 값과 자릿수 기반 허용 오차로 변환한다."""
        number = float(numberText.replace(",", ""))
        decimals = len(numberText.rsplit(".", 1)[1]) if "." in numberText else 0
        tolerance = scale * 0.5 * (10**-decimals)
        return number * scale, max(tolerance, 1e-9)

    termPattern = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*(조|억|만)\s*원?")
    for match in termPattern.finditer(prose):
        amounts.append(parse(match.group(1), scales[match.group(2)]))

    compoundPattern = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*조\s*(\d[\d,]*(?:\.\d+)?)\s*억\s*원?")
    for match in compoundPattern.finditer(prose):
        major, _majorTolerance = parse(match.group(1), scales["조"])
        minor, minorTolerance = parse(match.group(2), scales["억"])
        amounts.append((major + minor, minorTolerance))

    wonPattern = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*원")
    for match in wonPattern.finditer(prose):
        amounts.append(parse(match.group(1), 1.0))
    return amounts


def _dateCandidates(value: str) -> set[str]:
    compact = _compactText(value)
    candidates = {compact}
    fiscalYear = re.fullmatch(r"(\d{4})(?:fy|y)", compact)
    if fiscalYear:
        year = fiscalYear.group(1)
        candidates.update({_compactText(year), _compactText(f"{year}년"), _compactText(f"{year} 연간")})
    quarter = re.fullmatch(r"(\d{4})q([1-4])", compact)
    if quarter:
        year, number = quarter.groups()
        candidates.update({_compactText(f"{year}년 {number}분기"), _compactText(f"{year} {number}분기")})
    date = re.fullmatch(r"(\d{4})[-./]?(\d{1,2})[-./]?(\d{1,2})", value.strip())
    if date:
        year, month, day = date.groups()
        candidates.update(
            {
                _compactText(f"{year}-{int(month):02d}-{int(day):02d}"),
                _compactText(f"{year}.{int(month):02d}.{int(day):02d}"),
                _compactText(f"{year}년 {int(month)}월 {int(day)}일"),
            }
        )
    isoPrefix = re.match(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
    if isoPrefix:
        year, month, day = isoPrefix.groups()
        candidates.update(
            {
                _compactText(f"{year}-{month}-{day}"),
                _compactText(f"{year}년 {int(month)}월 {int(day)}일"),
            }
        )
    return {candidate for candidate in candidates if candidate}


def _compactText(value: str) -> str:
    return re.sub(r"\s+", "", value.casefold())


def _compactNumberText(value: str) -> str:
    return re.sub(r"[\s,_]", "", value.casefold())
