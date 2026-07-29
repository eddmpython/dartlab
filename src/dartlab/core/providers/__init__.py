"""AI provider 카탈로그 + secret store SSOT (core 강등).

이전: src/dartlab/ai/settings/{provider_catalog, secrets}.py
사유: provider 카탈로그·secret 저장은 dartlab.core 의 cross-cutting primitive
(외부 L2 의존 0, 도메인 지식 0, ai/cli/server 모두 소비). 단방향 import 정책
하에 ai 가 core import 하는 게 정공법.

ai/settings/{provider_catalog, secrets}.py 는 0.10 까지 re-export shim 유지,
0.11 에서 제거 예정 (CHANGELOG 명시).
"""

from dartlab.core.providers.registry import (
    _PROVIDERS,
    AI_ROLES,
    ProviderSpec,
    apiKeySecretName,
    buildProviderCatalog,
    cliProviderChoices,
    getDefaultProvider,
    getProviderSpec,
    normalizeProvider,
    oauthSecretName,
    providerChoices,
    publicProviderIds,
    wiredProviderIds,
)
from dartlab.core.providers.secrets import (
    SecretEntry,
    SecretStore,
    SecretStoreBackendError,
    SecretStoreCompositeError,
    SecretStoreCorruptError,
    SecretStoreDecryptError,
    SecretStoreError,
    SecretStoreLockError,
    SecretStoreReadError,
    SecretStoreWriteError,
    getSecretStore,
)
from dartlab.core.providers.setupGuide import (
    DISPLAY_ORDER,
    noProviderMessage,
    providerGuide,
    resolveAlias,
)

__all__ = [
    "AI_ROLES",
    "DISPLAY_ORDER",
    "ProviderSpec",
    "SecretEntry",
    "SecretStoreBackendError",
    "SecretStoreCompositeError",
    "SecretStoreCorruptError",
    "SecretStoreDecryptError",
    "SecretStore",
    "SecretStoreError",
    "SecretStoreLockError",
    "SecretStoreReadError",
    "SecretStoreWriteError",
    "_PROVIDERS",
    "apiKeySecretName",
    "buildProviderCatalog",
    "cliProviderChoices",
    "getDefaultProvider",
    "getProviderSpec",
    "getSecretStore",
    "noProviderMessage",
    "normalizeProvider",
    "oauthSecretName",
    "providerChoices",
    "providerGuide",
    "publicProviderIds",
    "resolveAlias",
    "wiredProviderIds",
]
