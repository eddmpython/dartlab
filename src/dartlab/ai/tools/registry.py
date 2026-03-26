"""DartLab 분석 도구 레지스트리 — OpenAI function calling 형식.

LLM 에이전트가 사용할 수 있는 도구를 등록·관리한다.
Company 인스턴스에 바인딩된 도구를 생성하여 tool calling에 사용.
"""

from __future__ import annotations

from typing import Any, Callable

from dartlab.core.capabilities import (
    CapabilityChannel,
    CapabilityKind,
    clear_capability_registry,
    register_tool_capability,
)

# ── 공개 헬퍼: _helpers.py에서 가져오되, 기존 import 경로 호환 ──
from ._helpers import (
    get_coding_runtime_policy as _get_coding_runtime_policy,
)
from .runtime import (
    ToolRuntime,
    create_tool_runtime,
    get_default_tool_runtime,
    set_default_tool_runtime,
)


def get_coding_runtime_policy() -> tuple[bool, str]:
    """현재 세션의 coding runtime 노출 정책을 반환한다."""
    return _get_coding_runtime_policy()


def register_tool(
    name: str,
    func: Callable[..., str],
    description: str,
    parameters: dict,
    *,
    label: str | None = None,
    kind: str = CapabilityKind.WORKFLOW,
    channels: tuple[str, ...] = (CapabilityChannel.CHAT, CapabilityChannel.MCP),
    requires_company: bool = False,
    result_kind: str = "text",
    stability: str = "experimental",
    ai_hint: str = "",
    questionTypes: tuple[str, ...] = (),
    category: str = "general",
    priority: int = 50,
    dependsOn: tuple[str, ...] = (),
) -> None:
    """도구 등록."""
    get_default_tool_runtime().register_tool(name, func, description, parameters)
    register_tool_capability(
        name,
        description,
        parameters,
        label=label,
        kind=kind,
        channels=channels,
        requires_company=requires_company,
        result_kind=result_kind,
        stability=stability,
        ai_hint=ai_hint,
        questionTypes=questionTypes,
        category=category,
        priority=priority,
        dependsOn=dependsOn,
    )


def get_tool_schemas() -> list[dict]:
    """등록된 도구의 OpenAI function calling 스키마 목록."""
    return get_default_tool_runtime().get_tool_schemas()


def execute_tool(name: str, arguments: dict) -> str:
    """도구 실행. 결과는 문자열(마크다운)로 반환."""
    return get_default_tool_runtime().execute_tool(name, arguments)


def clear_registry() -> None:
    """등록된 모든 도구 제거 (테스트용)."""
    get_default_tool_runtime().clear()
    clear_capability_registry()


def build_tool_runtime(
    company: Any | None = None,
    *,
    name: str = "session",
    useSuperTools: bool = False,
) -> ToolRuntime:
    """Build an isolated tool runtime populated with current default tools."""
    runtime = create_tool_runtime(name=name)
    register_defaults(company, runtime=runtime, useSuperTools=useSuperTools)

    # 내장 플러그인 도구 등록 (import 시 @tool 데코레이터가 레지스트리에 추가)
    import dartlab.ai.tools.plugin_creator  # noqa: F401

    # 플러그인 도구 자동 주입
    from .plugin import get_plugin_registry, inject_plugins_into_runtime

    inject_plugins_into_runtime(get_plugin_registry(), runtime)

    return runtime


def register_defaults(
    company: Any | None = None,
    *,
    runtime: ToolRuntime | None = None,
    useSuperTools: bool = False,
) -> ToolRuntime:
    """전역 기능 + Company 바인딩 분석 도구 등록.

    useSuperTools=True이면 101개 도구 대신 7개 Super Tool만 등록.
    """
    if runtime is not None:
        previous_runtime = get_default_tool_runtime()
        set_default_tool_runtime(runtime)
        try:
            return register_defaults(company, useSuperTools=useSuperTools)
        finally:
            set_default_tool_runtime(previous_runtime)

    clear_registry()

    if useSuperTools:
        from .superTools import registerSuperTools

        registerSuperTools(company, register_tool)
    else:
        from .defaults import register_all_defaults

        register_all_defaults(company, register_tool)

    # CapabilitySpec 메타데이터에서 QUESTION_TYPE_MAP 자동 갱신
    try:
        from dartlab.ai.conversation.templates.analysis_rules import refreshQuestionTypeMap

        refreshQuestionTypeMap()
    except ImportError:
        pass

    return get_default_tool_runtime()
