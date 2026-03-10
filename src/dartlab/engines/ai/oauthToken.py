"""ChatGPT OAuth 토큰 관리.

PKCE(Proof Key for Code Exchange) 플로우로 ChatGPT 계정 인증 후
access_token / refresh_token을 안전하게 저장·갱신한다.

토큰 저장: ~/.dartlab/oauth_token.json (user-level, 600 permission)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


CHATGPT_AUTH_URL = "https://auth.openai.com/oauth/authorize"
CHATGPT_TOKEN_URL = "https://auth.openai.com/oauth/token"
CHATGPT_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CHATGPT_SCOPE = "openid profile email offline_access"

OAUTH_REDIRECT_PORT = 1455
OAUTH_REDIRECT_URI = f"http://localhost:{OAUTH_REDIRECT_PORT}/auth/callback"

_TOKEN_DIR = Path.home() / ".dartlab"
_TOKEN_FILE = _TOKEN_DIR / "oauth_token.json"


def _generate_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_auth_url() -> tuple[str, str, str]:
    """OAuth 인증 URL과 PKCE verifier, state를 반환."""
    verifier, challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)
    params = {
        "response_type": "code",
        "client_id": CHATGPT_CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "scope": CHATGPT_SCOPE,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
        "originator": "codex_cli_rs",
    }
    url = f"{CHATGPT_AUTH_URL}?{urlencode(params)}"
    return url, verifier, state


def exchange_code(code: str, verifier: str) -> dict[str, Any]:
    """Authorization code를 access_token으로 교환."""
    import requests

    resp = requests.post(
        CHATGPT_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": CHATGPT_CLIENT_ID,
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _save_token(data)
    return data


class TokenRefreshError(Exception):
    """refresh_token 갱신 실패 — 사유를 분류하여 전달."""

    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"토큰 갱신 실패 ({reason}): {detail}")


def refresh_access_token() -> dict[str, Any] | None:
    """저장된 refresh_token으로 access_token 갱신.

    Raises:
        TokenRefreshError: 갱신 실패 시 사유 분류
            - "no_token": 저장된 토큰 없음
            - "expired": refresh_token 만료
            - "reused": refresh_token 이미 사용됨 (rotation)
            - "revoked": refresh_token 취소됨
            - "network": 네트워크 오류
            - "unknown": 분류 불가
    """
    token_data = load_token()
    if not token_data or not token_data.get("refresh_token"):
        raise TokenRefreshError("no_token", "저장된 토큰이 없습니다. 재로그인이 필요합니다.")

    import requests

    try:
        resp = requests.post(
            CHATGPT_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": CHATGPT_CLIENT_ID,
                "refresh_token": token_data["refresh_token"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
    except requests.ConnectionError:
        raise TokenRefreshError("network", "OpenAI 인증 서버에 연결할 수 없습니다.")
    except requests.Timeout:
        raise TokenRefreshError("network", "OpenAI 인증 서버 응답 시간 초과.")

    if resp.status_code == 200:
        data = resp.json()
        if "refresh_token" not in data:
            data["refresh_token"] = token_data["refresh_token"]
        _save_token(data)
        return data

    error_body = {}
    try:
        error_body = resp.json()
    except (json.JSONDecodeError, ValueError):
        pass

    error_code = error_body.get("error", "")
    error_desc = error_body.get("error_description", resp.text[:200])

    if "expired" in error_code or "expired" in error_desc.lower():
        raise TokenRefreshError("expired", "refresh_token이 만료되었습니다. 재로그인이 필요합니다.")
    if "reuse" in error_code or "already" in error_desc.lower():
        raise TokenRefreshError("reused", "refresh_token이 이미 사용되었습니다. 재로그인이 필요합니다.")
    if "revoke" in error_code or "invalid_grant" in error_code:
        raise TokenRefreshError("revoked", "refresh_token이 취소되었습니다. 재로그인이 필요합니다.")
    if "invalid_client" in error_code:
        raise TokenRefreshError(
            "client_changed",
            "OAuth Client ID가 변경된 것 같습니다. "
            "openai/codex 레포에서 최신 Client ID를 확인하세요.",
        )

    raise TokenRefreshError("unknown", f"HTTP {resp.status_code}: {error_desc}")


def get_valid_token() -> str | None:
    """유효한 access_token을 반환. 만료 임박 시 자동 갱신.

    Raises:
        TokenRefreshError: 갱신 실패 시 (사유 분류 포함)
    """
    token_data = load_token()
    if not token_data:
        return None

    expires_at = token_data.get("expires_at", 0)
    if time.time() < expires_at - 300:
        return token_data.get("access_token")

    refreshed = refresh_access_token()
    if refreshed:
        return refreshed.get("access_token")

    return None


def is_authenticated() -> bool:
    return get_valid_token() is not None


def load_token() -> dict[str, Any] | None:
    if not _TOKEN_FILE.exists():
        return None
    raw = _TOKEN_FILE.read_text(encoding="utf-8")
    return json.loads(raw)


def revoke_token() -> None:
    if _TOKEN_FILE.exists():
        _TOKEN_FILE.unlink()


def get_account_id() -> str | None:
    """JWT access_token에서 ChatGPT account_id 추출."""
    token = get_valid_token()
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload_b64 = parts[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
    auth_claim = payload.get("https://api.openai.com/auth", {})
    if isinstance(auth_claim, dict):
        return auth_claim.get("account_id") or auth_claim.get("org_id")
    return None


def _save_token(data: dict[str, Any]) -> None:
    _TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    expires_in = data.get("expires_in", 3600)
    data["expires_at"] = time.time() + expires_in
    _TOKEN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if os.name != "nt":
        _TOKEN_FILE.chmod(0o600)
