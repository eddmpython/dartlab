"""OAuth token storage for Ask Workbench."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dartlab.ai.settings.providerCatalog import oauthSecretName
from dartlab.ai.settings.secrets import getSecretStore

CHATGPT_AUTH_URL = "https://auth.openai.com/oauth/authorize"
CHATGPT_TOKEN_URL = "https://auth.openai.com/oauth/token"
CHATGPT_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CHATGPT_SCOPE = "openid profile email offline_access api.connectors.read api.connectors.invoke"
OAUTH_REDIRECT_PORT = int(os.environ.get("DARTLAB_OAUTH_REDIRECT_PORT", "1455"))
OAUTH_REDIRECT_URI = os.environ.get(
    "DARTLAB_OAUTH_REDIRECT_URI", f"http://localhost:{OAUTH_REDIRECT_PORT}/auth/callback"
)
TOKEN_PATH = Path(os.environ.get("DARTLAB_OAUTH_TOKEN_PATH", str(Path.home() / ".dartlab" / "oauth_token.json")))
_TOKEN_SECRET_NAME = oauthSecretName("oauth-codex")


class TokenRefreshError(RuntimeError):
    """Raised when a stored OAuth token cannot be refreshed."""


def _tokenCandidates() -> list[Path]:
    return [
        TOKEN_PATH,
        Path.home() / ".dartlab" / "oauth_token.json",
        Path.home() / ".dartlab" / "oauth.json",
    ]


def _removeLegacyTokenFiles() -> None:
    for path in _tokenCandidates():
        with suppress(OSError):
            path.unlink(missing_ok=True)


def _saveToken(data: dict[str, Any]) -> None:
    expires_in = data.get("expires_in")
    if isinstance(expires_in, (int, float)):
        data["expires_at"] = time.time() + float(expires_in)
    getSecretStore().setJson(_TOKEN_SECRET_NAME, data)
    # SecretStore commit 뒤에 남아 있는 구버전 평문 토큰만 정리한다. 새 토큰을 다시
    # 파일로 쓰면 Read 도구나 로컬 백업을 통해 access/refresh token 이 노출된다.
    _removeLegacyTokenFiles()


def loadToken() -> dict[str, Any] | None:
    """env DARTLAB_OAUTH_TOKEN → secret store → legacy file 순서로 토큰 로드."""
    env_token = os.environ.get("DARTLAB_OAUTH_TOKEN")
    if env_token:
        return {"access_token": env_token, "source": "env"}
    data = getSecretStore().getJson(_TOKEN_SECRET_NAME)
    if isinstance(data, dict):
        _removeLegacyTokenFiles()
        return data
    for path in _tokenCandidates():
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            continue
        data = json.loads(raw)
        if isinstance(data, dict):
            getSecretStore().setJson(_TOKEN_SECRET_NAME, data)
            with suppress(OSError):
                path.unlink()
            return data
    return None


def revokeToken() -> None:
    """secret store + legacy 파일 모두 삭제 (재로그인 필요 상태로 복원)."""
    getSecretStore().delete(_TOKEN_SECRET_NAME)
    _removeLegacyTokenFiles()


def getAccountId() -> str | None:
    """토큰 dict 에서 account_id/sub/email 중 첫 발견 값 반환."""
    token = loadToken()
    if not token:
        return None
    for key in ("account_id", "accountId", "sub", "email"):
        value = token.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def isAuthenticated() -> bool:
    """유효 토큰 보유 여부 — getValidToken() 결과로 판정."""
    return getValidToken() is not None


def _pkcePair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def buildAuthUrl() -> tuple[str, str, str]:
    """PKCE flow OAuth URL + verifier + state 생성 (브라우저 로그인 진입점)."""
    authorize_url = os.environ.get("DARTLAB_OAUTH_AUTHORIZE_URL", CHATGPT_AUTH_URL)
    client_id = os.environ.get("DARTLAB_OAUTH_CLIENT_ID", CHATGPT_CLIENT_ID)
    verifier, challenge = _pkcePair()
    state = secrets.token_urlsafe(24)
    scope = os.environ.get("DARTLAB_OAUTH_SCOPE", CHATGPT_SCOPE)
    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "scope": scope,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "id_token_add_organizations": "true",
            "codex_cli_simplified_flow": "true",
            "originator": "codex_cli_rs",
        }
    )
    return f"{authorize_url}?{query}", verifier, state


def exchangeCode(code: str, verifier: str) -> dict[str, Any]:
    """authorization_code + PKCE verifier → access_token 교환 후 저장."""
    token_url = os.environ.get("DARTLAB_OAUTH_TOKEN_URL", CHATGPT_TOKEN_URL)
    client_id = os.environ.get("DARTLAB_OAUTH_CLIENT_ID", CHATGPT_CLIENT_ID)
    payload = urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "code_verifier": verifier,
        }
    ).encode("utf-8")
    request = Request(token_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - configured OAuth endpoint
        body = response.read().decode("utf-8")
    token = json.loads(body)
    if not isinstance(token, dict) or "access_token" not in token:
        raise RuntimeError("OAuth token response did not include access_token.")
    _saveToken(token)
    return token


def refreshAccessToken() -> dict[str, Any] | None:
    """refresh_token 으로 새 access_token 발급 후 저장 (실패 시 TokenRefreshError)."""
    token = loadToken()
    if not token or not token.get("refresh_token"):
        raise TokenRefreshError("저장된 refresh_token이 없습니다. 재로그인이 필요합니다.")
    token_url = os.environ.get("DARTLAB_OAUTH_TOKEN_URL", CHATGPT_TOKEN_URL)
    client_id = os.environ.get("DARTLAB_OAUTH_CLIENT_ID", CHATGPT_CLIENT_ID)
    payload = urlencode(
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": token["refresh_token"],
        }
    ).encode("utf-8")
    request = Request(token_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed OAuth endpoint, env-overridable
            body = response.read().decode("utf-8")
    except OSError as exc:
        raise TokenRefreshError(f"토큰 갱신 실패: {exc}") from exc
    refreshed = json.loads(body)
    if not isinstance(refreshed, dict) or "access_token" not in refreshed:
        raise TokenRefreshError("OAuth refresh response did not include access_token.")
    if "refresh_token" not in refreshed:
        refreshed["refresh_token"] = token["refresh_token"]
    _saveToken(refreshed)
    return refreshed


def getValidToken() -> str | None:
    """만료 5 분 전이면 자동 refresh — 유효 access_token 또는 None."""
    token = loadToken()
    if not token:
        return None
    expires_at = token.get("expires_at")
    if token.get("access_token") and (
        not isinstance(expires_at, (int, float)) or time.time() < float(expires_at) - 300
    ):
        return token.get("access_token")
    refreshed = refreshAccessToken()
    return refreshed.get("access_token") if refreshed else None
