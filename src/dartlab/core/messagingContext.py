"""Runtime context for user-facing messaging.

Capabilities:
    - Caches expensive messaging context checks such as DART key availability and verbose mode.

Args:
    Context properties take no arguments.

Returns:
    Boolean runtime flags used by formatting and emission helpers.

Example:
    >>> from dartlab.core.messagingContext import ctx
    >>> isinstance(ctx.verbose, bool)
    True

Guide:
    Keep this module free of message templates and public user guidance copy.

SeeAlso:
    ``dartlab.core.messaging`` and ``dartlab.core.messagingFormatting``.

Requires:
    ``dartlab.config`` and optional credential providers.

AIContext:
    Separates environment-sensitive checks from copy formatting so messaging remains testable.

LLM Specifications:
    AntiPatterns: Do not import providers directly; use core credential/provider registries.
    OutputSchema: Boolean context properties.
    Prerequisites: DartLab configuration importable.
    Freshness: Values are cached until ``reset`` is called.
    Dataflow: messaging caller -> context property -> config/credential registry.
    TargetMarkets: All DartLab runtimes.
"""

from __future__ import annotations


class Context:
    """Cached messaging runtime context.

    Args:
        None.

    Returns:
        Instance exposing ``hasDartKey`` and ``verbose`` properties.

    Raises:
        Credential 또는 config 내부 오류를 원인 그대로 전파한다.

    Example:
        >>> c = Context()
        >>> c.reset()
    """

    def __init__(self) -> None:
        self._dart_key: bool | None = None
        self._verbose: bool | None = None

    @property
    def hasDartKey(self) -> bool:
        """Return whether a DART API key is configured.

            Args:
                None.

            Returns:
                ``True`` when the credential registry reports a configured DART key.

        Raises:
            Credential registry import 또는 provider check 오류를 원인 그대로 전파한다.
        Requires:
            선택적으로 ``dartlab.core.credentials``가 import 가능하면 credential registry를 확인한다.

        Example:
            >>> isinstance(Context().hasDartKey, bool)
                True
        """
        if self._dart_key is None:
            from dartlab.core.credentials import getCredentialProvider

            provider = getCredentialProvider("dart_api_key")
            self._dart_key = bool(provider and provider.check().configured)
        return self._dart_key

    @property
    def verbose(self) -> bool:
        """Return current verbose mode.

            Args:
                None.

            Returns:
                ``dartlab.config.verbose`` cached as a boolean.

        Raises:
            Propagates unexpected config import/runtime errors.
        Requires:
            ``dartlab.config``가 import 가능해야 한다.

        Example:
            >>> isinstance(Context().verbose, bool)
                True
        """
        if self._verbose is None:
            from dartlab import config

            self._verbose = config.verbose
        return self._verbose

    def reset(self) -> None:
        """Clear cached context values.

        Args:
            None.

        Returns:
            ``None``.

        Raises:
            None.

        Example:
            >>> c = Context()
            >>> c.reset()
        """
        self._dart_key = None
        self._verbose = None


ctx = Context()

__all__ = ["Context", "ctx"]
