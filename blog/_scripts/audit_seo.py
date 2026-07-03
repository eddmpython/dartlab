"""
블로그 글 SEO 자동 스코어링.
전체 기업이야기 글을 순회하며 SEO 품질을 점수화한다.

사용: uv run python -X utf8 blog/_scripts/audit_seo.py
"""

import os
import re
import sys

try:
    import yaml  # frontmatter 중첩(`carousel:`) 검증. regex 는 중첩 못 읽음
except ImportError:  # pragma: no cover
    yaml = None

BLOG_DIR = "blog/05-company-reports"

# 카드 캐러셀 손글 narration 1줄 권장 최대 길이(슬라이드 가독).
CAROUSEL_NOTE_MAX = 140
# 캐러셀 hero 로 쓸 수 있는 이미지 확장자.
HERO_SUFFIXES = (".webp", ".png", ".jpg", ".jpeg")


def _numbers(text: str) -> set:
    """문자열에서 숫자 토큰(2자리+ 또는 소수) 추출. 콤마 제거한 digit-core. no-new-number 비교용."""
    out = set()
    for m in re.findall(r"\d[\d,]*\.?\d*", str(text)):
        core = m.replace(",", "").rstrip(".")
        if len(core.replace(".", "")) >= 2:  # 한 자리(연도 끝자리 등) 제외. 노이즈
            out.add(core)
    return out


def validate_carousel(folder_path: str) -> list:
    """frontmatter `carousel:` 블록 검증. 구조·hero 존재·노트 길이·no-new-number(노트 숫자⊆본문).

    캐러셀은 ReportModel 자동 투영이 기본이고, `carousel:` 는 *선택* 큐레이션 오버레이라
    없으면 검사 없음(빈 리스트). 손글 narration 이 본문에 없는 숫자를 새로 만들지 않게 가드한다.
    """
    index_path = os.path.join(folder_path, "index.md")
    if not os.path.isfile(index_path) or yaml is None:
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) < 3 or "carousel:" not in parts[1]:
        return []  # carousel 블록 없는 글은 YAML 파싱 안 함(mdsvex 가 허용하는 느슨한 frontmatter 오탐 회피)
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        return [("error", f"carousel 글 frontmatter YAML 파싱 실패: {exc}")]
    spec = fm.get("carousel")
    if spec is None:
        return []

    issues = []
    if not isinstance(spec, dict):
        return [("error", "carousel 은 매핑(dict)이어야 함")]

    body_numbers = _numbers(parts[2])
    assets_dir = os.path.join(folder_path, "assets")

    hero = spec.get("hero")
    if hero is not None:
        if not isinstance(hero, str) or not hero.lower().endswith(HERO_SUFFIXES):
            issues.append(("error", f"carousel.hero 는 이미지 파일명이어야 함: {hero!r}"))
        elif os.path.isdir(assets_dir) and not any(hero in f or f.endswith(hero) for f in os.listdir(assets_dir)):
            issues.append(("warn", f"carousel.hero {hero!r} 가 assets/ 에 없음(hfMedia 직접 게시면 무시)"))

    order = spec.get("order")
    if order is not None and not (isinstance(order, list) and all(isinstance(x, str) for x in order)):
        issues.append(("error", "carousel.order 는 문자열 리스트여야 함"))

    notes = spec.get("notes")
    if notes is not None:
        if not isinstance(notes, dict):
            issues.append(("error", "carousel.notes 는 매핑(key→손글 문장)이어야 함"))
        else:
            for key, line in notes.items():
                if not isinstance(line, str):
                    issues.append(("error", f"carousel.notes[{key}] 는 문자열이어야 함"))
                    continue
                if len(line) > CAROUSEL_NOTE_MAX:
                    issues.append(("warn", f"carousel.notes[{key}] {len(line)}자, {CAROUSEL_NOTE_MAX}자 권장 초과"))
                novel = _numbers(line) - body_numbers
                if novel:
                    issues.append(
                        ("warn", f"carousel.notes[{key}] 본문에 없는 숫자 {sorted(novel)}, no-new-number 위반 의심")
                    )

    # 인스타 포스트 텍스트(제목·캡션·고정댓글) 타입.
    title = spec.get("title")
    if title is not None and not isinstance(title, str):
        issues.append(("error", "carousel.title 은 문자열이어야 함"))
    for key in ("caption", "pinnedComment"):
        val = spec.get(key)
        if val is not None and not isinstance(val, str):
            issues.append(("error", f"carousel.{key} 는 문자열이어야 함"))

    # 손글 편집 슬라이드. layout enum·필수필드·image 타입·no-new-number(슬라이드 숫자⊆본문).
    slides = spec.get("slides")
    if slides is not None:
        if not isinstance(slides, list):
            issues.append(("error", "carousel.slides 는 리스트여야 함"))
        else:
            slide_required = {"editorial": ("line",), "editorialBeat": ("line",), "editorialStat": ("bigNumber",)}
            slide_text = ("kicker", "line", "sub", "bigNumber", "unit", "context")
            for i, sl in enumerate(slides):
                if not isinstance(sl, dict):
                    issues.append(("error", f"carousel.slides[{i}] 는 매핑이어야 함"))
                    continue
                layout = sl.get("layout")
                if layout not in slide_required:
                    issues.append(
                        (
                            "error",
                            f"carousel.slides[{i}].layout 은 editorial|editorialBeat|editorialStat 여야 함: {layout!r}",
                        )
                    )
                    continue
                for req in slide_required[layout]:
                    if not str(sl.get(req, "")).strip():
                        issues.append(("error", f"carousel.slides[{i}]({layout}) 필수 필드 '{req}' 누락"))
                img = sl.get("image")
                if img is not None and not isinstance(img, str):
                    issues.append(("error", f"carousel.slides[{i}].image 는 semantic 파일명(문자열)이어야 함"))
                novel = set()
                for f in slide_text:
                    if sl.get(f) is not None:
                        novel |= _numbers(sl[f]) - body_numbers
                if novel:
                    issues.append(
                        ("warn", f"carousel.slides[{i}] 본문에 없는 숫자 {sorted(novel)}, no-new-number 위반 의심")
                    )
    return issues


