"""DartLab Web Server — FastAPI + SSE 스트리밍.

dartlab ai 명령으로 실행:
    dartlab ai              # http://localhost:8400
    dartlab ai --port 9000  # 커스텀 포트
"""

from __future__ import annotations

import asyncio
import importlib.resources
import json
import traceback
from pathlib import Path
from typing import Any, Generator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

import dartlab
from dartlab import Company


app = FastAPI(title="DartLab", version=dartlab.__version__ if hasattr(dartlab, "__version__") else "0.2.0")


@app.on_event("startup")
async def _preload_ollama():
	"""서버 시작 시 Ollama 모델을 메모리에 미리 로딩 (cold start 제거)."""
	try:
		from dartlab.engines.llmAnalyzer.providers import create_provider
		from dartlab.engines.llmAnalyzer.types import LLMConfig

		config = LLMConfig(provider="ollama")
		provider = create_provider(config)
		if hasattr(provider, "preload") and provider.check_available():
			import asyncio
			ok = await asyncio.to_thread(provider.preload)
			if ok:
				print(f"  Ollama 모델 preload 완료: {provider.resolved_model}")
	except Exception:
		pass


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)


# ── Models ──

class HistoryMessage(BaseModel):
	role: str  # "user" | "assistant"
	text: str


class AskRequest(BaseModel):
	company: str | None = None
	question: str
	provider: str | None = None
	model: str | None = None
	include: list[str] | None = None
	exclude: list[str] | None = None
	stream: bool = False
	history: list[HistoryMessage] | None = None  # 이전 대화 기록


class ConfigureRequest(BaseModel):
	provider: str = "codex"
	model: str | None = None
	api_key: str | None = None
	base_url: str | None = None


# ── API Routes ──

@app.get("/api/status")
def api_status():
	"""LLM provider 상태 확인 (설치/인증/모델 포함)."""
	from dartlab.engines.llmAnalyzer.providers import create_provider
	from dartlab.engines.llmAnalyzer.types import LLMConfig

	# TODO: claude-code, codex, openai, claude — CLI/API 키 문제 해결 후 복원
	# providers_list = ["codex", "claude-code", "ollama", "openai", "claude"]
	providers_list = ["ollama"]
	results = {}

	# Provider별 메타 정보
	meta = {
		# "openai": {"label": "OpenAI", "desc": "GPT-5.4, o4-mini 등", "auth": "api_key", "envKey": "OPENAI_API_KEY"},
		# "claude": {"label": "Anthropic Claude", "desc": "Opus 4.6, Sonnet 4.6 등", "auth": "api_key", "envKey": "ANTHROPIC_API_KEY"},
		"ollama": {"label": "Ollama (로컬)", "desc": "무료, 오프라인, 프라이빗", "auth": "none"},
		# "claude-code": {"label": "Claude Code", "desc": "Claude CLI 기반", "auth": "cli"},
		# "codex": {"label": "OpenAI Codex", "desc": "Codex CLI 기반", "auth": "cli"},
	}

	for prov in providers_list:
		info = {"available": False, "model": None, **(meta.get(prov, {}))}
		try:
			config = LLMConfig(provider=prov)
			provider = create_provider(config)
			available = provider.check_available()
			info["available"] = available
			info["model"] = provider.resolved_model
		except Exception:
			pass
		results[prov] = info

	# Ollama 추가 상태 (설치/실행/GPU)
	ollama_detail = {}
	try:
		from dartlab.engines.llmAnalyzer.ollama_setup import detect_ollama, get_install_guide
		ollama_info = detect_ollama()
		ollama_detail["installed"] = ollama_info.get("installed", False)
		ollama_detail["running"] = ollama_info.get("running", False)
		ollama_detail["gpu"] = ollama_info.get("gpu", None)
		if not ollama_info.get("installed"):
			ollama_detail["installGuide"] = get_install_guide()
	except Exception:
		ollama_detail["installed"] = False
		ollama_detail["running"] = False

	return {"providers": results, "ollama": ollama_detail}


