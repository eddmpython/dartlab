"""DartLab AI 공개 진입점과 로컬 에이전트 런타임 연결."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .agent import runRuntimeAgent
from .contracts import TraceEvent, WorkbenchTask


class AskFailedError(RuntimeError):
    """실행이 답을 한 글자도 못 만들고 끝났을 때 던진다. 빈 문자열로 위장하지 않는다."""


def createTask(question: str, **_: Any) -> WorkbenchTask:
    """Create a compact research task for compatibility callers."""

    return WorkbenchTask(question=(question or "").strip())


def _askEvents(question: str, **kwargs: Any) -> Iterator[TraceEvent]:
    """Internal event stream for server/CLI adapters.

    모든 대화 모드는 사용자 PC에 설치된 agent CLI로 실행한다. 분석 깊이 같은
    표현 차이는 capsule context로 전달하며 별도 고정 graph로 우회하지 않는다.
    """
    yield from runRuntimeAgent(question, **kwargs)


def ask(question: str, *, stream: bool = True, events: bool = False, **kwargs: Any):
    """Ask DartLab.

    ``stream=True`` returns text chunks. ``stream=False`` returns the complete
    text. ``events=True`` is reserved for DartLab adapters and returns internal
    TraceEvent objects without exposing a second public answer entry point.
    """

    event_iter = _askEvents(question, **kwargs)
    if events:
        return event_iter
    if stream:
        return _chunkIter(event_iter)
    return _collectAnswer(event_iter)


def _collectAnswer(events: Iterator[TraceEvent]) -> str:
    """chunk 를 모으되, 한 글자도 못 만들고 끝난 실행은 조용히 빈 문자열로 돌려주지 않는다.

    예전에는 chunk 만 걸러 이어 붙였다. provider 가 통째로 실패해 error 이벤트만 나온 실행도
    빈 문자열을 돌려줬고, MCP 의 `ask` 는 그 위에 `ok: True` 를 고정으로 얹었다. 대표 진입점이
    완전 실패를 성공이라 보고한 셈이다. 부분이라도 답이 나왔으면 그것은 그대로 돌려준다.
    """
    pieces: list[str] = []
    errors: list[str] = []
    for event in events:
        if event.kind == "chunk":
            text = event.data.get("text", "")
            if text:
                pieces.append(str(text))
        elif event.kind == "error":
            errors.append(str(event.data.get("error") or "unknown_error"))
    if pieces:
        return "".join(pieces)
    if errors:
        raise AskFailedError(errors[-1])
    return ""


def _chunkIter(events: Iterator[TraceEvent]) -> Iterator[str]:
    for event in events:
        if event.kind == "chunk":
            text = event.data.get("text", "")
            if text:
                yield str(text)


__all__ = ["AskFailedError", "ask", "createTask"]