FORBIDDEN_PATTERNS = [
    r"~입니다$",  # 존댓말 (블로그 톤 아님)
    r"살펴보겠습니다",
    r"알아보겠습니다",
    r"~하겠습니다$",
    r"분석해 보겠습니다",
]


def score_post(folder_path: str) -> dict:
    """단일 글의 SEO 점수를 산출한다."""
    index_path = os.path.join(folder_path, "index.md")
    if not os.path.isfile(index_path):
        return None

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # frontmatter 분리
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter = parts[1]
    body = parts[2]

    scores = {}
    total = 0
    max_total = 0

    # 1. Frontmatter 완성도 (20점)
    fm_score = 0
    fm_max = 20
    required_fields = ["title", "description", "category", "series", "stockCode", "tags", "ogImage"]
    for field in required_fields:
        if field + ":" in frontmatter:
            fm_score += 2
        else:
            fm_score += 0
    # description 길이
    desc_match = re.search(r'description:\s*"(.+?)"', frontmatter, re.DOTALL)
    if desc_match:
        desc_len = len(desc_match.group(1))
        if 80 <= desc_len <= 200:
            fm_score += 4
        elif desc_len > 200:
            fm_score += 2
        else:
            fm_score += 1
    # tags 개수
    tag_count = frontmatter.count("  - ")
    if tag_count >= 5:
        fm_score += 2
    elif tag_count >= 3:
        fm_score += 1
    scores["frontmatter"] = min(fm_score, fm_max)
    total += scores["frontmatter"]
    max_total += fm_max

    # 2. 본문 길이 (15점). 본문(prose) 기준으로 표·SVG·코드·태그를 뺀 읽는 글자수만 센다.
    prose = re.sub(r"```[\s\S]*?```", " ", body)
    prose = re.sub(r"<svg[\s\S]*?</svg>", " ", prose, flags=re.I)
    prose = re.sub(r"<[^>]+>", " ", prose)
    prose = "\n".join(line for line in prose.splitlines() if not line.strip().startswith("|"))
    body_len = len(re.sub(r"\s", "", prose))
    len_max = 15
    if body_len >= 10000:
        len_score = 15
    elif body_len >= 6000:
        len_score = 12
    elif body_len >= 3500:
        len_score = 8
    else:
        len_score = 3
    scores["length"] = len_score
    scores["length_chars"] = body_len
    total += len_score
    max_total += len_max

    # 3. H2 구조 (15점)
    h2s = re.findall(r"^## (.+)$", body, re.MULTILINE)
    h2_max = 15
    h2_count = len(h2s)
    if 5 <= h2_count <= 15:
        h2_score = 10
    elif h2_count > 15:
        h2_score = 7
    elif h2_count >= 3:
        h2_score = 5
    else:
        h2_score = 2
    # H2에 한국어 포함
    korean_h2 = sum(1 for h in h2s if re.search(r"[가-힣]", h))
    if korean_h2 == h2_count and h2_count > 0:
        h2_score += 5
    elif korean_h2 > h2_count * 0.7:
        h2_score += 3
    scores["h2"] = min(h2_score, h2_max)
    scores["h2_count"] = h2_count
    total += scores["h2"]
    max_total += h2_max

    # 4. 내부 링크 (15점)
    internal_links = re.findall(r"\(/blog/[^)]+\)", body)
    il_max = 15
    il_count = len(internal_links)
    if il_count >= 5:
        il_score = 15
    elif il_count >= 3:
        il_score = 10
    elif il_count >= 1:
        il_score = 5
    else:
        il_score = 0
    scores["internal_links"] = il_score
    scores["internal_links_count"] = il_count
    total += il_score
    max_total += il_max

    # 5. 외부 출처 (10점)
    external_links = re.findall(r"\(https?://[^)]+\)", body)
    el_max = 10
    el_count = len(external_links)
    if el_count >= 5:
        el_score = 10
    elif el_count >= 3:
        el_score = 7
    elif el_count >= 1:
        el_score = 3
    else:
        el_score = 0
    scores["external_links"] = el_score
    scores["external_links_count"] = el_count
    total += el_score
    max_total += el_max

    # 6. 시각 자산 (15점)
    images = re.findall(r"!\[.+?\]\(.+?\)", body)
    svg_count = sum(1 for i in images if ".svg" in i)
    img_count = sum(1 for i in images if ".webp" in i or ".png" in i or ".jpg" in i)
    vis_max = 15
    vis_total = svg_count + img_count
    if vis_total >= 5:
        vis_score = 15
    elif vis_total >= 3:
        vis_score = 10
    elif vis_total >= 1:
        vis_score = 5
    else:
        vis_score = 0
    scores["visuals"] = vis_score
    scores["svg_count"] = svg_count
    scores["img_count"] = img_count
    total += vis_score
    max_total += vis_max

    # 7. dartlab 코드 포함 (10점)
    code_blocks = re.findall(r"```python\n.+?```", body, re.DOTALL)
    code_max = 10
    if len(code_blocks) >= 3:
        code_score = 10
    elif len(code_blocks) >= 1:
        code_score = 5
    else:
        code_score = 0
    scores["code_blocks"] = code_score
    scores["code_count"] = len(code_blocks)
    total += code_score
    max_total += code_max

    scores["total"] = total
    scores["max"] = max_total
    scores["pct"] = round(total / max_total * 100) if max_total > 0 else 0

    # 건강 상태
    if scores["pct"] >= 85:
        scores["health"] = "🟢"
    elif scores["pct"] >= 70:
        scores["health"] = "🟡"
    else:
        scores["health"] = "🔴"

    return scores