@app.post("/api/configure")
def api_configure(req: ConfigureRequest):
	"""LLM provider 설정. API 키 검증 포함."""
	from dartlab.engines.llmAnalyzer import configure, get_config
	from dartlab.engines.llmAnalyzer.providers import create_provider
	from dartlab.engines.llmAnalyzer.types import LLMConfig

	# 기존 설정을 유지하면서 새 값만 오버라이드
	current = get_config()
	kwargs: dict[str, Any] = {"provider": req.provider}
	if req.model:
		kwargs["model"] = req.model
	if req.api_key:
		kwargs["api_key"] = req.api_key
	elif current.api_key and current.provider == req.provider:
		# 같은 provider면 기존 API 키 유지
		kwargs["api_key"] = current.api_key
	if req.base_url:
		kwargs["base_url"] = req.base_url
	elif current.base_url and current.provider == req.provider:
		kwargs["base_url"] = current.base_url
	configure(**kwargs)

	# 설정 후 실제 사용 가능한지 체크
	available = False
	model = None
	try:
		config = LLMConfig(**kwargs)
		provider = create_provider(config)
		available = provider.check_available()
		model = provider.resolved_model
	except Exception:
		pass

	return {"ok": True, "provider": req.provider, "available": available, "model": model}


@app.get("/api/models/{provider}")
def api_models(provider: str):
	"""Provider별 사용 가능한 모델 목록 — SDK/API 자동 조회, 실패시 fallback."""
	from dartlab.engines.llmAnalyzer.providers import create_provider
	from dartlab.engines.llmAnalyzer.types import LLMConfig

	# CLI 기반 provider: 별칭 + 주요 모델ID
	CLI_MODELS = {
		"claude-code": [
			"opus",               # 최신 Opus (현재 4.6)
			"sonnet",             # 최신 Sonnet (현재 4.6)
			"haiku",              # 최신 Haiku (현재 4.5)
			"claude-opus-4-6",
			"claude-sonnet-4-6",
			"claude-haiku-4-5-20251001",
			"claude-opus-4-5",
			"claude-sonnet-4-5",
		],
		"codex": [
			"gpt-5.4",
			"gpt-5.4-pro",
			"gpt-5.3-codex",
			"gpt-5.2",
			"gpt-5.2-codex",
			"o4-mini",
			"o3",
			"gpt-4.1",
			"gpt-4.1-mini",
		],
	}
	if provider in CLI_MODELS:
		return {"models": CLI_MODELS[provider]}

	# Ollama: 로컬 설치된 모델 조회 + 추천 정보
	if provider == "ollama":
		try:
			config = LLMConfig(provider="ollama")
			prov = create_provider(config)
			installed = prov.get_installed_models()
			return {
				"models": installed,
				"recommendations": _OLLAMA_MODEL_GUIDE,
			}
		except Exception:
			return {"models": [], "recommendations": _OLLAMA_MODEL_GUIDE}

	# OpenAI: SDK의 models.list() 사용
	if provider == "openai":
		models = _fetch_openai_models()
		if models:
			return {"models": models}
		# API 키 없거나 실패시 fallback
		return {"models": [
			"gpt-5.4", "gpt-5.4-pro",
			"gpt-5.2", "gpt-5.2-pro",
			"gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
			"o4-mini", "o3", "o3-mini",
			"gpt-4o", "gpt-4o-mini",
		]}

	# Claude: REST API로 조회
	if provider == "claude":
		models = _fetch_anthropic_models()
		if models:
			return {"models": models}
		return {"models": [
			"claude-opus-4-6",
			"claude-sonnet-4-6",
			"claude-opus-4-5",
			"claude-sonnet-4-5",
			"claude-haiku-4-5-20251001",
		]}

	return {"models": []}


def _get_api_key(provider: str) -> str | None:
	"""글로벌 config 또는 환경변수에서 API 키를 가져온다."""
	import os
	from dartlab.engines.llmAnalyzer import get_config
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
		# 채팅 가능한 모델만 필터링
		chat_prefixes = ("gpt-5", "gpt-4", "gpt-3.5", "o1", "o3", "o4")
		exclude = ("realtime", "audio", "search", "instruct", "embedding", "tts", "whisper", "dall-e", "davinci", "babbage", "transcribe")
		models = []
		for m in raw:
			mid = m.id
			if any(mid.startswith(p) for p in chat_prefixes):
				if not any(x in mid for x in exclude):
					models.append(mid)
		# 정렬: 최신/인기 순
		priority = [
			"gpt-5.4", "gpt-5.4-pro", "gpt-5.3-codex", "gpt-5.2", "gpt-5.2-pro", "gpt-5.2-codex",
			"gpt-5.1", "gpt-5", "gpt-5-mini",
			"gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
			"gpt-4o", "gpt-4o-mini",
			"o4-mini", "o3", "o3-mini", "o1", "o1-mini",
		]
		def sort_key(name):
			for i, p in enumerate(priority):
				if name == p or name.startswith(p + "-"):
					return (i, name)
			return (100, name)
		models.sort(key=sort_key)
		return models
	except Exception:
		return []


