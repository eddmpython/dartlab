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

from typing import Any, Generator

from dartlab.engines.ai.runtime.events import AnalysisEvent
from dartlab.engines.ai.runtime.post_processing import (
    _detect_navigate_action,
    _run_validation,
    autoInjectArtifacts,
)
from dartlab.engines.ai.runtime.run_modes import (
    _run_agent,
    _run_guided_json,
    _run_light_mode,
    _run_stream,
)

# ── 질문 복잡도 → 동적 max_turns ─────────────────────────

_MULTI_KEYWORDS = frozenset({"비교", "vs", "종합", "전체", "전반", "왜", "구체적", "상세", "분석해"})
_VALIDATION_MODULES = frozenset({"BS", "IS", "CF", "ratios", "fsSummary"})
_FOLLOW_UP_PERIOD_HINTS = frozenset(
    {
        "최근",
        "올해",
        "작년",
        "전년",
        "개년",
        "년간",
        "추세",
        "현황",
    }
)
_FOLLOW_UP_PREFIXES = ("그럼", "그러면", "이어", "계속", "더", "같은 기준", "같은 방식")


def _estimate_max_turns(question: str, q_type: str) -> int:
    """질문 복잡도에 따라 agent loop max_turns를 5~10 범위로 결정."""
    turns = 5
    if any(k in question for k in _MULTI_KEYWORDS):
        turns += 2
    if q_type in ("사업", "리스크", "공시"):
        turns += 1
    if q_type == "종합":
        turns += 3
    return min(turns, 10)


def _should_run_validation(included_tables: list[str]) -> bool:
    """재무 컨텍스트가 실제로 포함된 경우에만 검증을 수행한다."""
    return bool(_VALIDATION_MODULES & set(included_tables))


def _build_included_evidence(included_tables: list[str]) -> list[dict[str, str]]:
    """내부 모듈명을 사용자용 evidence label로 함께 정리한다."""
    if not included_tables:
        return []

    from dartlab.engines.ai.context.builder import _section_key_to_module_name
    from dartlab.engines.ai.metadata import get_meta

    special_labels = {
        "BS": "재무상태표",
        "IS": "손익계산서",
        "CF": "현금흐름표",
        "CIS": "포괄손익계산서",
        "SCE": "자본변동표",
        "ratios": "핵심 재무비율",
        "dividend": "배당 데이터",
        "shareCapital": "자본 변동 데이터",
        "audit": "감사 관련 데이터",
        "businessOverview": "사업의 개요",
        "productService": "제품·서비스",
        "disclosureChanges": "공시 변화",
        "riskDerivative": "리스크·파생상품",
        "costByNature": "성격별 비용 분류",
        "segments": "사업부문 데이터",
        "IS_quarterly": "분기별 손익계산서",
        "CF_quarterly": "분기별 현금흐름표",
        "BS_quarterly": "분기별 재무상태표",
        "_dart_openapi_filings": "최근 공시 목록",
        "_diff": "공시 변화 비교",
        "_response_contract": "응답 계약",
        "_clarify": "확인 질문",
    }
    evidence: list[dict[str, str]] = []
    for raw_name in included_tables:
        normalized = _section_key_to_module_name(raw_name)
        meta = get_meta(normalized)
        if meta and meta.label and meta.label != normalized and meta.label != raw_name:
            label = meta.label
        else:
            label = special_labels.get(raw_name, special_labels.get(normalized, normalized))
        evidence.append({"name": raw_name, "label": label})
    return evidence


def _context_label(module_name: str, explicit_label: str | None = None) -> str | None:
    """context 이벤트용 사용자 표시 라벨."""
    if explicit_label:
        return explicit_label

    from dartlab.engines.ai.context.builder import _section_key_to_module_name
    from dartlab.engines.ai.metadata import get_meta

    normalized = _section_key_to_module_name(module_name)
    meta = get_meta(normalized)
    if meta and meta.label and meta.label != normalized and meta.label != module_name:
        return meta.label
    return next(
        (
            label
            for key, label in {
                "BS": "재무상태표",
                "IS": "손익계산서",
                "CF": "현금흐름표",
                "CIS": "포괄손익계산서",
                "SCE": "자본변동표",
                "ratios": "핵심 재무비율",
                "dividend": "배당 데이터",
                "shareCapital": "자본 변동 데이터",
                "audit": "감사 관련 데이터",
                "businessOverview": "사업의 개요",
                "productService": "제품·서비스",
                "disclosureChanges": "공시 변화",
                "riskDerivative": "리스크·파생상품",
                "costByNature": "성격별 비용 분류",
                "segments": "사업부문 데이터",
                "_dart_openapi_filings": "최근 공시 목록",
                "_diff": "공시 변화 비교",
            }.items()
            if normalized == key or module_name == key
        ),
        normalized,
    )


