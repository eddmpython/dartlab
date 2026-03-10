"""ChatGPT OAuth 기반 Codex provider — 진짜 SSE 스트리밍.

ChatGPT Plus/Pro 구독 계정의 OAuth 토큰으로
chatgpt.com/backend-api 엔드포인트에 직접 SSE 스트리밍 요청.
Codex CLI 없이 동작하며, 토큰 단위 실시간 스트리밍을 지원한다.

비공식 API이므로 예고 없이 변경될 수 있다.
에러 발생 시 구체적 사유를 분류하여 사용자에게 안내한다.
STATUS.md의 "브레이킹 체인지 대응 순서" 참조.

참고: opencode-openai-codex-auth 프로젝트의 접근법.
"""

from __future__ import annotations

import json
import logging
from typing import Generator

import requests

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMResponse
from dartlab.engines.ai import oauthToken
from dartlab.engines.ai.oauthToken import TokenRefreshError

log = logging.getLogger(__name__)

CODEX_API_BASE = "https://chatgpt.com/backend-api"
CODEX_RESPONSES_PATH = "/codex/responses"

AVAILABLE_MODELS = [
    "gpt-5.4",
    "gpt-5.3",
    "gpt-5.3-codex",
    "gpt-5.2",
    "gpt-5.2-codex",
    "gpt-5.1",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "o3",
    "o4-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
]


class ChatGPTOAuthError(Exception):
    """ChatGPT OAuth provider 에러 — action 필드로 사용자 대응 안내."""

    def __init__(self, action: str, message: str, *, detail: str = ""):
        self.action = action
        self.message = message
        self.detail = detail
        super().__init__(message)


def _raise_http_error(status: int, body: str) -> None:
    """HTTP 상태코드별 구체적 에러."""
    if status == 401:
        raise ChatGPTOAuthError(
            "relogin",
            "ChatGPT 인증이 만료되었습니다. 설정에서 재로그인하세요.",
            detail=f"HTTP 401: {body[:200]}",
        )
    if status == 403:
        raise ChatGPTOAuthError(
            "check_headers",
            "ChatGPT API 접근이 거부되었습니다. "
            "OpenAI가 요청 헤더 검증을 변경했을 수 있습니다. "
            "openai/codex 레포에서 최신 헤더를 확인하세요.",
            detail=f"HTTP 403: {body[:200]}",
        )
    if status == 404:
        raise ChatGPTOAuthError(
            "check_endpoint",
            "ChatGPT API 엔드포인트를 찾을 수 없습니다. "
            "OpenAI가 URL을 변경했을 수 있습니다. "
            "openai/codex 레포에서 최신 엔드포인트를 확인하세요.",
            detail=f"HTTP 404: {body[:200]}",
        )
    if status == 429:
        raise ChatGPTOAuthError(
            "rate_limit",
            "ChatGPT API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.",
            detail=f"HTTP 429: {body[:200]}",
        )
    raise ChatGPTOAuthError(
        "unknown",
        f"ChatGPT API 오류가 발생했습니다 (HTTP {status}).",
        detail=body[:300],
    )


