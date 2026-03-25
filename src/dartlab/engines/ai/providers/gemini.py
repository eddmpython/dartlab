"""Google Gemini provider.

인증: OAuth 2.0 (Google 계정 브라우저 로그인)
- GPT OAuth와 동일한 플로우: 버튼 클릭 → 브라우저 → 콜백 → 토큰 저장
- 토큰: ~/.dartlab/gemini_oauth.json
- client_secret: ~/.dartlab/gemini_client_secret.json (최초 1회 설정)

외부 OAuth 라이브러리 없이 표준 라이브러리 + httpx만 사용.
"""

from __future__ import annotations

import hashlib
import base64
import json
import logging
import secrets
import time
from pathlib import Path
from typing import Any, Generator
from urllib.parse import urlencode

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

_log = logging.getLogger(__name__)

_DARTLAB_DIR = Path.home() / ".dartlab"
_OAUTH_TOKEN_FILE = _DARTLAB_DIR / "gemini_oauth.json"
_CLIENT_SECRET_FILE = _DARTLAB_DIR / "gemini_client_secret.json"

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_OAUTH_SCOPES = "https://www.googleapis.com/auth/generative-language"

OAUTH_REDIRECT_PORT = 8098
_REDIRECT_URI = f"http://localhost:{OAUTH_REDIRECT_PORT}/auth/gemini/callback"


# ── PKCE (GPT OAuth와 동일) ──


