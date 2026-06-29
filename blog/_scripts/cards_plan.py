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

MIN_IMAGES = 5
MAX_IMAGES = 10
ASSET_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
FORBIDDEN_ASSET_TOKENS = ("card", "thumbnail", "thumb")
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
        if not MIN_IMAGES <= count <= MAX_IMAGES:
            raise ValueError(f"--count must be between {MIN_IMAGES} and {MAX_IMAGES}")
        return count
    return min(MAX_IMAGES, max(MIN_IMAGES, len(slides) or MIN_IMAGES))


def slide_line(slide: dict[str, Any]) -> str:
    for key in ("line", "context", "sub", "kicker", "bigNumber"):
        value = str(slide.get(key, "")).strip()
        if value:
            return value.replace("[[", "").replace("]]", "")
    return "핵심 장면"


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
        "rules": list(NARRATIVE_RULES),
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
                "purpose": "훅 강도, 서사 스파인, 앞장-다음장 연결, 블로그 산문과 카드 흐름의 일치 여부를 본다. 체크리스트식 나열이면 실패다.",
                "status": "todo",
            },
            {
                "id": "honestyEvidence",
                "purpose": "슬라이드 숫자와 주장 근거가 블로그 본문/검증표에 있는지 본다.",
                "status": "todo",
            },
            {
                "id": "imageFit",
                "purpose": "5~10장 이미지가 그 글의 회사·사건·장소에 맞는 서로 다른 의미 장면인지, 가짜 공식 로고·텍스트·도식이 없는지 본다.",
                "status": "todo",
            },
            {
                "id": "readerFit",
                "purpose": "처음 보는 독자가 첫 장부터 마지막 장까지 끊기지 않고 읽으며 관전 포인트를 이해하는지 본다.",
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
        "version": 1,
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
        "version": 1,
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
    if plan.get("version") != 1:
        errors.append(f"{slug}: version 은 1이어야 함")
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
    image_plan = plan.get("imagePlan")
    if not isinstance(image_plan, list):
        errors.append(f"{slug}: imagePlan 은 리스트여야 함")
        image_plan = []
    if not MIN_IMAGES <= len(image_plan) <= MAX_IMAGES:
        errors.append(f"{slug}: imagePlan 은 {MIN_IMAGES}~{MAX_IMAGES}장이어야 함(현재 {len(image_plan)})")
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


def validate_plan_file(path: Path, *, require_passed: bool = True, require_assets: bool = False) -> list[str]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{rel(path)}: JSON 파싱 실패: {exc}"]
    if not isinstance(plan, dict):
        return [f"{rel(path)}: 최상위 객체가 아님"]
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
        plan_errors = validate_plan_file(plan_path, require_passed=require_passed, require_assets=require_assets)
        if plan_errors:
            errors.extend(f"{rel(plan_path)}: {err}" for err in plan_errors)
        else:
            stats["passed"] += 1
    return errors, stats
