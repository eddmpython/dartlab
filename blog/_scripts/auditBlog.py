from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from blogMedia import ASSET_KEY_RE, SHA256_RE, loadMediaCatalog, loadMediaManifest, mediaPath, mediaUrl

POST_GLOB = "*/*/index.md"
SVG_GLOB = "*/*/assets/*.svg"
SHORT_POST_WORDS = 1200
LOW_SVG_COUNT = 4
LOW_INTERNAL_LINKS = 3
LOW_SVG_TEXT_NODES = 4
HIGH_TEMPLATE_REPETITION = 0.5

# 심층 콘텐츠 깊이 게이트 (본문 기준: 표·SVG·코드 제외한 읽는 글자수).
# 길이는 막·증거·시나리오의 산물이지 패딩이 아니다 (반복도 가드와 짝).
BLOG_CATEGORIES = {
    "reading-disclosures",
    "dartlab-news",
    "dartlab-stories",
    "credit-reports",
    "company-reports",
    "data-reports",
    "industry-map",
    "tech-story",
    "investment-stories",
}
CONTENT_GENRE_CATEGORIES = {
    "company-reports",
    "tech-story",
    "data-reports",
    "investment-stories",
    "dartlab-stories",
}
# 심층 = 6 막 인과 서사 장르. dartlab 이야기는 교육 연재라 막이 아니라 단계로 간다.
DEEP_GENRE_CATEGORIES = CONTENT_GENRE_CATEGORIES - {"dartlab-stories"}
GENRE_MIN_PROSE_CHARS = {
    "company-reports": 14000,
    "tech-story": 6000,
    "data-reports": 4000,
    "investment-stories": 5000,
    "dartlab-stories": 3000,
}
GENRE_TARGET_PROSE_CHARS = {
    "company-reports": 20000,
    "tech-story": 9000,
    "data-reports": 6500,
    "investment-stories": 8000,
    "dartlab-stories": 5000,
}

# 장르별 기획 산출물 최소 구조. 6 막 인과는 회사·기술·시장 글의 골격이지 교육 연재의 골격이 아니다.
# dartlab 이야기의 이미지는 기획이 정한 만큼만 만든다. 그래서 하한이 1 이고, 실물 개수는
# imagePlan 길이가 정한다(publish_gate 가 그 정합을 본다).
_DEFAULT_PLAN_SHAPE = {"acts": 6, "visuals": 3, "images": 3}
GENRE_PLAN_SHAPE = {"dartlab-stories": {"acts": 3, "visuals": 1, "images": 1}}
DEEP_MIN_PROSE_CHARS = GENRE_MIN_PROSE_CHARS["company-reports"]
DEEP_TARGET_PROSE_CHARS = GENRE_TARGET_PROSE_CHARS["company-reports"]
BLOG_REVIEW_SCORE_MIN = 92
BLOG_LOOP_WORKFLOW_NAME = "blog_plan_loop.workflow.js"
BLOG_PLAN_CONTRACT_VERSION = 2
PLAN_CANDIDATE_FILES = ("brief.json", "plan.json")
BLOG_REQUIRED_PLAN_FIELDS = (
    "titleContract",
    "readerQuestion",
    "insight",
    "acts",
    "sections",
    "visuals",
    "imagePlan",
    "relatedPosts",
    "honestyGuards",
    "evidenceMap",
)
DARTLAB_TITLE_FORBIDDEN_RE = re.compile(r"무엇\s*인가|사용법|총정리|정리$|하는\s*법|꺼내는\s*법|호출\s*방법|소개")
DARTLAB_TITLE_SEARCH_RE = re.compile(
    r"DART|EDGAR|공시|재무제표|사업보고서|손익계산서|재무상태표|현금흐름표|계정|데이터",
    re.I,
)
DARTLAB_TITLE_ACTION_RE = re.compile(r"설치|파이썬|코드|브라우저|한\s*줄|조회|불러오|실행|시작|열기|분석")
DARTLAB_CONCRETE_ANCHOR_RE = re.compile(
    r"```python|!\[[^\]]*\]\([^)]+\)|"
    r"`[^`]*(?:Company|panel|scan|analysis|credit|story|market|head|005930|AAPL|IS|BS|CF)[^`]*`|"
    r"Company\(|panel\(|scan\(|analysis\(|credit\(|story\(|market|"
    r"005930|AAPL|[0-9]{4}Q[1-4]|[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:조원|억원|만원|원|달러|USD|%p?|배)?|"
    r"매출|매출액|매출원가|매출총이익|매출채권|영업이익|순이익|자산|부채|자본|현금흐름|"
    r"영업활동현금흐름|재고|재고자산|차입|주석|사업|임원|직원|숫자|단위|빈\s*결과|후보|검색|"
    r"시세|뉴스|수급|최신\s*공시|공시\s*알림|"
    r"제품|원재료|생산설비|공급처|부문|가동|생산능력|business|products|materials|facilities|"
    r"목차|절|블록|문단|head\(|text|table|DART|EDGAR|코드|셀|출력\s*표|DataFrame|테이블|값|계정|기간",
    re.I,
)
COMMON_CONCRETE_ANCHOR_RE = re.compile(
    r"```|!\[[^\]]*\]\([^)]+\)|\|.+\||"
    r"DART|EDGAR|dartlab|Company|panel|scan|analysis|credit|story|market|공시|사업보고서|10-K|10-Q|"
    r"[0-9]{4}Q[1-4]|20[0-9]{2}|[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:조원|억원|만원|원|달러|USD|%p?|배|%|명|건|척|대)?|"
    r"매출|매출액|영업이익|순이익|자산|부채|자본|현금흐름|원가|마진|수주|수주잔고|"
    r"제품|고객|사업부|부문|공정|장비|소재|원재료|생산|가동률|생산능력|"
    r"주가|시가총액|거래량|외국인|기관|개인|금리|환율|물가|지지선|저항선|이동평균|RSI|MACD|"
    r"표|차트|그래프|이미지|도식|코드|계정|기간|값|숫자|검증표",
    re.I,
)
DARTLAB_ACTION_RE = re.compile(
    r"열|넣|누르|실행|확인|찾|고르|좁히|나누|빼|바꾸|비교|적|돌리|꺼내|만들|계산|입력|"
    r"보이|보는|본다|읽|익히|배우|구분|시작|풀|대비|이해|차이|맞추|분리"
)
DARTLAB_ABSTRACT_WORD_RE = re.compile(
    r"관통선|표면|정본|맥락|구조|흐름|프레임|층위|사상|메커니즘|의미|핵심|관점|기준|경계|연결|감각|역할"
)
COMMON_ABSTRACT_WORD_RE = re.compile(
    r"관통선|표면|정본|맥락|구조|흐름|프레임|층위|사상|메커니즘|의미|핵심|관점|기준|경계|"
    r"연결|감각|역할|내러티브|서사|시사점|함의|방향성|체력|퀄리티|스토리|모멘텀|레버리지"
)
COMMON_EXPERT_JARGON_RE = re.compile(
    r"OPM|GPM|NPM|EBITDA|CAPEX|FCF|ROE|ROA|ROIC|PER|PBR|PSR|EV/EBITDA|WACC|DCF|SOTP|KPI|"
    r"밸류에이션|멀티플|컨센서스|듀레이션|디레이팅|리레이팅|영업\s*레버리지|운전자본|자본배분|"
    r"스프레드|마진\s*믹스|가이던스|프레임워크|인사이트|아웃퍼폼|언더퍼폼|오버행|"
    r"파사드|스키마|런타임|정본|호출\s*계약|프로바이더|컨텍스트|아키텍처|레지스트리|"
    r"어댑터|추상화|인터페이스|axis|facade|schema|runtime|provider|adapter|context|architecture",
    re.I,
)
DARTLAB_EXPERT_JARGON_RE = re.compile(
    r"파사드|스키마|런타임|정본|호출\s*계약|계약|프로바이더|컨텍스트|아키텍처|레지스트리|"
    r"어댑터|추상화|인터페이스|엔진|axis|facade|schema|runtime|provider|adapter|context|architecture",
    re.I,
)
DARTLAB_BEGINNER_BRIDGE_RE = re.compile(
    r"쉽게\s*말해|말하면|뜻은|여기서는|처음|먼저|헷갈|막히|예를\s*들어|코드|표|값|계정|기간|"
    r"화면|칸|버튼|실행|눌러|보면|확인"
)
COMMON_BEGINNER_BRIDGE_RE = re.compile(
    r"쉽게\s*말해|말하면|뜻은|여기서는|처음|먼저|헷갈|막히|예를\s*들어|예를|"
    r"숫자로\s*보면|표에서|차트에서|공시에서|보고서에서|코드에서|화면에서|이\s*말은|"
    r"그래서|즉|풀어\s*쓰면|확인|보면|비교|계산|읽으면|바꾸면"
)
DARTLAB_OPENING_ARC_RE = re.compile(r"처음|먼저|왜|어떻게|헷갈|막히|궁금|문제|시작|이\s*편")
DARTLAB_DO_ARC_RE = re.compile(r"실행|눌러|열|넣|확인|계산|바꾸|찾|고르|본다|보자|해\s*본")
DARTLAB_TURN_ARC_RE = re.compile(r"오해|한계|주의|다르|틀리|빈칸|안\s*된다|안\s*됩니다|예외|검산")
DARTLAB_CLOSE_ARC_RE = re.compile(r"이제|다음|바꿔|직접|연결|넘어|남는|닫는다|한\s*줄|다음\s*편")
COMMON_OPENING_ARC_RE = re.compile(r"처음|먼저|왜|어떻게|궁금|문제|이상|차이|시작|질문|막히|헷갈")
COMMON_DO_ARC_RE = re.compile(r"확인|비교|계산|읽|보면|찾|따져|나누|연결|검증|표|차트|공시|코드|데이터")
COMMON_TURN_ARC_RE = re.compile(r"오해|한계|주의|다르|틀리|하지만|그런데|단,|반대로|리스크|조건|깨지|검산")
COMMON_CLOSE_ARC_RE = re.compile(r"다음|봐야|확인|조건|기준|렌즈|체크|공시|지표|질문|남는|닫|바꿔")
DARTLAB_TRANSITION_RE = re.compile(
    r"다음|이어|넘어|이제|앞|뒤|그래서|그다음|그러면|마지막|왜|해야|수\s*있|오해|반복|재사용|이해|막을"
)
SECTION_PLAN_FIELDS = (
    "heading",
    "subtitle",
    "visualAnchor",
    "explanation",
    "example",
    "support",
    "transition",
    "evaluation",
)


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


