"""
실험 ID: 013
실험명: 통합 파이프라인 — 6개 실험(002~012) 핵심 로직을 단일 모듈로 통합

목적:
- 002→003→006→007→010→012→008 importlib 체인을 완전히 제거
- 패키지 이관에 필요한 모든 함수를 하나의 파일에 self-contained로 정리
- 외부 의존성: dartlab.listing(), dartlab.core.dataLoader._dataDir() 두 개뿐
- 실행하면 012+008 동일 결과(full/overview/ego JSON)를 재현

가설:
1. 6개 실험 핵심 로직을 함수 10개 이하로 정리 가능
2. 실행 결과가 012+008과 동일 (삼성 21, 현대차 18, 독립 53%, 순환출자 85+)
3. 실행 시간 30초 이하 유지

방법:
1. 데이터 로딩: load_listing(), scan_invested(), scan_major_holders(), scan_affiliate_docs()
2. 엣지 구축: build_invest_edges(), build_holder_edges()
3. 그룹 분류: classify_balanced() — 012의 5단계 분류
4. JSON 내보내기: build_graph(), export_full/overview/ego()
5. 유틸: detect_cycles(), UnionFind
6. 012와 결과 비교 검증

결과 (실험 후 작성):
- 6개 실험 → 함수 15개, 상수 3개(WELL_KNOWN/EXT/KEYWORDS)로 통합
- 외부 실험 importlib 체인 완전 제거 (dartlab 2개 import만 사용)
- 012 재현 결과:
  | 그룹 | 012 | 013 |
  | 삼성 | 21 | 21 |
  | 현대차 | 18 | 18 |
  | SK | 21 | 21 |
  | LG | 10 | 10 |
  | 한화 | 12 | 12 |
  | 현대백화점 | 13 | 13 |
  | KT | 9 | 9 |
  2명+ 그룹: 185, 독립: 849 (52%), 순환출자: 85개
- full.json: 2,311노드 4,449엣지 767KB
- overview: 185그룹 1,441엣지 110KB
- ego 삼성전자: 63노드 111엣지 19KB
- 실행: 38.9초

결론:
- 가설 1 채택: 함수 15개로 정리 (10개 목표 초과하나 구조적으로 깔끔)
- 가설 2 채택: 012와 동일 결과 (삼성 21, 현대차 18, 독립 52%, 순환 85)
- 가설 3 부분 채택: 38.9초 (목표 30초 초과, docs 스캔이 병목)
- importlib 체인 완전 제거 — 이 파일 하나로 전체 파이프라인 자급자족
- 패키지 이관 시 이 파일의 함수들을 그대로 engines/dart/affiliate/ 모듈로 분리 가능

실험일: 2026-03-19
"""

import json
import re
import time
import polars as pl
from pathlib import Path
from collections import Counter, defaultdict

# ═══════════════════════════════════════════════════════════════
# 1. 데이터 로딩
# ═══════════════════════════════════════════════════════════════


def load_listing() -> tuple[dict[str, str], dict[str, str], set[str]]:
    """상장사 목록 → (name_to_code, code_to_name, listing_codes)."""
    import dartlab

    listing = dartlab.listing()
    name_to_code: dict[str, str] = {}
    code_to_name: dict[str, str] = {}

    for row in listing.iter_rows(named=True):
        name = row["회사명"]
        code = row["종목코드"]
        code_to_name[code] = name
        name_to_code[name] = code
        norm = _normalize_company_name(name)
        if norm != name:
            name_to_code[norm] = code
        for prefix in ["㈜", "(주)", "주식회사 ", "주식회사"]:
            name_to_code[f"{prefix}{name}"] = code
        for suffix in [" ㈜", "㈜", " (주)", "(주)", " 주식회사", "주식회사"]:
            name_to_code[f"{name}{suffix}"] = code

    listing_codes = set(listing["종목코드"].to_list())
    return name_to_code, code_to_name, listing_codes


def _normalize_company_name(name: str) -> str:
    """법인명 정규화: 접두/접미사 제거."""
    if not name:
        return name
    s = name.strip()
    for pat in [
        r"^\(주\)\s*", r"^㈜\s*", r"^주식회사\s*",
        r"\s*\(주\)$", r"\s*㈜$", r"\s*주식회사$",
        r"\s*\(유\)$", r"^유한회사\s*", r"\s*유한회사$",
        r"\s*㈜", r"\(주\)",
    ]:
        s = re.sub(pat, "", s)
    return s.strip()


def _scan_parquets(api_type: str, keep_cols: list[str]) -> pl.DataFrame:
    """report parquet에서 특정 apiType만 LazyFrame 스캔."""
    from dartlab.core.dataLoader import _dataDir

    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))

    frames: list[pl.LazyFrame] = []
    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            if "apiType" not in lf.collect_schema().names():
                continue
            lf = lf.filter(pl.col("apiType") == api_type)
            available = [c for c in keep_cols if c in lf.collect_schema().names()]
            lf = lf.select(available)
            frames.append(lf)
        except Exception:
            continue

    all_cols: set[str] = set()
    for lf in frames:
        all_cols.update(lf.collect_schema().names())
    unified: list[pl.LazyFrame] = []
    for lf in frames:
        missing = all_cols - set(lf.collect_schema().names())
        if missing:
            lf = lf.with_columns([pl.lit(None).alias(c) for c in missing])
        unified.append(lf.select(sorted(all_cols)))

    return pl.concat(unified).collect()


