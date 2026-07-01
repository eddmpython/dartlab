"""dartlab-news 썸네일 배경 — CC0/PD 스톡 수급 (FLUX 대체, 생성형 안 씀).

`gen_news_flux.py`(Replicate FLUX)의 **CC0 대체 경로**. 카드뉴스 발간 규칙(CARDS.md)과 같은 원칙 —
발간물 배경은 출처 깨끗한 PD/CC0 실사로 통일하고 생성형 이미지는 쓰지 않는다. 수급 엔진은
`fetch_cc0_images.py`(Wikimedia Commons + Openverse, 귀속 의무 없는 PD/CC0 만)를 그대로 재사용한다.

- 저장: blog/02-dartlab-news/{NN}-{slug}/assets/{NN}-thumbnail-bg.webp (덮어쓰기 없음 — --force 로만)
- 이후 합성: gen_news_thumbnails.py 가 이 배경 위에 좌상단 키커·제목·부제·마스코트를 얹는다.
- 받은 즉시 눈으로 확정한다(스톡 적중률 들쭉날쭉 — 오매치 섞임).

실행: uv run python -X utf8 blog/_scripts/gen_news_cc0.py [--only 10-cards-publish] [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_cc0_images import _candidates, _credit_line, _download, _relevant, _save_webp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NEWS_DIR = ROOT / "blog/02-dartlab-news"

# (NN, slug, queries[앞에서부터 첫 매치], keywords[제목/태그 관련성 게이트])
POSTS: list[tuple[str, str, list[str], list[str]]] = [
    (
        "09",
        "terminal-one-screen",
        [
            "stock market trading screens multiple monitors",
            "financial analytics dashboard dark monitor",
            "trading desk computer screens finance",
        ],
        ["screen", "monitor", "trading", "stock", "dashboard", "display", "computer", "finance"],
    ),
    (
        "10",
        "cards-publish",
        [
            "person holding smartphone social media app",
            "hand holding mobile phone screen",
            "smartphone scrolling feed close up",
        ],
        ["phone", "smartphone", "mobile", "hand", "screen", "social"],
    ),
    (
        "11",
        "dart-libraries-compared",
        [
            "colorful source code syntax highlighting screen",
            "python source code editor colourful",
            "programming code on computer monitor",
            "software code editor dark screen",
        ],
        ["code", "python", "programming", "software", "screen", "monitor", "laptop", "computer", "editor", "syntax"],
    ),
]


def run(nn: str, slug: str, queries: list[str], keywords: list[str], force: bool) -> str | None:
    out = NEWS_DIR / f"{nn}-{slug}" / "assets" / f"{nn}-thumbnail-bg.webp"
    if out.exists() and not force:
        return f"SKIP {nn}-{slug} (이미 있음, --force 로 덮어쓰기)"
    for query in queries:
        for item in _candidates(query):
            if not _relevant(item, keywords):
                continue
            im = _download(item.get("url", ""))
            if im is None:
                continue
            size = _save_webp(im, out)
            lic = f"{item.get('license', '')} {item.get('license_version', '')}".strip()
            # 출처는 글 폴더 CREDITS.md 에 기록(CC0/PD 는 의무 아니나 감사 추적).
            cred = out.parent.parent / "CREDITS.md"
            header = (
                "" if cred.exists() else "# 썸네일 배경 출처 (CC0 / Public Domain — Wikimedia Commons · Openverse)\n\n"
            )
            with cred.open("a", encoding="utf-8") as fh:
                fh.write(header + _credit_line("thumbnail-bg", query, item) + "\n")
            return f"OK   {nn}-{slug} ({size // 1024} KB) <- [{query}] {lic}"
    return f"MISS {nn}-{slug} — 관련 PD/CC0 매치 없음 (queries 조정 필요)"


def main() -> None:
    parser = argparse.ArgumentParser(description="dartlab-news 썸네일 배경 CC0 수급 (FLUX 대체)")
    parser.add_argument("--only", help="특정 {NN}-{slug} 만 (예: 10-cards-publish)")
    parser.add_argument("--force", action="store_true", help="기존 배경 덮어쓰기")
    args = parser.parse_args()

    for nn, slug, queries, keywords in POSTS:
        if args.only and f"{nn}-{slug}" != args.only:
            continue
        print(run(nn, slug, queries, keywords, args.force))
    print("DONE — 다음: gen_news_thumbnails.py 로 합성")


if __name__ == "__main__":
    main()