class OAuthCodexProvider(BaseProvider):
    """ChatGPT OAuth 기반 Codex provider."""

    @property
    def default_model(self) -> str:
        return "gpt-5.4"

    def check_available(self) -> bool:
        try:
            return oauthToken.is_authenticated()
        except TokenRefreshError:
            return False

    def _get_token_or_raise(self) -> str:
        """유효한 토큰 반환. 실패 시 구체적 에러."""
        try:
            token = oauthToken.get_valid_token()
        except TokenRefreshError as e:
            if e.reason == "client_changed":
                raise ChatGPTOAuthError("check_client_id", e.detail) from e
            raise ChatGPTOAuthError(
                "relogin",
                f"ChatGPT 토큰 갱신 실패: {e.detail}",
            ) from e
        if not token:
            raise ChatGPTOAuthError(
                "login",
                "ChatGPT OAuth 인증이 필요합니다. 설정에서 로그인하세요.",
            )
        return token

    def _request_with_retry(self, token: str, body: dict, *, stream: bool = False):
        """요청 + 401 시 refresh 재시도. 실패 시 구체적 에러."""
        url = f"{CODEX_API_BASE}{CODEX_RESPONSES_PATH}"
        headers = self._build_headers(token)

        try:
            resp = requests.post(
                url, headers=headers, json=body,
                stream=stream, timeout=300,
            )
        except requests.ConnectionError:
            raise ChatGPTOAuthError(
                "network",
                "ChatGPT 서버에 연결할 수 없습니다. 네트워크를 확인하세요.",
            )
        except requests.Timeout:
            raise ChatGPTOAuthError(
                "network",
                "ChatGPT 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도하세요.",
            )

        if resp.status_code == 401:
            try:
                refreshed = oauthToken.refresh_access_token()
            except TokenRefreshError as e:
                raise ChatGPTOAuthError(
                    "relogin",
                    f"토큰 갱신 실패 ({e.reason}): {e.detail}",
                ) from e
            if refreshed:
                headers = self._build_headers(refreshed["access_token"])
                resp = requests.post(
                    url, headers=headers, json=body,
                    stream=stream, timeout=300,
                )

        if resp.status_code != 200:
            resp.encoding = "utf-8"
            _raise_http_error(resp.status_code, resp.text[:500])

        resp.encoding = "utf-8"
        return resp

    def _build_headers(self, token: str) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "originator": "codex_cli_rs",
            "OpenAI-Beta": "responses=experimental",
            "accept": "text/event-stream",
        }
        account_id = oauthToken.get_account_id()
        if account_id:
            headers["chatgpt-account-id"] = account_id
        return headers

    def _build_body(self, messages: list[dict[str, str]]) -> dict:
        system_parts = []
        input_items = []

        for m in messages:
            if m["role"] == "system":
                system_parts.append(m["content"])
            elif m["role"] == "assistant":
                input_items.append({
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": m["content"]}],
                })
            else:
                input_items.append({
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": m["content"]}],
                })

        body: dict = {
            "model": self.resolved_model,
            "stream": True,
            "store": False,
            "input": input_items,
            "include": ["reasoning.encrypted_content"],
        }

        if system_parts:
            body["instructions"] = "\n\n".join(system_parts)

        return body

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        token = self._get_token_or_raise()
        body = self._build_body(messages)
        resp = self._request_with_retry(token, body)

        answer = self._parse_sse_response(resp.text)
        if not answer:
            log.warning("SSE 응답에서 텍스트를 추출하지 못함 — 이벤트 포맷 변경 의심")
            raise ChatGPTOAuthError(
                "check_sse",
                "ChatGPT 응답은 수신되었지만 텍스트를 추출할 수 없습니다. "
                "OpenAI가 SSE 이벤트 포맷을 변경했을 수 있습니다. "
                "openai/codex 레포에서 최신 이벤트 타입을 확인하세요.",
            )

        return LLMResponse(
            answer=answer,
            provider="chatgpt",
            model=self.resolved_model,
        )

    def stream(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        token = self._get_token_or_raise()
        body = self._build_body(messages)
        resp = self._request_with_retry(token, body, stream=True)

        has_content = False
        event_types_seen: set[str] = set()

        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue

            data_str = line[6:]
            if data_str == "[DONE]":
                break

            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type", "")
            if event_type:
                event_types_seen.add(event_type)

            if event_type == "response.output_text.delta":
                delta = event.get("delta", "")
                if delta:
                    has_content = True
                    yield delta

            elif event_type == "response.content_part.delta":
                delta = event.get("delta", {})
                text = delta.get("text", "") if isinstance(delta, dict) else ""
                if text:
                    has_content = True
                    yield text

            elif event_type == "response.output_item.done":
                item = event.get("item", {})
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            text = content.get("text", "")
                            if text:
                                has_content = True
                                yield text

        if not has_content and event_types_seen:
            log.warning(
                "SSE 스트림에서 텍스트 없음 — 수신된 이벤트 타입: %s",
                ", ".join(sorted(event_types_seen)),
            )
            yield (
                "\n\n---\n"
                "[ChatGPT 응답 수신 실패] SSE 이벤트는 도착했지만 텍스트를 추출하지 못했습니다. "
                f"수신된 이벤트 타입: {', '.join(sorted(event_types_seen))}. "
                "OpenAI가 SSE 포맷을 변경했을 수 있습니다."
            )

    def _parse_sse_response(self, raw: str) -> str:
        """완료된 SSE 응답에서 최종 텍스트 추출."""
        answer = ""
        for line in raw.split("\n"):
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "response.completed":
                resp_obj = event.get("response", {})
                for output in resp_obj.get("output", []):
                    if output.get("type") == "message":
                        for content in output.get("content", []):
                            if content.get("type") == "output_text":
                                answer = content.get("text", "")
            elif event.get("type") == "response.output_text.delta":
                answer += event.get("delta", "")

        return answer