def main():
    if not os.path.isdir(BLOG_DIR):
        print(f"디렉토리 없음: {BLOG_DIR}")
        sys.exit(1)

    results = []
    for folder in sorted(os.listdir(BLOG_DIR)):
        fp = os.path.join(BLOG_DIR, folder)
        if not os.path.isdir(fp):
            continue
        s = score_post(fp)
        if s:
            results.append((folder, s))

    # 콘솔 출력
    print(f"\n{'=' * 80}")
    print(f"블로그 SEO 스코어링: {len(results)}편")
    print(f"{'=' * 80}\n")

    print(f"{'글':<45} {'점수':>6} {'건강':>4} {'글자':>7} {'H2':>4} {'링크':>4} {'SVG':>4} {'IMG':>4} {'코드':>4}")
    print("-" * 90)

    for folder, s in results:
        name = folder[:44]
        print(
            f"{name:<45} {s['pct']:>5}% {s['health']:>4} {s['length_chars']:>6} {s['h2_count']:>4} {s['internal_links_count']:>4} {s['svg_count']:>4} {s['img_count']:>4} {s['code_count']:>4}"
        )

    # 약한 글 경고
    weak = [(f, s) for f, s in results if s["pct"] < 70]
    if weak:
        print(f"\n⚠️ 리라이트 후보 ({len(weak)}편):")
        for f, s in weak:
            issues = []
            if s["internal_links_count"] < 3:
                issues.append(f"내부링크 {s['internal_links_count']}개")
            if s["svg_count"] + s["img_count"] < 3:
                issues.append(f"시각자산 {s['svg_count'] + s['img_count']}개")
            if s["length_chars"] < 8000:
                issues.append(f"글자수 {s['length_chars']}")
            print(f"  🔴 {f}: {s['pct']}%: {', '.join(issues)}")

    print(f"\n평균: {sum(s['pct'] for _, s in results) // len(results)}%")

    # 카드 캐러셀 큐레이션 검증. `carousel:` 블록 있는 글만.
    car_issues = []
    for folder in sorted(os.listdir(BLOG_DIR)):
        fp = os.path.join(BLOG_DIR, folder)
        if os.path.isdir(fp):
            for level, msg in validate_carousel(fp):
                car_issues.append((folder, level, msg))
    if car_issues:
        errs = [c for c in car_issues if c[1] == "error"]
        print(f"\n🎠 캐러셀 검증: {len(car_issues)}건 ({len(errs)} error):")
        for folder, level, msg in car_issues:
            mark = "🔴" if level == "error" else "🟡"
            print(f"  {mark} {folder}: {msg}")
        if errs:
            sys.exit(1)
    elif yaml is not None:
        print("🎠 캐러셀 검증: carousel: 블록 없음(자동 투영만) 또는 0 이슈.")


if __name__ == "__main__":
    main()