def _fetch_anthropic_models() -> list[str]:
	"""Anthropic REST API로 모델 목록을 가져온다 (SDK에 models.list 없음)."""
	api_key = _get_api_key("claude")
	if not api_key:
		return []
	try:
		import requests
		resp = requests.get(
			"https://api.anthropic.com/v1/models",
			headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
			timeout=5,
		)
		if resp.status_code != 200:
			return []
		data = resp.json()
		models = [m["id"] for m in data.get("data", []) if "claude" in m.get("id", "")]
		# 정렬: 최신 먼저
		priority = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-opus-4-5", "claude-sonnet-4-5", "claude-opus-4-1", "claude-sonnet-4-0", "claude-haiku-4", "claude-3-"]
		def sort_key(name):
			for i, p in enumerate(priority):
				if name.startswith(p):
					return (i, name)
			return (100, name)
		models.sort(key=sort_key)
		return models
	except Exception:
		return []


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
		except Exception as e:
			yield {"event": "error", "data": json.dumps({"error": str(e)})}

	return EventSourceResponse(_stream_pull(), media_type="text/event-stream")


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1)):
	"""종목 검색."""
	try:
		df = Company.search(q)
		rows = df.to_dicts() if len(df) > 0 else []
		# 한글 컬럼명 → 영문 매핑
		mapped = []
		for r in rows[:20]:
			mapped.append({
				"corpName": r.get("회사명", r.get("corpName", "")),
				"stockCode": r.get("종목코드", r.get("stockCode", "")),
				"market": r.get("시장구분", ""),
				"sector": r.get("업종", ""),
			})
		return {"results": mapped}
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/company/{code}")
def api_company(code: str):
	"""기업 기본 정보."""
	try:
		c = Company(code)
		return {
			"stockCode": c.stockCode,
			"corpName": c.corpName,
		}
	except Exception as e:
		raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/company/{code}/modules")
def api_company_modules(code: str):
	"""기업의 사용 가능한 데이터 모듈 목록."""
	try:
		from dartlab.engines.llmAnalyzer.context import scan_available_modules
		c = Company(code)
		modules = scan_available_modules(c)
		return {"stockCode": c.stockCode, "corpName": c.corpName, "modules": modules}
	except Exception as e:
		raise HTTPException(status_code=404, detail=str(e))


_OLLAMA_MODEL_GUIDE: list[dict[str, str]] = [
	{"name": "qwen3", "size": "8B", "vram": "~6GB", "quality": "높음", "speed": "보통", "note": "한국어 재무분석에 가장 추천"},
	{"name": "gemma2", "size": "9B", "vram": "~7GB", "quality": "높음", "speed": "보통", "note": "다국어 성능 우수"},
	{"name": "llama3.2", "size": "3B", "vram": "~3GB", "quality": "보통", "speed": "빠름", "note": "저사양 PC 추천"},
	{"name": "mistral", "size": "7B", "vram": "~5GB", "quality": "보통", "speed": "빠름", "note": "영문 질문에 강함"},
	{"name": "phi4", "size": "14B", "vram": "~10GB", "quality": "매우높음", "speed": "느림", "note": "GPU 12GB+ 추천"},
	{"name": "qwen3:14b", "size": "14B", "vram": "~10GB", "quality": "매우높음", "speed": "느림", "note": "최고 품질, 고사양 PC"},
]

_COMPANY_SUFFIXES = ("차", "전자", "그룹", "건설", "화학", "제약", "바이오", "증권", "보험", "은행", "금융", "지주", "산업", "통신", "에너지")


def _search_fuzzy(query: str) -> Company | None:
	"""단일 쿼리로 Company.search → Company 반환. 실패 시 접미사 제거 후 재시도."""
	if len(query) < 2:
		return None
	try:
		df = Company.search(query)
		if len(df) > 0:
			row = df.to_dicts()[0]
			code = row.get("종목코드", row.get("stockCode", ""))
			if code:
				return Company(code)
	except Exception:
		pass

	for suffix in _COMPANY_SUFFIXES:
		if query.endswith(suffix) and len(query) > len(suffix):
			stripped = query[:-len(suffix)]
			if len(stripped) < 2:
				continue
			try:
				df = Company.search(stripped)
				if len(df) > 0:
					row = df.to_dicts()[0]
					code = row.get("종목코드", row.get("stockCode", ""))
					if code:
						return Company(code)
			except Exception:
				continue
	return None


