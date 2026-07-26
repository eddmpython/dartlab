"""LLM 질문 엔드포인트 — api_ask, plain_chat, company copilot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

import dartlab.config as dartlab_config

from ..agentGateway import streamAgentRun
from ..models import AgentRunMessage, AgentRunRequest, AskRequest
from ..services.aiAnalysis import runPlainChat

router = APIRouter()


class CopilotRequest(BaseModel):
    """/api/company/{code}/copilot — landing inline copilot dock 요청.

    context 는 사용자가 클릭한 차트/표 정보를 담아 시스템 프롬프트로 주입한다.
    """

    question: str
    sectionId: str | None = None
    chartId: str | None = None
    accountKey: str | None = None
    valueRef: str | None = None
    period: str | None = None
    rceptNo: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    stream: bool = True
    provider: str | None = None
    role: str | None = None
    model: str | None = None


@router.post("/api/ask")
async def apiAsk(req: AskRequest):
    """LLM 질문 — AI가 질문 의도를 자율 판단하고 종목/매크로/비교를 결정한다."""
    dartlab_config.verbose = False

    if req.stream:
        return EventSourceResponse(
            _streamPublicAsk(req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    return await runPlainChat(req)


async def _streamPublicAsk(req: AskRequest):
    context = {}
    if req.company:
        context["company"] = {"stockCode": req.company, "company": req.company}
    elif req.viewContext and req.viewContext.company:
        company = req.viewContext.company
        context["company"] = {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "company": company.company,
        }
    # 다중 턴 컨텍스트 — 직전 history 를 user message 앞에 prepend.
    # HistoryMessage(role, text) → AgentRunMessage(role, content). max_length=50 은 AskRequest 가 강제.
    messages: list[AgentRunMessage] = []
    for h in req.history or []:
        if not h.text:
            continue
        if h.role not in ("user", "assistant", "system"):
            continue
        messages.append(AgentRunMessage(role=h.role, content=h.text))
    messages.append(AgentRunMessage(role="user", content=req.question))
    agent_req = AgentRunRequest(
        messages=messages,
        provider=req.provider,
        role=req.role,
        model=req.model,
        workspaceContext=context,
        stream=True,
    )
    async for event in streamAgentRun(agent_req):
        yield event


@router.post("/api/company/{stockCode}/copilot")
async def apiCompanyCopilot(stockCode: str, req: CopilotRequest):
    """landing/company 인라인 Copilot dock — citation-first 답변.

    사용자가 차트/표 selection 을 했으면 chartId/accountKey/valueRef/period 를
    함께 받아 시스템 프롬프트의 evidence 진입점으로 주입한다. 응답은 SSE
    (stream=True) 또는 단일 plain_chat (stream=False).
    """
    dartlab_config.verbose = False

    if req.stream:
        return EventSourceResponse(
            _streamCompanyCopilot(stockCode, req),
            media_type="text/event-stream",
        )

    # non-stream fallback — 컨텍스트 주입 후 plain_chat
    augmented_q = _augmentCopilotQuestion(stockCode, req)
    plain_req = AskRequest(question=augmented_q, company=stockCode, stream=False)
    return await runPlainChat(plain_req)


def _augmentCopilotQuestion(stockCode: str, req: CopilotRequest) -> str:
    """사용자 질문에 chart/table selection context 를 부가."""
    parts = [req.question.strip()]
    ctx_lines: list[str] = []
    if req.sectionId:
        ctx_lines.append(f"섹션: {req.sectionId}")
    if req.chartId:
        ctx_lines.append(f"차트: {req.chartId}")
    if req.accountKey:
        ctx_lines.append(f"계정: {req.accountKey}")
    if req.period:
        ctx_lines.append(f"기간: {req.period}")
    if req.valueRef:
        ctx_lines.append(f"valueRef: {req.valueRef}")
    if req.rceptNo:
        ctx_lines.append(f"rcept_no: {req.rceptNo}")
    if ctx_lines:
        parts.append("\n[selection 컨텍스트]\n" + "\n".join(ctx_lines))
    return "\n".join(parts)


async def _streamCompanyCopilot(stockCode: str, req: CopilotRequest):
    """copilot SSE — agent gateway 위에 stockCode + selection context 주입."""
    augmented_q = _augmentCopilotQuestion(stockCode, req)
    context: dict[str, Any] = {
        "company": {"stockCode": stockCode, "company": stockCode},
        "copilot": {
            "sectionId": req.sectionId,
            "chartId": req.chartId,
            "accountKey": req.accountKey,
            "valueRef": req.valueRef,
            "period": req.period,
            "rcept_no": req.rceptNo,
            **req.extra,
        },
    }
    agent_req = AgentRunRequest(
        messages=[AgentRunMessage(role="user", content=augmented_q)],
        provider=req.provider,
        role=req.role,
        model=req.model,
        workspaceContext=context,
        stream=True,
    )
    async for event in streamAgentRun(agent_req):
        yield event


@router.get("/api/ask/artifacts/{day}/{filename}")
async def downloadAskArtifact(day: str, filename: str):
    """AI tool_result 에서 생성된 CSV/JSON/JSONL 아티팩트를 내려준다."""
    path = _artifactPath(day, filename)
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="artifact not found")
    if filename.endswith(".jsonl"):
        media_type = "application/x-ndjson; charset=utf-8"
    elif filename.endswith(".json"):
        media_type = "application/json; charset=utf-8"
    else:
        media_type = "text/csv; charset=utf-8"
    return FileResponse(path, media_type=media_type, filename=filename)


def _artifactPath(day: str, filename: str) -> Path | None:
    normalized_day = day.replace("-", "")
    if not normalized_day.isdigit() or len(normalized_day) != 8:
        return None
    if Path(filename).name != filename:
        return None
    roots = [
        Path.home() / ".dartlab" / "ask_artifacts",
        Path(dartlab_config.dataDir) / "ai-artifacts",
    ]
    day_candidates = [normalized_day, day]
    for root in roots:
        for day_part in day_candidates:
            path = (root / day_part / filename).resolve()
            try:
                path.relative_to(root.resolve())
            except ValueError:
                continue
            if path.exists():
                return path
    return (roots[0] / normalized_day / filename).resolve()
