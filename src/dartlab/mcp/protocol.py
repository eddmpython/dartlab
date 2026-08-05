"""MCP protocol surface shared by stdio, SSE, and tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_INSTRUCTION_PREAMBLE = """\
DartLab MCP는 설치형 agent CLI에 Skill OS, 데이터, 분석 도구를 제공한다. tools/list가
광고하는 목록이 유일한 정본이다. 모델 호출과 전체 답변 loop는 agent CLI가 소유하므로
재귀 호출을 만드는 ask 도구는 광고하지 않는다. 목적은 agent가 DartLab을 프롬프트 지식으로
외우는 대신 skill과 capability 계약을 찾고 실제 엔진 결과와 ref를 근거로 답하게 하는 것이다.\
"""

_INSTRUCTION_CLOSING = """\
## 경계
- Company, gather, scan, macro, analysis, quant, viz는 개별 MCP 도구로 우회하지 않는다.
  EngineCall 의 apiRef 로 지목하는 DartLab 라이브러리다.
- Skills는 MCP 전용 규칙이 아니라 dartlab.skills 공용 runtime을 그대로 노출한다.
- 삭제된 운영 문서 경로를 공식 진입점으로 안내하지 않는다. 모든 절차는 Skill OS에서 찾는다.
- 도구로 확인되지 않은 수치, 날짜, 실행 성공 여부를 단정하지 않는다.
- 후보·상위·랭킹 결과를 표 없이 종목명과 퍼센트만 나열하지 않는다.
- 옛 generated 도구(companyAnalysis, marketScan, gatherData 등)와 DARTLAB_MCP_COMPAT 는 폐기되었다.
  같은 일은 위 목록의 도구로 한다. 예: EngineCall({"apiRef": "Company.analysis",
  "args": {"stockCode": "005930", "axis": "수익성"}}).\
