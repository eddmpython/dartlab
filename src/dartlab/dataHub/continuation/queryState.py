"""Bounded binary codec for private continuation query state."""

from __future__ import annotations

import struct

from .contracts import ContinuationError, ContinuationQueryState

_MAGIC = b"DLQS1\x00"
_HEADER = struct.Struct(">6sII")


def encodeQueryState(state: ContinuationQueryState, *, maxBytes: int) -> bytes:
    """Private query와 cursor를 길이 고정 binary envelope로 인코딩한다.

    Capabilities:
        query와 cursor를 versioned, bounded binary state로 결박한다.

    Args:
        state: CAS에 넣을 query와 cursor state.
        maxBytes: encoded state의 최대 bytes.

    Returns:
        versioned binary state bytes.

    Raises:
        ContinuationError: state budget을 초과했을 때.
        TypeError: state 타입이 잘못됐을 때.

    Example:
        ``encodeQueryState(state, maxBytes=4096)``.

    Guide:
        반환 bytes는 private CAS에만 저장한다.

    When:
        최초 token을 issue하거나 다음 page cursor를 commit하기 직전에 호출한다.

    How:
        고정 header에 두 payload 길이를 기록하고 원문 bytes를 이어 붙인다.

    SeeAlso:
        ``decodeQueryState``.

    Requires:
        queryPayload는 canonical query bytes여야 한다.

    AIContext:
        SQLite에는 이 bytes가 아니라 SHA-256 digest만 들어간다.
    """
    if not isinstance(state, ContinuationQueryState):
        raise TypeError("state는 ContinuationQueryState여야 합니다")
    if type(maxBytes) is not int or maxBytes <= 0:
        raise ValueError("maxBytes는 양의 정수여야 합니다")
    querySize = len(state.queryPayload)
    cursorSize = len(state.cursorPayload)
    encodedSize = _HEADER.size + querySize + cursorSize
    if querySize > 0xFFFFFFFF or cursorSize > 0xFFFFFFFF or encodedSize > maxBytes:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return _HEADER.pack(_MAGIC, querySize, cursorSize) + state.queryPayload + state.cursorPayload


def decodeQueryState(payload: bytes, *, maxBytes: int) -> ContinuationQueryState:
    """CAS bytes를 길이와 version 검증 뒤 private state로 복원한다.

    Capabilities:
        state version, 길이 합계, byte bound를 검증해 query와 cursor를 복원한다.

    Args:
        payload: digest 검증을 끝낸 CAS bytes.
        maxBytes: 허용할 encoded state 최대 bytes.

    Returns:
        query와 cursor 원문을 가진 repr-safe state.

    Raises:
        ContinuationError: budget 또는 binary 구조가 잘못됐을 때.

    Example:
        ``decodeQueryState(encoded, maxBytes=4096)``.

    Guide:
        오류 메시지는 payload 일부도 포함하지 않는다.

    When:
        ``loadContext``가 digest 검증된 private CAS state를 읽었을 때 호출한다.

    How:
        header의 declared size와 실제 payload 길이가 정확히 같은지 확인한다.

    SeeAlso:
        ``encodeQueryState``.

    Requires:
        ArtifactStore의 SHA-256 검증 뒤 호출한다.

    AIContext:
        query와 cursor 원문은 반환 객체 repr에서도 숨겨진다.
    """
    if not isinstance(payload, bytes):
        raise TypeError("payload는 bytes여야 합니다")
    if type(maxBytes) is not int or maxBytes <= 0:
        raise ValueError("maxBytes는 양의 정수여야 합니다")
    if len(payload) > maxBytes:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    if len(payload) < _HEADER.size:
        raise ContinuationError("CONTINUATION_CORRUPT")
    try:
        magic, querySize, cursorSize = _HEADER.unpack_from(payload)
    except struct.error:
        raise ContinuationError("CONTINUATION_CORRUPT") from None
    if magic != _MAGIC or _HEADER.size + querySize + cursorSize != len(payload):
        raise ContinuationError("CONTINUATION_CORRUPT")
    queryStart = _HEADER.size
    cursorStart = queryStart + querySize
    return ContinuationQueryState(payload[queryStart:cursorStart], payload[cursorStart:])
