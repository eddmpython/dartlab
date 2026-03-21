"""SSE 스트리밍 generator — core.analyze() 이벤트 → SSE 변환.

[최우선 UX 원칙] 데이터 투명성 — 절대 제거 금지

모든 분석 로직은 engines/ai/core.py가 처리.
이 모듈은 이벤트를 SSE dict로 변환하는 thin adapter.

이벤트 흐름:
  meta          → 회사, 종목코드, 포함 모듈, 연도 범위
  snapshot      → 핵심 수치 (주가, 시총, PER 등)
  context       → 모듈별 데이터 (IS, BS, CF, ratios, dividend 등)
  system_prompt → 시스템 프롬프트 + LLM에 전달되는 전체 user content
  tool_call     → 에이전트 도구 호출
  tool_result   → 도구 실행 결과
  chart         → 차트 스펙
  ui_action     → canonical UI action
  chunk         → LLM 응답 텍스트 (실시간 스트리밍)
  validation    → 숫자 검증 결과
  done          → 완료 (responseMeta 포함)
  error         → 에러 + 사용자 행동 힌트
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import orjson

from dartlab import Company

from .cache import company_cache
from .models import AskRequest


@dataclass
class AnalysisStreamError(RuntimeError):
    """core.analyze() error event surfaced to server adapters."""

    message: str
    action: str = ""
    detail: str | None = None


async def stream_ask(c: Company | None, req: AskRequest, *, not_found_msg: str | None = None):
    """core.analyze() 이벤트 → SSE 변환.

    모든 분석 로직은 core.analyze()에 위임.
    이 함수는 snapshot 캐싱 + SSE 포맷 변환만 담당.
    """
    kwargs = await _build_kwargs(c, req, not_found_msg=not_found_msg)
    async for item in stream_analysis(c, req.question, **kwargs):
        yield item


async def stream_analysis(
    c: Company | None,
    question: str,
    **kwargs,
):
    """Generic core.analyze() → SSE adapter."""
    from dartlab.engines.ai.runtime.core import analyze

    async for event in _sync_gen_to_async(analyze, c, question, **kwargs):
        yield _sse(event.kind, event.data)


async def collect_analysis_text(
    c: Company | None,
    question: str,
    **kwargs,
) -> str:
    """Run core.analyze() and collect chunk text for non-stream HTTP endpoints."""
    from dartlab.engines.ai.runtime.core import analyze

    chunks: list[str] = []
    async for event in _sync_gen_to_async(analyze, c, question, **kwargs):
        if event.kind == "chunk":
            chunks.append(event.data.get("text", ""))
        elif event.kind == "error":
            raise AnalysisStreamError(
                event.data.get("error", "analysis error"),
                action=event.data.get("action", ""),
                detail=event.data.get("detail"),
            )
    return "".join(chunks)


async def _build_kwargs(
    c: Company | None,
    req: AskRequest,
    *,
    not_found_msg: str | None = None,
) -> dict:
    """AskRequest → core.analyze() kwargs 변환 + snapshot 캐싱."""
    kwargs: dict = {
        "provider": req.provider,
        "role": req.role,
        "model": req.model,
        "api_key": req.api_key,
        "base_url": req.base_url,
        "include": req.include,
        "exclude": req.exclude,
        "history": [h.model_dump() for h in req.history] if req.history else None,
        "view_context": req.viewContext.model_dump() if req.viewContext else None,
        "not_found_msg": not_found_msg,
    }

    # snapshot 캐시: 서버 세션에서 Company별 1회 계산
    if c is not None and not not_found_msg:
        from dartlab.engines.ai.context.snapshot import build_snapshot

        stock_id = getattr(c, "stockCode", getattr(c, "ticker", ""))
        cached = company_cache.get(stock_id)
        if cached:
            kwargs["snapshot"] = cached[1]
        else:
            snapshot = await asyncio.to_thread(build_snapshot, c)
            company_cache.put(stock_id, c, snapshot)
            kwargs["snapshot"] = snapshot
        kwargs["auto_snapshot"] = False

    return kwargs


def _sse(event: str, data: dict) -> dict:
    """이벤트 → SSE dict 변환."""
    return {"event": event, "data": orjson.dumps(data).decode()}


async def _sync_gen_to_async(gen_fn, *args, **kwargs):
    """동기 제너레이터 → async 큐 브릿지."""
    import queue as _queue_mod

    sync_queue: _queue_mod.Queue = _queue_mod.Queue(maxsize=64)
    _SENTINEL = object()

    def _run():
        try:
            for item in gen_fn(*args, **kwargs):
                sync_queue.put(item)
        except (OSError, RuntimeError, ValueError, TypeError, KeyError, StopIteration, AnalysisStreamError) as exc:
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
