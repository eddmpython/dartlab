"""Super Tool 등록 -- CAPABILITIES-Driven Code Execution.

execute_code 단일 도구가 dartlab 전체 기능을 대체.
LLM이 CAPABILITIES를 참조하여 dartlab Python 코드를 생성 -> 샌드박스 실행.
"""

from __future__ import annotations

from typing import Any, Callable

from .code import registerCodeTool


def registerSuperTools(company: Any | None, registerTool: Callable) -> None:
    """execute_code 도구를 등록한다."""
    registerCodeTool(registerTool, company=company)
