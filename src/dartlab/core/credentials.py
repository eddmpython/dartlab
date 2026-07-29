"""환경/토큰/키 통합 조회 — CredentialManager.

Protocol + Registry 패턴 (정공법 B — DIP). core 는 ai/providers 직접 import 0:
- CredentialProvider Protocol 정의
- registerCredentialProvider() / listCredentialProviders() registry
- providers/dart, ai/providers 등 외부 모듈이 import 시점에 register
- CredentialManager 는 registry 만 iterate
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


@dataclass(frozen=True)
class CredentialStatus:
    """단일 자격 증명 상태."""

    name: str
    configured: bool
    source: str
    maskedValue: str | None = None


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """전체 환경 스냅샷."""

    dataDir: str
    verbose: bool
    dartKey: CredentialStatus
    aiProviders: dict[str, CredentialStatus]
    aiDefaultProvider: str | None
    version: str


# ── Protocol DIP ──────────────────────────────────────────


@runtime_checkable
class CredentialProvider(Protocol):
    """단일 자격 증명 제공자 — Protocol DIP.

    구현 위치: gather/dart/keys.py 의 DartKeyProvider 등.
    각 provider 는 import 시점에 registerCredentialProvider() 로 등록.
    """

    name: str  # 자격 증명 식별자 (예: "dart_api_key")

    def check(self) -> CredentialStatus:
        """현재 자격 증명 상태 조회.

        Requires:
            구현 provider가 환경변수, secret store, OAuth token 등 자신의 저장소를 확인할 수 있어야 한다.
        Raises:
            구현체가 정의한 저장소 접근 예외를 그대로 전달할 수 있다.
        Returns:
            CredentialStatus: configured/source/maskedValue를 담은 상태 객체.
        Example:
            >>> provider.check().configured  # doctest: +SKIP
            True
        """
        ...

    def save(self, value: str) -> None:
        """자격 증명 저장.

        Requires:
            구현 provider가 value를 저장할 수 있는 안전한 저장소를 가져야 한다.
        Raises:
            구현체가 정의한 저장 실패 예외를 그대로 전달할 수 있다.
        Args:
            value: 저장할 API key, token, 또는 credential 문자열.
        Returns:
            None.
        Example:
            >>> provider.save("secret")  # doctest: +SKIP
        """
        ...


_PROVIDERS: dict[str, CredentialProvider] = {}


def _discoverProviders() -> None:
    """root composition이 등록한 CredentialProvider bootstrap을 실행한다."""
    bootstrap(__name__)


def registerCredentialProvider(provider: CredentialProvider) -> None:
    """CredentialProvider 등록 — providers 가 import 시점에 호출.

    같은 이름 재등록 시 덮어쓰기 (테스트 용이).

    Requires:
        provider.name이 registry key로 사용할 수 있는 문자열이어야 한다.
    Raises:
        AttributeError: provider가 name 속성을 제공하지 않을 때.
    Args:
        provider: check/save를 구현한 CredentialProvider.
    Returns:
        None.
    Example:
        >>> class P:
        ...     name = "x"
        ...     def check(self): ...
        ...     def save(self, value): ...
        >>> registerCredentialProvider(P())
    """
    _PROVIDERS[provider.name] = provider


def listCredentialProviders() -> dict[str, CredentialProvider]:
    """등록된 모든 CredentialProvider 반환 (dict 사본). auto-discovery 트리거.

    Requires:
        root composition이 credential provider bootstrap을 등록해야 한다.
    Raises:
        provider bootstrap 오류를 원인 그대로 전파한다.
    Returns:
        provider name을 key로 하는 registry 사본.
    Example:
        >>> isinstance(listCredentialProviders(), dict)
        True
    """
    _discoverProviders()
    return dict(_PROVIDERS)


def getCredentialProvider(name: str) -> CredentialProvider | None:
    """이름으로 단일 provider 조회. 미등록이면 None. auto-discovery 트리거.

    Requires:
        name은 registry에 등록된 provider name과 같은 문자열이어야 hit가 가능하다.
    Raises:
        provider bootstrap 오류를 원인 그대로 전파한다.
    Args:
        name: 조회할 credential provider 이름.
    Returns:
        CredentialProvider 또는 미등록 시 None.
    Example:
        >>> getCredentialProvider("__missing__") is None
        True
    """
    _discoverProviders()
    return _PROVIDERS.get(name)


# ── Manager ───────────────────────────────────────────────


class CredentialManager:
    """환경/토큰/키 통합 관리자 — Protocol Registry 기반.

    core 는 providers 직접 import 0. providers 가 module load 시점에
    registerCredentialProvider() 호출.
    """

    def snapshot(self) -> EnvironmentSnapshot:
        """현재 전체 환경 상태를 스냅샷으로 반환.

        Capabilities:
            dataDir, verbose, DART key, AI provider credential, 기본 AI provider, 버전을 한
            객체로 수집한다.
        AIContext:
            setup 진단과 CLI 환경 점검이 사용자에게 현재 인증 상태를 설명할 때 쓰는 L0
            snapshot boundary다.
        Guide:
            값을 변경하지 않는다. 저장은 saveKey, provider별 setup 함수가 담당한다.
        When:
            ``dartlab.setup()`` 또는 환경 진단 화면에서 전체 credential 상태가 필요할 때.
        How:
            package version과 config를 읽고, registry provider 및 core provider secret store를 조회한다.
        Requires:
            ``dartlab.config``와 importlib.metadata가 사용 가능해야 한다.
        Raises:
            ``dartlab.config`` import/runtime 오류는 그대로 전달될 수 있다.
        Returns:
            EnvironmentSnapshot: 현재 환경과 credential 상태.
        Example:
            >>> snap = CredentialManager().snapshot()
            >>> isinstance(snap.version, str)
            True
        SeeAlso:
            getCredential: 단일 credential 상태 조회.
            saveKey: credential 저장.
        """
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as _pkgVersion

        from dartlab import config

        try:
            __version__ = _pkgVersion("dartlab")
        except PackageNotFoundError:
            __version__ = "unknown"

        dartStatus = self.getCredential("dart_api_key")
        aiStatuses = self._checkAiProviders()
        defaultProvider = self._getDefaultProvider()

        return EnvironmentSnapshot(
            dataDir=config.dataDir,
            verbose=config.verbose,
            dartKey=dartStatus,
            aiProviders=aiStatuses,
            aiDefaultProvider=defaultProvider,
            version=__version__,
        )

    def getCredential(self, name: str) -> CredentialStatus:
        """특정 자격 증명 상태 조회 — registry 우선, fallback ai providers.

        Capabilities:
            등록된 CredentialProvider를 먼저 사용하고, AI provider key/oauth 이름은 core
            provider registry fallback으로 조회한다.
        AIContext:
            setup, messaging, provider bootstrap이 credential 존재 여부를 같은 규칙으로
            판단하게 한다.
        Guide:
            provider가 등록되어 있으면 provider.check가 SSOT다. 미등록 AI provider는
            ``<provider>_api_key`` 또는 ``<provider>_oauth`` 이름 규칙을 따른다.
        When:
            특정 key/token의 configured/source 상태만 필요할 때.
        How:
            getCredentialProvider(name) → provider.check, 없으면 _checkAiProviders fallback.
        Requires:
            name은 credential name 문자열이어야 한다.
        Raises:
            등록 provider.check가 발생시키는 예외를 그대로 전달할 수 있다.
        Args:
            name: 조회할 credential 이름.
        Returns:
            CredentialStatus. 미등록이면 configured=False/source="none".
        Example:
            >>> CredentialManager().getCredential("__missing__").configured
            False
        SeeAlso:
            registerCredentialProvider: provider 등록.
            snapshot: 전체 상태 조회.
        """
        provider = getCredentialProvider(name)
        if provider is not None:
            return provider.check()
        # AI provider 는 별도 로직 (auth_kind=api_key|oauth) 유지
        if name.endswith("_api_key") or name.endswith("_oauth"):
            aiStatuses = self._checkAiProviders()
            providerId = name.removesuffix("_api_key").removesuffix("_oauth")
            return aiStatuses.get(providerId, CredentialStatus(name=name, configured=False, source="none"))
        return CredentialStatus(name=name, configured=False, source="none")

    def saveKey(self, name: str, value: str) -> None:
        """키 저장 — registry 우선, AI provider 는 SecretStore 직접.

        Capabilities:
            등록 provider가 있으면 provider.save에 위임하고, 없으면 AI provider API key를
            core SecretStore에 저장한다.
        AIContext:
            setup flow가 provider별 저장 구현을 몰라도 동일한 credential 저장 entry를
            사용하게 한다.
        Guide:
            OAuth token 저장에는 provider별 setup을 우선 사용한다. 이 함수의 fallback은
            ``*_api_key`` 이름에 맞춘 API key 저장용이다.
        When:
            사용자가 setup에서 API key를 입력했거나 테스트가 credential provider 저장을 검증할 때.
        How:
            registry provider.save → 없으면 provider name 정규화 → apiKeySecretName → SecretStore.set.
        Requires:
            name과 value는 문자열이어야 한다. fallback 경로는 core.providers secret store가 필요하다.
        Raises:
            provider.save 또는 SecretStore.set에서 발생한 예외를 그대로 전달할 수 있다.
        Args:
            name: credential 이름. 예: ``"dart_api_key"`` 또는 ``"openai_api_key"``.
            value: 저장할 secret 문자열.
        Returns:
            None.
        Example:
            >>> CredentialManager().saveKey("openai_api_key", "sk-test")  # doctest: +SKIP
        SeeAlso:
            getCredential: 저장 후 상태 확인.
            dartlab.core.providers.getSecretStore: fallback 저장소.
        """
        provider = getCredentialProvider(name)
        if provider is not None:
            provider.save(value)
            return
        from dartlab.core.providers import apiKeySecretName, getSecretStore, normalizeProvider

        rawProvider = name.replace("_api_key", "")
        normalized = normalizeProvider(rawProvider) or rawProvider
        getSecretStore().set(apiKeySecretName(normalized), value)

    def _checkAiProviders(self) -> dict[str, CredentialStatus]:
        """AI provider 자격 (api_key + oauth) 일괄 검사 — core/providers registry."""
        results: dict[str, CredentialStatus] = {}
        from dartlab.core.providers import (
            _PROVIDERS as _AI_PROVIDERS,
        )
        from dartlab.core.providers import (
            apiKeySecretName,
            getSecretStore,
            oauthSecretName,
        )

        store = getSecretStore()
        secretNames = store.keys()
        for pid, spec in _AI_PROVIDERS.items():
            if spec.auth_kind == "api_key" and spec.env_key:
                envVal = os.environ.get(spec.env_key)
                secretName = apiKeySecretName(pid)
                secretVal = store.get(secretName) if not envVal and secretName in secretNames else None
                configured = bool(envVal or secretVal)
                source = "env" if envVal else ("secret_store" if secretVal else "none")
                val = envVal or secretVal
                masked = (val[:4] + "..." + val[-4:]) if val and len(val) > 8 else None
                results[pid] = CredentialStatus(
                    name=f"{pid}_api_key",
                    configured=configured,
                    source=source,
                    maskedValue=masked if configured else None,
                )
            elif spec.auth_kind == "oauth":
                configured = oauthSecretName(pid) in secretNames
                results[pid] = CredentialStatus(
                    name=f"{pid}_oauth",
                    configured=configured,
                    source="oauth" if configured else "none",
                )
        return results

    def _getDefaultProvider(self) -> str | None:
        """ai_profile.json 의 defaultProvider 만 직접 조회 (core/providers thin 헬퍼)."""
        from dartlab.core.providers import getDefaultProvider

        return getDefaultProvider()
