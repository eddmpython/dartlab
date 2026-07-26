from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from dartlab.ai.settings import (
    buildProviderCatalog,
    getProfileManager,
    getProviderSpec,
    publicProviderIds,
)
from dartlab.ai.settings.modelResolver import fallbackModels, isOpenaiChatModel, sortOpenaiModels


def _packageVersion() -> str:
    """설치된 dartlab 버전. facade 를 거치지 않고 패키지 메타데이터에서 직접 읽는다."""

    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("dartlab")
    except PackageNotFoundError:
        return "0.0.0"


from ..chat import OLLAMA_MODEL_GUIDE
from ..models import (
    AiProfileUpdateRequest,
    AiSecretUpdateRequest,
    ChannelConnectRequest,
    ConfigureRequest,
    DartKeyUpdateRequest,
)
from ..services.aiProfile import (
    buildCodexDetail,
    buildOauthCodexDetail,
    buildOllamaDetail,
    probeProviderAvailability,
    validateProviderConnection,
)
from .common import (
    HANDLED_API_ERRORS as _HANDLED_API_ERRORS,
)
from .common import (
    guideDetail as _guideDetail,
)
from .common import (
    normalizeProviderName as _normalize_provider_name,
)

logger = logging.getLogger(__name__)

router = APIRouter()

UI_PROVIDERS = publicProviderIds()
STATIC_MODELS: dict[str, list[str]] = {}

_oauthState: dict[str, Any] = {}

probe_provider_availability = probeProviderAvailability
build_ollama_detail = buildOllamaDetail


def _buildOpenDartStatus() -> dict[str, Any]:
    from dartlab.gather.dart.keys import getDartKeyStatus

    return getDartKeyStatus().toDict()


def _resolveCredentialSource(meta: dict[str, Any], profileProvider: dict[str, Any]) -> str:
    auth_kind = meta.get("authKind", "none")
    if auth_kind == "api_key":
        if profileProvider.get("secretConfigured"):
            return "secret_store"
        env_key = meta.get("envKey")
        if env_key and os.environ.get(env_key):
            return "env"
        return "none"
    if auth_kind == "oauth":
        return "oauth" if profileProvider.get("secretConfigured") else "none"
    if auth_kind == "cli":
        return "cli"
    return "none"


