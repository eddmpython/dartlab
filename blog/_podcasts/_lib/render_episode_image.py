"""Render podcast episode still images in the card visual language.

One reusable source artwork produces two derived stills:
  - static-video.jpg: 16:9 still for video and thumbnail surfaces
  - cover.jpg: square RSS artwork for podcast directories

Composition mirrors the card news slide (CardSlide.svelte): grayscale editorial
background with a rose accent, and a bottom-left text block. From top to bottom the
block is kicker(accent eyebrow), bold headline([[phrase]]=rose), small subtitle, and a
bottom-left signature of the round dartlab avatar plus the "dartlab" wordmark.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from card_style import (
    ACCENT_RGB,
    BG_RGB,
    BRIGHTNESS,
    CONTRAST,
    DIM_RGB,
    GRAYSCALE,
    INK_RGB,
    accent_parts,
)
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

LIB_DIR = Path(__file__).resolve().parent
PODCAST_DIR = LIB_DIR.parent
ROOT = PODCAST_DIR.parents[1]
EPISODES_DIR = PODCAST_DIR / "episodes"
AVATAR = ROOT / "landing" / "static" / "avatar.png"

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"


def load_episode(ep_dir: Path) -> dict:
    data = yaml.safe_load((ep_dir / "episode.yaml").read_text(encoding="utf-8")) or {}
    meta = data.get("episode") or {}
    if not meta:
        raise SystemExit(f"[render] episode.yaml 형식 오류: {ep_dir}")
    return meta


def resolve_episode_path(ep_dir: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return ep_dir / path


def cover_crop(im: Image.Image, width: int, height: int) -> Image.Image:
    w, h = im.size
    scale = max(width / w, height / h)
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    x = (im.width - width) // 2
    y = (im.height - height) // 2
    return im.crop((x, y, x + width, y + height))


def editorial_background(src: Path, width: int, height: int) -> Image.Image:
    im = Image.open(src).convert("RGB")
    im = cover_crop(im, width, height)
    gray = im.convert("L").convert("RGB")
    im = Image.blend(im, gray, GRAYSCALE)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
    return im


def add_scrim(im: Image.Image, left_strength: int, bottom_strength: int) -> Image.Image:
    width, height = im.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for x in range(width):
        t = 1.0 - min(1.0, x / (width * 0.72))
        a = int(left_strength * (t**1.8))
        if a:
            d.line([(x, 0), (x, height)], fill=(BG_RGB[0], BG_RGB[1], BG_RGB[2], a))
    for y in range(height):
        t = max(0.0, (y - height * 0.42) / (height * 0.58))
        a = int(bottom_strength * (t**1.35))
        if a:
            d.line([(0, y), (width, y)], fill=(BG_RGB[0], BG_RGB[1], BG_RGB[2], a))
    return Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def fit_font(
    d: ImageDraw.ImageDraw, text: str, path: str, size: int, max_width: int, min_size: int
) -> ImageFont.FreeTypeFont:
    while size > min_size:
        f = font(path, size)
        if d.textlength(text, font=f) <= max_width:
            return f
        size -= 4
    return font(path, min_size)


def truncate(d: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_width: int) -> str:
    if d.textlength(text, font=f) <= max_width:
        return text
    ell = "..."
    while text and d.textlength(text + ell, font=f) > max_width:
        text = text[:-1]
    return text.rstrip() + ell


def draw_accent_line(
    d: ImageDraw.ImageDraw, x: int, y: int, line: str, f: ImageFont.FreeTypeFont, ink: tuple, accent: tuple
) -> None:
    """한 줄을 그린다. `[[구절]]` 은 accent 색, 나머지는 ink (카드 강조 규약)."""
    cx = x
    for text, is_accent in accent_parts(line):
        d.text((cx, y), text, fill=(accent if is_accent else ink), font=f)
        cx += round(d.textlength(text, font=f))


def visual_spec(meta: dict) -> dict:
    visual = meta.get("visual") or {}
    if not isinstance(visual, dict):
        visual = {}
    return {
        "source": str(visual.get("source") or "assets/source-gray.webp"),
        # 에피소드 번호(EP.NN)는 이미지에 넣지 않는다 (운영자 지시 2026-07-03). kicker = 브랜드만.
        "kicker": str(visual.get("kicker") or "DartLab Podcast"),
        "titleLines": [str(x) for x in (visual.get("titleLines") or [str(meta.get("title") or "")]) if str(x).strip()],
        "subtitle": str(visual.get("subtitle") or meta.get("oneLineMessage") or meta.get("summary") or ""),
        "footer": str(visual.get("footer") or "DartLab"),
    }


def paste_avatar(img: Image.Image, x: int, y: int, s: int) -> None:
    """dartlab 아바타를 원형으로 좌측하단 서명 자리에 붙인다 (카드 아바타 규약)."""
    circle = Image.new("RGBA", (s, s), (BG_RGB[0], BG_RGB[1], BG_RGB[2], 255))
    if AVATAR.exists():
        av = Image.open(AVATAR).convert("RGBA").resize((s, s), Image.LANCZOS)
        circle.alpha_composite(av)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, s - 1, s - 1), fill=255)
    img.paste(circle.convert("RGB"), (x, y), mask)


def draw_frame(meta: dict, src: Path, out: Path, width: int, height: int, cfg: dict) -> None:
    """카드 시각언어 스틸 한 장. 하단좌측 = 아바타+dartlab, 그 위 kicker/굵은 헤드라인/작은 sub."""
    spec = visual_spec(meta)
    img = add_scrim(editorial_background(src, width, height), cfg["scrimL"], cfg["scrimB"])
    d = ImageDraw.Draw(img)

    x = cfg["x"]
    max_w = width - 2 * x
    bottom = height - cfg["marginB"]

    # 좌측하단 서명 = 원형 아바타 + dartlab 워드마크 (아바타 세로중앙에 텍스트 정렬)
    av = cfg["avatar"]
    sig_y = bottom - av
    paste_avatar(img, x, sig_y, av)
    d.text(
        (x + av + cfg["gapAv"], sig_y + av // 2),
        "dartlab",
        font=font(FONT_BOLD, cfg["brand"]),
        fill=INK_RGB,
        anchor="lm",
    )

    cy = sig_y - cfg["gapSig"]  # 서명 위부터 위로 쌓는다

    # 작은 sub (한 줄, 넘치면 자름)
    sub_f = font(FONT_REG, cfg["sub"])
    sub = truncate(d, spec["subtitle"], sub_f, max_w)
    if sub:
        d.text((x, cy - cfg["sub"]), sub, font=sub_f, fill=DIM_RGB)
        cy = cy - cfg["sub"] - cfg["gapSub"]

    # 굵은 헤드라인 (마지막 줄부터 위로) · [[구절]] = 로즈
    for line in reversed(spec["titleLines"][:4]):
        plain = "".join(t for t, _ in accent_parts(line))
        f = fit_font(d, plain, FONT_BOLD, cfg["head"], max_w, cfg["headMin"])
        draw_accent_line(d, x, cy - f.size, line, f, INK_RGB, ACCENT_RGB)
        cy = cy - f.size - cfg["lineGap"]

    # kicker (accent eyebrow + 점)
    cy = cy - cfg["gapKick"]
    k = cfg["kick"]
    dot = int(k * 0.42)
    ky = cy - k
    center = ky + int(k * 0.55)
    d.ellipse((x, center - dot // 2, x + dot, center + dot // 2), fill=ACCENT_RGB)
    d.text((x + dot + int(k * 0.5), ky), spec["kicker"].upper(), font=font(FONT_BOLD, k), fill=ACCENT_RGB)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=cfg["q"], optimize=True)
    print(f"[render] {out.name} {out.stat().st_size:,} B")


COVER_CFG = {
    "x": 210,
    "marginB": 210,
    "scrimL": 96,
    "scrimB": 235,
    "avatar": 136,
    "brand": 100,
    "gapAv": 36,
    "gapSig": 66,
    "sub": 60,
    "gapSub": 42,
    "head": 150,
    "headMin": 92,
    "lineGap": 28,
    "gapKick": 40,
    "kick": 54,
    "q": 89,
}
# 1280x720 (팟빵 + 유튜브 썸네일·정적영상 규격, 16:9). 픽셀 값은 옛 1920x1080 튜닝을 2/3 스케일.
# scrimL/scrimB 는 알파 강도(0~255)라 스케일하지 않는다.
STATIC_CFG = {
    "x": 75,
    "marginB": 57,
    "scrimL": 120,
    "scrimB": 185,
    "avatar": 48,
    "brand": 35,
    "gapAv": 13,
    "gapSig": 27,
    "sub": 23,
    "gapSub": 16,
    "head": 60,
    "headMin": 36,
    "lineGap": 11,
    "gapKick": 17,
    "kick": 20,
    "q": 91,
}


def draw_static(meta: dict, src: Path, out: Path) -> None:
    draw_frame(meta, src, out, 1280, 720, STATIC_CFG)


def draw_cover(meta: dict, src: Path, out: Path) -> None:
    draw_frame(meta, src, out, 3000, 3000, COVER_CFG)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render podcast episode static images")
    parser.add_argument("--episode", required=True, help="Episode folder name")
    args = parser.parse_args(argv)

    ep_dir = EPISODES_DIR / args.episode
    meta = load_episode(ep_dir)
    spec = visual_spec(meta)
    src = resolve_episode_path(ep_dir, spec["source"])
    if not src.exists():
        raise SystemExit(f"[render] source missing: {src}")

    static = meta.get("staticImage") or meta.get("thumbnail") or {}
    image = meta.get("image") or {}
    static_out = resolve_episode_path(ep_dir, str(static.get("source") or "static-video.jpg"))
    cover_out = resolve_episode_path(ep_dir, str(image.get("source") or "cover.jpg"))

    draw_static(meta, src, static_out)
    draw_cover(meta, src, cover_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
