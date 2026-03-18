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


@dataclass
class PostAudit:
    path: str
    title: str
    category: str
    series: str
    word_count: int
    svg_count: int
    faq: bool
    checklist_heading: bool
    internal_links: int
    external_links: int
    h2_count: int


@dataclass
class SvgAudit:
    path: str
    size_bytes: int
    view_box: str
    text_nodes: int
    color_count: int
    parse_error: str | None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def is_internal_link(target: str) -> bool:
    if target.startswith(("http://", "https://", "//")):
        return False
    return target.startswith(("/blog/", "/docs/", "/", "./", "../"))


def audit_posts(blog_root: Path) -> list[PostAudit]:
    rows: list[PostAudit] = []
    for file in sorted(blog_root.glob(POST_GLOB)):
        raw = file.read_text(encoding="utf-8")
        body = strip_frontmatter(raw)
        headings = re.findall(r"^##\s+(.+)$", body, re.M)
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", body)
        internal_links = [target for target in links if is_internal_link(target)]
        external_links = [target for target in links if target.startswith(("http://", "https://"))]
        rows.append(
            PostAudit(
                path=file.relative_to(blog_root).as_posix(),
                title=frontmatter_value(raw, "title"),
                category=frontmatter_value(raw, "category"),
                series=frontmatter_value(raw, "series"),
                word_count=plain_word_count(body),
                svg_count=len(re.findall(r"!\[[^\]]*\]\(\./assets/[^)]+\.svg\)", body)),
                faq=any(heading.strip().lower() in {"faq", "자주 묻는 질문"} for heading in headings),
                checklist_heading=any("체크리스트" in heading or "checklist" in heading.lower() for heading in headings),
                internal_links=len(internal_links),
                external_links=len(external_links),
                h2_count=len(headings),
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
        "low_svg_posts": [row.path for row in posts if row.svg_count < LOW_SVG_COUNT],
        "missing_faq": [row.path for row in posts if not row.faq],
        "missing_checklist_heading": [row.path for row in posts if not row.checklist_heading],
        "low_internal_links": [row.path for row in posts if row.internal_links < LOW_INTERNAL_LINKS],
        "svg_parse_errors": [row.path for row in svgs if row.parse_error],
        "svg_low_text_density": [row.path for row in svgs if not row.parse_error and row.text_nodes < LOW_SVG_TEXT_NODES],
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
    print(f"- low svg posts (<{LOW_SVG_COUNT}): {len(summary['low_svg_posts'])}")
    print(f"- missing faq: {len(summary['missing_faq'])}")
    print(f"- missing checklist heading: {len(summary['missing_checklist_heading'])}")
    print(f"- low internal links (<{LOW_INTERNAL_LINKS}): {len(summary['low_internal_links'])}")
    print(f"- svg parse errors: {len(summary['svg_parse_errors'])}")
    print(f"- svg low text density (<{LOW_SVG_TEXT_NODES} text nodes): {len(summary['svg_low_text_density'])}")

    print("\nTop repeated H2")
    for item in summary["top_repeated_h2"]:
        print(f"- {item['heading']}: {item['count']}")

    print("\nPriority review")
    for path in summary["low_svg_posts"][:5]:
        print(f"- low svg: {path}")
    for path in summary["svg_parse_errors"][:5]:
        print(f"- svg parse error: {path}")
    for path in summary["short_posts"][:10]:
        print(f"- short post: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit blog posts and SVG assets.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print the full report as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    blog_root = repo_root() / "blog"
    report = build_report(blog_root)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print_human(report)


if __name__ == "__main__":
    main()