@router.get("/api/status")
def apiStatus(
    provider: str | None = Query(None, description="상태를 적극 확인할 provider"),
    probe: bool = Query(True, description="True면 provider availability를 실제 점검"),
):
    """LLM provider 상태 확인 (설치/인증/모델 포함)."""
    profile_snapshot = getProfileManager().serialize()
    catalog = {item["id"]: item for item in buildProviderCatalog()}
    results = {}
    target_provider = _normalize_provider_name(provider) or provider
    if probe and target_provider is None:
        target_provider = _normalize_provider_name(profile_snapshot.get("defaultProvider")) or profile_snapshot.get(
            "defaultProvider"
        )
    role_bindings = profile_snapshot.get("roles", {})

    for prov in UI_PROVIDERS:
        meta = catalog.get(prov, {})
        profileProvider = profile_snapshot.get("providers", {}).get(prov, {})
        info: dict[str, Any] = {
            "available": None,
            "model": profileProvider.get("model"),
            "checked": False,
            "label": meta.get("label", prov),
            "desc": meta.get("description", ""),
            "auth": meta.get("authKind", "none"),
            "secretConfigured": bool(profileProvider.get("secretConfigured")),
            "credentialSource": _resolveCredentialSource(meta, profileProvider),
            "selected": profile_snapshot.get("defaultProvider") == prov,
            "selectedRoles": [
                role_name
                for role_name, binding in role_bindings.items()
                if isinstance(binding, dict) and binding.get("provider") == prov
            ],
        }
        if meta.get("envKey"):
            info["envKey"] = meta["envKey"]
        if meta.get("signupUrl"):
            info["signupUrl"] = meta["signupUrl"]
        if meta.get("freeTierHint"):
            info["freeTierHint"] = meta["freeTierHint"]
        should_probe = probe and (target_provider is None or prov == target_provider)
        if should_probe:
            available, model, checked = probe_provider_availability(prov)
            info["available"] = available
            info["model"] = model
            info["checked"] = checked
        else:
            # probe 안 했으면 secretConfigured 로 fallback — UI 가 null 을 "검증 실패" 로 잘못
            # 해석해서 "설정 필요" 표시하던 문제 차단. probe 결과는 별도로 (백그라운드 또는
            # Settings 패널 진입 시) 갱신.
            info["available"] = info["secretConfigured"]
        results[prov] = info

    ollama_detail = build_ollama_detail(probe=probe and (target_provider is None or target_provider == "ollama"))
    oauth_codex_detail = buildOauthCodexDetail(
        probe=probe and (target_provider is None or target_provider == "oauth-codex")
    )
    codex_detail = buildCodexDetail(probe=probe and (target_provider is None or target_provider == "codex"))

    version = _packageVersion()

    # Room 정보 (터널 모드에서 협업 세션 활성 시)
    room_info = None
    try:
        from ..room import roomManager

        active_room = roomManager.getRoom()
        if active_room is not None:
            room_info = {
                "roomId": active_room.roomId,
                "members": len(active_room.members),
            }
    except ImportError:
        pass

    resp: dict[str, Any] = {
        "providers": results,
        "ollama": ollama_detail,
        "codex": codex_detail,
        "oauthCodex": oauth_codex_detail,
        "openDart": _buildOpenDartStatus(),
        "profile": profile_snapshot,
        "version": version,
    }
    if room_info is not None:
        resp["room"] = room_info
    try:
        from ..services.channelRuntime import channelRuntime

        resp["channels"] = channelRuntime.status()
    except ImportError:
        resp["channels"] = {}
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        resp["channel"] = devChannelRuntime.status()
    except ImportError:
        resp["channel"] = {"kind": "devtunnel", "running": False, "url": None, "qrDataUrl": None, "error": None}
    return resp


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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_guideDetail(e)) from e
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.post("/api/provider/validate")
def apiValidateProvider(req: ConfigureRequest):
    """LLM provider 검증. 전역 상태는 변경하지 않는다."""
    return validateProviderConnection(req)


@router.post("/api/configure")
def apiConfigure(req: ConfigureRequest):
    """구버전 alias. 현재는 provider 검증만 수행한다."""
    return validateProviderConnection(req)


@router.get("/api/ai/profile")
def apiAiProfile():
    """공통 AI profile + provider catalog 반환."""
    return getProfileManager().serialize()


@router.put("/api/ai/profile")
def apiAiProfileUpdate(req: AiProfileUpdateRequest):
    """공통 AI profile 갱신."""
    from dartlab.ai import configure as configure_ai

    manager = getProfileManager()
    provider = _normalize_provider_name(req.provider) or req.provider
    if provider and getProviderSpec(provider) is None:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")
    profile = manager.update(
        provider=provider,
        role=req.role,
        model=req.model,
        baseUrl=req.baseUrl,
        temperature=req.temperature,
        maxTokens=req.maxTokens,
        systemPrompt=req.systemPrompt,
        updatedBy="ui",
    )
    if provider:
        configure_ai(
            provider=provider,
            role=req.role,
            model=req.model,
            baseUrl=req.baseUrl,
            temperature=req.temperature,
            maxTokens=req.maxTokens,
            systemPrompt=req.systemPrompt,
        )
    return manager.serialize() | {"revision": profile.revision}


@router.post("/api/ai/profile/secrets")
def apiAiProfileSecret(req: AiSecretUpdateRequest):
    """provider secret 저장/삭제."""
    provider = _normalize_provider_name(req.provider) or req.provider
    spec = getProviderSpec(provider)
    if spec is None:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")
    if spec.auth_kind != "api_key":
        raise HTTPException(status_code=400, detail=f"{provider} provider는 API key secret을 사용하지 않습니다")

    manager = getProfileManager()
    if req.clear or not req.apiKey:
        profile = manager.clearApiKey(provider, updatedBy="ui")
    else:
        profile = manager.saveApiKey(provider, req.apiKey, updatedBy="ui")
    return manager.serialize() | {"revision": profile.revision}