"""

# 광고되지 않는 도구를 지침이 가르치면 설치된 agent 는 없는 도구의 사용법을 배운다. 실측(2026-08-05):
# 실서비스 agent 프로필이 18 개를 광고하는데 정적 지침은 RunPython 을 9 회, SaveArtifact 를 1 회
# 가르치고 있었다. 그래서 도구 목록은 손으로 적지 않고 광고 SSOT 에서 생성한다.
_MAX_TOOL_SUMMARY = 150


def _toolSummaries() -> dict[str, str]:
    """등록된 도구의 이름과 한 줄 설명을 registry SSOT 에서 가져온다."""
    from dartlab.ai.tools.registry import toolSpecs

    summaries: dict[str, str] = {}
    for spec in toolSpecs():
        name = str(spec.get("name") or "")
        text = " ".join(str(spec.get("description") or "").split())
        if name:
            summaries[name] = text[:_MAX_TOOL_SUMMARY].rstrip()
    return summaries


def mcpInstructions(profile: str | None = None) -> str:
    """해당 프로필이 실제로 광고하는 도구만 담은 MCP 지침을 만든다.

    Args:
        profile: `agent` 또는 `full`. 생략하면 DARTLAB_MCP_PROFILE 환경변수를 따른다.

    Returns:
        str: 광고 목록과 어긋나지 않는 지침 본문.

    Example:
        `text = mcpInstructions("agent")`
    """
    advertised = mcpAdvertisedToolNames(profile)
    summaries = _toolSummaries()
    catalog = "\n".join(f"- {name}: {summaries.get(name, '')}".rstrip() for name in advertised)
    hasCompute = "RunPython" in advertised

    flow = [
        "## 기본 흐름",
        '1. 작업이 모호하거나 처음 만나는 도메인이면 `ReadSkill(query="start.dartlabSkillOs")` 를 먼저 호출한다.'
        " 분류 노드가 5 카테고리 (start/runtime/operation/engines/recipes) 와 작업 결을 매핑한다.",
        "2. ReadSkill 로 절차를 찾고 ReadCapability 로 apiRef 와 `engineCallable` 을 확인한 뒤"
        " EngineCall 로 실행하고 답변에 ref 를 남긴다.",
    ]
    if hasCompute:
        flow.append(
            "3. 비교·집계·시계열 가공처럼 여러 결과를 결합해야 하면 RunPython 을 쓴다."
            " 데이터셋 스키마와 최신 기준시점도 RunPython 안에서 dartlab.* 직접 호출로 확인한다."
        )
    else:
        flow.append(
            "3. 임의 코드 실행 도구는 이 프로필에 없다. 여러 결과가 필요하면 EngineCall 을 나눠 부르고"
            " 결합과 계산은 답변에서 직접 수행한다. 전용 분석 도구가 있으면 그쪽이 먼저다."
        )
    flow.append(
        "4. 후보·상위·랭킹 답변은 bullet 나열로 끝내지 않고 입력/유니버스, 필터, 계산식/지표,"
        " 결과와 evidence table 을 함께 낸다."
    )

    return "\n\n".join(
        [
            _INSTRUCTION_PREAMBLE,
            f"## 광고 도구 {len(advertised)} 종 (이 목록이 전부다)\n{catalog}",
            "\n".join(flow),
            _INSTRUCTION_CLOSING,
        ]
    )


def __getattr__(name: str) -> Any:
    """`MCP_INSTRUCTIONS` 를 첫 참조 시점에 만든다. import 시 registry 순환을 피한다."""
    if name == "MCP_INSTRUCTIONS":
        return mcpInstructions()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def mcpAdvertisedToolNames(profile: str | None = None) -> tuple[str, ...]:
    """MCP tools/list 에 advertise 할 분석 도구 이름 SSOT.

    `ask`는 제외한다. 설치형 에이전트가 다시 DartLab AI를 호출하면 재귀 런타임이 되므로
    MCP는 데이터, Skill OS, 실행 도구만 제공한다.
    """
    from dartlab.ai.tools.registry import CANONICAL_V2, isToolReadOnly

    selected = str(profile or os.environ.get("DARTLAB_MCP_PROFILE") or "full").strip().casefold()
    if selected == "agent":
        return tuple(name for name in CANONICAL_V2 if isToolReadOnly(name))
    if selected != "full":
        raise ValueError(f"지원하지 않는 MCP profile: {selected}")
    return tuple(CANONICAL_V2)


def isMcpAdvertisedTool(name: str) -> bool:
    """MCP ``tools/call`` 에서 실행 가능한 이름인지 advertise SSOT로 판정한다."""
    return str(name) in mcpAdvertisedToolNames()


def askWorkbenchToolSpecs() -> list[dict[str, Any]]:
    """Ask Workbench registry 에서 MCP 노출 도구 spec 을 만든다.

    Returns:
        list[dict[str, Any]]: ask + registry canonical tool spec 목록.

    Example:
        `names = [spec["name"] for spec in askWorkbenchToolSpecs()]`

    Raises:
        KeyError: MCP 노출 목록과 registry canonical tool 이름이 불일치할 때.
    """
    from dartlab.ai.tools.registry import toolSpecs as aiToolSpecs

    specs = {spec["name"]: spec for spec in aiToolSpecs()}
    # 광고와 실행 schema 사이 drift 는 서버 시작 전에 즉시 드러나야 한다. 누락을
    # silently skip 하면 tools/list 와 call allowlist 가 서로 다른 표면이 된다.
    advertised = mcpAdvertisedToolNames()
    missing = [name for name in advertised if name not in specs]
    if missing:
        raise KeyError(f"MCP advertised tool spec 누락: {missing}")
    return [specs[name] for name in advertised]


def executeAskWorkbenchTool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Ask Workbench 또는 compatibility 도구를 실행한다.

    Args:
        name: MCP tool name 또는 compatibility alias.
        args: JSON-serializable tool arguments.

    Returns:
        dict[str, Any]: ToolResult structuredContent 로 노출할 payload.

    Example:
        `payload = executeAskWorkbenchTool("ReadSkill", {"query": "MCP"})`

    Raises:
        RuntimeError: 하위 registry tool 실행이 실패할 때.
    """
    from dartlab.ai.tools.formatting import wrapExternalInResult
    from dartlab.ai.tools.registry import CANONICAL_TOOL_NAMES as aiToolNames
    from dartlab.ai.tools.registry import executeTool as executeAiTool

    # 외부 본문에 untrusted 마커를 씌우는 것은 MCP 쪽에도 필요하다. 예전에는 이 경로가
    # 통째로 빠져 있어서, MCP 클라이언트는 웹 검색 본문과 스킬 마켓 본문을 마커 없이 받았다.
    # external ref 가 없으면 원본을 그대로 돌려주므로 나머지 도구에는 영향이 없다.
    if name in aiToolNames:
        return wrapExternalInResult(executeAiTool(name, args))
    return wrapExternalInResult(executeCompatAskTool(name, args))


