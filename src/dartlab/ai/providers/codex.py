"""OpenAI Codex CLI provider.

ChatGPT Plus/Pro 구독 사용자가 API 키 없이 LLM을 사용할 수 있다.
사전 조건: codex CLI 설치 + 로그인 완료.
"""

from __future__ import annotations

import shutil
from typing import Generator

from dartlab.ai.providers.base import BaseProvider
from dartlab.ai.providers.support import codex_cli
from dartlab.ai.types import LLMResponse


class CodexProvider(BaseProvider):
    """OpenAI Codex CLI 기반 provider."""

    @property
    def default_model(self) -> str:
        """기본 모델명."""
        return codex_cli.get_codex_configured_model() or "gpt-4.1"

    def check_available(self) -> bool:
        """provider 사용 가능 여부 확인."""
        info = codex_cli.inspect_codex_cli()
        return bool(info.get("installed") and info.get("authenticated"))

    def _ensure_available(self) -> None:
        if not shutil.which("codex"):
            from dartlab.ai.providers.support.cli_setup import get_codex_install_guide

            raise FileNotFoundError(f"Codex CLI를 찾을 수 없습니다.\n\n{get_codex_install_guide()}")

        info = codex_cli.inspect_codex_cli()
        if not info.get("installed"):
            from dartlab.ai.providers.support.cli_setup import get_codex_install_guide

            raise FileNotFoundError(f"Codex CLI를 찾을 수 없습니다.\n\n{get_codex_install_guide()}")
        if not info.get("authenticated"):
            raise PermissionError(
                "Codex CLI가 설치되어 있지만 로그인이 필요합니다.\n\n"
                "  codex login\n\n"
                "ChatGPT 계정으로 로그인한 뒤 다시 시도하세요."
            )

    def _build_prompt(self, messages: list[dict[str, str]]) -> str:
        """messages를 단일 프롬프트로 합성."""
        parts: list[str] = []
        for m in messages:
            if m["role"] == "system":
                parts.insert(0, f"[System Instructions]\n{m['content']}\n")
            else:
                parts.append(m["content"])
        return "\n\n".join(parts)

    def _select_sandbox(self, messages: list[dict[str, str]]) -> str:
        return codex_cli.infer_codex_sandbox(messages)

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        """동기 완료 요청."""
        self._ensure_available()
        prompt = self._build_prompt(messages)
        sandbox = self._select_sandbox(messages)
        answer, usage = codex_cli.run_codex_exec(
            prompt,
            model=self.resolved_model,
            sandbox=sandbox,
            timeout=300,
        )

        return LLMResponse(
            answer=answer,
            provider="codex",
            model=self.resolved_model,
            usage=usage,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """스트리밍 응답 생성."""
        self._ensure_available()
        prompt = self._build_prompt(messages)
        sandbox = self._select_sandbox(messages)
        full_text, _usage = codex_cli.run_codex_exec(
            prompt,
            model=self.resolved_model,
            sandbox=sandbox,
            timeout=300,
        )

        if full_text:
            yield from _simulate_stream(full_text)


def _simulate_stream(text: str) -> Generator[str, None, None]:
    """전체 텍스트를 문장 단위로 잘라 yield — 타이핑 효과."""
    import re

    chunks = re.split(r"(?<=\n)", text)
    for chunk in chunks:
        if not chunk:
            continue
        if len(chunk) > 200:
            words = chunk.split(" ")
            buf = ""
            for w in words:
                buf += w + " "
                if len(buf) >= 40:
                    yield buf
                    buf = ""
            if buf:
                yield buf
        else:
            yield chunk
