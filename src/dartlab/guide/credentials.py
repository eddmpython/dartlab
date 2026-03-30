"""환경/토큰/키 통합 조회 — CredentialManager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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


class CredentialManager:
    """환경/토큰/키 통합 관리자.

    기존 모듈을 래핑하여 단일 진입점 제공.
    쓰기 작업은 기존 모듈에 위임.
    """

    def snapshot(self) -> EnvironmentSnapshot:
        """현재 전체 환경 상태를 스냅샷으로 반환."""
        from dartlab import config

        try:
            from dartlab import __version__
        except ImportError:
            __version__ = "unknown"

        dartStatus = self._checkDartKey()
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
        """특정 자격 증명 상태 조회."""
        if name == "dart_api_key":
            return self._checkDartKey()
        aiStatuses = self._checkAiProviders()
        return aiStatuses.get(name, CredentialStatus(
            name=name, configured=False, source="none"
        ))

    def saveKey(self, name: str, value: str) -> None:
        """키 저장 — 적절한 백엔드에 위임."""
        if name == "dart_api_key":
            from dartlab.providers.dart.openapi.dartKey import saveDartKeyToDotenv
            saveDartKeyToDotenv(value)
            return
        from dartlab.guide.profile import get_profile_manager
        mgr = get_profile_manager()
        provider = name.replace("_api_key", "")
        mgr.save_api_key(provider, value)

    def _checkDartKey(self) -> CredentialStatus:
        try:
            from dartlab.providers.dart.openapi.dartKey import getDartKeyStatus
            status = getDartKeyStatus()
            masked = None
            if status.configured:
                try:
                    from dartlab.providers.dart.openapi.dartKey import resolveDartKeys
                    keys = resolveDartKeys()
                    if keys:
                        k = keys[0]
                        masked = k[:4] + "..." + k[-4:] if len(k) > 8 else "***"
                except (ImportError, TypeError):
                    pass
            return CredentialStatus(
                name="dart_api_key",
                configured=status.configured,
                source=status.source,
                maskedValue=masked,
            )
        except ImportError:
            return CredentialStatus(name="dart_api_key", configured=False, source="none")

    def _checkAiProviders(self) -> dict[str, CredentialStatus]:
        results: dict[str, CredentialStatus] = {}
        try:
            import os

            from dartlab.guide.providers import _PROVIDERS, api_key_secret_name
            from dartlab.guide.secrets import get_secret_store

            store = get_secret_store()
            for pid, spec in _PROVIDERS.items():
                if spec.auth_kind == "api_key" and spec.env_key:
                    envVal = os.environ.get(spec.env_key)
                    secretVal = store.get(api_key_secret_name(pid))
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
                    from dartlab.guide.providers import oauth_secret_name
                    configured = store.has(oauth_secret_name(pid))
                    results[pid] = CredentialStatus(
                        name=f"{pid}_oauth",
                        configured=configured,
                        source="oauth" if configured else "none",
                    )
        except ImportError:
            pass
        return results

    def _getDefaultProvider(self) -> str | None:
        try:
            from dartlab.guide.profile import get_profile_manager
            mgr = get_profile_manager()
            profile = mgr.load()
            return profile.default_provider
        except ImportError:
            return None
