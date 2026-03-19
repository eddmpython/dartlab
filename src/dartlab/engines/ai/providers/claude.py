"""Claude / Anthropic provider."""

from __future__ import annotations

import json
from typing import Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

_CLAUDE_PROVIDER_ERRORS = (ImportError, OSError, RuntimeError, TypeError, ValueError)


def _openai_tools_to_anthropic(tools: list[dict]) -> list[dict]:
    """OpenAI function calling 스키마 → Anthropic tool 스키마 변환.

    OpenAI: [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
    Anthropic: [{"name": ..., "description": ..., "input_schema": ...}]
    """
    result = []
    for t in tools:
        fn = t.get("function", t)
        result.append(
            {
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            }
        )
    return result


def _split_system_and_user(messages: list[dict]) -> tuple[str, list[dict]]:
    """system 메시지를 분리하고 Anthropic 형식 user 메시지 리스트 반환."""
    system_msg = ""
    user_messages = []
    for m in messages:
        if m["role"] == "system":
            system_msg = m["content"] if isinstance(m["content"], str) else m["content"]
        else:
            user_messages.append(m)
    return system_msg, user_messages


class ClaudeProvider(BaseProvider):
    """Anthropic SDK 기반 provider.

    base_url 있으면 OpenAI 호환 모드 (프록시/CLIProxyAPI).
    없으면 anthropic SDK 네이티브 모드.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._use_openai_compat = False

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-6"

    @property
    def supports_native_tools(self) -> bool:
        return True

    def _get_client(self):
        if self._client is not None:
            return self._client

        if self.config.base_url:
            # OpenAI 호환 모드 (프록시)
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai 패키지가 필요합니다 (프록시 모드).\n  uv add dartlab[llm]")
            self._client = OpenAI(
                api_key=self.config.api_key or "proxy",
                base_url=self.config.base_url,
            )
            self._use_openai_compat = True
        else:
            # Anthropic 네이티브 모드
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "anthropic 패키지가 필요합니다.\n"
                    "  uv add dartlab[llm-anthropic]\n\n"
                    "프록시를 사용하려면 base_url을 설정하세요:\n"
                    "  dartlab.llm.configure(provider='claude', base_url='http://...')"
                )
            kwargs = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            self._client = Anthropic(**kwargs)
            self._use_openai_compat = False

        return self._client

    def check_available(self) -> bool:
        try:
            self._get_client()
            return True
        except _CLAUDE_PROVIDER_ERRORS:
            return False

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        client = self._get_client()

        if self._use_openai_compat:
            response = client.chat.completions.create(
                model=self.resolved_model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return LLMResponse(
                answer=response.choices[0].message.content or "",
                provider="claude",
                model=response.model,
                usage=usage,
            )
        else:
            # Anthropic 네이티브
            system_msg, user_messages = _split_system_and_user(messages)
            response = client.messages.create(
                model=self.resolved_model,
                system=system_msg,
                messages=user_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return LLMResponse(
                answer=response.content[0].text,
                provider="claude",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
            )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        client = self._get_client()

        if self._use_openai_compat:
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
        else:
            # Anthropic 네이티브 스트리밍
            system_msg, user_messages = _split_system_and_user(messages)
            with client.messages.stream(
                model=self.resolved_model,
                system=system_msg,
                messages=user_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            ) as stream:
                for text in stream.text_stream:
                    yield text

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolResponse:
        """Claude tool calling — OpenAI 호환 + Anthropic 네이티브 모두 지원."""
        client = self._get_client()

        if self._use_openai_compat:
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
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=json.loads(tc.function.arguments),
                        )
                    )

            return ToolResponse(
                answer=choice.message.content or "",
                provider="claude",
                model=response.model,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                usage=usage,
            )
        else:
            # Anthropic 네이티브 tool use
            return self._complete_with_tools_native(client, messages, tools)

    def _complete_with_tools_native(
        self,
        client,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolResponse:
        """Anthropic 네이티브 tool_use 블록 직접 지원."""
        system_msg, user_messages = _split_system_and_user(messages)

        # Anthropic 메시지 형식으로 변환
        anthropic_messages = self._to_anthropic_messages(user_messages)

        kwargs: dict = {
            "model": self.resolved_model,
            "system": system_msg,
            "messages": anthropic_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            kwargs["tools"] = _openai_tools_to_anthropic(tools)

        response = client.messages.create(**kwargs)

        # response.content에서 text와 tool_use 블록 분리
        answer = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                answer += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        finish_reason = "tool_use" if response.stop_reason == "tool_use" else "stop"

        return ToolResponse(
            answer=answer,
            provider="claude",
            model=response.model,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
        )

    def _to_anthropic_messages(self, messages: list[dict]) -> list[dict]:
        """OpenAI 형식 메시지를 Anthropic 형식으로 변환.

        - assistant + tool_calls → assistant content with tool_use blocks
        - tool role → user content with tool_result blocks
        """
        result = []
        i = 0
        while i < len(messages):
            m = messages[i]
            role = m.get("role", "user")

            if role == "assistant" and "tool_calls" in m:
                # assistant tool_calls → Anthropic content 블록
                content = []
                if m.get("content"):
                    content.append({"type": "text", "text": m["content"]})
                for tc in m["tool_calls"]:
                    fn = tc.get("function", tc)
                    args = fn.get("arguments", "{}")
                    if isinstance(args, str):
                        args = json.loads(args)
                    content.append(
                        {
                            "type": "tool_use",
                            "id": tc.get("id", fn.get("name", "")),
                            "name": fn.get("name", tc.get("name", "")),
                            "input": args,
                        }
                    )
                result.append({"role": "assistant", "content": content})
                i += 1

            elif role == "tool":
                # tool results → Anthropic user message with tool_result blocks
                tool_results = []
                while i < len(messages) and messages[i].get("role") == "tool":
                    tm = messages[i]
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tm.get("tool_call_id", ""),
                            "content": tm.get("content", ""),
                        }
                    )
                    i += 1
                result.append({"role": "user", "content": tool_results})

            else:
                # user/assistant 일반 메시지
                content = m.get("content", "")
                if isinstance(content, list):
                    result.append({"role": role, "content": content})
                else:
                    result.append({"role": role, "content": content or ""})
                i += 1

        return result

    def format_tool_result(self, tool_call_id: str, result: str) -> dict:
        """Anthropic 네이티브: tool_result 블록 형식."""
        if self._use_openai_compat:
            return super().format_tool_result(tool_call_id, result)
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        }

    def format_assistant_tool_calls(
        self,
        answer: str | None,
        tool_calls: list,
    ) -> dict:
        """Anthropic 네이티브: tool_use 블록 형식."""
        if self._use_openai_compat:
            return super().format_assistant_tool_calls(answer, tool_calls)
        content = []
        if answer:
            content.append({"type": "text", "text": answer})
        for tc in tool_calls:
            content.append(
                {
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                }
            )
        return {"role": "assistant", "content": content}