@router.post("/api/openapi/dart-key/validate")
def apiValidateDartKey(req: DartKeyUpdateRequest):
    """OpenDART API 키 유효성만 검증한다."""
    from dartlab.gather.dart.keys import validateDartApiKey

    apiKey = (req.apiKey or "").strip()
    if not apiKey:
        raise HTTPException(status_code=400, detail="DART API 키를 입력하세요.")
    try:
        result = validateDartApiKey(apiKey)
        return result | {"openDart": _buildOpenDartStatus()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_guideDetail(e)) from e
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.put("/api/openapi/dart-key")
def apiSaveDartKey(req: DartKeyUpdateRequest):
    """프로젝트 .env에 OpenDART API 키를 저장한다."""
    from dartlab.gather.dart.keys import saveDartKeyToDotenv

    apiKey = (req.apiKey or "").strip()
    if not apiKey:
        raise HTTPException(status_code=400, detail="DART API 키를 입력하세요.")
    try:
        env_path = saveDartKeyToDotenv(apiKey)
        return {"ok": True, "envPath": str(env_path), "openDart": _buildOpenDartStatus()}
    except OSError as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.delete("/api/openapi/dart-key")
def apiDeleteDartKey():
    """프로젝트 .env의 OpenDART API 키를 제거한다."""
    from dartlab.gather.dart.keys import clearDartKeyFromDotenv

    try:
        env_path = clearDartKeyFromDotenv()
        return {"ok": True, "envPath": str(env_path), "openDart": _buildOpenDartStatus()}
    except OSError as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.post("/api/channels/{platform}/start")
def apiChannelStart(platform: str, req: ChannelConnectRequest):
    """외부 채널 어댑터 시작."""
    try:
        from ..services.channelRuntime import channelRuntime

        payload = req.model_dump(exclude_none=True)
        return channelRuntime.start(platform, **payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_guideDetail(e)) from e
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.post("/api/channels/{platform}/stop")
def apiChannelStop(platform: str):
    """외부 채널 어댑터 정지."""
    try:
        from ..services.channelRuntime import channelRuntime

        return channelRuntime.stop(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_guideDetail(e)) from e
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


def _requestPort(request: Request) -> int:
    if request.url.port:
        return int(request.url.port)
    return 8400


@router.get("/api/channel")
def apiDevChannelStatus():
    """DevTunnels 모바일 접속 채널 상태를 반환한다."""
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        return devChannelRuntime.status()
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.post("/api/channel/start")
def apiDevChannelStart(request: Request):
    """현재 Web UI를 모바일에서 열 수 있는 DevTunnels 채널을 시작한다."""
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        return devChannelRuntime.start(port=_requestPort(request), autoYes=True)
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.post("/api/channel/stop")
def apiDevChannelStop():
    """DevTunnels 채널을 종료한다."""
    try:
        from ..services.devChannelRuntime import devChannelRuntime

        return devChannelRuntime.stop()
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=_guideDetail(e)) from e


@router.get("/api/ai/profile/events")
async def apiAiProfileEvents(request: Request):
    """profile 변경 SSE 스트림."""
    manager = getProfileManager()

    async def _generate():
        last_fingerprint = ""
        while True:
            if await request.is_disconnected():
                break
            payload = manager.serialize()
            fingerprint = manager.fingerprint()
            if fingerprint != last_fingerprint:
                last_fingerprint = fingerprint
                yield {
                    "event": "profile_changed",
                    "data": json.dumps(payload, ensure_ascii=False),
                }
            await asyncio.sleep(1.0)

    return EventSourceResponse(_generate())


