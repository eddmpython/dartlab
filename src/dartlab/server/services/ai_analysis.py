"""AI analysis helpers used by FastAPI routes."""

from __future__ import annotations

import orjson
from fastapi import HTTPException

from dartlab import Company
from dartlab.core.ai import normalize_provider
from dartlab.server.chat import build_topic_summary_question
from dartlab.server.models import AskRequest
from dartlab.server.streaming import AnalysisStreamError, collect_analysis_text, stream_analysis


def build_topic_summary_view_context(company: Company, topic: str) -> dict:
    """topic 요약용 뷰 컨텍스트를 구성한다."""
    return {
        "type": "viewer",
        "company": {
            "company": company.corpName,
            "corpName": company.corpName,
            "stockCode": company.stockCode,
        },
        "topic": topic,
        "topicLabel": topic,
    }


async def stream_topic_summary(
    company: Company,
    topic: str,
    *,
    provider: str | None = None,
    model: str | None = None,
):
    """topic 요약을 SSE 스트리밍으로 생성한다."""
    try:
        async for event in stream_analysis(
            company,
            build_topic_summary_question(topic),
            provider=normalize_provider(provider) or provider,
            role="summary",
            model=model,
            use_tools=False,
            validate=False,
            detect_navigate=False,
            emit_system_prompt=False,
            auto_snapshot=False,
            auto_diff=False,
            view_context=build_topic_summary_view_context(company, topic),
        ):
            yield event
    except AnalysisStreamError as e:
        yield {
            "event": "error",
            "data": orjson.dumps({"error": e.message, "action": e.action, "detail": e.detail}).decode(),
        }

    yield {"event": "done", "data": "{}"}


async def run_plain_chat(req: AskRequest) -> dict[str, str]:
    """회사 컨텍스트 없이 일반 AI 채팅을 실행한다."""
    try:
        answer = await collect_analysis_text(
            None,
            req.question,
            provider=normalize_provider(req.provider) or req.provider,
            role=req.role or "summary",
            model=req.model,
            api_key=req.api_key,
            base_url=req.base_url,
            history=[h.model_dump() for h in req.history] if req.history else None,
            view_context=req.viewContext.model_dump() if req.viewContext else None,
            use_tools=True,
            validate=False,
            detect_navigate=False,
            emit_system_prompt=False,
        )
        return {"answer": answer}
    except AnalysisStreamError as e:
        if e.action == "login":
            raise HTTPException(status_code=401, detail="Codex CLI 로그인이 필요합니다. `codex login`을 실행하세요.")
        raise HTTPException(status_code=500, detail=e.message) from e