def executeCompatAskTool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """기존 MCP alias 를 canonical Ask Workbench 도구로 정렬한다.

    Args:
        name: compatibility tool name.
        args: JSON-serializable tool arguments.

    Returns:
        dict[str, Any]: canonical tool 실행 결과 또는 migration error.

    Example:
        `payload = executeCompatAskTool("skill_search", {"query": "테스트"})`

    Raises:
        RuntimeError: skill/capability resolver 호출이 실패할 때.
    """
    from dartlab.ai.tools.registry import executeTool as executeAiTool

    if name == "ask_kernel_status":
        # tools = advertised SSOT(mcpAdvertisedToolNames). 옛 12-tuple leak(LookAheadGuard·
        # RequestUserInput) 제거. 'passes'(5-pass GRAPH_NODES) 노출도 제거. chat-native 정체성상
        # 고정 노드 그래프를 외부 resource 로 광고하지 않는다 (debt-honesty P2-6 / SD-2).
        return {
            "name": "DartLab Agent Tools",
            "entry": "agent-cli",
            "tools": list(mcpAdvertisedToolNames()),
        }
    if name == "search_reference":
        query = str(args.get("query") or "")
        skills = executeAiTool("ReadSkill", {"query": query, "limit": args.get("limit") or 5})
        specs = executeAiTool("ReadCapability", {"query": query, "limit": args.get("limit") or 5})
        return {
            "ok": bool(skills.get("ok") or specs.get("ok")),
            "refs": [*(skills.get("refs") or []), *(specs.get("refs") or [])],
        }
    if name == "listDartlabSkills":
        from dartlab.skills import listSkills

        return {"skills": [skill.toDict() for skill in listSkills(includeUser=bool(args.get("includeUser", True)))]}
    if name in {"searchDartlabSkills", "skill_search"}:
        return executeAiTool(
            "ReadSkill",
            {
                "query": args.get("query", ""),
                "limit": args.get("limit") or 8,
                "includeUser": args.get("includeUser", True),
            },
        )
    if name == "explainDartlabSkill":
        return executeAiTool("GetSkillBody", {"skillId": args.get("skillId")})
    if name == "checkDartlabSkillEvidence":
        from dartlab.skills import checkEvidence

        return checkEvidence(
            str(args.get("skillId") or ""), args.get("refs") or [], includeUser=bool(args.get("includeUser", True))
        ).toDict()
    return {
        "ok": False,
        "error": (
            f"Unknown tool: {name}. 0.10 부터 33 generated 도구 (companyStory / companyAnalysis / "
            f"marketScan 등) 와 DARTLAB_MCP_COMPAT 환경변수가 제거되었습니다. 단일 호출은 "
            'EngineCall({"apiRef": "Company.analysis", "args": {...}}) 양식, 다단 가공만 '
            "RunPython 으로. 자세한 마이그레이션은 CHANGELOG 참조."
        ),
    }


def executeWorkspaceAgentTool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """canonical Ask Workbench MCP 도구 실행 결과를 정형 dict 로 반환한다.

    Args:
        name: MCP tool name.
        args: JSON-serializable tool arguments.

    Returns:
        dict[str, Any]: MCP SDK 가 structuredContent 로 직렬화할 payload.

    Example:
        `result = executeWorkspaceAgentTool("RunPython", {"code": "emit_result(values={'x': 1})"})`

    Raises:
        RuntimeError: 하위 tool 실행 중 예외가 전파될 때.
    """
    if not isMcpAdvertisedTool(name):
        return boundMcpPayload(
            {
                "ok": False,
                "summary": f"MCP tools/list 에 advertise 되지 않은 도구는 실행할 수 없습니다: {name}",
                "refs": [],
                "data": {"advertisedTools": list(mcpAdvertisedToolNames())},
                "error": "tool_not_advertised",
            }
        )
    return boundMcpPayload(executeAskWorkbenchTool(name, args))


