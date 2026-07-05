"""편집 카드 캐러셀 계약 빌드 — 두 소스 → 단일 `carousels/index.json`.

소스 2갈래(저작), 서브 1개(발행):
  1. 회사 — 블로그 글(`blog/05-company-reports/{NN}-{code}-{slug}/index.md`) frontmatter `carousel:` 블록.
     한 글 = 한 스토리(회사+주제) = 산문(본문) + 캐러셀(frontmatter). 차트·핵심 지표는 /cards 가
     ReportModel 에서 덧붙인다(code 기반 라이브 조회).
  2. 이슈(standalone) — `blog/_issues/<slug>/carousel.yaml`. **블로그 글 없이 카드만** 발간(경제/시국 등
     그때그때 이슈). stockCode 가 있으면 /cards 가 회사 report 를 붙이고, 없으면 손글 editorial 만 렌더.
     슬라이드 image 는 `blog/_issues/<slug>/assets/<name>.webp`(cards.plan.json 기반 image_gen 산출물)
     → hfMedia `issues/<slug>/` 업로드.

손글 편집 카피(editorial/editorialBeat/editorialStat)가 캐러셀의 *중심점(계약)* 이고, landing /cards 가
**굽지 않고** 라이브 렌더한다. (옛 `sns/carousels/E*/hook.json` 분리 SSOT 폐기 → frontmatter 이관됨.)

키 = **슬러그**(회사 `003230-samyang-foods` · 이슈 `2026-06-korea-macro`). 회사당 N편(1:N).

계약(글당 1파일):
  { code, slug, name, sector?, title?, caption?, keyMetrics?, explainers?, relatedNews?, pinnedComment?, date?,
    slides: [ {layout, date?|kicker?, line?, sub?, bigNumber?, unit?, context?, image?} ],
    spec?: { hero?, order?, notes? } }
  layout ∈ editorial(커버) | editorialBeat(헤드라인 비트) | editorialStat(큰 숫자)
  image = semantic 파일명(확장자·해시 없음) — 렌더가 hfMedia 매니페스트로 해시 파일명 해석.
  spec = 자동 덱 큐레이션 오버레이(hero/order/notes) — 계약에 실어 /cards 가 blog 번들 비의존.

Serve = HF `eddmpython/dartlab-media` **단일** `carousels/index.json`(posts[]=전 계약, 슬라이드까지·
date 내림차순). 피드·상세 모두 이 1회 fetch 로(별도 인덱스 파일·per-slug round-trip 0). per-slug 파일
안 만든다 — 글 추가/삭제는 이 한 파일 재발행. `carousel:` 블록 있는 글만 계약 → /cards 기본 피드 = 이 글들.

Usage(운영자 로컬·HF_TOKEN=.env):
  uv run python -X utf8 blog/_scripts/build_carousel_contracts.py --dry-run   # 계획만(올리는 것·지울 것)
  uv run python -X utf8 blog/_scripts/build_carousel_contracts.py             # hfMedia 에 발행
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from cards_plan import validate_contract_plan_gate
from huggingface_hub import CommitOperationAdd, CommitOperationDelete, HfApi

from dartlab.core.dataConfig import HF_MEDIA_REPO
from dartlab.core.hfRetry import retryHfCall
from dartlab.pipeline.hfUpload import _resolveHfToken

ROOT = Path(__file__).resolve().parents[2]
BLOG_DIR = ROOT / "blog" / "05-company-reports"
TECH_DIR = ROOT / "blog" / "08-tech-story"  # 기술이야기: frontmatter carousel 블록 있는 글도 카드로 발행
ISSUES_DIR = ROOT / "blog" / "_issues"  # standalone 이슈 캐러셀(블로그 글 없음) — code 없는 경제/시국 카드
MEDIA_PREFIX = "carousels"
ISSUE_MEDIA_PREFIX = "issues"  # 이슈 이미지 hfMedia 네임스페이스(companies/ 와 병렬, 콘텐츠해시 파일명)
OG_MEDIA_PREFIX = "og"  # 브랜디드 OG 이미지 네임스페이스(og/<slug>.<hash8>.jpg)
OG_TEMPLATE_VERSION = "3"  # 렌더 템플릿 버전. bump 하면 해시 바뀌어 전량 재렌더(v3=가로 1200x630 링크 미리보기)
HF_MEDIA_RESOLVE = f"https://huggingface.co/datasets/{HF_MEDIA_REPO}/resolve/main"
AVATAR_PATH = ROOT / "landing" / "static" / "avatar.png"  # OG 좌상단 아바타
OG_RENDERER = ROOT / "blog" / "_scripts" / "render_og_cards.mjs"  # Node 배치 렌더러

_SLIDE_LAYOUTS = ("editorial", "editorialBeat", "editorialStat")
# 슬라이드가 채택하는 필드(나머지 키는 무시). image=semantic 파일명(해시 없음).
_SLIDE_FIELDS = ("date", "kicker", "line", "sub", "bigNumber", "unit", "context", "image")


def _read_frontmatter(md_path: Path) -> dict:
    """index.md 의 `---` frontmatter 블록 → dict(없거나 깨지면 빈 dict). 본문(산문)은 안 읽음."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)  # ['', frontmatter, body…]
    if len(parts) < 3:
        return {}
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        sys.stderr.write(f"  bad frontmatter in {md_path.parent.name}: {exc}\n")
        return {}
    return fm if isinstance(fm, dict) else {}


