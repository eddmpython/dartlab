"""L0 user-facing message formatting and emission primitives.

Capabilities:
    - Formats catalog messages without a transport side effect.
    - Emits user-facing ``[dartlab]`` logs with native structured metadata.
    - Emits verbose-aware one-line progress logs.

Args:
    Public functions accept catalog keys, template fields, or progress text.

Returns:
    Formatted strings or ``None`` depending on the primitive.

Example:
    >>> from dartlab.core.messaging import emit, progress, format
    >>> msg = format("download:done_short", sizeStr="1MB")

Guide:
    Keep this facade limited to ``emit``, ``format``, and ``progress``. Domain guidance
    belongs to ``messagingHandlers`` and exception guidance to ``messagingErrors``.

SeeAlso:
    ``messagingCatalog`` and ``messagingFormatting``.

Requires:
    Core logger and message catalog modules.

AIContext:
    Stable lower-layer message boundary shared by core, providers, CLI, server, and notebooks.

LLM Specifications:
    AntiPatterns: Do not re-export Company, provider, share, or exception guidance.
    OutputSchema: Formatted text or ``None``.
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
from dartlab.core.messagingFormatting import formatMessage as _formatMessage

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


def emit(key: str, *, raiseAs: type[Exception] | None = None, **kwargs: Any) -> str:
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
    text = _formatMessage(key, **kwargs)

    if raiseAs is not None:
        raise raiseAs(text)

    if key in _STRUCTURED or any(key.startswith(prefix) for prefix in _ALWAYS_SHOW_PREFIXES):
        _logMessage(text, key=key, kind="structured")
    elif _ctx.verbose:
        _logMessage(text, key=key, kind="verbose")

    return text


def _logMessage(text: str, *, key: str, kind: str) -> None:
    """사용자 메시지 한 건에 native 구조화 메타데이터를 함께 기록한다.

    브라우저에는 소비할 메트릭 수집기가 없으므로 일반 로그만 남긴다. native에서는
    별도 이벤트 로그를 추가하지 않고 같은 레코드의 ``extra``에 관측 메타데이터를 넣는다.
    """
    extra = None
    if sys.platform != "emscripten":
        extra = {
            "event": "message_emit",
            "fields": {"key": key, "kind": kind},
        }
    _log.info("%s %s", _PREFIX, text, extra=extra)


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
    return _formatMessage(key, **kwargs)


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
    "emit",
    "format",
    "progress",
]
