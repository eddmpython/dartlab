"""호환 shim — 실제 구현은 runtime/agent.py로 이동됨."""

from dartlab.ai.runtime.agent import (  # noqa: F401
    _reflect_on_answer,
)

__all__ = [
    "_reflect_on_answer",
]
