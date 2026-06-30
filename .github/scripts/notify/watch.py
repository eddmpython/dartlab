"""공개 왓처 토픽 러너 (P2) — scan SSOT 직독 → 매치 → 허브 /send 브로드캐스트.

토픽 1개 = 함수 1개(레지스트리·synth 모듈 0 — YAGNI, P3 졸업 시 발견적 추출). 베이크 0(scan 라이브 직독).
중복 억제 = 허브 sentNonce 가 곧 last-seen 매치 id set: 매치별 nonce = sha1(topic:slug) → 이미 보낸 매치는
허브에서 409(멱등 드롭), 새 매치만 실제 발송. 발행 러너(send.py)와 별개 워크플로(watch.yml cron).

  - newIpo   = scan('ipo') 신규상장(new_listing). slug = rcept(접수번호) — 발행사별 1회.
  - newOrders = scan('orders') book-to-bill >= 1(threshold_cross). slug = stockCode — 회사별 1회 크로싱.

설계: mainPlan/watcher-notify-platform/01-architecture.md §2·§5 · 04 §1 P2.
실행: uv run python -X utf8 .github/scripts/notify/watch.py [--topics newIpo,newOrders] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from hubClient import classify, post_to_hub
from sanitize import sanitize

_TERMINAL = "/terminal"  # 클릭 자기 라우트(피싱 차단). Phase D 에서 종목 deep-link 격상 가능.


def _won(v: object) -> str | None:
    try:
        return f"{int(float(v)):,}원"
    except (TypeError, ValueError):
        return None


def eval_new_ipo(df=None) -> list[dict]:
    """scan('ipo') → 신규상장 알림 매치. df 주입 시 그 df 사용(테스트). 항등식 미검증분도 알림(공모 사실은 사실)."""
    if df is None:
        import dartlab

        df = dartlab.scan("ipo")
    items: list[dict] = []
    for r in df.iter_rows(named=True):
        rcept = r.get("rcept")
        if not rcept:
            continue
        name = r.get("corpName") or "신규상장"
        low, high = _won(r.get("priceBandLow")), _won(r.get("priceBandHigh"))
        parts: list[str] = []
        if low and high:
            parts.append(f"공모가 {low.replace('원', '')}~{high}")
        if r.get("subscription"):
            parts.append(f"청약 {r['subscription']}")
        if r.get("appliedPer") is not None:
            parts.append(f"적용PER {r['appliedPer']}")
        spac = " (스팩)" if r.get("isSpac") else ""
        items.append(
            {
                "topic": "newIpo",
                "slug": str(rcept),
                "notification": {
                    "title": sanitize(f"[신규상장] {name}{spac}", 80),
                    "body": sanitize(" · ".join(parts) or "증권신고서 접수", 120),
                    "url": _TERMINAL,
                    "tag": f"ipo:{rcept}",
                },
            }
        )
    return items


def eval_new_orders(df=None, min_book_to_bill: float = 1.0) -> list[dict]:
    """scan('orders') → book-to-bill>=1 threshold_cross 매치. micro-cap/잡음 가드(매출·계약건수)."""
    if df is None:
        import dartlab

        df = dartlab.scan("orders")
    items: list[dict] = []
    for r in df.iter_rows(named=True):
        b2b = r.get("bookToBill")
        code = r.get("stockCode")
        if b2b is None or b2b < min_book_to_bill or not code:
            continue
        if not r.get("recentRevenue") or (r.get("nContract") or 0) < 1:
            continue  # micro-cap/잡음 가드(docstring 경고)
        parts = [f"book-to-bill {b2b:.2f}"]
        if r.get("grade"):
            parts.append(f"등급 {r['grade']}")
        if r.get("topCounterparty"):
            parts.append(f"주거래 {r['topCounterparty']}")
        items.append(
            {
                "topic": "newOrders",
                "slug": str(code),
                "notification": {
                    "title": sanitize(f"[신규수주] 종목 {code} 백로그 확대", 80),
                    "body": sanitize(" · ".join(parts), 120),
                    "url": _TERMINAL,
                    "tag": f"orders:{code}",
                },
            }
        )
    return items


_EVALUATORS = {"newIpo": eval_new_ipo, "newOrders": eval_new_orders}


def main() -> int:
    ap = argparse.ArgumentParser(description="공개 왓처 토픽 러너")
    ap.add_argument("--topics", default="newIpo,newOrders", help="콤마구분 토픽(기본 전체)")
    ap.add_argument("--dry-run", action="store_true", help="POST 생략(매치만)")
    args = ap.parse_args()

    hub = os.environ.get("PUSHHUB_URL", "").rstrip("/")
    token = os.environ.get("PUSHHUB_SEND_TOKEN", "")
    if not args.dry_run and (not hub or not token):
        # 허브 미배포/secret 미설정 = 롤아웃 전 = graceful no-op(scan 도 생략, RED 아님). 배포 후 자동 활성.
        print("[watch] PUSHHUB 미설정 — skip(허브 미배포·롤아웃 전)", flush=True)
        return 0

    topics = [t.strip() for t in args.topics.split(",") if t.strip() in _EVALUATORS]
    matches: list[dict] = []
    for t in topics:
        found = _EVALUATORS[t]()
        print(f"[watch] {t}: 매치 {len(found)}건", flush=True)
        matches += found

    if args.dry_run:
        for m in matches:
            print(
                f"[watch] dry-run {m['topic']}:{m['slug']}: {json.dumps(m['notification'], ensure_ascii=False)}",
                flush=True,
            )
        return 0
    if not matches:
        print("[watch] 매치 0 — no-op", flush=True)
        return 0

    ts = int(time.time())
    new_sent = dup = 0
    problems: list[str] = []
    for m in matches:
        status, body = post_to_hub(hub, token, m["topic"], m["slug"], m["notification"], ts)
        kind = classify(status)
        if kind == "problem":
            problems.append(f"{m['topic']}:{m['slug']} 발송 실패(HTTP {status})")
        elif kind == "dup":
            dup += 1  # 이미 보낸 매치(last-seen set) — 정상
        else:
            new_sent += 1
            b = body or {}
            print(f"[watch] {m['topic']}:{m['slug']} → sent={b.get('sent')}", flush=True)

    print(f"[watch] 신규 발송 {new_sent}건 · 기존(dup) {dup}건 · 실패 {len(problems)}건", flush=True)
    if problems:
        for p in problems:
            print(f"::error::왓처 발송 실패 — {p}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
