"""capability 카탈로그 라이브 빌더 — 엔진 docstring/registry introspect → 런타임 dict.

``loadCapabilities()`` 가 스킬엔진(EngineCall · ReadCapability · 검색) 첫 조회 시 docstring 소스에서
1 회 빌드(프로세스 캐시)한다. **사본(생성 파일) 없음** — docstring 이 유일 진실
(operation.code §"CAPABILITIES 단일 진실의 원천"), drift 표면 0. cold ~0.5s · warm ~18ms.

산출 (라이브, 캐시):
- ``loadCapabilities() -> CAPABILITIES`` (EngineCall · ReadCapability · ReadSkill · search · server 소비)
- ``loadAnalysisGraph() -> ANALYSIS_GRAPH`` (analysisGraph 소비)
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import re
from functools import lru_cache
from typing import Any

# ─── 유틸 ───────────────────────────────────────────────────────


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
        # NumPy style 구분선 ("-------") — 이전 섹션 헤더의 일부이므로 skip
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
                # 빈 줄 — 블록 종료가 아님 (다음 섹션이 나올 때까지)
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
            - 자산총계 : float — BS 자산 총계 (원)
            - 자본총계 : float — BS 자본 총계 (원)
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
    r"^(?P<indent>\s*)(?P<name>[^:\n]{1,120})\s*:\s*(?P<type>[^—\-\n]+)(?:[—-]\s*(?P<desc>.*))?$"
)
_RETURN_UNIT_RE = re.compile(r"\((?P<unit>%|원|백만원|천원|달러|USD|KRW|일|배|점|건|주|명|개|회|년|월|분기|bps|pp)\)")


def _parseReturnsSchema(value: str | None) -> list[dict[str, Any]]:
    """Parse Returns text into a machine-readable field schema.

    The docstring remains the SSOT. This parser only compiles the existing
    `key : type — description (unit)` convention into generated metadata.
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


# ─── Surface 1: Python API (__init__.py __all__) ────────────────


# ─── Surface 2: CLI (COMMAND_SPECS) ────────────────────────────


# ─── Surface 3: Server API (AST 기반 라우터 파싱) ──────────────


# ─── Surface 4: Data Modules (registry) ────────────────────────


# ─── Surface 5: AI Tools (super tools AST 파싱) ────────────────


# ─── 런타임 capability 카탈로그 생성 ──────────────────────────


# axis-engine 라이브 축 레지스트리 — 모듈 이동 추종 (AST-소스 의존 0, install-robust).
# gather 표준(engine(axis, target)) 전 엔진을 {engine}.{axis} 로 카탈로그 등록.
_AXIS_REGISTRIES: tuple[tuple[str, str, str], ...] = (
    ("scan", "dartlab.scan.router", "_AXIS_REGISTRY"),
    ("macro", "dartlab.macro", "_AXIS_REGISTRY"),
    ("gather", "dartlab.gather.entry.dispatch", "AXIS_REGISTRY"),
    ("industry", "dartlab.industry", "_AXIS_REGISTRY"),
    ("credit", "dartlab.credit", "_AXIS_REGISTRY"),
    ("quant", "dartlab.quant", "_AXIS_REGISTRY"),
)


# 축 엔트리에서 카탈로그로 실을 필요가 없는 필드. **항목마다 사유 필수** (게으른 덤프 방지).
_AXIS_IGNORE_FIELDS: frozenset[str] = frozenset(
    {
        "label",  # summary 로 이미 투영
        "description",  # capabilities 로 이미 투영
        "example",  # 사람용 예시. 기계 판정에 무관
        "module",  # 구현 위치 (선언이 아님)
        "fn",  # 구현 위치 (선언이 아님)
        "listModule",  # 구현 위치 (선언이 아님)
        "axis",  # credit 전용. "{prefix}.{axis}" 키와 중복
    }
)