def _slug_from_folder(folder_name: str) -> str:
    """폴더명 `02-003230-samyang-foods` → 슬러그 `003230-samyang-foods`(NN- 접두 제거·posts.ts 와 동일)."""
    return re.sub(r"^\d+-", "", folder_name)


def _code_from(fm: dict, slug: str) -> str:
    """frontmatter stockCode 권위 → 없으면 슬러그 첫 세그먼트가 6자리면 코드."""
    code = str(fm.get("stockCode", "")).strip()
    if code:
        return code
    first = slug.split("-", 1)[0]
    return first if (first.isdigit() and len(first) == 6) else ""


# 종목코드 → 회사명 안전망. frontmatter corpName·carousel.name 이 비면 kindList(gather SSOT)에서 실이름을
# 해석해 표시 이름이 종목코드로 폴백되는 것을 막는다("058610 · 058610" 회귀 차단). kindList 는 상장사 SSOT라
# 하드코딩보다 리네임에 강하고, 이름을 재구현하지 않고 getKindList 에 위임한다(수집=gather 원칙).
_KIND_NAME_CACHE: dict[str, str] | None = None


def _corp_name_from_code(code: str) -> str:
    """종목코드 → 회사명(kindList SSOT). 못 찾거나 조회 불가면 빈 문자열(호출부가 폴백 판단)."""
    global _KIND_NAME_CACHE
    if not code:
        return ""
    if _KIND_NAME_CACHE is None:
        try:
            from dartlab.gather.krx.listing import getKindList

            df = getKindList()
            _KIND_NAME_CACHE = dict(zip(df["종목코드"].to_list(), df["회사명"].to_list()))
        except Exception as exc:  # 네트워크·데이터 부재 등. 빈 문자열 폴백 후 가드가 name==code 를 차단
            sys.stderr.write(f"  kindList 회사명 해석 불가(코드 폴백 위험): {exc}\n")
            _KIND_NAME_CACHE = {}
    return str(_KIND_NAME_CACHE.get(code) or "")


def _normalize_slide(raw: object) -> dict | None:
    """frontmatter 슬라이드 → 계약 슬라이드. editorial 3종만(나머지 layout 무시)."""
    if not isinstance(raw, dict):
        return None
    layout = raw.get("layout")
    if layout not in _SLIDE_LAYOUTS:
        return None
    slide: dict = {"layout": layout}
    for f in _SLIDE_FIELDS:
        v = raw.get(f)
        if v not in (None, ""):
            slide[f] = v
    # 하이브리드 시각 슬롯 — 큰문장 아래 증거(렌더링 계약). dict 그대로 통과(종류·필드 검증은 cards_plan 게이트).
    vis = raw.get("visual")
    if isinstance(vis, dict) and vis.get("kind"):
        slide["visual"] = vis
    return slide


# ── 레이아웃 깨짐 가드(원천 체크) ───────────────────────────────────────────────
# editorialStat 의 bigNumber 는 거대폰트(최대 200px) 한 줄 펀치 숫자여야 한다. 길거나 공백/화살표가
# 있으면(예 '1조 4,375억', '641% → 102%') 줄이 쪼개지고 unit 과 충돌한다(렌더는 줄여서 방어하나,
# 소스에서 잡는 게 정공). unit 도 짧은 라벨만('%','조원','$B (-50%)') — 문장형('% 영업외 흡수율 · 9년
# 최저')은 context 로 가야 한다.
_BIGNUM_MAXLEN = 10
_UNIT_MAXLEN = 12


