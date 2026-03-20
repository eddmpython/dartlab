"""SSE 스트리밍 generator — 분석/대화 응답 생성.

[최우선 UX 원칙] 데이터 투명성 — 절대 제거 금지

이벤트 흐름의 모든 단계는 UI에서 뱃지/카드/모달로 투명하게 노출된다.
LLM이 보는 데이터, 시스템이 제공하는 컨텍스트는 반드시 SSE 이벤트로 전송하여
사용자가 실시간으로 확인할 수 있어야 한다.

이벤트 흐름:
  meta          → 회사, 종목코드, 포함 모듈, 연도 범위
  snapshot      → 핵심 수치 (주가, 시총, PER 등)
  context       → 모듈별 데이터 (IS, BS, CF, ratios, dividend 등)
  system_prompt → 시스템 프롬프트 + LLM에 전달되는 전체 user content
  tool_call     → 에이전트 도구 호출
  tool_result   → 도구 실행 결과
  chunk         → LLM 응답 텍스트 (실시간 스트리밍)
  done          → 완료 (responseMeta 포함)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import orjson

from dartlab import Company

from .cache import company_cache
from .chat import (
    build_diff_context,
    build_dynamic_chat_prompt,
    build_focus_context,
    build_history_messages,
    build_snapshot,
    compress_history,
)
from .dialogue import build_conversation_state, build_dialogue_policy, conversation_state_to_meta, detect_viewer_intent
from .models import AskRequest
from .resolve import _is_pure_conversation, has_analysis_intent


async def _stream_llm_chunks(llm, messages: list[dict]):
    """LLM stream을 큐 기반 async generator로 변환.

    별도 스레드에서 generator를 실행하고 큐에 넣어
    매 chunk마다 스레드 전환하는 오버헤드를 줄인다.
    """
    import queue as _queue_mod

    sync_queue: _queue_mod.Queue = _queue_mod.Queue(maxsize=64)
    _SENTINEL = object()

    def _run():
        try:
            for chunk in llm.stream(messages):
                sync_queue.put(chunk)  # blocking put — 배압 제어
        except Exception as exc:
            sync_queue.put(exc)
        finally:
            sync_queue.put(_SENTINEL)

    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, _run)

    while True:
        item = await asyncio.to_thread(sync_queue.get)
        if item is _SENTINEL:
            break
        if isinstance(item, Exception):
            raise item
        yield item

    await task


async def _get_snapshot(c: Company) -> dict | None:
    """캐시 우선 snapshot 조회 (중복 제거 헬퍼)."""
    cached = company_cache.get(c.stockCode)
    if cached:
        return cached[1]
    snapshot = await asyncio.to_thread(build_snapshot, c)
    company_cache.put(c.stockCode, c, snapshot)
    return snapshot


async def stream_ask(c: Company | None, req: AskRequest, *, not_found_msg: str | None = None):
    """SSE 스트리밍 generator.

    이벤트 흐름:
            meta → snapshot → context (모듈별, 여러 번) → chunk... → done
            tool_call/tool_result 이벤트는 agent_loop 사용 시 추가
    """
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.providers import create_provider

    # 순수 대화이면 viewContext 무시 — meta에 이전 회사가 찍히는 것 방지
    effective_view_context = None if _is_pure_conversation(req.question) else req.viewContext

    state = build_conversation_state(
        req.question,
        history=req.history,
        company=c,
        view_context=effective_view_context,
    )
    if c is not None:
        focus_context, diff_context = await asyncio.gather(
            asyncio.to_thread(build_focus_context, c, state),
            asyncio.to_thread(build_diff_context, c),
        )
    else:
        focus_context, diff_context = None, None

    if not_found_msg:
        yield {
            "event": "meta",
            "data": orjson.dumps(conversation_state_to_meta(state)).decode(),
        }
        yield {
            "event": "chunk",
            "data": orjson.dumps({"text": not_found_msg}).decode(),
        }
        yield {"event": "done", "data": "{}"}
        return

    yield {
        "event": "meta",
        "data": orjson.dumps(conversation_state_to_meta(state)).decode(),
    }

    done_payload: dict[str, Any] = {}

    try:
        config_ = get_config()
        overrides: dict[str, Any] = {}
        if req.provider:
            overrides["provider"] = req.provider
        if req.model:
            overrides["model"] = req.model
        if req.api_key:
            overrides["api_key"] = req.api_key
        if req.base_url:
            overrides["base_url"] = req.base_url
        if overrides:
            config_ = config_.merge(overrides)

        use_compact = config_.provider in ("ollama", "codex", "claude-code")
        # tool calling 가능 여부에 따라 context tier 결정
        _tool_capable_providers = {"openai", "claude", "chatgpt", "ollama"}
        use_tools_tier = config_.provider in _tool_capable_providers and not (
            use_compact and config_.provider != "ollama"
        )
        context_tier = "skeleton" if use_tools_tier else ("focused" if use_compact else "full")
        compressed = compress_history(req.history)
        history_msgs = build_history_messages(compressed)

        if c and not has_analysis_intent(state.question):
            snapshot = await _get_snapshot(c)
            if snapshot:
                yield {
                    "event": "snapshot",
                    "data": orjson.dumps(snapshot).decode(),
                }
            if focus_context:
                yield {
                    "event": "context",
                    "data": orjson.dumps(
                        {
                            "module": "_focus_topic",
                            "label": f"현재 섹션: {state.topic_label or state.topic}",
                            "text": focus_context,
                        },
                    ).decode(),
                }

            # Light mode용 간략 회사 컨텍스트 (topics + insights 요약)
            light_company_ctx = "\n\n## 현재 대화 종목\n"
            light_company_ctx += f"사용자가 **{c.corpName}** ({c.stockCode})에 대해 이야기하고 있습니다.\n"
            # insights 등급 1줄 요약
            try:
                from dartlab.engines.insight.pipeline import analyze as _light_analyze

                _light_result = _light_analyze(c.stockCode, company=c)
                if _light_result is not None:
                    _grades = _light_result.grades()
                    _grade_str = " / ".join(
                        f"{lbl}:{_grades.get(k, 'N')}"
                        for k, lbl in [
                            ("performance", "실적"),
                            ("profitability", "수익성"),
                            ("health", "건전성"),
                            ("cashflow", "CF"),
                            ("governance", "지배구조"),
                            ("risk", "리스크"),
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
                _topics = list(getattr(c, "topics", None) or [])[:10]
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
            messages = [{"role": "system", "content": light_prompt}]
            messages.extend(history_msgs)
            user_text = state.question
            if focus_context:
                user_text = f"{focus_context}\n\n---\n\n질문: {state.question}"
            messages.append({"role": "user", "content": user_text})

            yield {
                "event": "system_prompt",
                "data": orjson.dumps({"text": light_prompt}).decode(),
            }

            llm = create_provider(config_)

            async for chunk in _stream_llm_chunks(llm, messages):
                yield {
                    "event": "chunk",
                    "data": orjson.dumps({"text": chunk}).decode(),
                }
            yield {"event": "done", "data": "{}"}
            return

        elif c:
            from dartlab.engines.ai.context import (
                _get_sector,
                build_context_tiered,
                detect_year_range,
            )
            from dartlab.engines.ai.metadata import MODULE_META
            from dartlab.engines.ai.prompts import _classify_question_multi, build_system_prompt

            snapshot = await _get_snapshot(c)
            if snapshot:
                yield {
                    "event": "snapshot",
                    "data": orjson.dumps(snapshot).decode(),
                }

            modules_dict, included_tables, header_text = await asyncio.to_thread(
                build_context_tiered,
                c,
                state.question,
                context_tier,
                req.include,
                req.exclude,
            )

            if "_skeleton" in modules_dict:
                context_text = modules_dict["_skeleton"]
                if focus_context:
                    context_text = focus_context + "\n\n" + context_text
                yield {
                    "event": "context",
                    "data": orjson.dumps(
                        {
                            "module": "_skeleton",
                            "label": "핵심 요약 (도구로 상세 조회)",
                            "text": context_text,
                        },
                    ).decode(),
                }
            elif "_full" in modules_dict:
                context_text = modules_dict["_full"]
                if focus_context:
                    context_text = focus_context + "\n\n" + context_text
                    yield {
                        "event": "context",
                        "data": orjson.dumps(
                            {
                                "module": "_focus_topic",
                                "label": f"현재 섹션: {state.topic_label or state.topic}",
                                "text": focus_context,
                            },
                        ).decode(),
                    }
                yield {
                    "event": "context",
                    "data": orjson.dumps(
                        {
                            "module": "_full",
                            "label": "전체 데이터",
                            "text": context_text,
                        },
                    ).decode(),
                }
                # _full fallback에서도 topics/insights를 별도 이벤트로 전송
                for _extra_key, _extra_label in (("_topics", "공시 topic 목록"), ("_insights", "인사이트 등급")):
                    if _extra_key in modules_dict:
                        context_text = context_text + "\n\n" + modules_dict[_extra_key]
                        yield {
                            "event": "context",
                            "data": orjson.dumps(
                                {"module": _extra_key, "label": _extra_label, "text": modules_dict[_extra_key]},
                            ).decode(),
                        }
            else:
                _EXTRA_LABELS = {"_topics": "공시 topic 목록", "_insights": "인사이트 등급"}
                for mod_name in included_tables:
                    mod_text = modules_dict.get(mod_name, "")
                    if not mod_text:
                        continue
                    meta_info = MODULE_META.get(mod_name)
                    label = _EXTRA_LABELS.get(mod_name) or (meta_info.label if meta_info else mod_name)
                    yield {
                        "event": "context",
                        "data": orjson.dumps(
                            {
                                "module": mod_name,
                                "label": label,
                                "text": mod_text,
                            },
                        ).decode(),
                    }
                parts = [header_text] if header_text else []
                if focus_context:
                    parts.append(focus_context)
                for name in included_tables:
                    if name in modules_dict:
                        parts.append(modules_dict[name])
                context_text = "\n".join(parts)
                if focus_context:
                    yield {
                        "event": "context",
                        "data": orjson.dumps(
                            {
                                "module": "_focus_topic",
                                "label": f"현재 섹션: {state.topic_label or state.topic}",
                                "text": focus_context,
                            },
                        ).decode(),
                    }

            if context_tier == "full":
                from dartlab.engines.ai.pipeline import run_pipeline

                pipeline_result = await asyncio.to_thread(
                    run_pipeline,
                    c,
                    req.question,
                    included_tables,
                )
                if pipeline_result:
                    context_text = context_text + pipeline_result

            if diff_context:
                context_text = context_text + "\n\n" + diff_context
                yield {
                    "event": "context",
                    "data": orjson.dumps(
                        {
                            "module": "_diff",
                            "label": "공시 텍스트 변화 핫스팟",
                            "text": diff_context,
                        },
                    ).decode(),
                }

            meta_payload: dict[str, Any] = {
                **conversation_state_to_meta(state),
                "includedModules": included_tables,
            }
            if not use_compact:
                year_range = await asyncio.to_thread(detect_year_range, c, included_tables)
                if year_range:
                    meta_payload["dataYearRange"] = year_range
            yield {
                "event": "meta",
                "data": orjson.dumps(meta_payload).decode(),
            }

            sector = _get_sector(c)
            question_types = _classify_question_multi(state.question)
            system = build_system_prompt(
                config_.system_prompt,
                included_modules=included_tables,
                sector=sector,
                question_types=state.question_types or question_types,
                compact=context_tier != "full",
            )
            system = system + "\n\n" + build_dialogue_policy(state)
            messages = [{"role": "system", "content": system}]
            messages.extend(history_msgs)
            user_content = f"{context_text}\n\n---\n\n질문: {state.question}"
            messages.append({"role": "user", "content": user_content})

            yield {
                "event": "system_prompt",
                "data": orjson.dumps({"text": system, "userContent": user_content}).decode(),
            }
        else:
            chat_prompt = build_dynamic_chat_prompt(state)
            messages = [{"role": "system", "content": chat_prompt}]
            messages.extend(history_msgs)
            messages.append({"role": "user", "content": state.question})

            yield {
                "event": "system_prompt",
                "data": orjson.dumps({"text": chat_prompt}).decode(),
            }

        llm = create_provider(config_)

        use_guided = use_compact and c is not None and hasattr(llm, "complete_json")
        use_tools = not use_guided and hasattr(llm, "complete_with_tools")

        full_response_parts: list[str] = []

        if use_guided:
            from dartlab.engines.ai.prompts import GUIDED_SCHEMA, guided_json_to_markdown

            resp = await asyncio.to_thread(llm.complete_json, messages, GUIDED_SCHEMA)
            raw_json = resp.answer
            try:
                parsed = json.loads(raw_json)
                md_text = guided_json_to_markdown(parsed)
                done_payload["guidedRaw"] = parsed
                if parsed.get("grade"):
                    done_payload["responseMeta"] = {
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

            full_response_parts.append(md_text)
            paragraphs = md_text.split("\n\n")
            for i, para in enumerate(paragraphs):
                chunk_text = para if i == len(paragraphs) - 1 else para + "\n\n"
                yield {
                    "event": "chunk",
                    "data": orjson.dumps({"text": chunk_text}).decode(),
                }
                if i < len(paragraphs) - 1:
                    await asyncio.sleep(0.02)

        elif use_tools:
            from dartlab.engines.ai.agent import agent_loop_stream, build_agent_system_addition
            from dartlab.engines.ai.tools_registry import build_tool_runtime

            tool_runtime = build_tool_runtime(c, name="stream-agent")
            messages[0]["content"] += build_agent_system_addition(tool_runtime)

            # 소형 모델(Ollama)은 도구 10개 제한
            _agent_max_tools: int | None = 10 if config_.provider == "ollama" else None

            queue: asyncio.Queue = asyncio.Queue(maxsize=256)
            loop = asyncio.get_event_loop()

            def _enqueue_event(payload: dict[str, Any]) -> None:
                try:
                    if queue.full():
                        if payload.get("event") in {"chunk", "_done"}:
                            try:
                                queue.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                        else:
                            return
                    queue.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

            def _on_tool_call(name: str, args: dict):
                loop.call_soon_threadsafe(
                    _enqueue_event,
                    {"event": "tool_call", "name": name, "arguments": args},
                )

            def _on_tool_result(name: str, result: str):
                loop.call_soon_threadsafe(
                    _enqueue_event,
                    {"event": "tool_result", "name": name, "result": result[:2000]},
                )
                # create_chart 도구 결과에서 ChartSpec 추출 → 별도 chart 이벤트
                if name == "create_chart":
                    try:
                        parsed = json.loads(result)
                        charts = parsed.get("charts")
                        if charts:
                            loop.call_soon_threadsafe(
                                _enqueue_event,
                                {"event": "chart", "charts": charts},
                            )
                    except (json.JSONDecodeError, TypeError, KeyError):
                        pass

            def _run_agent_stream():
                for chunk in agent_loop_stream(
                    llm,
                    messages,
                    c,
                    max_turns=5,
                    max_tools=_agent_max_tools,
                    runtime=tool_runtime,
                    on_tool_call=_on_tool_call,
                    on_tool_result=_on_tool_result,
                ):
                    loop.call_soon_threadsafe(
                        _enqueue_event,
                        {"event": "chunk", "text": chunk},
                    )
                loop.call_soon_threadsafe(
                    _enqueue_event,
                    {"event": "_done"},
                )

            task = asyncio.ensure_future(asyncio.to_thread(_run_agent_stream))

            try:
                while True:
                    ev = await queue.get()
                    if ev["event"] == "_done":
                        break
                    if ev["event"] == "chunk":
                        text = ev["text"]
                        full_response_parts.append(text)
                        yield {
                            "event": "chunk",
                            "data": orjson.dumps({"text": text}).decode(),
                        }
                    else:
                        yield {
                            "event": ev["event"],
                            "data": orjson.dumps(ev).decode(),
                        }

                await task
            except BaseException:
                task.cancel()
                raise
        else:
            async for chunk in _stream_llm_chunks(llm, messages):
                full_response_parts.append(chunk)
                yield {
                    "event": "chunk",
                    "data": orjson.dumps({"text": chunk}).decode(),
                }

        if c and full_response_parts:
            from dartlab.engines.ai.prompts import extract_response_meta

            full_text = "".join(full_response_parts)
            response_meta = extract_response_meta(full_text)
            if response_meta.get("grade") or response_meta.get("has_conclusion"):
                done_payload["responseMeta"] = response_meta

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
        import logging

        logger = logging.getLogger(__name__)
        logger.warning("stream_ask error: %s: %s", type(e).__name__, e)
        from dartlab.server import _sanitize_error

        error_payload: dict[str, Any] = {"error": _sanitize_error(e)}
        if isinstance(e, FileNotFoundError):
            error_payload["action"] = "install"
        elif isinstance(e, PermissionError):
            error_payload["action"] = "login"

        # OAuth GPT 에러 — 사용자에게 구체적 action 전달
        err_type = type(e).__name__
        if err_type == "ChatGPTOAuthError":
            err_str = str(e).lower()
            if "token" in err_str or "expire" in err_str or "login" in err_str:
                error_payload["action"] = "relogin"
                error_payload["error"] = "ChatGPT 인증이 만료되었습니다. 다시 로그인해주세요."
            elif "rate" in err_str or "limit" in err_str:
                error_payload["action"] = "rate_limit"
                error_payload["error"] = "ChatGPT 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요."
            else:
                error_payload["action"] = "relogin"
                error_payload["error"] = f"ChatGPT 연결 오류: {_sanitize_error(e)}"
        elif err_type == "OpenAIError" or "api_key" in str(e).lower():
            error_payload["action"] = "config"
            error_payload["error"] = "AI 설정이 필요합니다. API 키를 확인하거나 다른 provider를 선택해주세요."

        yield {
            "event": "error",
            "data": orjson.dumps(error_payload).decode(),
        }

    # "보여줘" 의도 감지 → viewer_navigate SSE 이벤트
    if c is not None:
        company_topics = None
        try:
            company_topics = list(getattr(c, "topics", None) or [])
        except (AttributeError, TypeError):
            pass
        viewer_intent = detect_viewer_intent(req.question, topics=company_topics)
        if viewer_intent is not None:
            nav_payload: dict[str, Any] = {"topic": viewer_intent.get("topic", "")}
            if state.stock_code:
                nav_payload["stockCode"] = state.stock_code
            if state.company:
                nav_payload["company"] = state.company
            yield {
                "event": "viewer_navigate",
                "data": orjson.dumps(nav_payload).decode(),
            }

    # Phase 5: 숫자 검증 — LLM 답변의 재무 수치를 실제 값과 대조
    if c and full_response_parts:
        try:
            from dartlab.engines.ai.validation import extract_numbers, validate_claims

            full_text = "".join(full_response_parts)
            claims = extract_numbers(full_text)
            if claims:
                vresult = await asyncio.to_thread(validate_claims, claims, c)
                if vresult.mismatches:
                    yield {
                        "event": "validation",
                        "data": orjson.dumps(
                            {
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
                            },
                        ).decode(),
                    }
        except (ImportError, AttributeError, TypeError, ValueError, OSError):
            pass

    yield {"event": "done", "data": orjson.dumps(done_payload).decode()}