def _declaredAxisFields(entry: Any) -> dict[str, Any]:
    """축 엔트리가 **이미 선언한** 필드를 네이티브 이름 그대로 캐리 → declared dict.

    6 엔진의 축 엔트리 dataclass 는 필드 이름이 서로 다르다 (scan ``returnType``·``listFn``,
    quant ``stockRequired``·``multiStock``, gather/industry ``targetType``·``hidden``, macro ``act``,
    credit ``group``). **alias 표로 접지 않는다.** 접으면 그 표가 두 번째 SSOT 가 되어 drift 하고
    의미가 손실된다 (예 stockRequired 를 targetRequired 로 흡수). 대신 ignore 아닌 필드를 전부 원명
    으로 흘려보내므로, 새 엔진이 새 필드명을 써도 조용히 버려지지 않는다.

    lane·universeScope 같은 **파생 의미축은 저장하지 않는다.** 소비측이 순수함수로 계산한다
    (lane = f(returnType, listFn), universeScope = f(stockRequired, targetRequired, multiStock)).

    Args:
        entry: 축 엔트리 객체. dataclass 가 아니면 빈 dict (미래 비-dataclass 레지스트리 크래시 가드).

    Returns:
        {필드명: 값}. ``None`` 은 미선언이라 제외하되 ``False`` 는 유효 선언이라 보존한다
        (targetRequired=False = 타깃 불요 = 전종목 벌크 안전). primitive 만 캐리 (JSON 소비처 보호).
    """
    if not dataclasses.is_dataclass(entry):
        return {}
    declared: dict[str, Any] = {}
    for field in dataclasses.fields(entry):
        if field.name in _AXIS_IGNORE_FIELDS:
            continue
        value = getattr(entry, field.name, None)
        if value is None:  # 미선언. 0/False 로 대체 금지
            continue
        if isinstance(value, (str, bool, int, float)):
            declared[field.name] = value
    return declared


def _injectAxisRegistriesLive(entries: dict[str, dict[str, Any]]) -> None:
    """scan/macro/gather 축 레지스트리를 라이브 객체에서 직접 주입.

    레지스트리 dict 의 각 entry(``label``/``description`` 속성) → ``{prefix}.{axis}`` key.
    소스파일 AST 파싱 0. 레지스트리가 모듈 이동해도, 설치 패키지에서도 동작 (옛 AST 방식은
    ``_AXIS_REGISTRY`` 가 ``scan/__init__``→``scan/router`` 로 옮겨가며 scan 축을 누락했다).

    label/description 외의 **선언 필드도 ``declared`` 로 실는다** (2026-07-07). 이전에는 버려서
    소비측이 축의 반환형·타깃 필요 여부·카탈로그 원자 여부를 알 수 없었다. 키(``{prefix}.{axis}``)는
    불변이므로 additive 이며 소비처(engineCall·capabilities·search)는 하위호환이다.
    """
    import importlib as _il

    for prefix, modPath, attr in _AXIS_REGISTRIES:
        try:
            registry = getattr(_il.import_module(modPath), attr, None)
        except ImportError:
            continue
        if not isinstance(registry, dict):
            continue
        for axisName, entry in registry.items():
            axisEntry: dict[str, Any] = {"kind": f"{prefix}_axis"}
            if label := getattr(entry, "label", None):
                axisEntry["summary"] = str(label)
            if description := getattr(entry, "description", None):
                axisEntry["capabilities"] = str(description)
            if declared := _declaredAxisFields(entry):
                axisEntry["declared"] = declared
            entries[f"{prefix}.{axisName}"] = axisEntry


def _applyAiContractMetadata(entries: dict[str, dict[str, Any]]) -> None:
    """Attach generated contract metadata from core capabilities SSOT."""
    from dartlab.reference.capability.registry import getAnalysisContractSpecs

    for key, contract in getAnalysisContractSpecs().items():
        entries.setdefault(key, {})
        for field, value in contract.items():
            entries[key].setdefault(field, value)


