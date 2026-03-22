"""
실험 ID: 010
실험명: docs 계열회사 현황에서 공식 그룹 분류 추출

목적:
- 283개 docs parquet의 "계열회사 현황(상세)" section에서 그룹명 + 계열사 목록 파싱
- 공정위 지정 대기업집단 = 사업보고서에 명시된 그룹 → 정답지
- well-known dict 80개 수작업 대신 데이터 기반 그룹 분류 달성
- 목표: 그룹 분류 정확도 90%+

가설:
1. "XXX그룹에는 N개의 국내 계열회사" 패턴으로 그룹명 추출 가능
2. 테이블에서 회사명 → listing 매칭으로 상장사 그룹 배정 가능
3. 283개 종목에서 추출하면 주요 대기업집단 대부분 커버

방법:
1. 전종목 docs parquet 스캔 → "계열회사 현황" section 추출
2. 텍스트에서 그룹명 파싱 (regex: "XXX그룹" / "XXX계열")
3. 테이블에서 계열사 목록 파싱 (회사명 컬럼)
4. 상장사 매칭 → code_to_group 딕셔너리 생성
5. 007 결과와 비교, 정확도 검증

결과:
- 283개 docs parquet 전수 스캔, 6.0초
- 그룹명 텍스트 추출: 2/283 (1%) — 대부분 "XXX그룹" 표현 없이 바로 테이블
- 법인등록번호 기반 회사명 추출: 기아 146개, SK하이닉스 403개, 삼성화재 126개 등
- 클러스터링 (상장사 3개+ 겹침): 157개 상장사 매핑 (6%)
- 주요 그룹 (well-known 라벨 기반):
  | 그룹 | 상장사 수 | 정확도 |
  | SK | 21 | 정확 (SKC, SK가스, SK디스커버리 등) |
  | 삼성 | 15 | 정확 (원익/KCC 미포함!) |
  | 현대차 | 12 | 정확 (기아, 현대건설, 현대제철 등) |
  | 한화 | 10 | 정확 |
  | 롯데 | 10 | 정확 |
  | 효성 | 10 | 일부 오포함 (갤럭시아 등) |
  | 한진칼 | 8 | 정확 |
  | HD현대 | 7 | 정확 |
  | 두산 | 7 | 정확 |
  | 카카오 | 7 | 정확 |
  | 포스코 | 6 | 정확 |
- 삼성 검증: 15개 상장사 — 정확 (삼성전자~호텔신라, 원익/KCC 미포함)
- 문제:
  - "지누스" 13개에 현대지에프홀딩스 섞임 → 테이블 파싱 노이즈
  - LG 단독 → docs 283개 중 LG계열 문서가 1개뿐
  - docs 283개 한계 → report 982개 활용하면 커버리지 증가 가능

결론:
- 가설 1 부분 채택: 텍스트에서 그룹명 추출은 1%로 실패, 대부분 테이블 직행
- 가설 2 채택: 법인등록번호 기반 회사명 추출 + listing 매칭 작동
- 가설 3 채택: 클러스터링으로 주요 10개+ 대기업집단 식별
- **핵심 가치: 삼성 15개가 원익/KCC 없이 정확** — 007의 40개 대비 훨씬 정확
- 이 결과를 007 출자 관계 분류의 ground truth로 사용하면 정확도 대폭 개선
- docs 283개 한계는 있으나, 대기업집단은 대부분 커버

실험일: 2026-03-19
"""

import importlib.util
import re
import time
from collections import defaultdict
from pathlib import Path

import polars as pl

from dartlab.core.dataLoader import _dataDir

_parent = Path(__file__).resolve().parent
_sp2 = importlib.util.spec_from_file_location("_e2", str(_parent / "002_buildEdges.py"))
_m2 = importlib.util.module_from_spec(_sp2); _sp2.loader.exec_module(_m2)


def _extract_group_name(text: str) -> str | None:
    """텍스트에서 그룹명 추출.

    패턴: "XXX그룹에는", "XXX그룹의", "XXX계열"
    """
    # "XX그룹에는 N개" 패턴
    m = re.search(r"([가-힣A-Za-z]+)그룹에는\s*(?:전년말과\s*동일한\s*)?(\d+)개", text)
    if m:
        return m.group(1)

    # "XX그룹의 국내" 패턴
    m = re.search(r"([가-힣A-Za-z]+)그룹의\s*국내", text)
    if m:
        return m.group(1)

    # "XX그룹 소속" 패턴
    m = re.search(r"([가-힣A-Za-z]+)그룹\s*소속", text)
    if m:
        return m.group(1)

    # "XX계열에는" 패턴
    m = re.search(r"([가-힣A-Za-z]+)계열에는", text)
    if m:
        return m.group(1)

    return None


