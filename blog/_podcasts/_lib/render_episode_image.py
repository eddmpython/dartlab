"""Render podcast episode still images from one reusable source artwork.

The renderer keeps the source image reusable and creates two derived assets:
  - static-video.jpg: 16:9 still image for video and thumbnail surfaces
  - cover.jpg: square RSS artwork for podcast directories
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
    MUTED_RGB,
    accent_parts,
)
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

LIB_DIR = Path(__file__).resolve().parent
PODCAST_DIR = LIB_DIR.parent
EPISODES_DIR = PODCAST_DIR / "episodes"

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"

# 카드 팔레트 미러(card_style): INK=본문, DIM=부제, MUTED=풋터, ACCENT=로즈 강조.
INK = INK_RGB
DIM = MUTED_RGB
MUTED = DIM_RGB
ACCENT = ACCENT_RGB
BG = BG_RGB


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
            d.line([(x, 0), (x, height)], fill=(BG[0], BG[1], BG[2], a))
    for y in range(height):
        t = max(0.0, (y - height * 0.42) / (height * 0.58))
        a = int(bottom_strength * (t**1.35))
        if a:
            d.line([(0, y), (width, y)], fill=(BG[0], BG[1], BG[2], a))
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
    episode_no = int(meta.get("episodeNo") or 0)
    return {
        "source": str(visual.get("source") or "assets/source-gray.webp"),
        "kicker": str(visual.get("kicker") or f"EP.{episode_no:02d} · DartLab Podcast"),
        "titleLines": [str(x) for x in (visual.get("titleLines") or [str(meta.get("title") or "")]) if str(x).strip()],
        "subtitle": str(visual.get("subtitle") or meta.get("oneLineMessage") or meta.get("summary") or ""),
        "footer": str(visual.get("footer") or "DartLab"),
    }


def draw_label(d: ImageDraw.ImageDraw, x: int, y: int, text: str, scale: float) -> None:
    f = font(FONT_BOLD, round(30 * scale))
    d.rounded_rectangle(
        [x, y, x + round(d.textlength(text, font=f)) + round(32 * scale), y + round(50 * scale)],
        radius=round(6 * scale),
        fill=(18, 22, 25),
        outline=(72, 80, 86),
        width=max(1, round(1 * scale)),
    )
    d.text((x + round(16 * scale), y + round(9 * scale)), text, fill=ACCENT, font=f)


def draw_static(meta: dict, src: Path, out: Path) -> None:
    width, height = 1920, 1080
    spec = visual_spec(meta)
    img = add_scrim(editorial_background(src, width, height), 120, 165)
    d = ImageDraw.Draw(img)

    x = 128
    max_w = 1000
    d.line([(x, 145), (x, 845)], fill=(142, 153, 160), width=4)
    draw_label(d, x + 26, 144, spec["kicker"], 1.0)

    y = 284
    for idx, line in enumerate(spec["titleLines"][:4]):
        size = 100 if idx < 3 else 82
        plain = "".join(t for t, _ in accent_parts(line))
        f = fit_font(d, plain, FONT_BOLD, size, max_w, 58)
        draw_accent_line(d, x + 26, y, line, f, INK, ACCENT)
        y += f.size + 24

    sub_f = font(FONT_REG, 36)
    sub = truncate(d, spec["subtitle"], sub_f, max_w)
    d.text((x + 30, y + 22), sub, fill=DIM, font=sub_f)

    foot_f = font(FONT_REG, 25)
    d.text((x + 30, height - 118), spec["footer"], fill=MUTED, font=foot_f)
    d.text((width - 128, height - 118), "dartlab", fill=INK, font=font(FONT_BOLD, 26), anchor="ra")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=91, optimize=True)
    print(f"[render] static {out} {out.stat().st_size:,} B")


def draw_cover(meta: dict, src: Path, out: Path) -> None:
    width, height = 3000, 3000
    spec = visual_spec(meta)
    img = add_scrim(editorial_background(src, width, height), 96, 225)
    d = ImageDraw.Draw(img)

    x = 220
    y = 1500
    max_w = width - 440
    draw_label(d, x, y - 170, spec["kicker"], 1.35)
    for idx, line in enumerate(spec["titleLines"][:4]):
        size = 150 if idx < 3 else 124
        plain = "".join(t for t, _ in accent_parts(line))
        f = fit_font(d, plain, FONT_BOLD, size, max_w, 82)
        draw_accent_line(d, x, y, line, f, INK, ACCENT)
        y += f.size + 36

    sub_f = font(FONT_REG, 58)
    sub = truncate(d, spec["subtitle"], sub_f, max_w)
    d.text((x, y + 52), sub, fill=DIM, font=sub_f)
    d.text((x, height - 270), spec["footer"], fill=MUTED, font=font(FONT_REG, 42))
    d.text((width - 220, height - 270), "dartlab", fill=INK, font=font(FONT_BOLD, 46), anchor="ra")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=89, optimize=True)
    print(f"[render] cover {out} {out.stat().st_size:,} B")


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
