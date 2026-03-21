from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import orjson
from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

import dartlab
from dartlab.core.ai import (
	build_provider_catalog,
	get_profile_manager,
	get_provider_spec,
	public_provider_ids,
)

from .common import (
	HANDLED_API_ERRORS as _HANDLED_API_ERRORS,
	normalize_provider_name as _normalize_provider_name,
	sanitize_error as _sanitize_error,
)
from ..chat import OLLAMA_MODEL_GUIDE
from ..models import (
	AiProfileUpdateRequest,
	AiSecretUpdateRequest,
	ConfigureRequest,
)
from ..services.ai_profile import (
	build_ollama_detail,
	build_oauth_codex_detail,
	probe_provider_availability,
	validate_provider_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter()

UI_PROVIDERS = public_provider_ids()
STATIC_MODELS: dict[str, list[str]] = {}

_oauth_state: dict[str, Any] = {}


@router.get("/api/status")
def api_status(
	provider: str | None = Query(None, description="상태를 적극 확인할 provider"),
	probe: bool = Query(True, description="True면 provider availability를 실제 점검"),
):
	"""LLM provider 상태 확인 (설치/인증/모델 포함)."""
	profile_snapshot = get_profile_manager().serialize()
	catalog = {item["id"]: item for item in build_provider_catalog()}
	results = {}
	target_provider = _normalize_provider_name(provider) or provider
	if probe and target_provider is None:
		target_provider = _normalize_provider_name(profile_snapshot.get("defaultProvider")) or profile_snapshot.get("defaultProvider")
	role_bindings = profile_snapshot.get("roles", {})

	for prov in UI_PROVIDERS:
		meta = catalog.get(prov, {})
		profile_provider = profile_snapshot.get("providers", {}).get(prov, {})
		info: dict[str, Any] = {
			"available": None,
			"model": profile_provider.get("model"),
			"checked": False,
			"label": meta.get("label", prov),
			"desc": meta.get("description", ""),
			"auth": meta.get("authKind", "none"),
			"secretConfigured": bool(profile_provider.get("secretConfigured")),
			"selected": profile_snapshot.get("defaultProvider") == prov,
			"selectedRoles": [
				role_name
				for role_name, binding in role_bindings.items()
				if isinstance(binding, dict) and binding.get("provider") == prov
			],
		}
		if meta.get("envKey"):
			info["envKey"] = meta["envKey"]
		should_probe = probe and (target_provider is None or prov == target_provider)
		if should_probe:
			available, model, checked = probe_provider_availability(prov)
			info["available"] = available
			info["model"] = model
			info["checked"] = checked
		results[prov] = info

	ollama_detail = build_ollama_detail(probe=probe and (target_provider is None or target_provider == "ollama"))
	oauth_codex_detail = build_oauth_codex_detail(
		probe=probe and (target_provider is None or target_provider == "oauth-codex")
	)

	codex_detail = {"installed": False, "authenticated": False, "authMode": None, "loginStatus": None, "version": None}
	try:
		from dartlab.engines.ai.providers.support.cli_setup import detect_codex

		codex_detail = detect_codex()
	except (
		AttributeError,
		FileNotFoundError,
		ImportError,
		OSError,
		PermissionError,
		RuntimeError,
		TypeError,
		ValueError,
	):
		codex_detail = {
			"installed": False,
			"authenticated": False,
			"authMode": None,
			"loginStatus": None,
			"version": None,
		}

	version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"
	return {
		"providers": results,
		"ollama": ollama_detail,
		"codex": codex_detail,
		"oauthCodex": oauth_codex_detail,
		"profile": profile_snapshot,
		"version": version,
	}


@router.post("/api/provider/validate")
def api_validate_provider(req: ConfigureRequest):
	"""LLM provider 검증. 전역 상태는 변경하지 않는다."""
	return validate_provider_connection(req)


@router.post("/api/configure")
def api_configure(req: ConfigureRequest):
	"""구버전 alias. 현재는 provider 검증만 수행한다."""
	return validate_provider_connection(req)


@router.get("/api/ai/profile")
def api_ai_profile():
	"""공통 AI profile + provider catalog 반환."""
	return get_profile_manager().serialize()


@router.put("/api/ai/profile")
def api_ai_profile_update(req: AiProfileUpdateRequest):
	"""공통 AI profile 갱신."""
	manager = get_profile_manager()
	provider = _normalize_provider_name(req.provider) or req.provider
	if provider and get_provider_spec(provider) is None:
		raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")
	profile = manager.update(
		provider=provider,
		role=req.role,
		model=req.model,
		base_url=req.base_url,
		temperature=req.temperature,
		max_tokens=req.max_tokens,
		system_prompt=req.system_prompt,
		updated_by="ui",
	)
	return manager.serialize() | {"revision": profile.revision}


@router.post("/api/ai/profile/secrets")
def api_ai_profile_secret(req: AiSecretUpdateRequest):
	"""provider secret 저장/삭제."""
	provider = _normalize_provider_name(req.provider) or req.provider
	spec = get_provider_spec(provider)
	if spec is None:
		raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")
	if spec.auth_kind != "api_key":
		raise HTTPException(status_code=400, detail=f"{provider} provider는 API key secret을 사용하지 않습니다")

	manager = get_profile_manager()
	if req.clear or not req.api_key:
		profile = manager.clear_api_key(provider, updated_by="ui")
	else:
		profile = manager.save_api_key(provider, req.api_key, updated_by="ui")
	return manager.serialize() | {"revision": profile.revision}


@router.get("/api/ai/profile/events")
async def api_ai_profile_events(request: Request):
	"""profile 변경 SSE 스트림."""
	manager = get_profile_manager()

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
					"data": orjson.dumps(payload).decode(),
				}
			await asyncio.sleep(1.0)

	return EventSourceResponse(_generate())


