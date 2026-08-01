"""DataHub 원격 control plane의 단일 payload 예산 정책."""

from __future__ import annotations

from urllib.parse import urlsplit

MAX_REQUEST_BYTES = 1024 * 1024
MAX_RESULT_WIRE_BYTES = 16 * 1024 * 1024
RESULT_ENVELOPE_RESERVE_BYTES = 64 * 1024
MAX_RESULT_PAYLOAD_BYTES = (MAX_RESULT_WIRE_BYTES * 3) // 4 - RESULT_ENVELOPE_RESERVE_BYTES


def validateRemoteBaseUrl(baseUrl: str) -> str:
    """Bearer token을 평문 외부 host로 보내지 않도록 base URL을 검증한다."""

    if not isinstance(baseUrl, str):
        raise ValueError("baseUrl은 URL string이어야 합니다")
    parsed = urlsplit(baseUrl)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("baseUrl은 credential 없는 http 또는 https URL이어야 합니다")
    loopback = parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1", "testserver"}
    if parsed.scheme == "http" and not loopback:
        raise ValueError("외부 DataHub baseUrl은 https여야 합니다")
    return baseUrl.rstrip("/")


__all__ = [
    "MAX_REQUEST_BYTES",
    "MAX_RESULT_PAYLOAD_BYTES",
    "MAX_RESULT_WIRE_BYTES",
    "RESULT_ENVELOPE_RESERVE_BYTES",
    "validateRemoteBaseUrl",
]
