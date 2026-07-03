from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

POST_GLOB = "*/*/index.md"
SVG_GLOB = "*/*/assets/*.svg"
SHORT_POST_WORDS = 1200
LOW_SVG_COUNT = 4
LOW_INTERNAL_LINKS = 3
LOW_SVG_TEXT_NODES = 4
HIGH_TEMPLATE_REPETITION = 0.5

# 심층 리포트 깊이 게이트 (본문 기준: 표·SVG·코드 제외한 읽는 글자수).
# 길이는 막·증거·시나리오의 산물이지 패딩이 아니다 (반복도 가드와 짝).
DEEP_GENRE_CATEGORIES = {"company-reports"}
DEEP_MIN_PROSE_CHARS = 14000  # 미만 = 얕음, 깊이 보강 리라이트 후보
DEEP_TARGET_PROSE_CHARS = 20000  # 심층 완성 목표 (최고작 티어, 북극성)


@dataclass
class PostAudit:
    path: str
    title: str
    category: str
    series: str
    word_count: int
    prose_chars: int
    svg_count: int
    faq: bool
    checklist_heading: bool
    internal_links: int
    external_links: int
    h2_count: int
    template_repetition_score: float


@dataclass
class SvgAudit:
    path: str
    size_bytes: int
    view_box: str
    text_nodes: int
    color_count: int
    parse_error: str | None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def strip_frontmatter(raw: str) -> str:
    return re.sub(r"^---\n[\s\S]*?\n---\n", "", raw, count=1)


def frontmatter_value(raw: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.M)
    return match.group(1).strip() if match else ""


def plain_word_count(text: str) -> int:
    without_code = re.sub(r"```[\s\S]*?```", " ", text)
    without_images = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", without_code)
    without_links = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", without_images)
    plain = re.sub(r"[#>*`|_\-]", " ", without_links)
    plain = re.sub(r"\s+", " ", plain).strip()
    return len(plain.split()) if plain else 0


