"""호환 shim — 새 코드는 dartlab.guide.providers를 사용하세요."""

from dartlab.guide.providers import *  # noqa: F401,F403
from dartlab.guide.providers import (  # noqa: F401
    _PROVIDERS,
    ProviderSpec,
    api_key_secret_name,
    build_provider_catalog,
    cli_provider_choices,
    get_provider_spec,
    normalize_provider,
    oauth_secret_name,
    provider_choices,
    public_provider_ids,
)
