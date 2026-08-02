"""런타임 상태, 데이터 자격증명, 공유 채널 API."""

from __future__ import annotations

import asyncio
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from dartlab.ai.runtime import getRuntimeEngine

from ..models import (
    AiProfileUpdateRequest,
    AiSecretUpdateRequest,
    ChannelConnectRequest,
    ConfigureRequest,
    DartKeyUpdateRequest,
)
from .common import HANDLED_API_ERRORS as _HANDLED_API_ERRORS
from .common import guideDetail as _guideDetail

router = APIRouter()


def _packageVersion() -> str:
    """Sig: _packageVersion() -> str.

    Args: 없음.
    Returns: 설치된 DartLab 버전이다.
    Example: `current = _packageVersion()`.
    """
    try:
        return version("dartlab")
    except PackageNotFoundError:
        return "0.0.0"


def _buildOpenDartStatus() -> dict[str, Any]:
    """Sig: _buildOpenDartStatus() -> dict[str, Any].

    Args: 없음.
    Returns: OpenDART 데이터 자격증명 상태다.
    Example: `status = _buildOpenDartStatus()`.
    """
    from dartlab.gather.dart.keys import getDartKeyStatus

    return getDartKeyStatus().toDict()


@router.get("/api/status")
def apiStatus(
    runtimeId: str | None = Query(None, description="호환 필터: 설치형 agent runtime ID"),
    probe: bool = Query(True, description="True면 CLI와 MCP 상태를 확인"),
):
    """설치형 agent runtime과 데이터·채널 상태를 한 번에 반환한다."""
    runtimeStatus = getRuntimeEngine().status(refresh=probe)
    if runtimeId:
        runtimeStatus["runtimes"] = [item for item in runtimeStatus["runtimes"] if item["runtimeId"] == runtimeId]
    response: dict[str, Any] = {
        **runtimeStatus,
        "providers": {},
        "openDart": _buildOpenDartStatus(),
        "version": _packageVersion(),
    }
    try:
        from ..services.channelRuntime import channelRuntime

        response["channels"] = channelRuntime.status()
    except ImportError:
        response["channels"] = {}
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        response["channel"] = devChannelRuntime.status()
    except ImportError:
        response["channel"] = {"kind": "devtunnel", "running": False, "url": None, "error": None}
    return response


@router.get("/api/suggest")
def apiSuggest(stockCode: str = Query(..., description="추천 질문을 생성할 종목코드")):
    """회사 데이터 상태에 맞는 추천 질문 목록을 반환한다."""
    try:
        from ..services.companyApi import get_company

        company = get_company(stockCode)
        return {
            "stockCode": getattr(company, "stockCode", stockCode),
            "company": getattr(company, "corpName", stockCode),
            "suggestions": [],
            "dataReady": {},
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_guideDetail(exc)) from exc
    except _HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


def _runtimeMigration(detail: str) -> None:
    """Sig: _runtimeMigration(detail) -> None.

    Args: detail은 새 Runtime Center 안내다.
    Returns: 반환하지 않는다.
    Raises: HTTPException 410 for removed direct-model configuration.
    Example: legacy provider route에서 호출한다.
    """
    raise HTTPException(status_code=410, detail=detail)


@router.post("/api/provider/validate")
def apiValidateProvider(req: ConfigureRequest):
    """삭제된 direct provider 검증 경로를 Runtime Center로 안내한다."""
    _runtimeMigration("직접 provider 검증은 제거되었습니다. /api/agent/runtimes/{runtimeId}/probe를 사용하세요.")


@router.post("/api/configure")
def apiConfigure(req: ConfigureRequest):
    """삭제된 direct provider 설정 경로를 Runtime Center로 안내한다."""
    _runtimeMigration("DartLab은 모델 키를 저장하지 않습니다. /api/agent/runtimes를 사용하세요.")


@router.get("/api/ai/profile")
def apiAiProfile():
    """호환 조회에서 Runtime Center 상태와 migration 표식을 반환한다."""
    return {"mode": "agent-runtime", "deprecated": True, **getRuntimeEngine().status(refresh=False)}


@router.put("/api/ai/profile")
def apiAiProfileUpdate(req: AiProfileUpdateRequest):
    """삭제된 profile 갱신 경로를 Runtime Center로 안내한다."""
    _runtimeMigration("모델과 인증은 설치형 agent CLI가 소유합니다. Runtime Center에서 CLI를 선택하세요.")


@router.post("/api/ai/profile/secrets")
def apiAiProfileSecret(req: AiSecretUpdateRequest):
    """DartLab의 모델 secret 저장 기능이 제거되었음을 알린다."""
    _runtimeMigration("DartLab은 모델 API 키와 OAuth 토큰을 저장하지 않습니다.")


@router.post("/api/openapi/dart-key/validate")
def apiValidateDartKey(req: DartKeyUpdateRequest):
    """OpenDART 데이터 API 키 유효성만 검증한다."""
    from dartlab.gather.dart.keys import validateDartApiKey

    apiKey = (req.apiKey or "").strip()
    if not apiKey:
        raise HTTPException(status_code=400, detail="DART API 키를 입력하세요.")
    try:
        result = validateDartApiKey(apiKey)
        return result.toDict()
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=_guideDetail(exc)) from exc


