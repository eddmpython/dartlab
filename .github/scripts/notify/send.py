"""발행 알림 러너 — git diff 로 발행 검출 → 허브 /send 호출 + 관측성 헬스게이트.

흐름: detect(before..sha) → build_payload → auth_headers(Bearer+nonce) → POST /send → 응답 집계.
독립 워크플로(notify-publish.yml)에서 push 이벤트당 1회. (topic,slug) 결정적 nonce 라 재실행은 허브에서
409(멱등) — 발행 알림은 저-stakes 단발(놓친 알림=손실 아님)이라 best-effort.

헬스게이트(brokerageSync 미러): 발송 POST 가 401/5xx/네트워크 실패면 비-0 exit → 워크플로 RED → 운영자
자동알림(조용한 발송 실패 차단). 409(이미 발송)·sent==0(구독 0 no-op)은 정상 구분.
사용: python send.py --before <sha> --sha <sha> [--dry-run]
현재 운영 계약은 Skill OS ``operation.notifyPipeline``이다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml
from hubClient import classify, post_to_hub
from payload import PublishEvent, build_payload

_BLOG_RE = re.compile(r"^blog/[^/]+/\d+-([^/]+)/index\.md$")  # slug = \d+- 뒤 그룹(+page.ts normalizePath 동형)
_ISSUE_RE = re.compile(r"^blog/_issues/([^/]+)/cards\.plan\.json$")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout


def parse_frontmatter(text: str) -> dict:
    """--- ... --- 사이 통째 yaml.safe_load(라인파서 금지 — nested carousel dict·멀티라인 caption 처리)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def detect(before: str, sha: str) -> list[PublishEvent]:
    """git diff(추가/변경 파일) → 발행 이벤트. 블로그 글(+carousel) → blogPublish(+cardPublish), 이슈카드 → cardPublish."""
    files = _git("diff", "--name-only", before, sha).splitlines()
    events: list[PublishEvent] = []
    for f in files:
        f = f.strip()
        m = _BLOG_RE.match(f)
        if m:
            slug = m.group(1)
            p = Path(f)
            if not p.exists():  # 삭제분은 발행 아님
                continue
            front = parse_frontmatter(p.read_text(encoding="utf-8"))
            title = front.get("title", slug)
            desc = front.get("description", "")
            events.append(PublishEvent("blogPublish", slug, title, desc))
            if front.get("carousel"):  # carousel: 블록 있으면 카드도 발행(다른 토픽=다른 nonce)
                events.append(PublishEvent("cardPublish", slug, title, desc))
            continue
        m = _ISSUE_RE.match(f)
        if m:
            p = Path(f)
            if not p.exists():
                continue
            plan = json.loads(p.read_text(encoding="utf-8"))
            tgt = plan.get("target", {})  # title/slug 는 target 하위(top-level 부재)
            slug = tgt.get("slug", m.group(1))
            title = tgt.get("title", m.group(1))
            body = plan.get("planning", {}).get("cardThesis", "")  # description 부재 → cardThesis
            events.append(PublishEvent("cardPublish", slug, title, body))
    return events


def post_send(hub: str, token: str, ev: PublishEvent, ts: int) -> tuple[int, dict | None]:
    """이벤트 1개 → /send 1 POST(hubClient 공유). (status, body) 반환."""
    payload = build_payload(ev)
    return post_to_hub(hub, token, ev.topic, ev.slug, payload["notification"], ts)


def _write_summary(rows: list[dict]) -> None:
    """GITHUB_STEP_SUMMARY 에 topic별 발송 결과 표 — Actions 외(로컬)는 no-op."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "## 발행 알림 발송 결과",
        "",
        "| 토픽 | slug | HTTP | sent | pruned | failed |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        b = r["body"] or {}
        lines.append(
            f"| {r['topic']} | {r['slug']} | {r['status']} | {b.get('sent', '-')} | {b.get('pruned', '-')} | {b.get('failed', '-')} |"
        )
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="발행 알림 러너")
    ap.add_argument("--before", required=True, help="git diff 시작 sha(github.event.before)")
    ap.add_argument("--sha", required=True, help="git diff 끝 sha(github.sha)")
    ap.add_argument("--dry-run", action="store_true", help="POST 생략(검출만)")
    args = ap.parse_args()

    before = args.before
    if not before or set(before) <= {"0"}:  # 첫 push/강제 push = before all-zero → 부모 커밋과 diff
        before = args.sha + "^"
    events = detect(before, args.sha)
    if not events:
        print("[notify] 발행 이벤트 0 — no-op", flush=True)
        return 0
    print(f"[notify] 발행 이벤트 {len(events)}건: {[(e.topic, e.slug) for e in events]}", flush=True)

    if args.dry_run:
        for ev in events:
            print(
                f"[notify] dry-run {ev.topic} {ev.slug}: {json.dumps(build_payload(ev), ensure_ascii=False)}",
                flush=True,
            )
        return 0

    hub = os.environ.get("PUSHHUB_URL", "").rstrip("/")
    token = os.environ.get("PUSHHUB_SEND_TOKEN", "")
    if not hub or not token:
        # 허브 미배포/secret 미설정 = 롤아웃 전 = graceful no-op(RED 아님). 배포 후 자동 활성.
        print("[notify] PUSHHUB 미설정 — 발송 skip(허브 미배포·롤아웃 전)", flush=True)
        return 0

    ts = int(time.time())
    rows: list[dict] = []
    problems: list[str] = []
    for ev in events:
        status, body = post_send(hub, token, ev, ts)
        rows.append({"topic": ev.topic, "slug": ev.slug, "status": status, "body": body})
        kind = classify(status)
        if kind == "problem":
            problems.append(f"{ev.topic}:{ev.slug} 발송 실패(HTTP {status}) — SEND_TOKEN 짝맞춤·허브 점검")
        elif kind == "dup":
            print(f"[notify] {ev.topic}:{ev.slug} 이미 발송됨(409 멱등) — skip", flush=True)
        else:
            b = body or {}
            print(
                f"[notify] {ev.topic}:{ev.slug} → sent={b.get('sent')} pruned={b.get('pruned')} failed={b.get('failed')}",
                flush=True,
            )

    _write_summary(rows)
    if problems:
        for p in problems:
            print(f"::error::발행 알림 발송 실패 — {p}", flush=True)
        return 1
    print("[notify] 발송 정상", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
