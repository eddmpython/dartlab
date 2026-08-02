"""AI analysis helpers used by FastAPI routes."""

from __future__ import annotations

import asyncio
import json

from fastapi import HTTPException

from dartlab import Company
from dartlab.server.chat import buildTopicSummaryQuestion
from dartlab.server.models import AskRequest
from dartlab.server.streaming import AnalysisStreamError, collectAnalysisResult, streamAnalysis

collect_analysis_result = collectAnalysisResult


def buildTopicSummaryViewContext(company: Company, topic: str) -> dict:
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


async def streamTopicSummary(
    company: Company,
    topic: str,
    *,
    provider: str | None = None,
    model: str | None = None,
):
    """topic 요약을 SSE 스트리밍으로 생성한다."""
    try:
        async for event in streamAnalysis(
            buildTopicSummaryQuestion(topic),
            role="summary",
            use_tools=False,
            validate=False,
            detect_navigate=False,
            emit_system_prompt=False,
            auto_snapshot=False,
            auto_diff=False,
            view_context=buildTopicSummaryViewContext(company, topic),
        ):
            yield event
    except AnalysisStreamError as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": e.message, "action": e.action, "detail": e.detail}, ensure_ascii=False),
        }

    yield {"event": "done", "data": "{}"}


async def runPlainChat(req: AskRequest) -> dict:
    """설치형 로컬 에이전트로 비스트리밍 답변을 수집한다."""
    try:
        hintCode = req.company
        if not hintCode and req.viewContext and req.viewContext.company:
            vc = req.viewContext.company
            hintCode = vc.stockCode or vc.corpName or vc.company
        from dartlab.ai.kernel import ask

        answer = await asyncio.to_thread(
            ask,
            req.question,
            stream=False,
            runtimeId=req.runtimeId or req.provider,
            sessionId=req.sessionId,
            stockCode=hintCode,
        )
        return {"answer": answer, "text": answer, "sessionId": req.sessionId}
    except AnalysisStreamError as e:
        if e.action == "login":
            raise HTTPException(status_code=401, detail="Codex CLI 로그인이 필요합니다. `codex login`을 실행하세요.")
        raise HTTPException(status_code=500, detail=e.message) from e