@router.put("/api/openapi/dart-key")
def apiSaveDartKey(req: DartKeyUpdateRequest):
    """OpenDART 데이터 API 키를 프로젝트 환경에 저장한다."""
    from dartlab.gather.dart.keys import saveDartKeyToDotenv

    apiKey = (req.apiKey or "").strip()
    if not apiKey:
        raise HTTPException(status_code=400, detail="DART API 키를 입력하세요.")
    try:
        envPath = saveDartKeyToDotenv(apiKey)
        return {"ok": True, "envPath": str(envPath), "openDart": _buildOpenDartStatus()}
    except OSError as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


@router.delete("/api/openapi/dart-key")
def apiDeleteDartKey():
    """프로젝트 환경의 OpenDART 데이터 API 키를 제거한다."""
    from dartlab.gather.dart.keys import clearDartKeyFromDotenv

    try:
        envPath = clearDartKeyFromDotenv()
        return {"ok": True, "envPath": str(envPath), "openDart": _buildOpenDartStatus()}
    except OSError as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


@router.post("/api/channels/{platform}/start")
def apiChannelStart(platform: str, req: ChannelConnectRequest):
    """외부 공유 채널 어댑터를 시작한다."""
    try:
        from ..services.channelRuntime import channelRuntime

        return channelRuntime.start(platform, **req.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_guideDetail(exc)) from exc
    except _HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


@router.post("/api/channels/{platform}/stop")
def apiChannelStop(platform: str):
    """외부 공유 채널 어댑터를 중지한다."""
    try:
        from ..services.channelRuntime import channelRuntime

        return channelRuntime.stop(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=_guideDetail(exc)) from exc
    except _HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


def _requestPort(request: Request) -> int:
    """Sig: _requestPort(request) -> int.

    Args: FastAPI Request다.
    Returns: 명시 포트 또는 기본 8400이다.
    Example: `port = _requestPort(request)`.
    """
    return int(request.url.port) if request.url.port else 8400


@router.get("/api/channel")
def apiDevChannelStatus():
    """DevTunnels 모바일 접속 채널 상태를 반환한다."""
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        return devChannelRuntime.status()
    except _HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


@router.post("/api/channel/start")
def apiDevChannelStart(request: Request):
    """현재 Web UI용 DevTunnels 채널을 시작한다."""
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        return devChannelRuntime.start(port=_requestPort(request), autoYes=True)
    except _HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


@router.post("/api/channel/stop")
def apiDevChannelStop():
    """현재 DevTunnels 채널을 중지한다."""
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        return devChannelRuntime.stop()
    except _HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=_guideDetail(exc)) from exc


@router.get("/api/ai/profile/events")
async def apiAiProfileEvents(request: Request):
    """호환 SSE에서 Runtime Center 상태 변화를 전송한다."""

    async def _generate():
        lastPayload = ""
        while not await request.is_disconnected():
            payload = json.dumps(getRuntimeEngine().status(refresh=False), ensure_ascii=False, default=str)
            if payload != lastPayload:
                lastPayload = payload
                yield {"event": "runtime_changed", "data": payload}
            await asyncio.sleep(2.0)

    return EventSourceResponse(_generate())


@router.get("/api/models/{runtimeId}")
def apiModels(runtimeId: str):
    """모델 catalog의 세션 소유권을 새 endpoint로 안내한다."""
    return {
        "models": [],
        "runtimeId": runtimeId,
        "detail": "모델 목록은 열린 세션의 /api/agent/sessions/{sessionId}/models에서 CLI가 제공합니다.",
    }


@router.post("/api/codex/logout")
def apiCodexLogout():
    """DartLab이 CLI 인증을 변경하지 않음을 알린다."""
    _runtimeMigration("로그아웃은 해당 agent CLI의 공식 명령으로 실행하세요.")


@router.post("/api/oauth/authorize")
def apiOauthAuthorize():
    """DartLab OAuth 경로가 제거되었음을 알린다."""
    _runtimeMigration("DartLab OAuth는 제거되었습니다. agent CLI에서 로그인하세요.")


@router.get("/api/oauth/status")
def apiOauthStatus():
    """DartLab이 OAuth 상태를 보유하지 않음을 반환한다."""
    return {"done": True, "managedBy": "agent-cli", "deprecated": True}


@router.post("/api/oauth/logout")
def apiOauthLogout():
    """DartLab OAuth 토큰 저장소가 제거되었음을 알린다."""
    _runtimeMigration("DartLab OAuth 토큰 저장소는 제거되었습니다.")


@router.post("/api/ollama/pull")
def apiOllamaPull(req: dict[str, Any]):
    """직접 모델 다운로드가 Runtime Center 범위가 아님을 알린다."""
    _runtimeMigration("직접 모델 다운로드는 제거되었습니다. 설치형 agent CLI를 사용하세요.")