# DartLab 은 모델 loop 를 소유하지 않고 설치형 CLI 에 중개한다. 그래서 payload 예산의
# 기준은 우리가 감당할 수 있는 크기가 아니라 *소비하는 CLI 가 받아 주는* 크기다.
# 실측(2026-08-05 brokerReach): dataHub.catalog 결과 175,841 byte 를 그대로 내보내자
# CLI 가 tool result 를 통째로 거부하고 "exceeds maximum allowed tokens" 안내문으로
# 갈아치웠다. 본문뿐 아니라 refs 까지 사라져 그 턴은 근거 0 건으로 끝났다. 우리 예산이
# 소비자 상한보다 크면 초과분이 잘리는 게 아니라 결과 전체가 폐기된다.
# 예산은 실제로 통과하고 있는 결과의 실측 크기 위에 여유를 두고 잡았다. 같은 배터리에서
# 가장 큰 성공 결과가 Company.panel 31,285 byte(ref 45 개) 였으므로 64 KiB 는 2 배 여유다.
_MCP_DEFAULT_MAX_PAYLOAD_BYTES = 64 * 1024
_MCP_MIN_MAX_PAYLOAD_BYTES = 4 * 1024
# 예산 초과로 본문을 줄일 때도 남겨 두는 ref 신원의 최대 개수다.
_MCP_MAX_PRESERVED_REFS = 200
_MCP_CONTRACT_KEYS = (
    "ok",
    "summary",
    "error",
    "status",
    "quality",
    "gaps",
    "coverage",
    "universeCoverage",
    "provenance",
    "lineageRefs",
    "sourceRefs",
    "evidenceRefs",
    "executionReceipts",
    "asOf",
    "latestAsOf",
    "requestedAsOf",
    "dataAsOf",
    "period",
    "knowledgeBoundary",
    "snapshotId",
    "dataSnapshotId",
    "contractHash",
    "dataContractHash",
    "continuation",
    "nodes",
    "refs",
    "data",
)


def mcpMaxPayloadBytes() -> int:
    """MCP structured payload 상한을 반환한다."""
    import os

    raw = os.environ.get("DARTLAB_MCP_MAX_PAYLOAD_BYTES")
    try:
        return max(_MCP_MIN_MAX_PAYLOAD_BYTES, int(raw)) if raw else _MCP_DEFAULT_MAX_PAYLOAD_BYTES
    except (TypeError, ValueError):
        return _MCP_DEFAULT_MAX_PAYLOAD_BYTES


