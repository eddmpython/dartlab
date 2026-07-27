"""MCP protocol surface shared by stdio, SSE, and tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MCP_INSTRUCTIONS = """\
DartLab MCP의 기본 표면은 ask가 실행하는 Ask Workbench와 그 아래 데이터·분석 작업대 도구다
(advertise 되는 전체 도구 목록·갯수는 tools/list 가 정본 — 본 문서는 핵심만 안내). 목적은 LLM이 DartLab을
프롬프트 지식으로 외우게 하는 것이 아니라, 질문마다 먼저 skill을 고르고, capability docstring에서 호출 가능한 API를
확인한 뒤 RunPython으로 실행하고 ref 검증 후 답하게 하는 것이다.

## 핵심 데이터 작업대 도구 (advertised 전체는 tools/list 참조)
- ask: DartLab 공식 답변 진입점. 기본은 chat-native 자율 도구 호출이고, mode="analyze" 를 명시하면 작업대 경로로 간다.
- ReadSkill: Skill OS 검색 + frontmatter (whenToUse, capabilityRefs, requiredEvidence) + 본문.
- ReadCapability: dartlab 공개 API/docstring 검색.
- EngineCall: 단일 capability 1 회 호출 (Company.panel, scan, macro 등). JSON `{apiRef, args}` 양식.
  allowlist 된 capabilities 만 실행되어 RunPython 보다 안전·간단. 결과는 자동 tableRef/valueRef
  발급. 단일 호출 시 본 도구 우선, RunPython 은 다단 가공·계산만.
- RunPython: dartlab + Polars 코드 실행, ref 발급. 비교·집계·시계열 가공 같은 *다단 계산* 또는
  EngineCall 카탈로그에 없는 호출에만 사용.
- WebSearch: 외부 최신 정보 → webRef.
- SaveArtifact: 큰 표·차트 별도 파일 저장 → artifactRef.
- CompileVisual: 차트 spec codegen → visualRef (인라인 렌더).

## 전용 분석 도구 (단일 호출이면 EngineCall 보다 직접적 — tools/list 가 전체 정본)
- PeerCompareN: 동종 N 사(2~12) 재무·밸류 비교 표.
- DCFValuation / SensitivityAnalysis: 현금흐름 가치평가 + 민감도 격자.
- ScenarioOverlay / ScenarioCompareN: 시나리오 리플레이·비교.
- CreditScorecard: 신용 스코어카드. RegressionForecast: 회귀 예측.
- CompileFinancialDashboard: 재무 대시보드 컴파일. SearchPastSessions: 과거 세션 검색.

## 기본 흐름
1. **첫 진입 권장** — 작업 모호하거나 처음 만나는 도메인이면 `ReadSkill(query="start.dartlabSkillOs")` 먼저 호출.
   분류 노드가 5 카테고리 (start/runtime/operation/engines/recipes) 와 작업 결을 먼저 매핑한다.
2. ask로 전체 답변 루프 실행 (단순 질문은 이걸로 끝).
3. 작업대 직접 사용 시: ReadSkill 로 절차 → ReadCapability 로 API → RunPython 으로 실행 → 답변 + ref.
4. 데이터셋 스키마·기간·행 수·최신 기준시점이 필요하면 RunPython 안에서 dartlab.* 직접 호출로 확인한다.
5. 후보·상위·랭킹 답변은 bullet 나열로 끝내지 않고 입력/유니버스, 필터, 계산식/지표, 결과와 evidence table을 함께 낸다.

## 0.10 BREAKING — 옛 33 generated 도구 제거
companyStory / companyAnalysis / companyValuation / companyForecast / companyShow / companyTopics /
companyDiff / companyGovernance / companyAudit / companyProfile / companyCredit / companyGather /
companyQuant / companyFilings / marketScan / macroAnalysis / gatherData / quantAnalysis /
topdownScreen / dartlabSearch / dartlabListing / pastInsight / sectorInsights / industryMap /
capabilities / listDartlabApi / searchDartlabApi / verifyDartlabApi / 그리고 Analysis Graph 도구
(contextForQuestion / queryAnalysisGraph / impactForGraphNode / explainDartlabTool /
planDartlabQuestion / validateDartlabPlan / listDartlabProcesses) 는 모두 EngineCall 또는
RunPython 안에서 직접 호출하는 패턴으로 통합되었다. DARTLAB_MCP_COMPAT 환경변수도 폐기.
마이그레이션 예 — 단일 capability 호출은 EngineCall 우선:

    # 옛: companyAnalysis(stockCode="005930", axis="수익성")
    EngineCall({"apiRef": "Company.analysis", "args": {"stockCode": "005930", "axis": "수익성"}})

    # 다단 가공 (비교·계산·시계열) 만 RunPython
    RunPython(code='''
    a = dartlab.Company("005930").panel("IS")
    b = dartlab.Company("000660").panel("IS")
    print(a.join(b, on="period"))
    ''')

