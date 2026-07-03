"""data-reports 카테고리 썸네일 생성 — CC0 배경 수급 + 제목 오버레이 합성.

스펙: BLOG.md §썸네일 — news 레이아웃 재사용(1200×630, 좌측 그라데이션 + 흰 제목)
- 배경: Wikimedia Commons · Openverse 에서 PD/CC0 만 수급 (생성형 FLUX 안 씀, 출처 깨끗한 실사)
  → blog/06-data-reports/{NN}-{slug}/assets/{NN}-thumbnail-bg.webp + CREDITS.md
- 합성: landing/static/thumbnails/data-{slug}.webp (frontmatter ogImage 와 동일 경로)

실행: uv run python -X utf8 blog/_scripts/gen_data_thumbnails.py
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab")
DATA_DIR = ROOT / "blog/06-data-reports"
THUMBS = ROOT / "landing/static/thumbnails"
MASCOT = ROOT / "landing/static/avatar-chart.png"
FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"

COMMONS = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"
UA = {"User-Agent": "dartlab-data-reports/1.0 (license-clean CC0/PD image fetch)"}
FREE_TOKENS = ("public domain", "cc0", "pd-", "no restrictions")

# (NN, slug, prefix, [제목 2줄], 부제, [CC0 검색어], [채택 키워드])
POSTS: list[tuple[str, str, str, list[str], str, list[str], list[str]]] = [
    (
        "01",
        "treasury-stock-not-cancelled",
        "데이터 리포트 · 자사주",
        ["자사주를 사고도", "소각하지 않는다"],
        "전상장사 2,933곳 전수 · 자사주 보유사 93%가 소각 0",
        [
            "stock market display board",
            "stock exchange trading floor",
            "financial district skyscraper night",
            "stock market chart screen",
        ],
        ["stock", "market", "exchange", "finance", "trading", "board", "building", "skyline", "business", "screen"],
    ),
    (
        "02",
        "interest-coverage-zombie-firms",
        "데이터 리포트 · 한계기업",
        ["3년 내리 이자도", "못 갚은 상장사 713곳"],
        "비금융 상장사 1,924곳 전수 · 37%가 3년 연속 이자보상배율 1 미만",
        [
            "abandoned factory industrial",
            "financial district skyscraper night",
            "stock market chart red",
            "empty office building",
        ],
        ["factory", "industrial", "building", "finance", "chart", "market", "business", "office", "skyline", "screen"],
    ),
]


def _strip(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def _commons(query: str, n: int = 20) -> list[dict]:
    try:
        r = requests.get(
            COMMONS,
            params={
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"{query} filetype:bitmap",
                "gsrnamespace": "6",
                "gsrlimit": n,
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": 1600,
            },
            headers=UA,
            timeout=25,
        )
        r.raise_for_status()
        pages = (r.json().get("query", {}) or {}).get("pages", {}) or {}
    except Exception as exc:
        print(f"    commons '{query}' 실패: {exc}")
        return []
    out = []
    for p in pages.values():
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {}) or {}
        lic = (meta.get("LicenseShortName", {}) or {}).get("value", "")
        if not any(t in lic.lower() for t in FREE_TOKENS):
            continue
        out.append(
            {
                "url": info.get("thumburl") or info.get("url", ""),
                "title": _strip((meta.get("ObjectName", {}) or {}).get("value", "")) or p.get("title", ""),
                "creator": _strip((meta.get("Artist", {}) or {}).get("value", "")) or "unknown",
                "license": lic,
                "src": info.get("descriptionurl", ""),
            }
        )
    return out


def _openverse(query: str, n: int = 12) -> list[dict]:
    try:
        r = requests.get(
            OPENVERSE,
            params={"q": query, "license": "cc0,pdm", "page_size": n, "mature": "false"},
            headers=UA,
            timeout=25,
        )
        r.raise_for_status()
        res = r.json().get("results", [])
    except Exception as exc:
        print(f"    openverse '{query}' 실패: {exc}")
        return []
    return [
        {
            "url": it.get("url", ""),
            "title": it.get("title", ""),
            "creator": it.get("creator", "unknown"),
            "license": f"{it.get('license', '')} {it.get('license_version', '')}".strip(),
            "src": it.get("foreign_landing_url", ""),
        }
        for it in res
    ]


def _relevant(item: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    hay = (item.get("title") or "").lower()
    return any(k.lower() in hay for k in keywords)


def _download(url: str) -> Image.Image | None:
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200 or len(r.content) < 20000:
            return None
        im = Image.open(io.BytesIO(r.content))
        im.load()
        if min(im.size) < 600:
            return None
        return im.convert("RGB")
    except Exception:
        return None


def fetch_bg(nn: str, slug: str, queries: list[str], keywords: list[str]) -> tuple[Path, dict] | None:
    dest = DATA_DIR / f"{nn}-{slug}" / "assets" / f"{nn}-thumbnail-bg.webp"
    if dest.exists():
        print(f"SKIP bg {nn}-{slug} (이미 있음)")
        return dest, {}
    for q in queries:
        for item in _commons(q) + _openverse(q):
            if not _relevant(item, keywords):
                continue
            im = _download(item.get("url", ""))
            if im is None:
                continue
            w, h = im.size
            scale = min(1.0, 1600 / max(w, h))
            if scale < 1.0:
                im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, "WEBP", quality=86, method=6)
            print(f"OK   bg {nn}-{slug} ({dest.stat().st_size // 1024}KB) ← [{q}] {item['license']}")
            # CREDITS
            cred = dest.parent / "CREDITS.md"
            line = f"- **{nn}-thumbnail-bg.webp** — {item['title'] or '(무제)'} / {item['creator']} / {item['license']} / [{q}] / {item['src']}"
            header = "" if cred.exists() else "# 이미지 출처 (CC0 / Public Domain — Wikimedia Commons · Openverse)\n\n"
            with cred.open("a", encoding="utf-8") as fh:
                fh.write(header + line + "\n")
            return dest, item
    print(f"MISS bg {nn}-{slug} — 관련 PD/CC0 매치 없음")
    return None


def composite(nn: str, slug: str, prefix: str, title_lines: list[str], subtitle: str, bg_path: Path) -> None:
    W, H = 1200, 630
    bg = Image.open(bg_path).convert("RGB")
    bw, bh = bg.size
    ratio = max(W / bw, H / bh)
    nw, nh = int(bw * ratio), int(bh * ratio)
    bg = bg.resize((nw, nh), Image.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    bg = bg.crop((left, top, left + W, top + H))

    ovl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ovl)
    for x in range(W):
        alpha = max(0, int(210 * (1 - x / 900)))
        od.rectangle([(x, 0), (x + 1, H)], fill=(10, 14, 26, alpha))
    dim = Image.new("RGBA", (W, H), (10, 14, 26, 90))
    bg = Image.alpha_composite(bg.convert("RGBA"), dim)
    bg = Image.alpha_composite(bg, ovl)

    d = ImageDraw.Draw(bg)
    d.text((50, 40), prefix, fill=(148, 163, 184, 255), font=ImageFont.truetype(FONT_REG, 24))
    f_logo = ImageFont.truetype(FONT_BOLD, 22)
    d.text((W - 50 - d.textlength("dartlab", font=f_logo), 44), "dartlab", fill=(241, 245, 249, 255), font=f_logo)

    f_title = ImageFont.truetype(FONT_BOLD, 58)
    y = 190
    for line in title_lines:
        d.text((50, y), line, fill=(255, 255, 255, 255), font=f_title)
        y += 80
    d.text((50, y + 30), subtitle, fill=(148, 163, 184, 255), font=ImageFont.truetype(FONT_REG, 22))

    mascot = Image.open(MASCOT).convert("RGBA").resize((150, 150), Image.LANCZOS)
    bg.paste(mascot, (W - 150 - 30, H - 150 - 30), mascot)

    THUMBS.mkdir(parents=True, exist_ok=True)
    out = THUMBS / f"data-{slug}.webp"
    bg.convert("RGB").save(out, "WEBP", quality=90)
    print(f"OK   thumb data-{slug} -> {out.stat().st_size // 1024}KB")


def main() -> None:
    for nn, slug, prefix, title, sub, queries, keywords in POSTS:
        res = fetch_bg(nn, slug, queries, keywords)
        if not res:
            print(f"  bg 없음 — {slug} 합성 건너뜀")
            continue
        bg_path, _ = res
        composite(nn, slug, prefix, title, sub, bg_path)
    print("DONE")


if __name__ == "__main__":
    main()
