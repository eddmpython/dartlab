"""에이전트가 로컬 DartLab UI를 안전하게 검수·조작하는 API."""

from __future__ import annotations

import os
import re
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator, model_validator

from ..security import _isExposedMode
from ..services.uiQa import ALLOWED_ACTIONS, ALLOWED_KEYS, uiQaBroker

router = APIRouter(prefix="/api/ui-qa", tags=["ui-qa"])

_QA_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_-]{0,119}$")
_CAPABILITIES = [
    "semantic-snapshot",
    "click",
    "fill",
    "key",
    "navigate",
    "scroll",
    "visual-audit-plan",
    "visual-audit-receipt",
]
_VISUAL_AUDIT_PLAN = {
    "schemaVersion": "dartlab.ui-qa.visual-plan.v1",
    "viewports": [
        {"viewportId": "desktop", "width": 1440, "height": 900, "deviceScaleFactor": 1},
        {"viewportId": "tablet", "width": 768, "height": 1024, "deviceScaleFactor": 1},
        {"viewportId": "mobile", "width": 390, "height": 844, "deviceScaleFactor": 1},
    ],
    "globalAssertions": [
        "duplicate-qa-id 진단이 없어야 한다",
        "horizontal-overflow 진단이 없어야 한다",
        "console-error 진단이 없어야 한다",
        "주요 조작 대상이 viewport 안에서 보여야 한다",
    ],
    "scenarios": [
        {
            "scenarioId": "chat-core",
            "route": "/chat",
            "viewportIds": ["desktop", "tablet", "mobile"],
            "steps": [
                {
                    "stepId": "empty",
                    "action": "snapshot",
                    "assertQaIds": ["chat-welcome", "analysis-promise"],
                    "screenshotLabel": "chat-investment-welcome",
                },
                {
                    "stepId": "composer",
                    "action": "fill",
                    "targetQaId": "chat-input",
                    "value": "삼성전자 투자 분석",
                    "assertQaIds": ["chat-input", "chat-send"],
                    "screenshotLabel": "chat-composer-filled",
                },
                {"stepId": "composer-cleanup", "action": "fill", "targetQaId": "chat-input", "value": ""},
            ],
        },
        {
            "scenarioId": "runtime-center",
            "route": "/chat",
            "viewportIds": ["desktop", "mobile"],
            "steps": [
                {
                    "stepId": "open",
                    "action": "click",
                    "targetQaId": "runtime-center-open",
                    "assertQaIds": ["runtime-center-dialog", "runtime-center"],
                    "screenshotLabel": "runtime-center-open",
                },
                {
                    "stepId": "close",
                    "action": "click",
                    "targetQaId": "runtime-center-close",
                    "screenshotLabel": "runtime-center-closed",
                },
            ],
        },
        {
            "scenarioId": "runtime-settings",
            "route": "/settings/runtimes",
            "viewportIds": ["desktop", "mobile"],
            "steps": [
                {
                    "stepId": "status",
                    "action": "snapshot",
                    "assertQaIds": ["runtime-settings", "runtime-center"],
                    "screenshotLabel": "runtime-settings",
                }
            ],
        },
        {
            "scenarioId": "terminal-shell",
            "route": "/terminal/005930",
            "viewportIds": ["desktop", "mobile"],
            "steps": [
                {
                    "stepId": "loaded",
                    "action": "snapshot",
                    "assertAnyQaIds": ["terminal-surface", "terminal-loading"],
                    "screenshotLabel": "terminal-005930",
                }
            ],
        },
    ],
}
_VISUAL_SCENARIOS = {item["scenarioId"] for item in _VISUAL_AUDIT_PLAN["scenarios"]}
_VISUAL_VIEWPORTS = {item["viewportId"] for item in _VISUAL_AUDIT_PLAN["viewports"]}


