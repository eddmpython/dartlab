"""블로그 통합 썸네일 제너레이터. 카드뉴스(CardSlide) editorial 언어 그대로.

정책(BLOG.md §썸네일 신, 2026-06-27): 사진을 버리지 않는다. 카드뉴스 editorial 표지 그대로.
배경 사진을 흑백(그레이톤)으로 깔고 그 위에 어두운 스크림 + 카드뉴스 텍스트를 얹는다.
- 배경: 글 폴더 assets/{NN}*thumbnail-bg.webp 를 흑백 cover (CardSlide CSS와 동일: grayscale·대비·밝기).
        이미지가 없으면 navy #050811 + 좌하단 accent 글로우로 폴백.
- 스크림: 텍스트 시작점 위로 부드럽게 진해지는 navy 그라데이션. 사진 위에서도 글씨가 읽힌다.
- 텍스트: 하단 정렬·좌측. kicker(● + 카테고리, accent) → 제목(흰 #f6f8fb, 숫자=accent) → 부제(dim).
- 서명: 좌하단 avatar.webp(원형) + "dartlab"(굵게). CoverThumb .brand 그대로.
- 색 = CARD 팔레트(accent #ff3f6f). frontmatter title·description 만으로 생성(글마다 즉흥 없음).

실행:
  uv run python -X utf8 blog/_scripts/gen_blog_thumbnails.py --slugs treasury-stock-not-cancelled --out <dir>
  uv run python -X utf8 blog/_scripts/gen_blog_thumbnails.py --all --apply
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(r"c:/Users/MSI/OneDrive/Desktop/sideProject/dartlab")
BLOG = ROOT / "blog"
THUMBS = ROOT / "landing/static/thumbnails"
AVATAR = ROOT / "landing/static/avatar.webp"
FB = "C:/Windows/Fonts/malgunbd.ttf"
FR = "C:/Windows/Fonts/malgun.ttf"

W, H = 1200, 630
PAD = 64
BG = (5, 8, 17)  # CARD.bgDark #050811
BG2 = (10, 14, 24)  # 살짝 밝은 navy (옅은 그라데이션)
ACCENT = (255, 63, 111)  # CARD.accent #ff3f6f
INK = (246, 248, 251)  # CARD.text #f6f8fb
DIM = (200, 206, 214)  # 부제(사진 스크림 위라 약간 밝게)

# CardSlide editorial 필터값과 정렬(grayscale 0.85·대비 1.06·밝기 0.92, 사진을 무드 있게 통일)
GRAY_BLEND = 0.85
CONTRAST = 1.06
BRIGHTNESS = 0.92

PREFIX = {
    "reading-disclosures": "공시 읽기",
    "dartlab-news": "DartLab 소식",
    "dartlab-stories": "dartlab 이야기",
    "credit-reports": "신용분석 보고서",
    "company-reports": "기업이야기",
    "data-reports": "데이터 리포트",
    "tech-story": "기술이야기",
    "investment-stories": "투자이야기",
}

# 숫자(+한글 단위) = accent 강조 (카드뉴스 [[구절]] 자동 근사)
NUM = re.compile(r"([0-9][0-9,.]*\s*(?:%|곳|조|억|배|위|년|개사|개|만|천|건|배)?)")


def parseFrontmatter(text: str) -> dict:
    """index.md 상단 YAML frontmatter 를 평평한 dict 로 파싱(스칼라만)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out: dict = {}
    for line in m.group(1).split("\n"):
        km = re.match(r"^(\w+):\s*(.+)$", line)
        if km:
            out[km.group(1)] = km.group(2).strip().strip("'\"")
    return out


def circleAvatar(d: int) -> Image.Image:
    """avatar.webp 를 d×d 원형으로 마스크."""
    av = Image.open(AVATAR).convert("RGBA").resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d, d], fill=255)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(av, (0, 0), mask)
    return out


