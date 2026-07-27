"""OpenAI Codex CLI provider.

ChatGPT Plus/Pro 구독 사용자가 API 키 없이 LLM을 사용할 수 있다.
사전 조건: codex CLI 설치 + 로그인 완료.
"""

from __future__ import annotations

import shutil
from typing import Generator

from dartlab.ai.providers.base import BaseProvider
from dartlab.ai.providers.support import codexCli
from dartlab.ai.types import LLMResponse


class CodexProvider(BaseProvider):
    """OpenAI Codex CLI 기반 provider."""

    @property
    def defaultModel(self) -> str:
        """codex CLI 설정 모델 또는 gpt-4.1 폴백."""
        return codexCli.getCodexConfiguredModel() or "gpt-4.1"

    def checkAvailable(self) -> bool:
        """codex CLI 설치 + 로그인 동시 보유 여부."""
        info = codexCli.inspectCodexCli()
        return bool(info.get("installed") and info.get("authenticated"))

    def _ensureAvailable(self) -> None:
        if not shutil.which("codex"):
            from dartlab.ai.providers.support.cliSetup import getCodexInstallGuide

            raise FileNotFoundError(f"Codex CLI를 찾을 수 없습니다.\n\n{getCodexInstallGuide()}")

        info = codexCli.inspectCodexCli()
        if not info.get("installed"):
            from dartlab.ai.providers.support.cliSetup import getCodexInstallGuide

            raise FileNotFoundError(f"Codex CLI를 찾을 수 없습니다.\n\n{getCodexInstallGuide()}")
        if not info.get("authenticated"):
            raise PermissionError(
                "Codex CLI가 설치되어 있지만 로그인이 필요합니다.\n\n"
                "  codex login\n\n"
                "ChatGPT 계정으로 로그인한 뒤 다시 시도하세요."
            )

    def _buildPrompt(self, messages: list[dict[str, str]]) -> str:
        parts: list[str] = []
        for m in messages:
            if m["role"] == "system":
                parts.insert(0, f"[System Instructions]\n{m['content']}\n")
            else:
                parts.append(m["content"])
        return "\n\n".join(parts)

    def _selectSandbox(self, messages: list[dict[str, str]]) -> str:
        return codexCli.inferCodexSandbox(messages)

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        """messages → codex CLI 호출 (300s 타임아웃) → LLMResponse."""
        self._ensureAvailable()
        prompt = self._buildPrompt(messages)
        sandbox = self._selectSandbox(messages)
        answer, usage = codexCli.runCodexExec(
            prompt,
            model=self.resolvedModel,
            sandbox=sandbox,
            timeout=300,
        )

        return LLMResponse(
            answer=answer,
            provider="codex",
            model=self.resolvedModel,
            usage=usage,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        """codex CLI 일괄 응답을 line 단위 simulated stream 으로 yield."""
        self._ensureAvailable()
        prompt = self._buildPrompt(messages)
        sandbox = self._selectSandbox(messages)
        full_text, _usage = codexCli.runCodexExec(
            prompt,
            model=self.resolvedModel,
            sandbox=sandbox,
            timeout=300,
        )

        if full_text:
            yield from _simulateStream(full_text)


def _simulateStream(text: str) -> Generator[str, None, None]:
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