def uiQaEnabled() -> bool:
    """명시적으로 켠 로컬 개발 프로세스에서만 UI 검수 제어면을 활성화한다."""
    raw = os.environ.get("DARTLAB_UI_QA", "").strip().lower()
    return not _isExposedMode() and raw in {"1", "true", "yes", "on"}


def _requireEnabled() -> None:
    if not uiQaEnabled():
        raise HTTPException(status_code=403, detail="UI 검수 API가 비활성화되어 있습니다")


def _validQaId(value: str) -> str:
    if not _QA_ID.fullmatch(value):
        raise ValueError("targetQaId는 data-qa 식별자만 허용합니다")
    return value


class RegisterRequest(BaseModel):
    """로컬 UI 검수 브리지의 세션 등록 요청을 검증한다."""

    sessionId: str = Field(..., min_length=36, max_length=36)
    clientName: str = Field("dartlab-local-ui", min_length=1, max_length=80)
    capabilities: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("sessionId")
    @classmethod
    def validateSessionId(cls, value: str) -> str:
        """세션 식별자가 정규화 가능한 UUID인지 확인한다."""
        try:
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("sessionId는 UUID여야 합니다") from exc


class Rect(BaseModel):
    """화면 요소나 문서 영역의 좌표와 크기를 나타낸다."""

    x: float
    y: float
    width: float = Field(..., ge=0)
    height: float = Field(..., ge=0)


class ElementStyle(BaseModel):
    """시각 검수에 필요한 요소의 계산된 스타일 일부를 나타낸다."""

    display: str = Field(..., max_length=40)
    position: str = Field(..., max_length=40)
    color: str = Field(..., max_length=80)
    backgroundColor: str = Field(..., max_length=80)
    fontSize: str = Field(..., max_length=40)


class QaElement(BaseModel):
    """화면 스냅숏에서 검수 가능한 단일 요소의 상태를 나타낸다."""

    qaId: str = Field(..., min_length=1, max_length=120)
    tag: str = Field(..., min_length=1, max_length=30)
    role: str | None = Field(None, max_length=60)
    label: str | None = Field(None, max_length=300)
    text: str | None = Field(None, max_length=500)
    disabled: bool = False
    visible: bool
    checked: bool | None = None
    safeValue: str | None = Field(None, max_length=2000)
    rect: Rect
    style: ElementStyle

    @field_validator("qaId")
    @classmethod
    def validateQaId(cls, value: str) -> str:
        """요소 식별자가 허용된 data-qa 형식인지 확인한다."""
        return _validQaId(value)


class UiDiagnostic(BaseModel):
    """브라우저가 감지한 화면 구조 또는 콘솔 문제를 나타낸다."""

    code: Literal["duplicate-qa-id", "horizontal-overflow", "offscreen-element", "console-error"]
    severity: Literal["info", "warning", "error"]
    message: str = Field(..., min_length=1, max_length=500)
    qaId: str | None = Field(None, max_length=120)


class SnapshotRequest(BaseModel):
    """현재 경로와 검수 요소를 포함한 브라우저 화면 스냅숏을 검증한다."""

    route: str = Field(..., min_length=1, max_length=1000)
    title: str = Field("", max_length=300)
    viewport: Rect
    document: Rect
    activeQaId: str | None = Field(None, max_length=120)
    elements: list[QaElement] = Field(default_factory=list, max_length=500)
    diagnostics: list[UiDiagnostic] = Field(default_factory=list, max_length=200)
    capturedAt: str = Field(..., min_length=1, max_length=80)

    @field_validator("route")
    @classmethod
    def validateRoute(cls, value: str) -> str:
        """스냅숏 경로를 동일 출처의 절대 경로로 제한한다."""
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
            raise ValueError("route는 same-origin 절대 경로여야 합니다")
        return parsed.path

    @field_validator("activeQaId")
    @classmethod
    def validateActiveQaId(cls, value: str | None) -> str | None:
        """활성 요소 식별자가 있으면 허용된 data-qa 형식인지 확인한다."""
        return _validQaId(value) if value else None