def _mcpPayloadSize(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8"))


def _compactMcpValue(value: Any, *, limit: int, maxString: int, maxDepth: int, depth: int = 0) -> Any:
    """계약 키를 먼저 보존하며 JSON payload를 결정론적으로 축약한다."""
    if depth >= maxDepth:
        return {"previewTruncated": True, "reason": "mcp_max_depth"}
    if isinstance(value, str):
        if len(value) <= maxString:
            return value
        return value[: max(0, maxString - 3)].rstrip() + "..."
    if isinstance(value, dict):
        priority = [key for key in _MCP_CONTRACT_KEYS if key in value]
        remaining = [key for key in value if key not in priority]
        selected = [*priority, *remaining[:limit]]
        return {
            str(key): _compactMcpValue(value[key], limit=limit, maxString=maxString, maxDepth=maxDepth, depth=depth + 1)
            for key in selected
        }
    if isinstance(value, list | tuple):
        return [
            _compactMcpValue(item, limit=limit, maxString=maxString, maxDepth=maxDepth, depth=depth + 1)
            for item in value[:limit]
        ]
    return value


def _refIdentities(refs: Any) -> list[dict[str, Any]]:
    """본문을 줄여야 할 때도 인용 가능한 ref 신원만은 남긴다.

    ref 는 이 제품의 근거 계약이고 신원(id, kind, title, source)은 payload 본문보다
    두 자릿수 작다. 예산이 모자랄 때 먼저 버릴 것은 ref 가 아니라 ref 안의 본문이다.
    """
    if not isinstance(refs, list):
        return []
    identities: list[dict[str, Any]] = []
    for ref in refs[:_MCP_MAX_PRESERVED_REFS]:
        if not isinstance(ref, dict) or not ref.get("id"):
            continue
        identities.append(
            {
                "id": str(ref["id"])[:200],
                "kind": str(ref.get("kind") or "evidenceRef")[:60],
                "title": str(ref.get("title") or ref["id"])[:200],
                "source": str(ref.get("source") or "")[:200],
                "payloadTruncated": True,
            }
        )
    return identities


def _budgetReceipt(*, maxPayloadBytes: int, originalBytes: int, reason: str) -> dict[str, Any]:
    """예산 초과로 무엇을 줄였는지 공개하는 영수증을 만든다."""
    return {
        "maxBytes": maxPayloadBytes,
        "originalBytes": originalBytes,
        "truncated": True,
        "gap": {"id": "mcp.payload.truncated", "status": "partial", "reason": reason},
    }


def boundMcpPayload(payload: dict[str, Any], *, maxBytes: int | None = None) -> dict[str, Any]:
    """MCP payload를 명시적 예산 안에 두고 status/gap/provenance/time 계약을 보존한다.

    작은 결과는 byte-for-byte 동일한 dict를 반환한다. 상한을 넘을 때만 collection/string
    preview를 단계적으로 줄이고 ``payloadBudget.gap`` 으로 손실을 공개한다.

    축약 순서는 본문 먼저, 근거 나중이다. 옛 경로는 ``refs`` 도 다른 list 와 똑같이
    잘라서 마지막 봉투에서는 아예 빈 목록으로 만들었다. 그러면 성공한 엔진 호출이
    사용자가 확인할 근거를 하나도 남기지 못한다. 그래서 본문을 최대로 줄여도 모자랄
    때만 ref 를 신원 투영으로 낮추고, 목록 자체는 끝까지 비우지 않는다.
    """
    requestedLimit = mcpMaxPayloadBytes() if maxBytes is None else int(maxBytes)
    maxPayloadBytes = max(_MCP_MIN_MAX_PAYLOAD_BYTES, requestedLimit)
    originalBytes = _mcpPayloadSize(payload)
    if originalBytes <= maxPayloadBytes:
        return payload

    originalRefs = payload.get("refs") if isinstance(payload.get("refs"), list) else []
    levels = ((32, 4000, 12), (12, 1200, 10), (4, 400, 8), (1, 160, 6))
    reasons = {
        "keep": "structuredContent 본문이 MCP payload 예산을 초과해 preview로 축약되었습니다. 근거 ref는 보존되었습니다.",
        "identity": "structuredContent가 MCP payload 예산을 초과해 본문과 근거 payload를 축약했습니다. 인용용 ref 신원은 보존되었습니다.",
    }
    for refMode in ("keep", "identity"):
        boundedRefs = list(originalRefs) if refMode == "keep" else _refIdentities(originalRefs)
        for itemLimit, maxString, maxDepth in levels:
            candidate = _compactMcpValue(payload, limit=itemLimit, maxString=maxString, maxDepth=maxDepth)
            if not isinstance(candidate, dict):
                candidate = {"data": candidate}
            candidate["refs"] = boundedRefs
            candidate["payloadBudget"] = _budgetReceipt(
                maxPayloadBytes=maxPayloadBytes,
                originalBytes=originalBytes,
                reason=reasons[refMode],
            )
            returnedBytes = _mcpPayloadSize(candidate)
            candidate["payloadBudget"]["returnedBytes"] = returnedBytes
            if returnedBytes <= maxPayloadBytes:
                return candidate

    # 최소 상한(4 KiB)에서도 항상 직렬화 가능한 마지막 봉투를 보장한다. 본문은 비우되
    # 근거 신원은 예산이 허락하는 만큼 남겨 답변이 인용할 것을 잃지 않게 한다.
    fallback: dict[str, Any] = {
        "ok": bool(payload.get("ok", False)),
        "summary": _compactMcpValue(str(payload.get("summary") or ""), limit=1, maxString=160, maxDepth=2),
        "refs": [],
        "data": {},
        "error": payload.get("error"),
        "payloadBudget": _budgetReceipt(
            maxPayloadBytes=maxPayloadBytes,
            originalBytes=originalBytes,
            reason="structuredContent가 MCP payload 예산을 초과해 본문 없이 근거 신원만 반환되었습니다.",
        ),
    }
    identities = _refIdentities(originalRefs)
    while identities and _mcpPayloadSize({**fallback, "refs": identities}) > maxPayloadBytes:
        identities = identities[: len(identities) // 2]
    fallback["refs"] = identities
    fallback["payloadBudget"]["returnedBytes"] = _mcpPayloadSize(fallback)
    return fallback


def recipeSkillsForPrompts() -> list[Any]:
    """MCP prompts/list 에 노출할 Skill OS recipe skill 을 반환한다.

    Returns:
        list[Any]: `kind == "recipe"` 인 builtin skill spec 목록.

    Example:
        `prompts = recipeSkillsForPrompts()`

    Raises:
        RuntimeError: Skill OS index 로딩이 실패할 때.
    """
    from dartlab.skills import listSkills

    return [s for s in listSkills(includeUser=False) if s.kind == "recipe"]


def advertisedTools() -> list[dict[str, Any]]:
    """MCP tools/list 에 노출할 tool schema 와 annotations 를 반환한다.

    Returns:
        list[dict[str, Any]]: name, description, params, required, annotations mapping.

    Example:
        `names = [tool["name"] for tool in advertisedTools()]`

    Raises:
        KeyError: registry spec 에 필수 필드가 없을 때.
    """
    tools: list[dict[str, Any]] = []
    for spec in askWorkbenchToolSpecs():
        schema = spec.get("inputSchema") or {}
        annotations: dict[str, bool] = {}
        for key in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
            value = spec.get(key)
            if value is not None:
                annotations[key] = bool(value)
        tools.append(
            {
                "name": spec["name"],
                "description": spec["description"],
                "params": schema.get("properties") or {},
                "required": schema.get("required") or [],
                "annotations": annotations,
            }
        )
    return tools


def resourcePayload(uriStr: str) -> tuple[str, str]:
    """dartlab resource URI 를 MCP resource payload 로 변환한다.

    Args:
        uriStr: `dartlab://...` resource URI.

    Returns:
        tuple[str, str]: content text 와 MIME type.

    Example:
        `content, mimeType = resourcePayload("dartlab://info")`

    Raises:
        RuntimeError: skill 또는 run scratchpad resource 읽기가 실패할 때.
    """
    if uriStr == "dartlab://info":
        import dartlab

        return (
            json.dumps(
                {
                    "version": getattr(dartlab, "__version__", "unknown"),
                    "tools": len(advertisedTools()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            "application/json",
        )
    if uriStr in {"dartlab://agent-runtime", "dartlab://ask-workbench"}:
        return (
            json.dumps(executeAskWorkbenchTool("ask_kernel_status", {}), ensure_ascii=False, indent=2),
            "application/json",
        )
    if uriStr == "dartlab://datasets":
        return (
            json.dumps(
                {"datasets": [], "note": "dataset refs are produced by EngineCall/RunPython"},
                ensure_ascii=False,
                indent=2,
            ),
            "application/json",
        )
    if uriStr == "dartlab://reference":
        return (
            json.dumps(
                executeAskWorkbenchTool("search_reference", {"query": "DartLab Agent Runtime", "limit": 5}),
                ensure_ascii=False,
                indent=2,
            ),
            "application/json",
        )
    if uriStr == "dartlab://skills":
        return (
            json.dumps(
                executeAskWorkbenchTool("listDartlabSkills", {"includeUser": False}),
                ensure_ascii=False,
                indent=2,
            ),
            "application/json",
        )
    if uriStr.startswith("dartlab://skills/"):
        skillId = uriStr.replace("dartlab://skills/", "", 1)
        from dartlab.skills import describeSkill

        return (
            json.dumps(describeSkill(skillId, includeUser=False), ensure_ascii=False, indent=2),
            "application/json",
        )
    if uriStr.startswith("dartlab://runs/") and uriStr.endswith("/scratchpad"):
        runId = uriStr.removeprefix("dartlab://runs/").removesuffix("/scratchpad")
        path = Path.home() / ".dartlab" / "ask_runs" / f"{runId}.jsonl"
        if not path.exists():
            return ("", "application/jsonl")
        return (path.read_text(encoding="utf-8"), "application/jsonl")
    return ("Unknown resource", "text/plain")