def _validate_slide(layout: str, slide: dict) -> list[str]:
    """슬라이드 1장의 레이아웃 깨짐 위험 검사 — 위반 메시지 리스트(없으면 빈 리스트)."""
    issues: list[str] = []
    if layout == "editorialStat":
        big = str(slide.get("bigNumber", "")).strip()
        unit = str(slide.get("unit", "")).strip()
        if not big:
            issues.append("bigNumber 누락(editorialStat 필수)")
        elif len(big) > _BIGNUM_MAXLEN or " " in big:
            issues.append(f"bigNumber 과다/비펀치('{big}' {len(big)}자) — 짧은 한 숫자만(맥락은 context 로)")
        if len(unit) > _UNIT_MAXLEN:
            issues.append(f"unit 과다('{unit}' {len(unit)}자) — 짧은 단위만(문장은 context 로)")
    for f in ("line", "sub", "context"):
        v = str(slide.get(f, ""))
        if v.count("[[") != v.count("]]"):
            issues.append(f"{f} [[강조]] 마커 불균형")
    return issues


def validate_contracts(contracts: dict[str, dict]) -> list[str]:
    """전 계약 슬라이드를 검사해 위반 라인 리스트 반환(슬러그·슬라이드#·layout·사유)."""
    out: list[str] = []
    for slug, c in sorted(contracts.items()):
        # 표시 이름 == 종목코드 차단. 6자리 코드는 회사명이 아니다("058610 · 058610" 헤더 = 발행 금지 결함).
        # corpName 누락 + kindList 미해석이 겹칠 때만 도달. 회사명을 채우기 전엔 HF 에 안 올린다.
        code = str(c.get("code") or "")
        name = str(c.get("name") or "")
        if code and name == code:
            out.append(
                f"{slug}: 표시 이름이 종목코드와 동일('{code}'). corpName 누락 또는 kindList 미해석(회사명 필요)"
            )
        for i, s in enumerate(c.get("slides", []), 1):
            for msg in _validate_slide(s.get("layout", ""), s):
                out.append(f"{slug} #{i}({s.get('layout')}): {msg}")
    return out


def _spec_from(carousel: dict) -> dict | None:
    """자동 덱 큐레이션 오버레이(hero/order/notes) 추출 — 없으면 None."""
    spec: dict = {}
    if carousel.get("hero"):
        spec["hero"] = str(carousel["hero"])
    if isinstance(carousel.get("order"), list):
        spec["order"] = [str(k) for k in carousel["order"]]
    if isinstance(carousel.get("notes"), dict):
        spec["notes"] = {str(k): str(v) for k, v in carousel["notes"].items()}
    return spec or None


def _normalize_explainers(source: dict) -> list[dict]:
    """짧은 설명 목록(`explainers`) → 계약 필드. term/body 둘 다 있어야 한다."""
    raw = source.get("explainers") or []
    if isinstance(raw, dict):
        raw = [{"term": k, "body": v} for k, v in raw.items()]
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or item.get("label") or "").strip()
        body = str(item.get("body") or item.get("text") or item.get("description") or "").strip()
        if term and body:
            out.append({"term": term, "body": body})
    return out


def _normalize_related_news(source: dict) -> list[dict]:
    """관련 뉴스 링크(`relatedNews`) → 계약 필드. title/url 은 필수, 나머지는 표시 보조."""
    raw = source.get("relatedNews") or source.get("related_news") or []
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if not title or not url:
            continue
        news = {"title": title, "url": url}
        for key in ("source", "date", "description", "track"):
            value = str(item.get(key) or "").strip()
            if value:
                news[key] = value
        out.append(news)
    return out


def _normalize_key_metrics(source: dict) -> list[dict]:
    """검증된 핵심 지표(`keyMetrics`) → 계약 필드. label/value 둘 다 있어야 하며 빈 값은 버린다."""
    raw = source.get("keyMetrics") or source.get("key_metrics") or []
    if isinstance(raw, dict):
        raw = [{"label": k, "value": v} for k, v in raw.items()]
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("term") or "").strip()
        value = str(item.get("value") or item.get("text") or "").strip()
        if label and value and value not in {"-", "–"}:
            out.append({"label": label, "value": value})
    return out