def _should_use_light_mode(company: Any | None, question: str, state: Any, report_mode: bool) -> bool:
    """가벼운 대화/메타 질문에만 light mode를 허용한다."""
    if company is None or report_mode:
        return False

    from dartlab.engines.ai.conversation.intent import has_analysis_intent, is_meta_question, is_pure_conversation

    effective_question = state.question if state is not None and getattr(state, "question", None) else question
    if _is_analysis_follow_up(effective_question, state):
        return False
    if is_pure_conversation(effective_question):
        return True
    if is_meta_question(effective_question) and not has_analysis_intent(effective_question):
        return True
    return False


# ── 데이터 신선도 추출 ────────────────────────────────────


def _extract_data_date(company: Any) -> str | None:
    """Company에서 최신 데이터 기준일을 추출한다."""
    try:
        filings = company.filings() if callable(getattr(company, "filings", None)) else None
        if filings is not None and hasattr(filings, "columns") and "date" in filings.columns:
            dates = filings["date"].drop_nulls()
            if len(dates) > 0:
                return str(dates.max())
    except (AttributeError, TypeError, KeyError):
        pass
    return None


# ── context tier 결정 ─────────────────────────────────────


def _resolve_context_tier(provider: str, use_tools: bool) -> str:
    """standalone의 이진 선택과 server의 3단 선택을 통합."""
    tool_capable = provider in {"openai", "ollama", "custom"}

    if use_tools and tool_capable:
        return "skeleton"
    return "focused"


def _resolve_runtime_route(question: str, question_types: tuple[str, ...], report_mode: bool) -> str:
    """질문별 cheap-first 런타임 경로를 결정한다."""
    if report_mode:
        return "hybrid"

    try:
        from dartlab.engines.ai.context.builder import _resolve_context_route

        q_types = list(question_types) if question_types else []
        return _resolve_context_route(question, include=None, q_types=q_types)
    except (AttributeError, ImportError, RuntimeError, TypeError, ValueError):
        return "hybrid"


def _resolve_snapshot_policy(question: str, question_types: tuple[str, ...], report_mode: bool) -> dict[str, Any]:
    """질문별 snapshot 비용 정책."""
    route = _resolve_runtime_route(question, question_types, report_mode)
    enabled = route not in {"sections", "report"}
    return {
        "route": route,
        "enabled": enabled,
        "includeInsights": False,
        "includeDataDate": route == "hybrid",
    }


def _resolve_follow_up_include(include: list[str] | None, question: str, state: Any | None) -> list[str] | None:
    if include or state is None:
        return include

    history_modules = [name for name in getattr(state, "modules", ()) if isinstance(name, str) and name]
    if not history_modules:
        return include

    if not _is_analysis_follow_up(question, state):
        return include

    return history_modules


def _is_analysis_follow_up(question: str, state: Any | None) -> bool:
    if state is None or getattr(state, "dialogue_mode", "") != "follow_up":
        return False
    if not getattr(state, "modules", ()):
        return False

    lowered = question.strip().lower()
    return any(keyword in lowered for keyword in _FOLLOW_UP_PERIOD_HINTS) or lowered.startswith(_FOLLOW_UP_PREFIXES)


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


