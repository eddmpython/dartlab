"""MCP Server assembly for DartLab."""

from __future__ import annotations

import logging
import sys
from typing import Any, cast

from dartlab.mcp.protocol import (
    MCP_INSTRUCTIONS,
    advertisedTools,
    boundMcpPayload,
    executeWorkspaceAgentTool,
    isMcpAdvertisedTool,
    recipeSkillsForPrompts,
    resourcePayload,
)

mcpLog = logging.getLogger("dartlab.mcp")
mcpLog.propagate = False
if not any(isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stderr for h in mcpLog.handlers):
    mcpLog.addHandler(logging.StreamHandler(sys.stderr))
mcpLog.setLevel(logging.INFO)


def progressThresholdSec() -> float:
    """progress notification 시작 임계값을 환경변수에서 읽는다.

    Returns:
        float: `DARTLAB_PROGRESS_THRESHOLD_SEC` 또는 기본값 5.0.

    Example:
        `threshold = progressThresholdSec()`

    Raises:
        RuntimeError: 환경변수 접근 자체가 실패할 때.
    """
    import os

    raw = os.environ.get("DARTLAB_PROGRESS_THRESHOLD_SEC")
    try:
        return float(raw) if raw else 5.0
    except (TypeError, ValueError):
        return 5.0


def progressIntervalSec() -> float:
    """progress notification 반복 간격을 환경변수에서 읽는다.

    Returns:
        float: `DARTLAB_PROGRESS_INTERVAL_SEC` 또는 기본값 1.0.

    Example:
        `interval = progressIntervalSec()`

    Raises:
        RuntimeError: 환경변수 접근 자체가 실패할 때.
    """
    import os

    raw = os.environ.get("DARTLAB_PROGRESS_INTERVAL_SEC")
    try:
        return float(raw) if raw else 1.0
    except (TypeError, ValueError):
        return 1.0


async def handleRequestUserInput(args: dict[str, Any], session: Any) -> dict[str, Any]:
    """RequestUserInput 을 MCP elicit_form 으로 dispatch 한다.

    Args:
        args: message 와 fields 를 담은 tool arguments.
        session: MCP server request session.

    Returns:
        dict[str, Any]: accept/decline/cancel 또는 fallback 결과.

    Example:
        `result = await handleRequestUserInput({"message": "회사 선택"}, session)`

    Raises:
        RuntimeError: elicit schema 생성이 실패할 때.
    """
    from dartlab.ai.tools.requestUserInput import buildElicitSchema

    message = str(args.get("message") or "")
    fields = args.get("fields") or []
    if not isinstance(fields, list):
        fields = []
    schema = buildElicitSchema(fields)

    try:
        result = await session.elicit_form(message=message, requestedSchema=schema)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "summary": f"RequestUserInput — 클라이언트 elicit 미지원 또는 실패: {type(exc).__name__}",
            "data": {"message": message, "requestedSchema": schema, "fallback": True},
            "error": "elicit_unsupported_or_failed",
        }

    action = getattr(result, "action", "decline")
    content = getattr(result, "content", None)
    return {
        "ok": action == "accept",
        "summary": f"elicit action={action}",
        "data": {
            "action": action,
            "content": content if isinstance(content, dict) else None,
            "message": message,
            "requestedSchema": schema,
        },
        "error": None if action == "accept" else f"elicit_{action}",
    }


async def runWithProgress(
    name: str,
    arguments: dict[str, Any],
    progressToken: Any,
    session: Any,
) -> dict[str, Any]:
    """동기 tool 실행을 thread 로 옮기고 progress notification 을 보낸다.

    Args:
        name: 실행할 MCP tool name.
        arguments: tool arguments.
        progressToken: MCP `_meta.progressToken`.
        session: MCP server request session.

    Returns:
        dict[str, Any]: tool 실행 structured payload.

    Example:
        `result = await runWithProgress("RunPython", {"code": "..."}, token, session)`

    Raises:
        RuntimeError: tool executor 가 실패할 때.
    """
    import asyncio
    import time

    threshold = progressThresholdSec()
    interval = progressIntervalSec()
    start = time.perf_counter()

    async def emitProgress() -> None:
        """progress notification 을 주기적으로 전송한다.

        Returns:
            None: cancellation 될 때까지 notification 전송을 반복한다.

        Example:
            `task = asyncio.create_task(emitProgress())`

        Raises:
            RuntimeError: sleep 또는 cancellation 처리 자체가 실패할 때.
        """
        while True:
            await asyncio.sleep(interval)
            elapsed = time.perf_counter() - start
            if elapsed < threshold:
                continue
            try:
                await session.send_progress_notification(
                    progress_token=progressToken,
                    progress=elapsed,
                    total=None,
                    message=f"{name} 실행 중 ({elapsed:.0f} s)...",
                )
            except Exception:
                pass

    progressTask = asyncio.create_task(emitProgress())
    try:
        result = await asyncio.to_thread(executeWorkspaceAgentTool, name, arguments)
    finally:
        progressTask.cancel()
        try:
            await progressTask
        except (asyncio.CancelledError, Exception):
            pass
    return result