def _attach_caption_context(contract: dict, source: dict) -> None:
    """캡션 보조 맥락(짧은 설명·관련뉴스)을 계약에 싣는다."""
    key_metrics = _normalize_key_metrics(source)
    if key_metrics:
        contract["keyMetrics"] = key_metrics
    explainers = _normalize_explainers(source)
    if explainers:
        contract["explainers"] = explainers
    related_news = _normalize_related_news(source)
    if related_news:
        contract["relatedNews"] = related_news


def build_contracts(blog_dir: Path = BLOG_DIR) -> dict[str, dict]:
    """블로그 글 → 슬러그별 계약(`carousel:` 블록 있는 글만). 같은 회사 다른 슬러그 = 각자 계약(1:N)."""
    contracts: dict[str, dict] = {}
    for md in sorted(blog_dir.glob("*/index.md")):
        fm = _read_frontmatter(md)
        carousel = fm.get("carousel")
        if not isinstance(carousel, dict):
            continue
        slug = _slug_from_folder(md.parent.name)
        code = _code_from(fm, slug)
        if not code:
            sys.stderr.write(f"  skip(no code): {md.parent.name}\n")
            continue
        slides = [s for raw in (carousel.get("slides") or []) if (s := _normalize_slide(raw))]
        if not slides:
            sys.stderr.write(f"  skip(no slides): {md.parent.name}\n")
            continue
        contract: dict = {
            "code": code,
            "slug": slug,
            "name": str(fm.get("corpName") or carousel.get("name") or _corp_name_from_code(code) or code),
            "cardType": str(carousel.get("cardType") or "company"),  # 카드 필터 축 (company|event|economy)
            "slides": slides,
        }
        sector = carousel.get("sector") or fm.get("sector")
        if sector:
            contract["sector"] = str(sector)
        title = carousel.get("title") or fm.get("title")
        if title:
            contract["title"] = str(title)
        caption = carousel.get("caption")
        if caption:
            contract["caption"] = str(caption).strip()
        pinned = carousel.get("pinnedComment")
        if pinned:
            contract["pinnedComment"] = str(pinned).strip()
        _attach_caption_context(contract, carousel)
        date = str(fm.get("date") or "").strip()
        if date:
            contract["date"] = date
        spec = _spec_from(carousel)
        if spec:
            contract["spec"] = spec
        contract["_pub"] = _plan_generated_at(md.parent)  # 같은 날짜 내 발간 시각 정렬키(build_index 에서 사용 후 제거)
        if slug in contracts:
            sys.stderr.write(f"  dup slug(덮어쓰기 방지): {slug}\n")
        contracts[slug] = contract
    return contracts


