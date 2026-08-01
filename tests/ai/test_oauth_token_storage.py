"""OAuth token 저장소의 평문 파일 회귀 가드."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from dartlab.ai.providers.support import oauthToken


class _MemorySecretStore:
    def __init__(self, loaded: dict[str, Any] | None = None) -> None:
        self.saved: tuple[str, dict[str, Any]] | None = None
        self.loaded = loaded

    def setJson(self, name: str, data: dict[str, Any]) -> None:
        self.saved = (name, dict(data))

    def getJson(self, _name: str) -> dict[str, Any] | None:
        return self.loaded


def testSaveTokenUsesSecretStoreAndRemovesLegacyPlaintext(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    legacy = tmp_path / "oauth_token.json"
    older = tmp_path / "oauth.json"
    legacy.write_text('{"access_token":"exposed"}', encoding="utf-8")
    older.write_text('{"refresh_token":"exposed"}', encoding="utf-8")
    store = _MemorySecretStore()
    monkeypatch.setattr(oauthToken, "getSecretStore", lambda: store)
    monkeypatch.setattr(oauthToken, "_tokenCandidates", lambda: [legacy, older])

    token: dict[str, Any] = {"access_token": "safe", "expires_in": 3600}
    oauthToken._saveToken(token)

    assert store.saved is not None
    assert store.saved[0] == oauthToken._TOKEN_SECRET_NAME
    assert store.saved[1]["access_token"] == "safe"
    assert isinstance(store.saved[1]["expires_at"], float)
    assert not legacy.exists()
    assert not older.exists()


def testLoadTokenRemovesPlaintextWhenSecretStoreAlreadyHasToken(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy = tmp_path / "oauth_token.json"
    legacy.write_text('{"access_token":"exposed"}', encoding="utf-8")
    store = _MemorySecretStore({"access_token": "safe"})
    monkeypatch.delenv("DARTLAB_OAUTH_TOKEN", raising=False)
    monkeypatch.setattr(oauthToken, "getSecretStore", lambda: store)
    monkeypatch.setattr(oauthToken, "_tokenCandidates", lambda: [legacy])

    assert oauthToken.loadToken() == {"access_token": "safe"}
    assert not legacy.exists()
