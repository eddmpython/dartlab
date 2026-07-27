"""AI analysis helpers used by FastAPI routes."""

from __future__ import annotations

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
    """회사 컨텍스트 없이 일반 AI 채팅을 실행한다."""
    try:
        hintCode = req.company
        if not hintCode and req.viewContext and req.viewContext.company:
            vc = req.viewContext.company
            hintCode = vc.stockCode or vc.corpName or vc.company
        # ⚠ provider/model 을 반드시 forward 한다. 예전엔 여기서 떨어뜨려서
        # 비스트리밍 /api/ask 가 요청한 provider 를 무시하고 프로필 기본값으로 돌았다.
        # 스트리밍 경로(api/ask.py)는 넘기고 있어 두 경로가 서로 다른 모델로 답하는
        # drift 가 났고, 모델을 고정해야 하는 품질 측정 자체가 불가능했다.
        result = await collect_analysis_result(
            req.question,
            provider=req.provider,
            model=req.model,
            role=req.role or "summary",
            stockCode=hintCode,
            history=[h.model_dump() for h in req.history] if req.history else None,
            view_context=req.viewContext.model_dump() if req.viewContext else None,
            use_tools=True,
            validate=False,
            detect_navigate=False,
            emit_system_prompt=False,
        )
        return result
    except AnalysisStreamError as e:
        if e.action == "login":
            raise HTTPException(status_code=401, detail="Codex CLI 로그인이 필요합니다. `codex login`을 실행하세요.")
        raise HTTPException(status_code=500, detail=e.message) from e
