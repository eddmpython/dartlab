"""Reusable tool runtime for provider-agnostic tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class RegisteredTool:
    """In-memory tool definition and its function-calling schema."""

    name: str
    function: Callable[..., str]
    schema: dict[str, Any]


class ToolRuntime:
    """Simple tool registry/executor that can be reused across providers."""

    def __init__(self, name: str = "default"):
        self.name = name
        self._registry: dict[str, RegisteredTool] = {}

    def register_tool(
        self,
        name: str,
        func: Callable[..., str],
        description: str,
        parameters: dict[str, Any],
    ) -> None:
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._registry[name] = RegisteredTool(
            name=name,
            function=func,
            schema=schema,
        )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.schema for tool in self._registry.values()]

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._registry.get(name)
        if tool is None:
            return f"오류: '{name}' 도구를 찾을 수 없습니다."
        try:
            return tool.function(**arguments)
        except Exception as e:
            return f"도구 실행 오류 ({name}): {e}"

    def clear(self) -> None:
        self._registry.clear()

    def list_tool_names(self) -> list[str]:
        return list(self._registry.keys())

    def has_tool(self, name: str) -> bool:
        return name in self._registry

    @property
    def size(self) -> int:
        return len(self._registry)


_DEFAULT_TOOL_RUNTIME = ToolRuntime()


def create_tool_runtime(name: str = "runtime") -> ToolRuntime:
    return ToolRuntime(name=name)


def get_default_tool_runtime() -> ToolRuntime:
    return _DEFAULT_TOOL_RUNTIME


def set_default_tool_runtime(runtime: ToolRuntime) -> None:
    global _DEFAULT_TOOL_RUNTIME
    _DEFAULT_TOOL_RUNTIME = runtime
