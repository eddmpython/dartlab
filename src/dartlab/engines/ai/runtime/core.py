"""AI 분석 통합 오케스트레이터.

dartlab.ask(), server UI, CLI가 모두 이 코어를 소비한다.
동기 제너레이터로 AnalysisEvent를 생산하며, 소비자가 형식(SSE/텍스트/제너레이터)을 결정.

사용법::

    from dartlab.engines.ai.runtime.core import analyze

    # 코드에서 직접
    for event in analyze(company, "영업이익률 추세는?"):
        if event.kind == "chunk":
            print(event.data["text"], end="")

    # 서버에서 (SSE 변환)
    for event in analyze(company, question, snapshot=snapshot, ...):
        yield event_to_sse(event)
"""

from __future__ import annotations

import json
from typing import Any, Generator

from dartlab.engines.ai.runtime.events import AnalysisEvent, EventKind


# ── 상수 ──────────────────────────────────────────────────

_COMPACT_PROVIDERS = frozenset({"ollama", "codex"})


# ── context tier 결정 ─────────────────────────────────────

def _resolve_context_tier(provider: str, use_tools: bool) -> str:
    """standalone의 이진 선택과 server의 3단 선택을 통합."""
    compact = provider in _COMPACT_PROVIDERS
    tool_capable = provider in {"openai", "ollama", "custom"}

    if use_tools and tool_capable and not (compact and provider != "ollama"):
        return "skeleton"
    if compact:
        return "focused"
    return "full"


# ── 에러 분류 ─────────────────────────────────────────────

def _classify_error(e: Exception) -> dict[str, str]:
    """예외 → {error: str, action: str} 매핑."""
    err_type = type(e).__name__
    err_str = str(e)

    if isinstance(e, FileNotFoundError):
        return {"error": err_str, "action": "install"}
    if isinstance(e, PermissionError):
        return {"error": err_str, "action": "login"}
    if err_type == "ChatGPTOAuthError":
        err_low = err_str.lower()
        if any(kw in err_low for kw in ("token", "expire", "login")):
            return {"error": "ChatGPT 인증이 만료되었습니다. 다시 로그인해주세요.", "action": "relogin"}
        if any(kw in err_low for kw in ("rate", "limit")):
            return {"error": "ChatGPT 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.", "action": "rate_limit"}
        return {"error": f"ChatGPT 연결 오류: {err_str}", "action": "relogin"}
    if err_type == "OpenAIError" or "api_key" in err_str.lower():
        return {"error": "AI 설정이 필요합니다. API 키를 확인하거나 다른 provider를 선택해주세요.", "action": "config"}

    return {"error": err_str, "action": ""}


# ── 통합 오케스트레이터 ──────────────────────────────────