def min_prose_chars(category: str) -> int:
    return GENRE_MIN_PROSE_CHARS.get(category, DEEP_MIN_PROSE_CHARS)


def target_prose_chars(category: str) -> int:
    return GENRE_TARGET_PROSE_CHARS.get(category, DEEP_TARGET_PROSE_CHARS)


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
                svg_count=len(re.findall(r"!\[[^\]]*\]\([^)]+\.svg(?:\s+[\"'][^\"']*[\"'])?\)", body, re.I)),
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
    catalog, errors = loadMediaCatalog(blog_root.parent / "media" / "catalog.json")
    if catalog is not None and not errors:
        files = catalog.get("files")
        objects = catalog.get("objects")
        posts = catalog.get("posts")
        if isinstance(files, dict) and isinstance(objects, dict) and isinstance(posts, dict):
            rows: list[SvgAudit] = []
            seenSources: set[str] = set()
            for post in posts.values():
                diagrams = post.get("diagrams") if isinstance(post, dict) else None
                if not isinstance(diagrams, dict):
                    continue
                for source in diagrams.values():
                    normalizedSource = str(source)
                    if normalizedSource in seenSources:
                        continue
                    seenSources.add(normalizedSource)
                    sha256 = str(files.get(normalizedSource) or "")
                    record = objects.get(sha256)
                    if not isinstance(record, dict):
                        continue
                    rows.append(
                        SvgAudit(
                            path=normalizedSource.removeprefix("blog/"),
                            size_bytes=int(record.get("bytes") or 0),
                            view_box=str(record.get("viewBox") or ""),
                            text_nodes=int(record.get("textNodes") or 0),
                            color_count=int(record.get("colorCount") or 0),
                            parse_error=None,
                        )
                    )
            return sorted(rows, key=lambda row: row.path)

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
            if row.category in DEEP_GENRE_CATEGORIES and row.prose_chars < min_prose_chars(row.category)
        ],
        "deep_reports_at_target": [
            row.path
            for row in posts
            if row.category in DEEP_GENRE_CATEGORIES and row.prose_chars >= target_prose_chars(row.category)
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
    deep_total = sum(summary["category_counts"].get(cat, 0) for cat in DEEP_GENRE_CATEGORIES)
    print(
        "- shallow content reports (장르별 본문 하한 미달): "
        f"{len(summary['shallow_deep_reports'])}/{deep_total}편  "
        f"| 장르별 목표 도달: {len(summary['deep_reports_at_target'])}편"
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
# 형식만 채우면 통과하던 SEO 게이트의 구멍을 막는다. 기업이야기·기술이야기·데이터리포트는 이
# 게이트를 통과해야 발행한다. 위반 시 exit 1. 기존 글엔 소급 적용 안 함(--gate <폴더>로 신규 글만 검사).
_OG_RE = re.compile(r"^/thumbnails/.+\.webp$")


def _clean_scalar(value: str) -> str:
    return str(value or "").strip().strip("\"'")


def _compact_len(value: object) -> int:
    return len(re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")))


def _has_dartlab_concrete_anchor(value: object) -> bool:
    return bool(DARTLAB_CONCRETE_ANCHOR_RE.search(str(value or "")))


def _has_dartlab_action(value: object) -> bool:
    return bool(DARTLAB_ACTION_RE.search(str(value or "")))


def _has_common_concrete_anchor(value: object) -> bool:
    return bool(COMMON_CONCRETE_ANCHOR_RE.search(str(value or "")))


def _has_common_beginner_bridge(value: object) -> bool:
    return bool(COMMON_BEGINNER_BRIDGE_RE.search(str(value or "")))


def _common_jargon_terms(value: object) -> list[str]:
    return [match.group(0) for match in COMMON_EXPERT_JARGON_RE.finditer(str(value or ""))]


def _has_dartlab_beginner_bridge(value: object) -> bool:
    return bool(DARTLAB_BEGINNER_BRIDGE_RE.search(str(value or "")))


def _dartlab_jargon_terms(value: object) -> list[str]:
    return [match.group(0) for match in DARTLAB_EXPERT_JARGON_RE.finditer(str(value or ""))]


def _split_h2_sections(body: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+)$", body, re.M))
    if not matches:
        return [("", body)]
    sections: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        sections.append((match.group(1).strip(), body[start:end]))
    return sections


def _plain_sentences(text: str) -> list[str]:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return [part.strip() for part in re.split(r"(?<=[.!?다요까])\s+", text) if part.strip()]


def _validate_dartlab_story_title(value: object, label: str) -> list[str]:
    title = str(value or "").strip()
    fails: list[str] = []
    if not title:
        return [f"{label}: 제목 누락"]
    if _compact_len(title) > 24:
        fails.append(f"{label}: dartlab 이야기 제목은 최대 24자여야 함({title!r})")
    if DARTLAB_TITLE_FORBIDDEN_RE.search(title):
        fails.append(f"{label}: 소개형·정리형·긴 방법론 제목은 금지({title!r})")
    if not DARTLAB_TITLE_SEARCH_RE.search(title):
        fails.append(f"{label}: 외부 검색어(DART, 공시, 재무제표, 사업보고서 등)가 필요함({title!r})")
    if not DARTLAB_TITLE_ACTION_RE.search(title):
        fails.append(f"{label}: 즉시 효용(설치, 파이썬, 코드, 브라우저, 실행 등)이 필요함({title!r})")
    return fails


def _load_json_payload(path: Path) -> tuple[dict[str, object] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"{path.name} JSON 파싱 실패: {exc}"
    if not isinstance(payload, dict):
        return None, f"{path.name} 최상위가 객체가 아님"
    return payload, None


def _find_plan_payload(post_dir: Path) -> tuple[Path | None, dict[str, object] | None, list[str]]:
    for name in PLAN_CANDIDATE_FILES:
        path = post_dir / name
        if not path.is_file():
            continue
        payload, err = _load_json_payload(path)
        if err:
            return path, None, [err]
        return path, payload, []
    return None, None, [f"기획 루프 산출물({', '.join(PLAN_CANDIDATE_FILES)}) 없음"]


def _plan_from_payload(payload: dict[str, object]) -> dict[str, object]:
    nested = payload.get("plan")
    if isinstance(nested, dict):
        return nested
    return payload


def _score_from_round(row: dict[str, object]) -> int | None:
    for key in ("evaluatorScore", "minScore", "score"):
        raw = row.get(key)
        if isinstance(raw, (int, float)):
            return int(raw)
        if isinstance(raw, str) and raw.strip().isdigit():
            return int(raw.strip())
    return None


def _validate_loop_evidence(
    plan: dict[str, object],
    payload: dict[str, object],
    *,
    label: str,
) -> list[str]:
    fails: list[str] = []
    gate = plan.get("reviewGate") if isinstance(plan.get("reviewGate"), dict) else {}
    evidence = gate.get("loopEvidence") if isinstance(gate.get("loopEvidence"), dict) else None
    if evidence is None:
        return [f"{label}: reviewGate.loopEvidence 누락. 작가기획 > 평가 피드백 > 재기획 > 재평가 증거가 필요함"]

    workflow = str(evidence.get("workflow") or "").strip()
    if workflow != BLOG_LOOP_WORKFLOW_NAME:
        fails.append(f"{label}: loopEvidence.workflow 는 {BLOG_LOOP_WORKFLOW_NAME} 이어야 함(현재 {workflow!r})")
    rounds = evidence.get("rounds") if isinstance(evidence.get("rounds"), list) else []
    if len(rounds) < 2:
        fails.append(f"{label}: loopEvidence.rounds 는 최소 2라운드 이상이어야 함")
    saw_revision = False
    for idx, raw in enumerate(rounds, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: loopEvidence.rounds[{idx}] 은 객체여야 함")
            continue
        for field in ("planner", "evaluator", "skeptic"):
            if _compact_len(raw.get(field)) < 10:
                fails.append(f"{label}: loopEvidence.rounds[{idx}].{field} 설명이 너무 약함")
        decision = str(raw.get("decision") or "").strip().lower()
        if not decision:
            fails.append(f"{label}: loopEvidence.rounds[{idx}].decision 누락")
        planner = str(raw.get("planner") or "")
        revision = str(raw.get("plannerRevision") or "")
        if idx > 1 and ("개선" in planner or "재작성" in revision or "반영" in revision):
            saw_revision = True
        if decision in {"revise", "kill", "revised"}:
            saw_revision = True
    final = rounds[-1] if rounds and isinstance(rounds[-1], dict) else {}
    final_decision = str(final.get("decision") or "").strip().lower()
    final_score = _score_from_round(final)
    if final_decision not in {"pass", "passed", "survive"}:
        fails.append(f"{label}: loopEvidence 마지막 라운드가 통과로 닫히지 않음({final_decision!r})")
    if final_score is None or final_score < BLOG_REVIEW_SCORE_MIN:
        fails.append(f"{label}: loopEvidence 마지막 평가 점수 {final_score!r} < {BLOG_REVIEW_SCORE_MIN}")
    if not saw_revision:
        fails.append(f"{label}: 평가 피드백을 반영한 기획자 재작성 흔적이 없음")
    if payload.get("passed") is False:
        fails.append(f"{label}: workflow passed=false 상태")
    return fails


def plan_shape(category: str) -> dict[str, int]:
    return GENRE_PLAN_SHAPE.get(category, _DEFAULT_PLAN_SHAPE)


def _validate_section_plan(plan: dict[str, object], *, label: str, category: str, min_sections: int) -> list[str]:
    fails: list[str] = []
    sections = plan.get("sections") if isinstance(plan.get("sections"), list) else []
    if len(sections) < min_sections:
        fails.append(f"{label}: sections 는 {min_sections}개 이상이어야 함(현재 {len(sections)})")
    for idx, raw in enumerate(sections, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: sections[{idx}] 은 객체여야 함")
            continue
        for field in SECTION_PLAN_FIELDS:
            min_len = 8 if field in {"heading", "subtitle"} else 12
            if _compact_len(raw.get(field)) < min_len:
                fails.append(f"{label}: sections[{idx}].{field} 이 너무 약함")
        explanation = str(raw.get("explanation") or "")
        example = str(raw.get("example") or "")
        support = str(raw.get("support") or "")
        transition = str(raw.get("transition") or "")
        beginner_text = " ".join(str(raw.get(field) or "") for field in ("subtitle", "explanation", "support"))
        if category in CONTENT_GENRE_CATEGORIES and category != "dartlab-stories":
            if not (_has_common_concrete_anchor(explanation) or _has_common_beginner_bridge(explanation)):
                fails.append(
                    f"{label}: sections[{idx}].explanation 은 초보자가 보는 숫자·표·공시·사례나 쉬운 풀이에서 시작해야 함"
                )
            if not _has_common_concrete_anchor(example):
                fails.append(f"{label}: sections[{idx}].example 은 실제 숫자·회사·공시·사례 중 하나를 잡아야 함")
            if len(set(_common_jargon_terms(beginner_text))) >= 2 and not (
                _has_common_beginner_bridge(beginner_text) or _has_common_concrete_anchor(beginner_text)
            ):
                fails.append(
                    f"{label}: sections[{idx}] 이 전문가 용어를 쉬운 풀이 없이 씀. 초보자 문장과 실제 근거가 필요함"
                )
            if not COMMON_TURN_ARC_RE.search(support):
                fails.append(f"{label}: sections[{idx}].support 는 오해·한계·주의·조건 중 하나를 명시해야 함")
            if not DARTLAB_TRANSITION_RE.search(transition):
                fails.append(f"{label}: sections[{idx}].transition 은 다음 섹션으로 왜 넘어가는지 쉬운 연결문이어야 함")
        if category == "dartlab-stories":
            anchor = str(raw.get("visualAnchor") or "")
            if not re.search(r"코드|출력|표|도식|이미지|화면|panel|DataFrame|차트", anchor, re.I):
                fails.append(
                    f"{label}: sections[{idx}].visualAnchor 는 실제 코드 출력·표·도식·이미지 중 하나를 명시해야 함"
                )
            section_text = json.dumps(raw, ensure_ascii=False)
            if re.search(r"\.shape\b|\bshape\b|[0-9]+\s*x\s*[0-9]+|\([0-9]+\s*,\s*[0-9]+\)", section_text, re.I):
                fails.append(
                    f"{label}: sections[{idx}] 이 행열 크기나 shape 를 학습 근거로 씀. 실제 계정·기간·값을 보여 줘야 함"
                )
            if re.search(
                r"축수|축\s*수|축\s*개수|엔진별\s*축|axis\s*count|[0-9]+\s*/\s*[0-9]+\s*(?:인증|통과|표면)",
                section_text,
                re.I,
            ):
                fails.append(
                    f"{label}: sections[{idx}] 이 내부 기능 개수나 인증 수를 근거로 씀. 실제 호출 결과와 값을 보여 줘야 함"
                )
            if not re.search(r"오해|주의|한계|브라우저|로컬|틀리|예외|보완|검산", support):
                fails.append(f"{label}: sections[{idx}].support 는 오해 방지·한계·보완 설명을 명시해야 함")
            if not (_has_dartlab_action(explanation) or _has_dartlab_concrete_anchor(explanation)):
                fails.append(
                    f"{label}: sections[{idx}].explanation 은 독자가 보는 코드·표·값이나 직접 할 행동으로 써야 함"
                )
            if not _has_dartlab_concrete_anchor(example):
                fails.append(
                    f"{label}: sections[{idx}].example 은 코드·계정·기간·값·공시 문장 중 하나를 실제 예시로 잡아야 함"
                )
            if len(set(_dartlab_jargon_terms(beginner_text))) >= 2 and not _has_dartlab_beginner_bridge(beginner_text):
                fails.append(
                    f"{label}: sections[{idx}] 이 전문가 용어를 쉬운 풀이 없이 씀. 초보자 문장과 실제 화면 근거가 필요함"
                )
    return fails


def _validate_common_plan(
    plan: dict[str, object], payload: dict[str, object], *, label: str, category: str = ""
) -> list[str]:
    shape = plan_shape(category)
    fails: list[str] = []
    missing = [field for field in BLOG_REQUIRED_PLAN_FIELDS if field not in plan]
    if missing:
        fails.append(f"{label}: 기획 필수 필드 누락: {', '.join(missing)}")

    title_contract = plan.get("titleContract") if isinstance(plan.get("titleContract"), dict) else {}
    candidates = title_contract.get("candidates") if isinstance(title_contract.get("candidates"), list) else []
    if len(candidates) < 3:
        fails.append(f"{label}: titleContract.candidates 는 제목 후보 3개 이상이어야 함")
    for field in ("selectedTitle", "hookQuestion", "readerGap", "promise", "whySelected"):
        min_len = 6 if field == "selectedTitle" else 12
        if _compact_len(title_contract.get(field)) < min_len:
            fails.append(f"{label}: titleContract.{field} 이 너무 약함")
    selected = str(title_contract.get("selectedTitle") or plan.get("title") or "")
    if re.search(r"(?:정리|분석|리포트|이야기|총정리)$", selected):
        fails.append(f"{label}: 제목이 설명형 템플릿으로 끝남({selected!r})")
    if re.search(r"돈을\s*못\s*번|누가\s*돈을\s*버나|왜\s*못\s*버나", selected):
        fails.append(f"{label}: 제목이 반복 금융 템플릿임({selected!r})")
    if category == "dartlab-stories":
        fails.extend(_validate_dartlab_story_title(selected, f"{label}: titleContract.selectedTitle"))
        plan_title = str(plan.get("title") or "")
        fails.extend(_validate_dartlab_story_title(plan_title, f"{label}: title"))
        plan_text = json.dumps(plan, ensure_ascii=False)
        if re.search(r"\.shape\b|\bshape\b|[0-9]+\s*x\s*[0-9]+|\([0-9]+\s*,\s*[0-9]+\)", plan_text, re.I):
            fails.append(f"{label}: dartlab 이야기 기획은 shape·행열 크기를 근거로 쓰지 않는다")
        if re.search(
            r"축수|축\s*수|축\s*개수|엔진별\s*축|axis\s*count|[0-9]+\s*/\s*[0-9]+\s*(?:인증|통과|표면)",
            plan_text,
            re.I,
        ):
            fails.append(f"{label}: dartlab 이야기 기획은 내부 기능 개수나 인증 수를 근거로 쓰지 않는다")
        for idx, raw in enumerate(candidates, start=1):
            if isinstance(raw, dict):
                fails.extend(
                    _validate_dartlab_story_title(raw.get("title"), f"{label}: titleContract.candidates[{idx}]")
                )

    insight = plan.get("insight") if isinstance(plan.get("insight"), dict) else {}
    for field in ("commonBelief", "twistFact", "whatToWatch", "freshnessArgument"):
        if _compact_len(insight.get(field)) < 20:
            fails.append(f"{label}: insight.{field} 이 너무 약함")
    refs = insight.get("evidenceRefs") if isinstance(insight.get("evidenceRefs"), list) else []
    if not refs:
        fails.append(f"{label}: insight.evidenceRefs 누락")

    acts = plan.get("acts") if isinstance(plan.get("acts"), list) else []
    if len(acts) < shape["acts"]:
        fails.append(f"{label}: acts 는 {shape['acts']}막 이상이어야 함(현재 {len(acts)})")
    for idx, raw in enumerate(acts, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: acts[{idx}] 은 객체여야 함")
            continue
        for field in ("heading", "scene", "causalBridge"):
            if _compact_len(raw.get(field)) < 10:
                fails.append(f"{label}: acts[{idx}].{field} 이 너무 약함")
        if not str(raw.get("purpose") or "").strip():
            fails.append(f"{label}: acts[{idx}].purpose 누락")

    if category in CONTENT_GENRE_CATEGORIES and category != "dartlab-stories":
        sections = plan.get("sections") if isinstance(plan.get("sections"), list) else []
        first_arc_text = json.dumps(
            {
                "readerQuestion": plan.get("readerQuestion"),
                "firstAct": acts[0] if acts else {},
                "firstSection": sections[0] if sections else {},
            },
            ensure_ascii=False,
        )
        whole_arc_text = json.dumps(
            {"acts": acts, "sections": sections, "guards": plan.get("honestyGuards")}, ensure_ascii=False
        )
        close_arc_text = json.dumps(
            {
                "lastAct": acts[-1] if acts else {},
                "lastSection": sections[-1] if sections else {},
                "whatToWatch": insight.get("whatToWatch"),
            },
            ensure_ascii=False,
        )
        if not COMMON_OPENING_ARC_RE.search(first_arc_text):
            fails.append(f"{label}: 첫 단계는 초보자가 왜 이 글을 읽어야 하는지 먼저 잡아야 함")
        if not COMMON_DO_ARC_RE.search(whole_arc_text):
            fails.append(f"{label}: 본문 단계에는 독자가 직접 볼 숫자·표·공시·차트 장면이 필요함")
        if not COMMON_TURN_ARC_RE.search(whole_arc_text):
            fails.append(f"{label}: 본문 단계에는 오해·한계·주의·틀리는 조건 같은 전환 지점이 필요함")
        if not COMMON_CLOSE_ARC_RE.search(close_arc_text):
            fails.append(f"{label}: 마지막 단계는 다음에 볼 기준·지표·공시 질문으로 닫혀야 함")

    if category == "dartlab-stories":
        sections = plan.get("sections") if isinstance(plan.get("sections"), list) else []
        first_arc_text = json.dumps(
            {
                "readerQuestion": plan.get("readerQuestion"),
                "firstAct": acts[0] if acts else {},
                "firstSection": sections[0] if sections else {},
            },
            ensure_ascii=False,
        )
        whole_arc_text = json.dumps(
            {"acts": acts, "sections": sections, "guards": plan.get("honestyGuards")}, ensure_ascii=False
        )
        close_arc_text = json.dumps(
            {
                "lastAct": acts[-1] if acts else {},
                "lastSection": sections[-1] if sections else {},
                "whatToWatch": insight.get("whatToWatch"),
            },
            ensure_ascii=False,
        )
        if not DARTLAB_OPENING_ARC_RE.search(first_arc_text):
            fails.append(f"{label}: dartlab 이야기 첫 단계는 초보자가 어디서 막혔는지 또는 왜 시작하는지를 잡아야 함")
        if not DARTLAB_DO_ARC_RE.search(whole_arc_text):
            fails.append(f"{label}: dartlab 이야기 단계에는 독자가 직접 실행·확인·계산하는 장면이 필요함")
        if not DARTLAB_TURN_ARC_RE.search(whole_arc_text):
            fails.append(f"{label}: dartlab 이야기 단계에는 오해·한계·주의 같은 전환 지점이 필요함")
        if not DARTLAB_CLOSE_ARC_RE.search(close_arc_text):
            fails.append(f"{label}: dartlab 이야기 마지막 단계는 다음 행동이나 다음 편으로 닫혀야 함")

    fails.extend(_validate_section_plan(plan, label=label, category=category, min_sections=shape["acts"]))

    visuals = plan.get("visuals") if isinstance(plan.get("visuals"), list) else []
    if len(visuals) < shape["visuals"]:
        fails.append(f"{label}: visuals 는 최소 {shape['visuals']}개 이상 기획해야 함(현재 {len(visuals)})")
    for idx, raw in enumerate(visuals, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: visuals[{idx}] 은 객체여야 함")
            continue
        for field in ("title", "proves"):
            if _compact_len(raw.get(field)) < 8:
                fails.append(f"{label}: visuals[{idx}].{field} 이 너무 약함")
        for field in ("placement", "insertAfter", "narrativeUse"):
            if _compact_len(raw.get(field)) < 8:
                fails.append(
                    f"{label}: visuals[{idx}].{field} 누락. 비주얼은 본문 중간에서 어떤 설명을 돕는지 기획해야 함"
                )
        if not str(raw.get("kind") or "").strip():
            fails.append(f"{label}: visuals[{idx}].kind 누락")

    image_plan = plan.get("imagePlan") if isinstance(plan.get("imagePlan"), list) else []
    if len(image_plan) < shape["images"]:
        fails.append(f"{label}: imagePlan 은 {shape['images']}장 이상이어야 함(현재 {len(image_plan)})")
    for idx, raw in enumerate(image_plan, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: imagePlan[{idx}] 은 객체여야 함")
            continue
        for field in ("slot", "subject", "query", "keywords", "placement", "narrativeUse"):
            if field == "keywords":
                if not isinstance(raw.get(field), list) or not raw.get(field):
                    fails.append(f"{label}: imagePlan[{idx}].keywords 누락")
            elif field == "slot":
                if not str(raw.get(field) or "").strip():
                    fails.append(f"{label}: imagePlan[{idx}].slot 누락")
            elif _compact_len(raw.get(field)) < 8:
                fails.append(f"{label}: imagePlan[{idx}].{field} 이 너무 약함")

    contractVersion = _planContractVersion(plan)
    if contractVersion and contractVersion != BLOG_PLAN_CONTRACT_VERSION:
        fails.append(f"{label}: 지원하지 않는 contractVersion {contractVersion}")
    if contractVersion == BLOG_PLAN_CONTRACT_VERSION:
        fails.extend(_validateWatchScenarios(plan, label=label, category=category))
        assetKeys: list[str] = []
        for idx, raw in enumerate(image_plan, start=1):
            if not isinstance(raw, dict):
                continue
            assetKey = str(raw.get("assetKey") or "").strip()
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", assetKey):
                fails.append(f"{label}: imagePlan[{idx}].assetKey 는 영문 kebab-case 여야 함")
            elif assetKey in assetKeys:
                fails.append(f"{label}: imagePlan[{idx}].assetKey 중복({assetKey})")
            else:
                assetKeys.append(assetKey)
            if raw.get("sourcePolicy") != "auto":
                fails.append(f"{label}: imagePlan[{idx}].sourcePolicy 는 auto 여야 함")

    related = plan.get("relatedPosts") if isinstance(plan.get("relatedPosts"), dict) else {}
    searches = related.get("searches") if isinstance(related.get("searches"), list) else []
    links = related.get("links") if isinstance(related.get("links"), list) else []
    if not searches:
        fails.append(f"{label}: relatedPosts.searches 누락. 선행 글 검색어와 참고글 연결 계획이 필요함")
    if _compact_len(related.get("placementRule")) < 12:
        fails.append(f"{label}: relatedPosts.placementRule 이 너무 약함")
    for idx, raw in enumerate(links, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: relatedPosts.links[{idx}] 은 객체여야 함")
            continue
        for field in ("path", "title", "reason", "placement"):
            if _compact_len(raw.get(field)) < 6:
                fails.append(f"{label}: relatedPosts.links[{idx}].{field} 이 너무 약함")

    guards = plan.get("honestyGuards") if isinstance(plan.get("honestyGuards"), list) else []
    if len(guards) < 3:
        fails.append(f"{label}: honestyGuards 는 3개 이상이어야 함")

    evidence_map = plan.get("evidenceMap") if isinstance(plan.get("evidenceMap"), list) else []
    if len(evidence_map) < 3:
        fails.append(f"{label}: evidenceMap 은 DART/EDGAR/dartlab/scan 근거를 3개 이상 묶어야 함")
    else:
        evidence_labels = " ".join(
            str(row.get("sourceType") or row.get("source") or row.get("sourceRef") or "")
            for row in evidence_map
            if isinstance(row, dict)
        ).upper()
        evidence_tokens = ("DART", "EDGAR", "SCAN", "DARTLAB", "PRICE", "MACRO", "INTERNAL-BLOG")
        if not any(token in evidence_labels for token in evidence_tokens):
            fails.append(f"{label}: evidenceMap 에 DART/EDGAR/scan/dartlab/price/macro/internal-blog 근거 라벨이 없음")

    fails.extend(_validate_loop_evidence(plan, payload, label=label))
    return fails


def _planContractVersion(plan: dict[str, object] | None) -> int:
    if not isinstance(plan, dict):
        return 0
    value = plan.get("contractVersion")
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _validateWatchScenarios(plan: dict[str, object], *, label: str, category: str) -> list[str]:
    if category not in DEEP_GENRE_CATEGORIES:
        return []
    fails: list[str] = []
    scenarios = plan.get("watchScenarios") if isinstance(plan.get("watchScenarios"), list) else []
    if not 2 <= len(scenarios) <= 4:
        fails.append(f"{label}: watchScenarios 는 서로 다른 조건의 시나리오 2~4개여야 함")
    for idx, raw in enumerate(scenarios, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: watchScenarios[{idx}] 은 객체여야 함")
            continue
        for field in ("condition", "mechanism", "outcome", "watchMetric", "invalidatedBy"):
            if _compact_len(raw.get(field)) < 12:
                fails.append(f"{label}: watchScenarios[{idx}].{field} 이 너무 약함")
        evidenceRefs = raw.get("evidenceRefs") if isinstance(raw.get("evidenceRefs"), list) else []
        if not evidenceRefs:
            fails.append(f"{label}: watchScenarios[{idx}].evidenceRefs 누락")
    return fails


def _validate_dartlab_body_plainness(body: str) -> list[str]:
    fails: list[str] = []
    abstract_only_sentences: list[str] = []
    jargon_sentences: list[str] = []
    for heading, section in _split_h2_sections(body):
        section_chars = prose_char_count(section)
        if section_chars >= 100 and not _has_dartlab_concrete_anchor(section):
            fails.append(
                f"dartlab 이야기 섹션 {heading!r} 은 코드·표·계정·기간·값 없이 설명만 있음. 화면에 보이는 것을 먼저 둬야 함"
            )
        for sentence in _plain_sentences(section):
            if _compact_len(sentence) < 18:
                continue
            if len(DARTLAB_ABSTRACT_WORD_RE.findall(sentence)) >= 2 and not _has_dartlab_concrete_anchor(sentence):
                abstract_only_sentences.append(sentence[:80])
            if _dartlab_jargon_terms(sentence) and not (
                _has_dartlab_concrete_anchor(sentence) or _has_dartlab_beginner_bridge(sentence)
            ):
                jargon_sentences.append(sentence[:80])
    if len(abstract_only_sentences) >= 3:
        sample = " / ".join(abstract_only_sentences[:3])
        fails.append(f"dartlab 이야기 본문에 실제 코드·값 없이 떠 있는 추상 문장이 많음. 예: {sample}")
    if len(jargon_sentences) >= 2:
        sample = " / ".join(jargon_sentences[:2])
        fails.append(f"dartlab 이야기 본문이 전문가 말투로 흐름. 쉬운 풀이와 실제 화면 근거가 필요함. 예: {sample}")

    if prose_char_count(body) >= 500:
        opening = body[:1200]
        closing = body[-1400:]
        if not DARTLAB_OPENING_ARC_RE.search(opening):
            fails.append("dartlab 이야기 본문 첫 부분은 초보자가 왜 이 글을 읽는지 먼저 잡아야 함")
        if not DARTLAB_DO_ARC_RE.search(body):
            fails.append("dartlab 이야기 본문에는 독자가 직접 실행·확인·계산하는 장면이 필요함")
        if not DARTLAB_TURN_ARC_RE.search(body):
            fails.append("dartlab 이야기 본문에는 오해·한계·주의 같은 전환 지점이 필요함")
        if not DARTLAB_CLOSE_ARC_RE.search(closing):
            fails.append("dartlab 이야기 본문 마지막은 다음 행동이나 다음 편 연결로 닫혀야 함")
    return fails


def _validate_common_body_plainness(body: str, category: str) -> list[str]:
    if category not in BLOG_CATEGORIES:
        return []

    fails: list[str] = []
    abstract_only_sentences: list[str] = []
    jargon_sentences: list[str] = []
    isDeepEditorial = category in CONTENT_GENRE_CATEGORIES
    for _, section in _split_h2_sections(body):
        for sentence in _plain_sentences(section):
            compact = _compact_len(sentence)
            if compact < 15:
                continue
            if (
                compact >= 22
                and len(COMMON_ABSTRACT_WORD_RE.findall(sentence)) >= 2
                and not _has_common_concrete_anchor(sentence)
            ):
                abstract_only_sentences.append(sentence[:90])
            if _common_jargon_terms(sentence) and not (
                _has_common_concrete_anchor(sentence) or _has_common_beginner_bridge(sentence)
            ):
                jargon_sentences.append(sentence[:90])

    abstractLimit = 4 if isDeepEditorial else 2
    jargonLimit = 3 if isDeepEditorial else 2
    if len(abstract_only_sentences) >= abstractLimit:
        sample = " / ".join(abstract_only_sentences[:3])
        fails.append(f"본문에 실제 숫자·공시·사례 없이 떠 있는 추상 문장이 많음. 예: {sample}")
    if len(jargon_sentences) >= jargonLimit:
        sample = " / ".join(jargon_sentences[:3])
        fails.append(f"본문이 전문가 말투로 흐름. 쉬운 풀이와 실제 근거가 필요함. 예: {sample}")

    narrativeMinChars = 2500 if isDeepEditorial else 500
    if prose_char_count(body) >= narrativeMinChars:
        opening = body[:1600]
        closing = body[-1800:]
        if not COMMON_OPENING_ARC_RE.search(opening):
            fails.append("본문 첫 부분은 초보자가 왜 이 글을 읽어야 하는지 먼저 잡아야 함")
        if not COMMON_DO_ARC_RE.search(body):
            fails.append("본문에는 독자가 직접 볼 숫자·표·공시·차트 장면이 필요함")
        if not COMMON_TURN_ARC_RE.search(body):
            fails.append("본문에는 오해·한계·주의·틀리는 조건 같은 전환 지점이 필요함")
        if not COMMON_CLOSE_ARC_RE.search(closing):
            fails.append("본문 마지막은 다음에 볼 기준·지표·공시 질문으로 닫혀야 함")
    return fails


def _validate_genre_body(raw: str, body: str, category: str) -> list[str]:
    fails: list[str] = []
    title = _clean_scalar(frontmatter_value(raw, "title"))
    topic_slug = _clean_scalar(frontmatter_value(raw, "topicSlug"))
    stock_code = _clean_scalar(frontmatter_value(raw, "stockCode"))
    upper_body = body.upper()

    fails.extend(_validate_common_body_plainness(body, category))

    if category == "company-reports":
        if not stock_code:
            fails.append("기업이야기는 frontmatter stockCode 가 필요함")
        if "DART" not in upper_body and "EDGAR" not in upper_body:
            fails.append("기업이야기는 DART 또는 EDGAR 공시 근거를 본문에 명시해야 함")
        if not re.search(r"사업\s*구조|사업부|제품|고객|수주|원가|자본배치|현금흐름", body):
            fails.append("기업이야기는 회사 사업 구조와 재무 연결 설명이 필요함")
    elif category == "tech-story":
        if not topic_slug:
            fails.append("기술이야기는 frontmatter topicSlug 가 필요함")
        if stock_code:
            fails.append("기술이야기는 기본적으로 stockCode 를 달지 않는다. 주어는 회사가 아니라 기술임")
        if "DART" not in upper_body or "EDGAR" not in upper_body:
            fails.append("기술이야기는 DART와 EDGAR 근거를 모두 연결해야 함")
        if not ("공정" in body and "대표 회사" in body and "공시 근거" in body):
            fails.append("기술이야기는 공정/층위 | 대표 회사 | 공시 근거 지도가 필요함")
        if not re.search(r"왜\s*.+핵심|대체|전환비용|병목|인증|양산|특허|CAPEX", body, re.I):
            fails.append("기술이야기는 왜 그 회사가 그 공정·네트워크 칸의 핵심인지 설명해야 함")
        if "기술 성숙도" not in body:
            fails.append("기술이야기는 기술 성숙도와 출처 섹션이 필요함")
        if "오해" not in body:
            fails.append("기술이야기는 '이렇게 오해하면 안 된다' 류 오독 방지 섹션이 필요함")
    elif category == "data-reports":
        if not topic_slug:
            fails.append("데이터 리포트는 frontmatter topicSlug 가 필요함")
        if stock_code:
            fails.append("데이터 리포트는 기본적으로 stockCode 를 달지 않는다. 주어는 시장 전체임")
        if "```python" not in body:
            fails.append("데이터 리포트는 재현 가능한 python 코드블록이 필요함")
        if "SCAN" not in upper_body and "전수" not in body:
            fails.append("데이터 리포트는 scan 또는 전수 집계 방법을 본문에 명시해야 함")
        if "DART" not in upper_body or "EDGAR" not in upper_body:
            fails.append("데이터 리포트는 DART와 EDGAR 유니버스 또는 제외 사유를 명시해야 함")
        if "분모" not in body or "오해" not in body:
            fails.append("데이터 리포트는 분모·필터와 오독 방지 설명이 필요함")
    elif category == "investment-stories":
        internal_links = re.findall(r"\[[^\]]+\]\(/blog/[^)]+\)", body)
        indicator_topic = re.search(r"지지선|저항선|이동평균|RSI|MACD|볼린저|보조지표|거래량|거래대금", body, re.I)
        if not topic_slug:
            fails.append("투자이야기는 frontmatter topicSlug 가 필요함")
        if stock_code:
            fails.append("투자이야기는 기본적으로 stockCode 를 달지 않는다. 주어는 회사가 아니라 투자 개념임")
        if not re.search(
            r"주가|금리|환율|물가|경기|증권사|컨센서스|목표주가|투자\s*용어|밸류에이션|보조지표|지지선|저항선|이동평균|RSI|MACD|거래량|기술투자",
            body,
            re.I,
        ):
            fails.append(
                "투자이야기는 주가·경제·증권사 언어·투자 용어·보조지표·기술투자 중 하나를 본문 주어로 삼아야 함"
            )
        if len(internal_links) < 2:
            fails.append("투자이야기는 선행 참고글 내부 링크가 2개 이상 필요함")
        if not re.search(r"오해|한계|주의|틀리|깨지|재점검|투자권유|확정", body):
            fails.append("투자이야기는 오독 방지와 틀리는 조건을 본문에 명시해야 함")
        if indicator_topic and not re.search(r"기간|분봉|일봉|주봉|월봉|거래량|거래대금|기준선|데이터\s*기준", body):
            fails.append("투자이야기 보조지표 글은 기간·봉 단위·거래량·기준선 중 최소 하나를 명시해야 함")
    elif category == "dartlab-stories":
        # 주어는 회사가 아니라 dartlab 이다. 본문 코드는 독자가 브라우저에서 그대로 실행한다.
        # 계약 밖 호출이 섞이면 tests/audit/notebookContract.py 가 따로 막는다.
        fails.extend(_validate_dartlab_story_title(title, "frontmatter title"))
        if not topic_slug:
            fails.append("dartlab 이야기는 frontmatter topicSlug 가 필요함")
        if stock_code:
            fails.append("dartlab 이야기는 stockCode 를 달지 않는다. 주어는 회사가 아니라 dartlab 임")
        if "```python" not in body:
            fails.append("dartlab 이야기는 독자가 그대로 실행할 python 코드블록이 필요함")
        if not re.search(r"\bdartlab\b", body):
            fails.append("dartlab 이야기는 본문에 실제 dartlab 호출이 있어야 함")
        if re.search(r"\.shape\b|\bshape\b|[0-9]+\s*x\s*[0-9]+|\([0-9]+\s*,\s*[0-9]+\)", body, re.I):
            fails.append("dartlab 이야기는 shape·행열 크기를 학습 근거로 쓰지 않는다. 실제 계정·기간·값을 보여 줘야 함")
        if re.search(
            r"축수|축\s*수|축\s*개수|엔진별\s*축|axis\s*count|[0-9]+\s*/\s*[0-9]+\s*(?:인증|통과|표면)",
            body,
            re.I,
        ):
            fails.append(
                "dartlab 이야기는 내부 기능 개수나 인증 수를 학습 근거로 쓰지 않는다. 실제 호출 결과와 값을 보여 줘야 함"
            )
        if not re.search(r"안\s*됩니다|안\s*된다|한계|주의|오해|로컬에서만", body):
            fails.append("dartlab 이야기는 브라우저에서 안 되는 것과 오독 방지를 본문에 명시해야 함")
        fails.extend(_validate_dartlab_body_plainness(body))
    return fails


def _load_plan(post_dir: Path) -> tuple[dict[str, object] | None, str, list[str]]:
    """(plan, label, fails). fails 가 비어야 plan 이 유효하다."""
    plan_path, payload, load_fails = _find_plan_payload(post_dir)
    if load_fails:
        return None, "", load_fails
    assert payload is not None and plan_path is not None
    plan = _plan_from_payload(payload)
    if not isinstance(plan, dict):
        return None, plan_path.name, [f"{plan_path.name}: plan 이 객체가 아님"]
    return (
        plan,
        plan_path.name,
        _validate_common_plan(plan, payload, label=plan_path.name, category=_plan_category(post_dir)),
    )


def _plan_category(post_dir: Path) -> str:
    idx = post_dir / "index.md"
    if not idx.is_file():
        return ""
    return _clean_scalar(frontmatter_value(idx.read_text(encoding="utf-8"), "category"))


def _validate_plan_file(post_dir: Path) -> list[str]:
    _, _, fails = _load_plan(post_dir)
    return fails


def _image_plan(plan: dict[str, object] | None) -> list[dict[str, object]]:
    raw = plan.get("imagePlan") if isinstance(plan, dict) else None
    return [x for x in raw if isinstance(x, dict)] if isinstance(raw, list) else []


def _validateImageSsot(postDir: Path, body: str, plan: dict[str, object] | None) -> list[str]:
    if _planContractVersion(plan) != BLOG_PLAN_CONTRACT_VERSION:
        return []
    fails: list[str] = []
    planned = _image_plan(plan)
    manifest, manifestFails = loadMediaManifest(postDir)
    fails.extend(manifestFails)
    creditsPath = postDir / "assets" / "CREDITS.md"
    credits = creditsPath.read_text(encoding="utf-8") if creditsPath.is_file() else ""
    if not credits:
        fails.append("contract v2 이미지는 assets/CREDITS.md 출처 기록이 필요함")
    if manifest is None:
        return fails
    manifestAssets = manifest.get("assets") if isinstance(manifest.get("assets"), dict) else {}
    plannedKeys = [str(item.get("assetKey") or "").strip() for item in planned]
    extraKeys = sorted(set(manifestAssets) - set(plannedKeys))
    if extraKeys:
        fails.append(f"media/catalog.json에 imagePlan 밖 자산이 있음: {', '.join(extraKeys)}")
    for idx, item in enumerate(planned, start=1):
        assetKey = str(item.get("assetKey") or "").strip()
        if not assetKey:
            continue
        if credits and assetKey not in credits:
            fails.append(f"assets/CREDITS.md 에 imagePlan[{idx}] assetKey 누락: {assetKey}")
        record = manifestAssets.get(assetKey)
        if not isinstance(record, dict):
            fails.append(f"media/catalog.json에 imagePlan[{idx}] 누락: {assetKey}")
            continue
        remotePath = str(record.get("path") or "")
        sha256 = str(record.get("sha256") or "")
        if not ASSET_KEY_RE.fullmatch(assetKey) or not SHA256_RE.fullmatch(sha256):
            fails.append(f"media/catalog.json imagePlan[{idx}] 해시 계약 위반: {assetKey}")
            continue
        expectedPath = mediaPath(sha256)
        if remotePath != expectedPath:
            fails.append(f"media/catalog.json imagePlan[{idx}] 경로 불일치: {remotePath!r} != {expectedPath!r}")
        bodyRef = mediaUrl(expectedPath)
        bodyRefPattern = rf"!\[[^\]]*\]\({re.escape(bodyRef)}\)"
        if not re.search(bodyRefPattern, body):
            fails.append(f"imagePlan[{idx}] 본문 참조 없음: {bodyRef}")
        if f"./assets/{assetKey}.webp" in body:
            fails.append(f"imagePlan[{idx}] 로컬 바이너리 참조 금지: ./assets/{assetKey}.webp")

    diagrams = manifest.get("diagrams") if isinstance(manifest.get("diagrams"), dict) else {}
    for key, record in diagrams.items():
        if not isinstance(record, dict):
            fails.append(f"media/catalog.json SVG 계약 위반: {key}")
            continue
        remotePath = str(record.get("path") or "")
        sha256 = str(record.get("sha256") or "")
        expectedPath = mediaPath(sha256, ".svg") if SHA256_RE.fullmatch(sha256) else ""
        if not expectedPath or remotePath != expectedPath:
            fails.append(f"media/catalog.json SVG 해시·경로 계약 위반: {key}")
            continue
        bodyRef = mediaUrl(expectedPath)
        if not re.search(rf"!\[[^\]]*\]\({re.escape(bodyRef)}\)", body):
            fails.append(f"SVG 본문 참조 없음: {bodyRef}")
        if f"./assets/{key}.svg" in body:
            fails.append(f"SVG 로컬 참조 금지: ./assets/{key}.svg")

    og = manifest.get("og")
    if isinstance(og, dict):
        ogPath = str(og.get("path") or "")
        ogSha256 = str(og.get("sha256") or "")
        expectedOgPath = mediaPath(ogSha256)
        if not SHA256_RE.fullmatch(ogSha256) or ogPath != expectedOgPath:
            fails.append("media/catalog.json og 해시·경로 계약 위반")
    return fails


def _validateScenarioBody(body: str, plan: dict[str, object] | None, category: str) -> list[str]:
    if category not in DEEP_GENRE_CATEGORIES or _planContractVersion(plan) != BLOG_PLAN_CONTRACT_VERSION:
        return []
    sections = _split_h2_sections(body)
    if not sections:
        return ["contract v2 심층 글은 마지막 H2에 시나리오형 관전 포인트가 필요함"]
    heading, closing = sections[-1]
    fails: list[str] = []
    if not re.search(r"관전|시나리오|조건", heading):
        fails.append("contract v2 심층 글의 마지막 H2는 시나리오형 관전 포인트여야 함")
    conditionalCount = len(re.findall(r"만약|경우|조건|때라면|한다면|되면", closing))
    if conditionalCount < 2:
        fails.append("마지막 관전 포인트에는 서로 다른 '만약/조건' 시나리오가 2개 이상 필요함")
    if not re.search(r"지표|수치|공시|확인|관찰|추적", closing):
        fails.append("마지막 관전 포인트에는 시나리오를 확인할 지표나 공시가 필요함")
    if not re.search(r"무효|틀리|틀린|깨지|깨진|아니|반대|재점검", closing):
        fails.append("마지막 관전 포인트에는 시나리오가 틀렸음을 보여 줄 조건이 필요함")
    return fails


def publish_gate(post_dir: Path, *, requireContractV2: bool = False) -> list[str]:
    """단일 글 발행 하드 게이트. 위반 리스트 반환(비면 통과).

    9개 블로그 카테고리 모두에 내러티브와 쉬운 설명의 공통 편집 계약을 적용한다.
    기업이야기·기술이야기·데이터리포트·투자이야기 기준으로 (1)OG 카드 (2)hero webp
    (3)본문 콘텐츠 이미지 1장 이상 (4)장르별 본문 깊이 (5)기획 루프 산출물(brief.json)을 강제한다.
    손수 SVG·기본 아바타·얕은 본문·루프 스킵을 걸러 "형식만 통과"를 차단한다.

    dartlab 이야기만 (2)(3)이 다르다. 이미지 개수를 고정 하한으로 요구하지 않고, 기획(imagePlan)이
    정한 만큼 실물이 있는지를 본다. 교육 연재는 편마다 필요한 그림 수가 다르고, 하한을 두면
    채우기용 이미지가 붙는다."""
    idx = post_dir / "index.md"
    if not idx.is_file():
        return [f"index.md 없음: {post_dir}"]
    raw = idx.read_text(encoding="utf-8")
    body = strip_frontmatter(raw)
    cat = _clean_scalar(frontmatter_value(raw, "category"))
    fails: list[str] = []
    if cat not in CONTENT_GENRE_CATEGORIES:
        fails.extend(_validate_common_body_plainness(body, cat))
        return fails  # 단문 카테고리는 공통 편집 계약만 검사하고 심층 계약은 제외

    slug = re.sub(r"^\d+-", "", post_dir.name)
    assets = post_dir / "assets"
    asset_photos = []
    if assets.is_dir():
        for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
            asset_photos += list(assets.glob(ext))
    served_photos = [path for path in asset_photos if "thumbnail-bg" not in path.name]

    plan, _, plan_fails = _load_plan(post_dir)
    contractVersion = _planContractVersion(plan)
    # 1. 콘텐츠 OG 카드 (리스트/공유 미리보기). 중앙 카탈로그가 있으면 계약 버전과 무관하게 HF를 검증한다.
    og = _clean_scalar(frontmatter_value(raw, "ogImage"))
    manifest, manifestErrors = loadMediaManifest(post_dir)
    if isinstance(manifest, dict) and not manifestErrors:
        manifestOg = manifest.get("og") if isinstance(manifest, dict) else None
        expectedOg = mediaUrl(str(manifestOg.get("path") or "")) if isinstance(manifestOg, dict) else ""
        if not expectedOg or og != expectedOg:
            fails.append(f"ogImage는 media/catalog.json의 HF URL이어야 함(현재 {og!r})")
        manifestCard = manifest.get("card")
        if isinstance(manifestCard, dict):
            cardPreview = _clean_scalar(frontmatter_value(raw, "cardPreview"))
            expectedCard = mediaUrl(str(manifestCard.get("path") or ""))
            if cardPreview != expectedCard:
                fails.append(f"cardPreview는 media/catalog.json의 card HF URL이어야 함(현재 {cardPreview!r})")
    elif contractVersion == BLOG_PLAN_CONTRACT_VERSION:
        fails.extend(manifestErrors)
    elif not _OG_RE.match(og):
        fails.append(f"ogImage가 /thumbnails/*.webp 콘텐츠 OG가 아님(현재 {og!r}). 기본 아바타 폴백 금지")
    else:
        og_file = repo_root() / "landing" / "static" / og.lstrip("/")
        if not og_file.is_file():
            fails.append(f"OG 파일 없음: landing/static{og} (render_og_cards 미실행)")

    body_photos = re.findall(r"!\[[^\]]*\]\([^)]+\.(?:webp|jpg|jpeg|png)\)", body)

    if requireContractV2 and _planContractVersion(plan) != BLOG_PLAN_CONTRACT_VERSION:
        fails.append(f"신규 글은 brief.json contractVersion {BLOG_PLAN_CONTRACT_VERSION}가 필요함")

    # 0. 본문이 썸네일 합성 소스를 걸면 그 이미지는 화면에 뜨지 않는다. landing/vite.config.ts 의
    #    blogAssetsPlugin 이 `*thumbnail-bg.webp` 를 서빙 대상에서 일부러 뺀다(카테고리마다 NN 이
    #    다시 시작해 basename 이 전역 충돌하기 때문). 발행된 글 여러 편이 이미 이 함정에 빠져 있다.
    if re.search(r"!\[[^\]]*\]\([^)]*thumbnail-bg[^)]*\.webp\)", body):
        fails.append(
            "본문이 thumbnail-bg 계열 파일을 참조함. 서빙되지 않아 이미지가 깨진다. 고유 파일명으로 사본을 두고 그것을 걸어라"
        )

    # 2·3. 이미지. dartlab 이야기는 기획이 정한 만큼, 나머지 장르는 콘텐츠 이미지 하한.
    if contractVersion == BLOG_PLAN_CONTRACT_VERSION:
        planned = _image_plan(plan)
        if len(body_photos) < len(planned):
            fails.append(f"기획 imagePlan {len(planned)}장인데 HF 본문 이미지 {len(body_photos)}장")
    elif cat == "dartlab-stories":
        planned = _image_plan(plan)
        inline = [x for x in planned if str(x.get("slot") or "") != "hero"]
        availablePhotos = body_photos if isinstance(manifest, dict) else served_photos
        if len(availablePhotos) < len(planned):
            fails.append(
                f"기획 imagePlan {len(planned)}장인데 본문용 이미지 {len(availablePhotos)}장. 기획한 만큼 수급 필요"
            )
        if len(body_photos) < len(inline):
            fails.append(f"기획 inline {len(inline)}장인데 본문 삽입 {len(body_photos)}장")
    else:
        if not isinstance(manifest, dict) and not served_photos:
            fails.append("assets에 콘텐츠 이미지 0장(손수 SVG는 이미지 계획 대체 아님). imagePlan 수급 필요")
        if not body_photos:
            fails.append("본문 콘텐츠 이미지 0장(![](*.webp) 필요). 손수 SVG만으로는 시각 부실")

    # 4. 장르별 깊이 하드 블록
    pc = prose_char_count(body)
    threshold = min_prose_chars(cat)
    if pc < threshold:
        fails.append(
            f"본문 {pc}자 < {cat} 하한 {threshold}자(목표 {target_prose_chars(cat)}). blog_plan_loop 막 구조로 심화 필요"
        )

    # 5. 기획 루프 산출물(스토리·비주얼·근거·재평가 증거)
    fails.extend(plan_fails)
    fails.extend(_validate_genre_body(raw, body, cat))
    fails.extend(_validateImageSsot(post_dir, body, plan))
    fails.extend(_validateScenarioBody(body, plan, cat))

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