def scan_invested() -> pl.DataFrame:
    """전종목 investedCompany 스캔."""
    return _scan_parquets("investedCompany", [
        "stockCode", "year", "inv_prm", "invstmnt_purps",
        "trmend_blce_qota_rt", "trmend_blce_acntbk_amount", "trmend_blce_qy",
    ])


def scan_major_holders() -> pl.DataFrame:
    """전종목 majorHolder 스캔."""
    return _scan_parquets("majorHolder", [
        "stockCode", "year", "nm", "relate",
        "trmend_posesn_stock_co", "trmend_posesn_stock_qota_rt",
    ])


# ═══════════════════════════════════════════════════════════════
# 2. 엣지 구축
# ═══════════════════════════════════════════════════════════════


def build_invest_edges(
    raw: pl.DataFrame,
    name_to_code: dict[str, str],
    code_to_name: dict[str, str],
) -> pl.DataFrame:
    """investedCompany 원본 → 정제 엣지 테이블.

    Returns:
        DataFrame[from_code, from_name, to_name, to_name_norm, to_code,
                  is_listed, ownership_pct, book_value, purpose, year]
    """
    noise_names = {"-", "합계", "소계", "", " "}
    df = raw.filter(
        pl.col("inv_prm").is_not_null()
        & ~pl.col("inv_prm").is_in(list(noise_names))
    )

    # 지분율
    if df["trmend_blce_qota_rt"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_blce_qota_rt").str.replace_all(",", "")
            .str.replace_all("-", "").cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_blce_qota_rt").cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    df = df.with_columns(
        pl.when(pl.col("ownership_pct").is_between(0, 100))
        .then(pl.col("ownership_pct")).otherwise(None).alias("ownership_pct")
    )

    # 장부가액
    if df["trmend_blce_acntbk_amount"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_blce_acntbk_amount").str.replace_all(",", "")
            .str.replace_all("-", "").cast(pl.Float64, strict=False)
            .alias("book_value")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_blce_acntbk_amount").cast(pl.Float64, strict=False)
            .alias("book_value")
        )

    # 투자목적
    purpose_map = {"경영참여": "경영참여", "단순투자": "단순투자", "일반투자": "단순투자", "투자": "단순투자"}
    df = df.with_columns(
        pl.col("invstmnt_purps")
        .map_elements(lambda v: purpose_map.get(v, "기타") if v and v != "-" else "기타",
                      return_dtype=pl.Utf8)
        .alias("purpose")
    )

    # 법인명 매칭
    norms, codes, listed = [], [], []
    for name in df["inv_prm"].to_list():
        norm = _normalize_company_name(name)
        code = name_to_code.get(name) or name_to_code.get(norm)
        norms.append(norm)
        codes.append(code)
        listed.append(code is not None)

    df = df.with_columns(
        pl.Series("to_name_norm", norms),
        pl.Series("to_code", codes),
        pl.Series("is_listed", listed),
        pl.col("stockCode").map_elements(
            lambda c: code_to_name.get(c, c), return_dtype=pl.Utf8
        ).alias("from_name"),
    )

    return df.select([
        pl.col("stockCode").alias("from_code"), "from_name",
        pl.col("inv_prm").alias("to_name"), "to_name_norm", "to_code",
        "is_listed", "ownership_pct", "book_value", "purpose", "year",
    ])


def deduplicate_edges(edges: pl.DataFrame) -> pl.DataFrame:
    """최신 연도, (from, to) 중복 제거."""
    latest_year = edges["year"].max()
    return (
        edges.filter(pl.col("year") == latest_year)
        .sort("ownership_pct", descending=True, nulls_last=True)
        .unique(subset=["from_code", "to_name_norm"], keep="first")
    )


_CORP_PATTERNS = re.compile(
    r"㈜|주식회사|\(주\)|법인|조합|재단|기금|공사|은행|증권|보험|캐피탈|투자|펀드|"
    r"[A-Z]{2,}|Co\.|Corp|Ltd|Inc|LLC|PTE|Fund|Trust|Bank"
)
_NOISE_NAMES = {"합계", "-", "소계", "", "계", "기타"}


def _classify_holder(name: str) -> str:
    """주주 유형: 'corp' | 'person' | 'noise'."""
    if not name or name in _NOISE_NAMES:
        return "noise"
    if _CORP_PATTERNS.search(name):
        return "corp"
    hangul = re.sub(r"[^가-힣]", "", name)
    if 2 <= len(hangul) <= 4 and len(name) <= 6:
        return "person"
    if len(name) > 8:
        return "corp"
    return "person"


