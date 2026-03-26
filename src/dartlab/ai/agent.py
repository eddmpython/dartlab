"""호환 shim — 실제 구현은 runtime/agent.py로 이동됨.

기존 import 경로를 유지하기 위한 re-export.
"""

from dartlab.ai.runtime.agent import (  # noqa: F401
    AGENT_SYSTEM_ADDITION,
    PLANNING_PROMPT,
    _reflect_on_answer,
    agent_loop,
    agent_loop_planning,
    agent_loop_stream,
    build_agent_system_addition,
)
from dartlab.ai.tools.selector import selectTools  # noqa: F401

# 하위호환: _select_tools → selectTools 래퍼
_select_tools = selectTools

__all__ = [
    "AGENT_SYSTEM_ADDITION",
    "PLANNING_PROMPT",
    "_reflect_on_answer",
    "_select_tools",
    "agent_loop",
    "agent_loop_planning",
    "agent_loop_stream",
    "build_agent_system_addition",
    "selectTools",
]