@router.get("/api/models/{provider}")
def apiModels(provider: str):
    """Provider별 사용 가능한 모델 목록 — SDK/API 자동 조회, 실패시 fallback."""
    from dartlab.ai.providers import createProvider
    from dartlab.ai.settings.types import LLMConfig

    provider = _normalize_provider_name(provider) or provider

    if provider == "codex":
        try:
            from dartlab.ai.providers.support.codexCli import getCodexModelCatalog

            return {"models": getCodexModelCatalog()}
        except (ImportError, OSError, RuntimeError, ValueError):
            return {"models": fallbackModels("codex", allowFetch=False)}

    if provider == "oauth-codex":
        try:
            from dartlab.ai.providers.oauthCodex import availableModels

            # cache 우선 — 비어 있으면 정적 fallback 즉시 반환 + background thread 에서 warm.
            # 이전: cold 1 회 ~43s (DNS/TLS cold + remote /codex/models fetch) 동안 UI 가
            # "설정 필요" 표시. allow_fetch=False 로 fallback 도 cold HTTP 안 트리거.
            cached = availableModels(allowFetch=False)
            if cached:
                return {"models": cached}
            import threading

            threading.Thread(target=availableModels, daemon=True).start()
            return {"models": fallbackModels("oauth-codex", allowFetch=False)}
        except (ImportError, OSError, RuntimeError, ValueError):
            return {"models": fallbackModels("oauth-codex", allowFetch=False)}

    if provider in STATIC_MODELS:
        return {"models": STATIC_MODELS[provider]}

    if provider == "ollama":
        try:
            config = LLMConfig(provider="ollama")
            prov = createProvider(config)
            installed = prov.getInstalledModels()
            return {"models": installed, "recommendations": OLLAMA_MODEL_GUIDE}
        except _HANDLED_API_ERRORS:
            return {"models": [], "recommendations": OLLAMA_MODEL_GUIDE}

    if provider == "openai":
        models = _fetchOpenaiModels()
        if models:
            return {"models": models}
        return {"models": fallbackModels("openai", allowFetch=False)}

    return {"models": []}


def _getApiKey(provider: str) -> str | None:
    """글로벌 config 또는 환경변수에서 API 키를 가져온다."""
    from dartlab.ai import getConfig

    config = getConfig(provider)
    if config.apiKey:
        return config.apiKey
    env_map = {"openai": "OPENAI_API_KEY"}
    return os.environ.get(env_map.get(provider, ""))


def _fetchOpenaiModels() -> list[str]:
    """OpenAI SDK로 모델 목록을 가져온다."""
    apiKey = _getApiKey("openai")
    if not apiKey:
        return []
    try:
        from openai import OpenAI

        client = OpenAI(api_key=apiKey)
        raw = client.models.list()
        models = []
        for model in raw:
            mid = model.id
            if isOpenaiChatModel(mid):
                models.append(mid)
        return sortOpenaiModels(models)
    except (ImportError, OSError, RuntimeError, ValueError):
        return []


@router.post("/api/codex/logout")
def apiCodexLogout():
    """Codex CLI에 저장된 계정 인증을 제거한다."""
    try:
        from dartlab.ai.providers.support.codexCli import logoutCodexCli

        logoutCodexCli()
    except ImportError:
        return {"ok": True}
    except FileNotFoundError as exc:
        logger.info("Codex CLI logout skipped: %s", exc)
        return {"ok": True}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=_guideDetail(exc)) from exc
    return {"ok": True}


@router.get("/api/oauth/authorize")
def apiOauthAuthorize():
    """ChatGPT OAuth 인증 시작 — 브라우저 로그인 URL 반환 + 로컬 콜백 서버 시작."""
    from dartlab.ai.providers.support.oauthToken import OAUTH_REDIRECT_PORT, buildAuthUrl

    auth_url, verifier, state = buildAuthUrl()

    _oauthState["verifier"] = verifier
    _oauthState["state"] = state
    _oauthState["done"] = False
    _oauthState["error"] = None

    _startOauthCallbackServer(OAUTH_REDIRECT_PORT)

    return {"authUrl": auth_url, "state": state}


@router.get("/api/oauth/status")
def apiOauthStatus():
    """OAuth 인증 완료 여부 폴링."""
    if _oauthState.get("error"):
        return {"done": True, "error": _oauthState["error"]}
    if _oauthState.get("done"):
        return {"done": True, "error": None}
    return {"done": False}


