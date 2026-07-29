"""[shim] settings/secrets → core/providers/secrets 이전.

본체: src/dartlab/core/providers/secrets.py
0.10 부터 snake alias 제거. 0.11 release 시 본 shim 제거.
"""

from dartlab.core.providers.secrets import (  # noqa: F401
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

__all__ = [
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
    "getSecretStore",
]
