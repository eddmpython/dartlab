"""dartlab-news 카테고리 썸네일 합성 (8편).

스펙: BLOG.md §썸네일 — dartlab-news 카테고리 (2026-04-21 확장)
- MNST 풀블리드 스펙 재사용 (1200×630 WebP, 좌측 그라데이션 + 흰 제목 오버레이)
- 좌상단 prefix = "DartLab 소식 · {주제}"
- 저장: landing/static/thumbnails/news-{slug}.webp
- 배경 원본: blog/02-dartlab-news/{NN}-{slug}/assets/{NN}-thumbnail-bg.webp

실행: uv run python -X utf8 blog/_scripts/gen_news_thumbnails.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab")
NEWS_DIR = ROOT / "blog/02-dartlab-news"
THUMBS = ROOT / "landing/static/thumbnails"
MASCOT = ROOT / "landing/static/avatar-chart.png"
FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"

# (NN, slug, 카테고리 prefix, 제목 2줄, 부제)
POSTS: list[tuple[str, str, str, list[str], str]] = [
    (
        "01",
        "dartlab-easy-start",
        "DartLab 소식 · 설치",
        ["정말 쉬운 dartlab 사용법", "uv로 5분이면 끝"],
        "Python 초보자를 위한 3단계 설치 가이드",
    ),
    (
        "03",
        "scan-market-finance",
        "DartLab 소식 · scan",
        ["2,500개 종목 재무를", "한 줄로 꺼낸다"],
        "dartlab.scan · 사전 빌드 parquet",
    ),
    (
        "04",
        "company-one-stock-code",
        "DartLab 소식 · Company",
        ["종목코드 하나면", "회사의 전부가 나온다"],
        "dartlab.Company · 3초면 재무제표",
    ),
    (
        "05",
        "search-without-embeddings",
        "DartLab 소식 · search",
        ["임베딩 없이 400만 문서", "95% 정밀도로 찾는다"],
        "BM25F + 리랭크 · 1/100 비용",
    ),
    (
        "06",
        "magic-formula-korea",
        "DartLab 소식 · 매직포뮬러",
        ["매직포뮬러를 한국 시장에", "그대로 돌려보면"],
        "그린블라트 공식 · Korea 백테스트",
    ),
    (
        "07",
        "dataset-auto-sync",
        "DartLab 소식 · 자동 수집",
        ["사용자가 받기 전에", "Actions가 매일 두 번 수집"],
        "GitHub Actions + HuggingFace · 03·15시",
    ),
    (
        "08",
        "pyodide-dartlab-lite",
        "DartLab 소식 · Pyodide",
        ["설치 없이 엑셀·브라우저에서", "dartlab을 그대로"],
        "xlwings Lite · JupyterLite · Colab",
    ),
    (
        "09",
        "terminal-one-screen",
        "DartLab 소식 · 터미널",
        ["종목 하나 보려고", "창을 일곱 개?"],
        "전 상장사 · 한 화면 계기판",
    ),
    (
        "10",
        "cards-publish",
        "DartLab 소식 · 카드뉴스",
        ["2만 자 분석은 안 읽힌다", "같은 숫자를 카드로"],
        "회사·이슈 카드 · /cards 에서 스와이프",
    ),
    (
        "11",
        "dart-libraries-compared",
        "DartLab 소식 · 비교",
        ["가져오는 건 기존 도구도", "한다. 그다음이 dartlab"],
        "OpenDartReader·dart-fss 그리고 dartlab",
    ),
]


def make_thumb(nn: str, slug: str, prefix: str, title_lines: list[str], subtitle: str) -> None:
    W, H = 1200, 630
    src = NEWS_DIR / f"{nn}-{slug}" / "assets" / f"{nn}-thumbnail-bg.webp"
    if not src.exists():
        print(f"MISS {nn}-{slug}: {src.relative_to(ROOT)} not found")
        return

    bg = Image.open(src).convert("RGB")
    bw, bh = bg.size
    ratio = max(W / bw, H / bh)
    nw, nh = int(bw * ratio), int(bh * ratio)
    bg = bg.resize((nw, nh), Image.LANCZOS)
    left = (nw - W) // 2
    top = (nh - H) // 2
    bg = bg.crop((left, top, left + W, top + H))

    # 좌측 어두운 그라데이션 + 전체 어두운 필터 (MNST 스펙 그대로)
    ovl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ovl)
    for x in range(W):
        alpha = max(0, int(200 * (1 - x / 900)))
        od.rectangle([(x, 0), (x + 1, H)], fill=(10, 14, 26, alpha))
    dim = Image.new("RGBA", (W, H), (10, 14, 26, 70))
    bg = Image.alpha_composite(bg.convert("RGBA"), dim)
    bg = Image.alpha_composite(bg, ovl)

    d = ImageDraw.Draw(bg)
    f_prefix = ImageFont.truetype(FONT_REG, 24)
    d.text((50, 40), prefix, fill=(148, 163, 184, 255), font=f_prefix)

    f_logo = ImageFont.truetype(FONT_BOLD, 22)
    logo_w = d.textlength("dartlab", font=f_logo)
    d.text((W - 50 - logo_w, 44), "dartlab", fill=(241, 245, 249, 255), font=f_logo)

    f_title = ImageFont.truetype(FONT_BOLD, 58)
    y = 190
    for line in title_lines:
        d.text((50, y), line, fill=(255, 255, 255, 255), font=f_title)
        y += 80

    f_sub = ImageFont.truetype(FONT_REG, 22)
    d.text((50, y + 30), subtitle, fill=(148, 163, 184, 255), font=f_sub)

    mascot = Image.open(MASCOT).convert("RGBA")
    ms = 160
    mascot = mascot.resize((ms, ms), Image.LANCZOS)
    bg.paste(mascot, (W - ms - 30, H - ms - 30), mascot)

    THUMBS.mkdir(parents=True, exist_ok=True)
    out = THUMBS / f"news-{slug}.webp"
    bg.convert("RGB").save(out, "WEBP", quality=90)
    print(f"OK news-{slug} -> {out.stat().st_size // 1024}KB")


def main() -> None:
    for nn, slug, prefix, title, sub in POSTS:
        make_thumb(nn, slug, prefix, title, sub)
    print("DONE")


if __name__ == "__main__":
    main()