def _extract_companies_from_table(text: str) -> list[str]:
    """markdown 테이블에서 회사명 추출.

    전략: 법인등록번호(숫자-숫자 or 13자리 숫자)가 있는 행에서 회사명 추출.
    ㈜ 있는 것도, 없는 것도 ("현대자동차") 모두 잡음.
    """
    companies = []
    _CORP_RE = re.compile(r"[\(（]주[\)）]|㈜|주식회사")
    _REGNUM_RE = re.compile(r"\d{6}-?\d{7}")  # 법인등록번호
    _NOISE = {"상장", "비상장", "합계", "소계", "---", "기업명", "회사수",
              "법인등록번호", "상장여부", "비고", "단위", "기준일", "☞", "본문"}

    for line in text.split("\n"):
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]

        # 법인등록번호가 있는 행 → 회사 행
        has_regnum = any(_REGNUM_RE.search(c) for c in cells)
        if not has_regnum:
            continue

        for cell in cells:
            # 숫자만, 날짜, 법인등록번호, 잡음 제외
            if _REGNUM_RE.search(cell):
                continue
            if re.match(r"^[\d,.\-\s]+$", cell):
                continue
            if cell in _NOISE or len(cell) < 2:
                continue
            # 회사명 후보
            companies.append(cell)

    # ㈜ 패턴으로도 추가 (법인등록번호 없는 간략 테이블)
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


def _normalize_corp_name(name: str) -> str:
    """회사명 정규화: (주), ㈜, 주식회사 제거."""
    name = re.sub(r"[\(（]주[\)）]", "", name)
    name = name.replace("㈜", "").replace("주식회사", "")
    name = name.strip()
    return name


def scan_all_affiliate_sections() -> list[dict]:
    """전종목 계열회사 현황 스캔."""
    docs_dir = Path(_dataDir("docs"))
    parquet_files = sorted(docs_dir.glob("*.parquet"))

    results = []
    for pf in parquet_files:
        code = pf.stem
        try:
            df = pl.read_parquet(str(pf))
        except Exception:
            continue

        if "section_title" not in df.columns or "section_content" not in df.columns:
            continue

        # 최신 연도의 "계열회사 현황" section
        affiliate = df.filter(
            pl.col("section_title").str.contains("계열회사 현황")
            | pl.col("section_title").str.contains("계열회사에 관한 사항")
        )

        if len(affiliate) == 0:
            continue

        # 최신 연도
        if "year" in affiliate.columns:
            latest_year = affiliate["year"].max()
            affiliate = affiliate.filter(pl.col("year") == latest_year)

        # 모든 section_content 합치기
        contents = affiliate["section_content"].to_list()
        full_text = "\n".join(c for c in contents if c)

        if not full_text:
            continue

        group_name = _extract_group_name(full_text)
        companies = _extract_companies_from_table(full_text)

        results.append({
            "code": code,
            "group_name": group_name,
            "company_count": len(companies),
            "companies": companies,
            "text_length": len(full_text),
        })

    return results