@router.post("/api/oauth/logout")
def apiOauthLogout():
    """OAuth 토큰 제거."""
    try:
        from dartlab.ai.providers.support.oauthToken import revokeToken

        revokeToken()
    except (ImportError, OSError, RuntimeError, ValueError):
        pass
    getProfileManager().update(provider="oauth-codex", updatedBy="ui")
    return {"ok": True}


def _startOauthCallbackServer(port: int):
    """OAuth 콜백을 받을 임시 HTTP 서버를 백그라운드 스레드로 시작."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse

    class CallbackHandler(BaseHTTPRequestHandler):
        """CallbackHandler — TODO 한국어 클래스 설명."""

        def do_GET(self):
            """do_GET — TODO 한국어 동작 설명."""
            parsed = urlparse(self.path)
            if parsed.path != "/auth/callback":
                self.send_response(404)
                self.end_headers()
                return

            params = parse_qs(parsed.query)
            code = (params.get("code") or [None])[0]
            state = (params.get("state") or [None])[0]
            error = (params.get("error") or [None])[0]

            if error:
                _oauthState["error"] = error
                _oauthState["done"] = True
                self._respondHtml("인증 실패", f"오류: {error}")
                return

            if state != _oauthState.get("state"):
                _oauthState["error"] = "state_mismatch"
                _oauthState["done"] = True
                self._respondHtml("인증 실패", "보안 검증 실패 (state mismatch)")
                return

            if not code:
                _oauthState["error"] = "no_code"
                _oauthState["done"] = True
                self._respondHtml("인증 실패", "인증 코드를 받지 못했습니다")
                return

            try:
                from dartlab.ai.providers.support.oauthToken import exchangeCode

                exchangeCode(code, _oauthState["verifier"])
                getProfileManager().update(provider="oauth-codex", updatedBy="ui")
                _oauthState["done"] = True
                self._respondHtml("인증 성공", "DartLab 인증이 완료되었습니다. 이 창을 닫아주세요.")
            except _HANDLED_API_ERRORS as exc:
                _oauthState["error"] = str(exc)
                _oauthState["done"] = True
                self._respondHtml("인증 실패", f"토큰 교환 실패: {exc}")

        def _respondHtml(self, title: str, message: str):
            import html as _html

            safe_title = _html.escape(title)
            safe_message = _html.escape(message)
            markup = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{safe_title}</title>"
                "<style>body{font-family:system-ui;display:flex;align-items:center;"
                "justify-content:center;min-height:100vh;margin:0;background:#050811;color:#e5e5e5}"
                "div{text-align:center;padding:2rem}"
                "h1{font-size:1.5rem;margin-bottom:1rem}"
                "</style></head><body>"
                f"<div><h1>{safe_title}</h1><p>{safe_message}</p></div>"
                "<script>setTimeout(()=>window.close(),3000)</script>"
                "</body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(markup.encode("utf-8"))

        def logMessage(self, fmt, *args):
            """logMessage — TODO 한국어 동작 설명."""
            pass

    def _runServer():
        server = HTTPServer(("127.0.0.1", port), CallbackHandler)
        server.timeout = 120
        server.handle_request()
        server.server_close()

    thread = threading.Thread(target=_runServer, daemon=True)
    thread.start()


@router.post("/api/ollama/pull")
async def apiOllamaPull(req: dict):
    """Ollama 모델 다운로드 (SSE 스트리밍 진행률)."""
    model_name = req.get("model")
    if not model_name:
        raise HTTPException(400, "model name required")

    async def _streamPull():
        import httpx

        try:
            with httpx.Client(timeout=600) as client:
                with client.stream(
                    "POST",
                    "http://localhost:11434/api/pull",
                    json={"model": model_name, "stream": True},
                ) as resp:
                    for line in resp.iter_lines():
                        if line:
                            yield {
                                "event": "progress",
                                "data": line,
                            }
            yield {"event": "done", "data": "{}"}
        except _HANDLED_API_ERRORS as exc:
            yield {"event": "error", "data": json.dumps({"error": _guideDetail(exc)}, ensure_ascii=False)}

    return EventSourceResponse(_streamPull(), media_type="text/event-stream")
