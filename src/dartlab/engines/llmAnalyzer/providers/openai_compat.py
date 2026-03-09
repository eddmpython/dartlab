"""OpenAI / GPT / OpenAI-compatible provider."""

from __future__ import annotations

import json
from typing import Generator

from dartlab.engines.llmAnalyzer.providers.base import BaseProvider
from dartlab.engines.llmAnalyzer.types import LLMConfig, LLMResponse, ToolCall, ToolResponse


class OpenAICompatProvider(BaseProvider):
	"""OpenAI SDK 기반 provider.

	GPT 직접 호출, CLIProxyAPI, 기타 OpenAI-compatible API 모두 지원.
	base_url 설정으로 프록시/커스텀 엔드포인트 전환.
	"""

	def __init__(self, config: LLMConfig):
		super().__init__(config)
		self._client = None

	def _get_client(self):
		if self._client is None:
			try:
				from openai import OpenAI
			except ImportError:
				raise ImportError(
					"openai 패키지가 필요합니다.\n"
					"  uv add dartlab[llm]"
				)
			kwargs = {}
			if self.config.api_key:
				kwargs["api_key"] = self.config.api_key
			if self.config.base_url:
				kwargs["base_url"] = self.config.base_url
			self._client = OpenAI(**kwargs)
		return self._client

	@property
	def default_model(self) -> str:
		return "gpt-4o"

	def check_available(self) -> bool:
		try:
			self._get_client()
			return True
		except Exception:
			return False

	def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
		client = self._get_client()
		response = client.chat.completions.create(
			model=self.resolved_model,
			messages=messages,
			temperature=self.config.temperature,
			max_tokens=self.config.max_tokens,
		)
		choice = response.choices[0]
		usage = None
		if response.usage:
			usage = {
				"prompt_tokens": response.usage.prompt_tokens,
				"completion_tokens": response.usage.completion_tokens,
				"total_tokens": response.usage.total_tokens,
			}
		return LLMResponse(
			answer=choice.message.content or "",
			provider="openai",
			model=response.model,
			usage=usage,
		)

	def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
		client = self._get_client()
		stream = client.chat.completions.create(
			model=self.resolved_model,
			messages=messages,
			temperature=self.config.temperature,
			max_tokens=self.config.max_tokens,
			stream=True,
		)
		for chunk in stream:
			if chunk.choices and chunk.choices[0].delta.content:
				yield chunk.choices[0].delta.content

	def complete_with_tools(
		self,
		messages: list[dict],
		tools: list[dict],
	) -> ToolResponse:
		"""OpenAI tool calling 지원."""
		client = self._get_client()
		kwargs: dict = {
			"model": self.resolved_model,
			"messages": messages,
			"temperature": self.config.temperature,
			"max_tokens": self.config.max_tokens,
		}
		if tools:
			kwargs["tools"] = tools

		response = client.chat.completions.create(**kwargs)
		choice = response.choices[0]

		usage = None
		if response.usage:
			usage = {
				"prompt_tokens": response.usage.prompt_tokens,
				"completion_tokens": response.usage.completion_tokens,
				"total_tokens": response.usage.total_tokens,
			}

		tool_calls = []
		if choice.message.tool_calls:
			for tc in choice.message.tool_calls:
				tool_calls.append(ToolCall(
					id=tc.id,
					name=tc.function.name,
					arguments=json.loads(tc.function.arguments),
				))

		return ToolResponse(
			answer=choice.message.content or "",
			provider="openai",
			model=response.model,
			tool_calls=tool_calls,
			finish_reason=choice.finish_reason or "stop",
			usage=usage,
		)
