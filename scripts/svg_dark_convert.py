"""SVG 라이트→다크 테마 변환 스크립트.

사용법:
  uv run python scripts/svg_dark_convert.py <svg_file_or_directory>

글 단위 변환:
  uv run python scripts/svg_dark_convert.py blog/03-financial-interpretation/115-ifrs18-income-statement-changes/assets/
"""
import re
import sys
from pathlib import Path


# ── 색상 매핑 ──────────────────────────────────────────────
# 배경/카드 (fill 속성에서만 교체)
BG_MAP = {
    "#f8fafc": "#0f1219",
}

# 하이라이트 배경 (fill 속성에서만)
HIGHLIGHT_MAP = {
    "#eff6ff": "rgba(37,99,235,0.15)",
    "#ecfdf5": "rgba(5,150,105,0.15)",
    "#fef2f2": "rgba(220,38,38,0.15)",
    "#fef3c7": "rgba(245,158,11,0.12)",
    "#fffbeb": "rgba(245,158,11,0.15)",
    "#fff7ed": "rgba(234,88,12,0.15)",
    "#f5f3ff": "rgba(124,58,237,0.15)",
}

# 구분선 (stroke 속성에서)
STROKE_MAP = {
    "#e5e7eb": "#2d3748",
    "#e2e8f0": "#2d3748",
}

# 텍스트 색상 (fill 속성에서, text 요소 안에서만)
TEXT_MAP = {
    "#1e293b": "#e2e8f0",
    "#374151": "#e2e8f0",
}


def is_text_context(line: str) -> bool:
    """text 요소 안의 fill인지 판별."""
    return "<text " in line or "font-family" in line or "font-size" in line


def is_card_fill(line: str, color: str) -> bool:
    """fill="#fff"가 카드 배경인지 (텍스트가 아닌) 판별."""
    if color not in ("#fff", "#ffffff", "white"):
        return False
    # rect, circle 등 도형 요소의 fill이면 카드
    if any(tag in line for tag in ("<rect ", "<circle ", "<ellipse ", "<path ")):
        return True
    # text 요소의 fill이면 텍스트 (건드리지 않음)
    if "<text " in line or "font-" in line:
        return False
    # polygon (화살표 등)은 건드리지 않음
    if "<polygon " in line:
        return False
    return False


def convert_line(line: str) -> str:
    """한 줄을 다크 테마로 변환."""
    result = line

    # 1. 배경색 변환
    for light, dark in BG_MAP.items():
        result = result.replace(f'fill="{light}"', f'fill="{dark}"')

    # 2. 카드 배경 (#fff → #1a2233) — 도형 요소에서만
    if is_card_fill(result, "#fff"):
        result = result.replace('fill="#fff"', 'fill="#1a2233"')
    if is_card_fill(result, "#ffffff"):
        result = result.replace('fill="#ffffff"', 'fill="#1a2233"')

    # 3. 하이라이트 배경
    for light, dark in HIGHLIGHT_MAP.items():
        result = result.replace(f'fill="{light}"', f'fill="{dark}"')

    # 4. 텍스트 색상 — text 요소에서만
    if is_text_context(result):
        for light, dark in TEXT_MAP.items():
            result = result.replace(f'fill="{light}"', f'fill="{dark}"')

    # 5. 구분선 stroke
    for light, dark in STROKE_MAP.items():
        result = result.replace(f'stroke="{light}"', f'stroke="{dark}"')

    # 6. 강한 구분선 반전 (stroke="#1e293b" on line 요소)
    if "<line " in result and 'stroke="#1e293b"' in result:
        result = result.replace('stroke="#1e293b"', 'stroke="#e2e8f0"')

    return result


def add_border(lines: list[str]) -> list[str]:
    """배경 rect 다음에 border rect 추가 (없으면)."""
    result = []
    for i, line in enumerate(lines):
        result.append(line)
        # 배경 rect (첫 번째 rect로 fill="#0f1219") 찾기
        if 'fill="#0f1219"' in line and "<rect " in line and "stroke" not in line:
            # viewBox에서 크기 추출
            for prev in lines[:i]:
                vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', prev)
                if vb:
                    w, h = int(vb.group(1)), int(vb.group(2))
                    # rx 추출
                    rx_match = re.search(r'rx="(\d+)"', line)
                    rx = rx_match.group(1) if rx_match else "12"
                    border = f'  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{rx}" stroke="#1e2433" stroke-width="1" fill="none"/>\n'
                    # 이미 border가 있는지 확인
                    if i + 1 < len(lines) and "#1e2433" in lines[i + 1]:
                        break
                    result.append(border)
                    break
    return result


def convert_svg(path: Path) -> bool:
    """SVG 파일을 다크 테마로 변환. 변경되면 True."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(True)

    # 이미 다크 테마인지 확인
    if "#0f1219" in content or "#050811" in content:
        return False

    # 밝은 배경이 없으면 스킵
    if "#f8fafc" not in content and '#fff"' not in content:
        return False

    # 줄 단위 변환
    converted = [convert_line(line) for line in lines]

    # border 추가
    converted = add_border(converted)

    new_content = "".join(converted)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python svg_dark_convert.py <file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("*.svg"))
    else:
        print(f"Not found: {target}")
        sys.exit(1)

    changed = 0
    skipped = 0
    for f in files:
        try:
            if convert_svg(f):
                print(f"  ✓ {f.name}")
                changed += 1
            else:
                print(f"  - {f.name} (skip)")
                skipped += 1
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")

    print(f"\n변환: {changed}개, 스킵: {skipped}개")


if __name__ == "__main__":
    main()
