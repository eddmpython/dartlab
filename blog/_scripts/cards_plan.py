"""Landing /cards planning helpers.

`cards.plan.json` is the bridge between the blog article, the editorial
carousel, and image_gen assets. Existing legacy carousels may not have a plan;
when a plan exists, publish tooling treats it as a real gate.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
BLOG_DIR = ROOT / "blog" / "05-company-reports"
ISSUES_DIR = ROOT / "blog" / "_issues"
SNS_ASSETS_DIR = ROOT / "sns" / "assets"
PLAN_FILE = "cards.plan.json"

PLAN_VERSION = 4
SUPPORTED_PLAN_VERSIONS = {1, 2, 3, PLAN_VERSION}
STRICT_FLOW_MIN_VERSION = 3  # 이 버전 이상이면 큰문장 흐름(연결·판단형 종결)을 강제 검사
INSIGHT_MIN_VERSION = 4  # 이 버전 이상이면 insightContract(통념·반전·렌즈)를 강제
LEGACY_MIN_IMAGES = 5
MIN_IMAGES = 7
RECOMMENDED_MAX_IMAGES = 10
ASSET_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
FORBIDDEN_ASSET_TOKENS = ("card", "thumbnail", "thumb")
STRUCTURE_KICKER_LABELS = {"기", "승", "전", "결", "서론", "본론", "전개", "결론", "도입", "마무리"}
VISIBLE_STRUCTURE_LABEL_RULE = "기/승/전/결 같은 구조명은 내부 기획에만 쓰고 카드 위 라벨로 노출하지 않는다."
REQUIRED_REVIEW_ROUNDS = (
    "writerPanel",
    "honestyEvidence",
    "imageFit",
    "readerFit",
    "reevaluation",
)
NARRATIVE_RULES = (
    "한 주제 안에서 훅 -> 왜 지금 중요한가 -> 근거 -> 전환 -> 판단 질문으로 이어진다.",
    "각 슬라이드는 앞장의 주장이나 숫자를 받아 다음 장으로 넘겨야 한다.",
    "서로 끊긴 체크리스트, '다음에는 이것을 본다'식 나열, 새 항목만 덧붙이는 끝맺음은 실패다.",
    "마지막 장은 새 정보를 추가하는 장이 아니라 앞선 주장과 근거를 종합해 독자가 남길 판단 질문으로 닫는다.",
)
BIG_SENTENCE_RULES = (
    "카드는 7장 이상으로 잡고, 큰문장만 이어 읽어도 한 편의 짧은 글처럼 이해되어야 한다.",
    "각 장의 큰문장은 단어·라벨·메모가 아니라 앞장 뒤에 붙는 완성 문장이어야 한다.",
    "숫자 카드는 bigNumber만 던지지 말고 context에 그 숫자가 앞장 주장과 어떻게 이어지는지 문장으로 쓴다.",
    "중간 장은 '이 구조', '그 결과', '하지만', '그래서', '결국'처럼 앞장과의 관계를 자연스럽게 드러낸다.",
    "마지막 장은 새 항목 소개가 아니라 앞선 흐름에서 나온 판단 문장으로 닫는다.",
)
PLAIN_LANGUAGE_RULES = (
    "카드 문장은 독자가 소리 내어 읽어도 자연스러운 한국어 문장이어야 한다.",
    "전문용어와 약어를 앞세우지 말고 쉬운 말로 먼저 설명한다.",
    "꼭 필요한 산업 용어는 짧은 설명에 풀어 쓰되, 슬라이드 본문은 가능한 쉬운 말로 쓴다.",
    "브랜드명과 공식 제품명은 허용하지만, 의미를 설명하지 않은 약어는 실패다.",
)
INSIGHT_CONTRACT_FIELDS = ("commonBelief", "twistFact", "whatToWatch")
INSIGHT_CONTRACT_RULES = (
    "통념(commonBelief): 독자가 당연하게 여기는 상식·헤드라인 관점을 한 문장으로 적는다.",
    "반전 사실(twistFact): 그 통념과 충돌하는, 공시 직독으로 확인한 단 하나의 사실 + 왜 그게 가능한가(메커니즘)를 적는다. 제목·캡션의 재진술이면 인사이트가 아니다.",
    "그래서 볼 것(whatToWatch): 독자가 이 덱을 본 뒤 앞으로 무엇을 다르게 볼지(렌즈·관전 포인트)를 적는다.",
    "evidenceRefs: 반전·렌즈를 떠받치는 실측 수치나 ref 를 최소 1개 이상 적는다(분모·기간 명시).",
)
JARGON_REPLACEMENTS = {
    "AI": "인공지능",
    "ARR": "연간 반복 매출",
    "EDR": "단말 보안 대응",
    "SOC": "보안 관제",
    "FCF": "잉여현금흐름",
    "ID": "계정",
    "CDMO": "위탁개발생산",
    "HBM": "고대역폭 메모리",
    "HBM4E": "차세대 고대역폭 메모리",
    "GPU": "그래픽처리장치",
    "MR-MUF": "보호재 충전 패키징",
    "Gbps": "기가비트/초",
}
CHECKLIST_PHRASES = (
    "다음 체크포인트",
    "다음 질문",
    "체크포인트는",
    "다음에 이것",
    "다음에는 이것",
)
CONTINUITY_TOKENS = (
    "그래서",
    "하지만",
    "그런데",
    "그다음",
    "그 다음",
    "두 번째",
    "세 번째",
    "반대로",
    "여기서",
    "이 구조",
    "이 숫자",
    "이 돈",
    "이 흐름",
    "이 회사",
    "그 구조",
    "그 숫자",
    "그 돈",
    "그 결과",
    "여기에",
    "문제는",
    "답은",
    "핵심은",
    "결국",
    "이어집니다",
    "바뀝니다",
    "남습니다",
)
CLOSING_TOKENS = (
    "결국",
    "그래서",
    "남는",
    "판단",
    "확인",
    "보면",
    "봐야",
    "물어야",
    "힘",
    "약해",
    "강해",
)
SENTENCE_END_RE = re.compile(r"[다요까죠][.!?…)]*$")

# ── 렌더링 계약 레지스트리 — 카드가 쓸 수 있는 시각 계약의 공식 카탈로그(정례화) ──
# 기획이 beat 마다 큰문장 + visual 계약을 선언한다. 부른 계약이 RENDERABLE(렌더러 구현분)이면 통과,
# REGISTERED 이나 렌더러 미구현(예: finChart)이면 게이트가 "계약 추가(확장 루프)"로 막는다 —
# 파이프라인이 가장 강한 기획에 맞춰 자라게 하는 닫힌 루프의 기계 게이트. SSOT 표는 operation.content.
LAYOUT_CONTRACTS = ("editorial", "editorialBeat", "editorialStat")
VISUAL_CONTRACTS_RENDERABLE = ("bars", "line", "table")  # CardSlide 에 렌더러 구현분 — 발행 통과
VISUAL_CONTRACTS_REGISTERED = (
    "bars",
    "line",
    "table",
    "finChart",
)  # 카탈로그 등록분(finChart=등록만, 렌더러는 확장 루프로)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_yaml_frontmatter(md_path: Path) -> tuple[dict[str, Any], str]:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    return (fm if isinstance(fm, dict) else {}), parts[2]


def slug_from_folder(folder_name: str) -> str:
    return re.sub(r"^\d+-", "", folder_name)


def code_from(fm: dict[str, Any], slug: str) -> str:
    code = str(fm.get("stockCode", "")).strip()
    if code:
        return code
    first = slug.split("-", 1)[0]
    return first if first.isdigit() and len(first) == 6 else ""


def sanitize_key(value: str, fallback: str) -> str:
    # Keep ASCII semantic keys because the hfMedia asset index is filename-based.
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    lowered = re.sub(r"-{2,}", "-", lowered)
    if not lowered:
        lowered = fallback
    if any(token in lowered for token in FORBIDDEN_ASSET_TOKENS) or lowered.startswith(("og-", "og_")):
        lowered = f"scene-{lowered}"
    return lowered[:63].strip("-") or fallback


def normalize_slide(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    layout = raw.get("layout")
    if layout not in {"editorial", "editorialBeat", "editorialStat"}:
        return None
    return {k: v for k, v in raw.items() if v not in (None, "")}


def requested_image_count(slides: list[dict[str, Any]], count: int | None) -> int:
    if count is not None:
        if count < MIN_IMAGES:
            raise ValueError(f"--count must be at least {MIN_IMAGES}")
        return count
    return max(MIN_IMAGES, len(slides) or MIN_IMAGES)


def clean_card_text(value: object) -> str:
    return " ".join(str(value or "").replace("[[", "").replace("]]", "").split())


def slide_line(slide: dict[str, Any]) -> str:
    for key in ("line", "context", "sub", "kicker", "bigNumber"):
        value = clean_card_text(slide.get(key, ""))
        if value:
            return value
    return "핵심 장면"


def big_sentence_for_slide(slide: dict[str, Any]) -> str:
    layout = str(slide.get("layout") or "")
    if layout == "editorialStat":
        context = clean_card_text(slide.get("context"))
        kicker = clean_card_text(slide.get("kicker"))
        number = clean_card_text(" ".join(str(slide.get(k) or "") for k in ("bigNumber", "unit")))
        if context and number:
            prefix = f"{kicker} {number}".strip()
            return f"{prefix}: {context}" if prefix and prefix not in context else context
        return context or f"{kicker} {number}".strip()
    return clean_card_text(slide.get("line") or slide.get("sub") or slide.get("context") or slide.get("kicker"))


def big_sentence_strip(slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order": idx,
            "layout": str(slide.get("layout") or ""),
            "mainText": big_sentence_for_slide(slide),
        }
        for idx, slide in enumerate(slides, start=1)
    ]


def scene_role(order: int, count: int, slide: dict[str, Any] | None) -> str:
    if order == 1:
        return "cover-hook"
    if order == count:
        return "closing-checkpoint"
    if slide and slide.get("layout") == "editorialStat":
        return "number-evidence"
    if slide and slide.get("layout") == "editorialBeat":
        return "narrative-turn"
    return "business-context"


def narrative_contract() -> dict[str, Any]:
    return {
        "spine": "훅 -> 왜 지금 중요한가 -> 근거 -> 전환 -> 판단 질문",
        "rules": [*NARRATIVE_RULES, VISIBLE_STRUCTURE_LABEL_RULE],
    }


def big_sentence_contract(slides: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "slideRange": f"{MIN_IMAGES}장 이상({MIN_IMAGES}~{RECOMMENDED_MAX_IMAGES}장 권장, 필요하면 초과)",
        "mainTextFields": {
            "editorial": "line",
            "editorialBeat": "line",
            "editorialStat": "context",
        },
        "rules": list(BIG_SENTENCE_RULES),
        "strip": big_sentence_strip(slides),
    }


def plain_language_contract() -> dict[str, Any]:
    return {
        "rules": list(PLAIN_LANGUAGE_RULES),
        "preferredRewrites": dict(JARGON_REPLACEMENTS),
    }


def insight_contract() -> dict[str, Any]:
    """인사이트 계약 — 빈 스캐폴드. v4+ 발행 게이트는 통념·반전·렌즈가 채워졌는지 강제한다.

    충돌하는 사실에서 멈추지 않고, 왜 가능한가(메커니즘)와 독자가 앞으로 무엇을 다르게
    볼지(렌즈)까지 적게 해 '매끄럽지만 알맹이 없는' 덱을 기획 단계에서 막는다.
    """
    return {
        "rules": list(INSIGHT_CONTRACT_RULES),
        "commonBelief": "",
        "twistFact": "",
        "whatToWatch": "",
        "evidenceRefs": [],
    }


def scene_for(role: str, topic: str, corp_name: str, slide: dict[str, Any] | None) -> str:
    cue = slide_line(slide or {})
    subject = corp_name or topic
    if role == "cover-hook":
        return f"story-specific opening scene for {subject}, making the article angle '{cue}' visible through a concrete asset, place, or operation"
    if role == "number-evidence":
        return f"real-world {subject} operation or evidence scene behind the number '{cue}', using physical production, facility, customer, or supply-chain context instead of charts"
    if role == "narrative-turn":
        return f"editorial business-news scene tied to {subject}, showing the turning point '{cue}' through physical work, demand, location, or operations"
    if role == "closing-checkpoint":
        return f"quiet final-check scene tied to {subject} for the reader to verify '{cue}', such as documents, equipment, facility context, or customer workflow"
    return f"specific business context scene for {subject} and '{cue}' with concrete objects, work sites, locations, or customer context"


def prompt_for(
    *,
    asset_root: str,
    asset_key: str,
    title: str,
    corp_name: str,
    code: str,
    role: str,
    scene: str,
    reason: str,
) -> str:
    subject = f"{corp_name} ({code})" if code else title
    return "\n".join(
        [
            "Use case: photorealistic-natural",
            f"Asset type: vertical landing /cards news-card background for {asset_root}/{asset_key}.webp",
            f"Asset key: {asset_key}",
            f"Primary request: Create a realistic editorial image for DartLab landing /cards about {subject}.",
            f"Story title: {title}.",
            f"Carousel role: {role}.",
            f"Image subject: {scene}.",
            f"Image reason: {reason}.",
            "Story specificity: make the image feel planned for this exact article, company, event, location, facility, product, or operating question; avoid generic stock-finance imagery.",
            "Concrete-scene requirement: translate abstract business words into physical subjects from the story, such as products, facilities, process equipment, quality tests, logistics, customer workflow, or field operations.",
            "Composition/framing: strict vertical 4:5 image; keep the main subject in the upper and middle 60%; keep the lower 40% natural but non-critical so text overlays remain readable.",
            "Style/medium: realistic business-news photography, not illustration, not a chart, not an infographic.",
            "Lighting/mood: bright enough to survive a dark overlay; real-world depth and contrast; no heavy vignette.",
            "Brand/name handling: company and trade names may be used as context. Do not fabricate an official logo, official document, real facility interior, or readable claim; incidental public signage is acceptable only when it supports the article and is not the main subject.",
            "Constraints: no watermark, no recognizable public figure, no fake chart, no fake newspaper, no fabricated official badge, no brand packaging close-up.",
            "Avoid: collage, split panels, gradients, abstract glow, bokeh-only background, generic financial wallpaper, blacked-out half frame, 9:16 crop, ultra-tall phone wallpaper.",
        ]
    )


def build_image_plan(
    *,
    title: str,
    slug: str,
    corp_name: str,
    code: str,
    asset_root: str,
    slides: list[dict[str, Any]],
    count: int | None,
) -> list[dict[str, Any]]:
    n = requested_image_count(slides, count)
    out: list[dict[str, Any]] = []
    used_keys: set[str] = set()
    for idx in range(1, n + 1):
        slide = slides[idx - 1] if idx - 1 < len(slides) else None
        role = scene_role(idx, n, slide)
        asset_key = sanitize_key(f"scene-{idx:02d}-{role}", f"scene-{idx:02d}")
        while asset_key in used_keys:
            asset_key = sanitize_key(f"{asset_key}-{idx}", f"scene-{idx:02d}")
        used_keys.add(asset_key)
        scene = scene_for(role, title, corp_name, slide)
        reason = "그 글의 회사·사건·장소·운영 질문을 한 장면으로 묶는 시각 앵커"
        out.append(
            {
                "order": idx,
                "assetKey": asset_key,
                "slideRefs": [idx] if slide else [],
                "role": role,
                "scene": scene,
                "reason": reason,
                "status": "planned",
                "prompt": prompt_for(
                    asset_root=asset_root,
                    asset_key=asset_key,
                    title=title,
                    corp_name=corp_name,
                    code=code,
                    role=role,
                    scene=scene,
                    reason=reason,
                ),
            }
        )
    return out


def review_gate(status: str = "planned") -> dict[str, Any]:
    return {
        "status": status,
        "requiredRounds": [
            {
                "id": "writerPanel",
                "purpose": "표지 후크(호기심 갭), 서사 스파인, 앞장-다음장의 긴장 전진(연결만이 아니라 매 장이 질문을 얹거나 갚는가), 인사이트(통념과 충돌하는 사실 + 메커니즘 + 독자 렌즈), 표지 약속을 마지막이 갚는가(promise·payoff), 쉬운 말·문장 리듬을 본다. 순서를 바꿔도 말이 되는 덱, 충돌 사실만 던지고 끝나는 덱, 체크리스트식 나열은 실패다.",
                "status": "todo",
            },
            {
                "id": "honestyEvidence",
                "purpose": "슬라이드 숫자와 주장 근거가 블로그 본문/검증표에 있는지 본다.",
                "status": "todo",
            },
            {
                "id": "imageFit",
                "purpose": "7장 이상 이미지가 그 글의 회사·사건·장소에 맞는 서로 다른 의미 장면인지, 가짜 공식 로고·텍스트·도식이 없는지 본다.",
                "status": "todo",
            },
            {
                "id": "readerFit",
                "purpose": "처음 보는 독자가 첫 장부터 마지막 장까지 끊기지 않고 자연스럽게 읽으며 관전 포인트를 이해하는지 본다. 어려운 약어가 남으면 실패다.",
                "status": "todo",
            },
            {
                "id": "reevaluation",
                "purpose": "수정 후 같은 패널이 다시 보고 발행 가능 여부를 닫는다.",
                "status": "todo",
            },
        ],
        "decisionLog": [],
    }


def build_company_post_plan(post_dir: Path, *, count: int | None = None) -> dict[str, Any]:
    fm, body = read_yaml_frontmatter(post_dir / "index.md")
    carousel = fm.get("carousel") if isinstance(fm.get("carousel"), dict) else {}
    slides = [s for raw in carousel.get("slides", []) if (s := normalize_slide(raw))]
    slug = slug_from_folder(post_dir.name)
    code = code_from(fm, slug)
    title = str(carousel.get("title") or fm.get("title") or slug)
    corp_name = str(fm.get("corpName") or carousel.get("name") or code or title)
    asset_root = f"sns/assets/{code or slug}"
    return {
        "version": PLAN_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "target": {
            "kind": "companyPost",
            "slug": slug,
            "stockCode": code,
            "corpName": corp_name,
            "title": title,
            "postPath": rel(post_dir / "index.md"),
            "assetRoot": asset_root,
            "planPath": rel(post_dir / PLAN_FILE),
        },
        "planning": {
            "blogThesis": str(fm.get("description") or title).strip(),
            "cardThesis": str(carousel.get("caption") or title).strip().splitlines()[0],
            "audienceQuestion": f"{corp_name} 이야기를 /cards에서 넘길 때 첫 장에서 무엇을 궁금해해야 하나?",
            "blogAndCardsTogether": True,
            "narrativeContract": narrative_contract(),
            "bigSentenceContract": big_sentence_contract(slides),
            "plainLanguageContract": plain_language_contract(),
            "insightContract": insight_contract(),
            "bodyPreview": " ".join(body.strip().split())[:360],
        },
        "carousel": {
            "slideCount": len(slides),
            "layouts": [str(s.get("layout")) for s in slides],
        },
        "imagePlan": build_image_plan(
            title=title,
            slug=slug,
            corp_name=corp_name,
            code=code,
            asset_root=asset_root,
            slides=slides,
            count=count,
        ),
        "imagegen": {
            "tool": "GPT image_gen",
            "generationRule": "각 imagePlan.prompt 를 한 장씩 image_gen 으로 생성한다. 프롬프트는 그 글의 회사·사건·장소·운영 질문을 상징하는 실제 사용용 이미지를 목표로 하며, 범용 금융 배경은 탈락시킨다.",
            "extractCommand": (
                "uv run python -X utf8 sns/scripts/extractImagegenAssets.py "
                f"{code or slug} --count {requested_image_count(slides, count)} "
                "--names "
                + ",".join(
                    item["assetKey"]
                    for item in build_image_plan(
                        title=title,
                        slug=slug,
                        corp_name=corp_name,
                        code=code,
                        asset_root=asset_root,
                        slides=slides,
                        count=count,
                    )
                )
                + f' --keywords "{corp_name},{slug}"'
            ),
            "checkCommand": f"uv run python -X utf8 sns/scripts/checkImagegenAssets.py {code or slug}",
            "publishCommands": [
                "uv run python -X utf8 sns/scripts/build_index.py",
                "uv run python -X utf8 sns/scripts/publish_assets_hf.py",
                "uv run python -X utf8 blog/_scripts/build_carousel_contracts.py",
            ],
        },
        "reviewGate": review_gate(),
    }


def build_issue_plan(issue_dir: Path, *, count: int | None = None) -> dict[str, Any]:
    data = yaml.safe_load((issue_dir / "carousel.yaml").read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        data = {}
    slides = [s for raw in data.get("slides", []) if (s := normalize_slide(raw))]
    slug = issue_dir.name
    title = str(data.get("title") or data.get("name") or slug)
    code = code_from(data, slug)
    corp_name = str(data.get("corpName") or data.get("name") or code or "")
    asset_root = f"blog/_issues/{slug}/assets"
    names = ",".join(
        item["assetKey"]
        for item in build_image_plan(
            title=title, slug=slug, corp_name=corp_name, code=code, asset_root=asset_root, slides=slides, count=count
        )
    )
    keyword_bits = ",".join(bit for bit in (corp_name, slug, title) if bit)
    return {
        "version": PLAN_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "target": {
            "kind": "issue",
            "slug": slug,
            "stockCode": code,
            "corpName": corp_name,
            "title": title,
            "postPath": rel(issue_dir / "carousel.yaml"),
            "assetRoot": asset_root,
            "planPath": rel(issue_dir / PLAN_FILE),
        },
        "planning": {
            "blogThesis": str(data.get("caption") or title).strip().splitlines()[0],
            "cardThesis": str(data.get("caption") or title).strip().splitlines()[0],
            "audienceQuestion": f"{title} 이슈를 /cards에서 볼 때 마지막에 무엇을 확인해야 하나?",
            "blogAndCardsTogether": False,
            "narrativeContract": narrative_contract(),
            "bigSentenceContract": big_sentence_contract(slides),
            "plainLanguageContract": plain_language_contract(),
            "insightContract": insight_contract(),
            "bodyPreview": "",
        },
        "carousel": {
            "slideCount": len(slides),
            "layouts": [str(s.get("layout")) for s in slides],
        },
        "imagePlan": build_image_plan(
            title=title,
            slug=slug,
            corp_name=corp_name,
            code=code,
            asset_root=asset_root,
            slides=slides,
            count=count,
        ),
        "imagegen": {
            "tool": "GPT image_gen",
            "generationRule": "각 imagePlan.prompt 를 한 장씩 image_gen 으로 생성한다. 프롬프트는 그 글의 회사·사건·장소·운영 질문을 상징하는 실제 사용용 이미지를 목표로 하며, 범용 금융 배경은 탈락시킨다.",
            "extractCommand": (
                "uv run python -X utf8 sns/scripts/extractImagegenAssets.py "
                f"assets --assets-root blog/_issues/{slug} --count {requested_image_count(slides, count)} "
                f'--names {names} --keywords "{keyword_bits}"'
            ),
            "checkCommand": f"uv run python -X utf8 sns/scripts/checkImagegenAssets.py blog/_issues/{slug}/assets",
            "publishCommands": [
                "uv run python -X utf8 blog/_scripts/build_carousel_contracts.py",
            ],
        },
        "reviewGate": review_gate(),
    }


def validate_plan(plan: dict[str, Any], *, require_passed: bool = True, require_assets: bool = False) -> list[str]:
    errors: list[str] = []
    target = plan.get("target") if isinstance(plan.get("target"), dict) else {}
    slug = str(target.get("slug") or "<unknown>")
    version = plan.get("version")
    if version not in SUPPORTED_PLAN_VERSIONS:
        errors.append(f"{slug}: version 은 {sorted(SUPPORTED_PLAN_VERSIONS)} 중 하나여야 함")
    strict_big_sentence = isinstance(version, int) and version >= STRICT_FLOW_MIN_VERSION
    require_insight = isinstance(version, int) and version >= INSIGHT_MIN_VERSION
    for field in ("kind", "slug", "title", "assetRoot"):
        if not str(target.get(field, "")).strip():
            errors.append(f"{slug}: target.{field} 누락")
    planning = plan.get("planning") if isinstance(plan.get("planning"), dict) else {}
    for field in ("blogThesis", "cardThesis", "audienceQuestion"):
        if not str(planning.get(field, "")).strip():
            errors.append(f"{slug}: planning.{field} 누락")
    narrative = planning.get("narrativeContract")
    if not isinstance(narrative, dict):
        errors.append(f"{slug}: planning.narrativeContract 누락")
    else:
        rules = narrative.get("rules")
        if not isinstance(rules, list):
            errors.append(f"{slug}: planning.narrativeContract.rules 는 리스트여야 함")
            rules = []
        rule_texts = {str(rule).strip() for rule in rules}
        missing_rules = [rule for rule in NARRATIVE_RULES if rule not in rule_texts]
        if missing_rules:
            errors.append(f"{slug}: planning.narrativeContract 필수 규칙 누락 {len(missing_rules)}건")
    if strict_big_sentence:
        big_sentence = planning.get("bigSentenceContract")
        if not isinstance(big_sentence, dict):
            errors.append(f"{slug}: planning.bigSentenceContract 누락")
        else:
            rules = big_sentence.get("rules")
            if not isinstance(rules, list):
                errors.append(f"{slug}: planning.bigSentenceContract.rules 는 리스트여야 함")
                rules = []
            rule_texts = {str(rule).strip() for rule in rules}
            missing_rules = [rule for rule in BIG_SENTENCE_RULES if rule not in rule_texts]
            if missing_rules:
                errors.append(f"{slug}: planning.bigSentenceContract 필수 규칙 누락 {len(missing_rules)}건")
            strip = big_sentence.get("strip")
            if not isinstance(strip, list) or not strip:
                errors.append(f"{slug}: planning.bigSentenceContract.strip 누락")
    plain = planning.get("plainLanguageContract")
    if not isinstance(plain, dict):
        errors.append(f"{slug}: planning.plainLanguageContract 누락")
    else:
        rules = plain.get("rules")
        if not isinstance(rules, list):
            errors.append(f"{slug}: planning.plainLanguageContract.rules 는 리스트여야 함")
            rules = []
        rule_texts = {str(rule).strip() for rule in rules}
        missing_rules = [rule for rule in PLAIN_LANGUAGE_RULES if rule not in rule_texts]
        if missing_rules:
            errors.append(f"{slug}: planning.plainLanguageContract 필수 규칙 누락 {len(missing_rules)}건")
    if require_insight:
        insight = planning.get("insightContract")
        if not isinstance(insight, dict):
            errors.append(
                f"{slug}: planning.insightContract 누락 — v{INSIGHT_MIN_VERSION}+ 는 통념·반전·렌즈를 적어야 함"
            )
        else:
            for field in INSIGHT_CONTRACT_FIELDS:
                if not str(insight.get(field, "")).strip():
                    errors.append(
                        f"{slug}: planning.insightContract.{field} 누락 — 인사이트는 통념·반전·렌즈를 모두 적어야 함"
                    )
            refs = insight.get("evidenceRefs")
            if not isinstance(refs, list) or not [r for r in refs if str(r).strip()]:
                errors.append(f"{slug}: planning.insightContract.evidenceRefs 누락 — 반전을 떠받치는 실측 ref 최소 1개")
            twist = re.sub(r"\s+", "", str(insight.get("twistFact", "")))
            title_norm = re.sub(r"\s+", "", str(target.get("title", "")))
            thesis_norm = re.sub(r"\s+", "", str(planning.get("cardThesis", "")))
            if twist and twist in (title_norm, thesis_norm):
                errors.append(
                    f"{slug}: insightContract.twistFact 가 제목/카드주제의 재진술 — 헤드라인 너머의 사실이어야 함"
                )
            elif twist and len(twist) < 20:
                errors.append(
                    f"{slug}: insightContract.twistFact 가 너무 짧음 — 충돌하는 사실 + 메커니즘을 한 문장으로"
                )
    image_plan = plan.get("imagePlan")
    if not isinstance(image_plan, list):
        errors.append(f"{slug}: imagePlan 은 리스트여야 함")
        image_plan = []
    min_images = MIN_IMAGES if strict_big_sentence else LEGACY_MIN_IMAGES
    if len(image_plan) < min_images:
        errors.append(f"{slug}: imagePlan 은 최소 {min_images}장이어야 함(현재 {len(image_plan)})")
    asset_root = ROOT / str(target.get("assetRoot", ""))
    for idx, item in enumerate(image_plan, start=1):
        if not isinstance(item, dict):
            errors.append(f"{slug}: imagePlan[{idx}] 은 객체여야 함")
            continue
        key = str(item.get("assetKey", "")).strip()
        if not ASSET_KEY_RE.match(key):
            errors.append(f"{slug}: imagePlan[{idx}].assetKey 형식 오류: {key!r}")
        if any(token in key for token in FORBIDDEN_ASSET_TOKENS) or key.startswith(("og-", "og_")):
            errors.append(f"{slug}: imagePlan[{idx}].assetKey 에 비발행 토큰 포함: {key!r}")
        prompt = str(item.get("prompt", ""))
        if "Asset key:" not in prompt or "/cards" not in prompt:
            errors.append(f"{slug}: imagePlan[{idx}].prompt 에 Asset key 또는 /cards 문맥 누락")
        if require_assets and key and not (asset_root / f"{key}.webp").exists():
            errors.append(f"{slug}: 생성 이미지 없음: {rel(asset_root / f'{key}.webp')}")
    gate = plan.get("reviewGate") if isinstance(plan.get("reviewGate"), dict) else {}
    rounds = gate.get("requiredRounds") if isinstance(gate.get("requiredRounds"), list) else []
    round_ids = {str(r.get("id")) for r in rounds if isinstance(r, dict)}
    missing = [r for r in REQUIRED_REVIEW_ROUNDS if r not in round_ids]
    if missing:
        errors.append(f"{slug}: reviewGate.requiredRounds 누락: {', '.join(missing)}")
    if require_passed and gate.get("status") != "passed":
        errors.append(f"{slug}: reviewGate.status 가 passed 가 아님({gate.get('status')!r})")
    if require_passed:
        not_passed = [str(r.get("id")) for r in rounds if isinstance(r, dict) and r.get("status") != "passed"]
        if not_passed:
            errors.append(f"{slug}: review round 미통과: {', '.join(not_passed)}")
    return errors


def _term_in_text(text: str, term: str) -> bool:
    flags = re.IGNORECASE if term.isascii() else 0
    if re.search(r"^[A-Za-z0-9-]+$", term):
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text, flags=flags) is not None
    return term in text


def _contract_reading_texts(contract: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    title = str(contract.get("title") or "").strip()
    if title:
        out.append(("title", title))
    for key in ("caption", "pinnedComment"):
        value = str(contract.get(key) or "").strip()
        if value:
            out.append((key, value))
    for idx, slide in enumerate(contract.get("slides", []), start=1):
        if not isinstance(slide, dict):
            continue
        for key in ("kicker", "line", "sub", "context", "unit"):
            value = str(slide.get(key) or "").strip()
            if value:
                out.append((f"slide[{idx}].{key}", value))
    for idx, item in enumerate(contract.get("explainers", []), start=1):
        if not isinstance(item, dict):
            continue
        for key in ("term", "body"):
            value = str(item.get(key) or "").strip()
            if value:
                out.append((f"explainers[{idx}].{key}", value))
    for idx, item in enumerate(contract.get("relatedNews", []), start=1):
        if not isinstance(item, dict):
            continue
        value = str(item.get("description") or "").strip()
        if value:
            out.append((f"relatedNews[{idx}].description", value))
    return out


def validate_contract_big_sentence_flow(slug: str, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    slides = [s for s in contract.get("slides", []) if isinstance(s, dict)]
    if len(slides) < MIN_IMAGES:
        errors.append(f"{slug}: 큰문장 서사형 카드는 최소 {MIN_IMAGES}장이어야 함(현재 {len(slides)}장)")
        return errors

    strip: list[tuple[int, str, str]] = []
    for idx, slide in enumerate(slides, start=1):
        layout = str(slide.get("layout") or "")
        text = big_sentence_for_slide(slide)
        strip.append((idx, layout, text))
        compact = re.sub(r"[^0-9A-Za-z가-힣]", "", text)
        if layout == "editorialStat" and not clean_card_text(slide.get("context")):
            errors.append(f"{slug} #{idx}: 숫자 카드도 context 에 큰문장 서사를 써야 함")
        if len(compact) < 12:
            errors.append(f"{slug} #{idx}: 큰문장이 너무 짧아 메모처럼 보임: {text!r}")
        if text and not SENTENCE_END_RE.search(text):
            errors.append(f"{slug} #{idx}: 큰문장은 완성 문장으로 끝나야 함: {text!r}")

    continuity_hits = sum(1 for _, _, text in strip[1:-1] if any(token in text for token in CONTINUITY_TOKENS))
    required_hits = max(3, (len(strip) - 2) // 2)
    if continuity_hits < required_hits:
        errors.append(
            f"{slug}: 큰문장 사이 연결어/지시어가 부족함({continuity_hits}/{required_hits}) — "
            "넘겨 읽으면 낱장 메모처럼 끊김"
        )

    last_text = strip[-1][2] if strip else ""
    if last_text and not any(token in last_text for token in CLOSING_TOKENS):
        errors.append(f"{slug}: 마지막 큰문장이 앞선 흐름을 판단으로 닫지 못함: {last_text!r}")
    return errors


def validate_contract_readability(slug: str, contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for idx, slide in enumerate(contract.get("slides", []), start=1):
        if not isinstance(slide, dict):
            continue
        kicker = clean_card_text(slide.get("kicker"))
        normalized_kicker = re.sub(r"[^0-9A-Za-z가-힣]", "", kicker)
        if normalized_kicker in STRUCTURE_KICKER_LABELS:
            errors.append(f"{slug}: slide[{idx}].kicker 구조 라벨 금지: {kicker!r} — 내용 문장 자체에 흐름을 넣어야 함")
    for loc, text in _contract_reading_texts(contract):
        for phrase in CHECKLIST_PHRASES:
            if phrase in text:
                errors.append(f"{slug}: {loc} 체크리스트식 문구 금지: {phrase!r}")
        if "약자입니다" in text:
            errors.append(f"{slug}: {loc} 약자 설명형 문장 금지 — 쉬운 뜻부터 써야 함")
        for term, replacement in JARGON_REPLACEMENTS.items():
            if _term_in_text(text, term):
                errors.append(f"{slug}: {loc} 어려운 약어 사용: {term!r} -> {replacement!r}")
    return errors


def validate_contract_visuals(slug: str, contract: dict[str, Any]) -> list[str]:
    """하이브리드 visual 슬롯 검증 + 확장 루프 게이트.

    부른 시각 계약이 미등록이면 "레지스트리에 추가", 등록됐으나 렌더러 미구현이면
    "CardSlide 렌더러 추가(확장 루프) 후 발행" 으로 막는다. 종류별 필수 필드도 본다.
    """
    errors: list[str] = []
    for idx, slide in enumerate(contract.get("slides", []), start=1):
        if not isinstance(slide, dict):
            continue
        vis = slide.get("visual")
        if vis in (None, "", {}):
            continue
        if not isinstance(vis, dict):
            errors.append(f"{slug}: slide[{idx}].visual 은 객체여야 함")
            continue
        kind = str(vis.get("kind") or "")
        if kind not in VISUAL_CONTRACTS_REGISTERED:
            errors.append(
                f"{slug}: slide[{idx}].visual.kind {kind!r} 미등록 렌더링 계약 — "
                f"레지스트리에 계약 추가(확장 루프). 등록분: {', '.join(VISUAL_CONTRACTS_REGISTERED)}"
            )
            continue
        if kind not in VISUAL_CONTRACTS_RENDERABLE:
            errors.append(
                f"{slug}: slide[{idx}].visual.kind {kind!r} 은 등록됐으나 렌더러 미구현 — "
                "CardSlide 에 렌더러 추가(확장 루프) 후 발행"
            )
            continue
        if kind == "bars" and not (isinstance(vis.get("rows"), list) and vis.get("rows")):
            errors.append(f"{slug}: slide[{idx}].visual(bars) 는 rows 가 필요함")
        elif kind == "line":
            series = vis.get("series")
            if not (isinstance(series, list) and sum(1 for n in series if isinstance(n, (int, float))) >= 2):
                errors.append(f"{slug}: slide[{idx}].visual(line) 은 series 최소 2개 수치가 필요함")
        elif kind == "table" and not (
            isinstance(vis.get("cols"), list)
            and vis.get("cols")
            and isinstance(vis.get("data"), list)
            and vis.get("data")
        ):
            errors.append(f"{slug}: slide[{idx}].visual(table) 는 cols·data 가 필요함")
    return errors


def load_plan_file(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)}: JSON 파싱 실패: {exc}"]
    if not isinstance(plan, dict):
        return None, [f"{rel(path)}: 최상위 객체가 아님"]
    return plan, []


def validate_plan_file(path: Path, *, require_passed: bool = True, require_assets: bool = False) -> list[str]:
    plan, errors = load_plan_file(path)
    if errors:
        return errors
    assert plan is not None
    return validate_plan(plan, require_passed=require_passed, require_assets=require_assets)


def plan_path_for_contract(
    slug: str, contract: dict[str, Any], blog_dir: Path = BLOG_DIR, issues_dir: Path = ISSUES_DIR
) -> Path | None:
    if contract.get("standalone"):
        return issues_dir / slug / PLAN_FILE
    for folder in blog_dir.glob(f"*-{slug}"):
        if folder.is_dir():
            return folder / PLAN_FILE
    return None


def validate_contract_plan_gate(
    contracts: dict[str, dict[str, Any]],
    *,
    blog_dir: Path = BLOG_DIR,
    issues_dir: Path = ISSUES_DIR,
    require_plan: bool = False,
    require_passed: bool = True,
    require_assets: bool = False,
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    stats = {"contracts": len(contracts), "plans": 0, "missing": 0, "passed": 0}
    for slug, contract in sorted(contracts.items()):
        plan_path = plan_path_for_contract(slug, contract, blog_dir=blog_dir, issues_dir=issues_dir)
        if not plan_path or not plan_path.exists():
            if require_plan:
                stats["missing"] += 1
                errors.append(f"{slug}: cards.plan.json 없음")
            continue
        stats["plans"] += 1
        plan, load_errors = load_plan_file(plan_path)
        plan_errors = load_errors
        strict_big_sentence = False
        if plan is not None:
            plan_errors.extend(validate_plan(plan, require_passed=require_passed, require_assets=require_assets))
            strict_big_sentence = (
                isinstance(plan.get("version"), int) and plan.get("version") >= STRICT_FLOW_MIN_VERSION
            )
        copy_errors = validate_contract_readability(slug, contract)
        flow_errors = validate_contract_big_sentence_flow(slug, contract) if strict_big_sentence else []
        visual_errors = validate_contract_visuals(slug, contract)
        if plan_errors or copy_errors or flow_errors or visual_errors:
            errors.extend(f"{rel(plan_path)}: {err}" for err in plan_errors)
            errors.extend(copy_errors)
            errors.extend(flow_errors)
            errors.extend(visual_errors)
        else:
            stats["passed"] += 1
    return errors, stats
