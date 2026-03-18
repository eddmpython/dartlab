"""Ollama 로컬 LLM provider."""

from __future__ import annotations

from typing import Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

OLLAMA_DEFAULT_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """Ollama 로컬 provider.

    OpenAI 호환 엔드포인트 사용 (localhost:11434/v1).
    Ollama 미설치/미실행 시 OS별 설치 안내 제공.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._base_url = config.base_url or f"{OLLAMA_DEFAULT_URL}/v1"

    @property
    def default_model(self) -> str:
        # 설치된 모델 중 첫 번째 사용, 없으면 llama3.1 fallback
        models = self.get_installed_models()
        if models:
            return models[0]
        return "llama3.1"

    def check_available(self) -> bool:
        import requests

        try:
            resp = requests.get(f"{OLLAMA_DEFAULT_URL}/api/tags", timeout=2)
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def get_installed_models(self) -> list[str]:
        """설치된 모델 목록."""
        import requests

        try:
            resp = requests.get(f"{OLLAMA_DEFAULT_URL}/api/tags", timeout=2)
            data = resp.json()
            names = []
            for m in data.get("models", []):
                name = m["name"]
                # ":latest" 태그 제거 (표시 간결화)
                if name.endswith(":latest"):
                    name = name[:-7]
                names.append(name)
            return names
        except (requests.RequestException, AttributeError, KeyError, OSError, TypeError, ValueError):
            return []

    def preload(self) -> bool:
        """모델을 메모리에 미리 로딩 (keep_alive=-1).

        서버 시작 시 호출하면 첫 질문의 cold start 지연을 제거한다.
        Ollama native API 사용 (OpenAI 호환 API는 keep_alive 미지원).
        """
        import requests

        try:
            resp = requests.post(
                f"{OLLAMA_DEFAULT_URL}/api/generate",
                json={"model": self.resolved_model, "prompt": "", "keep_alive": -1, "stream": False},
                timeout=60,
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def _ensure_available(self):
        if not self.check_available():
            from dartlab.engines.ai.ollama_setup import get_install_guide

            raise ConnectionError(f"Ollama 서버에 접근할 수 없습니다 ({OLLAMA_DEFAULT_URL}).\n\n{get_install_guide()}")

    def _get_client(self):
        if self._client is None:
            self._ensure_available()
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다.\n  uv add dartlab[llm]")
            self._client = OpenAI(base_url=self._base_url, api_key="ollama")
        return self._client

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.resolved_model,
            messages=messages,
            temperature=self.config.temperature,
        )
        return LLMResponse(
            answer=response.choices[0].message.content or "",
            provider="ollama",
            model=self.resolved_model,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        client = self._get_client()
        stream = client.chat.completions.create(
            model=self.resolved_model,
            messages=messages,
            temperature=self.config.temperature,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def complete_json(
        self,
        messages: list[dict[str, str]],
        schema: dict | None = None,
    ) -> LLMResponse:
        """JSON 구조 강제 completion (Guided Generation).

        Args:
                schema: JSON Schema dict. None이면 단순 json_object 모드.
        """
        client = self._get_client()
        if schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "analysis", "schema": schema},
            }
        else:
            response_format = {"type": "json_object"}

        response = client.chat.completions.create(
            model=self.resolved_model,
            messages=messages,
            temperature=self.config.temperature,
            response_format=response_format,
        )
        return LLMResponse(
            answer=response.choices[0].message.content or "",
            provider="ollama",
            model=self.resolved_model,
        )

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolResponse:
        """Ollama tool calling 지원 (v0.3.0+)."""
        import json

        client = self._get_client()
        kwargs: dict = {
            "model": self.resolved_model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return ToolResponse(
            answer=choice.message.content or "",
            provider="ollama",
            model=self.resolved_model,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
        )
