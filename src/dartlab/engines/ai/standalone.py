"""Company에서 분리된 LLM 분석 함수.

ask/chat은 Company가 AI를 품는 게 아니라 AI가 Company를 소비하는 구조.

사용법::

    from dartlab.engines.ai.standalone import ask, chat

    ask(company, "재무 건전성을 분석해줘")
    chat(company, "배당 추세를 분석하고 이상 징후를 찾아줘")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


def ask(
    company: Any,
    question: str,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    provider: str | None = None,
    model: str | None = None,
    stream: bool = False,
    **kwargs: Any,
) -> str:
    """LLM에게 기업에 대해 질문.

    Args:
        company: Company 인스턴스 (DART 또는 EDGAR).
        question: 질문 텍스트 (한국어 또는 영어).
        include: 명시적으로 포함할 데이터.
        exclude: 제외할 데이터.
        provider: per-call provider override.
        model: per-call model override.
        stream: True면 터미널에 스트리밍 출력 후 전체 텍스트 반환.
        **kwargs: LLMConfig override.

    Returns:
        LLM 응답 텍스트.
    """
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.context import (
        _get_sector,
        build_compact_context,
        build_context,
    )
    from dartlab.engines.ai.pipeline import run_pipeline
    from dartlab.engines.ai.prompts import _classify_question, build_system_prompt
    from dartlab.engines.ai.providers import create_provider

    config_ = get_config()
    overrides = {k: v for k, v in {"provider": provider, "model": model, **kwargs}.items() if v is not None}
    if overrides:
        config_ = config_.merge(overrides)

    use_compact = config_.provider in ("ollama", "codex", "claude-code")

    if use_compact:
        context_text, included_tables = build_compact_context(
            company,
            question,
            include=include,
            exclude=exclude,
        )
    else:
        context_text, included_tables = build_context(
            company,
            question,
            include=include,
            exclude=exclude,
        )

    if not use_compact:
        pipeline_result = run_pipeline(company, question, included_tables)
        if pipeline_result:
            context_text = context_text + pipeline_result

    sector = _get_sector(company)
    question_type = _classify_question(question)
    system = build_system_prompt(
        config_.system_prompt,
        included_modules=included_tables,
        sector=sector,
        question_type=question_type,
        compact=use_compact,
    )

    corp_name = getattr(company, "corpName", "Unknown")
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", ""))

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{context_text}\n\n---\n\n질문: {question}"},
    ]

    llm = create_provider(config_)

    if stream:
        chunks: list[str] = []
        for chunk in llm.stream(messages):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        print()
        return "".join(chunks)

    response = llm.complete(messages)
    response.context_tables = included_tables

    from dartlab import config

    if config.verbose:
        print(f"  [LLM] {response.provider}/{response.model}")
        if response.usage:
            print(f"  [LLM] tokens: {response.usage.get('total_tokens', '?')}")

    return response.answer


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
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.agent import AGENT_SYSTEM_ADDITION, agent_loop
    from dartlab.engines.ai.prompts import build_system_prompt
    from dartlab.engines.ai.providers import create_provider

    config_ = get_config()
    overrides = {k: v for k, v in {"provider": provider, "model": model, **kwargs}.items() if v is not None}
    if overrides:
        config_ = config_.merge(overrides)

    corp_name = getattr(company, "corpName", "Unknown")
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", ""))

    system = build_system_prompt(config_.system_prompt) + AGENT_SYSTEM_ADDITION
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"기업: {corp_name} ({stock_id})\n\n{question}"},
    ]

    llm = create_provider(config_)
    return agent_loop(
        llm,
        messages,
        company,
        max_turns=max_turns,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
    )
