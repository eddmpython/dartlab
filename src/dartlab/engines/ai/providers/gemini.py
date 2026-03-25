"""Google Gemini provider.

인증: API key (AI Studio에서 무료 발급)
- https://aistudio.google.com/apikey 에서 발급
- GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수, 또는 설정 패널에서 입력
"""

from __future__ import annotations

import logging
from typing import Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

_log = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """Google Gemini API provider.

    google-genai SDK 기반. API key 인증.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google import genai
        except ImportError:
            raise ImportError("google-genai 패키지가 필요합니다.\n  pip install dartlab[llm]")

        import os

        apiKey = self.config.api_key
        if not apiKey:
            apiKey = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if not apiKey:
            raise ValueError(
                "Gemini API key가 필요합니다.\n"
                "  발급: https://aistudio.google.com/apikey (무료)\n"
                "  설정: GEMINI_API_KEY 환경변수 또는 설정 패널에서 입력"
            )

        self._client = genai.Client(api_key=apiKey)
        return self._client

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    @property
    def supports_native_tools(self) -> bool:
        return True

    def check_available(self) -> bool:
        try:
            self._get_client()
            return True
        except (ImportError, ValueError, OSError):
            return False

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        client = self._get_client()

        systemInstruction, contents = _splitSystemAndContents(messages)

        kwargs: dict = {
            "model": self.resolved_model,
            "contents": contents,
        }

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
        )
        if systemInstruction:
            config.system_instruction = systemInstruction
        kwargs["config"] = config

        response = client.models.generate_content(**kwargs)

        usage = None
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                "total_tokens": response.usage_metadata.total_token_count or 0,
            }

        return LLMResponse(
            answer=response.text or "",
            provider="gemini",
            model=self.resolved_model,
            usage=usage,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        client = self._get_client()

        systemInstruction, contents = _splitSystemAndContents(messages)

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
        )
        if systemInstruction:
            config.system_instruction = systemInstruction

        for chunk in client.models.generate_content_stream(
            model=self.resolved_model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolResponse:
        client = self._get_client()
        from google.genai import types

        systemInstruction, contents = _splitSystemAndContents(messages)

        geminiTools = _convertToolsToGemini(tools)

        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            tools=geminiTools,
        )
        if systemInstruction:
            config.system_instruction = systemInstruction

        response = client.models.generate_content(
            model=self.resolved_model,
            contents=contents,
            config=config,
        )

        usage = None
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                "total_tokens": response.usage_metadata.total_token_count or 0,
            }

        toolCalls: list[ToolCall] = []
        answer = ""
        finishReason = "stop"

        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if part.text:
                    answer += part.text
                if part.function_call:
                    fc = part.function_call
                    args = dict(fc.args) if fc.args else {}
                    toolCalls.append(
                        ToolCall(
                            id=f"call_{fc.name}_{len(toolCalls)}",
                            name=fc.name,
                            arguments=args,
                        )
                    )
            if toolCalls:
                finishReason = "tool_calls"

        return ToolResponse(
            answer=answer,
            provider="gemini",
            model=self.resolved_model,
            usage=usage,
            tool_calls=toolCalls,
            finish_reason=finishReason,
        )

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """Gemini tool result → OpenAI 형식으로 변환."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        }


def _splitSystemAndContents(messages: list[dict]) -> tuple[str | None, list]:
    """OpenAI 메시지 형식 → Gemini system/contents 분리."""
    system = None
    contents = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            system = content
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content or ""}]})
        elif role == "tool":
            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": f"[Tool Result] {content}"}],
                }
            )
        else:
            contents.append({"role": "user", "parts": [{"text": content or ""}]})

    return system, contents


def _convertToolsToGemini(tools: list[dict]) -> list:
    """OpenAI tool schema → Gemini tool 형식 변환."""
    from google.genai import types

    declarations = []
    for tool in tools:
        if tool.get("type") != "function":
            continue
        func = tool["function"]
        params = func.get("parameters", {})

        cleanedParams = _cleanSchemaForGemini(params)

        declarations.append(
            types.FunctionDeclaration(
                name=func["name"],
                description=func.get("description", ""),
                parameters=cleanedParams if cleanedParams.get("properties") else None,
            )
        )

    if not declarations:
        return []
    return [types.Tool(function_declarations=declarations)]


def _cleanSchemaForGemini(schema: dict) -> dict:
    """JSON Schema에서 Gemini 미지원 속성 제거."""
    cleaned = {}
    for key, value in schema.items():
        if key in ("additionalProperties", "$schema"):
            continue
        if isinstance(value, dict):
            cleaned[key] = _cleanSchemaForGemini(value)
        elif isinstance(value, list):
            cleaned[key] = [_cleanSchemaForGemini(item) if isinstance(item, dict) else item for item in value]
        else:
            cleaned[key] = value
    return cleaned
