"""발송 인증 헤더 — Bearer + 결정적 nonce. HMAC 서명층 제거(품질점검: SIGN_KEY·SEND_TOKEN 동일 secrets → 독립 신뢰축 0).

nonce = sha1(topic:slug) 결정적 → 같은 발행 재push 는 허브에서 409(멱등). topic 다르면(blog vs card) 다른 nonce.
pushHub 요청 인증 헤더의 단일 구현이다.
"""

from __future__ import annotations

import hashlib
import json


def serialize_body(payload: dict) -> bytes:
    """전송할 바로 그 바이트(재직렬화 금지 — send 가 이 bytes 를 그대로 HTTP body 로)."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def nonce_for(topic: str, slug: str) -> str:
    """(topic, slug) 결정적 nonce. uuid 아님 — 같은 발행 멱등 보장."""
    return hashlib.sha1(f"{topic}:{slug}".encode("utf-8")).hexdigest()


def auth_headers(ts: int, topic: str, slug: str) -> dict:
    """Bearer 제외(send 가 부착)한 nonce/ts 헤더. raw body 는 serialize_body 로 별도."""
    return {"X-DL-Ts": str(ts), "X-DL-Nonce": nonce_for(topic, slug)}
