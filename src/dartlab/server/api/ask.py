"""LLM 질문 엔드포인트 — api_ask, plain_chat."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

import dartlab
from dartlab import Company

from ..cache import company_cache
from ..models import AskRequest
from ..resolve import (
    ResolveResult,
    _collect_candidates,
    build_ambiguous_msg,
    build_not_found_msg,
    needs_match_verification,
    try_resolve_company,
    try_resolve_from_history,
    verify_match_with_llm,
)
from ..services.ai_analysis import run_plain_chat
from ..streaming import stream_ask
from .common import (
    HANDLED_API_ERRORS,
    normalize_provider_name,
    sanitize_error,
)

router = APIRouter()


@router.post("/api/ask")
async def api_ask(req: AskRequest):
    """LLM 질문 — 종목이 있으면 데이터 기반 분석, 없으면 순수 대화."""
    dartlab.verbose = False

    resolved = try_resolve_company(req)
    c: Company | None = resolved.company

    resolved_from_explicit_context = bool(req.company) or bool(req.viewContext and req.viewContext.company)

    if c and not resolved_from_explicit_context and needs_match_verification(req.question, c.corpName):
        corrected = await asyncio.to_thread(
            verify_match_with_llm,
            req.question,
            c.corpName,
            c.stockCode,
        )
        if corrected:
            try:
                c = Company(corrected)
            except (ValueError, OSError):
                candidates = _collect_candidates(corrected, strict=False)
                if candidates:
                    resolved = ResolveResult(ambiguous=True, suggestions=candidates)
                    c = None

    if c:
        cached = company_cache.get(c.stockCode)
        if cached:
            c = cached[0]

    if not c and not resolved.not_found and not resolved.ambiguous and req.history:
        c = try_resolve_from_history(req.history)
        if c:
            cached = company_cache.get(c.stockCode)
            if cached:
                c = cached[0]

    disambig_msg: str | None = None
    if resolved.not_found:
        disambig_msg = build_not_found_msg(resolved.suggestions)
    elif resolved.ambiguous:
        disambig_msg = build_ambiguous_msg(resolved.suggestions)

    if req.stream:
        return EventSourceResponse(
            stream_ask(c, req, not_found_msg=disambig_msg),
            media_type="text/event-stream",
        )

    if disambig_msg:
        return {"answer": disambig_msg}

    if c is None:
        return await run_plain_chat(req)

    try:
        answer = await asyncio.to_thread(
            c.ask,
            req.question,
            include=req.include,
            exclude=req.exclude,
            provider=normalize_provider_name(req.provider) or req.provider,
            role=req.role,
            model=req.model,
            api_key=req.api_key,
            base_url=req.base_url,
        )
        return {
            "company": c.corpName,
            "stockCode": c.stockCode,
            "answer": answer,
        }
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=sanitize_error(e))
