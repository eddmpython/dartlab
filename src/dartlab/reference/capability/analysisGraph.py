"""Analysis Graph lookup.

Analysis Graph is a generated index over the existing capability/docstring
surface. It is not a planner and does not own domain truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dartlab.reference.capability._contractMerge import _mergeDicts, _unique


@dataclass(frozen=True)
class QuestionProfile:
    """Machine-readable question shape used by selectors and gates."""

    types: tuple[str, ...] = ()

    def has(self, name: str) -> bool:
        """has — TODO 한국어 동작 설명."""
        return name in self.types


@dataclass(frozen=True)
class PreflightAction:
    """One graph-declared runtime action."""

    tool: str
    argsTemplate: dict[str, Any] = field(default_factory=dict)
    primaryEvidence: bool = False


@dataclass(frozen=True)
class CapabilityContract:
    """Resolved Analysis Graph contract metadata."""

    contractId: str
    tool: str | None = None
    questionTypes: tuple[str, ...] = ()
    requiredEvidence: tuple[str, ...] = ()
    evidenceSchema: dict[str, Any] = field(default_factory=dict)
    freshness: dict[str, Any] = field(default_factory=dict)
    comparisonCompleteness: dict[str, Any] = field(default_factory=dict)
    visualPolicy: dict[str, Any] = field(default_factory=dict)
    artifactPolicy: dict[str, Any] = field(default_factory=dict)
    toolArgPolicy: tuple[str, ...] = ()
    toolBudget: dict[str, Any] = field(default_factory=dict)
    preflightActions: tuple[PreflightAction, ...] = ()
    acceptanceCriteria: dict[str, Any] = field(default_factory=dict)
    failurePolicy: dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    sourceKey: str | None = None
    toolNames: tuple[str, ...] = ()

    def toDict(self) -> dict[str, Any]:
        """toDict — TODO 한국어 동작 설명."""
        return {
            "contractId": self.contractId,
            "tool": self.tool,
            "questionTypes": list(self.questionTypes),
            "requiredEvidence": list(self.requiredEvidence),
            "evidenceSchema": dict(self.evidenceSchema),
            "freshness": dict(self.freshness),
            "comparisonCompleteness": dict(self.comparisonCompleteness),
            "visualPolicy": dict(self.visualPolicy),
            "artifactPolicy": dict(self.artifactPolicy),
            "toolArgPolicy": list(self.toolArgPolicy),
            "toolBudget": dict(self.toolBudget),
            "acceptanceCriteria": dict(self.acceptanceCriteria),
            "failurePolicy": dict(self.failurePolicy),
            "preflightActions": [
                {
                    "tool": action.tool,
                    "argsTemplate": dict(action.argsTemplate),
                    "primaryEvidence": action.primaryEvidence,
                }
                for action in self.preflightActions
            ],
            "priority": self.priority,
            "sourceKey": self.sourceKey,
            "toolNames": list(self.toolNames),
        }


def graphStatus() -> dict[str, Any]:
    """graphStatus — TODO 한국어 동작 설명."""
    graph = loadAnalysisGraph()
    return {
        "graphVersion": graph.get("graphVersion"),
        "sourceHash": graph.get("sourceHash"),
        "nodeCount": len(graph.get("nodes") or []),
        "edgeCount": len(graph.get("edges") or []),
        "contractCount": len(graph.get("contracts") or {}),
        "routeCount": len(graph.get("routes") or []),
        "processMapCount": len(graph.get("processMaps") or {}),
    }


def loadAnalysisGraph() -> dict[str, Any]:
    """Analysis Graph payload — capability 카탈로그에서 라이브 컴파일 (사본 없음)."""
    try:
        from dartlab.reference.capability.builder import loadAnalysisGraph as _liveGraph

        return _liveGraph()
    except Exception:
        return {
            "graphVersion": 0,
            "sourceHash": "missing",
            "nodes": [],
            "edges": [],
            "contracts": {},
            "routes": [],
            "processMaps": {},
        }


def inferQuestionProfile(question: str | None) -> QuestionProfile:
    """Infer profile by matching generated graph route triggers."""
    q = (question or "").lower()
    types: list[str] = []
    for route in _routes():
        triggers = route.get("triggers") or {}
        if _matchesTriggers(q, triggers):
            question_type = str(route.get("questionType") or "")
            if question_type:
                types.append(question_type)
    return QuestionProfile(tuple(dict.fromkeys(types)))


def routeQuestion(
    question: str | None,
    *,
    category: str = "finance",
    intent: str | None = None,
    stockCode: str | None = None,
) -> dict[str, Any]:
    """Resolve one request into graph route metadata."""
    profile = inferQuestionProfile(question)
    contract_ids = [contract.contractId for contract in contractsForQuestion(question)]
    if intent == "compare" and "comparison.same_axis" not in contract_ids:
        contract_ids.append("comparison.same_axis")
    if intent == "act3_cash" and "cashflow.primary" not in contract_ids:
        contract_ids.append("cashflow.primary")

    tools: list[str] = []
    route_ids: list[str] = []
    for route in _routes():
        if route.get("questionType") not in profile.types:
            continue
        route_ids.append(str(route.get("id")))
        for name in route.get("toolNames") or []:
            if name and name not in tools:
                tools.append(str(name))
    for contractId in contract_ids:
        contract = allContracts().get(contractId)
        if contract is None:
            continue
        for name in contract.toolNames or ([contract.tool] if contract.tool else []):
            if name and name not in tools:
                tools.append(str(name))

    return {
        "category": category,
        "intent": intent,
        "stockCode": stockCode,
        "profileTypes": list(profile.types),
        "routeIds": route_ids,
        "contractIds": contract_ids,
        "processMapIds": _processMapIdsForProfile(profile),
        "toolNames": tools,
        "graph": graphStatus(),
    }


def allContracts() -> dict[str, CapabilityContract]:
    """Return Analysis Graph contracts keyed by contractId."""
    out: dict[str, CapabilityContract] = {}
    for contractId, raw in (loadAnalysisGraph().get("contracts") or {}).items():
        if not isinstance(raw, dict):
            continue
        parsed = _contractFromGraph(str(contractId), raw)
        out[parsed.contractId] = parsed
    return out


def contractsForQuestion(question: str | None) -> list[CapabilityContract]:
    """contractsForQuestion — TODO 한국어 동작 설명."""
    profile = inferQuestionProfile(question)
    if not profile.types:
        return []
    profile_types = set(profile.types)
    contracts = [contract for contract in allContracts().values() if set(contract.questionTypes) & profile_types]
    return sorted(contracts, key=lambda item: item.priority, reverse=True)


def contractIdsForQuestion(question: str | None) -> list[str]:
    """contractIdsForQuestion — TODO 한국어 동작 설명."""
    return [contract.contractId for contract in contractsForQuestion(question)]


def allProcessMaps() -> dict[str, dict[str, Any]]:
    """allProcessMaps — TODO 한국어 동작 설명."""
    maps = loadAnalysisGraph().get("processMaps") or {}
    return {str(k): v for k, v in maps.items() if isinstance(v, dict)}


def processMapsForQuestion(question: str | None) -> list[dict[str, Any]]:
    """processMapsForQuestion — TODO 한국어 동작 설명."""
    profile = inferQuestionProfile(question)
    ids = _processMapIdsForProfile(profile)
    maps = allProcessMaps()
    return [maps[pid] for pid in ids if pid in maps]


def understandingPacketForQuestion(
    question: str | None,
    *,
    category: str = "finance",
    intent: str | None = None,
    stockCode: str | None = None,
) -> dict[str, Any]:
    """Compact LLM-facing contract packet for one request."""
    route = routeQuestion(question, category=category, intent=intent, stockCode=stockCode)
    processMaps = processMapsForQuestion(question)
    contracts = [allContracts()[cid].toDict() for cid in route["contractIds"] if cid in allContracts()]
    process_acceptance = _mergeDicts(p.get("acceptanceCriteria") for p in processMaps)
    process_failure = _mergeDicts(p.get("failurePolicy") for p in processMaps)
    return _dropEmpty(
        {
            "question": question,
            "routeIds": route["routeIds"],
            "contractIds": route["contractIds"],
            "processMapIds": route["processMapIds"],
            "candidateTools": route["toolNames"],
            "requiredEvidence": _unique(v for c in contracts for v in c.get("requiredEvidence") or []),
            "artifactPolicy": _mergeDicts(c.get("artifactPolicy") for c in contracts),
            "visualPolicy": _mergeDicts(c.get("visualPolicy") for c in contracts),
            "freshness": _mergeDicts(c.get("freshness") for c in contracts),
            "acceptanceCriteria": process_acceptance or _mergeDicts(c.get("acceptanceCriteria") for c in contracts),
            "failurePolicy": process_failure or _mergeDicts(c.get("failurePolicy") for c in contracts),
            "toolArgPolicy": _unique(v for c in contracts for v in c.get("toolArgPolicy") or []),
            "processMaps": [_compactProcessMap(p) for p in processMaps],
            "graph": route.get("graph"),
        }
    )


def planDartlabQuestion(question: str, stockCode: str | None = None) -> dict[str, Any]:
    """MCP-facing graph plan for an external LLM agent."""
    return understandingPacketForQuestion(question, stockCode=stockCode)


def explainDartlabTool(toolName: str) -> dict[str, Any]:
    """Explain one DartLab tool through graph contracts that reference it."""
    contracts = []
    for contract in allContracts().values():
        names = set(contract.toolNames or ())
        if contract.tool:
            names.add(contract.tool)
        if toolName in names:
            contracts.append(contract.toDict())
    return {
        "toolName": toolName,
        "contracts": contracts,
        "requiredEvidence": _unique(v for c in contracts for v in c.get("requiredEvidence") or []),
        "toolArgPolicy": _unique(v for c in contracts for v in c.get("toolArgPolicy") or []),
        "artifactPolicy": _mergeDicts(c.get("artifactPolicy") for c in contracts),
        "visualPolicy": _mergeDicts(c.get("visualPolicy") for c in contracts),
    }


def validateDartlabPlan(question: str, proposedTools: list[str] | str) -> dict[str, Any]:
    """Validate an external agent's tool plan against graph contracts."""
    tools = _coerceToolList(proposedTools)
    packet = understandingPacketForQuestion(question)
    required_tools = _primaryTools(packet.get("processMaps") or [])
    candidate_tools = set(packet.get("candidateTools") or [])
    missing = [tool for tool in required_tools if tool not in tools]
    invalid = [tool for tool in tools if candidate_tools and tool not in candidate_tools]
    warnings: list[str] = []
    if packet.get("artifactPolicy", {}).get("primaryCsv") and "pythonExec" not in tools and "gather" not in tools:
        warnings.append("primary CSV 질문은 계산/수집 tool 결과가 필요합니다.")
    if packet.get("visualPolicy", {}).get("requiredFor") and not tools:
        warnings.append("visual explanation required question has no proposed tools.")
    return {
        "ok": not missing and not invalid,
        "question": question,
        "proposedTools": tools,
        "requiredPrimaryTools": required_tools,
        "missingPrimaryTools": missing,
        "invalidTools": invalid,
        "warnings": warnings,
        "contractIds": packet.get("contractIds") or [],
        "processMapIds": packet.get("processMapIds") or [],
        "acceptanceCriteria": packet.get("acceptanceCriteria") or {},
    }