def analyze(
    company: Any | None,
    question: str,
    *,
    # LLM 설정
    provider: str | None = None,
    role: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    # 모드
    use_tools: bool = True,
    max_turns: int = 5,
    max_tools: int | None = None,
    reflect: bool = False,
    # 자동 계산 OR pre-computed
    snapshot: dict | None = None,
    auto_snapshot: bool = True,
    focus_context: str | None = None,
    diff_context: str | None = None,
    auto_diff: bool = True,
    history: list | None = None,
    history_messages: list[dict] | None = None,
    view_context: dict | None = None,
    dialogue_policy: str | None = None,
    conversation_meta: dict | None = None,
    question_types: tuple[str, ...] = (),
    # 기능 플래그
    validate: bool = True,
    detect_navigate: bool = True,
    emit_system_prompt: bool = True,
    # 단축 경로
    not_found_msg: str | None = None,
    # 추가 LLMConfig overrides
    **kwargs: Any,
) -> Generator[AnalysisEvent, None, None]:
    """AI 분석 이벤트 스트림 생산.

    Args:
        company: Company 인스턴스 (DART/EDGAR). None이면 순수 대화.
        question: 질문 텍스트.
        provider: LLM provider override.
        role: role-aware provider/model binding override.
        model: 모델 override.
        api_key: API 키 override.
        base_url: Base URL override.
        include: 포함할 데이터 모듈.
        exclude: 제외할 데이터 모듈.
        use_tools: True면 에이전트 모드 (도구 사용).
        max_turns: 에이전트 최대 반복 횟수.
        max_tools: 도구 최대 개수 (소형 모델용).
        reflect: True면 답변 자체 검증 (1회 reflection).
        snapshot: pre-computed 핵심 수치 스냅샷.
        auto_snapshot: True면 snapshot 미전달 시 자동 계산.
        focus_context: pre-computed 뷰어 포커스 컨텍스트.
        diff_context: pre-computed 기간간 변화 핫스팟.
        auto_diff: True면 diff_context 미전달 시 자동 계산.
        history: raw 히스토리 (dict/Pydantic). 자동으로 경량 타입 변환.
        history_messages: pre-computed LLM messages 포맷 히스토리.
        view_context: raw 뷰어 컨텍스트 (dict/Pydantic).
        dialogue_policy: pre-computed 대화 정책 텍스트.
        conversation_meta: 대화 메타 정보 (meta 이벤트에 포함).
        question_types: 질문 유형 분류 결과.
        validate: True면 LLM 답변 숫자 검증.
        detect_navigate: True면 navigate ui_action 감지.
        emit_system_prompt: True면 system_prompt 이벤트 생산.
        not_found_msg: 종목 미발견 메시지. 설정 시 meta+chunk+done만 emit.

    Yields:
        AnalysisEvent — kind별 이벤트.
    """
    # ── not_found 단축 경로 ──
    if not_found_msg:
        meta = conversation_meta or {}
        corp_name = getattr(company, "corpName", None) if company else None
        stock_id = (
            getattr(company, "stockCode", getattr(company, "ticker", ""))
            if company else None
        )
        if corp_name:
            meta.setdefault("company", corp_name)
        if stock_id:
            meta.setdefault("stockCode", stock_id)
        yield AnalysisEvent("meta", meta)
        yield AnalysisEvent("chunk", {"text": not_found_msg})
        yield AnalysisEvent("done", {})
        return

    full_response_parts: list[str] = []
    done_payload: dict[str, Any] = {}
    included_tables: list[str] = []

    try:
        yield from _analyze_inner(
            company, question,
            provider=provider, role=role, model=model, api_key=api_key, base_url=base_url,
            include=include, exclude=exclude,
            use_tools=use_tools, max_turns=max_turns, max_tools=max_tools,
            reflect=reflect,
            snapshot=snapshot, auto_snapshot=auto_snapshot,
            focus_context=focus_context, diff_context=diff_context, auto_diff=auto_diff,
            history=history, history_messages=history_messages,
            view_context=view_context, dialogue_policy=dialogue_policy,
            conversation_meta=conversation_meta, question_types=question_types,
            validate=validate, detect_navigate=detect_navigate,
            emit_system_prompt=emit_system_prompt,
            _full_response_parts=full_response_parts,
            _done_payload=done_payload,
            _included_tables=included_tables,
            **kwargs,
        )
    except (
        AttributeError, ConnectionError, FileNotFoundError, ImportError,
        KeyError, OSError, PermissionError, RuntimeError, TimeoutError,
        TypeError, ValueError,
    ) as e:
        yield AnalysisEvent("error", _classify_error(e))

    # ── 후처리: navigate ui_action ──
    if detect_navigate and company is not None:
        nav_event = _detect_navigate_action(company, question)
        if nav_event:
            yield nav_event

    # ── 후처리: validation ──
    if validate and company is not None and full_response_parts:
        val_event = _run_validation(company, full_response_parts)
        if val_event:
            yield val_event

    # ── Done 이벤트 ──
    done_payload.setdefault("includedModules", included_tables)
    yield AnalysisEvent("done", done_payload)


