"""LLM tool 호출의 세션별 실행 권한 경계."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def executeAllowedTool(
    executor: Callable[[str, dict[str, Any]], dict[str, Any]],
    name: str,
    args: dict[str, Any],
    allowedNames: Iterable[str],
) -> dict[str, Any]:
    """현재 turn에 광고된 도구만 실행하고 나머지는 구조화 오류로 거절한다."""

    allowed = frozenset(item for item in allowedNames if isinstance(item, str) and item)
    if not isinstance(name, str) or name not in allowed:
        return {
            "ok": False,
            "summary": f"현재 세션에서 허용되지 않은 도구 호출: {name or '(empty)'}",
            "refs": [],
            "data": None,
            "error": "tool_not_allowed",
        }
    return executor(name, args)


__all__ = ["executeAllowedTool"]
