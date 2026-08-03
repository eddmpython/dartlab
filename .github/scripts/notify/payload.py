"""발행 알림 페이로드 조립 — 토픽별 url/tag, body=description/cardThesis. aes128gcm 평문이라 제목+본문 실제 표시.

url 은 app-path(base 없음) — SW 가 한 곳에서 BASE_PATH(/dartlab) 접두([07 §1]). 라이브 라우트 SSOT:
blog=/blog/{slug}, card=/cards?post={slug}(landing share.ts cardShareUrl 동형).
현재 운영 계약은 Skill OS ``operation.notifyPipeline``이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from sanitize import sanitize


@dataclass
class PublishEvent:
    topic: str  # 'blogPublish' | 'cardPublish'
    slug: str  # +page.ts normalizePath 동형(카테고리·번호 미포함)
    title: str
    summary: str  # 블로그=frontmatter description, 이슈카드=planning.cardThesis


def build_payload(ev: PublishEvent) -> dict:
    """PublishEvent → 허브 /send body({topic, notification:{title,body,url,tag}})."""
    if ev.topic == "blogPublish":
        url = f"/blog/{ev.slug}"
        tag = f"blog:{ev.slug}"
        title = "[새 글] " + sanitize(ev.title, max_len=80)
    else:
        url = f"/cards?post={quote(ev.slug)}"  # 라이브 카드 라우트 = /cards?post= (share.ts 동형)
        tag = f"card:{ev.slug}"
        title = "[새 카드] " + sanitize(ev.title, max_len=80)
    return {
        "topic": ev.topic,
        "notification": {
            "title": title,
            "body": sanitize(ev.summary, max_len=120),
            "url": url,
            "tag": tag,
        },
    }
