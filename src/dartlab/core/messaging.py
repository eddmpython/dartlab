"""Public messaging facade for DartLab.

Capabilities:
    - Emits user-facing ``[dartlab]`` messages through one stable public import path.
    - Re-exports guidance, formatting, sharing, and error helpers from focused modules.

Args:
    Public functions accept message keys, text, or domain context.

Returns:
    Formatted strings, guidance lists, or ``None`` depending on the helper.

Example:
    >>> from dartlab.core.messaging import emit, progress, format
    >>> msg = format("download:done_short", sizeStr="1MB")

Guide:
    Keep this module as the compatibility surface. Implementation belongs in
    ``messagingContext``, ``messagingFormatting``, ``messagingHandlers``,
    ``messagingShare``, and ``messagingErrors``.

SeeAlso:
    ``messagingCatalog`` and ``messagingFormatting``.

Requires:
    Core logger and message catalog modules.

AIContext:
    Stable import surface for CLI, providers, server, and notebooks while internal
    messaging responsibilities remain split and testable.

LLM Specifications:
    AntiPatterns: Do not add large handler branches or template catalogs here.
    OutputSchema: Public messaging helper outputs.
    Prerequisites: Message keys exist in the catalog for ``emit``/``format``.
    Freshness: Template freshness follows ``messagingCatalog``.
    Dataflow: caller -> public facade -> focused helper module -> text/log output.
    TargetMarkets: All DartLab user-facing environments.
"""

from __future__ import annotations

import sys
from typing import Any

from dartlab.core.logger import getLogger
from dartlab.core.messagingCatalog import STRUCTURED as _STRUCTURED
from dartlab.core.messagingContext import ctx as _ctx
from dartlab.core.messagingErrors import handleError, inferFeature
from dartlab.core.messagingFormatting import formatMessage, suggest
from dartlab.core.messagingHandlers import (
    apiKeyMissingHint,
    missingDataHint,
    nextSteps,
    onAnalysisRequested,
    onCompanyCreated,
    onKeyRequired,
    onScanRequested,
    promptKeyIfMissing,
)
from dartlab.core.messagingShare import (
    onCloudflaredMissing,
    onCloudflareLoginRequired,
    onShareSecurityWarning,
    onTunnelStartFailed,
)

_PREFIX = "[dartlab]"
_log = getLogger(__name__)
_ALWAYS_SHOW_PREFIXES = (
    "hint:",
    "error:",
    "collect:",
    "download:",
    "edgar:",
    "scan:prebuild",
    "stemindex:",
    "data:",
)


def emit(key: str, *, raiseAs: type | None = None, **kwargs: Any) -> str:
    """Format and emit a user-facing message.

    Parameters
    ----------
    key : str
        Message key registered in ``messagingCatalog``.
    raiseAs : type | None
        Exception class to raise with the formatted message instead of logging.
    **kwargs : Any
        Template variables such as ``stockCode``, ``label``, or ``sizeStr``.

    Returns
    -------
    str
        Formatted message text.

    Raises
    ------
    Exception
        Raises ``raiseAs(text)`` when ``raiseAs`` is supplied.

    Examples
    --------
    >>> emit("download:done_short", sizeStr="1MB")
    '✓ 다운로드 완료 (1MB)'

    Capabilities:
        Formats catalog messages and logs them according to structured/verbose rules.

    AIContext:
        User-facing runtime notifications should go through this function to preserve
        consistent wording and logger routing.

    Guide:
        Use ``format`` when the caller needs text only and no log side effect.

    When:
        Called by data loading, gathering, provider, CLI, and server code at user-visible events.

    How:
        Delegates formatting to ``messagingFormatting`` and logs via ``dartlab.core.messaging``.

    Requires:
        Message key in ``SIMPLE`` or ``STRUCTURED``.

    SeeAlso:
        :func:`format`, :func:`progress`.
    """
    text = formatMessage(key, **kwargs)

    if raiseAs is not None:
        raise raiseAs(text)

    if key in _STRUCTURED or any(key.startswith(prefix) for prefix in _ALWAYS_SHOW_PREFIXES):
        _log.info("%s %s", _PREFIX, text)
        _emitStructured("message_emit", key=key, kind="structured")
    elif _ctx.verbose:
        _log.info("%s %s", _PREFIX, text)
        _emitStructured("message_emit", key=key, kind="verbose")

    return text


def _emitStructured(event: str, **fields: object) -> None:
    """T1-1 structured log 발급. emit/format 동행.

    브라우저(pyodide)에서는 내보내지 않는다. 이벤트 이름을 메시지 본문으로 찍는 구조라
    stderr 를 그대로 셀 출력에 담는 노트북에서는 ``message_emit`` 이라는 날문자열이
    사용자에게 보인다. 그 이벤트를 소비할 메트릭 수집기도 브라우저에는 없다.
    """
    if sys.platform == "emscripten":
        return
    try:
        from dartlab.core.logger import logEvent

        logEvent("info", event, **fields)
    except ImportError:
        pass


def format(key: str, **kwargs: Any) -> str:
    """Format a message without emitting it.

    Args:
        key: Message key registered in ``messagingCatalog``.
        **kwargs: Template variables.

    Returns:
        Formatted message text.

    Raises:
        ``KeyError`` when the key or template variable is missing.
    Requires:
        key가 ``messagingCatalog``의 simple 또는 structured catalog에 등록되어 있어야 한다.

    Example:
        >>> format("download:done_short", sizeStr="1MB")
        '✓ 다운로드 완료 (1MB)'
    """
    return formatMessage(key, **kwargs)


def progress(text: str) -> None:
    """Emit a verbose-aware one-line progress message.

    Args:
        text: Progress text to log.

    Returns:
        ``None``.

    Raises:
        Logger backend errors, if configured logger raises.
    Requires:
        dartlab logger가 초기화 가능해야 한다. verbose가 꺼져 있으면 로그를 남기지 않는다.

    Example:
        >>> progress("KRX KIND 상장법인 목록 다운로드 중...")
    """
    if _ctx.verbose:
        _log.info("%s %s", _PREFIX, text)


__all__ = [
    "_ctx",
    "apiKeyMissingHint",
    "emit",
    "format",
    "handleError",
    "inferFeature",
    "missingDataHint",
    "nextSteps",
    "onAnalysisRequested",
    "onCloudflareLoginRequired",
    "onCloudflaredMissing",
    "onCompanyCreated",
    "onKeyRequired",
    "onScanRequested",
    "onShareSecurityWarning",
    "onTunnelStartFailed",
    "progress",
    "promptKeyIfMissing",
    "suggest",
]
