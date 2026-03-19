"""DartLab Web Server — FastAPI + SSE 스트리밍.

dartlab ai 명령으로 실행:
    dartlab ai              # http://localhost:8400
    dartlab ai --port 9000  # 커스텀 포트
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

import dartlab
from dartlab import Company

from .cache import company_cache
from .chat import OLLAMA_MODEL_GUIDE, build_dynamic_chat_prompt, build_history_messages, build_topic_summary_prompt
from .dialogue import build_conversation_state
from .models import AskRequest, ConfigureRequest, TocChapter, TocResponse, TocTopic
from .resolve import (
    ResolveResult,
    _collect_candidates,
    build_ambiguous_msg,
    build_not_found_msg,
    needs_match_verification,
    try_resolve_company,
    try_resolve_from_history,
    verify_match_with_llm,
)
from .streaming import stream_ask

logger = logging.getLogger(__name__)

UI_PROVIDERS = ("codex", "ollama", "openai")
UI_PROVIDER_META: dict[str, dict[str, str]] = {
    "codex": {
        "label": "GPT (ChatGPT 계정)",
        "desc": "ChatGPT Plus/Pro 구독, Codex CLI 로그인 필요. 코드 작업은 workspace-write로 위임 가능",
        "auth": "cli",
    },
    "ollama": {"label": "Ollama (로컬)", "desc": "무료, 오프라인, 프라이빗", "auth": "none"},
    "openai": {
        "label": "OpenAI API",
        "desc": "GPT-5.4, o4 등 전체 모델",
        "auth": "api_key",
        "envKey": "OPENAI_API_KEY",
    },
}

STATIC_MODELS: dict[str, list[str]] = {}
_HANDLED_API_ERRORS = (
    AttributeError,
    FileNotFoundError,
    ImportError,
    KeyError,
    OSError,
    PermissionError,
    RuntimeError,
    TimeoutError,
    TypeError,
    ValueError,
)


async def _preload_ollama_once() -> None:
    """서버 시작 직후 Ollama 모델을 미리 깨워 cold start를 줄인다."""

    await asyncio.sleep(2)

    try:
        from dartlab.engines.ai.providers import create_provider
        from dartlab.engines.ai.types import LLMConfig

        config = LLMConfig(provider="ollama")
        provider = create_provider(config)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        logger.debug("Ollama preload 준비 실패", exc_info=exc)
        return

    if not hasattr(provider, "preload"):
        return

    try:
        if provider.check_available():
            ok = await asyncio.to_thread(provider.preload)
            if ok:
                logger.info("Ollama 모델 preload 완료: %s", provider.resolved_model)
    except (ConnectionError, OSError, RuntimeError, TimeoutError, ValueError) as exc:
        logger.debug("Ollama preload 실행 실패", exc_info=exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    preload_task = asyncio.create_task(_preload_ollama_once())
    try:
        yield
    finally:
        if not preload_task.done():
            preload_task.cancel()
        with suppress(asyncio.CancelledError):
            await preload_task


app = FastAPI(title="DartLab", version=dartlab.__version__, lifespan=lifespan)


def _default_host() -> str:
    return os.environ.get("DARTLAB_HOST", "127.0.0.1")


def _cors_origins() -> list[str]:
    raw = os.environ.get("DARTLAB_CORS_ORIGINS")
    if raw:
        raw = raw.strip()
        if raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [
        "http://127.0.0.1:8400",
        "http://localhost:8400",
        "http://127.0.0.1:5400",
        "http://localhost:5400",
    ]


def _normalize_provider_name(provider: str | None) -> str | None:
    """Normalize deprecated provider aliases to the current public surface."""
    if provider == "chatgpt":
        return "codex"
    return provider


def _serialize_payload(payload: Any, *, max_rows: int = 200) -> dict[str, Any]:
    """Company index/show/trace payload를 UI 친화 JSON으로 직렬화."""
    import polars as pl

    if payload is None:
        return {"type": "none", "data": None}

    if isinstance(payload, pl.DataFrame):
        preview = payload.head(max_rows)
        rows = preview.to_dicts()
        for row in rows:
            for key, value in row.items():
                if value is not None and not isinstance(value, (str, int, float, bool)):
                    row[key] = str(value)
        return {
            "type": "table",
            "columns": preview.columns,
            "rows": rows,
            "totalRows": payload.height,
            "truncated": payload.height > max_rows,
        }

    if isinstance(payload, dict):
        return {"type": "dict", "data": payload}

    if isinstance(payload, str):
        return {"type": "text", "data": payload}

    return {"type": "unknown", "data": str(payload)}


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def api_status():
    """LLM provider 상태 확인 (설치/인증/모델 포함)."""
    from dartlab.engines.ai.providers import create_provider
    from dartlab.engines.ai.types import LLMConfig

    results = {}

    for prov in UI_PROVIDERS:
        info = {"available": False, "model": None, **UI_PROVIDER_META.get(prov, {})}
        try:
            config = LLMConfig(provider=prov)
            provider = create_provider(config)
            available = provider.check_available()
            info["available"] = available
            info["model"] = provider.resolved_model
        except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
            info["available"] = False
            info["model"] = None
        results[prov] = info

    ollama_detail = {}
    try:
        from dartlab.engines.ai.ollama_setup import detect_ollama, get_install_guide

        ollama_info = detect_ollama()
        ollama_detail["installed"] = ollama_info.get("installed", False)
        ollama_detail["running"] = ollama_info.get("running", False)
        ollama_detail["gpu"] = ollama_info.get("gpu", None)
        if not ollama_info.get("installed"):
            ollama_detail["installGuide"] = get_install_guide()
    except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
        ollama_detail["installed"] = False
        ollama_detail["running"] = False

    codex_detail = {"installed": False, "authenticated": False, "authMode": None, "loginStatus": None, "version": None}
    try:
        from dartlab.engines.ai.cli_setup import detect_codex

        codex_detail = detect_codex()
    except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
        codex_detail = {
            "installed": False,
            "authenticated": False,
            "authMode": None,
            "loginStatus": None,
            "version": None,
        }

    chatgpt_detail = {
        "deprecated": True,
        "mappedTo": "codex",
        "available": results.get("codex", {}).get("available", False),
        "authenticated": codex_detail.get("authenticated", False),
        "authMode": codex_detail.get("authMode"),
        "loginStatus": codex_detail.get("loginStatus"),
    }

    version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"
    return {
        "providers": results,
        "ollama": ollama_detail,
        "codex": codex_detail,
        "chatgpt": chatgpt_detail,
        "version": version,
    }


def _validate_provider_connection(req: ConfigureRequest) -> dict[str, Any]:
    """LLM provider 연결 가능 여부만 검증한다."""
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.providers import create_provider
    from dartlab.engines.ai.types import LLMConfig

    current = get_config()
    effective_provider = _normalize_provider_name(req.provider) or req.provider
    kwargs: dict[str, Any] = {
        "provider": effective_provider,
        "model": req.model or current.model,
        "api_key": req.api_key,
        "base_url": req.base_url or current.base_url,
        "temperature": current.temperature,
        "max_tokens": current.max_tokens,
        "system_prompt": current.system_prompt,
    }

    available = False
    model = None
    try:
        config = LLMConfig(**kwargs)
        provider = create_provider(config)
        available = provider.check_available()
        model = provider.resolved_model
    except (FileNotFoundError, ImportError, OSError, PermissionError, RuntimeError, ValueError):
        available = False
        model = None

    return {"ok": True, "provider": effective_provider, "available": available, "model": model}


@app.post("/api/provider/validate")
def api_validate_provider(req: ConfigureRequest):
    """LLM provider 검증. 전역 상태는 변경하지 않는다."""
    return _validate_provider_connection(req)


@app.post("/api/configure")
def api_configure(req: ConfigureRequest):
    """구버전 alias. 현재는 provider 검증만 수행한다."""
    return _validate_provider_connection(req)


@app.get("/api/models/{provider}")
def api_models(provider: str):
    """Provider별 사용 가능한 모델 목록 — SDK/API 자동 조회, 실패시 fallback."""
    from dartlab.engines.ai.providers import create_provider
    from dartlab.engines.ai.types import LLMConfig

    provider = _normalize_provider_name(provider) or provider

    if provider == "codex":
        from dartlab.engines.ai.codex_cli import get_codex_model_catalog

        return {"models": get_codex_model_catalog()}

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

    if provider == "claude":
        models = _fetch_anthropic_models()
        if models:
            return {"models": models}
        return {
            "models": [
                "claude-opus-4-6",
                "claude-sonnet-4-6",
                "claude-opus-4-5",
                "claude-sonnet-4-5",
                "claude-haiku-4-5-20251001",
            ]
        }

    return {"models": []}


def _get_api_key(provider: str) -> str | None:
    """글로벌 config 또는 환경변수에서 API 키를 가져온다."""
    import os

    from dartlab.engines.ai import get_config

    config = get_config()
    if config.api_key and config.provider == provider:
        return config.api_key
    env_map = {"openai": "OPENAI_API_KEY", "claude": "ANTHROPIC_API_KEY"}
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
        for m in raw:
            mid = m.id
            if any(mid.startswith(p) for p in chat_prefixes):
                if not any(x in mid for x in exclude):
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

        def sort_key(name):
            for i, p in enumerate(priority):
                if name == p or name.startswith(p + "-"):
                    return (i, name)
            return (100, name)

        models.sort(key=sort_key)
        return models
    except (ImportError, OSError, RuntimeError, ValueError):
        return []


def _fetch_anthropic_models() -> list[str]:
    """Anthropic REST API로 모델 목록을 가져온다."""
    api_key = _get_api_key("claude")
    if not api_key:
        return []
    try:
        import requests
    except ImportError:
        return []

    try:
        resp = requests.get(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            timeout=5,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        models = [m["id"] for m in data.get("data", []) if "claude" in m.get("id", "")]
        priority = [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-opus-4-1",
            "claude-sonnet-4-0",
            "claude-haiku-4",
            "claude-3-",
        ]

        def sort_key(name):
            for i, p in enumerate(priority):
                if name.startswith(p):
                    return (i, name)
            return (100, name)

        models.sort(key=sort_key)
        return models
    except (OSError, ValueError, requests.RequestException):
        return []


@app.post("/api/codex/logout")
def api_codex_logout():
    """Codex CLI에 저장된 계정 인증을 제거한다."""
    from dartlab.engines.ai.codex_cli import logout_codex_cli

    try:
        logout_codex_cli()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True}


@app.get("/api/oauth/authorize")
def api_oauth_authorize():
    """ChatGPT OAuth 인증 시작 — 브라우저 로그인 URL 반환 + 로컬 콜백 서버 시작."""
    from dartlab.engines.ai.oauthToken import OAUTH_REDIRECT_PORT, build_auth_url

    auth_url, verifier, state = build_auth_url()

    _oauth_state["verifier"] = verifier
    _oauth_state["state"] = state
    _oauth_state["done"] = False
    _oauth_state["error"] = None

    _start_oauth_callback_server(OAUTH_REDIRECT_PORT)

    return {"authUrl": auth_url, "state": state}


@app.get("/api/oauth/status")
def api_oauth_status():
    """OAuth 인증 완료 여부 폴링."""
    if _oauth_state.get("error"):
        return {"done": True, "error": _oauth_state["error"]}
    if _oauth_state.get("done"):
        return {"done": True, "error": None}
    return {"done": False}


@app.post("/api/oauth/logout")
def api_oauth_logout():
    """OAuth 토큰 제거."""
    from dartlab.engines.ai.oauthToken import revoke_token

    revoke_token()
    return {"ok": True}


_oauth_state: dict = {}


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
                from dartlab.engines.ai.oauthToken import exchange_code

                exchange_code(code, _oauth_state["verifier"])
                _oauth_state["done"] = True
                self._respond_html("인증 성공", "DartLab 인증이 완료되었습니다. 이 창을 닫아주세요.")
            except _HANDLED_API_ERRORS as e:
                _oauth_state["error"] = str(e)
                _oauth_state["done"] = True
                self._respond_html("인증 실패", f"토큰 교환 실패: {e}")

        def _respond_html(self, title: str, message: str):
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{title}</title>"
                "<style>body{font-family:system-ui;display:flex;align-items:center;"
                "justify-content:center;min-height:100vh;margin:0;background:#050811;color:#e5e5e5}"
                "div{text-align:center;padding:2rem}"
                "h1{font-size:1.5rem;margin-bottom:1rem}"
                "</style></head><body>"
                f"<div><h1>{title}</h1><p>{message}</p></div>"
                "<script>setTimeout(()=>window.close(),3000)</script>"
                "</body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, fmt, *args):
            pass

    def _run_server():
        server = HTTPServer(("127.0.0.1", port), CallbackHandler)
        server.timeout = 120
        server.handle_request()
        server.server_close()

    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()


@app.post("/api/ollama/pull")
async def api_ollama_pull(req: dict):
    """Ollama 모델 다운로드 (SSE 스트리밍 진행률)."""
    model_name = req.get("model")
    if not model_name:
        raise HTTPException(400, "model name required")

    async def _stream_pull():
        import requests

        try:
            resp = requests.post(
                "http://localhost:11434/api/pull",
                json={"model": model_name, "stream": True},
                stream=True,
                timeout=600,
            )
            for line in resp.iter_lines():
                if line:
                    yield {
                        "event": "progress",
                        "data": line.decode("utf-8"),
                    }
            yield {"event": "done", "data": "{}"}
        except _HANDLED_API_ERRORS as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(_stream_pull(), media_type="text/event-stream")


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1)):
    """종목 검색."""
    try:
        df = dartlab.search(q)
        rows = df.to_dicts() if len(df) > 0 else []
        mapped = []
        for r in rows[:20]:
            mapped.append(
                {
                    "corpName": r.get("회사명", r.get("corpName", "")),
                    "stockCode": r.get("종목코드", r.get("stockCode", "")),
                    "market": r.get("시장구분", ""),
                    "sector": r.get("업종", ""),
                }
            )
        return {"results": mapped}
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=400, detail=str(e))


def _get_company(code: str) -> Company:
    """캐시 우선 Company 조회 — 뷰어 엔드포인트 공용."""
    cached = company_cache.get(code)
    if cached:
        return cached[0]
    c = Company(code)
    company_cache.put(code, c, None)
    return c


def _findPrevComparable(periods: list[str], target: str) -> str | None:
    """같은 보고서 유형의 직전 기간을 찾는다. (연간↔연간, Q1↔Q1)"""
    import re

    m = re.fullmatch(r"(\d{4})(Q[1-4])?", target)
    if not m:
        return None
    year, q = int(m.group(1)), m.group(2)
    # 같은 유형의 가장 가까운 이전 기간 찾기
    best: str | None = None
    bestYear = -1
    for p in periods:
        if p == target:
            continue
        pm = re.fullmatch(r"(\d{4})(Q[1-4])?", p)
        if not pm:
            continue
        pYear, pQ = int(pm.group(1)), pm.group(2)
        if q == pQ and pYear < year and pYear > bestYear:
            best = p
            bestYear = pYear
    return best


def _filterBlocksByPeriod(blocks: list, period: str) -> list:
    """viewerBlocks를 특정 period + 직전 동주기로 필터링한다."""
    import polars as pl

    filtered = []
    for block in blocks:
        if block.data is None:
            filtered.append(block)
            continue

        allPeriods = block.meta.periods if block.meta.periods else []
        if period not in allPeriods:
            # period가 없는 블록은 그대로 (finance 등)
            filtered.append(block)
            continue

        prev = _findPrevComparable(allPeriods, period)
        keepPeriods = [p for p in [period, prev] if p is not None and p in block.data.columns]
        nonPeriodCols = [c for c in block.data.columns if c not in allPeriods]
        selectCols = nonPeriodCols + keepPeriods

        from copy import copy

        newBlock = copy(block)
        newBlock.data = block.data.select([c for c in selectCols if c in block.data.columns])
        newBlock.meta = type(block.meta)(
            unit=block.meta.unit,
            scale=block.meta.scale,
            scaleDivisor=block.meta.scaleDivisor,
            periods=keepPeriods,
            rowCount=block.meta.rowCount,
            colCount=len(keepPeriods),
        )
        filtered.append(newBlock)
    return filtered


@app.get("/api/company/{code}")
def api_company(code: str):
    """기업 기본 정보 + 현재 공개 surface 안내."""
    try:
        c = _get_company(code)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "surface": {
                "index": f"/api/company/{c.stockCode}/index",
                "show": f"/api/company/{c.stockCode}/show/{{topic}}",
                "trace": f"/api/company/{c.stockCode}/trace/{{topic}}",
            },
            "profile": {
                "status": "roadmap",
                "description": "변화 지점을 문서처럼 읽는 company report view가 추후 추가될 예정입니다.",
            },
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/index")
def api_company_index(code: str):
    """Company index DataFrame."""
    try:
        c = _get_company(code)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "payload": _serialize_payload(c.index),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/sections")
def api_company_sections(code: str):
    """Company sections — 전체 지도."""
    try:
        c = _get_company(code)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "payload": _serialize_payload(c.sections, max_rows=5000),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/toc")
def api_company_toc(code: str):
    """뷰어용 목차 — chapter/topic 트리 + text/table 블록 카운트."""
    try:
        c = _get_company(code)
        sec = c.sections
        if sec is None:
            return TocResponse(stockCode=c.stockCode, corpName=c.corpName, chapters=[])

        import polars as pl

        chapterMap: dict[str, list[TocTopic]] = {}
        chapterOrder: list[str] = []
        seenTopics: set[str] = set()

        # finance topics 먼저 추가 (III장)
        _FINANCE_TOPICS = ("BS", "IS", "CIS", "CF", "SCE", "ratios")
        financeChapter = "III. 재무에 관한 사항"
        for ft in _FINANCE_TOPICS:
            df = getattr(c, ft, None) if ft != "ratios" else None
            if ft == "ratios":
                rsPair = c._ratioSeries() if c._hasFinance else None
                if rsPair is None:
                    continue
            elif df is None:
                continue
            seenTopics.add(ft)
            if financeChapter not in chapterMap:
                chapterMap[financeChapter] = []
                chapterOrder.append(financeChapter)
            chapterMap[financeChapter].append(TocTopic(topic=ft, label=c._topicLabel(ft), textCount=0, tableCount=1))

        # sections topics
        if "topic" in sec.columns:
            for row in sec.iter_rows(named=True):
                topic = row.get("topic")
                if not isinstance(topic, str) or not topic or topic in seenTopics:
                    continue
                seenTopics.add(topic)

                topicFrame = sec.filter(pl.col("topic") == topic)
                bt = topicFrame["blockType"] if "blockType" in topicFrame.columns else None
                textCount = bt.eq("text").sum() if bt is not None else topicFrame.height
                tableCount = bt.eq("table").sum() if bt is not None else 0

                chapterVal = topicFrame.item(0, "chapter") if "chapter" in topicFrame.columns else None
                chapter = chapterVal if isinstance(chapterVal, str) and chapterVal else "기타"
                if chapter not in chapterMap:
                    chapterMap[chapter] = []
                    chapterOrder.append(chapter)
                chapterMap[chapter].append(
                    TocTopic(
                        topic=topic,
                        label=c._topicLabel(topic),
                        textCount=int(textCount),
                        tableCount=int(tableCount),
                    )
                )

        chapters = [TocChapter(chapter=ch, topics=chapterMap[ch]) for ch in chapterOrder]
        return TocResponse(stockCode=c.stockCode, corpName=c.corpName, chapters=chapters)
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/viewer/{topic}")
def api_company_viewer_topic(
    code: str,
    topic: str,
    period: str | None = Query(None, description="특정 기간만 반환 (타임라인 클릭 최적화)"),
):
    """뷰어 전용 — topic의 viewerBlocks + textDocument.

    period 생략 → 전체 기간 반환 (초기 로드).
    period 지정 → 해당 기간 + 직전 동주기만 포함한 경량 응답 (타임라인 클릭).
    """
    try:
        from dartlab.engines.dart.docs.viewer import (
            serializeViewerBlock,
            serializeViewerTextDocument,
            viewerBlocks,
            viewerTextDocument,
        )

        c = _get_company(code)
        blocks = viewerBlocks(c, topic)

        if period is not None:
            blocks = _filterBlocksByPeriod(blocks, period)

        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "topicLabel": c._topicLabel(topic),
            "period": period,
            "blocks": [serializeViewerBlock(b) for b in blocks],
            "textDocument": serializeViewerTextDocument(viewerTextDocument(topic, blocks)),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/show/{topic}/all")
def api_company_show_all(code: str, topic: str, raw: bool = Query(False)):
    """topic의 모든 블록 데이터를 viewer 레이어 경유로 반환.

    각 블록에 kind(finance/text/structured/raw_markdown/report),
    meta(unit/scale/periods), changeSummary(text 변천사),
    textDocument(텍스트 전용 timeline 문서)를 포함한다.
    """
    try:
        from dartlab.engines.dart.docs.viewer import (
            serializeViewerBlock,
            serializeViewerTextDocument,
            viewerBlocks,
            viewerTextDocument,
        )

        c = _get_company(code)
        blocks = viewerBlocks(c, topic)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "blocks": [serializeViewerBlock(b) for b in blocks],
            "textDocument": serializeViewerTextDocument(viewerTextDocument(topic, blocks)),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/company/{code}/show/{topic}/{block_idx}/parse")
async def api_parse_raw_table(code: str, topic: str, block_idx: int):
    """raw_markdown 블록을 AI로 구조화된 DataFrame으로 변환."""
    try:
        from dartlab.engines.dart.docs.tableAI import parseRawMarkdownBlock
        from dartlab.engines.dart.docs.viewer import viewerBlocks

        c = _get_company(code)
        blocks = viewerBlocks(c, topic)
        target = None
        for b in blocks:
            if b.block == block_idx and b.kind == "raw_markdown":
                target = b
                break
        if target is None:
            raise HTTPException(status_code=404, detail="raw_markdown 블록이 아님")

        result = await parseRawMarkdownBlock(target.rawMarkdown, topic, block_idx)
        return {
            "stockCode": c.stockCode,
            "topic": topic,
            "block": block_idx,
            "parsed": result,
        }
    except HTTPException:
        raise
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/company/{code}/show/{topic}")
def api_company_show(code: str, topic: str, block: int | None = Query(None), raw: bool = Query(False)):
    """Company topic payload.

    block=None → 블록 목차, block=N → 실제 데이터.
    """
    try:
        c = _get_company(code)
        if block is not None:
            result = c.show(topic, block, period=None, raw=raw)
        else:
            result = c.show(topic)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "block": block,
            "payload": _serialize_payload(result),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/trace/{topic}")
def api_company_trace(code: str, topic: str):
    """Company topic source trace."""
    try:
        c = _get_company(code)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "payload": _serialize_payload(c.trace(topic)),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/summary/{topic}")
async def api_company_topic_summary(code: str, topic: str):
    """topic별 AI 요약 생성 (SSE 스트리밍)."""
    try:
        c = _get_company(code)
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))

    result = build_topic_summary_prompt(c, topic)
    if result is None:
        raise HTTPException(status_code=404, detail=f"topic '{topic}' 데이터 없음")

    messages, context_text = result

    async def _generate():
        from dartlab.engines.ai import get_config
        from dartlab.engines.ai.providers import create_provider

        yield {
            "event": "context",
            "data": json.dumps(
                {"module": "_topic_summary", "label": f"{topic} 요약 근거", "text": context_text},
                ensure_ascii=False,
            ),
        }

        try:
            config_ = get_config()
            llm = create_provider(config_)

            def _stream():
                yield from llm.stream(messages)

            gen = _stream()
            while True:
                chunk = await asyncio.to_thread(next, gen, None)
                if chunk is None:
                    break
                yield {
                    "event": "chunk",
                    "data": json.dumps({"text": chunk}, ensure_ascii=False),
                }
        except (ImportError, OSError, RuntimeError, ValueError) as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False),
            }

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(_generate())


@app.get("/api/company/{code}/diff")
def api_company_diff(code: str):
    """Company sections 전체 diff 요약."""
    try:
        c = _get_company(code)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "payload": _serialize_payload(c.diff()),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/diff/{topic}/summary")
def api_company_diff_topic_summary(code: str, topic: str):
    """뷰어용 diff 요약 — changeRate + 최신 변경의 added/removed 미리보기."""
    try:
        from dartlab.engines.common.docs.diff import sectionsDiff

        c = _get_company(code)
        sec = c.docs.sections
        if sec is None:
            raise HTTPException(status_code=404, detail="sections 없음")

        diffResult = sectionsDiff(sec)
        # topic에 해당하는 모든 row summary 집계
        topicSummaries = [s for s in diffResult.summaries if s.topic == topic]
        totalChanged = sum(s.changedCount for s in topicSummaries)
        maxPeriods = max((s.totalPeriods for s in topicSummaries), default=0)
        changeRate = round(totalChanged / max(1, (maxPeriods - 1) * len(topicSummaries)), 3) if topicSummaries else 0.0
        changedCount = totalChanged
        totalPeriods = maxPeriods

        # 최신 변경쌍의 added/removed 미리보기
        topicEntries = [e for e in diffResult.entries if e.topic == topic]
        added: list[str] = []
        removed: list[str] = []
        latestFrom: str | None = None
        latestTo: str | None = None

        if topicEntries:
            latest = max(topicEntries, key=lambda e: e.toPeriod)
            latestFrom = latest.fromPeriod
            latestTo = latest.toPeriod

            # sections에서 해당 topic의 모든 row에서 실제 변화 추출
            import difflib
            import polars as pl

            filtered = sec.filter(pl.col("topic") == topic)
            for row in filtered.iter_rows(named=True):
                fromText = str(row.get(latestFrom) or "").strip()
                toText = str(row.get(latestTo) or "").strip()
                if not fromText and not toText:
                    continue
                if fromText == toText:
                    continue
                # 줄 단위 diff
                fromLines = fromText.splitlines()
                toLines = toText.splitlines()
                for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, fromLines, toLines).get_opcodes():
                    if tag in ("insert", "replace"):
                        for line in toLines[j1:j2]:
                            line = line.strip()
                            if line and len(added) < 3:
                                added.append(line[:120])
                    if tag in ("delete", "replace"):
                        for line in fromLines[i1:i2]:
                            line = line.strip()
                            if line and len(removed) < 3:
                                removed.append(line[:120])
                if len(added) >= 3 and len(removed) >= 3:
                    break

        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "changeRate": changeRate,
            "changedCount": changedCount,
            "totalPeriods": totalPeriods,
            "latestFrom": latestFrom,
            "latestTo": latestTo,
            "added": added,
            "removed": removed,
        }
    except HTTPException:
        raise
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/diff/{topic}")
def api_company_diff_topic(
    code: str,
    topic: str,
    fromPeriod: str = Query(..., alias="from"),
    toPeriod: str = Query(..., alias="to"),
):
    """Company 특정 topic의 두 기간 줄 단위 diff."""
    try:
        c = _get_company(code)
        result = c.diff(topic, fromPeriod, toPeriod)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "fromPeriod": fromPeriod,
            "toPeriod": toPeriod,
            "payload": _serialize_payload(result),
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/modules")
def api_company_modules(code: str):
    """기업의 사용 가능한 데이터 모듈 목록."""
    try:
        from dartlab.engines.ai.context import scan_available_modules

        c = _get_company(code)
        modules = scan_available_modules(c)
        return {"stockCode": c.stockCode, "corpName": c.corpName, "modules": modules}
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/data/sources/{code}")
async def api_data_sources(code: str):
    """경량 데이터 소스 목록 — registry 메타 + 파일 존재 여부만 확인 (빠름).

    discoverSources와 달리 getattr로 실제 데이터를 로드하지 않는다.
    Company 생성 + _hasFinance/_hasDocs/_hasReport 3개 플래그만 확인.
    """
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    from dartlab.core.registry import getEntries

    hasFlags = {
        "finance": c._hasFinance,
        "docs": c._hasDocs,
        "report": c._hasReport,
    }

    categoryOrder = ["finance", "report", "disclosure", "notes", "analysis", "raw"]
    categories: dict[str, list[dict]] = {}
    totalAvailable = 0

    for entry in getEntries():
        req = entry.requires or ""
        if req:
            available = hasFlags.get(req, False)
        else:
            available = True

        item = {
            "name": entry.name,
            "label": entry.label,
            "dataType": entry.dataType,
            "description": entry.description,
            "available": available,
        }
        categories.setdefault(entry.category, []).append(item)
        if available:
            totalAvailable += 1

    ordered: dict[str, list[dict]] = {}
    for cat in categoryOrder:
        if cat in categories:
            ordered[cat] = categories[cat]
    for cat in categories:
        if cat not in ordered:
            ordered[cat] = categories[cat]

    totalSources = sum(len(v) for v in ordered.values())

    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "totalSources": totalSources,
        "availableSources": totalAvailable,
        "categories": ordered,
    }


@app.get("/api/export/modules/{code}")
async def api_export_modules(code: str):
    """Excel 내보내기 가능한 모듈 목록."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    from dartlab.export.excel import listAvailableModules

    modules = await asyncio.to_thread(listAvailableModules, c)
    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "modules": modules,
    }


