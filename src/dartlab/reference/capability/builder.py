"""capability 카탈로그 라이브 빌더 - 엔진 docstring/registry introspect → 런타임 dict.

``loadCapabilities()`` 가 스킬엔진(EngineCall · ReadCapability · 검색) 첫 조회 시 docstring 소스에서
1 회 빌드(프로세스 캐시)한다. **사본(생성 파일) 없음** - docstring 이 유일 진실
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
# ─── Surface 1: Python API (__init__.py __all__) ────────────────
# ─── Surface 2: CLI (COMMAND_SPECS) ────────────────────────────
# ─── Surface 3: Server API (AST 기반 라우터 파싱) ──────────────
# ─── Surface 4: Data Modules (registry) ────────────────────────
# ─── Surface 5: AI Tools (super tools AST 파싱) ────────────────
# ─── 런타임 capability 카탈로그 생성 ──────────────────────────
# axis-engine 라이브 축 레지스트리 - 모듈 이동 추종 (AST-소스 의존 0, install-robust).
# gather 표준(engine(axis, target)) 전 엔진을 {engine}.{axis} 로 카탈로그 등록.
from dartlab.reference.capability._contractMerge import _mergeDicts, _unique
from dartlab.reference.capability.dataProducts import axisRegistryTargets
from dartlab.reference.capability.docstringSections import (
    _applyAiContract,
    _parseAiContract,
    _parseDocstringSections,
    _parseLLMSpecs,
    _parseReturnsSchema,
)

_AXIS_REGISTRIES: tuple[tuple[str, str, str], ...] = axisRegistryTargets()


# 축 엔트리에서 카탈로그로 실을 필요가 없는 필드. **항목마다 사유 필수** (게으른 덤프 방지).
_AXIS_IGNORE_FIELDS: frozenset[str] = frozenset(
    {
        "label",  # summary 로 이미 투영
        "description",  # capabilities 로 이미 투영
        "example",  # top-level example 필드로 별도 투영
        "module",  # 구현 위치 (선언이 아님)
        "fn",  # 구현 위치 (선언이 아님)
        "listModule",  # 구현 위치 (선언이 아님)
        "axis",  # credit 전용. "{prefix}.{axis}" 키와 중복
    }
)


def _jsonSafeDeclaredValue(value: Any) -> Any:
    """선언 값을 JSON 소비처가 받을 수 있는 형태로 보존한다."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _jsonSafeDeclaredValue(getattr(value, field.name, None)) for field in dataclasses.fields(value)
        }
    if isinstance(value, (list, tuple)):
        return [_jsonSafeDeclaredValue(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonSafeDeclaredValue(item) for key, item in value.items()}
    return str(value)


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
        declared[field.name] = _jsonSafeDeclaredValue(value)
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
            label = getattr(entry, "label", None)
            description = getattr(entry, "description", None)
            axisEntry["summary"] = str(label or description or axisName)
            if description:
                axisEntry["capabilities"] = str(description)
            example = getattr(entry, "example", None)
            if example:
                axisEntry["example"] = _jsonSafeDeclaredValue(example)
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


def _applyExecutionMetadata(entries: dict[str, dict[str, Any]]) -> None:
    """검색 가능 capability와 EngineCall 실행 권한을 각 entry에 명시한다."""
    from dartlab.reference.capability.execution import (
        canonicalReplacementRefs,
        engineCallContract,
        executionGuide,
        isEngineCallableRef,
    )

    for apiRef, entry in entries.items():
        engineCallable = isEngineCallableRef(apiRef)
        replacementRefs = canonicalReplacementRefs(apiRef, entry)
        entry["engineCallable"] = engineCallable
        entry["replacementRefs"] = list(replacementRefs)
        entry["execution"] = engineCallContract(apiRef, entry)
        entry["executionGuide"] = executionGuide(
            apiRef,
            engineCallable=engineCallable,
            replacementRefs=replacementRefs,
        )


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


def _appendContractSteps(contract: dict[str, Any], steps: list[dict[str, Any]]) -> None:
    """계약 하나가 만드는 실행 단계를 누적 목록에 붙인다.

    preflight 로 선언된 것이 있으면 그것이 곧 단계다. 하나도 없을 때만 도구 이름으로
    후보 단계를 만든다. "없을 때만" 을 판정하려면 이미 쌓인 목록을 봐야 해서 함수가
    누적 목록을 받는다. 반환값으로 바꾸면 그 판정이 호출부로 새어 나간다.
    """
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
    if any(step.get("contractId") == contractId for step in steps):
        return
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
            _appendContractSteps(contract, steps)
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


_ENTRY_SECTION_KEYS = ("capabilities", "requires", "aicontext", "guide", "seealso", "returns", "args", "example")

# Provider 라우팅용 static/class method 는 root ``dartlab.Company`` factory 의 구현
# 세부사항이다. 또한 Phase 10 때 실험적으로 붙었던 아래 4개 서사 helper 는 현재
# 안정 public surface(``Company.story`` / ``Company.reportModel`` / ``Company.simulate``)
# 밖의 하위호환 메서드다. Python 직접 호출은 깨지지 않게 남기되 capability 검색과
# EngineCall allowlist 에서는 제외한다.
_COMPATIBILITY_ONLY_COMPANY_MEMBERS = frozenset({"causalWeights", "valuationImpact", "storyTree", "narrativeDiff"})


def _entryFromDoc(doc: str, kind: str) -> dict[str, Any]:
    """docstring 하나를 카탈로그 entry 로 조립한다.

    `__all__` 훑는 자리와 Company 메서드 훑는 자리가 이 열두 줄을 글자까지 똑같이 갖고
    있었다. 카탈로그에 새 섹션을 하나 붙이려면 두 곳을 다 고쳐야 했고, 한 곳만 고치면
    같은 카탈로그 안에서 항목 종류에 따라 섹션이 있다 없다 했다.
    """
    entry: dict[str, Any] = {"summary": doc.split("\n")[0].strip(), "kind": kind}
    sections = _parseDocstringSections(doc)
    for key in _ENTRY_SECTION_KEYS:
        if value := sections.get(key):
            entry[key if key != "seealso" else "seeAlso"] = value
    if returnSchema := _parseReturnsSchema(sections.get("returns")):
        entry["returnSchema"] = returnSchema
    if llmSpecs := _parseLLMSpecs(sections.get("llmspecifications")):
        entry["llmSpecs"] = llmSpecs
    _applyAiContract(entry, sections)
    return entry


def _richestCallableDoc(obj: Any, name: str, doc: str | None) -> str | None:
    """호출 가능한 모듈이나 클래스에서 가장 내용 많은 docstring 을 고른다.

    `_CallableModule` 패턴(scan, macro, quant)은 모듈 docstring 보다 내부 `__call__` 쪽이
    풍부하다. Returns 를 가진 쪽을 우선하고, 없으면 긴 쪽을 쓴다.
    """
    from dartlab.reference.capability.dataProducts import callableModuleTargets

    callableModuleMap = callableModuleTargets()
    candidates = [inspect.getdoc(getattr(type(obj), "__call__", None))]
    if name in callableModuleMap:
        modPath, className = callableModuleMap[name]
        try:
            import importlib as _importlib

            module = _importlib.import_module(modPath)
            if className:
                cls = getattr(module, className, None)
                if cls:
                    candidates.append(inspect.getdoc(getattr(cls, "__call__", None)))
            else:
                fn = getattr(module, name, None)
                if fn and callable(fn):
                    candidates.append(inspect.getdoc(fn))
        except ImportError:
            pass
    for callDoc in candidates:
        if not callDoc:
            continue
        # Returns 있는 __call__ 우선 (모듈 docstring 이 길어도 Returns 없으면 교체)
        if "Returns" in callDoc and "Returns" not in (doc or ""):
            doc = callDoc
        elif len(callDoc) > len(doc or ""):
            doc = callDoc
    return doc


def _companyMemberDoc(companyClass: Any, memberName: str) -> tuple[str, str] | None:
    """Company 멤버의 종류와 docstring 을 고른다. 문서가 없으면 None.

    property 는 fget 의 docstring 이 빈약할 때 `_{name}Impl` 쪽을 쓴다. 9 섹션 규칙이
    구현 함수에 붙어 있는 경우가 있어서다.
    """
    static = inspect.getattr_static(companyClass, memberName, None)
    if static is None or isinstance(static, (staticmethod, classmethod)):
        return None
    obj = getattr(companyClass, memberName, None)
    if obj is None:
        return None
    if isinstance(static, property):
        doc = inspect.getdoc(static.fget) if static.fget else None
        implDoc = inspect.getdoc(getattr(companyClass, f"_{memberName}Impl", None))
        if implDoc and len(implDoc) > len(doc or ""):
            doc = implDoc
        return ("property", doc) if doc else None
    doc = inspect.getdoc(obj)
    return ("method", doc) if doc else None


def buildCapabilities() -> dict[str, Any]:
    """런타임 capabilities 카탈로그 dict 를 docstring 소스에서 라이브 빌드.

    ``__all__`` 함수 + Company 메서드 + scan/macro/gather 축 레지스트리를 하나의 dict 로.
    사본(``_generated.py``) 없이 매 프로세스 첫 조회 시 1 회 빌드(loader 가 캐시). docstring 이
    유일 진실(operation.code §"CAPABILITIES 단일 진실의 원천"), drift 표면 0.
    """
    import dartlab
    from dartlab.providers.dart.company import Company as DartCompany

    entries: dict[str, dict[str, Any]] = {}

    # 1) __all__ 함수/클래스
    for name in getattr(dartlab, "__all__", []):
        try:
            obj = getattr(dartlab, name, None)
        except (ImportError, ModuleNotFoundError, AttributeError):
            continue
        if obj is None:
            continue
        kind = "class" if inspect.isclass(obj) else "function" if callable(obj) else "module"
        doc = inspect.getdoc(obj)
        if hasattr(obj, "__call__") and not inspect.isfunction(obj):
            doc = _richestCallableDoc(obj, name, doc)
        entries[name] = _entryFromDoc(doc or "", kind)

    # 2) Company 공개 메서드/프로퍼티
    for memberName in sorted(dir(DartCompany)):
        if memberName.startswith("_") or memberName in _COMPATIBILITY_ONLY_COMPANY_MEMBERS:
            continue
        resolved = _companyMemberDoc(DartCompany, memberName)
        if resolved is None:
            continue
        kind, doc = resolved
        entries[f"Company.{memberName}"] = _entryFromDoc(doc, kind)

    # 3~6) scan/macro/gather 축 레지스트리. 라이브 객체 introspection (install-robust,
    # AST-소스파싱 X). 레지스트리가 모듈 이동해도 추종한다 (옛 AST 는 _AXIS_REGISTRY 가
    # scan/__init__ 에서 router 로 이동하며 scan 19 축을 조용히 누락하던 버그).
    _injectAxisRegistriesLive(entries)

    _applyAiContractMetadata(entries)
    _applyExecutionMetadata(entries)
    return entries


@lru_cache(maxsize=1)
def loadCapabilities() -> dict[str, Any]:
    """capability 카탈로그 - docstring 소스에서 라이브 빌드 (프로세스당 1 회 캐시).

    스킬엔진(EngineCall/ReadCapability/검색)이 처음 조회할 때 1 회 빌드하고 캐시한다.
    사본(``_generated.py``) 없음 → drift 불가, 항상 현재 docstring 진실. cold ~0.5s, warm ~18ms.
    """
    return buildCapabilities()


@lru_cache(maxsize=1)
def loadAnalysisGraph() -> dict[str, Any]:
    """analysisGraph - capability 카탈로그에서 라이브 컴파일 (프로세스당 1 회 캐시)."""
    return _buildAnalysisGraph(loadCapabilities())