def prose_char_count(text: str) -> int:
    """읽는 본문의 글자수 (공백 제외). 표(| … |)·SVG·코드·HTML 태그는 데이터라 제외 =
    문장 깊이의 정직한 지표. 길이 패딩을 막으려 반복도 가드와 함께 쓴다."""
    body = re.sub(r"```[\s\S]*?```", " ", text)
    body = re.sub(r"<svg[\s\S]*?</svg>", " ", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = "\n".join(line for line in body.splitlines() if not line.strip().startswith("|"))
    return len(re.sub(r"\s", "", body))


def is_internal_link(target: str) -> bool:
    if target.startswith(("http://", "https://", "//")):
        return False
    return target.startswith(("/blog/", "/docs/", "/", "./", "../"))


def _compute_top_repeated(blog_root: Path, topN: int = 20) -> set[str]:
    """Pre-scan all posts to find the top-N most repeated H2 headings."""
    counter: Counter[str] = Counter()
    for file in sorted(blog_root.glob(POST_GLOB)):
        raw = file.read_text(encoding="utf-8")
        body = strip_frontmatter(raw)
        counter.update(h.strip() for h in re.findall(r"^##\s+(.+)$", body, re.M))
    return {heading for heading, _ in counter.most_common(topN)}


def audit_posts(blog_root: Path) -> list[PostAudit]:
    top20 = _compute_top_repeated(blog_root, 20)
    rows: list[PostAudit] = []
    for file in sorted(blog_root.glob(POST_GLOB)):
        raw = file.read_text(encoding="utf-8")
        body = strip_frontmatter(raw)
        headings = [h.strip() for h in re.findall(r"^##\s+(.+)$", body, re.M)]
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", body)
        internal_links = [target for target in links if is_internal_link(target)]
        external_links = [target for target in links if target.startswith(("http://", "https://"))]
        repetition = sum(1 for h in headings if h in top20) / len(headings) if headings else 0.0
        rows.append(
            PostAudit(
                path=file.relative_to(blog_root).as_posix(),
                title=frontmatter_value(raw, "title"),
                category=frontmatter_value(raw, "category"),
                series=frontmatter_value(raw, "series"),
                word_count=plain_word_count(body),
                prose_chars=prose_char_count(body),
                svg_count=len(re.findall(r"!\[[^\]]*\]\(\./assets/[^)]+\.svg\)", body)),
                faq=any(heading.lower() in {"faq", "자주 묻는 질문"} for heading in headings),
                checklist_heading=any(
                    "체크리스트" in heading or "checklist" in heading.lower() for heading in headings
                ),
                internal_links=len(internal_links),
                external_links=len(external_links),
                h2_count=len(headings),
                template_repetition_score=round(repetition, 3),
            )
        )
    return rows


def audit_svgs(blog_root: Path) -> list[SvgAudit]:
    rows: list[SvgAudit] = []
    for file in sorted(blog_root.glob(SVG_GLOB)):
        raw = file.read_text(encoding="utf-8")
        parse_error: str | None = None
        view_box = ""
        text_nodes = 0
        try:
            root = ET.fromstring(raw)
            view_box = root.attrib.get("viewBox", "")
            for element in root.iter():
                if element.tag.split("}")[-1] == "text":
                    text_nodes += 1
        except ET.ParseError as exc:
            parse_error = str(exc)
        colors = set(re.findall(r"#[0-9A-Fa-f]{6}", raw))
        rows.append(
            SvgAudit(
                path=file.relative_to(blog_root).as_posix(),
                size_bytes=file.stat().st_size,
                view_box=view_box,
                text_nodes=text_nodes,
                color_count=len(colors),
                parse_error=parse_error,
            )
        )
    return rows


def repeated_headings(blog_root: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    for file in sorted(blog_root.glob(POST_GLOB)):
        raw = file.read_text(encoding="utf-8")
        body = strip_frontmatter(raw)
        counter.update(heading.strip() for heading in re.findall(r"^##\s+(.+)$", body, re.M))
    return counter


def build_report(blog_root: Path) -> dict[str, object]:
    posts = audit_posts(blog_root)
    svgs = audit_svgs(blog_root)
    headings = repeated_headings(blog_root)

    summary = {
        "post_count": len(posts),
        "svg_count": len(svgs),
        "short_posts": [row.path for row in posts if row.word_count < SHORT_POST_WORDS],
        "shallow_deep_reports": [
            {"path": row.path, "prose_chars": row.prose_chars}
            for row in posts
            if row.category in DEEP_GENRE_CATEGORIES and row.prose_chars < DEEP_MIN_PROSE_CHARS
        ],
        "deep_reports_at_target": [
            row.path
            for row in posts
            if row.category in DEEP_GENRE_CATEGORIES and row.prose_chars >= DEEP_TARGET_PROSE_CHARS
        ],
        "low_svg_posts": [row.path for row in posts if row.svg_count < LOW_SVG_COUNT],
        "missing_faq": [row.path for row in posts if not row.faq],
        "missing_checklist_heading": [row.path for row in posts if not row.checklist_heading],
        "low_internal_links": [row.path for row in posts if row.internal_links < LOW_INTERNAL_LINKS],
        "svg_parse_errors": [row.path for row in svgs if row.parse_error],
        "svg_low_text_density": [
            row.path for row in svgs if not row.parse_error and row.text_nodes < LOW_SVG_TEXT_NODES
        ],
        "high_template_repetition": [
            {"path": row.path, "score": row.template_repetition_score}
            for row in posts
            if row.template_repetition_score >= HIGH_TEMPLATE_REPETITION
        ],
        "top_repeated_h2": [{"heading": heading, "count": count} for heading, count in headings.most_common(10)],
        "series_counts": Counter(row.series for row in posts),
        "category_counts": Counter(row.category for row in posts),
    }

    return {
        "summary": summary,
        "posts": [asdict(row) for row in posts],
        "svgs": [asdict(row) for row in svgs],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    print("Blog Audit")
    print(f"- posts: {summary['post_count']}")
    print(f"- svgs: {summary['svg_count']}")
    print(f"- short posts (<{SHORT_POST_WORDS} words): {len(summary['short_posts'])}")
    deep_total = summary["category_counts"].get("company-reports", 0)
    print(
        f"- shallow deep reports (본문 <{DEEP_MIN_PROSE_CHARS}자): "
        f"{len(summary['shallow_deep_reports'])}/{deep_total}편  "
        f"| 목표(>={DEEP_TARGET_PROSE_CHARS}자) 도달: {len(summary['deep_reports_at_target'])}편"
    )
    print(f"- low svg posts (<{LOW_SVG_COUNT}): {len(summary['low_svg_posts'])}")
    print(f"- missing faq: {len(summary['missing_faq'])}")
    print(f"- missing checklist heading: {len(summary['missing_checklist_heading'])}")
    print(f"- low internal links (<{LOW_INTERNAL_LINKS}): {len(summary['low_internal_links'])}")
    print(f"- svg parse errors: {len(summary['svg_parse_errors'])}")
    print(f"- svg low text density (<{LOW_SVG_TEXT_NODES} text nodes): {len(summary['svg_low_text_density'])}")
    print(f"- high template repetition (>={HIGH_TEMPLATE_REPETITION}): {len(summary['high_template_repetition'])}")

    print("\nTop repeated H2")
    for item in summary["top_repeated_h2"]:
        print(f"- {item['heading']}: {item['count']}")

    print("\nPriority story")
    for path in summary["low_svg_posts"][:5]:
        print(f"- low svg: {path}")
    for path in summary["svg_parse_errors"][:5]:
        print(f"- svg parse error: {path}")
    for path in summary["short_posts"][:10]:
        print(f"- short post: {path}")
    for item in summary["high_template_repetition"][:5]:
        print(f"- high repetition ({item['score']:.1%}): {item['path']}")
    for item in sorted(summary["shallow_deep_reports"], key=lambda x: x["prose_chars"])[:8]:
        print(f"- shallow deep report (본문 {item['prose_chars']}자): {item['path']}")


# ── 발행 하드 게이트 (단일 글) ──
# 형식만 채우면 통과하던 SEO 게이트의 구멍을 막는다. company-reports 심층 리포트는 이 게이트를
# 통과해야 발행한다. 위반 시 exit 1. 기존 글엔 소급 적용 안 함(--gate <폴더>로 신규 글만 검사).
_OG_RE = re.compile(r"^/thumbnails/.+\.webp$")


def publish_gate(post_dir: Path) -> list[str]:
    """단일 글 발행 하드 게이트. 위반 리스트 반환(비면 통과).

    company-reports(심층) 기준으로 (1)실사 OG 카드 (2)실사 hero webp (3)본문 실사 사진 ≥1
    (4)본문 깊이 ≥14,000자 (5)기획 루프 산출물(brief.json)을 강제한다. 손수 SVG·기본 아바타·
    얕은 본문·루프 스킵을 걸러 "형식만 통과"를 차단한다."""
    idx = post_dir / "index.md"
    if not idx.is_file():
        return [f"index.md 없음: {post_dir}"]
    raw = idx.read_text(encoding="utf-8")
    body = strip_frontmatter(raw)
    cat = frontmatter_value(raw, "category")
    fails: list[str] = []
    if cat not in DEEP_GENRE_CATEGORIES:
        return fails  # 심층 카테고리만 하드 게이트

    slug = re.sub(r"^\d+-", "", post_dir.name)
    assets = post_dir / "assets"
    photos = []
    if assets.is_dir():
        for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
            photos += list(assets.glob(ext))

    # 1. 실사 OG 카드 (리스트/공유 미리보기). 기본 아바타 폴백이면 실패.
    og = frontmatter_value(raw, "ogImage").strip().strip("\"'")
    if not _OG_RE.match(og):
        fails.append(
            f"ogImage가 /thumbnails/{slug}.webp 실사 OG가 아님(현재 {og!r}). 기본 아바타 폴백 금지 → render_og_cards 수급"
        )
    else:
        og_file = repo_root() / "landing" / "static" / og.lstrip("/")
        if not og_file.is_file():
            fails.append(f"OG 파일 없음: landing/static{og} (render_og_cards 미실행)")

    # 2. 실사 hero/사진 webp (손수 SVG는 실사 아님)
    if not photos:
        fails.append("assets에 실사 사진 0장(손수 SVG는 실사 아님). gen_blog_cc0/imagePlan 수급 필요")

    # 3. 본문에 실사 사진 markdown 이미지 ≥1
    if not re.search(r"!\[[^\]]*\]\([^)]+\.(?:webp|jpg|jpeg|png)\)", body):
        fails.append("본문 실사 사진 0장(![](*.webp) 필요). 손수 SVG만으론 시각 부실")

    # 4. 깊이 하드 블록
    pc = prose_char_count(body)
    if pc < DEEP_MIN_PROSE_CHARS:
        fails.append(
            f"본문 {pc}자 < 심층 하한 {DEEP_MIN_PROSE_CHARS}자(목표 {DEEP_TARGET_PROSE_CHARS}). blog_plan_loop 막 구조로 심화 필요"
        )

    # 5. 기획 루프 산출물(루프 실행 증거)
    if not (post_dir / "brief.json").is_file() and not (post_dir / "plan.json").is_file():
        fails.append("기획 루프 산출물(brief.json/plan.json) 없음. blog_plan_loop.workflow.js 미실행 의심")

    return fails


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit blog posts and SVG assets.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print the full report as JSON.")
    parser.add_argument("--gate", metavar="POST_DIR", help="단일 글 발행 하드 게이트(위반 시 exit 1).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.gate:
        post_dir = Path(args.gate).resolve()
        fails = publish_gate(post_dir)
        if fails:
            print(f"발행 게이트 실패: {post_dir.name}")
            for f in fails:
                print(f"  ❌ {f}")
            raise SystemExit(1)
        print(f"발행 게이트 통과: {post_dir.name}")
        return
    blog_root = repo_root() / "blog"
    report = build_report(blog_root)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print_human(report)


if __name__ == "__main__":
    main()