class CommandRequest(BaseModel):
    """브라우저 검수 브리지에 전달할 제한된 조작 명령을 검증한다."""

    action: Literal["click", "fill", "key", "navigate", "scroll", "snapshot"]
    targetQaId: str | None = Field(None, max_length=120)
    value: str | None = Field(None, max_length=2000)
    key: str | None = Field(None, max_length=30)
    path: str | None = Field(None, max_length=1000)
    behavior: Literal["auto", "smooth"] | None = None
    block: Literal["start", "center", "end", "nearest"] | None = None

    @model_validator(mode="after")
    def validateCommand(self) -> "CommandRequest":
        """동작별 필수 인자와 동일 출처 이동 경로를 함께 검증한다."""
        if self.action not in ALLOWED_ACTIONS:
            raise ValueError("허용되지 않은 UI 검수 명령입니다")
        targetActions = {"click", "fill", "key", "scroll"}
        if self.action in targetActions:
            if not self.targetQaId:
                raise ValueError("이 명령에는 targetQaId가 필요합니다")
            _validQaId(self.targetQaId)
        elif self.targetQaId is not None:
            raise ValueError("이 명령에는 targetQaId를 사용할 수 없습니다")
        if self.action == "fill" and self.value is None:
            raise ValueError("fill 명령에는 value가 필요합니다")
        if self.action == "key" and self.key not in ALLOWED_KEYS:
            raise ValueError("허용되지 않은 키입니다")
        if self.action == "navigate":
            if not self.path:
                raise ValueError("navigate 명령에는 path가 필요합니다")
            parsed = urlsplit(self.path)
            if (
                parsed.scheme
                or parsed.netloc
                or parsed.query
                or parsed.fragment
                or not parsed.path.startswith("/")
                or "\\" in parsed.path
            ):
                raise ValueError("navigate는 query와 fragment가 없는 same-origin 절대 경로만 허용합니다")
        return self


class CommandResultRequest(BaseModel):
    """브라우저가 보고하는 검수 명령의 실행 결과를 검증한다."""

    ok: bool
    message: str | None = Field(None, max_length=1000)
    detail: dict[str, Any] | None = None


class VisualFinding(BaseModel):
    """시각 검수에서 발견한 단일 문제와 관련 요소를 나타낸다."""

    severity: Literal["info", "warning", "error"]
    code: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")
    message: str = Field(..., min_length=1, max_length=500)
    qaId: str | None = Field(None, max_length=120)

    @field_validator("qaId")
    @classmethod
    def validateQaId(cls, value: str | None) -> str | None:
        """관련 요소 식별자가 있으면 허용된 data-qa 형식인지 확인한다."""
        return _validQaId(value) if value else None


class VisualAuditRequest(BaseModel):
    """등록된 시나리오와 화면 크기에 대한 시각 검수 결과를 검증한다."""

    scenarioId: str = Field(..., min_length=1, max_length=80)
    viewportId: str = Field(..., min_length=1, max_length=40)
    result: Literal["passed", "failed", "blocked"]
    screenshotCaptured: bool
    screenshotLabel: str | None = Field(None, max_length=120)
    findings: list[VisualFinding] = Field(default_factory=list, max_length=100)
    capturedAt: str = Field(..., min_length=1, max_length=80)

    @model_validator(mode="after")
    def validatePlanReferences(self) -> "VisualAuditRequest":
        """검수 계획의 시나리오와 화면 크기 참조 및 실패 근거를 확인한다."""
        if self.scenarioId not in _VISUAL_SCENARIOS:
            raise ValueError("등록되지 않은 visual audit scenario입니다")
        if self.viewportId not in _VISUAL_VIEWPORTS:
            raise ValueError("등록되지 않은 visual audit viewport입니다")
        if self.result == "failed" and not self.findings:
            raise ValueError("실패한 visual audit에는 finding이 필요합니다")
        return self