def _generatePkce() -> tuple[str, str]:
    """PKCE code_verifier + code_challenge 생성."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


# ── Client credentials ──


def _loadClientSecret() -> dict[str, str]:
    """client_secret.json에서 client_id, client_secret 추출."""
    if not _CLIENT_SECRET_FILE.exists():
        raise FileNotFoundError(
            "Gemini OAuth 설정이 필요합니다.\n"
            "설정 패널에서 Google OAuth Client ID를 등록하세요."
        )
    data = json.loads(_CLIENT_SECRET_FILE.read_text(encoding="utf-8"))
    for key in ("installed", "web"):
        if key in data:
            return {
                "client_id": data[key]["client_id"],
                "client_secret": data[key].get("client_secret", ""),
            }
    # 단순 형식: {"client_id": "...", "client_secret": "..."}
    if "client_id" in data:
        return {
            "client_id": data["client_id"],
            "client_secret": data.get("client_secret", ""),
        }
    raise ValueError("client_secret.json 형식이 올바르지 않습니다.")


def saveClientSecret(clientSecretJson: str) -> None:
    """GUI에서 받은 client_secret JSON을 저장."""
    data = json.loads(clientSecretJson)
    # 형식 검증
    clientId = None
    for key in ("installed", "web"):
        if key in data:
            clientId = data[key].get("client_id")
            break
    if not clientId:
        clientId = data.get("client_id")
    if not clientId:
        raise ValueError("client_id를 찾을 수 없습니다.")
    _DARTLAB_DIR.mkdir(parents=True, exist_ok=True)
    _CLIENT_SECRET_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def hasClientSecret() -> bool:
    """client_secret.json 존재 여부."""
    return _CLIENT_SECRET_FILE.exists()


# ── 토큰 관리 ──


def _loadToken() -> dict[str, Any] | None:
    """저장된 OAuth 토큰 JSON 로드."""
    if not _OAUTH_TOKEN_FILE.exists():
        return None
    try:
        return json.loads(_OAUTH_TOKEN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        _log.warning("gemini OAuth 토큰 파일 손상 — 삭제")
        _OAUTH_TOKEN_FILE.unlink(missing_ok=True)
        return None


def _saveToken(token: dict[str, Any]) -> None:
    """토큰 JSON 저장."""
    _DARTLAB_DIR.mkdir(parents=True, exist_ok=True)
    _OAUTH_TOKEN_FILE.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")


def _refreshAccessToken(token: dict[str, Any]) -> dict[str, Any] | None:
    """refresh_token으로 access_token 갱신."""
    refreshToken = token.get("refresh_token")
    if not refreshToken:
        return None
    try:
        clientCreds = _loadClientSecret()
    except (FileNotFoundError, ValueError):
        return None

    import httpx

    resp = httpx.post(
        _GOOGLE_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refreshToken,
            "client_id": clientCreds["client_id"],
            "client_secret": clientCreds["client_secret"],
        },
        timeout=15,
    )
    if resp.status_code != 200:
        _log.warning(f"gemini OAuth 토큰 갱신 실패: {resp.status_code}")
        return None

    data = resp.json()
    token["access_token"] = data["access_token"]
    token["expires_at"] = time.time() + data.get("expires_in", 3600)
    if "refresh_token" in data:
        token["refresh_token"] = data["refresh_token"]
    _saveToken(token)
    return token


def _getValidToken() -> dict[str, Any] | None:
    """유효한 access_token이 있는 토큰 반환. 만료 시 자동 갱신."""
    token = _loadToken()
    if token is None:
        return None

    expiresAt = token.get("expires_at", 0)
    if time.time() < expiresAt - 60:
        return token

    refreshed = _refreshAccessToken(token)
    if refreshed is None:
        _OAUTH_TOKEN_FILE.unlink(missing_ok=True)
        return None
    return refreshed


# ── OAuth 플로우 (GPT와 동일한 패턴) ──


def buildAuthUrl() -> tuple[str, str, str]:
    """OAuth authorize URL + PKCE verifier + state 반환."""
    clientCreds = _loadClientSecret()
    verifier, challenge = _generatePkce()
    state = secrets.token_urlsafe(32)
    params = {
        "response_type": "code",
        "client_id": clientCreds["client_id"],
        "redirect_uri": _REDIRECT_URI,
        "scope": _OAUTH_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"
    return url, verifier, state


def exchangeCode(code: str, verifier: str) -> None:
    """Authorization code → 토큰 교환 + 저장. (PKCE)"""
    clientCreds = _loadClientSecret()

    import httpx

    resp = httpx.post(
        _GOOGLE_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _REDIRECT_URI,
            "client_id": clientCreds["client_id"],
            "client_secret": clientCreds["client_secret"],
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if resp.status_code != 200:
        raise ValueError(f"토큰 교환 실패: {resp.status_code} {resp.text}")

    data = resp.json()
    token = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        "expires_at": time.time() + data.get("expires_in", 3600),
        "token_type": data.get("token_type", "Bearer"),
        "scope": data.get("scope", _OAUTH_SCOPES),
    }
    _saveToken(token)
    _log.info("Gemini OAuth 인증 완료 — 토큰 저장됨")


def revokeOAuth() -> None:
    """저장된 OAuth 토큰 삭제."""
    _OAUTH_TOKEN_FILE.unlink(missing_ok=True)


def isOAuthAuthenticated() -> bool:
    """Gemini OAuth 토큰이 유효한지 확인."""
    return _getValidToken() is not None


# ── Provider 클래스 ──


class GeminiProvider(BaseProvider):
    """Google Gemini API provider.

    google-genai SDK 기반. OAuth 2.0 전용.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._auth_method: str = "none"

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from google import genai
        except ImportError:
            raise ImportError("google-genai 패키지가 필요합니다.\n  uv add google-genai")

        # API key는 config에 명시적으로 설정한 경우에만 사용
        if self.config.api_key:
            self._client = genai.Client(api_key=self.config.api_key)
            self._auth_method = "api_key"
            return self._client

        # 기본: OAuth 2.0
        token = _getValidToken()
        if token is None:
            raise ValueError(
                "Gemini OAuth 인증이 필요합니다.\n"
                "  서버: 설정 패널에서 Google 로그인\n"
                "  CLI: dartlab setup gemini"
            )

        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials(
                token=token["access_token"],
                refresh_token=token.get("refresh_token"),
                token_uri=_GOOGLE_TOKEN_URL,
                client_id=_loadClientSecret()["client_id"],
                client_secret=_loadClientSecret()["client_secret"],
                scopes=[_OAUTH_SCOPES],
            )
            self._client = genai.Client(credentials=creds)
        except ImportError:
            raise ImportError("google-auth 패키지가 필요합니다.\n  uv add google-auth")

        self._auth_method = "oauth"
        return self._client

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    @property
    def supports_native_tools(self) -> bool:
        return True

    def check_available(self) -> bool:
        """OAuth 토큰이 있고 SDK가 설치되어 있으면 True."""
        try:
            from google import genai  # noqa: F401
        except ImportError:
            return False
        return _getValidToken() is not None

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