def _analyze_inner(
    company: Any | None,
    question: str,
    *,
    provider: str | None, role: str | None, model: str | None,
    api_key: str | None, base_url: str | None,
    include: list[str] | None, exclude: list[str] | None,
    use_tools: bool, max_turns: int, max_tools: int | None,
    reflect: bool,
    snapshot: dict | None, auto_snapshot: bool,
    focus_context: str | None, diff_context: str | None, auto_diff: bool,
    history: list | None, history_messages: list[dict] | None,
    view_context: dict | None, dialogue_policy: str | None,
    conversation_meta: dict | None, question_types: tuple[str, ...],
    validate: bool, detect_navigate: bool, emit_system_prompt: bool,
    _full_response_parts: list[str],
    _done_payload: dict[str, Any],
    _included_tables: list[str],
    **kwargs: Any,
) -> Generator[AnalysisEvent, None, None]:
    """analyze() 본체 — 에러 핸들링은 외부에서."""
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.providers import create_provider

    # ── 1. Config 해석 ──
    config_ = get_config(role=role)
    overrides = {
        k: v
        for k, v in {
            "provider": provider, "model": model,
            "api_key": api_key, "base_url": base_url,
            **kwargs,
        }.items()
        if v is not None
    }
    if overrides:
        config_ = config_.merge(overrides)

    resolved_provider = config_.provider
    context_tier = _resolve_context_tier(resolved_provider, use_tools)
    is_compact = context_tier != "full"

    corp_name = getattr(company, "corpName", "Unknown") if company else None
    stock_id = (
        getattr(company, "stockCode", getattr(company, "ticker", ""))
        if company
        else None
    )

    # ── 2. 대화 상태 자동 빌드 ──
    state = None
    if history is not None or view_context is not None:
        from dartlab.engines.ai.conversation.dialogue import build_conversation_state
        from dartlab.engines.ai.types import history_from_dicts, view_context_from_dict

        light_history = history_from_dicts(history)
        light_view = view_context_from_dict(view_context)

        # 순수 대화이면 viewContext 무시
        from dartlab.engines.ai.conversation.intent import is_pure_conversation
        if is_pure_conversation(question):
            light_view = None

        state = build_conversation_state(
            question,
            history=light_history,
            company=company,
            view_context=light_view,
        )

        # dialogue_policy 자동 생성
        if dialogue_policy is None:
            from dartlab.engines.ai.conversation.dialogue import build_dialogue_policy
            dialogue_policy = build_dialogue_policy(state)

        # conversation_meta 자동 생성
        if conversation_meta is None:
            from dartlab.engines.ai.conversation.dialogue import conversation_state_to_meta
            conversation_meta = conversation_state_to_meta(state)

        # question_types 자동 추출
        if not question_types and state.question_types:
            question_types = state.question_types

    # ── 3. 히스토리 messages 자동 빌드 ──
    if history_messages is None and history is not None:
        from dartlab.engines.ai.conversation.history import build_history_messages, compress_history
        from dartlab.engines.ai.types import history_from_dicts

        light_history = history_from_dicts(history)
        compressed = compress_history(light_history)
        history_messages = build_history_messages(compressed)

    # ── 4. Auto-snapshot ──
    if snapshot is None and auto_snapshot and company is not None:
        from dartlab.engines.ai.context.snapshot import build_snapshot
        snapshot = build_snapshot(company)

    # ── 5. Auto focus/diff context ──
    if focus_context is None and state is not None and company is not None and state.topic:
        from dartlab.engines.ai.conversation.focus import build_focus_context
        focus_context = build_focus_context(company, state)

    if diff_context is None and auto_diff and company is not None:
        from dartlab.engines.ai.conversation.focus import build_diff_context
        diff_context = build_diff_context(company)

    # ── 6. Intent 분류 → light mode 감지 ──
    from dartlab.engines.ai.conversation.intent import has_analysis_intent

    is_light = company is not None and not has_analysis_intent(
        state.question if state else question
    )

    # ── 7. Meta 이벤트 ──
    meta = conversation_meta or {}
    if corp_name:
        meta.setdefault("company", corp_name)
    if stock_id:
        meta.setdefault("stockCode", stock_id)
    yield AnalysisEvent("meta", meta)

    # ── 8. Snapshot 이벤트 ──
    if snapshot is not None:
        yield AnalysisEvent("snapshot", snapshot)

    # ── 9. Light mode 경로 ──
    if is_light:
        yield from _run_light_mode(
            company, question, config_, state,
            focus_context=focus_context,
            history_messages=history_messages,
            dialogue_policy=dialogue_policy,
            emit_system_prompt=emit_system_prompt,
            _full_response_parts=_full_response_parts,
        )
        return

    # ── 10. Full analysis 경로 ──

    # Context 빌드
    context_text = ""
    if company is not None:
        from dartlab.engines.ai.context.builder import (
            _get_sector,
            build_context_tiered,
        )

        modules_dict, included_tables_local, header_text = build_context_tiered(
            company, question, context_tier, include, exclude,
        )
        _included_tables.extend(included_tables_local)

        # 모듈별 context 이벤트 yield
        for module_name, module_text in modules_dict.items():
            yield AnalysisEvent("context", {
                "module": module_name,
                "text": module_text,
            })

        # context_text 조립
        context_parts = [header_text] if header_text else []
        if focus_context:
            context_parts.append(focus_context)
        context_parts.extend(
            modules_dict[name] for name in included_tables_local
            if name in modules_dict
        )
        context_text = "\n\n".join(context_parts)

    # focus/diff context 합류
    if focus_context and company is None:
        context_text = focus_context
    if diff_context:
        context_text = f"{context_text}\n\n{diff_context}" if context_text else diff_context
        yield AnalysisEvent("context", {
            "module": "_diff",
            "label": "공시 텍스트 변화 핫스팟",
            "text": diff_context,
        })

    # Pipeline (full tier만)
    if context_tier == "full" and company is not None:
        from dartlab.engines.ai.runtime.pipeline import run_pipeline

        pipeline_result = run_pipeline(company, question, _included_tables)
        if pipeline_result:
            context_text = context_text + pipeline_result

    # ── 11. 프롬프트 조립 ──
    from dartlab.engines.ai.conversation.prompts import _classify_question, build_system_prompt

    sector = None
    if company is not None:
        from dartlab.engines.ai.context.builder import _get_sector
        sector = _get_sector(company)

    q_type = _classify_question(question)
    system = build_system_prompt(
        config_.system_prompt,
        included_modules=_included_tables,
        sector=sector,
        question_type=q_type,
        question_types=list(question_types) if question_types else None,
        compact=is_compact,
    )

    if dialogue_policy:
        system = system + "\n\n" + dialogue_policy

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": system})

    # ── 12. Messages 조립 ──
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]

    if history_messages:
        messages.extend(history_messages)

    user_content = f"{context_text}\n\n---\n\n질문: {question}" if context_text else question
    messages.append({"role": "user", "content": user_content})

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": system, "userContent": user_content})

    # ── 13. LLM 호출 ──
    llm = create_provider(config_)

    use_guided = is_compact and company is not None and hasattr(llm, "complete_json")
    tool_capable = (
        not use_guided
        and use_tools
        and company is not None
        and getattr(llm, "supports_native_tools", False)
        and hasattr(llm, "complete_with_tools")
    )

    if use_guided:
        yield from _run_guided_json(llm, messages, _full_response_parts, _done_payload)
    elif tool_capable:
        if max_tools is None and resolved_provider == "ollama":
            max_tools = 10
        yield from _run_agent(
            llm, messages, company, question,
            max_turns=max_turns,
            max_tools=max_tools,
            q_type=q_type,
            _full_response_parts=_full_response_parts,
        )
    else:
        yield from _run_stream(llm, messages, _full_response_parts)

    # ── 14. Response meta 추출 ──
    if company and _full_response_parts and "responseMeta" not in _done_payload:
        from dartlab.engines.ai.conversation.prompts import extract_response_meta

        full_text = "".join(_full_response_parts)
        response_meta = extract_response_meta(full_text)
        if response_meta.get("grade") or response_meta.get("has_conclusion"):
            _done_payload["responseMeta"] = response_meta

    # ── 15. Meta 업데이트 (includedModules, yearRange) ──
    if _included_tables:
        meta_update: dict[str, Any] = {"includedModules": _included_tables}
        if not is_compact and company is not None:
            from dartlab.engines.ai.context.builder import detect_year_range
            year_range = detect_year_range(company, _included_tables)
            if year_range:
                meta_update["dataYearRange"] = year_range
        yield AnalysisEvent("meta", meta_update)


