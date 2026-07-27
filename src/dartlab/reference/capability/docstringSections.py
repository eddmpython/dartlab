"""엔진 docstring 을 카탈로그가 읽을 수 있는 조각으로 파싱한다.

여기 있는 것은 "글에서 무엇을 뽑아내나" 하나만 다룬다. 카탈로그를 조립하는 쪽(`builder`)은
어떤 대상을 훑을지와 뽑아낸 조각을 어떻게 엮을지를 정하고, 글의 문법은 전부 이 모듈이 안다.

docstring 문법은 Google 과 NumPy 양식이 섞여 들어오고 섹션도 계속 는다. 한 파일에 두면
카탈로그 조립 쪽 변경이 파싱 규칙을 건드리게 된다.
"""

from __future__ import annotations

import json
import re
from typing import Any


def _parseDocstringSections(doc: str | None) -> dict[str, str]:
    """Google-style docstring에서 Capabilities/Requires/AIContext/Args/Returns 섹션 추출."""
    if not doc:
        return {}

    result: dict[str, str] = {}
    knownSections = {
        "capabilities",
        "requires",
        "aicontext",
        "aicontract",
        "guide",
        "seealso",
        "args",
        "returns",
        "example",
        "llmspecifications",
    }
    currentKey: str | None = None
    currentLines: list[str] = []

    for line in doc.split("\n"):
        stripped = line.strip()
        # NumPy style 구분선 ("-------") - 이전 섹션 헤더의 일부이므로 skip
        if stripped and all(c == "-" for c in stripped):
            continue
        # "SectionName:" (Google) 또는 "SectionName" 단독 줄 (NumPy) 매칭
        # 공백 포함 헤더 ("LLM Specifications:") 도 인식하기 위해 공백 제거 변형도 비교
        candidate_raw = stripped.rstrip(":").lower()
        candidate = candidate_raw.replace(" ", "")
        if candidate in knownSections and (stripped.endswith(":") or candidate_raw == stripped.lower()):
            # 이전 섹션 저장
            if currentKey is not None:
                result[currentKey] = "\n".join(currentLines).strip()
            currentKey = candidate
            currentLines = []
            continue

        if currentKey is not None:
            # 들여쓰기 블록 안의 줄 수집 (leading whitespace 제거)
            if stripped.startswith("- "):
                currentLines.append(stripped[2:].strip())
            elif stripped:
                currentLines.append(stripped)
            elif currentLines:
                # 빈 줄 - 블록 종료가 아님 (다음 섹션이 나올 때까지)
                currentLines.append("")

    # 마지막 섹션 저장
    if currentKey is not None:
        result[currentKey] = "\n".join(currentLines).strip()

    return result


_LLM_SPEC_SUBKEYS = {
    "antipatterns": "antiPatterns",
    "outputschema": "outputSchema",
    "prerequisites": "prerequisites",
    "freshness": "freshness",
    "dataflow": "dataflow",
    "targetmarkets": "targetMarkets",
}


def _parseLLMSpecs(value: str | None) -> dict[str, Any]:
    """LLM Specifications 섹션 본문에서 6 sub-key (AntiPatterns/OutputSchema/Prerequisites/Freshness/Dataflow/TargetMarkets) 추출.

    형식 (들여쓰기 기반):
        AntiPatterns:
            - 분기 데이터인데 monthly average 비교
            - 한국 회사에 미국 GAAP 가정
        OutputSchema:
            - 자산총계 : float - BS 자산 총계 (원)
            - 자본총계 : float - BS 자본 총계 (원)
        Freshness:
            분기마감 후 45일 (DART 공시 마감)
        ...

    각 sub-key 는 list (bullet 일 때) 또는 string (free text 일 때).
    파싱 실패 시 raw text 보존 (key='_raw').
    """
    if not value or not value.strip():
        return {}
    out: dict[str, Any] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    # freshness 만 string. 나머지 5 sub-key 는 항상 list (multi-line 자동 인식).
    string_keys = {"freshness"}

    def _flush() -> None:
        if current_key is None:
            return
        camel = _LLM_SPEC_SUBKEYS.get(current_key, current_key)
        non_empty = [line for line in current_lines if line.strip()]
        if not non_empty:
            return
        if current_key in string_keys:
            out[camel] = " ".join(non_empty).strip()
            return
        # bullet 마커가 있으면 제거. _parseDocstringSections 가 이미 "- " 를 제거했을 수도.
        items = [line.strip().lstrip("-").lstrip("*").strip() for line in non_empty]
        items = [item for item in items if item]
        if items:
            out[camel] = items if len(items) > 1 else items[0]

    for line in value.splitlines():
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue
        candidate = stripped.rstrip(":").lower().replace(" ", "")
        if stripped.endswith(":") and candidate in _LLM_SPEC_SUBKEYS:
            _flush()
            current_key = candidate
            current_lines = []
            continue
        if current_key is not None:
            current_lines.append(stripped)
    _flush()

    return out or {"_raw": value.strip()}


def _parseAiContract(value: str | None) -> dict[str, Any]:
    """Parse an AI Contract docstring block into generated metadata."""
    if not value:
        return {}
    text = value.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    out: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not key:
            continue
        if raw.startswith("[") or raw.startswith("{"):
            try:
                out[key] = json.loads(raw)
                continue
            except json.JSONDecodeError:
                pass
        if "," in raw:
            out[key] = [part.strip() for part in raw.split(",") if part.strip()]
        else:
            out[key] = raw
    return out


_RETURN_FIELD_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>[^:\n]{1,120})\s*:\s*(?P<type>[^\u2014\u2013\-\n]+)"
    r"(?:[\u2014\u2013-]\s*(?P<desc>.*))?$"
)
_RETURN_UNIT_RE = re.compile(r"\((?P<unit>%|원|백만원|천원|달러|USD|KRW|일|배|점|건|주|명|개|회|년|월|분기|bps|pp)\)")


def _parseReturnsSchema(value: str | None) -> list[dict[str, Any]]:
    """Parse Returns text into a machine-readable field schema.

    The docstring remains the SSOT. This parser only compiles the existing
    `key : type - description (unit)` convention into generated metadata.
    """
    if not value:
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in value.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or ":" not in line:
            continue
        match = _RETURN_FIELD_RE.match(line)
        if not match:
            continue
        name = match.group("name").strip()
        type_name = match.group("type").strip()
        if not name or not type_name:
            continue
        description = (match.group("desc") or "").strip()
        unit_match = _RETURN_UNIT_RE.search(description)
        rows.append(
            {
                "name": name,
                "type": type_name,
                "description": description,
                "unit": unit_match.group("unit") if unit_match else None,
                "depth": len(match.group("indent").replace("\t", "    ")) // 4,
            }
        )
    return rows


def _applyAiContract(entry: dict[str, Any], sections: dict[str, str]) -> None:
    contract = _parseAiContract(sections.get("aicontract"))
    if not contract:
        return
    for key in (
        "contractId",
        "whenToUse",
        "questionTypes",
        "requiredInputs",
        "requiredEvidence",
        "evidenceSchema",
        "outputShape",
        "dataColumns",
        "freshness",
        "comparisonCompleteness",
        "commonCalculations",
        "verification",
        "visualPolicy",
        "artifactPolicy",
        "toolArgPolicy",
        "toolBudget",
        "preflightActions",
        "acceptanceCriteria",
        "failurePolicy",
        "failureModes",
        "badUses",
        "priority",
    ):
        if key in contract:
            entry[key] = contract[key]