def _search_suggestions(question: str) -> list[dict[str, str]]:
	"""질문에서 단어를 추출하여 비슷한 종목 후보를 검색한다."""
	import re
	words = re.split(r'\s+', question)
	seen_codes: set[str] = set()
	suggestions: list[dict[str, str]] = []

	for word in words:
		if len(word) < 2:
			continue
		queries = [word]
		for suffix in _COMPANY_SUFFIXES:
			if word.endswith(suffix) and len(word) > len(suffix):
				queries.append(word[:-len(suffix)])
		for q in queries:
			try:
				df = Company.search(q)
				for row in df.head(3).to_dicts():
					code = row.get("종목코드", row.get("stockCode", ""))
					name = row.get("회사명", row.get("corpName", ""))
					if code and code not in seen_codes:
						seen_codes.add(code)
						suggestions.append({"corpName": name, "stockCode": code})
						if len(suggestions) >= 5:
							return suggestions
			except Exception:
				continue
	return suggestions


class _ResolveResult:
	"""종목 검색 결과를 담는 컨테이너."""
	__slots__ = ("company", "not_found", "suggestions")

	def __init__(self, company: Company | None = None, *, not_found: bool = False, suggestions: list[dict[str, str]] | None = None):
		self.company = company
		self.not_found = not_found
		self.suggestions = suggestions or []


def _build_not_found_msg(suggestions: list[dict[str, str]]) -> str:
	"""NOT_FOUND 안내 메시지. 후보가 있으면 목록 포함."""
	if not suggestions:
		return (
			"해당 종목을 찾을 수 없습니다. "
			"정확한 종목명(예: 삼성전자, 기아, LG에너지솔루션) 또는 "
			"6자리 종목코드(예: 005930)로 다시 질문해 주세요."
		)
	lines = ["해당 종목을 정확히 찾지 못했습니다. 혹시 아래 종목을 찾으시나요?\n"]
	for s in suggestions:
		lines.append(f"- **{s['corpName']}** ({s['stockCode']})")
	lines.append("\n종목명이나 종목코드를 정확히 입력하시면 바로 분석해 드리겠습니다.")
	return "\n".join(lines)


def _try_resolve_company(req: AskRequest) -> _ResolveResult:
	"""company 필드 또는 질문에서 종목을 찾는다."""
	if req.company:
		try:
			return _ResolveResult(company=Company(req.company))
		except Exception:
			suggestions = _search_suggestions(req.company)
			return _ResolveResult(not_found=True, suggestions=suggestions)

	import re
	q = req.question
	code_match = re.search(r'\b(\d{6})\b', q)
	if code_match:
		try:
			return _ResolveResult(company=Company(code_match.group(1)))
		except Exception:
			return _ResolveResult(not_found=True)

	words = re.split(r'\s+', q)
	for length in range(min(4, len(words)), 0, -1):
		for i in range(len(words) - length + 1):
			candidate = " ".join(words[i:i + length])
			result = _search_fuzzy(candidate)
			if result:
				return _ResolveResult(company=result)

	return _ResolveResult()


def _try_resolve_from_history(history: list[HistoryMessage]) -> Company | None:
	"""대화 히스토리에서 가장 최근 언급된 종목코드를 찾는다."""
	import re
	for msg in reversed(history):
		if not msg.text:
			continue
		code_match = re.search(r'\b(\d{6})\b', msg.text)
		if code_match:
			try:
				return Company(code_match.group(1))
			except Exception:
				continue
	return None