@router.get("/config")
def getConfig():
    """현재 프로세스의 UI 검수 활성화 상태와 지원 기능을 반환한다."""
    enabled = uiQaEnabled()
    return {
        "schemaVersion": "dartlab.ui-qa.v1",
        "enabled": enabled,
        "localOnly": not _isExposedMode(),
        "capabilities": _CAPABILITIES if enabled else [],
        "auditPlanUrl": "/api/ui-qa/audit-plan" if enabled else None,
        "sessionTtlSeconds": 60,
    }


@router.get("/audit-plan")
def getVisualAuditPlan():
    """활성화된 로컬 검수 환경의 시각 검수 시나리오를 반환한다."""
    _requireEnabled()
    return _VISUAL_AUDIT_PLAN


@router.post("/sessions/register", status_code=status.HTTP_201_CREATED)
def registerSession(req: RegisterRequest):
    """검수 브리지 세션을 등록하고 허용된 기능만 승인한다."""
    _requireEnabled()
    allowed = [item for item in req.capabilities if item in _CAPABILITIES]
    return uiQaBroker.register(req.sessionId, req.clientName, allowed)


@router.post("/sessions/{sessionId}/snapshot", status_code=status.HTTP_202_ACCEPTED)
def updateSnapshot(sessionId: str, req: SnapshotRequest):
    """지정한 검수 세션의 최신 화면 스냅숏을 저장한다."""
    _requireEnabled()
    try:
        return uiQaBroker.updateSnapshot(sessionId, req.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions")
def listSessions():
    """현재 연결된 UI 검수 세션의 요약 목록을 반환한다."""
    _requireEnabled()
    return {"sessions": uiQaBroker.listSessions()}


@router.get("/sessions/{sessionId}")
def getSession(sessionId: str):
    """지정한 검수 세션의 화면과 최근 실행 이력을 반환한다."""
    _requireEnabled()
    try:
        return uiQaBroker.getSession(sessionId)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/sessions/{sessionId}", status_code=status.HTTP_204_NO_CONTENT)
def deleteSession(sessionId: str):
    """지정한 UI 검수 세션과 메모리 내 이력을 종료한다."""
    _requireEnabled()
    try:
        uiQaBroker.deleteSession(sessionId)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/{sessionId}/commands", status_code=status.HTTP_202_ACCEPTED)
def createCommand(sessionId: str, req: CommandRequest):
    """검증된 UI 조작 명령을 지정한 세션의 대기열에 추가한다."""
    _requireEnabled()
    payload = req.model_dump()
    payload["commandId"] = str(uuid4())
    try:
        return uiQaBroker.enqueue(sessionId, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{sessionId}/commands/next")
def nextCommand(sessionId: str, response: Response):
    """브라우저 브리지가 실행할 다음 검수 명령을 전달한다."""
    _requireEnabled()
    try:
        command = uiQaBroker.nextCommand(sessionId)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if command is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None
    return command


@router.post("/sessions/{sessionId}/commands/{commandId}/result")
def completeCommand(sessionId: str, commandId: str, req: CommandResultRequest):
    """브라우저가 실행한 검수 명령의 완료 결과를 기록한다."""
    _requireEnabled()
    try:
        return uiQaBroker.completeCommand(
            sessionId,
            commandId,
            ok=req.ok,
            message=req.message,
            detail=req.detail,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{sessionId}/commands/{commandId}")
def getCommand(sessionId: str, commandId: str):
    """지정한 검수 명령의 전달 및 완료 상태를 반환한다."""
    _requireEnabled()
    try:
        return uiQaBroker.getCommand(sessionId, commandId)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{sessionId}/visual-audits", status_code=status.HTTP_201_CREATED)
def recordVisualAudit(sessionId: str, req: VisualAuditRequest):
    """검증된 시각 검수 결과를 지정한 세션 이력에 기록한다."""
    _requireEnabled()
    audit = req.model_dump()
    audit["auditId"] = str(uuid4())
    try:
        return uiQaBroker.recordVisualAudit(sessionId, audit)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
