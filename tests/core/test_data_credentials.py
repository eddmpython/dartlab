"""데이터 공급자 자격증명 레지스트리 회귀 — `core/providers/dataCredentials.py`.

검증:
  1. getKey 우선순위 — 명시 > 환경변수 > SecretStore > None.
  2. resolveKey 미설정 시 레지스트리 기반 안내 CredentialError (envKey·발급 URL 포함).
  3. getSpec 미등록 공급자 가드.
  4. setCredential → SecretStore 라운드트립 (env 부재 시 secret 폴백 해석).
  5. envTemplate / credentialStatus SSOT 불변식 (모든 공급자·envKey 포함).
  6. dataGoKr 단일 키 = gov/customs/pension 3 소스 (공급자 단위 설계 불변식).
"""

from __future__ import annotations

import json

import pytest

import dartlab.core.providers.secrets as secretModule

pytestmark = pytest.mark.unit

_PROVIDER_ENVS = (
    "DATA_GO_KR_KEY",
    "FRED_API_KEY",
    "ECOS_API_KEY",
    "DART_API_KEY",
    "DART_API_KEYS",
    "KRX_API_KEY",
    "HF_TOKEN",
    "OPENFIGI_API_KEY",
)


@pytest.fixture
def cleanEnv(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """모든 공급자 env 제거 + SecretStore 를 tmp 로 격리."""
    for key in _PROVIDER_ENVS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DARTLAB_HOME", str(tmp_path))
    monkeypatch.setattr(secretModule, "_usesDpapi", lambda: True)
    monkeypatch.setattr(secretModule, "_protectWindows", lambda raw: raw)
    monkeypatch.setattr(secretModule, "_unprotectWindows", lambda raw: raw)
    return tmp_path


def test_getKey_precedence(cleanEnv, monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core.providers.dataCredentials import getKey

    assert getKey("dataGoKr") is None
    assert getKey("dataGoKr", "explicit") == "explicit"
    monkeypatch.setenv("DATA_GO_KR_KEY", "envval")
    assert getKey("dataGoKr") == "envval"
    # 명시 인자가 env 보다 우선
    assert getKey("dataGoKr", "explicit") == "explicit"


def test_resolveKey_missing_guidance(cleanEnv) -> None:
    from dartlab.core.providers.dataCredentials import CredentialError, resolveKey

    with pytest.raises(CredentialError) as exc:
        resolveKey("dataGoKr")
    msg = str(exc.value)
    assert "DATA_GO_KR_KEY" in msg
    assert "data.go.kr" in msg.lower()
    assert "활용신청" in msg


def test_getSpec_unknown_guard() -> None:
    from dartlab.core.providers.dataCredentials import CredentialError, getSpec

    with pytest.raises(CredentialError):
        getSpec("doesNotExist")


def test_setCredential_secret_roundtrip(cleanEnv) -> None:
    from dartlab.core.providers.dataCredentials import getKey, isConfigured, setCredential

    assert not isConfigured("dataGoKr")
    setCredential("dataGoKr", "storedSecret")
    # env 부재인데 secret 에서 해석돼야 한다
    assert getKey("dataGoKr") == "storedSecret"
    assert isConfigured("dataGoKr")


def test_setCredential_rejects_empty(cleanEnv) -> None:
    from dartlab.core.providers.dataCredentials import CredentialError, setCredential

    with pytest.raises(CredentialError):
        setCredential("dataGoKr", "   ")


def test_setCredential_reports_lifecycle_failure_after_secret_commit(cleanEnv, monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core import credentialLifecycle
    from dartlab.core.providers.dataCredentials import CredentialWriteError, getKey, setCredential

    def failLifecycle(*_args, **_kwargs) -> None:
        raise OSError("metadata unavailable")

    monkeypatch.setattr(credentialLifecycle, "recordIssuance", failLifecycle)

    with pytest.raises(CredentialWriteError, match="키 저장은 완료") as exc:
        setCredential("dart", "storedSecret")

    assert isinstance(exc.value.__cause__, OSError)
    assert exc.value.committed is True
    assert getKey("dart") == "storedSecret"


def test_setCredential_preserves_secret_store_commit_state(cleanEnv, monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core.providers.dataCredentials import CredentialWriteError, setCredential
    from dartlab.core.providers.secrets import SecretStoreLockError

    class CommittedFailureStore:
        def set(self, _name: str, _value: str) -> None:
            raise SecretStoreLockError("release failed", committed=True)

    monkeypatch.setattr(secretModule, "getSecretStore", lambda: CommittedFailureStore())

    with pytest.raises(CredentialWriteError, match="저장은 완료") as exc:
        setCredential("dataGoKr", "storedSecret")

    assert exc.value.committed is True
    assert isinstance(exc.value.__cause__, SecretStoreLockError)


def test_corrupt_secret_store_is_not_treated_as_missing(cleanEnv) -> None:
    from dartlab.core.providers.dataCredentials import CredentialError, getKey

    (cleanEnv / "secrets.json").write_text(json.dumps({"DATA_GO_KR_KEY": {"backend": "dpapi"}}), encoding="utf-8")

    with pytest.raises(CredentialError, match="SecretStore 조회 실패") as exc:
        getKey("dataGoKr")

    assert exc.value.__cause__ is not None


def test_credentialStatus_source_classification(cleanEnv, monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core.providers.dataCredentials import credentialStatus, setCredential

    monkeypatch.setenv("FRED_API_KEY", "x")
    setCredential("dataGoKr", "y")  # secret
    statuses = {s.id: s for s in credentialStatus()}
    assert statuses["fred"].source == "env"
    assert statuses["dataGoKr"].source == "secret"
    assert statuses["ecos"].source == "missing"
    assert statuses["fred"].configured and not statuses["ecos"].configured


def test_credentialStatus_reads_secret_store_once(cleanEnv, monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core.providers.dataCredentials import credentialStatus, setCredential

    setCredential("dataGoKr", "y")
    originalLoad = secretModule.SecretStore._load
    calls = 0

    def countedLoad(store):
        nonlocal calls
        calls += 1
        return originalLoad(store)

    monkeypatch.setattr(secretModule.SecretStore, "_load", countedLoad)

    credentialStatus()

    assert calls == 1


def test_credentialStatus_rejects_present_but_unusable_secret(cleanEnv, monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core.providers.dataCredentials import CredentialError, credentialStatus, setCredential

    setCredential("dataGoKr", "y")

    def failDecrypt(_raw: bytes) -> bytes:
        raise OSError("decrypt failed")

    monkeypatch.setattr(secretModule, "_unprotectWindows", failDecrypt)

    with pytest.raises(CredentialError, match="상태용 SecretStore 조회 실패") as exc:
        credentialStatus()

    assert exc.value.__cause__ is not None


def test_envTemplate_covers_all_providers(cleanEnv) -> None:
    from dartlab.core.providers.dataCredentials import allSpecs, envTemplate

    tmpl = envTemplate()
    for spec in allSpecs():
        assert f"{spec.envKey}=" in tmpl, spec.envKey
        assert spec.signupUrl in tmpl


def test_dataGoKr_single_key_three_sources() -> None:
    from dartlab.core.providers.dataCredentials import getSpec

    spec = getSpec("dataGoKr")
    assert spec.envKey == "DATA_GO_KR_KEY"
    assert set(spec.sources) == {"gov", "customs", "pension"}