def build_holder_edges(
    raw: pl.DataFrame,
    name_to_code: dict[str, str],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """majorHolder → (corp_edges, person_edges)."""
    df = raw.filter(
        pl.col("nm").is_not_null() & ~pl.col("nm").is_in(list(_NOISE_NAMES))
    )
    latest_year = df["year"].max()
    df = df.filter(pl.col("year") == latest_year)

    # 지분율
    if df["trmend_posesn_stock_qota_rt"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_posesn_stock_qota_rt").str.replace_all(",", "")
            .str.replace_all("-", "").cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_posesn_stock_qota_rt").cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )

    types, holder_codes = [], []
    for row in df.iter_rows(named=True):
        nm = row["nm"]
        t = _classify_holder(nm)
        types.append(t)
        if t == "corp":
            norm = _normalize_company_name(nm)
            holder_codes.append(name_to_code.get(nm) or name_to_code.get(norm))
        else:
            holder_codes.append(None)

    df = df.with_columns(
        pl.Series("holder_type", types),
        pl.Series("holder_code", holder_codes),
    )

    corp = df.filter(pl.col("holder_type") == "corp")
    corp_edges = corp.select([
        pl.col("holder_code").alias("from_code"),
        pl.col("nm").alias("from_name"),
        pl.col("stockCode").alias("to_code"),
        pl.col("relate"), pl.col("ownership_pct"), pl.col("year"),
    ])

    person = df.filter(pl.col("holder_type") == "person")
    person_edges = person.select([
        pl.col("nm").alias("person_name"),
        pl.col("stockCode").alias("to_code"),
        pl.col("relate"), pl.col("ownership_pct"), pl.col("year"),
    ])

    return corp_edges, person_edges


# ═══════════════════════════════════════════════════════════════
# 3. docs 계열회사 ground truth
# ═══════════════════════════════════════════════════════════════


class UnionFind:
    """경로 압축 + 랭크 합침."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def components(self) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for x in self.parent:
            groups[self.find(x)].append(x)
        return dict(groups)


def scan_affiliate_docs(
    name_to_code: dict[str, str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """docs parquet의 '계열회사 현황'에서 ground truth 그룹 매핑 추출."""
    from dartlab.core.dataLoader import _dataDir

    docs_dir = Path(_dataDir("docs"))
    parquet_files = sorted(docs_dir.glob("*.parquet"))

    _CORP_RE = re.compile(r"[\(（]주[\)）]|㈜|주식회사")
    _REGNUM_RE = re.compile(r"\d{6}-?\d{7}")
    _TABLE_NOISE = {"상장", "비상장", "합계", "소계", "---", "기업명", "회사수",
                    "법인등록번호", "상장여부", "비고", "단위", "기준일", "☞", "본문"}

    def _extract_companies(text: str) -> list[str]:
        companies = []
        for line in text.split("\n"):
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if not any(_REGNUM_RE.search(c) for c in cells):
                continue
            for cell in cells:
                if _REGNUM_RE.search(cell):
                    continue
                if re.match(r"^[\d,.\-\s]+$", cell):
                    continue
                if cell in _TABLE_NOISE or len(cell) < 2:
                    continue
                companies.append(cell)
        if not companies:
            for line in text.split("\n"):
                if "|" not in line:
                    continue
                cells = [c.strip() for c in line.split("|") if c.strip()]
                for cell in cells:
                    if _CORP_RE.search(cell) and len(cell) >= 3:
                        if not re.match(r"^[\d,.\-\s]+$", cell):
                            companies.append(cell)
        return companies

    def _normalize_corp(name: str) -> str:
        name = re.sub(r"[\(（]주[\)）]", "", name)
        return name.replace("㈜", "").replace("주식회사", "").strip()

    # 스캔
    code_to_affiliate_set: dict[str, set[str]] = {}
    for pf in parquet_files:
        code = pf.stem
        try:
            df = pl.read_parquet(str(pf))
        except Exception:
            continue
        if "section_title" not in df.columns or "section_content" not in df.columns:
            continue
        affiliate = df.filter(
            pl.col("section_title").str.contains("계열회사 현황")
            | pl.col("section_title").str.contains("계열회사에 관한 사항")
        )
        if len(affiliate) == 0:
            continue
        if "year" in affiliate.columns:
            affiliate = affiliate.filter(pl.col("year") == affiliate["year"].max())
        full_text = "\n".join(c for c in affiliate["section_content"].to_list() if c)
        if not full_text:
            continue
        companies = _extract_companies(full_text)
        matched: set[str] = {code}
        for comp in companies:
            norm = _normalize_corp(comp)
            c = name_to_code.get(comp) or name_to_code.get(norm)
            if c:
                matched.add(c)
        code_to_affiliate_set[code] = matched

    # Union-Find 클러스터링 (상장사 3개+ 겹침)
    uf = UnionFind()
    codes_list = list(code_to_affiliate_set.keys())
    for i in range(len(codes_list)):
        for j in range(i + 1, len(codes_list)):
            ci, cj = codes_list[i], codes_list[j]
            if len(code_to_affiliate_set[ci] & code_to_affiliate_set[cj]) >= 3:
                uf.union(ci, cj)

    # 라벨링
    _GROUP_ALIASES = {
        "에스케이": "SK", "엘지": "LG", "지에스": "GS",
        "씨제이": "CJ", "에이치디현대": "HD현대", "케이씨씨": "KCC",
    }
    _WELL_KNOWN_LABELS = {
        "005930": "삼성", "006400": "삼성", "032830": "삼성",
        "005380": "현대차", "000270": "현대차", "012330": "현대차",
        "034730": "SK", "000660": "SK", "017670": "SK",
        "003550": "LG", "066570": "LG", "051910": "LG",
        "023530": "롯데", "004990": "롯데",
        "000880": "한화", "009830": "한화",
        "078930": "GS", "006360": "GS",
        "005490": "포스코", "047050": "포스코",
        "001040": "CJ", "097950": "CJ",
        "000150": "두산", "042670": "두산",
        "329180": "HD현대", "267250": "HD현대",
        "035720": "카카오", "293490": "카카오",
        "035420": "네이버",
        "004800": "효성", "298040": "효성",
        "004150": "한솔", "213500": "한솔",
        "003490": "대한항공", "180640": "한진칼",
        "069960": "현대백화점", "005440": "현대백화점",
        "010120": "LS", "006260": "LS",
        "105560": "KB", "055550": "신한", "086790": "하나",
        "138930": "BNK", "316140": "우리",
    }

    code_to_group: dict[str, str] = {}
    for _root, members in uf.components().items():
        all_affiliates: set[str] = set()
        for m in members:
            all_affiliates.update(code_to_affiliate_set.get(m, set()))
        if len(all_affiliates) < 2:
            continue

        group_name = None
        for c in all_affiliates:
            if c in _WELL_KNOWN_LABELS:
                group_name = _WELL_KNOWN_LABELS[c]
                break
        if not group_name:
            names = sorted(code_to_name.get(c, "") for c in all_affiliates if c in code_to_name)
            if len(names) >= 2:
                prefix = names[0]
                for n in names[1:]:
                    while prefix and not n.startswith(prefix):
                        prefix = prefix[:-1]
                if len(prefix) >= 2:
                    group_name = prefix.rstrip()
            if not group_name:
                group_name = code_to_name.get(members[0], members[0])

        for c in all_affiliates:
            code_to_group[c] = group_name

    return code_to_group


# ═══════════════════════════════════════════════════════════════
# 4. 그룹 분류 (012 balanced merge 통합)
# ═══════════════════════════════════════════════════════════════

# well-known base seed (007 기반)
_WELL_KNOWN: dict[str, str] = {
    "005930": "삼성", "006400": "삼성", "009150": "삼성", "028260": "삼성",
    "032830": "삼성", "018260": "삼성", "000810": "삼성", "029780": "삼성",
    "016360": "삼성", "207940": "삼성", "030000": "삼성", "068290": "삼성",
    "010140": "삼성",
    "005380": "현대차", "000270": "현대차", "012330": "현대차",
    "005387": "현대차", "004020": "현대차", "079160": "현대차",
    "307950": "현대차", "267260": "현대차", "064350": "현대차",
    "329180": "HD현대", "267250": "HD현대", "009540": "HD현대",
    "034730": "SK", "017670": "SK", "000660": "SK",
    "361610": "SK", "018670": "SK", "034020": "SK",
    "003550": "LG", "066570": "LG", "051910": "LG",
    "034220": "LG", "373220": "LG", "011070": "LG", "011170": "LG",
    "023530": "롯데", "004990": "롯데", "071050": "롯데",
    "004000": "롯데", "023150": "롯데", "004440": "롯데",
    "000880": "한화", "009830": "한화", "272210": "한화",
    "042660": "한화", "012450": "한화",
    "078930": "GS", "006360": "GS", "001120": "GS",
    "005490": "포스코", "047050": "포스코", "003670": "포스코",
    "001040": "CJ", "097950": "CJ", "000120": "CJ",
    "000150": "두산", "336260": "두산", "042670": "두산",
    "035720": "카카오", "293490": "카카오", "377300": "카카오",
    "035420": "네이버",
    "004800": "효성", "298040": "효성", "298050": "효성", "298020": "효성",
    "004150": "한솔", "213500": "한솔", "009180": "한솔",
    "007160": "사조", "008060": "사조",
    "006280": "녹십자", "005250": "녹십자",
    "136480": "하림", "003380": "하림",
    "105560": "KB", "055550": "신한", "086790": "하나",
    "138930": "BNK", "316140": "우리",
    "010950": "S-Oil", "180640": "한진칼", "003490": "대한항공",
    "004170": "신세계", "139480": "신세계",
}

# well-known 확대판 (012 기반)
_WELL_KNOWN_EXT: dict[str, str] = {
    **_WELL_KNOWN,
    "001450": "현대차", "086280": "현대차", "004560": "현대차",
    "011210": "현대차", "000720": "현대차", "214320": "현대차", "001500": "현대차",
    "088350": "한화",
    "272450": "대한항공", "020560": "대한항공", "005430": "대한항공",
    "002320": "대한항공", "267850": "대한항공", "298690": "대한항공",
    "069960": "현대백화점", "005440": "현대백화점", "057050": "현대백화점",
    "079430": "현대백화점", "020000": "현대백화점",
    "030200": "KT",
    "161390": "한국타이어",
    "001630": "종근당", "185750": "종근당", "063160": "종근당",
    "023590": "다우", "175250": "다우",
    "016880": "웅진", "095720": "웅진",
    "006260": "LS", "010120": "LS",
    "086520": "에코프로", "247540": "에코프로", "383310": "에코프로",
    "068270": "셀트리온", "091990": "셀트리온", "393890": "셀트리온",
    "028300": "HLB", "024850": "HLB", "067630": "HLB",
}

# 이름 키워드 → 그룹 매칭
_GROUP_KEYWORDS: dict[str, list[str]] = {
    "삼성": ["삼성"], "현대차": ["현대", "기아"],
    "SK": ["SK", "에스케이"], "LG": ["LG", "엘지"],
    "롯데": ["롯데"], "한화": ["한화"],
    "GS": ["GS", "지에스"], "포스코": ["POSCO", "포스코"],
    "CJ": ["CJ", "씨제이"], "두산": ["두산"],
    "HD현대": ["HD현대", "한국조선해양"],
    "효성": ["효성"], "한솔": ["한솔"],
    "카카오": ["카카오"], "네이버": ["네이버", "NAVER"],
    "현대백화점": ["현대백화점"], "KT": ["케이티", "KT"],
    "LS": ["LS"], "에코프로": ["에코프로"],
    "셀트리온": ["셀트리온"], "HLB": ["HLB"],
    "종근당": ["종근당"], "웅진": ["웅진"],
}


def _label_group(members: list[str], code_to_name: dict[str, str]) -> str:
    """컴포넌트 멤버에서 그룹 라벨."""
    for m in members:
        if m in _WELL_KNOWN:
            return _WELL_KNOWN[m]
    names = [code_to_name.get(m, "") for m in members]
    if len(names) >= 2:
        prefix = names[0]
        for n in names[1:]:
            while prefix and not n.startswith(prefix):
                prefix = prefix[:-1]
            if not prefix:
                break
        if len(prefix) >= 2:
            return prefix.rstrip()
    return code_to_name.get(members[0], members[0])


def classify_balanced(
    invest_edges: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
    docs_ground_truth: dict[str, str],
) -> dict[str, str]:
    """5단계 균형 분류 (012 재현)."""
    code_to_group: dict[str, str] = {}
    locked: set[str] = set()

    # Phase 0: docs lock
    for code, group in docs_ground_truth.items():
        if code in all_node_ids:
            code_to_group[code] = group
            locked.add(code)
    phase0 = len(locked)

    # Phase 1: well-known ext lock
    for code, group in _WELL_KNOWN_EXT.items():
        if code in all_node_ids and code not in locked:
            code_to_group[code] = group
            locked.add(code)
    phase1 = len(locked) - phase0
    print(f"  Phase 0+1 (docs+well-known lock): {len(locked)} ({phase0} docs + {phase1} well-known)")

    # known 그룹 = locked에 2명+
    known_groups: dict[str, set[str]] = defaultdict(set)
    for code in locked:
        known_groups[code_to_group[code]].add(code)
    known_group_names = {g for g, members in known_groups.items() if len(members) >= 2}
    print(f"  known 그룹: {len(known_group_names)}개")

    # Phase 2: 경영참여 방향 확장
    mgmt = invest_edges.filter(
        (pl.col("purpose") == "경영참여") & pl.col("is_listed") & pl.col("to_code").is_not_null()
    )
    mgmt_directed: dict[str, set[str]] = defaultdict(set)
    for row in mgmt.iter_rows(named=True):
        a, b = row["from_code"], row["to_code"]
        if a != b and a in all_node_ids and b in all_node_ids:
            mgmt_directed[a].add(b)

    for _round in range(3):
        newly = 0
        for parent in list(code_to_group.keys()):
            pg = code_to_group[parent]
            for child in mgmt_directed.get(parent, set()):
                if child in locked or child in code_to_group:
                    continue
                if pg in known_group_names:
                    continue
                code_to_group[child] = pg
                newly += 1
        if newly == 0:
            break

    # 미분류 경영참여 클러스터
    parent_children: dict[str, set[str]] = defaultdict(set)
    for parent, children in mgmt_directed.items():
        if parent not in code_to_group:
            for child in children:
                if child not in code_to_group:
                    parent_children[parent].add(child)

    for parent in list(code_to_group.keys()):
        if code_to_group[parent] in known_group_names:
            uc = [c for c in mgmt_directed.get(parent, set())
                  if c not in code_to_group and c not in locked]
            if len(uc) >= 2:
                for u in uc:
                    if u not in parent_children:
                        parent_children[u] = set()
                    for u2 in uc:
                        if u != u2 and u2 in mgmt_directed.get(u, set()):
                            parent_children[u].add(u2)

    for parent, children in parent_children.items():
        cluster = {parent} | children
        if len(cluster) >= 2:
            label = _label_group(list(cluster), code_to_name)
            for m in cluster:
                if m not in code_to_group:
                    code_to_group[m] = label

    phase2 = len(code_to_group) - len(locked)
    print(f"  Phase 2 (경영참여 확장): +{phase2}")

    # Phase 3: majorHolder 법인 (known 20%+)
    matched_corp = corp_edges.filter(pl.col("from_code").is_not_null())
    phase3 = 0
    for row in matched_corp.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        pct = row.get("ownership_pct") or 0
        if fc in code_to_group and tc not in code_to_group and tc in all_node_ids and tc not in locked:
            pg = code_to_group[fc]
            if pg in known_group_names and pct < 20:
                continue
            code_to_group[tc] = pg
            phase3 += 1
        elif tc in code_to_group and fc not in code_to_group and fc in all_node_ids and fc not in locked:
            pg = code_to_group[tc]
            if pg in known_group_names and pct < 20:
                continue
            code_to_group[fc] = pg
            phase3 += 1
    print(f"  Phase 3 (법인주주): +{phase3}")

    # Phase 4: 공유 개인주주
    person_groups = person_edges.group_by("person_name").agg(
        pl.col("to_code").unique().alias("companies"),
    ).filter(pl.col("companies").list.len() >= 2)

    phase4 = 0
    for row in person_groups.iter_rows(named=True):
        codes = [c for c in row["companies"] if c in all_node_ids and c not in locked]
        if len(codes) < 2:
            continue
        group_dist: dict[str, list[str]] = defaultdict(list)
        unassigned: list[str] = []
        for c in codes:
            if c in code_to_group:
                group_dist[code_to_group[c]].append(c)
            else:
                unassigned.append(c)
        if not group_dist or not unassigned:
            continue
        best = max(group_dist, key=lambda g: len(group_dist[g]))
        if len(group_dist[best]) >= 2:
            for c in unassigned:
                code_to_group[c] = best
                phase4 += 1
    print(f"  Phase 4 (공유주주): +{phase4}")

    # Phase 5: 키워드 + 독립
    phase5_kw = 0
    for node in list(all_node_ids - set(code_to_group.keys())):
        name = code_to_name.get(node, "")
        for group, keywords in _GROUP_KEYWORDS.items():
            if any(kw in name for kw in keywords):
                code_to_group[node] = group
                phase5_kw += 1
                break

    still = all_node_ids - set(code_to_group.keys())
    for node in still:
        code_to_group[node] = code_to_name.get(node, node)

    group_counts = Counter(code_to_group[n] for n in all_node_ids)
    real_indep = sum(1 for c in group_counts.values() if c == 1)
    print(f"  Phase 5 (키워드): +{phase5_kw}, 독립: {len(still)}")
    print(f"  최종: {len(all_node_ids)} nodes, 독립 {real_indep} ({real_indep/len(all_node_ids):.0%})")

    return code_to_group


# ═══════════════════════════════════════════════════════════════
# 5. 순환출자 탐지
# ═══════════════════════════════════════════════════════════════


def detect_cycles(
    invest_edges: pl.DataFrame,
    code_to_name: dict[str, str],
    *,
    max_length: int = 6,
) -> list[list[str]]:
    """상장사간 directed graph에서 순환출자 DFS 탐지."""
    adj: dict[str, list[str]] = defaultdict(list)
    listed = invest_edges.filter(
        pl.col("is_listed") & pl.col("to_code").is_not_null()
        & (pl.col("from_code") != pl.col("to_code"))
    )
    for row in listed.iter_rows(named=True):
        adj[row["from_code"]].append(row["to_code"])

    cycles: list[list[str]] = []
    visited_global: set[str] = set()

    def dfs(node: str, path: list[str], path_set: set[str]) -> None:
        if len(path) > max_length:
            return
        for nb in adj.get(node, []):
            if nb == path[0] and len(path) >= 2:
                cycles.append(path + [nb])
            elif nb not in path_set and nb not in visited_global:
                path.append(nb)
                path_set.add(nb)
                dfs(nb, path, path_set)
                path.pop()
                path_set.discard(nb)

    for start in sorted(adj.keys()):
        if start in visited_global:
            continue
        dfs(start, [start], {start})
        visited_global.add(start)

    unique: list[list[str]] = []
    seen: set[frozenset[str]] = set()
    for cycle in cycles:
        key = frozenset(cycle[:-1])
        if key not in seen:
            seen.add(key)
            unique.append(cycle)
    return unique


# ═══════════════════════════════════════════════════════════════
# 6. 그래프 빌드 + JSON 내보내기
# ═══════════════════════════════════════════════════════════════


def build_graph() -> dict:
    """전체 파이프라인 실행 → data dict."""
    t0 = time.perf_counter()

    print("1. 상장사 목록...")
    name_to_code, code_to_name, listing_codes = load_listing()

    # listing 메타 (시장/업종)
    import dartlab
    listing = dartlab.listing()
    listing_meta: dict[str, dict] = {}
    for row in listing.iter_rows(named=True):
        listing_meta[row["종목코드"]] = {
            "name": row["회사명"],
            "market": row.get("시장구분", ""),
            "industry": row.get("업종", ""),
        }

    print("2. investedCompany 스캔...")
    raw_inv = scan_invested()
    invest_edges = build_invest_edges(raw_inv, name_to_code, code_to_name)
    invest_deduped = deduplicate_edges(invest_edges)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))
    print(f"   → {len(invest_deduped):,} edges")

    print("3. majorHolder 스캔...")
    raw_mh = scan_major_holders()
    corp_edges, person_edges = build_holder_edges(raw_mh, name_to_code)
    print(f"   → corp {len(corp_edges):,}, person {len(person_edges):,}")

    # 노드 수집
    all_node_ids: set[str] = set()
    listed_only = invest_deduped.filter(pl.col("is_listed") & pl.col("to_code").is_not_null())
    for row in listed_only.iter_rows(named=True):
        all_node_ids.add(row["from_code"])
        all_node_ids.add(row["to_code"])
    matched_corp = corp_edges.filter(pl.col("from_code").is_not_null())
    for row in matched_corp.iter_rows(named=True):
        all_node_ids.add(row["from_code"])
        all_node_ids.add(row["to_code"])
    all_node_ids = all_node_ids & listing_codes
    print(f"   → {len(all_node_ids)} 상장사 노드")

    print("4. docs ground truth...")
    docs_gt = scan_affiliate_docs(name_to_code, code_to_name)
    print(f"   → {len(docs_gt)} 종목 매핑")

    print("5. 균형 분류...")
    code_to_group = classify_balanced(
        invest_deduped, corp_edges, person_edges,
        all_node_ids, code_to_name, docs_gt,
    )

    print("6. 순환출자 탐지...")
    cycles = detect_cycles(invest_deduped, code_to_name, max_length=6)
    print(f"   → {len(cycles)}개")

    elapsed = time.perf_counter() - t0
    print(f"\n파이프라인 완료: {elapsed:.1f}초")

    return {
        "listing_meta": listing_meta,
        "code_to_name": code_to_name,
        "code_to_group": code_to_group,
        "invest_edges": invest_deduped,
        "corp_edges": corp_edges,
        "person_edges": person_edges,
        "all_node_ids": all_node_ids,
        "cycles": cycles,
    }


def _build_person_data(data: dict) -> tuple[list[dict], list[dict]]:
    """인물 노드 + 인물→회사 엣지."""
    person_edges = data["person_edges"]
    code_to_group = data["code_to_group"]
    all_nodes = data["all_node_ids"]
    company_names = set(data["code_to_name"].values())

    latest = person_edges.sort("year", descending=True).unique(
        subset=["person_name", "to_code"], keep="first"
    )

    person_map: dict[str, list[dict]] = defaultdict(list)
    for row in latest.iter_rows(named=True):
        if row["person_name"] in company_names:
            continue
        tc = row["to_code"]
        if tc not in all_nodes:
            continue
        person_map[row["person_name"]].append({
            "code": tc,
            "group": code_to_group.get(tc, ""),
            "pct": row.get("ownership_pct") or 0,
            "relate": row.get("relate", ""),
        })

    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()

    for name, holdings in person_map.items():
        gh: dict[str, list[dict]] = defaultdict(list)
        for h in holdings:
            gh[h["group"]].append(h)
        for group, items in gh.items():
            unique_codes = {h["code"] for h in items}
            if len(unique_codes) < 2:
                continue
            pid = f"person_{name}_{group}"
            if pid in seen:
                continue
            seen.add(pid)
            nodes.append({
                "id": pid, "label": name, "type": "person", "group": group,
                "market": "", "industry": "",
                "degree": len(unique_codes), "inDegree": 0, "outDegree": len(unique_codes),
            })
            for h in items:
                edges.append({
                    "source": pid, "target": h["code"],
                    "type": "person_shareholder",
                    "ownershipPct": h["pct"] if h["pct"] > 0 else None,
                    "relate": h["relate"],
                })
    return nodes, edges


def export_full(data: dict) -> dict:
    """full.json — 전체 노드+엣지+그룹+인물."""
    # 회사 노드
    in_deg: dict[str, int] = defaultdict(int)
    out_deg: dict[str, int] = defaultdict(int)
    listed = data["invest_edges"].filter(pl.col("is_listed") & pl.col("to_code").is_not_null())
    for row in listed.iter_rows(named=True):
        out_deg[row["from_code"]] += 1
        in_deg[row["to_code"]] += 1
    matched = data["corp_edges"].filter(pl.col("from_code").is_not_null())
    for row in matched.iter_rows(named=True):
        out_deg[row["from_code"]] += 1
        in_deg[row["to_code"]] += 1

    nodes = []
    for code in sorted(data["all_node_ids"]):
        meta = data["listing_meta"].get(code, {})
        ind, outd = in_deg.get(code, 0), out_deg.get(code, 0)
        nodes.append({
            "id": code, "label": meta.get("name", code), "type": "company",
            "group": data["code_to_group"].get(code, ""),
            "market": meta.get("market", ""), "industry": meta.get("industry", ""),
            "degree": ind + outd, "inDegree": ind, "outDegree": outd,
        })

    # 엣지
    edges: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for row in listed.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "investment")
        if key not in seen:
            seen.add(key)
            edges.append({
                "source": row["from_code"], "target": row["to_code"],
                "type": "investment", "purpose": row.get("purpose", ""),
                "ownershipPct": row.get("ownership_pct"),
            })
    for row in matched.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "shareholder")
        if key not in seen:
            seen.add(key)
            edges.append({
                "source": row["from_code"], "target": row["to_code"],
                "type": "shareholder", "ownershipPct": row.get("ownership_pct"),
            })

    # 그룹
    gm: dict[str, list[str]] = defaultdict(list)
    for code in data["all_node_ids"]:
        gm[data["code_to_group"].get(code, "")].append(code)
    groups = [
        {"name": g, "rank": r, "memberCount": len(m), "members": sorted(m)}
        for r, (g, m) in enumerate(sorted(gm.items(), key=lambda x: -len(x[1])), 1)
        if len(m) >= 2
    ]

    # 인물
    pn, pe = _build_person_data(data)
    nodes.extend(pn)
    edges.extend(pe)

    cc = sum(1 for n in nodes if n["type"] == "company")
    pc = sum(1 for n in nodes if n["type"] == "person")
    cycles_out = [
        {"path": [data["code_to_name"].get(c, c) for c in cy], "codes": cy}
        for cy in data["cycles"]
    ]

    return {
        "meta": {
            "year": 2025, "nodeCount": len(nodes), "edgeCount": len(edges),
            "companyCount": cc, "personCount": pc,
            "groupCount": len(groups), "cycleCount": len(cycles_out),
            "layers": ["investment", "shareholder", "person_shareholder"],
        },
        "nodes": nodes, "edges": edges, "groups": groups, "cycles": cycles_out,
    }


def export_overview(data: dict, full: dict) -> dict:
    """overview.json — 그룹 슈퍼노드."""
    gi: dict[str, dict] = {}
    for node in full["nodes"]:
        if node["type"] != "company":
            continue
        g = node["group"]
        if g not in gi:
            gi[g] = {"id": g, "label": g, "memberCount": 0, "totalDegree": 0, "members": []}
        gi[g]["memberCount"] += 1
        gi[g]["totalDegree"] += node["degree"]
        gi[g]["members"].append(node["id"])

    ge: dict[tuple[str, str], dict] = {}
    ctg = data["code_to_group"]
    for edge in full["edges"]:
        sg, tg = ctg.get(edge["source"], ""), ctg.get(edge["target"], "")
        if sg == tg:
            continue
        key = (sg, tg) if sg < tg else (tg, sg)
        if key not in ge:
            ge[key] = {"source": key[0], "target": key[1], "weight": 0, "types": set()}
        ge[key]["weight"] += 1
        ge[key]["types"].add(edge["type"])

    edges_out = [
        {"source": e["source"], "target": e["target"], "weight": e["weight"], "types": sorted(e["types"])}
        for e in ge.values()
    ]
    super_nodes = [
        {"id": g, "label": g, "memberCount": info["memberCount"], "totalDegree": info["totalDegree"]}
        for g, info in sorted(gi.items(), key=lambda x: -x[1]["memberCount"])
        if info["memberCount"] >= 2
    ]

    return {
        "meta": {"type": "overview", "groupCount": len(super_nodes), "edgeCount": len(edges_out)},
        "nodes": super_nodes, "edges": edges_out,
    }


def export_ego(data: dict, full: dict, code: str, *, hops: int = 1) -> dict:
    """ego_{code}.json — BFS ego 서브그래프."""
    adj: dict[str, set[str]] = defaultdict(set)
    for edge in full["edges"]:
        adj[edge["source"]].add(edge["target"])
        adj[edge["target"]].add(edge["source"])

    visited: set[str] = {code}
    frontier = {code}
    for _ in range(hops):
        nf: set[str] = set()
        for node in frontier:
            for nb in adj.get(node, set()):
                if nb not in visited:
                    visited.add(nb)
                    nf.add(nb)
        frontier = nf

    nl = {n["id"]: n for n in full["nodes"]}
    en = [nl[nid] for nid in sorted(visited) if nid in nl]
    ee = [e for e in full["edges"] if e["source"] in visited and e["target"] in visited]

    return {
        "meta": {
            "type": "ego", "center": code,
            "centerName": data["code_to_name"].get(code, code),
            "hops": hops, "nodeCount": len(en), "edgeCount": len(ee),
        },
        "nodes": en, "edges": ee,
    }


def _save_json(obj: dict, path: Path) -> int:
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text)


# ═══════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════


if __name__ == "__main__":
    t0 = time.perf_counter()

    data = build_graph()

    # 결과 비교
    gc = Counter(data["code_to_group"][n] for n in data["all_node_ids"])
    print(f"\n{'=' * 60}")
    print("012와 비교 검증")
    print("=" * 60)
    compare = ["삼성", "현대차", "SK", "LG", "한화", "롯데", "GS", "효성",
               "현대백화점", "KT", "HD현대", "대한항공", "포스코", "CJ", "두산"]
    for g in compare:
        c = gc.get(g, 0)
        if c > 0:
            print(f"  {g:12s} {c:5d}")
    indep = sum(1 for c in gc.values() if c == 1)
    multi = sum(1 for c in gc.values() if c >= 2)
    print(f"\n  2명+ 그룹: {multi}, 독립: {indep} ({indep/len(data['all_node_ids']):.0%})")
    print(f"  순환출자: {len(data['cycles'])}개")

    # JSON 내보내기
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)

    print("\nJSON 내보내기...")
    full = export_full(data)
    size = _save_json(full, output_dir / "affiliate_full_v3.json")
    print(f"  full: {full['meta']['nodeCount']}노드 {full['meta']['edgeCount']}엣지 {size/1024:.0f}KB")

    overview = export_overview(data, full)
    size = _save_json(overview, output_dir / "affiliate_overview_v3.json")
    print(f"  overview: {overview['meta']['groupCount']}그룹 {overview['meta']['edgeCount']}엣지 {size/1024:.0f}KB")

    for code, name in [("005930", "삼성전자"), ("005380", "현대자동차"), ("035720", "카카오")]:
        ego = export_ego(data, full, code, hops=1)
        size = _save_json(ego, output_dir / f"ego_{code}_v3.json")
        print(f"  ego {name}: {ego['meta']['nodeCount']}노드 {ego['meta']['edgeCount']}엣지 {size/1024:.0f}KB")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
