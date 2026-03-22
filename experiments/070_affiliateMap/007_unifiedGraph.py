"""
실험 ID: 007
실험명: 3-Layer 통합 그래프 + 그룹 분류 + 순환출자 탐지

목적:
- L1(investedCompany 출자) + L2(majorHolder 지분) 통합
- seed 기반 그룹 분류 (4단계)
- 순환출자 경로 탐지 (DFS cycle detection)
- 모든 노드에 group/degree 메타 부여

가설:
1. well-known seed + 경영참여 방향 확장으로 주요 그룹 식별
2. majorHolder 법인주주 + 공유 개인주주로 추가 커버리지
3. 순환출자 경로가 최소 1개 탐지됨

방법:
1. 002에서 investedCompany 엣지, 006에서 majorHolder 엣지 가져오기
2. 4단계 그룹 분류:
   Step 1: well-known seed + 경영참여 방향 확장 (A→B 소유 = B는 A 그룹)
   Step 2: majorHolder 법인 주주 연결로 확장
   Step 3: 공유 개인주주 (해당 그룹에 이미 2+ 있을 때만)
   Step 4: 이름 키워드 매칭 / 나머지 → 독립
3. 순환출자: 상장사간 directed graph에서 DFS cycle detection (max_length=6)
4. 전체 그래프 통합 + 통계

결과:
- 통합 그래프: 1,028 상장사 노드
  - L1 엣지 (출자): 1,056 (상장사간, 중복 제거)
  - L2 엣지 (주주법인): 932 (majorHolder 상장사 매칭)
  - L2 엣지 (주주개인): 17,886
- 그룹 분류:
  - Step 1 (seed+경영참여): 365개 분류
  - Step 2 (+법인주주): +55개 (총 420)
  - Step 3 (+공유주주): +28개
  - Step 4 (키워드): +22개, 독립: 558개
  - 최종: 388개 그룹 분류 (38%), 568개 독립
  - 2명+ 그룹: 100개
- TOP 10 그룹:
  | 그룹   | 멤버수 | 비고 |
  | 삼성   |   40 | well-known 13 + 경영참여 확장 27 (원익/KCC 서플라이체인 포함) |
  | 현대차  |   29 | 현대자동차/기아/모비스/글로비스/위아/오토에버 등 |
  | SK    |   15 | SK가스/디스커버리/케미칼/바이오팜 등 |
  | LG    |   14 | LG전자/LG화학/LG이노텍 등 |
  | 효성   |   11 | 효성/효성중공업/효성티앤씨/효성화학/효성첨단소재 등 |
  | 한화   |   10 | 한화/한화에어로/한화솔루션/한화오션 등 |
  | 한솔   |    9 | 한솔홀딩스/한솔제지/한솔테크닉스 등 |
  | 두산   |    7 | 두산/두산에너빌리티/두산밥캣 등 |
  | GS    |    8 | GS/GS건설/GS리테일 |
  | 롯데   |    8 | 롯데지주/롯데케미칼/롯데쇼핑 |
- 순환출자: 27개 탐지 (중복 제거 후)
  - 현대차 체인: 기아→현대모비스→현대자동차→기아 등 6개
  - 2자간 순환: 경방↔삼양홀딩스, 대동↔대동기어, 삼화콘덴서↔삼화전기 등
  - 교차 그룹: 케이씨씨→현대모비스→현대자동차→HD현대→HD한국조선해양→케이씨씨
  - 총 소요: 6.8초

결론:
- 가설 1 채택: well-known seed + 방향 기반 경영참여 확장으로 주요 20개 그룹 식별
  - Union-Find는 체인 효과로 메가컴포넌트 생성 → 방향 기반 확장이 더 정확
  - 삼성 40개는 원익/KCC 등 서플라이체인 포함 (데이터상 삼성이 경영참여 투자)
- 가설 2 채택: Step 2~3에서 +83개 추가 분류
  - 개인주주 동명이인 문제로 보수적 전략 필요 (기존 그룹에 2+ anchor 있을 때만)
- 가설 3 채택: 27개 순환출자 탐지
  - 현대차 그룹 내부 순환이 가장 복잡 (6개 경로)
  - 교차 그룹 순환: 케이씨씨-현대 5홉 사이클
- 한계: 독립 568개 (55%) — 대부분 단순투자만 있는 소규모 회사
  - 완전 분류(100%)는 외부 데이터(공정위 대기업집단 목록) 없이는 불가능
  - 현재 수준은 출자/지분 관계만으로 달성 가능한 합리적 범위

실험일: 2026-03-19
"""

