"""Google Gemini provider.

인증: OAuth 2.0 (Google 계정 로그인)
- 첫 실행: 브라우저 로그인 → 토큰 ~/.dartlab/gemini_oauth.json 저장
- 이후: 저장된 토큰 자동 사용 (만료 시 자동 갱신)
- client_secret.json: ~/.dartlab/gemini_client_secret.json 에 배치
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Generator

from dartlab.engines.ai.providers.base import BaseProvider
from dartlab.engines.ai.types import LLMConfig, LLMResponse, ToolCall, ToolResponse

_log = logging.getLogger(__name__)

_DARTLAB_DIR = Path.home() / ".dartlab"
_OAUTH_TOKEN_FILE = _DARTLAB_DIR / "gemini_oauth.json"
_CLIENT_SECRET_FILE = _DARTLAB_DIR / "gemini_client_secret.json"
_OAUTH_SCOPES = ["https://www.googleapis.com/auth/generative-language"]


def _loadOAuthCredentials():
    """저장된 OAuth 토큰을 로드하고, 만료 시 자동 갱신."""
    if not _OAUTH_TOKEN_FILE.exists():
        return None

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(_OAUTH_TOKEN_FILE), _OAUTH_SCOPES)
    except (json.JSONDecodeError, ValueError, KeyError):
        _log.warning("gemini OAuth 토큰 파일 손상 — 삭제 후 재인증 필요")
        _OAUTH_TOKEN_FILE.unlink(missing_ok=True)
        return None

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _saveOAuthCredentials(creds)
            return creds
        except Exception as e:
            _log.warning(f"gemini OAuth 토큰 갱신 실패: {e}")
            _OAUTH_TOKEN_FILE.unlink(missing_ok=True)
            return None

    return None


def _ensureOAuthDeps():
    """google_auth_oauthlib 설치 확인."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401
    except ImportError:
        raise ImportError(
            "Google OAuth 인증에 필요한 패키지가 없습니다.\n"
            "  uv add google-auth-oauthlib"
        )


def _ensureClientSecret():
    """client_secret.json 존재 확인."""
    if not _CLIENT_SECRET_FILE.exists():
        raise FileNotFoundError(
            f"Google OAuth client secret 파일이 필요합니다.\n"
            f"  위치: {_CLIENT_SECRET_FILE}\n"
            f"  생성: https://console.cloud.google.com/apis/credentials\n"
            f"  → OAuth 2.0 Client ID → Desktop app → JSON 다운로드"
        )


OAUTH_REDIRECT_PORT = 8098
_REDIRECT_URI = f"http://localhost:{OAUTH_REDIRECT_PORT}/auth/gemini/callback"


def buildAuthUrl() -> tuple[str, str]:
    """OAuth authorize URL + state 반환. 서버/GUI에서 호출."""
    _ensureOAuthDeps()
    _ensureClientSecret()
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(_CLIENT_SECRET_FILE),
        scopes=_OAUTH_SCOPES,
        redirect_uri=_REDIRECT_URI,
    )
    authUrl, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authUrl, state


def exchangeCode(code: str, state: str) -> None:
    """Authorization code → 토큰 교환 + 저장."""
    _ensureOAuthDeps()
    _ensureClientSecret()
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        str(_CLIENT_SECRET_FILE),
        scopes=_OAUTH_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=state,
    )
    flow.fetch_token(code=code)
    _saveOAuthCredentials(flow.credentials)
    _log.info("Gemini OAuth 인증 완료 — 토큰 저장됨")


def _runOAuthFlow():
    """CLI용: 브라우저 기반 OAuth 로그인 → 토큰 저장."""
    _ensureOAuthDeps()
    _ensureClientSecret()
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(_CLIENT_SECRET_FILE), _OAUTH_SCOPES)
    creds = flow.run_local_server(port=0)
    _saveOAuthCredentials(creds)
    _log.info("Gemini OAuth 인증 완료 — 토큰 저장됨")
    return creds


def _saveOAuthCredentials(creds) -> None:
    """OAuth credential을 JSON으로 저장."""
    _DARTLAB_DIR.mkdir(parents=True, exist_ok=True)
    _OAUTH_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")


def revokeOAuth() -> None:
    """저장된 OAuth 토큰 삭제."""
    _OAUTH_TOKEN_FILE.unlink(missing_ok=True)


def isOAuthAuthenticated() -> bool:
    """Gemini OAuth 토큰이 유효한지 확인."""
    return _loadOAuthCredentials() is not None


class GeminiProvider(BaseProvider):
    """Google Gemini API provider.

    google-genai SDK 기반. OAuth 2.0 전용.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._auth_method: str = "none"  # "oauth" | "api_key" | "none"

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
        creds = _loadOAuthCredentials()
        if creds is None:
            creds = _runOAuthFlow()

        self._client = genai.Client(credentials=creds)
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
        return _loadOAuthCredentials() is not None

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

        # tool call 추출
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
        """Gemini tool result → OpenAI 형식으로 변환 (agent loop 호환)."""
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
            # tool result → user 메시지로 변환 (Gemini function response)
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

        # Gemini는 additionalProperties를 지원하지 않으므로 제거
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
