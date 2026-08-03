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
    """검증 완료 chunk만 모으고 실패 종료를 빈 문자열이나 부분 성공으로 숨기지 않는다."""
    pieces: list[str] = []
    errors: list[str] = []
    for event in events:
        if event.kind == "chunk":
            text = event.data.get("text", "")
            if text:
                pieces.append(str(text))
        elif event.kind == "error":
            errors.append(str(event.data.get("error") or "unknown_error"))
        elif event.kind == "done":
            completionError = _doneFailure(event)
            if completionError:
                errors.append(completionError)
    if errors:
        raise AskFailedError(errors[-1])
    if pieces:
        return "".join(pieces)
    return ""


def _chunkIter(events: Iterator[TraceEvent]) -> Iterator[str]:
    for event in events:
        if event.kind == "chunk":
            text = event.data.get("text", "")
            if text:
                yield str(text)
        elif event.kind == "error":
            raise AskFailedError(str(event.data.get("error") or "unknown_error"))
        elif event.kind == "done":
            completionError = _doneFailure(event)
            if completionError:
                raise AskFailedError(completionError)


def _doneFailure(event: TraceEvent) -> str | None:
    """실패 done 이벤트를 모든 ask 소비자가 공유하는 오류 문자열로 정규화한다."""
    meta = event.data.get("responseMeta")
    if not isinstance(meta, dict):
        return None
    finalEvent = str(meta.get("finalEvent") or "")
    responseStatus = str(meta.get("responseStatus") or "")
    if responseStatus != "failed" and finalEvent not in {"runtime_error", "failed", "unable"}:
        return None
    return str(meta.get("failureReason") or meta.get("failureCode") or "DartLab 답변 품질 검증에 실패했습니다")


__all__ = ["AskFailedError", "ask", "createTask"]