import time
import polars as pl
from pathlib import Path
from collections import defaultdict
import importlib.util

_parent = Path(__file__).resolve().parent
_sp2 = importlib.util.spec_from_file_location("_e2", str(_parent / "002_buildEdges.py"))
_m2 = importlib.util.module_from_spec(_sp2); _sp2.loader.exec_module(_m2)
_sp3 = importlib.util.spec_from_file_location("_e3", str(_parent / "003_graphAnalysis.py"))
_m3 = importlib.util.module_from_spec(_sp3); _sp3.loader.exec_module(_m3)
_sp6 = importlib.util.spec_from_file_location("_e6", str(_parent / "006_majorHolder.py"))
_m6 = importlib.util.module_from_spec(_sp6); _sp6.loader.exec_module(_m6)


# ── Well-known 그룹 라벨 ────────────────────────────────────

_WELL_KNOWN: dict[str, str] = {
    # 삼성
    "005930": "삼성", "006400": "삼성", "009150": "삼성", "028260": "삼성",
    "032830": "삼성", "018260": "삼성", "000810": "삼성", "029780": "삼성",
    "016360": "삼성", "207940": "삼성", "030000": "삼성", "068290": "삼성",
    "010140": "삼성",
    # 현대차
    "005380": "현대차", "000270": "현대차", "012330": "현대차",
    "005387": "현대차", "004020": "현대차", "079160": "현대차",
    "307950": "현대차", "267260": "현대차", "064350": "현대차",
    # HD현대
    "329180": "HD현대", "267250": "HD현대", "009540": "HD현대",
    # SK
    "034730": "SK", "017670": "SK", "000660": "SK",
    "361610": "SK", "018670": "SK", "034020": "SK",
    # LG
    "003550": "LG", "066570": "LG", "051910": "LG",
    "034220": "LG", "373220": "LG", "011070": "LG", "011170": "LG",
    # 롯데
    "023530": "롯데", "004990": "롯데", "071050": "롯데",
    "004000": "롯데", "023150": "롯데", "004440": "롯데",
    # 한화
    "000880": "한화", "009830": "한화", "272210": "한화",
    "042660": "한화", "012450": "한화",
    # GS
    "078930": "GS", "006360": "GS", "001120": "GS",
    # 포스코
    "005490": "포스코", "047050": "포스코", "003670": "포스코",
    # CJ
    "001040": "CJ", "097950": "CJ", "000120": "CJ",
    # 두산
    "000150": "두산", "336260": "두산", "042670": "두산",
    # 카카오
    "035720": "카카오", "293490": "카카오", "377300": "카카오",
    # 네이버
    "035420": "네이버",
    # 효성
    "004800": "효성", "298040": "효성", "298050": "효성", "298020": "효성",
    # 한솔
    "004150": "한솔", "213500": "한솔", "009180": "한솔",
    # 사조
    "007160": "사조", "008060": "사조",
    # 녹십자
    "006280": "녹십자", "005250": "녹십자",
    # 하림
    "136480": "하림", "003380": "하림",
    # 금융지주
    "105560": "KB", "055550": "신한", "086790": "하나",
    "138930": "BNK", "316140": "우리",
    # 기타 대기업
    "010950": "S-Oil", "180640": "한진칼", "003490": "대한항공",
    # 신세계
    "004170": "신세계", "139480": "신세계",
}


