"""Claude Code CLI provider — subprocess로 claude CLI 호출.

Claude Pro/Max 구독 사용자가 API 키 없이 LLM을 사용할 수 있다.
사전 조건: claude CLI 설치 + claude auth login 완료.

VSCode 내부 등 중첩 세션 환경에서는 CLI가 hang되므로
Anthropic SDK fallback을 자동으로 사용한다.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from typing import Generator

_IS_WINDOWS = platform.system() == "Windows"

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMResponse

# CLI 별칭 → Anthropic SDK 모델ID 매핑
_ALIAS_TO_MODEL = {
	"opus": "claude-opus-4-6-20250616",
	"sonnet": "claude-sonnet-4-6-20250616",
	"haiku": "claude-haiku-4-5-20251001",
}

# CLI가 hang되는지 빠르게 판별하는 타임아웃 (초)
_CLI_PROBE_TIMEOUT = 8


class ClaudeCodeProvider(BaseProvider):
	"""Claude Code CLI 기반 provider.

	CLI 호출이 실패하거나 중첩 세션(VSCode 등)에서 hang되면
	Anthropic SDK로 자동 fallback한다.
	"""

	def __init__(self, config):
		super().__init__(config)
		# VSCode Claude Code 확장 내부면 CLI가 hang되므로 즉시 SDK fallback
		self._use_sdk = bool(os.environ.get("CLAUDECODE"))
		self._sdk_client = None
		self._api_key_from_cli: str | None = None

	@property
	def default_model(self) -> str:
		return "sonnet"

	def _resolve_sdk_model(self) -> str:
		"""CLI 별칭을 SDK 모델ID로 변환."""
		model = self.resolved_model
		return _ALIAS_TO_MODEL.get(model, model)

	# ── CLI 환경 관리 ──

	def _clean_env(self) -> dict[str, str]:
		"""중첩 세션 방지 — Claude Code/Electron/VSCode 환경변수 제거."""
		env = os.environ.copy()
		for key in list(env.keys()):
			if key.startswith("CLAUDE") or key.startswith("claude"):
				env.pop(key)
		for key in ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ASAR"):
			env.pop(key, None)
		for key in list(env.keys()):
			if key.startswith("VSCODE"):
				env.pop(key)
		return env

	# ── Availability ──

	def check_available(self) -> bool:
		if not shutil.which("claude"):
			return False
		# VSCode 중첩 세션에서는 SDK fallback 필요
		if self._use_sdk:
			# SDK fallback 가능하면 available
			return bool(self._get_sdk_api_key()) and self._sdk_importable()
		try:
			result = subprocess.run(
				["claude", "auth", "status"],
				capture_output=True, text=True, timeout=10,
				shell=_IS_WINDOWS,
				env=self._clean_env(),
			)
			return result.returncode == 0
		except (subprocess.TimeoutExpired, OSError):
			return False

	@staticmethod
	def _sdk_importable() -> bool:
		try:
			import anthropic  # noqa: F401
			return True
		except ImportError:
			return False

	def _ensure_available(self) -> None:
		if not shutil.which("claude"):
			from dartlab.engines.ai.cli_setup import get_claude_code_install_guide
			raise FileNotFoundError(
				f"Claude Code CLI를 찾을 수 없습니다.\n\n"
				f"{get_claude_code_install_guide()}"
			)
		try:
			result = subprocess.run(
				["claude", "auth", "status"],
				capture_output=True, text=True, timeout=10,
				shell=_IS_WINDOWS,
				env=self._clean_env(),
			)
			if result.returncode != 0:
				raise PermissionError(
					"Claude Code CLI가 설치되어 있지만 인증이 필요합니다.\n\n"
					"  claude auth login\n\n"
					"Claude Pro/Max 구독 계정으로 로그인하세요."
				)
		except (subprocess.TimeoutExpired, OSError):
			pass

	# ── SDK Fallback ──

	def _get_sdk_api_key(self) -> str | None:
		"""claude auth 세션에서 API 키를 추출하거나 환경변수에서 가져온다."""
		if self._api_key_from_cli:
			return self._api_key_from_cli

		# 환경변수 우선
		api_key = os.environ.get("ANTHROPIC_API_KEY")
		if api_key:
			self._api_key_from_cli = api_key
			return api_key

		# claude auth status에서 sessionKey 추출 시도
		try:
			result = subprocess.run(
				["claude", "auth", "status", "--json"],
				capture_output=True, text=True, timeout=10,
				shell=_IS_WINDOWS,
				env=self._clean_env(),
			)
			if result.returncode == 0:
				data = json.loads(result.stdout)
				# CLI 인증 세션의 API 키
				key = data.get("apiKey") or data.get("sessionKey")
				if key:
					self._api_key_from_cli = key
					return key
		except Exception:
			pass

		return None

	def _get_sdk_client(self):
		"""Anthropic SDK 클라이언트 생성."""
		if self._sdk_client is not None:
			return self._sdk_client

		try:
			from anthropic import Anthropic
		except ImportError:
			raise ImportError(
				"Claude Code CLI가 현재 환경에서 작동하지 않습니다 (VSCode 중첩 세션).\n"
				"SDK fallback을 위해 anthropic 패키지가 필요합니다:\n"
				"  uv add anthropic\n\n"
				"또는 별도 터미널에서 dartlab ai를 실행하세요."
			)

		api_key = self._get_sdk_api_key()
		if not api_key:
			raise RuntimeError(
				"Claude Code CLI가 현재 환경에서 작동하지 않습니다 (VSCode 중첩 세션).\n\n"
				"해결 방법:\n"
				"1. Settings에서 'Anthropic Claude' provider로 전환 후 API 키 입력\n"
				"2. 또는 별도 터미널(PowerShell/CMD)에서 dartlab ai 실행"
			)

		self._sdk_client = Anthropic(api_key=api_key)
		return self._sdk_client

	def _probe_cli(self) -> bool:
		"""CLI가 실제로 응답하는지 빠르게 확인. hang되면 False."""
		if self._use_sdk:
			return False
		try:
			result = subprocess.run(
				[
					"claude", "-p", "ping", "--output-format", "json",
					"--model", self.resolved_model, "--max-turns", "1",
				],
				stdin=subprocess.DEVNULL,
				capture_output=True,
				timeout=_CLI_PROBE_TIMEOUT,
				env=self._clean_env(),
				shell=_IS_WINDOWS,
			)
			return result.returncode == 0
		except (subprocess.TimeoutExpired, OSError):
			self._use_sdk = True
			return False

	# ── Messages 변환 ──

	def _split_messages(self, messages: list[dict[str, str]]) -> tuple[str, str | None]:
		"""messages에서 system/user를 분리."""
		system_parts: list[str] = []
		user_parts: list[str] = []
		for m in messages:
			if m["role"] == "system":
				system_parts.append(m["content"])
			else:
				user_parts.append(m["content"])
		system = "\n\n".join(system_parts) if system_parts else None
		user = "\n\n".join(user_parts)
		return user, system

	def _split_messages_sdk(self, messages: list[dict[str, str]]) -> tuple[str, list[dict]]:
		"""messages를 Anthropic SDK 포맷으로 분리."""
		system_msg = ""
		user_messages = []
		for m in messages:
			if m["role"] == "system":
				system_msg = m["content"]
			else:
				user_messages.append(m)
		return system_msg, user_messages

	# ── CLI 명령 구성 ──

	def _build_cmd(
		self, prompt: str, system: str | None, *, stream: bool = False,
	) -> list[str]:
		fmt = "stream-json" if stream else "json"
		cmd = [
			"claude", "-p", prompt,
			"--output-format", fmt,
			"--model", self.resolved_model,
			"--max-turns", "1",
		]
		if system:
			cmd.extend(["--system-prompt", system])
		return cmd

	# ── SDK complete/stream ──

	def _sdk_complete(self, messages: list[dict[str, str]]) -> LLMResponse:
		client = self._get_sdk_client()
		system_msg, user_messages = self._split_messages_sdk(messages)
		model = self._resolve_sdk_model()

		response = client.messages.create(
			model=model,
			system=system_msg,
			messages=user_messages,
			max_tokens=self.config.max_tokens,
		)
		return LLMResponse(
			answer=response.content[0].text,
			provider="claude-code",
			model=response.model,
			usage={
				"prompt_tokens": response.usage.input_tokens,
				"completion_tokens": response.usage.output_tokens,
				"total_tokens": response.usage.input_tokens + response.usage.output_tokens,
			},
		)

	def _sdk_stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
		client = self._get_sdk_client()
		system_msg, user_messages = self._split_messages_sdk(messages)
		model = self._resolve_sdk_model()

		with client.messages.stream(
			model=model,
			system=system_msg,
			messages=user_messages,
			max_tokens=self.config.max_tokens,
		) as stream:
			for text in stream.text_stream:
				yield text

	# ── Public API ──

	def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
		self._ensure_available()

		# SDK fallback이 이미 결정된 경우
		if self._use_sdk:
			return self._sdk_complete(messages)

		# CLI 시도
		prompt, system = self._split_messages(messages)
		cmd = self._build_cmd(prompt, system)

		try:
			result = subprocess.run(
				cmd,
				stdin=subprocess.DEVNULL,
				capture_output=True,
				timeout=120,
				env=self._clean_env(),
				shell=_IS_WINDOWS,
			)
		except subprocess.TimeoutExpired:
			# CLI hang → SDK fallback 전환
			self._use_sdk = True
			return self._sdk_complete(messages)

		if result.returncode != 0:
			raw_err = result.stderr or b""
			stderr = raw_err.decode("utf-8", errors="replace").strip() if isinstance(raw_err, bytes) else raw_err.strip()
			raise RuntimeError(
				f"Claude Code CLI 오류 (exit {result.returncode}):\n"
				f"{stderr}"
			)

		raw_out = result.stdout or b""
		stdout = raw_out.decode("utf-8", errors="replace") if isinstance(raw_out, bytes) else raw_out
		data = json.loads(stdout)

		if data.get("is_error"):
			raise RuntimeError(f"Claude Code CLI 오류: {data.get('result', 'unknown')}")

		answer = data.get("result", "")
		usage: dict = {}
		if data.get("total_cost_usd") is not None:
			usage["total_cost_usd"] = data["total_cost_usd"]
		if data.get("num_turns") is not None:
			usage["num_turns"] = data["num_turns"]
		if data.get("duration_ms") is not None:
			usage["duration_ms"] = data["duration_ms"]

		return LLMResponse(
			answer=answer,
			provider="claude-code",
			model=self.resolved_model,
			usage=usage or None,
		)

	def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
		self._ensure_available()

		# SDK fallback 모드
		if self._use_sdk:
			yield from self._sdk_stream(messages)
			return

		# CLI 시도
		prompt, system = self._split_messages(messages)
		cmd = self._build_cmd(prompt, system, stream=True)

		proc = subprocess.Popen(
			cmd,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			env=self._clean_env(),
			shell=_IS_WINDOWS,
		)

		try:
			for raw_line in proc.stdout:  # type: ignore[union-attr]
				line = raw_line.decode("utf-8", errors="replace").strip()
				if not line:
					continue
				try:
					event = json.loads(line)
					if event.get("type") == "assistant" and "content" in event:
						for block in event["content"]:
							if block.get("type") == "text":
								yield block["text"]
					elif event.get("type") == "result":
						text = event.get("result", "")
						if text:
							yield text
				except json.JSONDecodeError:
					continue
		finally:
			proc.terminate()
			try:
				proc.wait(timeout=5)
			except subprocess.TimeoutExpired:
				proc.kill()
