"""설치형 agent runtime이 DartLab AI의 단일 실행 경계인지 검증한다."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def _fakeEvents(_question: str, **_kwargs):
    """Sig: _fakeEvents(question, **kwargs) -> Iterator[TraceEvent].

    Args: 테스트 질문과 무시하는 런타임 선택값이다.
    Returns: 공개 ask 변환을 검증할 결정론적 이벤트다.
    Example: `events = list(_fakeEvents("질문"))`.
    """
    from dartlab.ai.contracts import TraceEvent

    yield TraceEvent("runtime_session", {"sessionId": "s1", "runtimeId": "codex", "resumed": False})
    yield TraceEvent("chunk", {"text": "DartLab runtime 응답"})
    yield TraceEvent(
        "done",
        {"responseMeta": {"finalEvent": "answer", "responseStatus": "ok", "runtimeId": "codex"}},
    )


def test_agent_runtime_registry_is_manifest_driven():
    from dartlab.ai.runtime.registry import loadRuntimeRegistry

    registry = loadRuntimeRegistry()

    assert set(registry) == {"codex", "claude", "cline"}
    assert {item.driver for item in registry.values()} == {"codexAppServer", "claudeStreamJson", "acp"}
    assert all(item.installArgs for item in registry.values())


def test_public_ask_non_stream_returns_runtime_text(monkeypatch):
    import dartlab
    from dartlab.ai import kernel

    monkeypatch.setattr(kernel, "runRuntimeAgent", _fakeEvents)

    assert dartlab.ask("너 뭐 할 수 있니", stream=False) == "DartLab runtime 응답"


def test_public_ask_stream_prints_and_returns_text(monkeypatch, capsys):
    import dartlab
    from dartlab.ai import kernel

    monkeypatch.setattr(kernel, "runRuntimeAgent", _fakeEvents)

    assert dartlab.ask("너 뭐 할 수 있니", stream=True) == "DartLab runtime 응답"
    assert "DartLab runtime 응답" in capsys.readouterr().out


def test_public_ask_stream_does_not_swallow_runtime_failure(monkeypatch):
    import dartlab
    from dartlab.ai import kernel

    def failingEvents(_question: str, **_kwargs):
        raise RuntimeError("runtime failed")
        yield

    monkeypatch.setattr(kernel, "runRuntimeAgent", failingEvents)

    with pytest.raises(RuntimeError, match="runtime failed"):
        dartlab.ask("실패를 숨기지 마", stream=True)


@pytest.mark.parametrize("stream", [False, True])
def test_public_ask_rejects_failed_done_event(monkeypatch, stream):
    import dartlab
    from dartlab.ai import kernel
    from dartlab.ai.contracts import TraceEvent

    def rejectedEvents(_question: str, **_kwargs):
        yield TraceEvent(
            "done",
            {
                "responseMeta": {
                    "finalEvent": "runtime_error",
                    "responseStatus": "failed",
                    "failureReason": "근거 셀 검증 실패",
                }
            },
        )

    monkeypatch.setattr(kernel, "runRuntimeAgent", rejectedEvents)

    with pytest.raises(kernel.AskFailedError, match="근거 셀 검증 실패"):
        dartlab.ask("실패 답변을 공개하지 마", stream=stream)


def test_internal_events_are_reserved_for_adapters(monkeypatch):
    from dartlab.ai import kernel

    monkeypatch.setattr(kernel, "runRuntimeAgent", _fakeEvents)

    events = list(kernel.ask("너 뭐 할 수 있니", events=True))

    assert events[0].kind == "runtime_session"
    assert events[-1].kind == "done"