@app.post("/api/ask")
async def api_ask(req: AskRequest):
	"""LLM 질문 — 종목이 있으면 데이터 기반 분석, 없으면 순수 대화."""
	dartlab.verbose = False

	if req.provider or req.model:
		from dartlab.engines.llmAnalyzer import configure, get_config
		current = get_config()
		overrides: dict[str, Any] = {
			"provider": req.provider or current.provider,
		}
		if req.model:
			overrides["model"] = req.model
		if current.api_key:
			overrides["api_key"] = current.api_key
		if current.base_url:
			overrides["base_url"] = current.base_url
		configure(**overrides)

	resolved = _try_resolve_company(req)
	c: Company | None = resolved.company
	if not c and not resolved.not_found and req.history:
		c = _try_resolve_from_history(req.history)

	if req.stream:
		return EventSourceResponse(
			_stream_ask(c, req, not_found_msg=_build_not_found_msg(resolved.suggestions) if resolved.not_found else None),
			media_type="text/event-stream",
		)

	if resolved.not_found:
		return {"answer": _build_not_found_msg(resolved.suggestions)}

	if c is None:
		return await _plain_chat(req)

	try:
		answer = await asyncio.to_thread(
			c.ask,
			req.question,
			include=req.include,
			exclude=req.exclude,
		)
		return {
			"company": c.corpName,
			"stockCode": c.stockCode,
			"answer": answer,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


_CHAT_SYSTEM_PROMPT = (
	"당신은 DartLab의 금융 분석 AI 어시스턴트입니다. "
	"한국 주식시장과 DART 전자공시 데이터에 대해 전문적으로 답변합니다.\n\n"
	"## DartLab 데이터 안내\n"
	"DartLab은 한국 DART 전자공시 시스템의 공시 데이터를 분석합니다.\n"
	"현재 보유 데이터:\n"
	"- **공시 문서(docs)**: 267개 주요 상장기업의 정기보고서 파싱 데이터\n"
	"  - 재무제표 36개 항목 (매출, 영업이익, 자산, 부채 등)\n"
	"  - 공시 서술 섹션 4개 항목 (사업개요, 위험요소, 주요계약, 연구개발)\n"
	"  - K-IFRS 주석 12개 항목 (재고자산, 매출채권, 유형자산 등)\n"
	"- **재무제표(finance)**: 2,743개 상장기업의 XBRL 재무제표 (2015~최근)\n"
	"  - 손익계산서, 재무상태표, 현금흐름표\n"
	"  - 분기별 standalone 시계열\n"
	"  - 재무비율 자동 계산 (ROE, ROA, 부채비율, 영업이익률 등)\n\n"
	"사용자가 '어떤 데이터가 있나', '뭘 분석할 수 있나' 같은 메타 질문을 하면 위 내용을 바탕으로 안내하세요.\n\n"
	"## 역할\n"
	"- 특정 종목이 언급되면 해당 기업의 DART 공시 데이터를 기반으로 분석합니다.\n"
	"- 종목이 언급되지 않으면 일반적인 금융/투자 지식으로 답변합니다.\n"
	"- 특정 종목을 분석하려면 종목명이나 종목코드(예: 삼성전자, 005930)를 알려달라고 안내하세요.\n\n"
	"## 답변 규칙\n"
	"- 수치가 2개 이상 등장하면 반드시 마크다운 테이블(|표)로 정리하세요. 텍스트 나열보다 테이블이 항상 우선입니다.\n"
	"- 시계열 데이터(연도별 매출, 이익률 추이 등)는 해석 컬럼(판단, 전년비 등)을 추가한 분석 테이블로 정리하세요.\n"
	"- 핵심 수치는 **굵게** 표시하세요.\n"
	"- 질문과 같은 언어로 답변하세요. 한국어 질문이면 한국어로.\n"
	"- 답변은 간결하되, 근거가 있는 분석을 제공하세요.\n"
	"- 숫자만 나열하지 말고 해석에 집중하세요. '왜?'와 '그래서?'를 설명하세요."
)

# 멀티턴 히스토리에서 최근 N턴만 포함 (토큰 절약)
_MAX_HISTORY_TURNS = 10


def _build_history_messages(history: list[HistoryMessage] | None) -> list[dict[str, str]]:
	"""클라이언트의 대화 기록을 LLM messages 포맷으로 변환. 최근 N턴만 유지."""
	if not history:
		return []
	# 최근 N*2 메시지만 (user+assistant 1쌍 = 2메시지)
	trimmed = history[-(_MAX_HISTORY_TURNS * 2):]
	msgs = []
	for h in trimmed:
		role = h.role if h.role in ("user", "assistant") else "user"
		text = h.text.strip()
		if text:
			msgs.append({"role": role, "content": text})
	return msgs


async def _plain_chat(req: AskRequest):
	"""종목 없는 순수 LLM 대화."""
	from dartlab.engines.llmAnalyzer import get_config
	from dartlab.engines.llmAnalyzer.providers import create_provider

	config_ = get_config()
	overrides: dict[str, Any] = {}
	if req.provider:
		overrides["provider"] = req.provider
	if req.model:
		overrides["model"] = req.model
	if overrides:
		config_ = config_.merge(overrides)

	messages = [{"role": "system", "content": _CHAT_SYSTEM_PROMPT}]
	messages.extend(_build_history_messages(req.history))
	messages.append({"role": "user", "content": req.question})

	llm = create_provider(config_)
	try:
		answer = await asyncio.to_thread(llm.complete, messages)
		return {"answer": answer}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


def _build_snapshot(company: Company) -> dict | None:
	"""ratios + 핵심 시계열에서 즉시 표시할 스냅샷 데이터 추출."""
	ratios = getattr(company, "ratios", None)
	if ratios is None:
		return None

	def _fmt(val, suffix=""):
		if val is None:
			return None
		abs_v = abs(val)
		sign = "-" if val < 0 else ""
		if abs_v >= 1e12:
			return f"{sign}{abs_v / 1e12:,.1f}조{suffix}"
		if abs_v >= 1e8:
			return f"{sign}{abs_v / 1e8:,.0f}억{suffix}"
		if abs_v >= 1e4:
			return f"{sign}{abs_v / 1e4:,.0f}만{suffix}"
		if abs_v >= 1:
			return f"{sign}{abs_v:,.0f}{suffix}"
		return f"0{suffix}"

	def _pct(val):
		return f"{val:.1f}%" if val is not None else None

	def _judge_pct(val, good, caution):
		if val is None:
			return None
		if val >= good:
			return "good"
		if val >= caution:
			return "caution"
		return "danger"

	def _judge_pct_inv(val, good, caution):
		if val is None:
			return None
		if val <= good:
			return "good"
		if val <= caution:
			return "caution"
		return "danger"

	items = []

	if ratios.revenueTTM is not None:
		items.append({"label": "매출(TTM)", "value": _fmt(ratios.revenueTTM), "status": None})
	if ratios.operatingIncomeTTM is not None:
		items.append({"label": "영업이익(TTM)", "value": _fmt(ratios.operatingIncomeTTM), "status": "good" if ratios.operatingIncomeTTM > 0 else "danger"})
	if ratios.netIncomeTTM is not None:
		items.append({"label": "순이익(TTM)", "value": _fmt(ratios.netIncomeTTM), "status": "good" if ratios.netIncomeTTM > 0 else "danger"})
	if ratios.operatingMargin is not None:
		items.append({"label": "영업이익률", "value": _pct(ratios.operatingMargin), "status": _judge_pct(ratios.operatingMargin, 10, 5)})
	if ratios.roe is not None:
		items.append({"label": "ROE", "value": _pct(ratios.roe), "status": _judge_pct(ratios.roe, 10, 5)})
	if ratios.roa is not None:
		items.append({"label": "ROA", "value": _pct(ratios.roa), "status": _judge_pct(ratios.roa, 5, 2)})
	if ratios.debtRatio is not None:
		items.append({"label": "부채비율", "value": _pct(ratios.debtRatio), "status": _judge_pct_inv(ratios.debtRatio, 100, 200)})
	if ratios.currentRatio is not None:
		items.append({"label": "유동비율", "value": _pct(ratios.currentRatio), "status": _judge_pct(ratios.currentRatio, 150, 100)})
	if ratios.fcf is not None:
		items.append({"label": "FCF", "value": _fmt(ratios.fcf), "status": "good" if ratios.fcf > 0 else "danger"})
	if ratios.revenueGrowth3Y is not None:
		items.append({"label": "매출 3Y CAGR", "value": _pct(ratios.revenueGrowth3Y), "status": _judge_pct(ratios.revenueGrowth3Y, 5, 0)})

	annual = getattr(company, "annual", None)
	trend = None
	if annual is not None:
		series, years = annual
		if years and len(years) >= 2:
			rev_list = series.get("IS", {}).get("revenue")
			if rev_list:
				n = min(5, len(rev_list))
				recent_years = years[-n:]
				recent_vals = rev_list[-n:]
				trend = {"years": recent_years, "values": [v for v in recent_vals]}

	if not items:
		return None

	snapshot: dict[str, Any] = {"items": items}
	if trend:
		snapshot["trend"] = trend
	if ratios.warnings:
		snapshot["warnings"] = ratios.warnings[:3]

	return snapshot


async def _stream_ask(c: Company | None, req: AskRequest, *, not_found_msg: str | None = None):
	"""SSE 스트리밍 generator.

	이벤트 흐름:
	  meta → snapshot → context (모듈별, 여러 번) → chunk... → done
	  tool_call/tool_result 이벤트는 agent_loop 사용 시 추가
	"""
	from dartlab.engines.llmAnalyzer import get_config
	from dartlab.engines.llmAnalyzer.providers import create_provider

	if not_found_msg:
		yield {
			"event": "meta",
			"data": json.dumps({"company": None, "stockCode": None}, ensure_ascii=False),
		}
		yield {
			"event": "chunk",
			"data": json.dumps({"text": not_found_msg}, ensure_ascii=False),
		}
		yield {"event": "done", "data": "{}"}
		return

	yield {
		"event": "meta",
		"data": json.dumps({
			"company": c.corpName if c else None,
			"stockCode": c.stockCode if c else None,
		}, ensure_ascii=False),
	}

	try:
		config_ = get_config()
		overrides: dict[str, Any] = {}
		if req.provider:
			overrides["provider"] = req.provider
		if req.model:
			overrides["model"] = req.model
		if overrides:
			config_ = config_.merge(overrides)

		use_compact = config_.provider in ("ollama", "codex", "claude-code")
		history_msgs = _build_history_messages(req.history)

		if c:
			from dartlab.engines.llmAnalyzer.context import (
				build_context_by_module,
				detect_year_range, _get_sector,
			)
			from dartlab.engines.llmAnalyzer.prompts import build_system_prompt, _classify_question_multi
			from dartlab.engines.llmAnalyzer.metadata import MODULE_META

			snapshot = await asyncio.to_thread(_build_snapshot, c)
			if snapshot:
				yield {
					"event": "snapshot",
					"data": json.dumps(snapshot, ensure_ascii=False),
				}

			modules_dict, included_tables, header_text = await asyncio.to_thread(
				build_context_by_module, c, req.question,
				req.include, req.exclude, use_compact,
			)

			if "_full" in modules_dict:
				context_text = modules_dict["_full"]
				yield {
					"event": "context",
					"data": json.dumps({
						"module": "_full",
						"label": "전체 데이터",
						"text": context_text,
					}, ensure_ascii=False),
				}
			else:
				for mod_name in included_tables:
					mod_text = modules_dict.get(mod_name, "")
					if not mod_text:
						continue
					meta_info = MODULE_META.get(mod_name)
					label = meta_info.label if meta_info else mod_name
					yield {
						"event": "context",
						"data": json.dumps({
							"module": mod_name,
							"label": label,
							"text": mod_text,
						}, ensure_ascii=False),
					}
				parts = [header_text] if header_text else []
				for name in included_tables:
					if name in modules_dict:
						parts.append(modules_dict[name])
				context_text = "\n".join(parts)

			if not use_compact:
				from dartlab.engines.llmAnalyzer.pipeline import run_pipeline
				pipeline_result = await asyncio.to_thread(
					run_pipeline, c, req.question, included_tables,
				)
				if pipeline_result:
					context_text = context_text + pipeline_result

			meta_payload: dict[str, Any] = {"includedModules": included_tables}
			if not use_compact:
				year_range = await asyncio.to_thread(detect_year_range, c, included_tables)
				if year_range:
					meta_payload["dataYearRange"] = year_range
			yield {
				"event": "meta",
				"data": json.dumps(meta_payload, ensure_ascii=False),
			}

			sector = _get_sector(c)
			question_types = _classify_question_multi(req.question)
			system = build_system_prompt(
				config_.system_prompt,
				included_modules=included_tables,
				sector=sector,
				question_types=question_types,
				compact=use_compact,
			)
			messages = [{"role": "system", "content": system}]
			messages.extend(history_msgs)
			messages.append({"role": "user", "content": f"{context_text}\n\n---\n\n질문: {req.question}"})
		else:
			messages = [{"role": "system", "content": _CHAT_SYSTEM_PROMPT}]
			messages.extend(history_msgs)
			messages.append({"role": "user", "content": req.question})

		llm = create_provider(config_)

		use_guided = (
			use_compact
			and c is not None
			and hasattr(llm, "complete_json")
		)
		use_tools = c is not None and not use_guided and hasattr(llm, "complete_with_tools")

		full_response_parts: list[str] = []
		done_payload: dict[str, Any] = {}

		if use_guided:
			from dartlab.engines.llmAnalyzer.prompts import GUIDED_SCHEMA, guided_json_to_markdown

			resp = await asyncio.to_thread(llm.complete_json, messages, GUIDED_SCHEMA)
			raw_json = resp.answer
			try:
				parsed = json.loads(raw_json)
				md_text = guided_json_to_markdown(parsed)
				done_payload["guidedRaw"] = parsed
				if parsed.get("grade"):
					done_payload["responseMeta"] = {
						"grade": parsed["grade"],
						"has_conclusion": bool(parsed.get("conclusion")),
						"signals": {
							"positive": [p[:20] for p in parsed.get("positives", [])[:3]],
							"negative": [r.get("description", "")[:20] for r in parsed.get("risks", [])[:3] if isinstance(r, dict)],
						},
						"tables_count": 1,
					}
			except (json.JSONDecodeError, ValueError):
				md_text = raw_json

			full_response_parts.append(md_text)
			yield {
				"event": "chunk",
				"data": json.dumps({"text": md_text}, ensure_ascii=False),
			}

		elif use_tools:
			from dartlab.engines.llmAnalyzer.agent import agent_loop, AGENT_SYSTEM_ADDITION

			messages[0]["content"] += AGENT_SYSTEM_ADDITION

			queue: asyncio.Queue = asyncio.Queue()
			loop = asyncio.get_event_loop()

			def _on_tool_call(name: str, args: dict):
				loop.call_soon_threadsafe(
					queue.put_nowait,
					{"event": "tool_call", "name": name, "arguments": args},
				)

			def _on_tool_result(name: str, result: str):
				loop.call_soon_threadsafe(
					queue.put_nowait,
					{"event": "tool_result", "name": name, "result": result[:2000]},
				)

			async def _run_agent():
				ans = await asyncio.to_thread(
					agent_loop,
					llm, messages, c,
					max_turns=5,
					on_tool_call=_on_tool_call,
					on_tool_result=_on_tool_result,
				)
				await queue.put({"event": "_done", "answer": ans})

			task = asyncio.create_task(_run_agent())

			while True:
				ev = await queue.get()
				if ev["event"] == "_done":
					if ev.get("answer"):
						full_response_parts.append(ev["answer"])
						yield {
							"event": "chunk",
							"data": json.dumps({"text": ev["answer"]}, ensure_ascii=False),
						}
					break
				yield {
					"event": ev["event"],
					"data": json.dumps(ev, ensure_ascii=False),
				}

			await task
		else:
			def _gen():
				yield from llm.stream(messages)

			gen = _gen()
			while True:
				chunk = await asyncio.to_thread(next, gen, None)
				if chunk is None:
					break
				full_response_parts.append(chunk)
				yield {
					"event": "chunk",
					"data": json.dumps({"text": chunk}, ensure_ascii=False),
				}

		if c and full_response_parts:
			from dartlab.engines.llmAnalyzer.prompts import extract_response_meta
			full_text = "".join(full_response_parts)
			response_meta = extract_response_meta(full_text)
			if response_meta.get("grade") or response_meta.get("has_conclusion"):
				done_payload["responseMeta"] = response_meta

	except Exception as e:
		yield {
			"event": "error",
			"data": json.dumps({"error": str(e)}, ensure_ascii=False),
		}

	yield {"event": "done", "data": json.dumps(done_payload, ensure_ascii=False)}


# ── Static Files (Svelte build) ──

_UI_DIR = Path(__file__).parent / "ui" / "build"

if _UI_DIR.exists():
	app.mount("/assets", StaticFiles(directory=str(_UI_DIR / "assets")), name="assets")


@app.get("/{path:path}")
def serve_spa(path: str = ""):
	"""SPA fallback — index.html 반환."""
	if not _UI_DIR.exists():
		return HTMLResponse(
			"<h2>DartLab UI not built</h2>"
			"<p>Run: <code>cd src/dartlab/ui && npm install && npm run build</code></p>",
			status_code=503,
		)

	file = _UI_DIR / path
	if path and file.is_file():
		return FileResponse(file)

	index = _UI_DIR / "index.html"
	if index.exists():
		return FileResponse(index, media_type="text/html")

	return HTMLResponse("<h2>index.html not found</h2>", status_code=404)


def run_server(host: str = "0.0.0.0", port: int = 8400):
	"""서버 실행."""
	import socket
	import sys

	import uvicorn

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sock.bind(("127.0.0.1", port))
		sock.close()
	except OSError:
		print(f"\n  오류: 포트 {port}이 이미 사용 중입니다.", file=sys.stderr)
		print(f"  다른 포트를 사용하세요: dartlab ai --port {port + 1}\n", file=sys.stderr)
		return

	uvicorn.run(app, host=host, port=port, log_level="info")
