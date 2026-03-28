"""Reusable tool runtime for provider-agnostic tool execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

_TOOL_RUNTIME_ERRORS = (
    AttributeError,
    FileNotFoundError,
    ImportError,
    KeyError,
    OSError,
    PermissionError,
    RuntimeError,
    TimeoutError,
    TypeError,
    ValueError,
)


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
        """도구를 function calling 스키마와 함께 등록한다."""
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
        """등록된 모든 도구의 OpenAI function calling 스키마를 반환한다."""
        return [tool.schema for tool in self._registry.values()]

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """이름과 인자로 도구를 실행한다."""
        tool = self._registry.get(name)
        if tool is None:
            return f"오류: '{name}' 도구를 찾을 수 없습니다."
        try:
            return tool.function(**arguments)
        except _TOOL_RUNTIME_ERRORS as e:
            return f"도구 실행 오류 ({name}): {e}"

    def clear(self) -> None:
        """등록된 모든 도구를 제거한다."""
        self._registry.clear()

    def list_tool_names(self) -> list[str]:
        """등록된 도구 이름 목록을 반환한다."""
        return list(self._registry.keys())

    def has_tool(self, name: str) -> bool:
        """해당 이름의 도구가 등록되어 있는지 확인한다."""
        return name in self._registry

    @property
    def size(self) -> int:
        """등록된 도구 수를 반환한다."""
        return len(self._registry)


_DEFAULT_TOOL_RUNTIME = ToolRuntime()


def create_tool_runtime(name: str = "runtime") -> ToolRuntime:
    """새 ToolRuntime 인스턴스를 생성한다."""
    return ToolRuntime(name=name)


def get_default_tool_runtime() -> ToolRuntime:
    """전역 기본 ToolRuntime을 반환한다."""
    return _DEFAULT_TOOL_RUNTIME


def set_default_tool_runtime(runtime: ToolRuntime) -> None:
    """전역 기본 ToolRuntime을 교체한다."""
    global _DEFAULT_TOOL_RUNTIME
    _DEFAULT_TOOL_RUNTIME = runtime