# ── Light mode ────────────────────────────────────────────

def _run_light_mode(
    company: Any,
    question: str,
    config_: Any,
    state: Any,
    *,
    focus_context: str | None,
    history_messages: list[dict] | None,
    dialogue_policy: str | None,
    emit_system_prompt: bool,
    _full_response_parts: list[str],
) -> Generator[AnalysisEvent, None, None]:
    """분석 의도 없을 때 — 간략 회사 컨텍스트 + 대화 프롬프트."""
    from dartlab.engines.ai.conversation.prompts import build_dynamic_chat_prompt
    from dartlab.engines.ai.providers import create_provider

    if focus_context:
        yield AnalysisEvent("context", {
            "module": "_focus_topic",
            "label": f"현재 섹션: {getattr(state, 'topic_label', '') or getattr(state, 'topic', '')}",
            "text": focus_context,
        })

    # 간략 회사 컨텍스트
    light_company_ctx = f"\n\n## 현재 대화 종목\n"
    light_company_ctx += f"사용자가 **{company.corpName}** ({getattr(company, 'stockCode', getattr(company, 'ticker', ''))})에 대해 이야기하고 있습니다.\n"

    # insights 등급 1줄 요약
    try:
        from dartlab.engines.insight.pipeline import analyze as _light_analyze

        _light_result = _light_analyze(
            getattr(company, "stockCode", getattr(company, "ticker", "")),
            company=company,
        )
        if _light_result is not None:
            _grades = _light_result.grades()
            _grade_str = " / ".join(
                f"{lbl}:{_grades.get(k, 'N')}"
                for k, lbl in [
                    ("performance", "실적"), ("profitability", "수익성"),
                    ("health", "건전성"), ("cashflow", "CF"),
                    ("governance", "지배구조"), ("risk", "리스크"),
                    ("opportunity", "기회"),
                ]
                if _grades.get(k)
            )
            light_company_ctx += f"- 인사이트 등급: {_grade_str}\n"
            if _light_result.profile:
                light_company_ctx += f"- 프로파일: {_light_result.profile}\n"
    except (ImportError, AttributeError, FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
        pass

    # topics 상위 10개
    try:
        _topics = list(getattr(company, "topics", None) or [])[:10]
        if _topics:
            light_company_ctx += f"- 조회 가능 topic(일부): {', '.join(_topics)}\n"
    except (AttributeError, TypeError):
        pass

    light_company_ctx += (
        "\n아직 구체적 분석 요청은 아닙니다. 가볍게 대화하되, "
        "분석이 필요하면 어떤 분석을 원하는지 물어보세요.\n"
        "예: '어떤 분석을 원하시나요? 재무 건전성, 수익성, 배당, 종합 분석 등을 해드릴 수 있습니다.'"
    )

    light_prompt = build_dynamic_chat_prompt(state) + light_company_ctx

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": light_prompt})

    messages: list[dict[str, str]] = [{"role": "system", "content": light_prompt}]
    if history_messages:
        messages.extend(history_messages)

    user_text = question
    if focus_context:
        user_text = f"{focus_context}\n\n---\n\n질문: {question}"
    messages.append({"role": "user", "content": user_text})

    llm = create_provider(config_)
    for chunk in llm.stream(messages):
        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})


