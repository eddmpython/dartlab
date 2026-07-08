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

# 심층 콘텐츠 깊이 게이트 (본문 기준: 표·SVG·코드 제외한 읽는 글자수).
# 길이는 막·증거·시나리오의 산물이지 패딩이 아니다 (반복도 가드와 짝).
CONTENT_GENRE_CATEGORIES = {"company-reports", "tech-story", "data-reports", "investment-stories"}
DEEP_GENRE_CATEGORIES = set(CONTENT_GENRE_CATEGORIES)
GENRE_MIN_PROSE_CHARS = {
    "company-reports": 14000,
    "tech-story": 6000,
    "data-reports": 4000,
    "investment-stories": 5000,
}
GENRE_TARGET_PROSE_CHARS = {
    "company-reports": 20000,
    "tech-story": 9000,
    "data-reports": 6500,
    "investment-stories": 8000,
}
DEEP_MIN_PROSE_CHARS = GENRE_MIN_PROSE_CHARS["company-reports"]
DEEP_TARGET_PROSE_CHARS = GENRE_TARGET_PROSE_CHARS["company-reports"]
BLOG_REVIEW_SCORE_MIN = 92
BLOG_LOOP_WORKFLOW_NAME = "blog_plan_loop.workflow.js"
PLAN_CANDIDATE_FILES = ("brief.json", "plan.json")
BLOG_REQUIRED_PLAN_FIELDS = (
    "titleContract",
    "readerQuestion",
    "insight",
    "acts",
    "visuals",
    "imagePlan",
    "relatedPosts",
    "honestyGuards",
    "evidenceMap",
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


def _validate_common_plan(plan: dict[str, object], payload: dict[str, object], *, label: str) -> list[str]:
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

    insight = plan.get("insight") if isinstance(plan.get("insight"), dict) else {}
    for field in ("commonBelief", "twistFact", "whatToWatch", "freshnessArgument"):
        if _compact_len(insight.get(field)) < 20:
            fails.append(f"{label}: insight.{field} 이 너무 약함")
    refs = insight.get("evidenceRefs") if isinstance(insight.get("evidenceRefs"), list) else []
    if not refs:
        fails.append(f"{label}: insight.evidenceRefs 누락")

    acts = plan.get("acts") if isinstance(plan.get("acts"), list) else []
    if len(acts) < 6:
        fails.append(f"{label}: acts 는 6막 이상이어야 함(현재 {len(acts)})")
    for idx, raw in enumerate(acts, start=1):
        if not isinstance(raw, dict):
            fails.append(f"{label}: acts[{idx}] 은 객체여야 함")
            continue
        for field in ("heading", "scene", "causalBridge"):
            if _compact_len(raw.get(field)) < 10:
                fails.append(f"{label}: acts[{idx}].{field} 이 너무 약함")
        if not str(raw.get("purpose") or "").strip():
            fails.append(f"{label}: acts[{idx}].purpose 누락")

    visuals = plan.get("visuals") if isinstance(plan.get("visuals"), list) else []
    if len(visuals) < 3:
        fails.append(f"{label}: visuals 는 막별로 최소 3개 이상 기획해야 함(현재 {len(visuals)})")
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
    if len(image_plan) < 3:
        fails.append(f"{label}: imagePlan 은 hero 1장 + inline 2장 이상이어야 함(현재 {len(image_plan)})")
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


def _validate_genre_body(raw: str, body: str, category: str) -> list[str]:
    fails: list[str] = []
    topic_slug = _clean_scalar(frontmatter_value(raw, "topicSlug"))
    stock_code = _clean_scalar(frontmatter_value(raw, "stockCode"))
    upper_body = body.upper()

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
    return fails


def _validate_plan_file(post_dir: Path) -> list[str]:
    plan_path, payload, load_fails = _find_plan_payload(post_dir)
    if load_fails:
        return load_fails
    assert payload is not None and plan_path is not None
    plan = _plan_from_payload(payload)
    if not isinstance(plan, dict):
        return [f"{plan_path.name}: plan 이 객체가 아님"]
    return _validate_common_plan(plan, payload, label=plan_path.name)


def publish_gate(post_dir: Path) -> list[str]:
    """단일 글 발행 하드 게이트. 위반 리스트 반환(비면 통과).

    기업이야기·기술이야기·데이터리포트·투자이야기 기준으로 (1)실사 OG 카드 (2)실사 hero webp
    (3)본문 실사 사진 1장 이상 (4)장르별 본문 깊이 (5)기획 루프 산출물(brief.json)을 강제한다.
    손수 SVG·기본 아바타·얕은 본문·루프 스킵을 걸러 "형식만 통과"를 차단한다."""
    idx = post_dir / "index.md"
    if not idx.is_file():
        return [f"index.md 없음: {post_dir}"]
    raw = idx.read_text(encoding="utf-8")
    body = strip_frontmatter(raw)
    cat = _clean_scalar(frontmatter_value(raw, "category"))
    fails: list[str] = []
    if cat not in CONTENT_GENRE_CATEGORIES:
        return fails  # 교육·소식 등 단문 카테고리는 여기서 제외

    slug = re.sub(r"^\d+-", "", post_dir.name)
    assets = post_dir / "assets"
    photos = []
    if assets.is_dir():
        for ext in ("*.webp", "*.jpg", "*.jpeg", "*.png"):
            photos += list(assets.glob(ext))

    # 1. 실사 OG 카드 (리스트/공유 미리보기). 기본 아바타 폴백이면 실패.
    og = _clean_scalar(frontmatter_value(raw, "ogImage"))
    if not _OG_RE.match(og):
        fails.append(f"ogImage가 /thumbnails/*.webp 실사 OG가 아님(현재 {og!r}). 기본 아바타 폴백 금지")
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

    # 4. 장르별 깊이 하드 블록
    pc = prose_char_count(body)
    threshold = min_prose_chars(cat)
    if pc < threshold:
        fails.append(
            f"본문 {pc}자 < {cat} 하한 {threshold}자(목표 {target_prose_chars(cat)}). blog_plan_loop 막 구조로 심화 필요"
        )

    # 5. 기획 루프 산출물(스토리·비주얼·근거·재평가 증거)
    fails.extend(_validate_plan_file(post_dir))
    fails.extend(_validate_genre_body(raw, body, cat))

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
