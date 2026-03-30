"""호환 shim — 새 코드는 dartlab.guide.secrets를 사용하세요."""

from dartlab.guide.secrets import (  # noqa: F401
    SecretEntry,
    SecretStore,
    SecretStoreError,
    get_secret_store,
)