@router.get("/api/models/{provider}")
def api_models(provider: str):
	"""Provider별 사용 가능한 모델 목록 — SDK/API 자동 조회, 실패시 fallback."""
	from dartlab.engines.ai.providers import create_provider
	from dartlab.engines.ai.types import LLMConfig

	provider = _normalize_provider_name(provider) or provider

	if provider == "codex":
		from dartlab.engines.ai.providers.support.codex_cli import get_codex_model_catalog

		return {"models": get_codex_model_catalog()}

	if provider == "oauth-codex":
		from dartlab.engines.ai.providers.oauth_codex import AVAILABLE_MODELS

		return {"models": AVAILABLE_MODELS}

	if provider in STATIC_MODELS:
		return {"models": STATIC_MODELS[provider]}

	if provider == "ollama":
		try:
			config = LLMConfig(provider="ollama")
			prov = create_provider(config)
			installed = prov.get_installed_models()
			return {"models": installed, "recommendations": OLLAMA_MODEL_GUIDE}
		except _HANDLED_API_ERRORS:
			return {"models": [], "recommendations": OLLAMA_MODEL_GUIDE}

	if provider == "openai":
		models = _fetch_openai_models()
		if models:
			return {"models": models}
		return {
			"models": [
				"o3",
				"gpt-4.1",
				"gpt-4.1-mini",
				"gpt-4.1-nano",
				"o4-mini",
				"o3-mini",
				"gpt-4o",
				"gpt-4o-mini",
			]
		}

	return {"models": []}


def _get_api_key(provider: str) -> str | None:
	"""글로벌 config 또는 환경변수에서 API 키를 가져온다."""
	from dartlab.engines.ai import get_config

	config = get_config(provider)
	if config.api_key:
		return config.api_key
	env_map = {"openai": "OPENAI_API_KEY"}
	return os.environ.get(env_map.get(provider, ""))


def _fetch_openai_models() -> list[str]:
	"""OpenAI SDK로 모델 목록을 가져온다."""
	api_key = _get_api_key("openai")
	if not api_key:
		return []
	try:
		from openai import OpenAI

		client = OpenAI(api_key=api_key)
		raw = client.models.list()
		chat_prefixes = ("gpt-5", "gpt-4", "gpt-3.5", "o1", "o3", "o4")
		exclude = (
			"realtime",
			"audio",
			"search",
			"instruct",
			"embedding",
			"tts",
			"whisper",
			"dall-e",
			"davinci",
			"babbage",
			"transcribe",
		)
		models = []
		for model in raw:
			mid = model.id
			if any(mid.startswith(prefix) for prefix in chat_prefixes):
				if not any(excluded in mid for excluded in exclude):
					models.append(mid)
		priority = [
			"gpt-5.4",
			"gpt-5.4-pro",
			"gpt-5.3-codex",
			"gpt-5.2",
			"gpt-5.2-pro",
			"gpt-5.2-codex",
			"gpt-5.1",
			"gpt-5",
			"gpt-5-mini",
			"gpt-4.1",
			"gpt-4.1-mini",
			"gpt-4.1-nano",
			"gpt-4o",
			"gpt-4o-mini",
			"o4-mini",
			"o3",
			"o3-mini",
			"o1",
			"o1-mini",
		]

		def sort_key(name: str):
			for idx, prefix in enumerate(priority):
				if name == prefix or name.startswith(prefix + "-"):
					return (idx, name)
			return (100, name)

		models.sort(key=sort_key)
		return models
	except (ImportError, OSError, RuntimeError, ValueError):
		return []



