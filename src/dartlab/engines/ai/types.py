"""LLM 분석기 타입 정의."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Literal

ProviderName = Literal["claude", "openai", "ollama", "custom", "claude-code", "codex", "chatgpt"]


@dataclass
class LLMConfig:
	"""LLM 연결 설정."""

	provider: ProviderName = "openai"
	model: str | None = None
	api_key: str | None = None
	base_url: str | None = None
	temperature: float = 0.3
	max_tokens: int = 4096
	system_prompt: str | None = None

	def __post_init__(self):
		import os
		if self.base_url is None:
			env_url = os.environ.get("DARTLAB_LLM_BASE_URL")
			if env_url:
				self.base_url = env_url

	def merge(self, overrides: dict[str, Any]) -> LLMConfig:
		"""per-call override 적용한 새 Config 반환."""
		vals = dataclasses.asdict(self)
		vals.update({k: v for k, v in overrides.items() if v is not None})
		return LLMConfig(**vals)


@dataclass
class LLMResponse:
	"""LLM 응답 결과."""

	answer: str
	provider: str
	model: str
	context_tables: list[str] = field(default_factory=list)
	usage: dict[str, int] | None = None


@dataclass
class ToolCall:
	"""LLM이 요청한 도구 호출."""

	id: str
	name: str
	arguments: dict[str, Any]


@dataclass
class ToolResponse(LLMResponse):
	"""도구 호출을 포함할 수 있는 LLM 응답."""

	tool_calls: list[ToolCall] = field(default_factory=list)
	finish_reason: str = "stop"