def _content_hash(path: Path) -> str:
    """파일 콘텐츠 sha256 앞 8자. served 파일명 캐시버스트(companies/ 의 hash8 동형)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


# 브랜디드 OG 이미지.
# 카드 첫 슬라이드를 dartlab 에디토리얼 카드(그레이톤+아바타/dartlab+헤드라인) 1080x1350 JPEG 로 렌더해
# HF og/<slug>.<hash>.jpg 로 올리고, 계약에 ogImage 를 실어 공유 워커 og:image 가 그걸 가리키게 한다.
# 텍스트·로고 합성은 URL 필터로 불가, 엣지 런타임 생성은 무료 워커 용량 한계라 발행 시점 렌더가 정공.


def _og_bg(post: dict, repo_files: set[str]) -> tuple[str | None, str | None]:
    """첫 슬라이드 배경을 렌더용 소스로 해석. 반환 (bgUrl, bgId).
    이슈: 로컬 assets webp(file:// · 신규 발행분도 HF 업로드 전 렌더 가능). 회사: HF url(이미 올라감).
    bgId = og 파일명 해시 입력(콘텐츠 식별). 못 풀면 (None, None)."""
    slides = post.get("slides") or []
    if not slides:
        return None, None
    img = str(slides[0].get("image") or "")
    if not img:
        return None, None
    if "/" in img:  # 이슈: issues/<slug>/<name>.<hash>.webp
        parts = img.split("/")
        if len(parts) >= 3:
            slug, fname = parts[1], parts[-1]
            name = fname.rsplit(".", 2)[0]  # <name>.<hash>.webp 에서 <name>
            local = ISSUES_DIR / slug / "assets" / f"{name}.webp"
            if local.exists():
                return str(local), _content_hash(local)  # 로컬 절대경로(렌더러가 data URI 임베드)
        return f"{HF_MEDIA_RESOLVE}/{img}", img  # 폴백: HF(기존 발행분)
    # 회사: semantic 파일명을 companies/<key>/<name>.<hash>.webp 로 해석(repo_files 매칭)
    code = str(post.get("code") or "")
    key = code if (code.isdigit() and len(code) == 6) else code.upper()
    prefix = f"companies/{key}/{img}."
    match = next((f for f in sorted(repo_files) if f.startswith(prefix) and f.endswith(".webp")), None)
    if match:
        return f"{HF_MEDIA_RESOLVE}/{match}", match
    return None, None


def plan_og_images(contracts: dict[str, dict], repo_files: set[str], *, enabled: bool = True) -> list[dict]:
    """각 계약에 ogImage(og/<slug>.<hash>.jpg) 를 설정하고, 아직 HF 에 없는 것들의 렌더 잡을 반환한다.
    해시 = name+line+배경식별자. 입력 안 바뀌면 파일명 동일이라 재렌더·재업로드 스킵. enabled=False 면 no-op."""
    jobs: list[dict] = []
    if not enabled:
        return jobs
    for slug, c in contracts.items():
        slides = c.get("slides") or []
        line = str(slides[0].get("line") or "") if slides else ""
        name = str(c.get("name") or "")
        if not line:
            continue
        bg_url, bg_id = _og_bg(c, repo_files)
        if not bg_url or not bg_id:
            continue
        h = hashlib.sha256(f"{OG_TEMPLATE_VERSION}\x00{name}\x00{line}\x00{bg_id}".encode()).hexdigest()[:8]
        og_path = f"{OG_MEDIA_PREFIX}/{slug}.{h}.jpg"
        c["ogImage"] = og_path
        if og_path not in repo_files:
            jobs.append({"slug": slug, "name": name, "line": line, "bg": bg_url, "og_path": og_path})
    return jobs


def render_og_images(jobs: list[dict], out_dir: Path, contracts: dict[str, dict]) -> list[CommitOperationAdd]:
    """렌더 잡을 Node 배치 렌더러로 1080x1350 JPEG 생성 후 업로드 op 반환. Node/Playwright 부재·개별
    실패는 경고 후 스킵(그 카드는 ogImage 제거 → 워커가 평사진 폴백). 발행 자체는 절대 막지 않는다."""
    ops: list[CommitOperationAdd] = []
    if not jobs:
        return ops
    node = shutil.which("node")
    if not node:
        sys.stderr.write("  OG 렌더 스킵: node 없음 (카드 og 없이 발행)\n")
        for j in jobs:
            contracts[j["slug"]].pop("ogImage", None)
        return ops
    for j in jobs:
        j["out"] = str(out_dir / f"og_{j['slug']}.jpg")
    manifest = out_dir / "og_manifest.json"
    manifest.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    try:
        r = subprocess.run(
            [node, str(OG_RENDERER), str(manifest), str(AVATAR_PATH)],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if r.stderr:
            sys.stderr.write("  [og] " + r.stderr.strip()[-800:] + "\n")
    except Exception as exc:
        sys.stderr.write(f"  OG 렌더 스킵(예외): {exc}\n")
        for j in jobs:
            contracts[j["slug"]].pop("ogImage", None)
        return ops
    for j in jobs:
        out = Path(j["out"])
        if out.exists() and out.stat().st_size > 0:
            ops.append(CommitOperationAdd(path_in_repo=j["og_path"], path_or_fileobj=str(out)))
        else:
            contracts[j["slug"]].pop("ogImage", None)  # 산출 실패분은 폴백
    return ops


def build_issue_contracts(
    issues_dir: Path, existing_files: set[str]
) -> tuple[dict[str, dict], list[CommitOperationAdd]]:
    """blog/_issues/<slug>/carousel.yaml → standalone 이슈 계약. 블로그 글 없이 카드만.

    회사 계약과 동일 슬라이드 스키마(editorial 3종)지만 키 = 폴더 슬러그. stockCode 가 있으면
    회사 report 카드가 뒤에 붙고, stockCode 가 없으면 손글 editorial 슬라이드만 렌더한다.
    슬라이드 image(semantic 'cover') → 로컬 `assets/<image>.webp` 콘텐츠해시해서 hfMedia
    `issues/<slug>/<image>.<hash8>.webp` 경로로 치환(렌더가 originUrl('hfMedia', path) 로 해석).
    반환: (슬러그별 계약, 업로드할 이미지 CommitOperationAdd 리스트 — 이미 올라간 해시는 스킵).
    """
    contracts: dict[str, dict] = {}
    ops: list[CommitOperationAdd] = []
    if not issues_dir.exists():
        return contracts, ops
    for yml in sorted(issues_dir.glob("*/carousel.yaml")):
        slug = yml.parent.name
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            sys.stderr.write(f"  bad issue yaml {slug}: {exc}\n")
            continue
        if not isinstance(data, dict):
            continue
        assets_dir = yml.parent / "assets"
        slides: list[dict] = []
        for raw in data.get("slides") or []:
            s = _normalize_slide(raw)
            if not s:
                continue
            img = s.get("image")
            if img:
                local = assets_dir / f"{img}.webp"
                if local.exists():
                    remote = f"{ISSUE_MEDIA_PREFIX}/{slug}/{img}.{_content_hash(local)}.webp"
                    s["image"] = remote  # hfMedia 상대경로(슬래시 포함 → 렌더가 직접 해석)
                    if remote not in existing_files:
                        ops.append(CommitOperationAdd(path_in_repo=remote, path_or_fileobj=str(local)))
                else:
                    sys.stderr.write(f"  issue {slug}: 이미지 없음 {local.name} (배경 없이 렌더)\n")
                    s.pop("image", None)
            slides.append(s)
        if not slides:
            sys.stderr.write(f"  skip issue(no slides): {slug}\n")
            continue
        code = _code_from(data, slug)
        card_type = str(data.get("type") or ("event" if code else "economy"))
        contract: dict = {
            "code": code,  # code 있으면 회사 report 조회/차트 첨부, 없으면 순수 이슈 카드
            "slug": slug,
            "name": str(
                data.get("corpName")
                or data.get("name")
                or data.get("title")
                or _corp_name_from_code(code)
                or code
                or slug
            ),
            "cardType": card_type,  # company|event|economy — 카드 필터/크로스검색 축
            "standalone": True,  # 블로그 글 없음 → PostModal '블로그 이어 읽기' CTA 숨김(code 유무와 별개)
            "slides": slides,
        }
        for key in ("sector", "title"):
            if data.get(key):
                contract[key] = str(data[key])
        if data.get("caption"):
            contract["caption"] = str(data["caption"]).strip()
        if data.get("pinnedComment"):
            contract["pinnedComment"] = str(data["pinnedComment"]).strip()
        _attach_caption_context(contract, data)
        if data.get("date"):
            contract["date"] = str(data["date"]).strip()
        spec = _spec_from(data)
        if spec:
            contract["spec"] = spec
        contract["_pub"] = _plan_generated_at(
            yml.parent
        )  # 같은 날짜 내 발간 시각 정렬키(build_index 에서 사용 후 제거)
        contracts[slug] = contract
    return contracts, ops


def _list_repo_files(api: HfApi, repo: str) -> set[str]:
    """repo 전체 파일 목록(best-effort·공개 repo 는 토큰 없이도 list 가능)."""
    try:
        return set(api.list_repo_files(repo_id=repo, repo_type="dataset"))
    except Exception:
        return set()


def _stale_carousel_jsons(files: set[str]) -> set[str]:
    """carousels/*.json 중 단일 index.json 외 옛 파일(삭제 대상)."""
    return {f for f in files if f.startswith(f"{MEDIA_PREFIX}/") and f.endswith(".json")} - {
        f"{MEDIA_PREFIX}/index.json"
    }


def _stale_og_images(files: set[str], contracts: dict[str, dict]) -> set[str]:
    """og/ 중 현재 어느 계약도 안 쓰는 옛 OG 파일(삭제 대상). 템플릿 버전 bump·헤드라인 변경 시 옛 해시 정리."""
    used = {str(c["ogImage"]) for c in contracts.values() if c.get("ogImage")}
    return {f for f in files if f.startswith(f"{OG_MEDIA_PREFIX}/")} - used


def _plan_generated_at(folder: Path) -> str:
    """cards.plan.json 의 generatedAt(ISO). 같은 날짜(day) 안 발간 시각 2차 정렬키. 없으면 빈 문자열.
    커밋되는 값이라 CI 체크아웃에서도 유지된다(파일 mtime 은 체크아웃에서 리셋돼 못 쓴다)."""
    plan = folder / "cards.plan.json"
    if not plan.exists():
        return ""
    try:
        return str(json.loads(plan.read_text(encoding="utf-8")).get("generatedAt") or "")
    except (json.JSONDecodeError, OSError):
        return ""


def build_index(contracts: dict[str, dict]) -> list[dict]:
    """발간 최신순 전체 계약 배열(단일 index.json 의 posts[]). 1차 date(day) 내림차순,
    같은 날짜는 cards.plan.json generatedAt(발간 시각) 내림차순, 그다음 슬러그. date 없으면 맨 뒤.
    피드·상세 모두 이 한 파일로(별도 인덱스·per-slug round-trip 0)."""
    ordered = sorted(
        contracts.values(),
        key=lambda c: (c.get("date") or "", c.get("_pub") or "", c["slug"]),
        reverse=True,
    )
    for c in ordered:
        c.pop("_pub", None)  # 내부 정렬키. 발행 JSON 에는 안 싣는다
    return ordered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="게시 안 함, 요약만")
    parser.add_argument("--repo", default=HF_MEDIA_REPO)
    parser.add_argument("--allow-layout-warn", action="store_true", help="레이아웃 가드 위반이 있어도 발행 강행")
    parser.add_argument("--require-card-plan", action="store_true", help="모든 계약에 cards.plan.json 요구")
    parser.add_argument(
        "--allow-unreviewed-card-plan",
        action="store_true",
        help="cards.plan.json 이 planned 상태여도 발행 허용(운영 중 임시 우회)",
    )
    parser.add_argument(
        "--require-card-assets", action="store_true", help="cards.plan.json 의 모든 image_gen 산출물 존재 요구"
    )
    parser.add_argument("--no-og", action="store_true", help="브랜디드 OG 이미지 렌더/업로드 건너뜀")
    args = parser.parse_args()

    # 발간 전 repo 파일 목록 1회(옛 json 삭제 + 이미 올라간 이슈 이미지 해시 스킵 양쪽에 씀).
    repo_files = _list_repo_files(HfApi(), args.repo)

    contracts = build_contracts()  # 회사 계약(블로그 frontmatter)
    # 기술이야기(TECH_DIR) 카드 배선 임시 차단. 회사카드 틀에 잘못 얹어(종목코드 강제·논지 배신·기획 미수행)
    # 라이브에서 내림. 종목 정체성 제거 + 배지 "기술이야기" + 주제 사진 + cards.plan 정식화 후 재배선한다.
    # for _slug, _c in build_contracts(TECH_DIR).items():
    #     contracts.setdefault(_slug, _c)
    issue_contracts, image_ops = build_issue_contracts(ISSUES_DIR, repo_files)  # standalone 이슈
    for slug, c in issue_contracts.items():
        if slug in contracts:
            sys.stderr.write(f"  dup slug(이슈↔회사 충돌, 회사 우선): {slug}\n")
            continue
        contracts[slug] = c

    # 원천 레이아웃 가드 — 거대폰트 editorialStat 줄깨짐/충돌 등을 발행 전에 잡는다.
    violations = validate_contracts(contracts)
    if violations:
        sys.stderr.write(f"⚠ 레이아웃 가드 위반 {len(violations)}건:\n")
        for v in violations:
            sys.stderr.write(f"  - {v}\n")
        if not args.dry_run and not args.allow_layout_warn:
            sys.stderr.write("발행 중단 — 위반 수정 후 재시도(또는 --allow-layout-warn 로 강행).\n")
            sys.exit(1)
    else:
        print("레이아웃 가드: 위반 0건 ✓")

    # 신규/개선 카드뉴스 운영 게이트. legacy 계약은 plan 파일이 없으면 허용하되, cards.plan.json 이 생긴
    # 글은 작가 패널·정직성·이미지 적합성·재평가를 passed 로 닫아야 발행한다.
    plan_violations, plan_stats = validate_contract_plan_gate(
        contracts,
        require_plan=args.require_card_plan,
        require_passed=not args.allow_unreviewed_card_plan,
        require_assets=args.require_card_assets,
    )
    if plan_violations:
        sys.stderr.write(f"⚠ 카드 기획/토론 게이트 위반 {len(plan_violations)}건:\n")
        for v in plan_violations:
            sys.stderr.write(f"  - {v}\n")
        sys.stderr.write(
            "발행 중단 — plan_card_news.py 로 cards.plan.json 을 만들고 reviewGate 를 passed 로 닫은 뒤 재시도.\n"
        )
        sys.exit(1)
    print(
        "카드 기획/토론 게이트: "
        f"계약 {plan_stats['contracts']}편 · 계획 {plan_stats['plans']}개 · "
        f"통과 {plan_stats['passed']}개 · 누락 {plan_stats['missing']}개"
    )

    # 브랜디드 OG 계획. 계약에 ogImage 설정, 렌더 필요분(HF 미보유) 잡 목록. 렌더는 실제 발행에서만.
    og_jobs = plan_og_images(contracts, repo_files, enabled=not args.no_og)

    posts = build_index(contracts)
    n_slides = sum(len(c["slides"]) for c in contracts.values())
    n_companies = len({c["code"] for c in contracts.values() if c.get("code")})
    n_issues = len(issue_contracts)
    print(
        f"계약: {len(contracts)}편 · {n_companies}개 회사 · {n_issues}개 이슈 · "
        f"{n_slides}개 편집 슬라이드 · 이슈 이미지 {len(image_ops)}장 · OG 렌더 {len(og_jobs)}장 예정 (+ index.json)"
    )

    if args.dry_run:
        for p in posts[:8]:
            c = contracts[p["slug"]]
            layouts = ", ".join(s["layout"] for s in c["slides"][:4])
            tag = "ISSUE" if c.get("standalone") else c["code"]
            print(f"  {tag} {p['slug']} · {len(c['slides'])}장 [{layouts}…] {p.get('date', '')}")
        if len(posts) > 8:
            print(f"  … 총 {len(posts)}편")
        if image_ops:
            print(f"  이슈 이미지 업로드: {', '.join(op.path_in_repo for op in image_ops[:6])} …")
        stale = _stale_carousel_jsons(repo_files)
        if stale:
            print(f"  옛 파일 {len(stale)}개 삭제 예정(단일 index.json 만 유지): {', '.join(sorted(stale)[:6])} …")
        print("dry-run — 게시 안 함.")
        return

    api = HfApi(token=_resolveHfToken())
    with tempfile.TemporaryDirectory() as td:
        # OG 렌더 먼저(개별 실패분 ogImage 제거) → index.json 이 최종 ogImage 를 반영하게. 같은 commit.
        og_ops = render_og_images(og_jobs, Path(td), contracts)
        # 단일 파일. 전 계약(슬라이드까지)을 index.json 하나에. per-slug 파일 안 만듦.
        idx = Path(td) / "index.json"
        idx.write_text(json.dumps({"posts": posts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ops: list = [CommitOperationAdd(path_in_repo=f"{MEDIA_PREFIX}/index.json", path_or_fileobj=str(idx))]
        ops += image_ops  # 이슈 이미지(issues/<slug>/...) 동시 업로드. 같은 commit
        ops += og_ops  # 브랜디드 OG 이미지(og/<slug>.<hash>.jpg)
        # 그 외 carousels/*.json(옛 code-키·옛 per-slug) 전부 삭제. 단일 index.json 만 유지(폴더 청결).
        stale = sorted(_stale_carousel_jsons(repo_files))
        ops += [CommitOperationDelete(path_in_repo=p) for p in stale]
        # 안 쓰는 옛 OG(버전 bump·헤드라인 변경 잔재) 정리.
        stale_og = sorted(_stale_og_images(repo_files, contracts))
        ops += [CommitOperationDelete(path_in_repo=p) for p in stale_og]
        retryHfCall(
            api.create_commit,
            repo_id=args.repo,
            repo_type="dataset",
            operations=ops,
            commit_message=(
                f"carousels: {len(contracts)} posts ({n_companies} companies, {n_issues} issues), "
                f"+{len(image_ops)} issue imgs, +{len(og_ops)} og imgs, -{len(stale)} stale"
            ),
        )
    print(
        f"완료. {args.repo} carousels/index.json 게시({len(contracts)}편, 이슈 {n_issues} · "
        f"이미지 +{len(image_ops)} · OG +{len(og_ops)} · 옛 {len(stale)}개 삭제)."
    )


if __name__ == "__main__":
    main()
