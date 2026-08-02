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
    "계약 내용",
    "공시 내용",
    "소송",
    "위험 요인",
    "주석 내용",
    "지배구조",
)


@dataclass(frozen=True)
class AnswerQualityReport:
    """공개 가능 여부와 실패 원인을 담는 content-free 품질 결과."""

    passed: bool
    contract: EvidenceContract
    score: int
    issues: tuple[str, ...]
    citedRefIds: tuple[str, ...]

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
) -> AnswerQualityReport:
    """종료 상태, exact citation, 값과 시점 binding을 모두 검사한다."""
    contract = classifyEvidenceContract(question)
    issues: list[str] = []
    cleanAnswer = answer.strip()
    canonicalRefs = [ref for ref in refs if isinstance(ref, dict) and ref.get("id") and ref.get("kind")]
    cited = [ref for ref in canonicalRefs if str(ref["id"]) in cleanAnswer]
    citedKinds = {str(ref["kind"]) for ref in cited}
    prose = cleanAnswer
    for ref in cited:
        prose = prose.replace(str(ref["id"]), " ")

    if failed or not completionSucceeded:
        issues.append("runtime_not_completed")
    if not cleanAnswer:
        issues.append("empty_answer")
    if not ({"tableRef", "docRef"} & citedKinds):
        issues.append("source_ref_missing")
    if "dateRef" not in citedKinds:
        issues.append("date_ref_missing")
    if contract == "quantitative" and "valueRef" not in citedKinds:
        issues.append("value_ref_missing")
    if contract == "quantitative" and "valueRef" in citedKinds and not _hasBoundValue(prose, cited):
        issues.append("value_binding_mismatch")
    if "dateRef" in citedKinds and not _hasBoundDate(prose, cited):
        issues.append("date_binding_mismatch")

    uniqueIssues = tuple(dict.fromkeys(issues))
    score = max(0, 100 - 20 * len(uniqueIssues))
    return AnswerQualityReport(
        passed=not uniqueIssues,
        contract=contract,
        score=score,
        issues=uniqueIssues,
        citedRefIds=tuple(str(ref["id"]) for ref in cited),
    )


def _hasBoundValue(prose: str, cited: list[dict[str, Any]]) -> bool:
    """payload가 제공된 cited value 중 하나의 정확한 값이 본문에 있는지 확인한다."""
    values = [_payload(ref).get("value") for ref in cited if ref.get("kind") == "valueRef"]
    concrete = [value for value in values if isinstance(value, (str, int, float)) and not isinstance(value, bool)]
    if not concrete:
        return True
    compact = _compactNumberText(prose)
    return any(candidate and candidate in compact for value in concrete for candidate in _valueCandidates(value))


def _hasBoundDate(prose: str, cited: list[dict[str, Any]]) -> bool:
    """payload가 제공된 cited date의 기간 또는 기준일이 본문에 있는지 확인한다."""
    candidates: set[str] = set()
    hasConcrete = False
    for ref in cited:
        if ref.get("kind") != "dateRef":
            continue
        payload = _payload(ref)
        for key in ("period", "dataAsOf"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                hasConcrete = True
                candidates.update(_dateCandidates(value))
    if not hasConcrete:
        return True
    normalized = _compactText(prose)
    return any(candidate in normalized for candidate in candidates)


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


def _dateCandidates(value: str) -> set[str]:
    compact = _compactText(value)
    candidates = {compact}
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
    return {candidate for candidate in candidates if candidate}


def _compactText(value: str) -> str:
    return re.sub(r"\s+", "", value.casefold())


def _compactNumberText(value: str) -> str:
    return re.sub(r"[\s,_]", "", value.casefold())