def listDartlabProcesses() -> list[dict[str, Any]]:
    """List generated process maps in compact form."""
    return [_compactProcessMap(process) for process in allProcessMaps().values()]


def contractForTool(name: str, arguments: dict[str, Any] | None = None) -> CapabilityContract | None:
    """contractForTool — TODO 한국어 동작 설명."""
    args = arguments or {}
    for contract in sorted(allContracts().values(), key=lambda item: item.priority, reverse=True):
        raw = _rawContract(contract.contractId)
        for matcher in raw.get("toolMatch") or []:
            if _matchesTool(name, args, matcher):
                return contract
    for contract in allContracts().values():
        raw = _rawContract(contract.contractId)
        if raw.get("toolMatch"):
            continue
        if contract.tool == name:
            return contract
    return None


def answerContractNames(question: str | None, toolCalls: list[dict[str, Any]]) -> set[str]:
    """Compatibility-level answer contract names derived from graph contracts."""
    contract_ids = set(contractIdsForQuestion(question))
    for call in toolCalls:
        args = call.get("arguments") or call.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        contract = contractForTool(str(call.get("name") or ""), args)
        if contract:
            contract_ids.add(contract.contractId)

    names: set[str] = set()
    if contract_ids & {"gather.krx.close", "macro.recent"}:
        names.add("recent")
    if "comparison.same_axis" in contract_ids:
        names.add("comparison")
    if "disclosure.importance" in contract_ids:
        names.add("disclosure")
    if "capabilities.valid_key" in contract_ids:
        names.add("capabilities")
    return names


