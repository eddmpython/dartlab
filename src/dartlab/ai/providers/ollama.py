"""Ollama 로컬 LLM provider."""

from __future__ import annotations

from typing import Generator

from dartlab.ai.providers.base import BaseProvider
from dartlab.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

OLLAMA_DEFAULT_URL = "http://localhost:11434"


def _buildInferenceOptions() -> dict:
    """GPU VRAM 기반 Ollama 추론 옵션 자동 결정."""
    from dartlab.ai.providers.support.ollamaSetup import _detectGpu

    gpu = _detectGpu()
    options: dict = {"num_gpu": 999 if gpu["available"] else 0}

    vram = gpu.get("vram_mb") or 0
    if vram >= 12000:
        options["num_ctx"] = 8192
        options["num_batch"] = 1024
    elif vram >= 6000:
        options["num_ctx"] = 4096
        options["num_batch"] = 512
    else:
        options["num_ctx"] = 2048
        options["num_batch"] = 256

    options["flash_attn"] = True
    return options


_VRAM_MODEL_TIERS: list[tuple[int, str, str]] = [
    (24000, "qwen3:32b-q4_K_M", "32B 4bit — 최고 품질"),
    (12000, "qwen3:14b-q4_K_M", "14B 4bit — 고품질"),
    (8000, "qwen3:8b-q4_K_M", "8B 4bit — 균형"),
    (6000, "qwen3:4b-q4_K_M", "4B 4bit — 경량"),
    (4000, "qwen3:1.7b-q4_K_M", "1.7B 4bit — 최경량"),
    (0, "qwen3:0.6b", "0.6B — CPU 전용"),
]


def recommendModel(vramMb: int | None = None) -> dict:
    """GPU VRAM 기반 모델 추천 — _VRAM_MODEL_TIERS 매핑."""
    if vramMb is None:
        from dartlab.ai.providers.support.ollamaSetup import _detectGpu

        gpu = _detectGpu()
        vramMb = gpu.get("vram_mb") or 0

    for minVram, model, desc in _VRAM_MODEL_TIERS:
        if vramMb >= minVram:
            return {"model": model, "description": desc, "vram_mb": vramMb}
    return {"model": _VRAM_MODEL_TIERS[-1][1], "description": _VRAM_MODEL_TIERS[-1][2], "vram_mb": vramMb}


class OllamaProvider(BaseProvider):
    """Ollama 로컬 provider."""

    @property
    def supportsNativeTools(self) -> bool:
        """Ollama 0.4+ native tool calling 지원."""
        return True

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._base_url = config.baseUrl or f"{OLLAMA_DEFAULT_URL}/v1"

    @property
    def defaultModel(self) -> str:
        """설치된 첫 모델 또는 llama3.1 폴백."""
        models = self.getInstalledModels()
        if models:
            return models[0]
        return "llama3.1"

    def checkAvailable(self) -> bool:
        """Ollama 서버 /api/tags 응답 2 초 내 200 여부."""
        import httpx

        try:
            resp = httpx.get(f"{OLLAMA_DEFAULT_URL}/api/tags", timeout=2)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def getInstalledModels(self) -> list[str]:
        """Ollama 서버 설치 모델 목록 (:latest 접미사 제거)."""
        import httpx

        try:
            resp = httpx.get(f"{OLLAMA_DEFAULT_URL}/api/tags", timeout=2)
            data = resp.json()
            names = []
            for m in data.get("models", []):
                name = m["name"]
                if name.endswith(":latest"):
                    name = name[:-7]
                names.append(name)
            return names
        except (httpx.HTTPError, AttributeError, KeyError, OSError, TypeError, ValueError):
            return []

    def preload(self, *, keepAliveMinutes: int = 30) -> bool:
        """모델 VRAM 로드 후 keepAliveMinutes 분 동안 유지."""
        import httpx

        options = _buildInferenceOptions()
        keepAlive = f"{keepAliveMinutes}m" if keepAliveMinutes > 0 else -1
        try:
            resp = httpx.post(
                f"{OLLAMA_DEFAULT_URL}/api/generate",
                json={
                    "model": self.resolvedModel,
                    "prompt": "",
                    "keep_alive": keepAlive,
                    "stream": False,
                    "options": options,
                },
                timeout=120,
            )
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def unload(self) -> bool:
        """keep_alive=0 으로 모델 VRAM 즉시 해제."""
        import httpx

        try:
            resp = httpx.post(
                f"{OLLAMA_DEFAULT_URL}/api/generate",
                json={"model": self.resolvedModel, "prompt": "", "keep_alive": 0, "stream": False},
                timeout=10,
            )
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    def serverVersion(self) -> str | None:
        """Ollama 서버 /api/version 조회 (실패 시 None)."""
        import httpx

        try:
            resp = httpx.get(f"{OLLAMA_DEFAULT_URL}/api/version", timeout=2)
            if resp.status_code == 200:
                return resp.json().get("version")
        except (httpx.HTTPError, ValueError, KeyError, OSError):
            pass
        return None

    def _ensureAvailable(self):
        if not self.checkAvailable():
            from dartlab.ai.providers.support.ollamaSetup import getInstallGuide

            raise ConnectionError(f"Ollama 서버에 접근할 수 없습니다 ({OLLAMA_DEFAULT_URL}).\n\n{getInstallGuide()}")

    def _getClient(self):
        if self._client is None:
            self._ensureAvailable()
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다.\n  pip install --upgrade dartlab")
            self._client = OpenAI(base_url=self._base_url, api_key="ollama")
        return self._client

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Ollama 동기 chat.completions 호출 (OpenAI 호환 API)."""
        client = self._getClient()
        response = client.chat.completions.create(
            model=self.resolvedModel,
            messages=messages,
            temperature=self.config.temperature,
        )
        return LLMResponse(
            answer=response.choices[0].message.content or "",
            provider="ollama",
            model=self.resolvedModel,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """Ollama 스트리밍 chat.completions — delta.content 만 yield."""
        client = self._getClient()
        stream = client.chat.completions.create(
            model=self.resolvedModel,
            messages=messages,
            temperature=self.config.temperature,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def completeJson(
        self,
        messages: list[dict[str, str]],
        schema: dict | None = None,
    ) -> LLMResponse:
        """JSON schema 강제 응답 모드 (response_format=json_schema 또는 json_object)."""
        client = self._getClient()
        if schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "analysis", "schema": schema},
            }
        else:
            response_format = {"type": "json_object"}

        response = client.chat.completions.create(
            model=self.resolvedModel,
            messages=messages,
            temperature=self.config.temperature,
            response_format=response_format,
        )
        return LLMResponse(
            answer=response.choices[0].message.content or "",
            provider="ollama",
            model=self.resolvedModel,
        )

    def completeWithTools(
        self,
        messages: list[dict],
        tools: list[dict],
        *,
        toolChoice: str | None = None,
    ) -> ToolResponse:
        """Ollama tool calling — chat.completions tools 파라미터 사용."""
        import json

        client = self._getClient()
        kwargs: dict = {
            "model": self.resolvedModel,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        toolCalls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                toolCalls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return ToolResponse(
            answer=choice.message.content or "",
            provider="ollama",
            model=self.resolvedModel,
            toolCalls=toolCalls,
            finish_reason=choice.finish_reason or "stop",
        )