def _enrich_with_guide(result: dict[str, str]) -> dict[str, str]:
    """설정 관련 에러에 guide 메시지를 추가."""
    if result.get("action") in ("config", "install", "login", "relogin"):
        try:
            from dartlab.core.ai.guide import no_provider_message

            result["guide"] = no_provider_message()
        except ImportError:
            pass
    return result


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
    report_mode: bool = False,
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
        stock_id = getattr(company, "stockCode", getattr(company, "ticker", "")) if company else None
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
            company,
            question,
            provider=provider,
            role=role,
            model=model,
            api_key=api_key,
            base_url=base_url,
            include=include,
            exclude=exclude,
            use_tools=use_tools,
            max_turns=max_turns,
            max_tools=max_tools,
            reflect=reflect,
            report_mode=report_mode,
            snapshot=snapshot,
            auto_snapshot=auto_snapshot,
            focus_context=focus_context,
            diff_context=diff_context,
            auto_diff=auto_diff,
            history=history,
            history_messages=history_messages,
            view_context=view_context,
            dialogue_policy=dialogue_policy,
            conversation_meta=conversation_meta,
            question_types=question_types,
            validate=validate,
            detect_navigate=detect_navigate,
            emit_system_prompt=emit_system_prompt,
            _full_response_parts=full_response_parts,
            _done_payload=done_payload,
            _included_tables=included_tables,
            **kwargs,
        )
    except (
        AttributeError,
        ConnectionError,
        FileNotFoundError,
        ImportError,
        KeyError,
        OSError,
        PermissionError,
        RuntimeError,
        TimeoutError,
        TypeError,
        ValueError,
    ) as e:
        yield AnalysisEvent("error", _enrich_with_guide(_classify_error(e)))

    # ── 후처리: navigate ui_action ──
    if detect_navigate and company is not None:
        nav_event = _detect_navigate_action(company, question)
        if nav_event:
            yield nav_event

    # ── 후처리: validation ──
    if validate and company is not None and full_response_parts and _should_run_validation(included_tables):
        val_event = _run_validation(company, full_response_parts)
        if val_event:
            yield val_event

    # ── 후처리: auto-artifact injection ──
    if company is not None:
        _q_type = done_payload.get("_q_type")
        _tc_names = done_payload.pop("_tool_call_names", [])
        done_payload.pop("_q_type", None)
        for art_event in autoInjectArtifacts(company, _q_type, _tc_names):
            yield art_event

    # ── 후처리: plugin hints ──
    if question:
        from dartlab.core.plugins import get_loaded_plugins
        from dartlab.engines.ai.runtime.plugin_hints import (
            detect_plugin_hints,
            format_plugin_hints,
        )

        loaded_names = [p.name for p in get_loaded_plugins()]
        hints = detect_plugin_hints(question, loaded_names)
        if hints:
            done_payload["pluginHints"] = hints
            hint_text = format_plugin_hints(hints)
            if hint_text:
                done_payload["pluginHintsText"] = hint_text

    # ── Done 이벤트 ──
    done_payload.setdefault("includedModules", included_tables)
    yield AnalysisEvent("done", done_payload)