def grayscaleCover(bg_path: Path) -> Image.Image:
    """배경 사진을 1200×630 cover-crop 후 흑백 editorial 톤(CardSlide CSS와 동일)으로."""
    im = Image.open(bg_path).convert("RGB")
    w, h = im.size
    scale = max(W / w, H / h)
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    gray = im.convert("L").convert("RGB")
    im = Image.blend(im, gray, GRAY_BLEND)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    return im


def flatNavy() -> Image.Image:
    """이미지 없는 글 폴백. navy 세로 그라데이션 + 좌하단 옅은 accent 글로우."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(BG[i] + (BG2[i] - BG[i]) * t) for i in range(3)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([-260, H - 360, 320, H + 200], fill=(255, 63, 111, 26))
    return Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")


def applyScrim(img: Image.Image, text_top: int) -> Image.Image:
    """text_top 위로 부드럽게, 아래로 진하게. 사진 위에서도 글씨가 읽히는 navy 스크림."""
    fade_start = max(0, text_top - 230)
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(H):
        if y <= fade_start:
            a = 26  # 상단: 사진 거의 그대로(살짝만 가라앉힘)
        elif y >= text_top:
            t2 = (y - text_top) / max(1, H - text_top)
            a = int(165 + 78 * t2)  # 텍스트 영역 165 → 바닥 243
        else:
            t1 = (y - fade_start) / (text_top - fade_start)
            a = int(26 + (165 - 26) * (t1**1.7))
        sd.line([(0, y), (W, y)], fill=(BG[0], BG[1], BG[2], a))
    return Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB")


def wrapAccent(d: ImageDraw.ImageDraw, title: str, max_w: int) -> tuple[list[list[tuple]], ImageFont.FreeTypeFont]:
    """제목을 폭에 맞춰 ≤3줄로 자른다. 각 줄은 [(텍스트, accent여부)] 세그먼트. 안 맞으면 폰트 축소."""
    for size in (58, 52, 46, 42):
        font = ImageFont.truetype(FB, size)
        words = title.split(" ")
        lines: list[str] = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textlength(test, font=font) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) <= 3:
            return [[(seg, bool(NUM.fullmatch(seg))) for seg in NUM.split(ln) if seg] for ln in lines], font
    font = ImageFont.truetype(FB, 42)
    return [[(seg, bool(NUM.fullmatch(seg))) for seg in NUM.split(ln) if seg] for ln in lines[:3]], font


def render(fm: dict, bg_path: Path | None, out_path: Path) -> None:
    """frontmatter 한 건 → 카드뉴스 editorial 썸네일 1장(흑백 사진 + 스크림 + 하단 텍스트)."""
    base = grayscaleCover(bg_path) if (bg_path and bg_path.exists()) else flatNavy()

    # 텍스트 레이아웃을 먼저 측정(하단 정렬, 좌하단 서명 위)
    measure = ImageDraw.Draw(base)
    title = fm.get("title", "")
    seg_lines, ftitle = wrapAccent(measure, title, W - PAD - 80)
    line_h = ftitle.size + 14
    fkick = ImageFont.truetype(FB, 24)
    fsub = ImageFont.truetype(FR, 23)

    avatar_d = 34
    avatar_top = H - 44 - avatar_d
    sub_top = avatar_top - 46
    title_bottom = sub_top - 22
    title_top = title_bottom - len(seg_lines) * line_h
    kicker_top = title_top - 16 - fkick.size

    # 스크림은 텍스트 시작점(kicker) 기준: 사진이면 강하게, 폴백 navy 면 거의 영향 없음
    img = applyScrim(base, kicker_top)
    d = ImageDraw.Draw(img)

    # kicker: ● + 카테고리(accent)
    prefix = PREFIX.get(fm.get("category", ""), "DartLab")
    dot_r = 7
    d.ellipse([PAD, kicker_top + 9, PAD + dot_r * 2, kicker_top + 9 + dot_r * 2], fill=ACCENT)
    d.text((PAD + dot_r * 2 + 12, kicker_top), prefix, fill=ACCENT, font=fkick)

    # 제목: 흰색 + 숫자 accent
    y = title_top
    for segs in seg_lines:
        x = PAD
        for text, is_num in segs:
            d.text((x, y), text, fill=ACCENT if is_num else INK, font=ftitle)
            x += d.textlength(text, font=ftitle)
        y += line_h

    # 부제: dim, 1줄(폭 넘으면 말줄임)
    desc = fm.get("description", "")
    if desc:
        full = desc
        while desc and d.textlength(desc, font=fsub) > W - PAD - 80:
            desc = desc[:-2]
        if desc != full:
            desc = desc.rstrip() + "…"
        d.text((PAD, sub_top), desc, fill=DIM, font=fsub)

    # 서명: 좌하단 avatar(원형) + dartlab
    img.paste(circleAvatar(avatar_d), (PAD, avatar_top), circleAvatar(avatar_d))
    d.text((PAD + avatar_d + 12, avatar_top + 6), "dartlab", fill=INK, font=ImageFont.truetype(FB, 23))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, "WEBP", quality=90)
    tag = "img" if (bg_path and bg_path.exists()) else "navy"
    print(f"OK   {out_path.name} [{tag}] ← {title[:34]}")


def renderCard(bg_path: Path | None, out_path: Path) -> None:
    """리스트 카드용: 텍스트 없는 깨끗한 흑백 이미지(제목은 카드가 따로 보여줌, 중복·crop 방지)."""
    img = grayscaleCover(bg_path) if (bg_path and bg_path.exists()) else flatNavy()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, "WEBP", quality=88)


def findBg(post_dir: Path) -> Path | None:
    """글 폴더 assets/ 에서 *thumbnail-bg.webp 첫 매치(없으면 None)."""
    hits = sorted((post_dir / "assets").glob("*thumbnail-bg.webp"))
    return hits[0] if hits else None


def iterPosts():
    """blog/*/*/index.md 전부를 (slug, frontmatter, post_dir, bg_path) 로 순회."""
    for md in BLOG.glob("*/*/index.md"):
        rel = md.relative_to(BLOG).as_posix()
        sm = re.match(r"^[^/]+/\d+-([^/]+)/index\.md$", rel)
        if not sm:
            continue
        fm = parseFrontmatter(md.read_text(encoding="utf-8"))
        if not fm.get("title"):
            continue
        yield sm.group(1), fm, md.parent, findBg(md.parent)


def outPathFor(slug: str, fm: dict, preview_dir: Path | None) -> Path | None:
    """미리보기면 preview_dir/{slug}.webp. 적용이면 ogImage 경로 덮어쓰기(없으면 None, 건너뜀)."""
    if preview_dir is not None:
        return preview_dir / f"{slug}.webp"
    og = fm.get("ogImage", "")
    if og.startswith("/thumbnails/"):
        return THUMBS / Path(og).name
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", help="쉼표 구분 slug 목록(부분일치)")
    ap.add_argument("--all", action="store_true", help="전체 글")
    ap.add_argument("--apply", action="store_true", help="라이브 ogImage 경로 덮어쓰기(없으면 preview)")
    ap.add_argument("--out", default="preview", help="미리보기 출력 폴더(절대경로)")
    args = ap.parse_args()

    preview_dir = None if args.apply else Path(args.out)
    want = [s.strip() for s in (args.slugs or "").split(",") if s.strip()]
    n = 0
    n_img = 0
    skipped: list[str] = []
    for slug, fm, post_dir, bg in iterPosts():
        if not args.all and not any(w in slug for w in want):
            continue
        out = outPathFor(slug, fm, preview_dir)
        if out is None:
            skipped.append(f"{fm.get('category', '?')}/{slug}")
            continue
        render(fm, bg, out)  # og:image: 텍스트 합성(소셜 공유용)
        renderCard(bg, out.with_name(out.stem + "-card" + out.suffix))  # 리스트 카드용: 텍스트 없는 깨끗한 이미지
        n += 1
        if bg:
            n_img += 1
    print(
        f"DONE {n} thumbnails (+{n} card 변형, {n_img} 사진 / {n - n_img} navy 폴백, {'apply' if args.apply else 'preview'})"
    )
    if skipped:
        print(f"SKIP {len(skipped)} (ogImage 없음):")
        for s in skipped:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