# ── Guided JSON ───────────────────────────────────────────

def _run_guided_json(
    llm,
    messages: list[dict],
    _full_response_parts: list[str],
    _done_payload: dict[str, Any],
) -> Generator[AnalysisEvent, None, None]:
    """Compact provider용 guided JSON → markdown 변환."""
    from dartlab.engines.ai.conversation.prompts import GUIDED_SCHEMA, guided_json_to_markdown

    resp = llm.complete_json(messages, GUIDED_SCHEMA)
    raw_json = resp.answer
    try:
        parsed = json.loads(raw_json)
        md_text = guided_json_to_markdown(parsed)
        _done_payload["guidedRaw"] = parsed
        if parsed.get("grade"):
            _done_payload["responseMeta"] = {
                "grade": parsed["grade"],
                "has_conclusion": bool(parsed.get("conclusion")),
                "signals": {
                    "positive": [p[:20] for p in parsed.get("positives", [])[:3]],
                    "negative": [
                        r.get("description", "")[:20]
                        for r in parsed.get("risks", [])[:3]
                        if isinstance(r, dict)
                    ],
                },
                "tables_count": 1,
            }
    except (json.JSONDecodeError, ValueError):
        md_text = raw_json

    _full_response_parts.append(md_text)
    # 단락별 yield
    paragraphs = md_text.split("\n\n")
    for i, para in enumerate(paragraphs):
        chunk_text = para if i == len(paragraphs) - 1 else para + "\n\n"
        yield AnalysisEvent("chunk", {"text": chunk_text})


# ── 내부 헬퍼 ────────────────────────────────────────────

def _run_stream(
    llm,
    messages: list[dict],
    _full_response_parts: list[str],
) -> Generator[AnalysisEvent, None, None]:
    """직접 스트리밍 — 도구 없이 LLM 응답 chunk를 yield."""
    for chunk in llm.stream(messages):
        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})


