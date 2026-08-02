"""설치형 에이전트 Runtime Center API."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dartlab.ai.runtime import getRuntimeEngine
from dartlab.ai.runtime.installManager import buildInstallPlan, executeInstallPlan
from dartlab.ai.runtime.mcpBootstrap import buildMcpConnectPlan, executeMcpConnectPlan
from dartlab.productOutcome import outcomeSnapshot, verifyOutcomeEvidence

router = APIRouter(prefix="/api/agent", tags=["agent-runtime"])


class RuntimeActionRequest(BaseModel):
    """설치 또는 MCP 연결 적용 요청."""

    runtimeId: str = Field(..., min_length=1, max_length=50)
    approvedDigest: str = Field(..., min_length=64, max_length=64)


class SessionOpenRequest(BaseModel):
    """새 세션 또는 저장 세션 재개 요청."""

    runtimeId: str | None = Field(None, max_length=50)
    sessionId: str | None = Field(None, max_length=120)
    cwd: str | None = Field(None, max_length=1000)


class ApprovalRequest(BaseModel):
    """pending agent permission에 대한 사용자 결정."""

    approvalId: str = Field(..., min_length=1, max_length=200)
    allow: bool


class EvidenceVerifyRequest(BaseModel):
    """사용자가 실제 연 exact evidence ref receipt."""

    refId: str = Field(..., min_length=1, max_length=1000)


@router.get("/runtimes")
async def listRuntimes(refresh: bool = Query(False)):
    """설치형 런타임, 버전, MCP 연결 상태를 반환한다."""
    return await asyncio.to_thread(getRuntimeEngine().status, refresh=refresh)


@router.get("/runtimes/{runtimeId}")
async def getRuntime(runtimeId: str, refresh: bool = Query(False)):
    """한 런타임의 Runtime Center 상태를 반환한다."""
    status = await listRuntimes(refresh=refresh)
    for item in status["runtimes"]:
        if item["runtimeId"] == runtimeId:
            return item
    raise HTTPException(status_code=404, detail="runtime not found")


@router.post("/runtimes/{runtimeId}/probe")
async def probeRuntime(runtimeId: str):
    """TTL 캐시를 무시하고 설치와 연결 상태를 다시 점검한다."""
    return await getRuntime(runtimeId, refresh=True)


@router.post("/runtimes/{runtimeId}/install/plan")
def planRuntimeInstall(runtimeId: str):
    """실행하지 않고 설치 argv와 승인 digest를 만든다."""
    try:
        return buildInstallPlan(runtimeId).toDict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="runtime not found") from exc


@router.post("/runtimes/install/apply")
async def applyRuntimeInstall(req: RuntimeActionRequest):
    """동일 digest를 명시적으로 승인한 설치 계획만 실행한다."""
    try:
        plan = buildInstallPlan(req.runtimeId)
        result = await asyncio.to_thread(executeInstallPlan, plan, approvedDigest=req.approvedDigest)
        return {"ok": True, "runtimeId": req.runtimeId, "stdout": result.stdout[-4000:]}
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/runtimes/{runtimeId}/mcp/plan")
def planMcpConnect(runtimeId: str):
    """공식 CLI MCP 연결 명령과 승인 digest를 만든다."""
    try:
        return buildMcpConnectPlan(runtimeId).toDict()
    except (KeyError, ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runtimes/mcp/apply")
async def applyMcpConnect(req: RuntimeActionRequest):
    """동일 digest를 승인한 MCP 연결 계획만 실행한다."""
    try:
        plan = buildMcpConnectPlan(req.runtimeId)
        result = await asyncio.to_thread(executeMcpConnectPlan, plan, approvedDigest=req.approvedDigest)
        return {"ok": True, "runtimeId": req.runtimeId, "stdout": result.stdout[-4000:]}
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions")
def listSessions(limit: int = Query(100, ge=1, le=1000)):
    """네이티브 transcript를 제외한 세션 매핑을 최신순 반환한다."""
    engine = getRuntimeEngine()
    return {"sessions": [session.toDict() for session in engine.sessionStore.list(limit=limit)]}


@router.post("/sessions")
async def openSession(req: SessionOpenRequest):
    """선택 런타임으로 새 세션을 열거나 저장 세션을 재개한다."""
    try:
        session = await asyncio.to_thread(
            getRuntimeEngine().openSession,
            runtimeId=req.runtimeId,
            sessionId=req.sessionId,
            cwd=Path(req.cwd) if req.cwd else None,
        )
        return session.toDict()
    except (KeyError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/sessions/{sessionId}")
def deleteSession(sessionId: str):
    """hot process를 닫고 DartLab 세션 매핑을 삭제한다."""
    engine = getRuntimeEngine()
    engine.sessionManager.close(sessionId)
    engine.sessionStore.delete(sessionId)
    return {"ok": True}


@router.get("/sessions/{sessionId}/events")
def replaySessionEvents(sessionId: str, afterSequence: int = Query(0, ge=0)):
    """재연결 클라이언트에 ring buffer의 후속 이벤트를 반환한다."""
    try:
        return {
            "events": [event.toDict() for event in getRuntimeEngine().replay(sessionId, afterSequence=afterSequence)]
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc


@router.post("/sessions/{sessionId}/cancel")
def cancelSessionTurn(sessionId: str):
    """현재 활성 턴을 네이티브 프로토콜로 취소한다."""
    try:
        getRuntimeEngine().cancel(sessionId)
        return {"ok": True}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc


@router.post("/sessions/{sessionId}/approval")
def resolveApproval(sessionId: str, req: ApprovalRequest):
    """사용자가 확인한 pending 권한 요청을 네이티브 프로토콜로 응답한다."""
    try:
        getRuntimeEngine().approve(sessionId, req.approvalId, allow=req.allow)
        return {"ok": True}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="approval not found") from exc


@router.get("/sessions/{sessionId}/models")
def listSessionModels(sessionId: str):
    """모델 목록을 제공하는 CLI에서만 네이티브 catalog를 반환한다."""
    try:
        managed = getRuntimeEngine()._managed(sessionId)
        return {"models": managed.driver.models(managed.handle)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc


@router.get("/product-outcomes")
def productOutcomes():
    """대화·모델 정보를 포함하지 않는 로컬 북극성 상태 집계를 반환한다."""
    return outcomeSnapshot(feature="ask")


@router.post("/product-outcomes/{outcomeId}/verify")
def verifyProductOutcome(outcomeId: str, req: EvidenceVerifyRequest):
    """exact evidence를 실제 해석한 뒤 같은 outcome receipt를 verified로 전이한다."""
    try:
        evidence = getRuntimeEngine().resolveEvidence(outcomeId, req.refId)
        receipt = verifyOutcomeEvidence(outcomeId, req.refId).toDict()
        return {"evidence": evidence, "receipt": receipt}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