def _analyze_inner(
    company: Any | None,
    question: str,
    *,
    provider: str | None,
    role: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    include: list[str] | None,
    exclude: list[str] | None,
    use_tools: bool,
    max_turns: int,
    max_tools: int | None,
    reflect: bool,
    report_mode: bool,
    snapshot: dict | None,
    auto_snapshot: bool,
    focus_context: str | None,
    diff_context: str | None,
    auto_diff: bool,
    history: list | None,
    history_messages: list[dict] | None,
    view_context: dict | None,
    dialogue_policy: str | None,
    conversation_meta: dict | None,
    question_types: tuple[str, ...],
    validate: bool,
    detect_navigate: bool,
    emit_system_prompt: bool,
    _full_response_parts: list[str],
    _done_payload: dict[str, Any],
    _included_tables: list[str],
    **kwargs: Any,
) -> Generator[AnalysisEvent, None, None]:
    """analyze() 본체 — 에러 핸들링은 외부에서."""
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.context.dartOpenapi import (
        buildDartFilingPrefetch,
        buildMissingDartKeyUiAction,
    )
    from dartlab.engines.ai.providers import create_provider

    # ── report_mode 강제 설정 ──
    if report_mode:
        context_tier_override = "full"
        max_turns = max(max_turns, 10)
    else:
        context_tier_override = None

    # ── 1. Config 해석 ──
    config_ = get_config(role=role)
    overrides = {
        k: v
        for k, v in {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            **kwargs,
        }.items()
        if v is not None
    }
    if overrides:
        config_ = config_.merge(overrides)

    resolved_provider = config_.provider
    context_tier = context_tier_override or _resolve_context_tier(resolved_provider, use_tools)
    is_compact = context_tier != "full"

    corp_name = getattr(company, "corpName", "Unknown") if company else None
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", "")) if company else None
    dataReadySummary = ""

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

    effective_include = _resolve_follow_up_include(include, question, state)
    if effective_include and effective_include != include:
        _done_payload["inheritedModules"] = list(effective_include)

    snapshotPolicy = _resolve_snapshot_policy(question, question_types, report_mode)
    _done_payload["route"] = snapshotPolicy["route"]

    # ── 4. Auto-snapshot ──
    if snapshot is None and auto_snapshot and company is not None and snapshotPolicy["enabled"]:
        from dartlab.engines.ai.context.snapshot import build_snapshot

        snapshot = build_snapshot(company, includeInsights=snapshotPolicy["includeInsights"])

    # ── 5. Auto focus/diff context ──
    if focus_context is None and state is not None and company is not None and state.topic:
        from dartlab.engines.ai.conversation.focus import build_focus_context

        focus_context = build_focus_context(company, state)

    if diff_context is None and auto_diff and company is not None and context_tier == "full":
        from dartlab.engines.ai.conversation.focus import build_diff_context

        diff_context = build_diff_context(company)

    # ── 6. Intent 분류 → light mode 감지 ──
    is_light = _should_use_light_mode(company, question, state, report_mode)
    dart_filing_prefetch = buildDartFilingPrefetch(question, company=company)

    # ── 7. Meta 이벤트 (데이터 신선도 포함) ──
    meta = conversation_meta or {}
    if corp_name:
        meta.setdefault("company", corp_name)
    if stock_id:
        meta.setdefault("stockCode", stock_id)
    if company is not None:
        if snapshotPolicy["includeDataDate"]:
            _dataDate = _extract_data_date(company)
            if _dataDate:
                meta.setdefault("dataDate", _dataDate)
        if stock_id:
            try:
                from dartlab.engines.ai.conversation.data_ready import formatDataReadyStatus

                dataReadySummary = formatDataReadyStatus(stock_id, detailed=False)
                _done_payload["dataReady"] = dataReadySummary
            except (AttributeError, ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError):
                dataReadySummary = ""
    yield AnalysisEvent("meta", meta)

    # ── 8. Snapshot 이벤트 ──
    if snapshot is not None:
        yield AnalysisEvent("snapshot", snapshot)

    if dart_filing_prefetch.matched and dart_filing_prefetch.needsKey:
        ui_action = dart_filing_prefetch.uiAction or buildMissingDartKeyUiAction()
        yield AnalysisEvent("ui_action", ui_action)
        yield AnalysisEvent(
            "context",
            {
                "module": "_dart_openapi_filings",
                "label": "OpenDART 키 설정 안내",
                "text": dart_filing_prefetch.message,
            },
        )
        _full_response_parts.append(dart_filing_prefetch.message)
        yield AnalysisEvent("chunk", {"text": dart_filing_prefetch.message})
        return

    # ── 9. Light mode 경로 ──
    if is_light:
        yield from _run_light_mode(
            company,
            question,
            config_,
            state,
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
            _module_name_to_section_keys,
            build_context_tiered,
        )

        modules_dict, included_tables_local, header_text = build_context_tiered(
            company,
            question,
            context_tier,
            effective_include,
            exclude,
        )
        _included_tables.extend(included_tables_local)

        # 모듈별 context 이벤트 yield
        for module_name, module_text in modules_dict.items():
            yield AnalysisEvent(
                "context",
                {
                    "module": module_name,
                    "label": _context_label(module_name),
                    "text": module_text,
                },
            )

        # context_text 조립
        context_parts = [header_text] if header_text else []
        if focus_context:
            context_parts.append(focus_context)
        for module_name in included_tables_local:
            for key in _module_name_to_section_keys(module_name):
                if key in modules_dict:
                    context_parts.append(modules_dict[key])
                    break
        for special_name in ("_response_contract", "_clarify"):
            if special_name in modules_dict:
                context_parts.append(modules_dict[special_name])
        if "_clarify" in modules_dict:
            _done_payload["clarificationNeeded"] = True
        context_text = "\n\n".join(context_parts)

    if dart_filing_prefetch.matched and dart_filing_prefetch.contextText:
        context_text = (
            f"{context_text}\n\n{dart_filing_prefetch.contextText}"
            if context_text
            else dart_filing_prefetch.contextText
        )
        yield AnalysisEvent(
            "context",
            {
                "module": "_dart_openapi_filings",
                "label": "OpenDART 공시목록",
                "text": dart_filing_prefetch.contextText,
            },
        )

    # focus/diff context 합류
    if focus_context and company is None:
        context_text = f"{context_text}\n\n{focus_context}" if context_text else focus_context
    if diff_context:
        context_text = f"{context_text}\n\n{diff_context}" if context_text else diff_context
        yield AnalysisEvent(
            "context",
            {
                "module": "_diff",
                "label": "공시 텍스트 변화 핫스팟",
                "text": diff_context,
            },
        )

    # Pipeline (full tier만)
    if context_tier == "full" and company is not None:
        from dartlab.engines.ai.runtime.pipeline import run_pipeline

        try:
            pipeline_result = run_pipeline(company, question, _included_tables)
        except (ValueError, TypeError, AttributeError, KeyError, FileNotFoundError, OSError) as e:
            import logging

            logging.getLogger(__name__).debug("pipeline failed: %s", e)
            pipeline_result = ""
        if pipeline_result:
            context_text = context_text + pipeline_result

    # ── 11. 프롬프트 조립 ──
    from dartlab.engines.ai.conversation.prompts import (
        _classify_question,
        build_system_prompt_parts,
    )

    sector = None
    if company is not None:
        from dartlab.engines.ai.context.builder import _get_sector

        sector = _get_sector(company)

    q_type = _classify_question(question)
    _done_payload["_q_type"] = q_type
    _done_payload["_tool_call_names"] = []
    company_market = getattr(company, "market", "KR") if company else "KR"
    allow_tool_guidance = use_tools and resolved_provider in {"openai", "ollama", "custom"}
    static_part, dynamic_part = build_system_prompt_parts(
        config_.system_prompt,
        included_modules=_included_tables,
        sector=sector,
        question_type=q_type,
        question_types=list(question_types) if question_types else None,
        compact=is_compact,
        report_mode=report_mode,
        market=company_market,
        allow_tools=allow_tool_guidance,
    )

    if dataReadySummary:
        dataReadyBlock = f"데이터 가용성\n{dataReadySummary}"
        dynamic_part = f"{dynamic_part}\n\n{dataReadyBlock}" if dynamic_part else dataReadyBlock

    if dialogue_policy:
        dynamic_part = dynamic_part + "\n\n" + dialogue_policy if dynamic_part else dialogue_policy

    system = static_part + "\n" + dynamic_part if dynamic_part else static_part

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": system})

    # ── 12. Messages 조립 (Claude prompt caching 적용) ──
    # Claude provider면 정적/동적 분리 → cache_control 블록으로 전달
    if resolved_provider == "claude" and dynamic_part:
        system_content: str | list[dict] = [
            {"type": "text", "text": static_part, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": dynamic_part},
        ]
    else:
        system_content = system
    messages: list[dict] = [{"role": "system", "content": system_content}]

    if history_messages:
        messages.extend(history_messages)

    user_content = f"{context_text}\n\n---\n\n질문: {question}" if context_text else question

    # 플러그인 힌트를 LLM context에 주입 (AI가 자연스럽게 안내)
    if question:
        from dartlab.core.plugins import get_loaded_plugins
        from dartlab.engines.ai.runtime.plugin_hints import (
            detect_plugin_hints,
            format_plugin_hints,
        )

        _loaded = [p.name for p in get_loaded_plugins()]
        _hints = detect_plugin_hints(question, _loaded)
        if _hints:
            _hint_ctx = format_plugin_hints(_hints)
            if _hint_ctx:
                user_content += f"\n\n---\n{_hint_ctx}"

    messages.append({"role": "user", "content": user_content})

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": system, "userContent": user_content})

    # ── 13. LLM 호출 ──
    llm = create_provider(config_)

    tool_capable = (
        use_tools
        and getattr(llm, "supports_native_tools", False)
        and hasattr(llm, "complete_with_tools")
    )
    use_guided = (
        not tool_capable
        and is_compact
        and company is not None
        and hasattr(llm, "complete_json")
    )

    if tool_capable:
        if max_tools is None and resolved_provider == "ollama":
            max_tools = 10
        effective_turns = max(max_turns, _estimate_max_turns(question, q_type or ""))
        for _ev in _run_agent(
            llm,
            messages,
            company,
            question,
            max_turns=effective_turns,
            max_tools=max_tools,
            q_type=q_type,
            _full_response_parts=_full_response_parts,
        ):
            if _ev.kind == "tool_call" and isinstance(_ev.data, dict):
                _done_payload["_tool_call_names"].append(_ev.data.get("name", ""))
            yield _ev
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
        includedEvidence = _build_included_evidence(_included_tables)
        meta_update: dict[str, Any] = {
            "includedModules": _included_tables,
            "includedModuleLabels": [item["label"] for item in includedEvidence],
            "includedEvidence": includedEvidence,
        }
        _done_payload["includedEvidence"] = includedEvidence
        if not is_compact and company is not None:
            from dartlab.engines.ai.context.builder import detect_year_range

            year_range = detect_year_range(company, _included_tables)
            if year_range:
                meta_update["dataYearRange"] = year_range
        yield AnalysisEvent("meta", meta_update)