@app.get("/api/export/sources/{code}")
async def api_export_sources(code: str):
    """데이터 소스 디스커버리 — registry 기반 전체 소스 트리."""
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    from dartlab.export.sources import discoverSources

    tree = await asyncio.to_thread(discoverSources, c)
    return tree.toDict()


@app.get("/api/export/templates")
def api_export_templates():
    """저장된 템플릿 목록 (프리셋 포함)."""
    from dartlab.export.store import TemplateStore

    store = TemplateStore()
    templates = store.list()
    return {
        "templates": [t.toDict() for t in templates],
    }


@app.get("/api/export/templates/{template_id}")
def api_export_template_get(template_id: str):
    """단일 템플릿 조회."""
    from dartlab.export.store import TemplateStore

    store = TemplateStore()
    t = store.get(template_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"템플릿 '{template_id}'을 찾을 수 없습니다")
    return t.toDict()


@app.post("/api/export/templates")
def api_export_template_save(req: dict):
    """템플릿 저장 (신규 or 업데이트)."""
    from dartlab.export.store import TemplateStore
    from dartlab.export.template import ExcelTemplate

    store = TemplateStore()
    t = ExcelTemplate.fromDict(req)
    tid = store.save(t)
    return {"ok": True, "templateId": tid}


@app.delete("/api/export/templates/{template_id}")
def api_export_template_delete(template_id: str):
    """템플릿 삭제."""
    from dartlab.export.store import TemplateStore

    store = TemplateStore()
    deleted = store.delete(template_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="프리셋 템플릿은 삭제할 수 없습니다")
    return {"ok": True}


