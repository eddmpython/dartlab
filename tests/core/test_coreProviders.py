"""core/providers/ — provider 카탈로그 + secrets + getDefaultProvider 단위 테스트.

P1 PR 1: ai/settings/{provider_catalog, secrets, routing} 의 core 강등 검증.
ai/settings/* shim 의 BC alias 도 같이 검증.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import dartlab.core.providers.secrets as secretModule
from dartlab.core.providers import (
    _PROVIDERS,
    AI_ROLES,
    ProviderSpec,
    SecretStore,
    apiKeySecretName,
    buildProviderCatalog,
    getDefaultProvider,
    getProviderSpec,
    getSecretStore,
    normalizeProvider,
    oauthSecretName,
    publicProviderIds,
    wiredProviderIds,
)

pytestmark = pytest.mark.unit


def test_aiRolesIsTuple():
    """AI_ROLES 는 4 개 표준 역할의 immutable tuple."""
    assert AI_ROLES == ("analysis", "summary", "coding", "ui_control")


def test_normalizeProviderKnown():
    """알려진 provider 는 strip 후 그대로 반환."""
    assert normalizeProvider("openai") == "openai"
    assert normalizeProvider("  openai  ") == "openai"


def test_normalizeProviderUnknownPassthrough():
    """미등록 provider 는 원본 그대로 (None 만 None)."""
    assert normalizeProvider("unknown-provider") == "unknown-provider"
    assert normalizeProvider(None) is None


def test_getProviderSpecValid():
    """등록된 provider id 는 ProviderSpec 반환."""
    spec = getProviderSpec("openai")
    assert isinstance(spec, ProviderSpec)
    assert spec.id == "openai"
    assert spec.auth_kind == "api_key"
    assert spec.env_key == "OPENAI_API_KEY"


def test_getProviderSpecMissing():
    """미등록 provider id 는 None."""
    assert getProviderSpec("does-not-exist") is None


def test_secretNameFormat():
    """SecretStore 키 이름 — `provider:{id}:api_key` / `provider:{id}:oauth`."""
    assert apiKeySecretName("openai") == "provider:openai:api_key"
    assert oauthSecretName("oauth-codex") == "provider:oauth-codex:oauth"


def test_publicProviderIdsExcludesHidden():
    """publicProviderIds 는 public=True 만."""
    public = set(publicProviderIds())
    wired = wiredProviderIds()
    assert public.issubset(wired)
    for pid in public:
        assert _PROVIDERS[pid].public is True


def test_buildProviderCatalogJsonSafe():
    """build 결과는 JSON-safe — json.dumps 로 round-trip 가능."""
    catalog = buildProviderCatalog()
    payload = json.dumps(catalog, ensure_ascii=False)
    assert "openai" in payload
    decoded = json.loads(payload)
    assert isinstance(decoded, list)
    assert all("id" in item for item in decoded)


def test_secretStoreRoundTrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """SecretStore — set/get/has/delete 기본 round-trip."""
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: True)
    monkeypatch.setattr(secretModule, "_protectWindows", lambda raw: raw)
    monkeypatch.setattr(secretModule, "_unprotectWindows", lambda raw: raw)
    store = SecretStore(path=tmp_path / "secrets.json")
    store.set("test-key", "test-value")
    assert store.has("test-key") is True
    assert store.get("test-key") == "test-value"
    store.delete("test-key")
    assert store.has("test-key") is False
    assert store.get("test-key") is None


def test_getSecretStoreReturnsInstance():
    """getSecretStore — 기본 경로의 SecretStore 인스턴스 반환."""
    store = getSecretStore()
    assert isinstance(store, SecretStore)


def test_credentialManager_reads_ai_secret_through_provider_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CredentialManager의 public 단건 조회가 provider id keyed 상태표를 정확히 찾는다."""
    from dartlab.core.credentials import CredentialManager

    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: True)
    monkeypatch.setattr(secretModule, "_protectWindows", lambda raw: raw)
    monkeypatch.setattr(secretModule, "_unprotectWindows", lambda raw: raw)
    getSecretStore().set(apiKeySecretName("openai"), "stored-openai-key")
    originalLoad = secretModule.SecretStore._load
    loads = 0

    def countedLoad(store):
        nonlocal loads
        loads += 1
        return originalLoad(store)

    monkeypatch.setattr(secretModule.SecretStore, "_load", countedLoad)

    status = CredentialManager().getCredential("openai_api_key")

    assert status.configured is True
    assert status.name == "openai_api_key"
    assert status.source == "secret_store"
    assert loads == 2  # 전체 key index 1회 + 실제 존재하는 openai 값 복호화 1회


def test_getDefaultProviderMissingProfile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """ai_profile.json 미존재 → None (loud-fail 아닌 silent return)."""
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    assert getDefaultProvider() is None


def test_getDefaultProviderReadsProfile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """ai_profile.json 의 defaultProvider 필드만 직접 추출."""
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    profile = tmp_path / "ai_profile.json"
    profile.write_text(json.dumps({"defaultProvider": "gemini"}), encoding="utf-8")
    assert getDefaultProvider() == "gemini"


def test_getDefaultProviderHandlesLegacyKey(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """`provider` 필드 (legacy) 도 지원."""
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    profile = tmp_path / "ai_profile.json"
    profile.write_text(json.dumps({"provider": "groq"}), encoding="utf-8")
    assert getDefaultProvider() == "groq"


def test_shimSnakeAliasesStillWork():
    """ai/settings/provider_catalog shim 의 snake alias — 0.10 까지 BC 보장."""
    from dartlab.ai.settings.providerCatalog import (
        getProviderSpec,
        normalizeProvider,
    )
    from dartlab.ai.settings.secrets import getSecretStore

    assert normalizeProvider("openai") == "openai"
    assert getProviderSpec("openai").id == "openai"
    assert isinstance(getSecretStore(), SecretStore)


def test_shimRoutingAlias():
    """ai/settings/routing shim 도 동일 BC."""
    from dartlab.ai.settings.routing import AI_ROLES as legacyRoles
    from dartlab.ai.settings.routing import normalizeRole

    assert legacyRoles == AI_ROLES
    assert normalizeRole("Analysis") == "analysis"
    assert normalizeRole("nope") is None
