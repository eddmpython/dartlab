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

from dartlab import Company

from .cache import company_cache
from .chat import (
    build_diff_context,
    build_dynamic_chat_prompt,
    build_focus_context,
    build_history_messages,
    build_snapshot,
)
from .dialogue import build_conversation_state, build_dialogue_policy, conversation_state_to_meta, detect_viewer_intent
from .models import AskRequest
from .resolve import has_analysis_intent


async def stream_ask(c: Company | None, req: AskRequest, *, not_found_msg: str | None = None):
    """SSE 스트리밍 generator.

    이벤트 흐름:
            meta → snapshot → context (모듈별, 여러 번) → chunk... → done
            tool_call/tool_result 이벤트는 agent_loop 사용 시 추가
    """
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.providers import create_provider

    state = build_conversation_state(
        req.question,
        history=req.history,
        company=c,
        view_context=req.viewContext,
    )
    focus_context = await asyncio.to_thread(build_focus_context, c, state) if c is not None else None
    diff_context = await asyncio.to_thread(build_diff_context, c) if c is not None else None

    if not_found_msg:
        yield {
            "event": "meta",
            "data": json.dumps(conversation_state_to_meta(state), ensure_ascii=False),
        }
        yield {
            "event": "chunk",
            "data": json.dumps({"text": not_found_msg}, ensure_ascii=False),
        }
        yield {"event": "done", "data": "{}"}
        return

    yield {
        "event": "meta",
        "data": json.dumps(conversation_state_to_meta(state), ensure_ascii=False),
    }

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
        history_msgs = build_history_messages(req.history)

        if c and not has_analysis_intent(state.question):
            cached = company_cache.get(c.stockCode)
            if cached:
                snapshot = cached[1]
            else:
                snapshot = await asyncio.to_thread(build_snapshot, c)
                company_cache.put(c.stockCode, c, snapshot)
            if snapshot:
                yield {
                    "event": "snapshot",
                    "data": json.dumps(snapshot, ensure_ascii=False),
                }
            if focus_context:
                yield {
                    "event": "context",
                    "data": json.dumps(
                        {
                            "module": "_focus_topic",
                            "label": f"현재 섹션: {state.topic_label or state.topic}",
                            "text": focus_context,
                        },
                        ensure_ascii=False,
                    ),
                }

            light_prompt = (
                build_dynamic_chat_prompt(state) + f"\n\n## 현재 대화 종목\n"
                f"사용자가 **{c.corpName}** ({c.stockCode})에 대해 이야기하고 있습니다.\n"
                f"아직 구체적 분석 요청은 아닙니다. 가볍게 대화하되, "
                f"분석이 필요하면 어떤 분석을 원하는지 물어보세요.\n"
                f"예: '어떤 분석을 원하시나요? 재무 건전성, 수익성, 배당, 종합 분석 등을 해드릴 수 있습니다.'"
            )
            messages = [{"role": "system", "content": light_prompt}]
            messages.extend(history_msgs)
            user_text = state.question
            if focus_context:
                user_text = f"{focus_context}\n\n---\n\n질문: {state.question}"
            messages.append({"role": "user", "content": user_text})

            yield {
                "event": "system_prompt",
                "data": json.dumps({"text": light_prompt}, ensure_ascii=False),
            }

            llm = create_provider(config_)

            def _gen_light():
                yield from llm.stream(messages)

            gen = _gen_light()
            while True:
                chunk = await asyncio.to_thread(next, gen, None)
                if chunk is None:
                    break
                yield {
                    "event": "chunk",
                    "data": json.dumps({"text": chunk}, ensure_ascii=False),
                }
            yield {"event": "done", "data": "{}"}
            return

        elif c:
            from dartlab.engines.ai.context import (
                _get_sector,
                build_context_by_module,
                detect_year_range,
            )
            from dartlab.engines.ai.metadata import MODULE_META
            from dartlab.engines.ai.prompts import _classify_question_multi, build_system_prompt

            cached = company_cache.get(c.stockCode)
            if cached:
                snapshot = cached[1]
            else:
                snapshot = await asyncio.to_thread(build_snapshot, c)
                company_cache.put(c.stockCode, c, snapshot)
            if snapshot:
                yield {
                    "event": "snapshot",
                    "data": json.dumps(snapshot, ensure_ascii=False),
                }

            modules_dict, included_tables, header_text = await asyncio.to_thread(
                build_context_by_module,
                c,
                state.question,
                req.include,
                req.exclude,
                use_compact,
            )

            if "_full" in modules_dict:
                context_text = modules_dict["_full"]
                if focus_context:
                    context_text = focus_context + "\n\n" + context_text
                    yield {
                        "event": "context",
                        "data": json.dumps(
                            {
                                "module": "_focus_topic",
                                "label": f"현재 섹션: {state.topic_label or state.topic}",
                                "text": focus_context,
                            },
                            ensure_ascii=False,
                        ),
                    }
                yield {
                    "event": "context",
                    "data": json.dumps(
                        {
                            "module": "_full",
                            "label": "전체 데이터",
                            "text": context_text,
                        },
                        ensure_ascii=False,
                    ),
                }
            else:
                for mod_name in included_tables:
                    mod_text = modules_dict.get(mod_name, "")
                    if not mod_text:
                        continue
                    meta_info = MODULE_META.get(mod_name)
                    label = meta_info.label if meta_info else mod_name
                    yield {
                        "event": "context",
                        "data": json.dumps(
                            {
                                "module": mod_name,
                                "label": label,
                                "text": mod_text,
                            },
                            ensure_ascii=False,
                        ),
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
                        "data": json.dumps(
                            {
                                "module": "_focus_topic",
                                "label": f"현재 섹션: {state.topic_label or state.topic}",
                                "text": focus_context,
                            },
                            ensure_ascii=False,
                        ),
                    }

            if not use_compact:
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
                    "data": json.dumps(
                        {
                            "module": "_diff",
                            "label": "공시 텍스트 변화 핫스팟",
                            "text": diff_context,
                        },
                        ensure_ascii=False,
                    ),
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
                "data": json.dumps(meta_payload, ensure_ascii=False),
            }

            sector = _get_sector(c)
            question_types = _classify_question_multi(state.question)
            system = build_system_prompt(
                config_.system_prompt,
                included_modules=included_tables,
                sector=sector,
                question_types=state.question_types or question_types,
                compact=use_compact,
            )
            system = system + "\n\n" + build_dialogue_policy(state)
            messages = [{"role": "system", "content": system}]
            messages.extend(history_msgs)
            user_content = f"{context_text}\n\n---\n\n질문: {state.question}"
            messages.append({"role": "user", "content": user_content})

            yield {
                "event": "system_prompt",
                "data": json.dumps({"text": system, "userContent": user_content}, ensure_ascii=False),
            }
        else:
            chat_prompt = build_dynamic_chat_prompt(state)
            messages = [{"role": "system", "content": chat_prompt}]
            messages.extend(history_msgs)
            messages.append({"role": "user", "content": state.question})

            yield {
                "event": "system_prompt",
                "data": json.dumps({"text": chat_prompt}, ensure_ascii=False),
            }

        llm = create_provider(config_)

        use_guided = use_compact and c is not None and hasattr(llm, "complete_json")
        use_tools = not use_guided and hasattr(llm, "complete_with_tools")

        full_response_parts: list[str] = []
        done_payload: dict[str, Any] = {}

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
                    "data": json.dumps({"text": chunk_text}, ensure_ascii=False),
                }
                if i < len(paragraphs) - 1:
                    await asyncio.sleep(0.02)

        elif use_tools:
            from dartlab.engines.ai.agent import agent_loop_stream, build_agent_system_addition
            from dartlab.engines.ai.tools_registry import build_tool_runtime

            tool_runtime = build_tool_runtime(c, name="stream-agent")
            messages[0]["content"] += build_agent_system_addition(tool_runtime)

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

            def _run_agent_stream():
                for chunk in agent_loop_stream(
                    llm,
                    messages,
                    c,
                    max_turns=5,
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

            while True:
                ev = await queue.get()
                if ev["event"] == "_done":
                    break
                if ev["event"] == "chunk":
                    text = ev["text"]
                    full_response_parts.append(text)
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"text": text}, ensure_ascii=False),
                    }
                else:
                    yield {
                        "event": ev["event"],
                        "data": json.dumps(ev, ensure_ascii=False),
                    }

            await task
        else:

            def _gen():
                yield from llm.stream(messages)

            gen = _gen()
            while True:
                chunk = await asyncio.to_thread(next, gen, None)
                if chunk is None:
                    break
                full_response_parts.append(chunk)
                yield {
                    "event": "chunk",
                    "data": json.dumps({"text": chunk}, ensure_ascii=False),
                }

        if c and full_response_parts:
            from dartlab.engines.ai.prompts import extract_response_meta

            full_text = "".join(full_response_parts)
            response_meta = extract_response_meta(full_text)
            if response_meta.get("grade") or response_meta.get("has_conclusion"):
                done_payload["responseMeta"] = response_meta

    except (
        AttributeError,
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
        error_payload: dict[str, Any] = {"error": str(e)}
        if isinstance(e, FileNotFoundError):
            error_payload["action"] = "install"
        elif isinstance(e, PermissionError):
            error_payload["action"] = "login"

        yield {
            "event": "error",
            "data": json.dumps(error_payload, ensure_ascii=False),
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
                "data": json.dumps(nav_payload, ensure_ascii=False),
            }

    yield {"event": "done", "data": json.dumps(done_payload, ensure_ascii=False)}
