"""OpenAI Codex CLI provider — subprocess로 codex CLI 호출.

ChatGPT Plus/Pro 구독 사용자가 API 키 없이 LLM을 사용할 수 있다.
사전 조건: codex CLI 설치 + 로그인 완료.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from typing import Generator

_IS_WINDOWS = platform.system() == "Windows"

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMResponse


class CodexProvider(BaseProvider):
    """OpenAI Codex CLI 기반 provider."""

    @property
    def default_model(self) -> str:
        return "gpt-4.1"

    def check_available(self) -> bool:
        if not shutil.which("codex"):
            return False
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=_IS_WINDOWS,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    def _ensure_available(self) -> None:
        if not shutil.which("codex"):
            from dartlab.engines.ai.cli_setup import get_codex_install_guide

            raise FileNotFoundError(f"Codex CLI를 찾을 수 없습니다.\n\n{get_codex_install_guide()}")
        # 설치됐지만 로그인 안 된 경우 확인
        try:
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=_IS_WINDOWS,
            )
            if result.returncode != 0:
                raise PermissionError(
                    "Codex CLI가 설치되어 있지만 로그인이 필요합니다.\n\n"
                    "  codex\n\n"
                    "처음 실행하면 브라우저에서 ChatGPT 계정으로 로그인됩니다."
                )
        except (subprocess.TimeoutExpired, OSError):
            pass

    def _build_prompt(self, messages: list[dict[str, str]]) -> str:
        """messages를 단일 프롬프트로 합성."""
        parts: list[str] = []
        for m in messages:
            if m["role"] == "system":
                parts.insert(0, f"[System Instructions]\n{m['content']}\n")
            else:
                parts.append(m["content"])
        return "\n\n".join(parts)

    def _build_cmd(self) -> list[str]:
        return [
            "codex",
            "exec",
            "-",
            "--json",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
        ]

    def _parse_jsonl(self, output: str) -> tuple[str, dict | None]:
        """JSONL 출력에서 답변과 usage를 추출."""
        answer = ""
        usage: dict = {}

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                event_type = event.get("type", "")

                if event_type == "item.completed":
                    item = event.get("item", {})
                    if item.get("type") == "agent_message":
                        answer = item.get("text", "")

                elif event_type == "turn.completed":
                    turn_usage = event.get("usage", {})
                    if turn_usage:
                        usage["prompt_tokens"] = turn_usage.get("input_tokens")
                        usage["completion_tokens"] = turn_usage.get("output_tokens")
                        pt = usage.get("prompt_tokens") or 0
                        ct = usage.get("completion_tokens") or 0
                        if pt or ct:
                            usage["total_tokens"] = pt + ct
            except json.JSONDecodeError:
                continue

        return answer, usage or None

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        self._ensure_available()
        prompt = self._build_prompt(messages)
        cmd = self._build_cmd()

        try:
            result = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=300,
                shell=_IS_WINDOWS,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError("Codex CLI 응답 시간 초과 (5분)")

        if result.returncode != 0:
            raw_err = result.stderr or b""
            stderr = (
                raw_err.decode("utf-8", errors="replace").strip() if isinstance(raw_err, bytes) else raw_err.strip()
            )
            raise RuntimeError(f"Codex CLI 오류 (exit {result.returncode}):\n{stderr}")

        raw_out = result.stdout or b""
        stdout = raw_out.decode("utf-8", errors="replace") if isinstance(raw_out, bytes) else raw_out
        answer, usage = self._parse_jsonl(stdout)

        if not answer:
            raise RuntimeError("Codex CLI에서 응답을 추출할 수 없습니다.")

        return LLMResponse(
            answer=answer,
            provider="codex",
            model=self.resolved_model,
            usage=usage,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        self._ensure_available()
        prompt = self._build_prompt(messages)
        cmd = self._build_cmd()

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=_IS_WINDOWS,
        )
        proc.stdin.write(prompt.encode("utf-8"))  # type: ignore[union-attr]
        proc.stdin.close()  # type: ignore[union-attr]

        full_text = ""
        try:
            for raw_line in proc.stdout:  # type: ignore[union-attr]
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if event.get("type") == "item.completed":
                        item = event.get("item", {})
                        if item.get("type") == "agent_message":
                            full_text = item.get("text", "")
                except json.JSONDecodeError:
                    continue
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

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