def _label_group(members: list[str], code_to_name: dict[str, str]) -> str:
    """컴포넌트 멤버에서 그룹 라벨."""
    for m in members:
        if m in _WELL_KNOWN:
            return _WELL_KNOWN[m]
    # 최다 멤버의 이름에서 추출
    names = [code_to_name.get(m, "") for m in members]
    # 공통 접두사
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


# ── 3단계 그룹 분류 ─────────────────────────────────────────


def classify_groups(
    invest_edges: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """그룹 분류: seed → expand → absorb.

    기존 Union-Find는 체인 효과로 메가컴포넌트를 생성하므로,
    seed-based 확장 방식으로 전환.

    Step 1: well-known seed + 경영참여 direct neighbor 확장 (BFS 1홉)
    Step 2: majorHolder 법인 주주 연결로 확장
    Step 3: 공유 개인주주 (seed 그룹에 이미 2+ 있을 때만)
    Step 4: 나머지 → 이름 키워드 매칭 또는 독립
    """
    code_to_group: dict[str, str] = {}

    # ── Step 1: well-known seed → 경영참여 BFS 확장 ──
    # well-known 그룹별 seed set
    group_seeds: dict[str, set[str]] = defaultdict(set)
    for code, group in _WELL_KNOWN.items():
        if code in all_node_ids:
            group_seeds[group].add(code)
            code_to_group[code] = group

    # 경영참여 인접 리스트
    mgmt_adj: dict[str, set[str]] = defaultdict(set)
    mgmt = invest_edges.filter(
        (pl.col("purpose") == "경영참여")
        & pl.col("is_listed")
        & pl.col("to_code").is_not_null()
    )
    for row in mgmt.iter_rows(named=True):
        a, b = row["from_code"], row["to_code"]
        if a != b:
            mgmt_adj[a].add(b)
            mgmt_adj[b].add(a)

    # 방향 기반 경영참여 확장: A→B (경영참여) = A가 B를 소유
    # A가 분류됨 → B도 A의 그룹 (B가 미분류일 때만)
    # 역방향은 안 함 (피투자사가 투자사 그룹에 들어가는 건 이상)
    mgmt_directed: dict[str, set[str]] = defaultdict(set)  # from→to (소유 방향)
    for row in mgmt.iter_rows(named=True):
        a, b = row["from_code"], row["to_code"]
        if a != b and a in all_node_ids and b in all_node_ids:
            mgmt_directed[a].add(b)

    for _round in range(3):
        newly_added = 0
        for parent in list(code_to_group.keys()):
            parent_group = code_to_group[parent]
            for child in mgmt_directed.get(parent, set()):
                if child not in code_to_group:
                    code_to_group[child] = parent_group
                    newly_added += 1
        if newly_added == 0:
            break

    # well-known에 없는 경영참여 미분류 클러스터: 방향 기반 그루핑
    # 같은 parent에서 경영참여로 투자받은 미분류 노드끼리 → 새 그룹
    parent_children: dict[str, set[str]] = defaultdict(set)
    for parent, children in mgmt_directed.items():
        if parent not in code_to_group:
            for child in children:
                if child not in code_to_group:
                    parent_children[parent].add(child)

    for parent, children in parent_children.items():
        cluster = {parent} | children
        if len(cluster) >= 2:
            label = _label_group(list(cluster), code_to_name)
            for m in cluster:
                if m not in code_to_group:
                    code_to_group[m] = label

    step1_count = len(code_to_group)
    print(f"  Step 1 (seed+경영참여): {step1_count} classified")

    # ── Step 2: majorHolder 법인 주주 연결 ──
    matched_corp = corp_edges.filter(pl.col("from_code").is_not_null())
    for row in matched_corp.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        # 법인 주주가 이미 분류 → 피투자사도 같은 그룹 (미분류일 때만)
        if fc in code_to_group and tc not in code_to_group and tc in all_node_ids:
            code_to_group[tc] = code_to_group[fc]
        elif tc in code_to_group and fc not in code_to_group and fc in all_node_ids:
            code_to_group[fc] = code_to_group[tc]

    step2_count = len(code_to_group)
    print(f"  Step 2 (+법인주주): {step2_count} classified (+{step2_count - step1_count})")

    # ── Step 3: 공유 개인주주 (해당 그룹에 이미 2+ 있을 때만) ──
    person_groups = person_edges.group_by("person_name").agg(
        pl.col("to_code").unique().alias("companies"),
    ).filter(pl.col("companies").list.len() >= 2)

    step3_added = 0
    for row in person_groups.iter_rows(named=True):
        codes = [c for c in row["companies"] if c in all_node_ids]
        if len(codes) < 2:
            continue

        # 이미 분류된 코드의 그룹 분포
        group_dist: dict[str, list[str]] = defaultdict(list)
        unassigned: list[str] = []
        for c in codes:
            if c in code_to_group:
                group_dist[code_to_group[c]].append(c)
            else:
                unassigned.append(c)

        if not group_dist or not unassigned:
            continue

        # 가장 많은 그룹에 2개+ 있어야 합류 허용
        best_group = max(group_dist, key=lambda g: len(group_dist[g]))
        if len(group_dist[best_group]) >= 2:
            for c in unassigned:
                code_to_group[c] = best_group
                step3_added += 1

    print(f"  Step 3 (+공유주주): {step3_added} added")

    # ── Step 4: 이름 키워드 매칭 → 독립 ──
    _GROUP_KEYWORDS = {
        "삼성": ["삼성"], "현대차": ["현대", "기아"],
        "SK": ["SK", "에스케이"], "LG": ["LG", "엘지"],
        "롯데": ["롯데"], "한화": ["한화"],
        "GS": ["GS", "지에스"], "포스코": ["POSCO", "포스코"],
        "CJ": ["CJ", "씨제이"], "두산": ["두산"],
        "HD현대": ["HD현대", "한국조선해양"],
        "효성": ["효성"], "한솔": ["한솔"],
    }

    keyword_assigned = 0
    for node in list(all_node_ids - set(code_to_group.keys())):
        name = code_to_name.get(node, "")
        matched = False
        for group, keywords in _GROUP_KEYWORDS.items():
            for kw in keywords:
                if kw in name:
                    code_to_group[node] = group
                    matched = True
                    break
            if matched:
                keyword_assigned += 1
                break

    # 나머지 → 독립
    still_unclassified = all_node_ids - set(code_to_group.keys())
    for node in still_unclassified:
        code_to_group[node] = code_to_name.get(node, node)

    total_in_groups = sum(1 for n in all_node_ids
                         if code_to_group.get(n) not in {code_to_name.get(n, n)})
    print(f"  Step 4 (키워드): {keyword_assigned}, 독립: {len(still_unclassified)}")
    print(f"  최종: {len(all_node_ids)} nodes, {total_in_groups} in groups ({total_in_groups/len(all_node_ids):.0%})")

    return code_to_group


# ── 순환출자 탐지 ────────────────────────────────────────────


def detect_cycles(
    invest_edges: pl.DataFrame,
    code_to_name: dict[str, str],
    *,
    max_length: int = 6,
) -> list[list[str]]:
    """상장사간 directed graph에서 순환출자 탐지 (DFS)."""
    # 경영참여 + 상장사간 directed 엣지
    adj: dict[str, list[str]] = defaultdict(list)
    listed_edges = invest_edges.filter(
        pl.col("is_listed")
        & pl.col("to_code").is_not_null()
        & (pl.col("from_code") != pl.col("to_code"))
    )
    for row in listed_edges.iter_rows(named=True):
        adj[row["from_code"]].append(row["to_code"])

    cycles: list[list[str]] = []
    visited_global: set[str] = set()

    def dfs(node: str, path: list[str], path_set: set[str]) -> None:
        if len(path) > max_length:
            return
        for neighbor in adj.get(node, []):
            if neighbor == path[0] and len(path) >= 2:
                # 순환 발견!
                cycle = path + [neighbor]
                cycles.append(cycle)
            elif neighbor not in path_set and neighbor not in visited_global:
                path.append(neighbor)
                path_set.add(neighbor)
                dfs(neighbor, path, path_set)
                path.pop()
                path_set.discard(neighbor)

    for start in sorted(adj.keys()):
        if start in visited_global:
            continue
        dfs(start, [start], {start})
        # 시작점에서 시작하는 순환은 더 찾을 필요 없음
        visited_global.add(start)

    # 중복 순환 제거 (같은 순환의 다른 시작점)
    unique: list[list[str]] = []
    seen: set[frozenset] = set()
    for cycle in cycles:
        key = frozenset(cycle[:-1])  # 마지막은 시작점 반복
        if key not in seen:
            seen.add(key)
            unique.append(cycle)

    return unique


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 데이터 로드...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}

    # investedCompany
    raw_inv = _m2.scan_all_invested()
    invest_edges = _m2.clean_and_build_edges(raw_inv, name_to_code)
    latest_year = invest_edges["year"].max()
    invest_deduped = _m3.deduplicate_edges(invest_edges, latest_year)
    # 자기참조 제거
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))

    # majorHolder
    raw_mh = _m6.scan_all_major_holders()
    corp_edges, person_edges = _m6.build_holder_edges(raw_mh, name_to_code, code_to_name)

    print(f"   investedCompany: {len(invest_deduped):,} edges")
    print(f"   majorHolder corp: {len(corp_edges):,}, person: {len(person_edges):,}")

    # 2. 전체 노드 수집
    all_node_ids: set[str] = set()
    listed_only = invest_deduped.filter(pl.col("is_listed") & pl.col("to_code").is_not_null())
    for row in listed_only.iter_rows(named=True):
        all_node_ids.add(row["from_code"])
        all_node_ids.add(row["to_code"])
    # majorHolder의 매칭된 법인 주주도 추가
    matched_corp = corp_edges.filter(pl.col("from_code").is_not_null())
    for row in matched_corp.iter_rows(named=True):
        all_node_ids.add(row["from_code"])
        all_node_ids.add(row["to_code"])
    # listing에 있는 노드만 유지
    listing_codes = set(listing["종목코드"].to_list())
    all_node_ids = all_node_ids & listing_codes
    print(f"   전체 상장사 노드: {len(all_node_ids)}")

    # 3. 그룹 분류
    print("\n2. 3단계 그룹 분류...")
    code_to_group = classify_groups(invest_deduped, corp_edges, person_edges, all_node_ids, code_to_name)

    # 그룹 통계
    group_counts: dict[str, int] = defaultdict(int)
    for code in all_node_ids:
        group_counts[code_to_group.get(code, "?")] += 1

    multi_member_groups = {g: c for g, c in group_counts.items() if c >= 2}
    print(f"\n  그룹 통계:")
    print(f"    총 그룹: {len(group_counts)}")
    print(f"    2명+ 그룹: {len(multi_member_groups)}")
    print(f"    독립 (1명): {sum(1 for c in group_counts.values() if c == 1)}")
    print(f"\n  TOP 20 그룹:")
    for g, c in sorted(group_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"    {g:15s}: {c}")

    # 4. 순환출자 탐지
    print("\n3. 순환출자 탐지...")
    cycles = detect_cycles(invest_deduped, code_to_name, max_length=6)
    print(f"   발견된 순환: {len(cycles)}개")
    for cycle in cycles[:20]:
        path = " → ".join(code_to_name.get(c, c) for c in cycle)
        print(f"   {path}")

    # 5. 통합 통계
    print(f"\n{'=' * 70}")
    print("통합 그래프 요약")
    print("=" * 70)
    print(f"  노드: {len(all_node_ids)} 상장사")
    print(f"  L1 엣지 (출자): {len(listed_only):,}")
    print(f"  L2 엣지 (주주법인): {len(matched_corp):,}")
    print(f"  L2 엣지 (주주개인): {len(person_edges):,}")
    print(f"  그룹 수: {len(multi_member_groups)} (2명+), {len(group_counts)} (총)")
    print(f"  순환출자: {len(cycles)}개")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