def preflightActionsForQuestion(
    *,
    question: str | None,
    category: str,
    intent: str | None,
    stockCode: str | None = None,
) -> list[tuple[str, dict[str, Any], CapabilityContract]]:
    """preflightActionsForQuestion — TODO 한국어 동작 설명."""
    if category != "finance":
        return []
    route = routeQuestion(question, category=category, intent=intent, stockCode=stockCode)
    actions: list[tuple[str, dict[str, Any], CapabilityContract]] = []
    for contractId in route["contractIds"]:
        contract = allContracts().get(contractId)
        if contract is None:
            continue
        for action in contract.preflightActions:
            args = dict(action.argsTemplate)
            if action.tool in {"analysis", "show"} and stockCode and contract.contractId != "comparison.same_axis":
                args.setdefault("stockCode", stockCode)
            if (
                action.tool in {"analysis", "show"}
                and contract.contractId != "comparison.same_axis"
                and not args.get("stockCode")
            ):
                continue
            actions.append((action.tool, args, contract))
    return actions


def toolBudgetForQuestion(question: str | None, intent: str | None) -> dict[str, Any]:
    """toolBudgetForQuestion — TODO 한국어 동작 설명."""
    route = routeQuestion(question, intent=intent)
    budget: dict[str, Any] = {}
    for contractId in route["contractIds"]:
        contract = allContracts().get(contractId)
        if contract is not None:
            budget.update(contract.toolBudget)
    return budget


