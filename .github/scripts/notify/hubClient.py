"""허브 /send POST + 응답 분류 — 발행 러너(send.py)·왓처 러너(watch.py) 공유.

발송 1건 = topic 브로드캐스트 또는 endpoints 타겟. (topic,slug) 결정적 nonce 라 같은 매치 재발송은 409(멱등).
분류: 401/5xx/네트워크 = problem(헬스게이트 RED), 409 = dup(이미 발송, 정상), 2xx = ok.
현재 운영 계약은 Skill OS ``operation.notifyPipeline``이다.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from authHeaders import auth_headers, serialize_body


def post_to_hub(hub: str, token: str, topic: str, slug: str, notification: dict, ts: int) -> tuple[int, dict | None]:
    """topic 브로드캐스트 1 POST. (status, body) 반환. 네트워크 실패는 status=0."""
    raw = serialize_body({"topic": topic, "notification": notification})
    headers = {
        **auth_headers(ts, topic, slug),
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(hub + "/send", data=raw, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            body = None
        return e.code, body
    except Exception:
        return 0, None


def post_active(hub: str, token: str, topic: str, matches: list[dict], ts: int) -> tuple[int, dict | None]:
    """stateful 토픽(threshold_cross) 활성 매치 set 1 POST. 허브가 직전 set 과 diff 해 신규 진입만 발화.

    per-match /send(영구 nonce) 대신 set-diff 커서 경로(재크로싱, 하락 후 재상승 발화용). (status, body) 반환.
    """
    raw = serialize_body({"topic": topic, "matches": matches})
    headers = {
        "X-DL-Ts": str(ts),
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(hub + "/active", data=raw, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            body = None
        return e.code, body
    except Exception:
        return 0, None


def classify(status: int) -> str:
    """발송 응답 → 'ok' | 'dup'(409 멱등) | 'problem'(401/5xx/네트워크 = RED)."""
    if status == 0 or status == 401 or status >= 500:
        return "problem"
    if status == 409:
        return "dup"
    return "ok"
