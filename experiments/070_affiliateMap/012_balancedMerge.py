"""
실험 ID: 012
실험명: 균형 잡힌 docs+well-known merge (독립 감소 + 정확도 유지)

목적:
- 011의 docs 제약으로 현대해상/한화생명 등이 독립 → 해결
- well-known 확대판을 docs와 동일 우선순위로 lock
- docs 있는 그룹: docs + well-known lock → 경영참여 확장은 이 그룹으로 제한
- docs 없는 그룹: well-known seed + 자유 확장

가설:
1. well-known 확대 + docs lock → 독립 55%→45% 이하
2. 삼성 그룹 17~20개 유지 (공급체인 재유입 방지)
3. 현대해상→현대차, 한화생명→한화 등 정당한 분류 복원

방법:
1. docs ground truth lock
2. well-known 확대판도 lock (docs와 동일 우선순위)
3. 경영참여 확장: docs 있는 그룹은 멤버 제한, 없는 그룹은 자유 확장
4. majorHolder/공유주주/키워드도 동일 원칙

결과:
- Phase 0+1 (docs+well-known lock): 205 (159 docs + 46 well-known), known 그룹 32개
- Phase 2 (경영참여 확장): +377, Phase 3 (법인주주 20%+): +99
- Phase 4 (공유주주): +81, Phase 5 (키워드): +16, 독립: 842

  주요 그룹:
  | 그룹 | 011 | 012 | 007 |
  | 삼성 | 17 | 21 | 55 |
  | 현대차 | 13 | 18 | 22 |
  | SK | 20 | 21 | 17 |
  | LG | 12 | 10 | 14 |
  | 한화 | 9 | 12 | 12 |
  | 현대백화점 | 13 | 13 | 0 |
  | KT | 0 | 9 | 0 |
  | 다우 | 0 | 8 | 0 |
  | HLB | 0 | 9 | 0 |

  독립: 007=808(50%), 011=885(55%), 012=854(53%)
  2명+ 그룹: 007=178, 011=182, 012=185

결론:
- 가설 1 부분 채택: 독립 55%→53% (목표 45% 미달, 하지만 정확도 유지하면서 감소)
- 가설 2 채택: 삼성 21개 (원익/솔브레인 제거, 레인보우로보틱스 35%는 정당)
- 가설 3 채택: 현대해상/한화생명/한국타이어 등 정당한 분류 복원
- **011 대비 개선**: 현대차 13→18, 한화 9→12, KT/다우/HLB 신규 그룹 추가
- **핵심 설계**: known 그룹은 경영참여 확장 차단 + majorHolder 20%+ 허용
  - 삼성→원익(경영참여) 차단, 삼성→레인보우(35% majorHolder) 허용
- 독립 53%는 소규모 회사 한계 — 외부 데이터 없이 달성 가능한 합리적 범위
- 이 분류를 008 JSON export에 적용

실험일: 2026-03-19
"""

import importlib.util
import time
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

_parent = Path(__file__).resolve().parent

_sp2 = importlib.util.spec_from_file_location("_e2", str(_parent / "002_buildEdges.py"))
_m2 = importlib.util.module_from_spec(_sp2); _sp2.loader.exec_module(_m2)
_sp3 = importlib.util.spec_from_file_location("_e3", str(_parent / "003_graphAnalysis.py"))
_m3 = importlib.util.module_from_spec(_sp3); _sp3.loader.exec_module(_m3)
_sp6 = importlib.util.spec_from_file_location("_e6", str(_parent / "006_majorHolder.py"))
_m6 = importlib.util.module_from_spec(_sp6); _sp6.loader.exec_module(_m6)
_sp7 = importlib.util.spec_from_file_location("_e7", str(_parent / "007_unifiedGraph.py"))
_m7 = importlib.util.module_from_spec(_sp7); _sp7.loader.exec_module(_m7)
_sp10 = importlib.util.spec_from_file_location("_e10", str(_parent / "010_affiliateFromDocs.py"))
_m10 = importlib.util.module_from_spec(_sp10); _sp10.loader.exec_module(_m10)


# ── well-known 확대판 ────────────────────────────────────────
_WELL_KNOWN_EXT: dict[str, str] = {
    **_m7._WELL_KNOWN,
    # 현대차 보충 (docs에 없는 주요 멤버)
    "001450": "현대차",   # 현대해상
    "086280": "현대차",   # 현대글로비스
    "004560": "현대차",   # 현대비앤지스틸
    "011210": "현대차",   # 현대위아
    "000720": "현대차",   # 현대건설
    "214320": "현대차",   # 이노션
    "001500": "현대차",   # 현대차증권
    # 한화 보충
    "088350": "한화",     # 한화생명
    # 한진칼/대한항공
    "272450": "대한항공",  # 진에어
    "020560": "대한항공",  # 아시아나항공
    "005430": "대한항공",  # 한국공항
    "002320": "대한항공",  # 한진
    "267850": "대한항공",  # 아시아나IDT
    "298690": "대한항공",  # 에어부산
    # 현대백화점
    "069960": "현대백화점", "005440": "현대백화점", "057050": "현대백화점",
    "079430": "현대백화점", "020000": "현대백화점",
    # KT
    "030200": "KT",
    # 한국타이어
    "161390": "한국타이어",
    # 종근당
    "001630": "종근당", "185750": "종근당", "063160": "종근당",
    # 다우
    "023590": "다우", "175250": "다우",
    # 웅진
    "016880": "웅진", "095720": "웅진",
    # LS
    "006260": "LS", "010120": "LS",
    # 에코프로
    "086520": "에코프로", "247540": "에코프로", "383310": "에코프로",
    # 셀트리온
    "068270": "셀트리온", "091990": "셀트리온", "393890": "셀트리온",
    # HLB
    "028300": "HLB", "024850": "HLB", "067630": "HLB",
}


