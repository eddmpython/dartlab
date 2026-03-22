"""
블로그 포스트 035~094의 깨진 SVG 5개를 다크 테마로 재생성하는 스크립트.
각 포스트에 decision-tree, evidence-layer, good-vs-risky-matrix, reading-flow, watchboard 5개 SVG를 생성.
"""

import os
import re
from pathlib import Path

BLOG_ROOT = Path(__file__).parent.parent / "blog"

# 카테고리별 accent 색상
CAT_COLORS = {
    "01-disclosure-systems": {"accent": "#fb923c", "accentDim": "rgba(251,146,60,0.12)", "label": "공시 시스템"},
    "02-report-reading": {"accent": "#38bdf8", "accentDim": "rgba(56,189,248,0.12)", "label": "사업보고서 읽기"},
    "03-financial-interpretation": {"accent": "#a78bfa", "accentDim": "rgba(167,139,250,0.12)", "label": "재무 해석"},
    "04-data-automation": {"accent": "#34d399", "accentDim": "rgba(52,211,153,0.12)", "label": "데이터 자동화"},
}

# SVG 타입별 부제목과 아이콘 힌트
SVG_TYPES = {
    "decision-tree": {"subtitle": "판단 흐름도", "icon": "◇"},
    "evidence-layer": {"subtitle": "근거 레이어", "icon": "▤"},
    "good-vs-risky-matrix": {"subtitle": "양호 vs 위험", "icon": "◐"},
    "reading-flow": {"subtitle": "읽기 순서", "icon": "→"},
    "watchboard": {"subtitle": "감시 보드", "icon": "▣"},
}


def get_post_info(post_dir: Path):
    """index.md에서 title과 번호를 추출."""
    index_md = post_dir / "index.md"
    if not index_md.exists():
        return None
    text = index_md.read_text(encoding="utf-8-sig")
    title_match = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
    if not title_match:
        return None
    title = title_match.group(1).strip()
    slug = post_dir.name
    num = slug.split("-")[0]
    return {"num": num, "title": title, "slug": slug}


def truncate_title(title: str, max_len: int = 28) -> list[str]:
    """긴 제목을 2줄로 분할."""
    if len(title) <= max_len:
        return [title]
    # 자연스러운 분할점 찾기
    for sep in ["은 ", "는 ", "이 ", "가 ", "를 ", "을 ", "와 ", "과 ", " 때 ", "에서 "]:
        idx = title.find(sep, max_len // 2)
        if 0 < idx < len(title) - 3:
            return [title[: idx + len(sep)].rstrip(), title[idx + len(sep) :]]
    # 강제 분할
    mid = len(title) // 2
    space = title.rfind(" ", 0, mid + 5)
    if space > 0:
        return [title[:space], title[space + 1 :]]
    return [title[:max_len], title[max_len:]]


def generate_svg(post_info: dict, svg_type: str, cat_colors: dict) -> str:
    """다크 테마 SVG 생성."""
    num = post_info["num"]
    title = post_info["title"]
    accent = cat_colors["accent"]
    accent_dim = cat_colors["accentDim"]
    cat_label = cat_colors["label"]
    type_info = SVG_TYPES[svg_type]
    subtitle = type_info["subtitle"]
    icon = type_info["icon"]

    title_lines = truncate_title(title)
    title_y1 = 200 if len(title_lines) == 1 else 188
    title_svg = ""
    for i, line in enumerate(title_lines):
        y = title_y1 + i * 28
        title_svg += f'  <text x="400" y="{y}" text-anchor="middle" font-family="Pretendard, Inter, sans-serif" font-size="20" font-weight="700" fill="#f1f5f9">{_esc(line)}</text>\n'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420" fill="none">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#050811"/>
      <stop offset="100%" stop-color="#0f1219"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="800" height="420" rx="12" fill="url(#bg)"/>
  <rect x="0.5" y="0.5" width="799" height="419" rx="12" stroke="#1e2433" stroke-width="1" fill="none"/>

  <!-- Category badge -->
  <rect x="300" y="60" width="200" height="26" rx="13" fill="{accent_dim}" stroke="{accent}" stroke-width="1" opacity="0.8"/>
  <text x="400" y="78" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="11" font-weight="600" fill="{accent}" letter-spacing="0.04em">{_esc(cat_label)}</text>

  <!-- Post number -->
  <text x="400" y="120" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="42" font-weight="800" fill="{accent}" opacity="0.15">{num}</text>

  <!-- Title -->
{title_svg}
  <!-- Divider -->
  <line x1="340" y1="240" x2="460" y2="240" stroke="{accent}" stroke-width="1.5" opacity="0.4"/>

  <!-- SVG type icon + subtitle -->
  <text x="380" y="278" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="24" fill="{accent}" opacity="0.6">{icon}</text>
  <text x="420" y="278" text-anchor="middle" font-family="Pretendard, Inter, sans-serif" font-size="14" fill="#94a3b8">{_esc(subtitle)}</text>

  <!-- DartLab branding -->
  <text x="400" y="380" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#475569" letter-spacing="0.08em">DartLab 전자공시 분석</text>
</svg>'''


def _esc(s: str) -> str:
    """XML escape."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    regenerated = 0
    for cat_dir in sorted(BLOG_ROOT.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_name = cat_dir.name
        if cat_name not in CAT_COLORS:
            continue
        colors = CAT_COLORS[cat_name]

        for post_dir in sorted(cat_dir.iterdir()):
            if not post_dir.is_dir():
                continue
            slug = post_dir.name
            # 035~094 범위만
            try:
                post_num = int(slug.split("-")[0])
            except ValueError:
                continue
            if not (35 <= post_num <= 94):
                continue

            info = get_post_info(post_dir)
            if not info:
                continue

            assets_dir = post_dir / "assets"
            assets_dir.mkdir(exist_ok=True)

            for svg_type in SVG_TYPES:
                filename = f"{info['num']}-{svg_type}.svg"
                filepath = assets_dir / filename
                svg_content = generate_svg(info, svg_type, colors)
                filepath.write_text(svg_content, encoding="utf-8")
                regenerated += 1

    print(f"재생성 완료: {regenerated}개 SVG")


if __name__ == "__main__":
    main()