@router.post("/api/codex/logout")
def api_codex_logout():
	"""Codex CLI에 저장된 계정 인증을 제거한다."""
	from dartlab.engines.ai.providers.support.codex_cli import logout_codex_cli

	try:
		logout_codex_cli()
	except FileNotFoundError as exc:
		raise HTTPException(status_code=404, detail=_sanitize_error(exc)) from exc
	except RuntimeError as exc:
		raise HTTPException(status_code=400, detail=_sanitize_error(exc)) from exc
	return {"ok": True}


@router.get("/api/oauth/authorize")
def api_oauth_authorize():
	"""ChatGPT OAuth 인증 시작 — 브라우저 로그인 URL 반환 + 로컬 콜백 서버 시작."""
	from dartlab.engines.ai.providers.support.oauth_token import OAUTH_REDIRECT_PORT, build_auth_url

	auth_url, verifier, state = build_auth_url()

	_oauth_state["verifier"] = verifier
	_oauth_state["state"] = state
	_oauth_state["done"] = False
	_oauth_state["error"] = None

	_start_oauth_callback_server(OAUTH_REDIRECT_PORT)

	return {"authUrl": auth_url, "state": state}


@router.get("/api/oauth/status")
def api_oauth_status():
	"""OAuth 인증 완료 여부 폴링."""
	if _oauth_state.get("error"):
		return {"done": True, "error": _oauth_state["error"]}
	if _oauth_state.get("done"):
		return {"done": True, "error": None}
	return {"done": False}


@router.post("/api/oauth/logout")
def api_oauth_logout():
	"""OAuth 토큰 제거."""
	from dartlab.engines.ai.providers.support.oauth_token import revoke_token

	revoke_token()
	get_profile_manager().update(provider="oauth-codex", updated_by="ui")
	return {"ok": True}


def _start_oauth_callback_server(port: int):
	"""OAuth 콜백을 받을 임시 HTTP 서버를 백그라운드 스레드로 시작."""
	import threading
	from http.server import BaseHTTPRequestHandler, HTTPServer
	from urllib.parse import parse_qs, urlparse

	class CallbackHandler(BaseHTTPRequestHandler):
		def do_GET(self):
			parsed = urlparse(self.path)
			if parsed.path != "/auth/callback":
				self.send_response(404)
				self.end_headers()
				return

			params = parse_qs(parsed.query)
			code = params.get("code", [None])[0]
			state = params.get("state", [None])[0]
			error = params.get("error", [None])[0]

			if error:
				_oauth_state["error"] = error
				_oauth_state["done"] = True
				self._respond_html("인증 실패", f"오류: {error}")
				return

			if state != _oauth_state.get("state"):
				_oauth_state["error"] = "state_mismatch"
				_oauth_state["done"] = True
				self._respond_html("인증 실패", "보안 검증 실패 (state mismatch)")
				return

			if not code:
				_oauth_state["error"] = "no_code"
				_oauth_state["done"] = True
				self._respond_html("인증 실패", "인증 코드를 받지 못했습니다")
				return

			try:
				from dartlab.engines.ai.providers.support.oauth_token import exchange_code

				exchange_code(code, _oauth_state["verifier"])
				get_profile_manager().update(provider="oauth-codex", updated_by="ui")
				_oauth_state["done"] = True
				self._respond_html("인증 성공", "DartLab 인증이 완료되었습니다. 이 창을 닫아주세요.")
			except _HANDLED_API_ERRORS as exc:
				_oauth_state["error"] = str(exc)
				_oauth_state["done"] = True
				self._respond_html("인증 실패", f"토큰 교환 실패: {exc}")

		def _respond_html(self, title: str, message: str):
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

		def log_message(self, fmt, *args):
			pass

	def _run_server():
		server = HTTPServer(("127.0.0.1", port), CallbackHandler)
		server.timeout = 120
		server.handle_request()
		server.server_close()

	thread = threading.Thread(target=_run_server, daemon=True)
	thread.start()


@router.post("/api/ollama/pull")
async def api_ollama_pull(req: dict):
	"""Ollama 모델 다운로드 (SSE 스트리밍 진행률)."""
	model_name = req.get("model")
	if not model_name:
		raise HTTPException(400, "model name required")

	async def _stream_pull():
		import requests

		try:
			with requests.post(
				"http://localhost:11434/api/pull",
				json={"model": model_name, "stream": True},
				stream=True,
				timeout=600,
			) as resp:
				for line in resp.iter_lines():
					if line:
						yield {
							"event": "progress",
							"data": line.decode("utf-8"),
						}
			yield {"event": "done", "data": "{}"}
		except _HANDLED_API_ERRORS as exc:
			yield {"event": "error", "data": orjson.dumps({"error": _sanitize_error(exc)}).decode()}

	return EventSourceResponse(_stream_pull(), media_type="text/event-stream")