def createServer():
    """MCP 서버 인스턴스 생성.

    Returns:
        mcp.server.Server: dartlab tools/resources/prompts handler 가 등록된 서버.

    Example:
        `app = createServer()`

    Raises:
        ImportError: MCP SDK 가 설치되어 있지 않을 때.
    """

    def _importMcp():
        from mcp.server import Server
        from mcp.server.lowlevel.helper_types import ReadResourceContents
        from mcp.types import (
            GetPromptResult,
            Prompt,
            PromptArgument,
            PromptMessage,
            Resource,
            TextContent,
            Tool,
            ToolAnnotations,
        )

        return (
            Server,
            ReadResourceContents,
            GetPromptResult,
            Prompt,
            PromptArgument,
            PromptMessage,
            Resource,
            TextContent,
            Tool,
            ToolAnnotations,
        )

    try:
        (
            Server,
            ReadResourceContents,
            GetPromptResult,
            Prompt,
            PromptArgument,
            PromptMessage,
            Resource,
            TextContent,
            Tool,
            ToolAnnotations,
        ) = _importMcp()
    except ImportError:
        # transports.py 와 같은 namespace collision 우회 — standalone mcp SDK 는
        # 'mcp/server/__init__.py' 가 존재. 그게 없는 path 의 mcp 는 collision.
        import os
        import sys

        _badPaths = set()
        for _p in sys.path:
            _cand = os.path.join(_p, "mcp", "__init__.py")
            if not os.path.exists(_cand):
                continue
            _serverInit = os.path.join(_p, "mcp", "server", "__init__.py")
            if not os.path.exists(_serverInit):
                _badPaths.add(os.path.normpath(_p))
        for _k in [k for k in sys.modules if k == "mcp" or k.startswith("mcp.")]:
            del sys.modules[_k]
        sys.path[:] = [p for p in sys.path if os.path.normpath(p) not in _badPaths]
        try:
            (
                Server,
                ReadResourceContents,
                GetPromptResult,
                Prompt,
                PromptArgument,
                PromptMessage,
                Resource,
                TextContent,
                Tool,
                ToolAnnotations,
            ) = _importMcp()
        except ImportError as exc:
            raise ImportError("MCP SDK 필요: pip install --upgrade dartlab") from exc

    app = Server("dartlab", instructions=MCP_INSTRUCTIONS)
    mcpLog.info("MCP 서버 초기화 완료")

    def toAnnotations(specAnnotations: dict[str, bool]) -> Any:
        """dict hint 를 MCP ToolAnnotations 객체로 변환한다.

        Args:
            specAnnotations: readOnly/destructive/idempotent/openWorld hint mapping.

        Returns:
            ToolAnnotations | None: 비어 있으면 None, 값이 있으면 SDK annotation 객체.

        Example:
            `annotations = toAnnotations({"readOnlyHint": True})`

        Raises:
            TypeError: SDK ToolAnnotations 가 전달된 hint 를 수용하지 못할 때.
        """
        if not specAnnotations:
            return None
        return ToolAnnotations(**cast(Any, specAnnotations))

    @app.list_tools()
    async def listTools() -> list[Any]:
        """tools/list 요청에 대해 advertise 된 tool list 를 반환한다.

        Returns:
            list[Tool]: inputSchema 와 ToolAnnotations 를 포함한 MCP 도구 목록.

        Example:
            `tools = await listTools()`

        Raises:
            RuntimeError: 등록된 registry spec 이 MCP Tool 로 변환될 수 없을 때.
        """
        tools: list[Any] = []
        for toolSpec in advertisedTools():
            tools.append(
                Tool(
                    name=toolSpec["name"],
                    description=toolSpec["description"],
                    inputSchema={
                        "type": "object",
                        "properties": toolSpec["params"],
                        "required": toolSpec["required"],
                    },
                    annotations=toAnnotations(toolSpec.get("annotations") or {}),
                )
            )
        return tools

    @app.call_tool()
    async def callTool(name: str, arguments: dict) -> dict[str, Any]:
        """tools/call 요청을 dispatch 하고 structuredContent 로 반환한다.

        Args:
            name: 호출할 MCP 도구 이름.
            arguments: MCP 클라이언트가 전달한 JSON arguments.

        Returns:
            dict[str, Any]: ToolResult 호환 structured payload.

        Example:
            `result = await callTool("ReadSkill", {"query": "MCP"})`

        Raises:
            RuntimeError: request context 가 손상되어 progress/session 처리가 불가능할 때.
        """
        mcpLog.info("call_tool: %s(%s)", name, list(arguments.keys()))

        progressToken = None
        session = None
        try:
            ctx = app.request_context
            meta = getattr(ctx, "meta", None)
            if meta is not None:
                progressToken = getattr(meta, "progressToken", None)
            session = getattr(ctx, "session", None)
        except (LookupError, RuntimeError):
            pass

        if name == "RequestUserInput" and session is not None and isMcpAdvertisedTool(name):
            return boundMcpPayload(await handleRequestUserInput(arguments, session))

        if progressToken is None or session is None:
            return executeWorkspaceAgentTool(name, arguments)

        return await runWithProgress(name, arguments, progressToken, session)

    @app.list_resources()
    async def listResources() -> list[Any]:
        """resources/list 요청에 대해 dartlab resource 목록을 반환한다.

        Returns:
            list[Resource]: info, ask-workbench, datasets, reference, skills resource.

        Example:
            `resources = await listResources()`

        Raises:
            RuntimeError: Resource 객체 생성이 SDK schema 와 맞지 않을 때.
        """
        return [
            Resource(
                uri=cast(Any, "dartlab://info"),
                name="DartLab",
                description="Ask Workbench Kernel 상태와 DartLab 런타임 정보",
                mimeType="application/json",
            ),
            Resource(
                uri=cast(Any, "dartlab://ask-workbench"),
                name="Ask Workbench",
                description="표준 MCP 도구, 런타임 데이터셋, 검산 경계 요약",
                mimeType="application/json",
            ),
            Resource(
                uri=cast(Any, "dartlab://datasets"),
                name="Runtime Dataset Catalog",
                description="접근 가능한 런타임 데이터셋 id, 경로, 최신 관측일 요약",
                mimeType="application/json",
            ),
            Resource(
                uri=cast(Any, "dartlab://reference"),
                name="DartLab Reference",
                description="Ask Workbench 설계와 공개 참조 검색 표면",
                mimeType="application/json",
            ),
            Resource(
                uri=cast(Any, "dartlab://skills"),
                name="DartLab Skills",
                description="DartLab Skill OS 목록. AI, MCP, story, UI, audit가 같은 resolver를 사용",
                mimeType="application/json",
            ),
        ]

    @app.read_resource()
    async def readResource(uri: Any) -> list[Any]:
        """resources/read 요청의 uri 본문을 읽는다.

        Args:
            uri: `dartlab://...` resource URI.

        Returns:
            list[ReadResourceContents]: content 와 mime type 을 담은 단일 항목 list.

        Example:
            `payload = await readResource("dartlab://skills/start.dartlabSkillOs")`

        Raises:
            RuntimeError: resource payload 를 SDK response 로 감쌀 수 없을 때.
        """
        content, mimeType = resourcePayload(str(uri))
        return [ReadResourceContents(content=content, mime_type=mimeType)]

    @app.list_prompts()
    async def listPrompts() -> list[Any]:
        """prompts/list 요청에 대해 recipe skill 기반 prompt 목록을 반환한다.

        Returns:
            list[Prompt]: Skill OS recipe 카테고리에서 파생한 prompt 목록.

        Example:
            `prompts = await listPrompts()`

        Raises:
            RuntimeError: skill frontmatter 가 Prompt schema 로 변환될 수 없을 때.
        """
        prompts: list[Any] = []
        for spec in recipeSkillsForPrompts():
            args = [
                PromptArgument(name=f"input{idx + 1}", description=text, required=False)
                for idx, text in enumerate(spec.inputs or [])
            ]
            prompts.append(
                Prompt(
                    name=spec.id,
                    description=f"{spec.title} — {spec.purpose[:200]}" if spec.purpose else spec.title,
                    arguments=args or None,
                )
            )
        return prompts

    @app.set_logging_level()
    async def setLoggingLevel(level: str) -> None:
        """logging/setLevel 요청으로 dartlab MCP logger 레벨을 조정한다.

        Args:
            level: MCP LoggingLevel 문자열.

        Returns:
            None: logger level 변경만 수행한다.

        Example:
            `await setLoggingLevel("debug")`

        Raises:
            RuntimeError: logger level 변경 중 logging backend 가 실패할 때.
        """
        mapping = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "notice": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
            "alert": logging.CRITICAL,
            "emergency": logging.CRITICAL,
        }
        pyLevel = mapping.get(str(level).lower(), logging.INFO)
        mcpLog.setLevel(pyLevel)
        mcpLog.info("logger level set to %s (Python %d) by client", level, pyLevel)

    @app.get_prompt()
    async def getPrompt(name: str, arguments: dict[str, str] | None = None) -> Any:
        """prompts/get 요청으로 recipe prompt 본문을 반환한다.

        Args:
            name: Skill OS recipe id.
            arguments: prompt 본문 앞에 붙일 사용자 입력 mapping.

        Returns:
            GetPromptResult: user role PromptMessage 를 포함한 MCP prompt 응답.

        Example:
            `prompt = await getPrompt("recipes.meta.report.dailyMorningNote", {"tickers": "005930"})`

        Raises:
            ValueError: name 에 해당하는 prompt skill 이 없을 때.
        """
        from dartlab.skills import getSkill

        try:
            spec = getSkill(name, includeUser=False)
        except KeyError as exc:
            raise ValueError(f"Unknown prompt: {name}") from exc

        body = str(spec.source.get("body") or "")
        prefix = ""
        if arguments:
            lines = "\n".join(f"- {key}: {value}" for key, value in arguments.items())
            prefix = f"## 사용자 입력\n{lines}\n\n---\n\n"
        text = f"# {spec.title}\n\n{spec.purpose}\n\n{prefix}{body}"

        return GetPromptResult(
            description=spec.title,
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=text))],
        )

    return app