def classify_balanced(
    invest_edges: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
    docs_ground_truth: dict[str, str],
) -> dict[str, str]:
    """균형 merge.

    핵심:
    - docs + well-known 확대 = locked (라벨 고정)
    - "known 그룹" = docs에 있거나 well-known에 3개+ 있는 그룹
    - known 그룹 → 경영참여 확장 시 locked 멤버만 허용 (공급체인 차단)
    - unknown 그룹 → 자유 확장
    """
    code_to_group: dict[str, str] = {}
    locked: set[str] = set()

    # ── Phase 0: docs ground truth lock ──
    for code, group in docs_ground_truth.items():
        if code in all_node_ids:
            code_to_group[code] = group
            locked.add(code)
    phase0 = len(locked)

    # ── Phase 1: well-known 확대 lock ──
    for code, group in _WELL_KNOWN_EXT.items():
        if code in all_node_ids and code not in locked:
            code_to_group[code] = group
            locked.add(code)
    phase1 = len(locked) - phase0
    print(f"  Phase 0+1 (docs+well-known lock): {len(locked)} ({phase0} docs + {phase1} well-known)")

    # "known 그룹" = locked에 2명+ 있는 그룹
    known_groups: dict[str, set[str]] = defaultdict(set)
    for code in locked:
        known_groups[code_to_group[code]].add(code)
    known_group_names = {g for g, members in known_groups.items() if len(members) >= 2}
    print(f"  known 그룹: {len(known_group_names)}개")

    # ── Phase 2: 경영참여 방향 확장 ──
    mgmt = invest_edges.filter(
        (pl.col("purpose") == "경영참여")
        & pl.col("is_listed")
        & pl.col("to_code").is_not_null()
    )
    mgmt_directed: dict[str, set[str]] = defaultdict(set)
    for row in mgmt.iter_rows(named=True):
        a, b = row["from_code"], row["to_code"]
        if a != b and a in all_node_ids and b in all_node_ids:
            mgmt_directed[a].add(b)

    # known 그룹에서 나가는 경영참여: child는 그 그룹이 아닌 독자 클러스터로
    # unknown 그룹에서 나가는 경영참여: child는 parent의 그룹으로 (기존 방식)
    for _round in range(3):
        newly_added = 0
        for parent in list(code_to_group.keys()):
            parent_group = code_to_group[parent]
            for child in mgmt_directed.get(parent, set()):
                if child in locked or child in code_to_group:
                    continue
                if parent_group in known_group_names:
                    # known 그룹 → child는 별도 클러스터 후보 (여기서 건드리지 않음)
                    continue
                code_to_group[child] = parent_group
                newly_added += 1
        if newly_added == 0:
            break

    # 미분류 경영참여 클러스터 (known의 child 포함)
    parent_children: dict[str, set[str]] = defaultdict(set)
    for parent, children in mgmt_directed.items():
        if parent not in code_to_group:
            for child in children:
                if child not in code_to_group:
                    parent_children[parent].add(child)

    # known 그룹이 경영참여로 소유하는 미분류 child끼리도 클러스터 가능
    for parent in list(code_to_group.keys()):
        if code_to_group[parent] in known_group_names:
            unclassified_children = [
                c for c in mgmt_directed.get(parent, set())
                if c not in code_to_group and c not in locked
            ]
            if len(unclassified_children) >= 2:
                # 이 children끼리 mutual 경영참여가 있으면 클러스터
                for uc in unclassified_children:
                    if uc not in parent_children:
                        parent_children[uc] = set()
                    for uc2 in unclassified_children:
                        if uc != uc2 and uc2 in mgmt_directed.get(uc, set()):
                            parent_children[uc].add(uc2)

    for parent, children in parent_children.items():
        cluster = {parent} | children
        if len(cluster) >= 2:
            label = _m7._label_group(list(cluster), code_to_name)
            for m in cluster:
                if m not in code_to_group:
                    code_to_group[m] = label

    phase2 = len(code_to_group) - len(locked)
    print(f"  Phase 2 (경영참여 확장): +{phase2}")

    # ── Phase 3: majorHolder 법인 주주 ──
    # known 그룹: ownership >= 20%일 때만 합류 (단순 재무투자 차단)
    # unknown 그룹: 제한 없음
    matched_corp = corp_edges.filter(pl.col("from_code").is_not_null())
    phase3 = 0
    for row in matched_corp.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        pct = row.get("ownership_pct") or 0
        if fc in code_to_group and tc not in code_to_group and tc in all_node_ids and tc not in locked:
            parent_group = code_to_group[fc]
            if parent_group in known_group_names and pct < 20:
                continue
            code_to_group[tc] = parent_group
            phase3 += 1
        elif tc in code_to_group and fc not in code_to_group and fc in all_node_ids and fc not in locked:
            parent_group = code_to_group[tc]
            if parent_group in known_group_names and pct < 20:
                continue
            code_to_group[fc] = parent_group
            phase3 += 1

    print(f"  Phase 3 (법인주주): +{phase3}")

    # ── Phase 4: 공유 개인주주 (known 그룹도 허용) ──
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

        best_group = max(group_dist, key=lambda g: len(group_dist[g]))
        if len(group_dist[best_group]) >= 2:
            for c in unassigned:
                code_to_group[c] = best_group
                phase4 += 1

    print(f"  Phase 4 (공유주주): +{phase4}")

    # ── Phase 5: 이름 키워드 + 독립 ──
    _GROUP_KEYWORDS = {
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

    phase5_kw = 0
    for node in list(all_node_ids - set(code_to_group.keys())):
        name = code_to_name.get(node, "")
        for group, keywords in _GROUP_KEYWORDS.items():
            matched = False
            for kw in keywords:
                if kw in name:
                    code_to_group[node] = group
                    phase5_kw += 1
                    matched = True
                    break
            if matched:
                break

    still_unclassified = all_node_ids - set(code_to_group.keys())
    for node in still_unclassified:
        code_to_group[node] = code_to_name.get(node, node)

    print(f"  Phase 5 (키워드): +{phase5_kw}, 독립: {len(still_unclassified)}")

    group_counts = Counter(code_to_group[n] for n in all_node_ids)
    real_indep = sum(1 for c in group_counts.values() if c == 1)
    print(f"  최종: {len(all_node_ids)} nodes, 독립 {real_indep} ({real_indep/len(all_node_ids):.0%})")

    return code_to_group


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 데이터 로드...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}
    listing_codes = set(listing["종목코드"].to_list())

    raw_inv = _m2.scan_all_invested()
    invest_edges = _m2.clean_and_build_edges(raw_inv, name_to_code)
    latest_year = invest_edges["year"].max()
    invest_deduped = _m3.deduplicate_edges(invest_edges, latest_year)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))

    raw_mh = _m6.scan_all_major_holders()
    corp_edges, person_edges = _m6.build_holder_edges(raw_mh, name_to_code, code_to_name)

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
    print(f"   전체 상장사 노드: {len(all_node_ids)}")

    print("\n2. docs ground truth...")
    docs_results = _m10.scan_all_affiliate_sections()
    docs_gt = _m10.build_group_mapping(docs_results, name_to_code, code_to_name)

    print("\n3. 균형 분류...")
    code_to_group = classify_balanced(
        invest_deduped, corp_edges, person_edges,
        all_node_ids, code_to_name, docs_gt,
    )

    # 결과
    group_counts = Counter(code_to_group[n] for n in all_node_ids)
    single = sum(1 for c in group_counts.values() if c == 1)
    multi = sum(1 for c in group_counts.values() if c >= 2)

    print(f"\n{'=' * 70}")
    print("결과")
    print("=" * 70)
    print(f"  2명+ 그룹: {multi}, 독립: {single} ({single/len(all_node_ids):.0%})")

    compare = ["삼성", "현대차", "SK", "LG", "한화", "롯데", "GS", "포스코",
               "CJ", "두산", "HD현대", "카카오", "효성", "한솔", "대한항공",
               "현대백화점", "KT", "네이버", "LS", "종근당", "에코프로", "셀트리온", "HLB", "웅진", "다우", "한국타이어"]

    print(f"\n  {'그룹':12s} {'멤버':>5s}")
    print(f"  {'-' * 20}")
    for g in compare:
        c = group_counts.get(g, 0)
        if c > 0:
            print(f"  {g:12s} {c:5d}")

    # 삼성 상세
    samsung = sorted(n for n in all_node_ids if code_to_group[n] == "삼성")
    print(f"\n  삼성 ({len(samsung)}개):")
    for c in samsung:
        print(f"    {c} {code_to_name.get(c, c)}")

    # 현대차 상세
    hyundai = sorted(n for n in all_node_ids if code_to_group[n] == "현대차")
    print(f"\n  현대차 ({len(hyundai)}개):")
    for c in hyundai:
        print(f"    {c} {code_to_name.get(c, c)}")

    cycles = _m7.detect_cycles(invest_deduped, code_to_name, max_length=6)
    print(f"\n  순환출자: {len(cycles)}개")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
