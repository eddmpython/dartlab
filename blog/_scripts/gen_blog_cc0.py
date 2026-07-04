"""블로그 전체: 배경 이미지 없는 글에 CC0/PD 스톡 배경 수급 (FLUX·생성형 안 씀).

`gen_news_cc0.py`(dartlab-news 한정)를 블로그 전 카테고리로 확장한 버전. 이미 배경이 있는 글은
건드리지 않고(--force 로만 덮어씀), `*thumbnail-bg.webp` 가 없는 글만 채운다. 수급 엔진은
`fetch_cc0_images.py`(Wikimedia Commons + Openverse, 귀속 의무 없는 PD/CC0 만 + OAuth)를 그대로 재사용.

쿼리 도출(자동). 썸네일은 흑백 + 다크 스크림이라 "분위기 배경"이면 충분하다.
- company-reports: 슬러그의 영문 회사명 토큰으로 **업종 추론**(반도체·식음료·제약·중공업·에너지화학·
  금융·소비재유통·엔터·우주항공·물류·IT소프트). 매핑되면 업종 실사 쿼리, 미매핑이면 기업 스카이라인.
  (회사명 직검색은 인물 초상화·로고 오매치가 잦아 안 씀.)
- reading-disclosures / credit-reports: 주제 쿼리 풀(공시 문서·감사·거래소·채권·신용)을 글 순서로 변주.
- 전 카테고리 끝에 범용 폴백(기업/금융 스카이라인) + 초상화·로고·지도 거부 필터로 0매치·오매치 최소화.

저장: blog/{cat}/{NN}-{slug}/assets/{NN}-thumbnail-bg.webp · 출처는 글 폴더 CREDITS.md 누적.
받은 뒤 gen_blog_thumbnails.py 가 이 배경을 흑백 cover 로 깔고 텍스트를 얹는다(눈검수는 합성본으로).

실행:
  uv run python -X utf8 blog/_scripts/gen_blog_cc0.py            # 이미지 없는 글 전부
  uv run python -X utf8 blog/_scripts/gen_blog_cc0.py --only 01-000660-skhynix
  uv run python -X utf8 blog/_scripts/gen_blog_cc0.py --limit 20 --dry   # 쿼리만 출력
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_cc0_images import _candidates, _credit_line, _download, _relevant, _save_webp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BLOG = ROOT / "blog"

# 업종 추론: 영문 회사명/슬러그에 토큰이 있으면 그 업종 쿼리 사용(앞에서부터 우선).
# 각 항목: (탐지 토큰들, [실사 쿼리들], [관련성 키워드])
SECTORS: list[tuple[list[str], list[str], list[str]]] = [
    (
        [
            "semi",
            "hynix",
            "micron",
            "nvidia",
            "broadcom",
            "qualcomm",
            "applied",
            "amat",
            "intellian",
            "rino",
            "silicon",
            "skhynix",
        ],
        [
            "semiconductor wafer fab cleanroom",
            "silicon chip circuit board macro",
            "semiconductor manufacturing equipment",
        ],
        ["semiconductor", "wafer", "chip", "circuit", "cleanroom", "electronics", "silicon"],
    ),
    (
        ["display", "lg-display"],
        ["display panel manufacturing line", "lcd oled panel factory"],
        ["display", "panel", "screen", "factory", "lcd", "oled"],
    ),
    (
        ["battery", "sdi", "ecopro", "energy-solution", "sk-on", "fuel-cell", "lg-energy"],
        ["lithium battery manufacturing line", "ev battery cell production", "battery gigafactory"],
        ["battery", "lithium", "cell", "factory", "energy", "manufacturing"],
    ),
    (
        ["chem", "oil", "s-oil", "lotte-chemical", "kolmar", "cosmax"],
        ["petrochemical plant refinery towers", "chemical industry plant pipes", "oil refinery night"],
        ["refinery", "chemical", "plant", "petrochemical", "industrial", "pipes", "oil"],
    ),
    (
        [
            "pharma",
            "bio",
            "celltrion",
            "yuhan",
            "alteogen",
            "pharmaresearch",
            "biologics",
            "bioscience",
            "hanmi",
            "thermo",
            "tmo",
        ],
        ["pharmaceutical laboratory research", "biotech lab scientist pipette", "medicine production line"],
        ["lab", "laboratory", "research", "pharma", "biotech", "scientist", "medicine"],
    ),
    (
        [
            "ship",
            "ksoe",
            "engine",
            "hyundai-engine",
            "hanwha-engine",
            "rotem",
            "doosan-ener",
            "enerbility",
            "cs-wind",
            "taihan",
            "ls-electric",
            "hd-hyundai",
            "ge-vernova",
            "vernova",
            "power-equipment",
            "electric",
        ],
        [
            "heavy industry shipyard cranes",
            "power plant turbine hall",
            "industrial steel factory",
            "electrical grid power transformer",
        ],
        ["shipyard", "crane", "turbine", "power", "industrial", "steel", "factory", "grid", "transformer", "plant"],
    ),
    (
        ["aero", "rocket", "rklb", "ionq", "smr", "nuscale", "oklo", "lmt", "lockheed", "space"],
        ["rocket launch night sky", "aerospace satellite space", "spacecraft engineering"],
        ["rocket", "space", "satellite", "launch", "aerospace", "spacecraft"],
    ),
    (
        [
            "food",
            "foods",
            "samyang",
            "ottogi",
            "orion",
            "daesang",
            "hite",
            "jinro",
            "mdlz",
            "mondelez",
            "cmg",
            "chipotle",
            "mnst",
            "monster",
            "beverage",
            "colgate",
            "cl-colgate",
            "altria",
        ],
        ["food production line factory", "beverage bottling plant", "grocery supermarket shelves"],
        ["food", "beverage", "bottle", "factory", "production", "grocery", "kitchen", "drink"],
    ),
    (
        ["cosmetic", "amore", "amorepacific", "lg-h-and-h", "h-and-h"],
        ["cosmetics laboratory beauty products", "skincare bottles flatlay", "cosmetic production line"],
        ["cosmetic", "beauty", "skincare", "makeup", "lab", "bottles"],
    ),
    (
        ["retail", "bgf", "silicon2", "coway", "shilla", "hotel", "uber", "nike", "underarmour"],
        ["modern retail store interior", "convenience store shelves", "shopping mall corridor"],
        ["store", "retail", "shop", "mall", "shelves", "consumer", "interior"],
    ),
    (
        ["toy", "toys", "aurora", "aurora-world", "sonokong", "daewon", "character", "plush", "mimiworld"],
        [
            "plush stuffed animals teddy bear shelf",
            "toy store colorful shelves children",
            "soft toys display collection",
        ],
        ["toy", "toys", "plush", "teddy", "bear", "stuffed", "doll", "character", "kids", "children", "store", "shelf"],
    ),
    (
        ["logistics", "cj-logistics", "hmm"],
        ["cargo container port aerial", "logistics warehouse shelves", "container ship sea"],
        ["cargo", "container", "port", "warehouse", "logistics", "ship", "shipping"],
    ),
    (
        [
            "bank",
            "financial",
            "card",
            "paypal",
            "pypl",
            "coinbase",
            "coin",
            "mstr",
            "strategy",
            "samsung-card",
            "kb",
            "shinhan",
        ],
        ["bank skyscraper financial district", "stock market trading floor", "financial charts screens"],
        ["bank", "financial", "trading", "market", "money", "finance", "tower"],
    ),
    (
        [
            "enter",
            "hybe",
            "sm-entertainment",
            "pearlabyss",
            "kakao",
            "naver",
            "douzone",
            "salesforce",
            "crm",
            "servicenow",
            "now",
            "ibm",
            "dell",
            "cisco",
            "csco",
            "palantir",
            "pltr",
            "meta",
            "tesla",
            "tsla",
            "samsung-sds",
            "sk-square",
        ],
        ["modern tech office workspace", "data center server racks", "software developer screens code"],
        ["office", "tech", "data center", "server", "software", "code", "screens", "computer"],
    ),
    (
        ["construction", "samsung-cnt", "cnt", "hyundai-engineering", "engineering-construction"],
        ["construction site cranes skyline", "skyscraper construction steel", "building under construction"],
        ["construction", "crane", "building", "site", "steel", "skyline"],
    ),
]

DEFAULT_QUERIES = [
    "corporate skyscraper city skyline",
    "modern office building glass facade",
    "business district downtown",
]
DEFAULT_KEYWORDS = ["building", "office", "city", "skyline", "tower", "downtown", "architecture", "skyscraper"]

# 모든 카테고리 마지막 안전망: 깨끗한 기업/금융 스카이라인(흑백+스크림 아래 무난). 느슨한 게이트.
GENERIC_FALLBACK = [
    ("city financial district skyline", DEFAULT_KEYWORDS),
    ("corporate office building glass facade", DEFAULT_KEYWORDS),
    ("downtown skyscrapers business", DEFAULT_KEYWORDS),
]

# 거부 피사체(썸네일 배경 부적합): 초상화·지도·인물 등. title/tags 에 있으면 탈락.
# 운영자 지시(2026-07): 회사 로고·상징품·제품은 내용 연상에 오히려 좋으니 거부하지 않는다
# (logo·emblem·seal·icon 제거). 인물 초상·지도·묘지·무기 등만 거부.
REJECT_TOKENS = (
    "portrait",
    "painting",
    "map",
    "flag",
    "banknote",
    "engraving",
    "statue",
    "bust",
    "grave",
    "tomb",
    "surgeon",
    "uniform",
    "soldier",
    "portrait of",
)

# 공시 읽기: 문서·감사·규제·거래소 (글 순서로 변주)
DISCLOSURE_THEMES: list[tuple[list[str], list[str]]] = [
    (["financial documents desk paperwork"], ["document", "paper", "desk", "report", "finance"]),
    (["annual report business documents"], ["report", "document", "business", "paper"]),
    (["stock exchange building facade"], ["exchange", "building", "stock", "facade"]),
    (["accounting audit calculator spreadsheet"], ["accounting", "audit", "calculator", "spreadsheet", "finance"]),
    (["business meeting boardroom table"], ["meeting", "boardroom", "office", "business", "table"]),
    (["library archive documents shelves"], ["library", "archive", "document", "shelves", "books"]),
    (["financial newspaper stock listings"], ["newspaper", "stock", "listings", "financial", "print"]),
    (["magnifying glass document analysis"], ["magnifying", "document", "analysis", "paper"]),
]

# 신용: 채권·신용·은행·재무
CREDIT_THEMES: list[tuple[list[str], list[str]]] = [
    (["bond market financial district"], ["bond", "financial", "district", "market", "bank"]),
    (["bank vault finance"], ["bank", "vault", "finance", "money"]),
    (["credit rating financial charts"], ["credit", "rating", "charts", "financial", "graph"]),
    (["balance sheet accounting documents"], ["balance", "accounting", "document", "sheet", "finance"]),
    (["downtown banking towers dusk"], ["bank", "tower", "downtown", "building", "finance"]),
]

CODE_RE = re.compile(r"^(\d{6}|[A-Z]{1,5})$")


def companyStages(slug_name: str) -> list[tuple[str, list[str]]]:
    """슬러그에서 업종 추론 → (쿼리, 키워드) 단계 리스트. 매핑되면 업종 쿼리, 아니면 기업 스카이라인."""
    hay = slug_name.lower()
    for detect, queries, keywords in SECTORS:
        if any(tok in hay for tok in detect):
            return [(q, keywords) for q in queries]  # 업종 매핑: 깨끗·구체. 회사명 직검색은 오매치라 안 씀
    return [(q, DEFAULT_KEYWORDS) for q in DEFAULT_QUERIES]  # 미매핑: 안정적 기업 스카이라인


def themeFor(category: str, slug_name: str, order: int) -> list[tuple[str, list[str]]]:
    """카테고리별 (쿼리, 키워드) 단계 리스트. 마지막에 범용 폴백을 붙여 0매치 최소화."""
    if category == "company-reports":
        stages = companyStages(slug_name)
    elif category == "tech-story":
        stages = companyStages(slug_name)  # 슬러그의 기술 토큰(semi·silicon·battery 등)으로 업종 실사 추론
    elif category == "reading-disclosures":
        q, k = DISCLOSURE_THEMES[order % len(DISCLOSURE_THEMES)]
        stages = [(query, k) for query in q]
    elif category == "credit-reports":
        q, k = CREDIT_THEMES[order % len(CREDIT_THEMES)]
        stages = [(query, k) for query in q]
    else:
        stages = [(query, DEFAULT_KEYWORDS) for query in DEFAULT_QUERIES]
    return stages + GENERIC_FALLBACK


def cleanSubject(item: dict) -> bool:
    """초상화·로고·지도 등 부적합 피사체 거부(title/tags 토큰 검사)."""
    hay = (item.get("title") or "").lower()
    hay += " " + " ".join(t.get("name", "") for t in (item.get("tags") or [])).lower()
    return not any(tok in hay for tok in REJECT_TOKENS)


def findBg(post_dir: Path) -> Path | None:
    hits = sorted((post_dir / "assets").glob("*thumbnail-bg.webp"))
    return hits[0] if hits else None


def categoryOf(post_dir: Path) -> str:
    """폴더명 '05-company-reports' → 'company-reports'."""
    return re.sub(r"^\d+-", "", post_dir.parent.name)


def iterImageless():
    """배경 없는 글을 (NN, slug_name, category, post_dir, order) 로 순회. order=카테고리 내 등장 순번."""
    seen: dict[str, int] = {}
    for md in sorted(BLOG.glob("*/*/index.md")):
        post_dir = md.parent
        m = re.match(r"^(\d+)-(.+)$", post_dir.name)
        if not m:
            continue
        nn, slug_name = m.group(1), m.group(2)
        cat = categoryOf(post_dir)
        order = seen.get(cat, 0)
        seen[cat] = order + 1
        yield nn, slug_name, cat, post_dir, order


# 한 process 안에서 이미 쓴 이미지 URL. 인접·동업종 중복 방지(전역 1장 1회).
USED_URLS: set[str] = set()


def run(nn: str, slug_name: str, cat: str, post_dir: Path, order: int, force: bool, dry: bool) -> str:
    out = post_dir / "assets" / f"{nn}-thumbnail-bg.webp"
    if findBg(post_dir) and not force:
        return f"SKIP {nn}-{slug_name} (배경 있음)"
    stages = themeFor(cat, slug_name, order)
    if dry:
        return f"DRY  {nn}-{slug_name} [{cat}] ← {stages[0][0]} (+{len(stages) - 1})"

    # 모든 단계의 관련·깨끗 후보를 1회 수집(쿼리당 1회 호출, 로컬 dedup).
    pool: list[tuple[dict, str]] = []
    local: set[str] = set()
    for query, keywords in stages:
        for it in _candidates(query):
            url = it.get("url", "")
            if not url or url in local:
                continue
            if _relevant(it, keywords) and cleanSubject(it):
                local.add(url)
                pool.append((it, query))
    if not pool:
        return f"MISS {nn}-{slug_name} [{cat}]: PD/CC0 매치 없음 (쿼리 조정 필요)"

    # 전역 미사용 우선, 다 쓰였으면 재사용 허용(navy 폴백 방지). 둘 다 order 로 회전 → 인접 글과 다른 사진.
    unused = [(it, q) for it, q in pool if (it.get("url") or "") not in USED_URLS]
    chosen = unused if unused else pool
    start = order % len(chosen)
    for item, query in chosen[start:] + chosen[:start]:
        url = item.get("url", "")
        was_used = url in USED_URLS
        im = _download(url)
        if im is None:
            continue
        USED_URLS.add(url)
        size = _save_webp(im, out)
        lic = f"{item.get('license', '')} {item.get('license_version', '')}".strip()
        cred = post_dir / "assets" / "CREDITS.md"
        header = "" if cred.exists() else "# 썸네일 배경 출처 (CC0 / Public Domain, Wikimedia Commons · Openverse)\n\n"
        with cred.open("a", encoding="utf-8") as fh:
            fh.write(header + _credit_line("thumbnail-bg", query, item) + "\n")
        reused = " (재사용)" if was_used else ""
        return f"OK   {nn}-{slug_name} ({size // 1024} KB) ← [{query}] {lic}{reused}"
    return f"MISS {nn}-{slug_name} [{cat}]: 다운로드 실패"


def main() -> None:
    ap = argparse.ArgumentParser(description="블로그 전체 CC0 썸네일 배경 수급 (이미지 없는 글)")
    ap.add_argument("--only", help="특정 폴더명 (예: 01-000660-skhynix)")
    ap.add_argument("--limit", type=int, default=0, help="최대 N개만(0=전체)")
    ap.add_argument("--force", action="store_true", help="기존 배경 덮어쓰기")
    ap.add_argument("--dry", action="store_true", help="쿼리만 출력(수급 안 함)")
    args = ap.parse_args()

    n_ok = n_miss = n = 0
    for nn, slug_name, cat, post_dir, order in iterImageless():
        folder = f"{nn}-{slug_name}"
        if args.only and folder != args.only:
            continue
        if not args.force and findBg(post_dir):
            continue
        if args.limit and n >= args.limit:
            break
        msg = run(nn, slug_name, cat, post_dir, order, args.force, args.dry)
        print(msg)
        n += 1
        if msg.startswith("OK"):
            n_ok += 1
        elif msg.startswith("MISS"):
            n_miss += 1
    print(f"\nDONE {n} 처리 ({n_ok} OK / {n_miss} MISS). 다음: gen_blog_thumbnails.py --all --apply")


if __name__ == "__main__":
    main()