def _buildAnalysisGraph(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """CAPABILITIES entries를 Analysis Graph JSON payload로 컴파일."""
    import hashlib

    contracts: dict[str, dict[str, Any]] = {}
    routes: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    processMaps: dict[str, dict[str, Any]] = {}

    for key, entry in sorted(entries.items()):
        contractId = entry.get("contractId")
        if not contractId:
            continue
        contract = {k: v for k, v in entry.items() if k not in {"args", "example", "guide", "returns", "seeAlso"}}
        contract["sourceKey"] = key
        contracts[str(contractId)] = contract
        nodes.append(
            {
                "id": f"contract:{contractId}",
                "kind": "contract",
                "label": entry.get("summary") or contractId,
                "source": key,
            }
        )
        if tool := entry.get("tool"):
            nodes.append({"id": f"tool:{tool}", "kind": "tool", "label": tool, "source": key})
            edges.append({"from": f"contract:{contractId}", "to": f"tool:{tool}", "kind": "usesTool"})
        for question_type in entry.get("questionTypes") or []:
            route_id = f"route:{question_type}"
            if not any(route["id"] == route_id for route in routes):
                routes.append(
                    {
                        "id": route_id,
                        "questionType": question_type,
                        "triggers": entry.get("questionTriggers") or {},
                        "contractIds": [],
                        "toolNames": [],
                        "processMapIds": [],
                    }
                )
            route = next(route for route in routes if route["id"] == route_id)
            route["triggers"] = _mergeQuestionTriggers(route.get("triggers") or {}, entry.get("questionTriggers") or {})
            route["contractIds"].append(str(contractId))
            for tool_name in entry.get("toolNames") or ([entry.get("tool")] if entry.get("tool") else []):
                if tool_name and tool_name not in route["toolNames"]:
                    route["toolNames"].append(str(tool_name))
            edges.append({"from": route_id, "to": f"contract:{contractId}", "kind": "requiresContract"})

    processMaps = _buildProcessMaps(contracts, routes)
    for process_id, process in processMaps.items():
        nodes.append(
            {
                "id": f"process:{process_id}",
                "kind": "process",
                "label": process.get("summary") or process_id,
                "source": process.get("questionType"),
            }
        )
        route_id = f"route:{process.get('questionType')}"
        edges.append({"from": route_id, "to": f"process:{process_id}", "kind": "usesProcess"})
        for contractId in process.get("contractIds") or []:
            edges.append({"from": f"process:{process_id}", "to": f"contract:{contractId}", "kind": "requiresContract"})
        for step in process.get("steps") or []:
            tool = step.get("tool")
            if tool:
                edges.append({"from": f"process:{process_id}", "to": f"tool:{tool}", "kind": "usesTool"})
            if step.get("produces") == "evidence":
                evidence_id = f"evidence:{process_id}:{step.get('id')}"
                nodes.append({"id": evidence_id, "kind": "evidence", "label": step.get("purpose") or "evidence"})
                edges.append({"from": f"process:{process_id}", "to": evidence_id, "kind": "producesEvidence"})
        if process.get("artifactPolicy", {}).get("primaryCsv"):
            artifact_id = f"artifact:{process_id}:primary_csv"
            nodes.append({"id": artifact_id, "kind": "artifact", "label": "primary CSV"})
            edges.append({"from": f"process:{process_id}", "to": artifact_id, "kind": "producesArtifact"})
        if process.get("visualPolicy", {}).get("requiredFor"):
            visual_id = f"visual:{process_id}:primary"
            nodes.append(
                {"id": visual_id, "kind": "visual", "label": process.get("visualPolicy", {}).get("preferredType")}
            )
            edges.append({"from": f"process:{process_id}", "to": visual_id, "kind": "requiresVisual"})
        edges.append({"from": f"process:{process_id}", "to": "workspace:analysis", "kind": "feedsWorkspace"})

    for route in routes:
        question_type = route.get("questionType")
        process_id = f"{question_type}.default"
        if process_id in processMaps and process_id not in route["processMapIds"]:
            route["processMapIds"].append(process_id)

    payload = {
        "graphVersion": 2,
        "sourceHash": hashlib.sha256(
            json.dumps({"contracts": contracts, "processMaps": processMaps}, ensure_ascii=False, sort_keys=True).encode(
                "utf-8"
            )
        ).hexdigest()[:16],
        "nodes": nodes,
        "edges": edges,
        "contracts": contracts,
        "routes": routes,
        "processMaps": processMaps,
    }
    return payload


def _buildProcessMaps(contracts: dict[str, dict[str, Any]], routes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build generated process maps from route contracts.

    This is not a new SSOT. It derives an LLM-facing execution map from contract
    metadata already compiled into the Analysis Graph.
    """
    out: dict[str, dict[str, Any]] = {}
    for route in routes:
        question_type = str(route.get("questionType") or "")
        if not question_type:
            continue
        route_contracts = [contracts[cid] for cid in route.get("contractIds") or [] if cid in contracts]
        if not route_contracts:
            continue
        steps: list[dict[str, Any]] = []
        for contract in route_contracts:
            contractId = str(contract.get("contractId") or "")
            for idx, action in enumerate(contract.get("preflightActions") or []):
                if not isinstance(action, dict) or not action.get("tool"):
                    continue
                steps.append(
                    {
                        "id": f"{contractId}.preflight.{idx + 1}",
                        "tool": action.get("tool"),
                        "argsTemplate": action.get("argsTemplate") or {},
                        "contractId": contractId,
                        "primaryEvidence": bool(action.get("primaryEvidence")),
                        "produces": "evidence",
                        "purpose": f"{contractId} primary evidence",
                    }
                )
            if not any(step.get("contractId") == contractId for step in steps):
                for tool in contract.get("toolNames") or ([contract.get("tool")] if contract.get("tool") else []):
                    if not tool:
                        continue
                    steps.append(
                        {
                            "id": f"{contractId}.{tool}",
                            "tool": tool,
                            "contractId": contractId,
                            "primaryEvidence": False,
                            "produces": "evidence",
                            "purpose": f"{contractId} evidence candidate",
                        }
                    )
        requiredEvidence = _unique(v for c in route_contracts for v in c.get("requiredEvidence") or [])
        artifactPolicy = _mergeDicts(c.get("artifactPolicy") for c in route_contracts)
        visualPolicy = _mergeDicts(c.get("visualPolicy") for c in route_contracts)
        freshness = _mergeDicts(c.get("freshness") for c in route_contracts)
        acceptance_criteria = _buildAcceptanceCriteria(
            route_contracts,
            requiredEvidence=requiredEvidence,
            artifactPolicy=artifactPolicy,
            visualPolicy=visualPolicy,
        )
        failure_policy = _mergeDicts(c.get("failurePolicy") for c in route_contracts) or {
            "onMissingEvidence": "repair_once",
            "onUnsupportedClaim": "disclose_or_repair",
        }
        primary_tools = _unique(step.get("tool") for step in steps if step.get("primaryEvidence"))
        required_artifacts = ["primary_csv"] if artifactPolicy.get("primaryCsv") else []
        required_visuals = (
            [str(visualPolicy.get("preferredType") or "visual")] if visualPolicy.get("requiredFor") else []
        )
        out[f"{question_type}.default"] = {
            "id": f"{question_type}.default",
            "questionType": question_type,
            "summary": f"{question_type} analysis process",
            "routeId": route.get("id"),
            "contractIds": list(route.get("contractIds") or []),
            "toolNames": list(route.get("toolNames") or []),
            "requiredTools": primary_tools,
            "requiredEvidence": requiredEvidence,
            "requiredArtifacts": required_artifacts,
            "requiredVisuals": required_visuals,
            "freshness": freshness,
            "artifactPolicy": artifactPolicy,
            "visualPolicy": visualPolicy,
            "acceptanceCriteria": acceptance_criteria,
            "failurePolicy": failure_policy,
            "steps": _dedupeSteps(steps),
        }
    return out


def _buildAcceptanceCriteria(
    contracts: list[dict[str, Any]],
    *,
    requiredEvidence: list[str],
    artifactPolicy: dict[str, Any],
    visualPolicy: dict[str, Any],
) -> dict[str, Any]:
    """Derive process acceptance criteria from contract metadata only."""
    out = _mergeDicts(c.get("acceptanceCriteria") for c in contracts)
    if requiredEvidence:
        out.setdefault("requiredEvidence", list(requiredEvidence))
    if artifactPolicy.get("primaryCsv"):
        out.setdefault("primaryCsv", True)
    if visualPolicy.get("requiredFor"):
        out.setdefault("visual", True)
    if any(c.get("comparisonCompleteness") for c in contracts):
        out.setdefault("sameAxisComparison", True)
    out.setdefault("claimSupportRateMin", 0.9)
    return out


def _unique(values: Any) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in out:
            out.append(text)
    return out


def _mergeDicts(values: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for value in values:
        if isinstance(value, dict):
            out.update(value)
    return out


def _dedupeSteps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for step in steps:
        key = json.dumps(
            {k: step.get(k) for k in ("tool", "argsTemplate", "contractId", "primaryEvidence")},
            ensure_ascii=False,
            sort_keys=True,
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(step)
    return out[:12]


def _mergeQuestionTriggers(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Merge route trigger specs from contracts sharing the same questionType."""
    if not left:
        return dict(right)
    if not right:
        return dict(left)
    merged = dict(left)
    for key, value in right.items():
        current = merged.get(key)
        if current is None:
            merged[key] = value
            continue
        if isinstance(current, list) and isinstance(value, list):
            for item in value:
                if item not in current:
                    current.append(item)
            continue
        if current != value:
            merged.setdefault("any", [])
            if isinstance(merged["any"], list):
                for item in (current, value):
                    if isinstance(item, list):
                        for inner in item:
                            if inner not in merged["any"]:
                                merged["any"].append(inner)
                    elif item not in merged["any"]:
                        merged["any"].append(item)
    return merged


def buildCapabilities() -> dict[str, Any]:
    """런타임 capabilities 카탈로그 dict 를 docstring 소스에서 라이브 빌드.

    ``__all__`` 함수 + Company 메서드 + scan/macro/gather 축 레지스트리를 하나의 dict 로.
    사본(``_generated.py``) 없이 매 프로세스 첫 조회 시 1 회 빌드(loader 가 캐시) — docstring 이
    유일 진실(operation.code §"CAPABILITIES 단일 진실의 원천"), drift 표면 0.
    """
    import dartlab
    from dartlab.providers.dart.company import Company as DartCompany

    entries: dict[str, dict[str, str]] = {}

    # 1) __all__ 함수/클래스
    allNames = getattr(dartlab, "__all__", [])
    for name in allNames:
        try:
            obj = getattr(dartlab, name, None)
        except (ImportError, ModuleNotFoundError, AttributeError):
            continue
        if obj is None:
            continue
        kind = "class" if inspect.isclass(obj) else "function" if callable(obj) else "module"
        doc = inspect.getdoc(obj)
        # callable class/module 의 __call__ docstring 이 더 풍부하면 fallback
        # _CallableModule 패턴 (scan/macro/quant): 내부 class __call__ 탐색
        if hasattr(obj, "__call__") and not inspect.isfunction(obj):
            _CALLABLE_MODULE_MAP = {
                "scan": ("dartlab.scan", "Scan"),
                "macro": ("dartlab.macro", "Macro"),
                "quant": ("dartlab.quant", "Quant"),
                "industry": ("dartlab.industry", "Industry"),
            }
            candidates = [inspect.getdoc(getattr(type(obj), "__call__", None))]
            if name in _CALLABLE_MODULE_MAP:
                mod_path, cls_name = _CALLABLE_MODULE_MAP[name]
                try:
                    import importlib as _importlib

                    mod = _importlib.import_module(mod_path)
                    if cls_name:
                        cls = getattr(mod, cls_name, None)
                        if cls:
                            candidates.append(inspect.getdoc(getattr(cls, "__call__", None)))
                    else:
                        fn = getattr(mod, name, None)
                        if fn and callable(fn):
                            candidates.append(inspect.getdoc(fn))
                except ImportError:
                    pass
            for callDoc in candidates:
                if not callDoc:
                    continue
                # Returns 있는 __call__ 우선 (모듈 docstring 이 길어도 Returns 없으면 교체)
                docHasReturns = "Returns" in (doc or "")
                callHasReturns = "Returns" in callDoc
                if callHasReturns and not docHasReturns:
                    doc = callDoc
                elif len(callDoc) > len(doc or ""):
                    doc = callDoc
        summary = doc.split("\n")[0].strip() if doc else ""
        sections = _parseDocstringSections(doc)
        entry: dict[str, Any] = {"summary": summary, "kind": kind}
        for key in ("capabilities", "requires", "aicontext", "guide", "seealso", "returns", "args", "example"):
            if val := sections.get(key):
                entry[key if key != "seealso" else "seeAlso"] = val
        if return_schema := _parseReturnsSchema(sections.get("returns")):
            entry["returnSchema"] = return_schema
        if llm_specs := _parseLLMSpecs(sections.get("llmspecifications")):
            entry["llmSpecs"] = llm_specs
        _applyAiContract(entry, sections)
        entries[name] = entry

    # 2) Company 공개 메서드/프로퍼티
    for memberName in sorted(dir(DartCompany)):
        if memberName.startswith("_"):
            continue
        obj = getattr(DartCompany, memberName, None)
        if obj is None:
            continue
        if isinstance(obj, (staticmethod, classmethod)):
            continue

        kind = "property" if isinstance(inspect.getattr_static(DartCompany, memberName), property) else "method"
        doc = None
        if kind == "property":
            prop = inspect.getattr_static(DartCompany, memberName)
            if prop.fget:
                doc = inspect.getdoc(prop.fget)
            # property fget docstring 이 빈약하면 _{name}Impl fallback (9섹션 규칙)
            implDoc = inspect.getdoc(getattr(DartCompany, f"_{memberName}Impl", None))
            if implDoc and len(implDoc) > (len(doc or "")):
                doc = implDoc
        else:
            doc = inspect.getdoc(obj)
        if doc is None:
            continue

        summary = doc.split("\n")[0].strip()
        sections = _parseDocstringSections(doc)
        entry = {"summary": summary, "kind": kind}
        for key in ("capabilities", "requires", "aicontext", "guide", "seealso", "returns", "args", "example"):
            if val := sections.get(key):
                entry[key if key != "seealso" else "seeAlso"] = val
        if return_schema := _parseReturnsSchema(sections.get("returns")):
            entry["returnSchema"] = return_schema
        if llm_specs := _parseLLMSpecs(sections.get("llmspecifications")):
            entry["llmSpecs"] = llm_specs
        _applyAiContract(entry, sections)
        entries[f"Company.{memberName}"] = entry

    # 3~6) scan/macro/gather 축 레지스트리 — 라이브 객체 introspection (install-robust,
    # AST-소스파싱 X). 레지스트리가 모듈 이동해도 추종한다 (옛 AST 는 _AXIS_REGISTRY 가
    # scan/__init__→router 로 이동하며 scan 19 축을 조용히 누락하던 버그).
    _injectAxisRegistriesLive(entries)

    _applyAiContractMetadata(entries)
    return entries


@lru_cache(maxsize=1)
def loadCapabilities() -> dict[str, Any]:
    """capability 카탈로그 — docstring 소스에서 라이브 빌드 (프로세스당 1 회 캐시).

    스킬엔진(EngineCall/ReadCapability/검색)이 처음 조회할 때 1 회 빌드하고 캐시한다.
    사본(``_generated.py``) 없음 → drift 불가, 항상 현재 docstring 진실. cold ~0.5s, warm ~18ms.
    """
    return buildCapabilities()


@lru_cache(maxsize=1)
def loadAnalysisGraph() -> dict[str, Any]:
    """analysisGraph — capability 카탈로그에서 라이브 컴파일 (프로세스당 1 회 캐시)."""
    return _buildAnalysisGraph(loadCapabilities())