@app.get("/api/export/excel/{code}")
async def api_export_excel(
    code: str,
    modules: str | None = Query(None, description="쉼표 구분 모듈: IS,BS,CF,ratios,dividend,employee"),
    template_id: str | None = Query(None, description="템플릿 ID (preset_full, preset_summary 등)"),
):
    """Excel 파일 내보내기 — .xlsx 다운로드."""
    import tempfile

    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    tmpDir = Path(tempfile.gettempdir())
    safeName = c.corpName.replace("/", "_").replace("\\", "_")

    if template_id:
        from dartlab.export.excel import exportWithTemplate
        from dartlab.export.store import TemplateStore

        store = TemplateStore()
        tmpl = store.get(template_id)
        if tmpl is None:
            raise HTTPException(status_code=404, detail=f"템플릿 '{template_id}'을 찾을 수 없습니다")
        templateSafe = tmpl.name.replace("/", "_").replace("\\", "_")
        outPath = tmpDir / f"{c.stockCode}_{safeName}_{templateSafe}.xlsx"
        try:
            await asyncio.to_thread(exportWithTemplate, c, tmpl, outPath)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return FileResponse(
            path=str(outPath),
            filename=f"{c.stockCode}_{safeName}_{templateSafe}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    modList = [m.strip() for m in modules.split(",")] if modules else None
    outPath = tmpDir / f"{c.stockCode}_{safeName}.xlsx"

    try:
        from dartlab.export.excel import exportToExcel

        await asyncio.to_thread(exportToExcel, c, outputPath=outPath, modules=modList)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return FileResponse(
        path=str(outPath),
        filename=f"{c.stockCode}_{safeName}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _resolve_module_data(c: Company, entry) -> Any:
    """registry entry에서 실제 데이터를 추출한다.

    finance 시계열(annual.IS, timeseries.CF 등)은 series dict → DataFrame 변환.
    extractor가 있는 모듈은 raw 데이터에 extractor를 적용.
    callable(메서드)은 호출하여 결과를 반환.
    dataclass/Enum은 dict/str로 변환.
    """
    import dataclasses
    import enum

    import polars as pl

    name = entry.name

    if name.startswith("annual.") or name.startswith("timeseries."):
        prefix, stmt = name.split(".", 1)
        prop = "annual" if prefix == "annual" else "timeseries"
        result = getattr(c, prop, None)
        if result is None:
            return None
        series, periods = result
        stmt_data = series.get(stmt)
        if not stmt_data or not periods:
            return None

        from dartlab.engines.dart.finance.mapper import AccountMapper

        order = AccountMapper.get().sortOrder(stmt)

        rows = []
        for account, values in stmt_data.items():
            row = {"계정명": account}
            for i, p in enumerate(periods):
                row[str(p)] = values[i] if i < len(values) else None
            rows.append(row)
        if not rows:
            return None
        if order:
            rows.sort(key=lambda r: order.get(r["계정명"], 9999))
        return pl.DataFrame(rows)

    attrName = entry.funcName or entry.name
    if name in ("IS", "BS", "CF"):
        attrName = name

    data = getattr(c, attrName, None)
    if data is None:
        return None

    if callable(data) and not isinstance(data, (pl.DataFrame, dict, str)):
        data = data()

    if entry.extractor:
        try:
            data = entry.extractor(data)
        except (AttributeError, TypeError):
            pass

    if dataclasses.is_dataclass(data) and not isinstance(data, type):
        data = {k: v for k, v in dataclasses.asdict(data).items() if v is not None}

    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, enum.Enum):
                cleaned[k] = v.value
            elif isinstance(v, (list, tuple)):
                cleaned[k] = [item.value if isinstance(item, enum.Enum) else item for item in v]
            else:
                cleaned[k] = v
        data = cleaned

    return data


def _build_finance_meta(moduleName: str) -> dict[str, Any]:
    """finance 시계열 모듈의 메타데이터 — 한글 라벨, 정렬, 레벨 정보."""
    if not moduleName.startswith("annual.") and not moduleName.startswith("timeseries."):
        return {}

    _, stmt = moduleName.split(".", 1)
    from dartlab.engines.dart.finance.mapper import AccountMapper

    mapper = AccountMapper.get()
    labels = mapper.labelMap()
    order = mapper.sortOrder(stmt)
    levels = mapper.levelMap(stmt)

    return {
        "labels": labels,
        "sortOrder": order,
        "levels": levels,
        "unit": "원",
        "stmtType": stmt,
    }


@app.get("/api/data/preview/{code}/{module}")
async def api_data_preview(code: str, module: str, max_rows: int = Query(50, ge=1, le=500)):
    """데이터 미리보기 — 모듈 데이터를 JSON으로 반환 (테이블/텍스트).

    finance 시계열의 경우 meta에 labels/sortOrder/levels 포함.
    """
    try:
        c = await asyncio.to_thread(Company, code)
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=404, detail=str(e))

    from dartlab.core.registry import getEntry

    entry = getEntry(module)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"모듈 '{module}'을 찾을 수 없습니다")

    import polars as pl

    try:
        data = await asyncio.to_thread(_resolve_module_data, c, entry)
    except (AttributeError, ValueError, OSError, KeyError, TypeError) as e:
        raise HTTPException(status_code=404, detail=f"데이터를 가져올 수 없습니다: {e}")

    if data is None:
        raise HTTPException(status_code=404, detail="데이터가 없습니다")

    if isinstance(data, pl.DataFrame):
        if "year" in data.columns:
            data = data.sort("year")
        preview = data.head(max_rows)
        rows = preview.to_dicts()
        for row in rows:
            for k, v in row.items():
                if v is not None and not isinstance(v, (str, int, float, bool)):
                    row[k] = str(v)
        result: dict[str, Any] = {
            "type": "table",
            "module": module,
            "label": entry.label,
            "unit": entry.unit,
            "columns": preview.columns,
            "rows": rows,
            "totalRows": data.height,
            "truncated": data.height > max_rows,
        }
        financeMeta = _build_finance_meta(module)
        if financeMeta:
            result["meta"] = financeMeta
        return result

    if isinstance(data, dict):
        flat: dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, pl.DataFrame):
                continue
            if isinstance(v, list) and v and isinstance(v[0], dict):
                flat[k] = json.dumps(v, ensure_ascii=False, default=str)
            elif isinstance(v, dict):
                flat[k] = json.dumps(v, ensure_ascii=False, default=str)
            elif isinstance(v, (str, int, float, bool, type(None))):
                flat[k] = v
            else:
                flat[k] = str(v)
        return {
            "type": "dict",
            "module": module,
            "label": entry.label,
            "unit": entry.unit,
            "data": flat,
        }

    if isinstance(data, str):
        truncated = len(data) > 5000
        return {
            "type": "text",
            "module": module,
            "label": entry.label,
            "text": data[:5000] if truncated else data,
            "truncated": truncated,
        }

    return {
        "type": "unknown",
        "module": module,
        "label": entry.label,
        "data": str(data)[:2000],
    }