def _run_agent(
    llm,
    messages: list[dict],
    company: Any,
    question: str,
    *,
    max_turns: int = 5,
    max_tools: int | None = None,
    q_type: str | None = None,
    _full_response_parts: list[str],
) -> Generator[AnalysisEvent, None, None]:
    """에이전트 모드 — 도구 호출 + 스트리밍 응답."""
    from dartlab.engines.ai.runtime.agent import agent_loop_stream, build_agent_system_addition
    from dartlab.engines.ai.tools.registry import build_tool_runtime

    runtime = build_tool_runtime(company, name="core-agent")

    system_addition = build_agent_system_addition(runtime)
    messages[0]["content"] += system_addition

    tool_calls_log: list[dict] = []
    tool_results_log: list[dict] = []
    chart_events: list[dict] = []
    ui_events: list[AnalysisEvent] = []

    def _on_tool_call(name: str, arguments: dict) -> None:
        tool_calls_log.append({"name": name, "arguments": arguments})

    def _on_tool_result(name: str, result: str) -> None:
        tool_results_log.append({"name": name, "result": result})
        # create_chart 도구 결과에서 ChartSpec 추출
        if name == "create_chart":
            try:
                parsed = json.loads(result)
                charts = parsed.get("charts")
                if charts:
                    chart_events.append({"charts": charts})
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        # UI 도구 결과는 canonical ui_action만 전달한다.
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and parsed.get("action"):
                ui_events.append(AnalysisEvent(EventKind.UI_ACTION, parsed))
        except (json.JSONDecodeError, TypeError):
            pass

    for chunk in agent_loop_stream(
        llm, messages, company,
        max_turns=max_turns,
        max_tools=max_tools,
        runtime=runtime,
        on_tool_call=_on_tool_call,
        on_tool_result=_on_tool_result,
        question_type=q_type,
    ):
        # tool call/result/chart/ui 이벤트를 먼저 flush
        while tool_calls_log:
            tc = tool_calls_log.pop(0)
            yield AnalysisEvent("tool_call", tc)
        while tool_results_log:
            tr = tool_results_log.pop(0)
            yield AnalysisEvent("tool_result", tr)
        while chart_events:
            ce = chart_events.pop(0)
            yield AnalysisEvent("chart", ce)
        while ui_events:
            yield ui_events.pop(0)

        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})

    # 남은 이벤트 flush
    while tool_calls_log:
        yield AnalysisEvent("tool_call", tool_calls_log.pop(0))
    while tool_results_log:
        yield AnalysisEvent("tool_result", tool_results_log.pop(0))
    while chart_events:
        yield AnalysisEvent("chart", chart_events.pop(0))
    while ui_events:
        yield ui_events.pop(0)


# ── 후처리 헬퍼 ──────────────────────────────────────────

def _detect_navigate_action(company: Any, question: str) -> AnalysisEvent | None:
    """질문에서 viewer 이동 의도를 감지해 navigate ui_action을 만든다."""
    from dartlab.engines.ai.conversation.dialogue import detect_viewer_intent

    company_topics = None
    try:
        company_topics = list(getattr(company, "topics", None) or [])
    except (AttributeError, TypeError):
        pass

    viewer_intent = detect_viewer_intent(question, topics=company_topics)
    if viewer_intent is None:
        return None

    nav_payload: dict[str, Any] = {"action": "navigate", "topic": viewer_intent.get("topic", "")}
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", None))
    corp_name = getattr(company, "corpName", None)
    if stock_id:
        nav_payload["stockCode"] = stock_id
    if corp_name:
        nav_payload["company"] = corp_name

    return AnalysisEvent(EventKind.UI_ACTION, nav_payload)


def _run_validation(company: Any, full_response_parts: list[str]) -> AnalysisEvent | None:
    """LLM 답변의 재무 수치를 실제 값과 대조."""
    try:
        from dartlab.engines.ai.runtime.validation import extract_numbers, validate_claims

        full_text = "".join(full_response_parts)
        claims = extract_numbers(full_text)
        if not claims:
            return None
        vresult = validate_claims(claims, company)
        if vresult.mismatches:
            return AnalysisEvent("validation", {
                "mismatches": [
                    {
                        "label": mm.label,
                        "claimed": mm.claimed,
                        "actual": mm.actual,
                        "diffPct": round(mm.diff_pct, 1),
                        "unit": mm.unit,
                    }
                    for mm in vresult.mismatches
                ],
            })
    except (ImportError, AttributeError, TypeError, ValueError, OSError):
        pass
    return None
