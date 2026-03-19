"""외부 도구 플러그인 시스템 — @tool 데코레이터.

사용법::

        from dartlab.engines.ai import tool

        @tool(category="custom")
        def my_analysis(metric: str) -> str:
            \"""내 분석.\"""
            return f"{metric} 분석 완료"

        # requires_company=True로 등록하면 Company 인스턴스 자동 주입
        @tool(requires_company=True)
        def company_metric(company, metric: str) -> str:
            \"""회사별 분석.\"""
            return f"{company.corpName}: {metric}"
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, get_type_hints

PYTHON_TO_JSON_TYPE: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


@dataclass
class ToolDef:
    """플러그인 도구 정의."""

    name: str
    func: Callable[..., str]
    description: str
    category: str
    requires_company: bool
    parameters: dict
    tags: list[str] = field(default_factory=list)


class ToolPluginRegistry:
    """플러그인 도구 레지스트리."""

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool_def: ToolDef) -> None:
        self._tools[tool_def.name] = tool_def

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get_schemas(self) -> list[dict]:
        """OpenAI function calling 스키마 목록."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict, company: Any = None) -> str:
        """도구 실행."""
        tool_def = self._tools.get(name)
        if not tool_def:
            return f"오류: 플러그인 '{name}' 도구를 찾을 수 없습니다."
        if tool_def.requires_company:
            return tool_def.func(company, **arguments)
        return tool_def.func(**arguments)

    @property
    def size(self) -> int:
        return len(self._tools)

    def list_names(self) -> list[str]:
        return list(self._tools.keys())


# 글로벌 레지스트리
_registry = ToolPluginRegistry()


def get_plugin_registry() -> ToolPluginRegistry:
    """글로벌 플러그인 레지스트리 반환."""
    return _registry


def _build_parameters_schema(func: Callable) -> tuple[dict, list[str]]:
    """함수 시그니처에서 OpenAI parameters 스키마를 자동 생성."""
    hints = get_type_hints(func)
    sig = inspect.signature(func)

    properties: dict[str, dict] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("company", "self", "cls"):
            continue

        param_type = hints.get(param_name, str)
        json_type = PYTHON_TO_JSON_TYPE.get(param_type, "string")
        prop: dict[str, Any] = {"type": json_type}

        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            prop["default"] = param.default

        properties[param_name] = prop

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema, required


def tool(
    name: str | None = None,
    category: str = "custom",
    requires_company: bool = False,
    tags: list[str] | None = None,
):
    """@tool 데코레이터 — 외부 함수를 AI 도구로 등록.

    Args:
            name: 도구명 (None이면 함수명 사용)
            category: 도구 카테고리
            requires_company: True면 첫 인자로 Company 인스턴스 주입
            tags: 분류 태그
    """

    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        description = (func.__doc__ or "").strip().split("\n")[0]
        parameters, _ = _build_parameters_schema(func)

        tool_def = ToolDef(
            name=tool_name,
            func=func,
            description=description,
            category=category,
            requires_company=requires_company,
            parameters=parameters,
            tags=tags or [],
        )
        _registry.register(tool_def)
        func._tool_def = tool_def  # type: ignore[attr-defined]
        return func

    return decorator


def inject_plugins_into_runtime(registry: ToolPluginRegistry, runtime: Any) -> None:
    """플러그인 레지스트리의 도구를 ToolRuntime에 주입."""
    for tool_def in registry._tools.values():
        if runtime.has_tool(tool_def.name):
            continue

        if tool_def.requires_company:

            def _make_wrapper(td: ToolDef) -> Callable[..., str]:
                def wrapper(**kwargs: Any) -> str:
                    return td.func(None, **kwargs)

                return wrapper

            func = _make_wrapper(tool_def)
        else:
            func = tool_def.func

        runtime.register_tool(
            tool_def.name,
            func,
            tool_def.description,
            tool_def.parameters,
        )