@app.get("/api/data/stats")
def api_data_stats():
    """로컬 데이터 현황 — 문서/재무 파일 수, dartlab 버전."""
    from dartlab.core.dataLoader import _dataDir

    stats: dict[str, Any] = {
        "version": dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown",
    }
    for category in ("docs", "finance"):
        try:
            d = _dataDir(category)
            if d.exists():
                files = list(d.glob("*.parquet"))
                stats[category] = {"count": len(files), "path": str(d)}
            else:
                stats[category] = {"count": 0, "path": str(d)}
        except _HANDLED_API_ERRORS:
            stats[category] = {"count": 0, "path": ""}
    return stats


@app.get("/api/spec")
def api_spec(engine: str | None = None, section: str | None = None):
    """시스템 스펙 조회 — LLM/MCP/외부 클라이언트용."""
    from dartlab.engines.ai.spec import buildSpec, getEngineSpec

    if engine:
        result = getEngineSpec(engine, section)
        if result is None:
            raise HTTPException(status_code=404, detail=f"엔진 '{engine}'을 찾을 수 없습니다")
        return result
    depth = "detail" if section == "detail" else "summary"
    return buildSpec(depth=depth)


@app.post("/api/ask")
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
        return await _plain_chat(req)

    try:
        answer = await asyncio.to_thread(
            c.ask,
            req.question,
            include=req.include,
            exclude=req.exclude,
            provider=_normalize_provider_name(req.provider) or req.provider,
            model=req.model,
            api_key=req.api_key,
            base_url=req.base_url,
        )
        return {
            "company": c.corpName,
            "stockCode": c.stockCode,
            "answer": answer,
        }
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _plain_chat(req: AskRequest):
    """종목 없는 순수 LLM 대화."""
    from dartlab.engines.ai import get_config
    from dartlab.engines.ai.providers import create_provider

    config_ = get_config()
    overrides: dict[str, Any] = {}
    if req.provider:
        overrides["provider"] = _normalize_provider_name(req.provider) or req.provider
    if req.model:
        overrides["model"] = req.model
    if req.api_key:
        overrides["api_key"] = req.api_key
    if req.base_url:
        overrides["base_url"] = req.base_url
    if overrides:
        config_ = config_.merge(overrides)

    state = build_conversation_state(
        req.question,
        history=req.history,
        view_context=req.viewContext,
    )
    messages = [{"role": "system", "content": build_dynamic_chat_prompt(state)}]
    messages.extend(build_history_messages(req.history))
    messages.append({"role": "user", "content": state.question})

    llm = create_provider(config_)
    try:
        answer = await asyncio.to_thread(llm.complete, messages)
        return {"answer": answer}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Codex CLI 로그인이 필요합니다. `codex login`을 실행하세요.")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except _HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Static Files (Svelte build) ──