## 경계
- Company, gather, scan, macro, analysis, quant, viz는 generated MCP tool로 직접 우회하지 않는다.
  RunPython 안에서 사용하는 DartLab 라이브러리다.
- Skills는 MCP 전용 규칙이 아니라 dartlab.skills 공용 runtime을 그대로 노출한다.
- 삭제된 운영 문서 경로를 공식 진입점으로 안내하지 않는다. 모든 절차는 Skill OS에서 찾는다.
- 도구로 확인되지 않은 수치, 날짜, 실행 성공 여부를 단정하지 않는다.
- 후보·상위·랭킹 결과를 표 없이 종목명과 퍼센트만 나열하지 않는다.
"""


def mcpAdvertisedToolNames() -> tuple[str, ...]:
    """MCP tools/list 에 advertise 할 도구 이름 SSOT — registry 변경 자동 추종.

    마스터 플랜 v2 트랙 7 PR-M1 — 옛 정적 12-tuple 상수(LookAheadGuard / RequestUserInput stub 포함)는
    ``CANONICAL_V2`` (21 종 정제 production-grade) 와 deviation 발생해 **폐기**(debt-honesty P2-6 —
    ask_kernel_status leak 경로 제거). 본 함수가 ``"ask" + CANONICAL_V2`` 를 SSOT 로 노출 → 신규 도구
    추가 시 advertise 도 자동 sync.

    Returns:
        tuple[str, ...]: ``("ask",) + CANONICAL_V2`` 합 (= 22 종).

    Example:
        ``names = mcpAdvertisedToolNames()``  # → ("ask", "ReadSkill", ..., "SearchPastSessions")
    """
    from dartlab.ai.tools.registry import CANONICAL_V2

    return ("ask", *CANONICAL_V2)


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
    specs["ask"] = {
        "name": "ask",
        "description": "DartLab 공식 AI 답변 진입점. Skill OS, generated spec, tools, ref 검증 루프를 통해 답변한다.",
        "inputSchema": {
            "type": "object",
            "properties": {"question": {"type": "string"}, "stockCode": {"type": "string"}},
            "required": ["question"],
        },
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
    # PR-M1 — mcpAdvertisedToolNames SSOT 추종. registry 에 누락된 이름은 silently skip.
    advertised = mcpAdvertisedToolNames()
    return [specs[name] for name in advertised if name in specs]


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

    if name == "ask":
        from dartlab.ai.kernel import AskFailedError, ask

        question = str(args.get("question") or "")
        kwargs = {key: value for key, value in args.items() if key != "question"}
        # ok 를 리터럴로 박아 두면 완전 실패한 실행도 성공으로 나간다. 대표 진입점이라
        # 클라이언트는 이 한 값을 보고 답의 유무를 판단한다.
        try:
            answer = ask(question, stream=False, **kwargs)
        except AskFailedError as exc:
            return {"ok": False, "answer": "", "error": str(exc)}
        return {"ok": True, "answer": answer}
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
        # tools = advertised SSOT(mcpAdvertisedToolNames) — 옛 12-tuple leak(LookAheadGuard·
        # RequestUserInput) 제거. 'passes'(5-pass GRAPH_NODES) 노출도 제거 — chat-native 정체성상
        # 고정 노드 그래프를 외부 resource 로 광고하지 않는다 (debt-honesty P2-6 / SD-2).
        return {
            "name": "Ask Workbench",
            "entry": "ask",
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
    return executeAskWorkbenchTool(name, args)


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
    if uriStr == "dartlab://ask-workbench":
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
                executeAskWorkbenchTool("search_reference", {"query": "DartLab Ask Workbench", "limit": 5}),
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