def build_group_mapping(
    results: list[dict],
    name_to_code: dict[str, str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """계열회사 현황에서 code_to_group 매핑 구축.

    전략:
    1. 각 종목의 계열사 테이블 → 상장사 코드 set으로 변환
    2. 같은 계열사 set을 공유하는 종목들 → 같은 그룹
    3. 그룹명: 텍스트에서 추출 or 멤버 이름 공통 접두사
    """
    # 그룹명 정규화
    _GROUP_ALIASES = {
        "에스케이": "SK", "엘지": "LG", "지에스": "GS",
        "씨제이": "CJ", "에이치디현대": "HD현대",
        "케이씨씨": "KCC",
    }

    # Step 1: 각 종목의 계열사 코드 set 구축
    code_to_affiliate_set: dict[str, set[str]] = {}
    code_to_text_group: dict[str, str | None] = {}

    for r in results:
        matched_codes: set[str] = set()
        for comp_name in r["companies"]:
            norm = _normalize_corp_name(comp_name)
            code = name_to_code.get(comp_name) or name_to_code.get(norm)
            if code:
                matched_codes.add(code)

        # 자기 자신도 포함
        matched_codes.add(r["code"])
        code_to_affiliate_set[r["code"]] = matched_codes

        group = r["group_name"]
        if group:
            group = _GROUP_ALIASES.get(group, group)
        code_to_text_group[r["code"]] = group

    # Step 2: 겹치는 set끼리 Union-Find로 클러스터링
    # 같은 계열사 목록(상장사 3개+ 겹침)을 공유하는 종목 = 같은 그룹
    import importlib.util as _iu
    _sp3 = _iu.spec_from_file_location("_e3", str(_parent / "003_graphAnalysis.py"))
    _m3 = _iu.module_from_spec(_sp3); _sp3.loader.exec_module(_m3)

    uf = _m3.UnionFind()
    codes_list = list(code_to_affiliate_set.keys())

    for i in range(len(codes_list)):
        for j in range(i + 1, len(codes_list)):
            ci, cj = codes_list[i], codes_list[j]
            overlap = code_to_affiliate_set[ci] & code_to_affiliate_set[cj]
            if len(overlap) >= 3:  # 상장사 3개+ 공유
                uf.union(ci, cj)

    # Step 3: 클러스터별 그룹명 + 멤버 확정
    code_to_group: dict[str, str] = {}
    comps = uf.components()

    for root, members in comps.items():
        # 이 클러스터의 모든 계열사 합집합
        all_affiliates: set[str] = set()
        for m in members:
            all_affiliates.update(code_to_affiliate_set.get(m, set()))

        if len(all_affiliates) < 2:
            continue

        # 그룹명 결정
        # 1. well-known 라벨 우선
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

        group_name = None
        for code in all_affiliates:
            if code in _WELL_KNOWN_LABELS:
                group_name = _WELL_KNOWN_LABELS[code]
                break

        # 2. 텍스트에서 추출된 것
        if not group_name:
            for m in members:
                g = code_to_text_group.get(m)
                if g:
                    group_name = g
                    break

        # 3. 공통 접두사
        if not group_name:
            names = sorted(code_to_name.get(c, "") for c in all_affiliates if c in code_to_name)
            if len(names) >= 2:
                prefix = names[0]
                for n in names[1:]:
                    while prefix and not n.startswith(prefix):
                        prefix = prefix[:-1]
                if len(prefix) >= 2:
                    group_name = prefix.rstrip()

        # 4. 가장 큰 회사 이름
        if not group_name:
            group_name = code_to_name.get(members[0], members[0])

        for code in all_affiliates:
            code_to_group[code] = group_name

    return code_to_group


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 상장사 목록 로드...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}
    listing_codes = set(listing["종목코드"].to_list())

    print("2. 전종목 계열회사 현황 스캔...")
    results = scan_all_affiliate_sections()
    print(f"   스캔 완료: {len(results)}개 종목")

    # 그룹명 추출 성공률
    with_group = [r for r in results if r["group_name"]]
    without_group = [r for r in results if not r["group_name"]]
    print(f"   그룹명 추출 성공: {len(with_group)}/{len(results)} ({len(with_group)/len(results):.0%})")

    # 그룹별 통계
    group_counts: dict[str, int] = defaultdict(int)
    for r in with_group:
        group_counts[r["group_name"]] += 1

    print(f"\n   발견된 그룹 ({len(group_counts)}개):")
    for g, c in sorted(group_counts.items(), key=lambda x: -x[1])[:30]:
        print(f"     {g}: {c}개 종목이 보고")

    # 그룹명 없는 종목 샘플
    print(f"\n   그룹명 미추출 종목 ({len(without_group)}개) 샘플:")
    for r in without_group[:10]:
        print(f"     {r['code']} ({code_to_name.get(r['code'], '?')}): text {r['text_length']}자, companies {r['company_count']}개")

    print("\n3. 그룹 매핑 구축...")
    code_to_group = build_group_mapping(results, name_to_code, code_to_name)
    print(f"   매핑된 상장사: {len(code_to_group)}")

    # listing 기준 커버리지
    listed_mapped = {c for c in code_to_group if c in listing_codes}
    print(f"   상장사 중 그룹 배정: {len(listed_mapped)} / {len(listing_codes)} ({len(listed_mapped)/len(listing_codes):.0%})")

    # 그룹별 상장사 수
    group_listed: dict[str, list[str]] = defaultdict(list)
    for code, group in code_to_group.items():
        if code in listing_codes:
            group_listed[group].append(code)

    print(f"\n   그룹별 상장사 (TOP 20):")
    for g, members in sorted(group_listed.items(), key=lambda x: -len(x[1]))[:20]:
        names = [code_to_name.get(c, c) for c in sorted(members)]
        print(f"     {g} ({len(members)}): {', '.join(names[:5])}{'...' if len(names) > 5 else ''}")

    # 삼성 검증
    if "삼성" in group_listed:
        samsung_codes = set(group_listed["삼성"])
        samsung_names = sorted(code_to_name.get(c, c) for c in samsung_codes)
        print(f"\n   삼성 상장사 ({len(samsung_codes)}개):")
        for n in samsung_names:
            print(f"     {n}")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