_UI_DIR = Path(__file__).parent.parent / "ui" / "build"

if _UI_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(_UI_DIR / "assets")), name="assets")


@app.get("/{path:path}")
def serve_spa(path: str = ""):
    """SPA fallback — index.html 반환."""
    if not _UI_DIR.exists():
        return HTMLResponse(
            "<h2>DartLab UI not built</h2><p>Run: <code>cd src/dartlab/ui && npm install && npm run build</code></p>",
            status_code=503,
        )

    file = _UI_DIR / path
    if path and file.is_file():
        return FileResponse(file)

    index = _UI_DIR / "index.html"
    if index.exists():
        return FileResponse(
            index,
            media_type="text/html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    return HTMLResponse("<h2>index.html not found</h2>", status_code=404)


def _is_dartlab_alive(port: int) -> bool:
    """DartLab 서버가 살아있는지 health check."""
    import urllib.request

    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=2)
        return resp.status == 200
    except (OSError, urllib.error.URLError):
        return False


def _kill_port(port: int) -> bool:
    """포트를 점유 중인 좀비 프로세스를 종료한다. 성공 시 True."""
    import platform
    import subprocess
    import time

    system = platform.system()
    pids: set[int] = set()

    if system == "Windows":
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                pid = int(parts[4])
                if pid > 0:
                    pids.add(pid)
    else:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.strip().splitlines():
            if line.strip().isdigit():
                pids.add(int(line.strip()))

    if not pids:
        return False

    import os

    my_pid = os.getpid()
    for pid in pids:
        if pid == my_pid:
            continue
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
        else:
            import signal

            os.kill(pid, signal.SIGTERM)

    time.sleep(0.5)
    return True


def ensure_port(port: int) -> str:
    """포트 확보. "ok" | "already_running" | "failed" 반환."""
    import socket
    import sys

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", port))
        sock.close()
        return "ok"
    except OSError:
        pass

    if _is_dartlab_alive(port):
        print(f"\n  기존 서버 종료 중 (포트 {port})...")
    else:
        print(f"\n  포트 {port} 사용 중 (좀비) — 기존 프로세스 종료 중...")
    if _kill_port(port):
        print("  종료 완료. 재시작합니다.\n")
        return "ok"

    print(f"\n  오류: 포트 {port}을 해제할 수 없습니다.", file=sys.stderr)
    print(f"  다른 포트를 사용하세요: dartlab ai --port {port + 1}\n", file=sys.stderr)
    return "failed"


def run_server(host: str | None = None, port: int = 8400):
    """서버 실행 (blocking)."""
    import uvicorn

    resolved_host = host or _default_host()
    os.environ["DARTLAB_HOST"] = resolved_host
    uvicorn.run("dartlab.server:app", host=resolved_host, port=port, log_level="info")
