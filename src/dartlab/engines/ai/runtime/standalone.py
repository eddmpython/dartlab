"""Company에서 분리된 LLM 분석 함수.

ask/chat은 Company가 AI를 품는 게 아니라 AI가 Company를 소비하는 구조.
내부적으로 core.analyze() 이벤트 스트림을 소비한다.

사용법::

    from dartlab.engines.ai.runtime.standalone import ask, chat

    ask(company, "재무 건전성을 분석해줘")
    chat(company, "배당 추세를 분석하고 이상 징후를 찾아줘")
"""

from __future__ import annotations

from typing import Any, Generator


def _collect_text(events) -> str:
    """이벤트 스트림에서 chunk 텍스트만 수집."""
    return "".join(ev.data["text"] for ev in events if ev.kind == "chunk")


def _stream_chunks(events) -> Generator[str, None, None]:
    """이벤트 스트림에서 chunk 텍스트만 제너레이터로 반환."""
    for ev in events:
        if ev.kind == "chunk":
            yield ev.data["text"]


def ask(
    company: Any,
    question: str,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    provider: str | None = None,
    model: str | None = None,
    stream: bool = True,
    reflect: bool = False,
    pattern: str | None = None,
    history: list[dict[str, str]] | None = None,
    **kwargs: Any,
) -> str | Generator[str, None, None]:
    """LLM에게 기업에 대해 질문.

    Args:
        company: Company 인스턴스 (DART 또는 EDGAR).
        question: 질문 텍스트 (한국어 또는 영어).
        include: 명시적으로 포함할 데이터.
        exclude: 제외할 데이터.
        provider: per-call provider override.
        model: per-call model override.
        stream: True면 제너레이터 반환 (chunk 단위).
        reflect: True면 답변 자체 검증 (1회 reflection).
        pattern: 분석 패턴 이름 (financial, risk, valuation 등).
        history: 이전 대화 메시지 리스트 (대화 연속 모드).
        **kwargs: LLMConfig override.

    Returns:
        str (stream=False) 또는 Generator[str] (stream=True).
    """
    # 패턴 적용 → 질문 앞에 패턴 프롬프트 삽입
    effective_question = question
    if pattern:
        from dartlab.engines.ai.patterns import get_pattern

        pattern_text = get_pattern(pattern)
        if pattern_text:
            effective_question = f"{pattern_text}\n\n---\n\n{question}"

    from dartlab.engines.ai.runtime.core import analyze

    events = analyze(
        company,
        effective_question,
        include=include,
        exclude=exclude,
        provider=provider,
        model=model,
        use_tools=False,
        reflect=reflect,
        history=history,
        **kwargs,
    )

    if stream:
        return _stream_chunks(events)

    answer = _collect_text(events)

    # Self-Critique: 답변 자체 검증 (1회 reflection)
    if reflect and answer:
        from dartlab.engines.ai import get_config
        from dartlab.engines.ai.providers import create_provider
        from dartlab.engines.ai.runtime.agent import _reflect_on_answer

        config_ = get_config(role=kwargs.get("role"))
        overrides = {k: v for k, v in {"provider": provider, "model": model, **kwargs}.items() if v is not None}
        if overrides:
            config_ = config_.merge(overrides)
        llm = create_provider(config_)
        # reflect는 전체 응답이 필요하므로 core 이후 후처리
        messages = [{"role": "user", "content": question}]
        answer = _reflect_on_answer(llm, messages, answer)

    return answer


def chat(
    company: Any,
    question: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    max_turns: int = 5,
    on_tool_call: Any = None,
    on_tool_result: Any = None,
    **kwargs: Any,
) -> str:
    """에이전트 모드: LLM이 필요한 도구를 직접 선택하여 분석.

    Args:
        company: Company 인스턴스.
        question: 질문 텍스트.
        provider: per-call provider override.
        model: per-call model override.
        max_turns: 최대 도구 호출 반복 횟수.
        on_tool_call: 도구 호출 시 콜백 (UI용).
        on_tool_result: 도구 결과 시 콜백 (UI용).
        **kwargs: LLMConfig override.

    Returns:
        LLM 최종 응답 텍스트.
    """
    from dartlab.engines.ai.runtime.core import analyze

    events = analyze(
        company,
        question,
        provider=provider,
        model=model,
        use_tools=True,
        max_turns=max_turns,
        **kwargs,
    )

    chunks: list[str] = []
    for ev in events:
        if ev.kind == "chunk":
            chunks.append(ev.data["text"])
        elif ev.kind == "tool_call" and on_tool_call is not None:
            on_tool_call(ev.data["name"], ev.data.get("arguments", {}))
        elif ev.kind == "tool_result" and on_tool_result is not None:
            on_tool_result(ev.data["name"], ev.data.get("result", ""))

    return "".join(chunks)


def analyze_full(
    company: Any,
    question: str,
    **kwargs: Any,
) -> list:
    """모든 이벤트를 리스트로 반환 — 노트북/스크립트용.

    core.analyze()의 전체 이벤트 스트림을 수집해서 반환.
    validation, ui_action, chart 등 모든 이벤트 접근 가능.

    Example::

        from dartlab.engines.ai.runtime.standalone import analyze_full

        events = analyze_full(company, "영업이익률 추세는?")
        for ev in events:
            print(ev.kind, ev.data)
    """
    from dartlab.engines.ai.runtime.core import analyze

    return list(analyze(company, question, **kwargs))
