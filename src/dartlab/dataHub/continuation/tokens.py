"""Opaque continuation bearer-token primitives."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re

from .contracts import ContinuationError

_TOKEN_RE = re.compile(r"^dltc1\.([A-Za-z0-9_-]{43})$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def encodeToken(secret: bytes) -> str:
    """32-byte secret을 versioned opaque token으로 인코딩한다.

    Args:
        secret: cryptographically random 32-byte secret.

    Returns:
        ``dltc1.*`` opaque bearer token.

    Raises:
        ValueError: secret 길이 또는 타입이 잘못됐을 때.

    Example:
        ``token = encodeToken(bytes(32))``.

    Requires:
        실제 issuance는 ``secrets.token_bytes`` 결과를 사용한다.
    """
    if not isinstance(secret, bytes) or len(secret) != 32:
        raise ValueError("continuation secret은 32 bytes여야 합니다")
    return "dltc1." + base64.urlsafe_b64encode(secret).rstrip(b"=").decode("ascii")


def decodeToken(token: str) -> bytes:
    """token 형식과 길이를 검증하고 secret을 복원한다.

    Capabilities:
        version, URL-safe alphabet, decoded length를 fail closed 검증한다.

    Args:
        token: opaque bearer token.

    Returns:
        검증된 32-byte secret.

    Raises:
        ContinuationError: token 형식이나 길이가 잘못됐을 때.

    Example:
        ``secret = decodeToken(token)``.

    Guide:
        반환 secret은 child token derivation 외에는 사용하지 않는다.

    When:
        token을 digest하거나 deterministic child를 만들기 전에 호출한다.

    How:
        strict regex 뒤 URL-safe base64를 복호화하고 32-byte인지 확인한다.

    SeeAlso:
        ``encodeToken``, ``tokenDigest``.

    Requires:
        token 원문을 log, repr, error에 넣지 않는다.

    AIContext:
        고정 ContinuationError만 발생해 malformed bearer가 gap으로 새지 않는다.
    """
    if not isinstance(token, str):
        raise ContinuationError("CONTINUATION_INVALID")
    match = _TOKEN_RE.fullmatch(token)
    if match is None:
        raise ContinuationError("CONTINUATION_INVALID")
    try:
        secret = base64.urlsafe_b64decode(match.group(1) + "=")
    except Exception:
        raise ContinuationError("CONTINUATION_INVALID") from None
    if len(secret) != 32:
        raise ContinuationError("CONTINUATION_INVALID")
    return secret


def tokenDigest(token: str) -> str:
    """형식 검증된 bearer token의 audit-safe digest를 만든다.

    Args:
        token: opaque bearer token.

    Returns:
        complete token string의 SHA-256 digest.

    Raises:
        ContinuationError: token이 유효하지 않을 때.

    Example:
        ``digest = tokenDigest(token)``.

    Requires:
        ledger와 lineage에는 반환 digest만 기록한다.
    """
    decodeToken(token)
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def childToken(parentToken: str, pageDigest: str, nextStateDigest: str) -> str:
    """parent secret과 immutable page/state에서 결정적 child token을 만든다.

    Capabilities:
        replay마다 같은 child bearer를 만들되 plaintext 저장을 없앤다.

    Args:
        parentToken: 현재 page bearer token.
        pageDigest: committed page SHA-256.
        nextStateDigest: next private state SHA-256.

    Returns:
        HMAC-SHA-256 기반 opaque child token.

    Raises:
        ContinuationError: token 또는 digest 형식이 잘못됐을 때.

    Example:
        ``nextToken = childToken(token, pageDigest, stateDigest)``.

    Guide:
        child 원문은 caller에게만 반환하고 ledger에는 digest만 쓴다.

    When:
        page에 nextState가 있어 다음 continuation row를 만들 때 호출한다.

    How:
        domain-separated page와 state material을 parent secret으로 HMAC한다.

    SeeAlso:
        ``tokenDigest``.

    Requires:
        pageDigest와 nextStateDigest가 lowercase SHA-256이어야 한다.

    AIContext:
        idempotent replay와 token plaintext 비저장을 동시에 만족한다.
    """
    parentSecret = decodeToken(parentToken)
    if _DIGEST_RE.fullmatch(pageDigest) is None or _DIGEST_RE.fullmatch(nextStateDigest) is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    material = b"dartlab-continuation-child-v1\0" + bytes.fromhex(pageDigest) + bytes.fromhex(nextStateDigest)
    return encodeToken(hmac.new(parentSecret, material, hashlib.sha256).digest())