def toolNamesForQuestion(question: str | None, *, intent: str | None = None) -> list[str]:
    """toolNamesForQuestion — TODO 한국어 동작 설명."""
    return [str(v) for v in routeQuestion(question, intent=intent).get("toolNames") or []]


def requiresVisualExplanation(question: str | None) -> bool:
    """requiresVisualExplanation — TODO 한국어 동작 설명."""
    for contract in contractsForQuestion(question):
        policy = contract.visualPolicy or {}
        if policy.get("requiredFor"):
            return True
    return False


def contextForQuestion(question: str, stockCode: str | None = None) -> dict[str, Any]:
    """MCP-facing compact route context."""
    route = routeQuestion(question, stockCode=stockCode)
    return {
        "question": question,
        "route": route,
        "contracts": [allContracts()[cid].toDict() for cid in route["contractIds"] if cid in allContracts()],
        "processMaps": processMapsForQuestion(question),
        "understandingPacket": understandingPacketForQuestion(question, stockCode=stockCode),
    }


def queryAnalysisGraph(query: str, *, kind: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """Simple graph search over node labels, ids, contract ids, and sources."""
    q = query.lower().strip()
    if not q:
        return []
    rows: list[dict[str, Any]] = []
    graph = loadAnalysisGraph()
    for node in graph.get("nodes") or []:
        if kind and node.get("kind") != kind:
            continue
        haystack = " ".join(str(node.get(k) or "") for k in ("id", "kind", "label", "source")).lower()
        if q in haystack:
            rows.append({"score": 1.0, **node})
    for contractId, contract in (graph.get("contracts") or {}).items():
        haystack = " ".join(
            str(contract.get(k) or "") for k in ("contractId", "tool", "summary", "sourceKey", "questionTypes")
        ).lower()
        if q in haystack:
            rows.append(
                {
                    "score": 0.9,
                    "id": f"contract:{contractId}",
                    "kind": "contract",
                    "label": contract.get("summary") or contractId,
                    "source": contract.get("sourceKey"),
                }
            )
    for process_id, process in (graph.get("processMaps") or {}).items():
        haystack = " ".join(
            str(process.get(k) or "") for k in ("id", "questionType", "summary", "contractIds", "toolNames")
        ).lower()
        if q in haystack:
            rows.append(
                {
                    "score": 0.85,
                    "id": f"process:{process_id}",
                    "kind": "process",
                    "label": process.get("summary") or process_id,
                    "source": process.get("questionType"),
                }
            )
    return rows[: max(1, min(int(limit or 10), 50))]


def impactForGraphNode(nodeId: str) -> dict[str, Any]:
    """Return graph edges adjacent to one node."""
    graph = loadAnalysisGraph()
    edges = [
        edge
        for edge in graph.get("edges") or []
        if isinstance(edge, dict) and (edge.get("from") == nodeId or edge.get("to") == nodeId)
    ]
    return {"nodeId": nodeId, "edges": edges, "edgeCount": len(edges)}


def _routes() -> list[dict[str, Any]]:
    return [route for route in loadAnalysisGraph().get("routes") or [] if isinstance(route, dict)]


def _processMapIdsForProfile(profile: QuestionProfile) -> list[str]:
    ids: list[str] = []
    for route in _routes():
        if route.get("questionType") not in profile.types:
            continue
        for pid in route.get("processMapIds") or []:
            if pid and pid not in ids:
                ids.append(str(pid))
    return ids


def _rawContract(contractId: str) -> dict[str, Any]:
    raw = (loadAnalysisGraph().get("contracts") or {}).get(contractId) or {}
    return raw if isinstance(raw, dict) else {}


def _contractFromGraph(contractId: str, entry: dict[str, Any]) -> CapabilityContract:
    preflights: list[PreflightAction] = []
    for raw in entry.get("preflightActions") or []:
        if isinstance(raw, dict) and raw.get("tool"):
            preflights.append(
                PreflightAction(
                    str(raw.get("tool")),
                    dict(raw.get("argsTemplate") or {}),
                    bool(raw.get("primaryEvidence")),
                )
            )
    return CapabilityContract(
        contractId=str(entry.get("contractId") or contractId),
        tool=entry.get("tool"),
        questionTypes=tuple(str(v) for v in entry.get("questionTypes") or ()),
        requiredEvidence=tuple(str(v) for v in entry.get("requiredEvidence") or ()),
        evidenceSchema=dict(entry.get("evidenceSchema") or {}),
        freshness=dict(entry.get("freshness") or {}),
        comparisonCompleteness=dict(entry.get("comparisonCompleteness") or {}),
        visualPolicy=dict(entry.get("visualPolicy") or {}),
        artifactPolicy=dict(entry.get("artifactPolicy") or {}),
        toolArgPolicy=tuple(str(v) for v in entry.get("toolArgPolicy") or ()),
        toolBudget=dict(entry.get("toolBudget") or {}),
        acceptanceCriteria=dict(entry.get("acceptanceCriteria") or {}),
        failurePolicy=dict(entry.get("failurePolicy") or {}),
        preflightActions=tuple(preflights),
        priority=int(entry.get("priority") or 50),
        sourceKey=str(entry.get("sourceKey") or "") or None,
        toolNames=tuple(str(v) for v in entry.get("toolNames") or ()),
    )


def _matchesTriggers(q: str, triggers: dict[str, Any]) -> bool:
    if not triggers:
        return False
    any_terms = [str(v).lower() for v in triggers.get("any") or []]
    if any_terms and any(term in q for term in any_terms):
        return True
    all_any = triggers.get("allAny") or []
    if all_any:
        for group in all_any:
            terms = [str(v).lower() for v in group or []]
            if not terms or not any(term in q for term in terms):
                return False
        return True
    return False


def _matchesTool(name: str, args: dict[str, Any], matcher: dict[str, Any]) -> bool:
    if str(matcher.get("tool") or "") != name:
        return False
    arg_rules = matcher.get("args") or {}
    if not isinstance(arg_rules, dict):
        return True
    for key, expected in arg_rules.items():
        if key.endswith("In"):
            arg_key = key[:-2]
            values = {str(v).lower() for v in expected or []}
            if str(args.get(arg_key) or "").lower() not in values:
                return False
            continue
        if str(args.get(key) or "").lower() != str(expected).lower():
            return False
    return True


def _compactProcessMap(process: dict[str, Any]) -> dict[str, Any]:
    return _dropEmpty(
        {
            "id": process.get("id"),
            "questionType": process.get("questionType"),
            "contractIds": process.get("contractIds") or [],
            "toolNames": process.get("toolNames") or [],
            "requiredTools": process.get("requiredTools") or [],
            "requiredEvidence": process.get("requiredEvidence") or [],
            "requiredArtifacts": process.get("requiredArtifacts") or [],
            "requiredVisuals": process.get("requiredVisuals") or [],
            "freshness": process.get("freshness") or {},
            "artifactPolicy": process.get("artifactPolicy") or {},
            "visualPolicy": process.get("visualPolicy") or {},
            "acceptanceCriteria": process.get("acceptanceCriteria") or {},
            "failurePolicy": process.get("failurePolicy") or {},
            "steps": [
                _dropEmpty(
                    {
                        "tool": step.get("tool"),
                        "argsTemplate": step.get("argsTemplate") or {},
                        "contractId": step.get("contractId"),
                        "primaryEvidence": step.get("primaryEvidence"),
                        "purpose": step.get("purpose"),
                    }
                )
                for step in process.get("steps") or []
                if isinstance(step, dict)
            ],
        }
    )


def _primaryTools(processMaps: list[dict[str, Any]]) -> list[str]:
    tools: list[str] = []
    for process in processMaps:
        for step in process.get("steps") or []:
            if not isinstance(step, dict) or not step.get("primaryEvidence"):
                continue
            tool = str(step.get("tool") or "")
            if tool and tool not in tools:
                tools.append(tool)
    return tools


def _coerceToolList(value: list[str] | str) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.replace(">", ",").replace("→", ",").split(",") if part.strip()]
    return [str(v).strip() for v in value if str(v).strip()]


def _dropEmpty(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v not in (None, "", [], {})}
