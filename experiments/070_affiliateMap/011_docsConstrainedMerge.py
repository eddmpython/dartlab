"""
실험 ID: 011
실험명: docs ground truth 우선 그룹 분류 (007+010 merge)

목적:
- 010에서 추출한 docs "계열회사 현황" ground truth가 007 expansion을 제약
- docs가 "삼성=15개사"라고 하면, 007이 추가 확장해도 삼성으로 분류하지 않음
- 정확도 대폭 개선: 삼성 54→15~17, 공급체인 오분류 제거

가설:
1. docs ground truth 우선 적용 → 삼성 멤버수 15~20개로 감소 (54에서)
2. 007 expansion은 docs 미커버 종목에만 적용 → 추가 분류 확보
3. 전체 그룹 수 유지/증가하면서 정확도 향상

방법:
1. 010 docs ground truth 먼저 적용 (code_to_group에 lock)
2. 007 classify_groups 실행하되, docs에서 이미 분류된 종목은 skip
3. 007의 Step 1~4 중 docs locked 종목은 재할당 불가
4. 삼성/현대차/SK 등 주요 그룹 비교

결과:
- 전체 1,620 상장사 노드, docs ground truth 174종목 → 159 locked (상장사)
- docs 그룹 21개 (SK 21, 삼성 17, 현대백화점 13, 현대차 12, 한화 10, 롯데 10, 효성 10 등)
- Phase 0 (docs lock): 159, Phase 1 (well-known): +31, Phase 2 (경영참여): +398
- Phase 3 (법인주주): +73, Phase 4 (공유주주): +91, Phase 5 (키워드+독립): +867

  주요 그룹 비교:
  | 그룹 | 007 단독 | docs제약 | docs원본 | 판정 |
  | 삼성 | 55 | 17 | 17 | 원익/솔브레인/KCC 38개 제거 — 정확 |
  | 현대차 | 22 | 13 | 12 | 오분류 제거 — 정확 |
  | SK | 17 | 20 | 21 | docs가 더 넓게 인식 — 정확 |
  | LG | 14 | 12 | 0 | docs에 LG 없음, well-known만 — 유지 |
  | 두산 | 12 | 7 | 7 | 오분류 5개 제거 — 정확 |
  | 효성 | 16 | 10 | 10 | 오분류 6개 제거 — 정확 |
  | 현대백화점 | 0 | 13 | 13 | 지누스→현대백화점 라벨 수정, 신규 분리 |
  | HD현대 | 5 | 7 | 7 | docs가 더 넓게 인식 — 정확 |

  전체 통계:
  |  | 007 | docs제약 |
  | 2명+ 그룹 | 178 | 181 |
  | 독립 | 809 | 877 |
  | 그룹 분류율 | 50% | 46% |
  | 순환출자 | 85 | 85 |

결론:
- 가설 1 채택: 삼성 55→17, 정확히 docs 원본(17)과 일치
- 가설 2 채택: docs 미커버 종목에 007 expansion 정상 작동 (LG 12, CJ 7, 한솔 9)
- 가설 3 부분 채택: 그룹 수 178→181 증가, 분류율 50%→46% 소폭 감소
  - 분류율 감소는 docs 제약이 오분류를 차단한 결과 → 정확도 우선이므로 수용
- **핵심 성과**: 공급체인 오분류 완전 제거 (삼성 38개, 두산 5개, 효성 6개 등)
- **현대백화점** 그룹 13개 신규 분리 (기존 "지누스" 라벨 오류 수정)
- docs에 없는 그룹(LG, CJ, 한솔)은 기존 007 방식 유지 — 합리적 fallback
- 이 방식을 008 JSON export에 적용하면 최종 데이터 정확도 대폭 향상

실험일: 2026-03-19
"""

import importlib.util
import time
from collections import defaultdict
from pathlib import Path

import polars as pl

_parent = Path(__file__).resolve().parent

# 기존 실험 모듈 로드
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


def classify_with_docs_constraint(
    invest_edges: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
    docs_ground_truth: dict[str, str],
) -> dict[str, str]:
    """docs ground truth 우선 그룹 분류.

    전략:
    1. docs ground truth를 먼저 적용 (locked, 재할당 불가)
    2. 007의 seed+경영참여 확장을 실행하되:
       - docs에서 이미 분류된 종목은 재할당 안 함
       - docs에서 그룹 X에 속한 종목이 경영참여로 Y를 소유해도,
         Y가 docs에서 X에 없으면 X로 분류하지 않음
    3. Step 2~4도 동일 원칙
    """
    code_to_group: dict[str, str] = {}
    locked: set[str] = set()  # docs에서 분류된 종목 (재할당 불가)

    # docs ground truth에 있는 그룹 목록 수집
    docs_groups: dict[str, set[str]] = defaultdict(set)
    for code, group in docs_ground_truth.items():
        if code in all_node_ids:
            docs_groups[group].add(code)

    # ── Phase 0: docs ground truth 적용 ──
    for code, group in docs_ground_truth.items():
        if code in all_node_ids:
            code_to_group[code] = group
            locked.add(code)

    phase0_count = len(code_to_group)
    print(f"  Phase 0 (docs ground truth): {phase0_count} locked")
    for g, members in sorted(docs_groups.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"    {g}: {len(members)}개")

    # ── Phase 1: well-known seed (docs에 없는 것만) ──
    for code, group in _m7._WELL_KNOWN.items():
        if code in all_node_ids and code not in locked:
            code_to_group[code] = group

    phase1_seed = len(code_to_group) - phase0_count
    print(f"  Phase 1 (well-known 추가): +{phase1_seed}")

    # ── Phase 2: 경영참여 방향 확장 (docs locked 존중) ──
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

    for _round in range(3):
        newly_added = 0
        for parent in list(code_to_group.keys()):
            parent_group = code_to_group[parent]
            for child in mgmt_directed.get(parent, set()):
                if child in locked:
                    continue  # docs에서 이미 분류 → 건드리지 않음
                if child not in code_to_group:
                    # docs에서 이 그룹의 멤버 목록이 있으면,
                    # child가 그 목록에 없으면 이 그룹에 넣지 않음
                    if parent_group in docs_groups and child not in docs_groups[parent_group]:
                        continue  # docs가 이 그룹을 알지만 child는 멤버 아님 → skip
                    code_to_group[child] = parent_group
                    newly_added += 1
        if newly_added == 0:
            break

    # well-known에 없는 경영참여 미분류 클러스터
    parent_children: dict[str, set[str]] = defaultdict(set)
    for parent, children in mgmt_directed.items():
        if parent not in code_to_group:
            for child in children:
                if child not in code_to_group:
                    parent_children[parent].add(child)

    for parent, children in parent_children.items():
        cluster = {parent} | children
        if len(cluster) >= 2:
            label = _m7._label_group(list(cluster), code_to_name)
            for m in cluster:
                if m not in code_to_group:
                    code_to_group[m] = label

    phase2_count = len(code_to_group) - phase0_count - phase1_seed
    print(f"  Phase 2 (경영참여 확장): +{phase2_count}")

    # ── Phase 3: majorHolder 법인 주주 ──
    matched_corp = corp_edges.filter(pl.col("from_code").is_not_null())
    phase3_added = 0
    for row in matched_corp.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        if fc in locked or tc in locked:
            continue  # docs locked 존중
        if fc in code_to_group and tc not in code_to_group and tc in all_node_ids:
            parent_group = code_to_group[fc]
            if parent_group in docs_groups and tc not in docs_groups[parent_group]:
                continue
            code_to_group[tc] = parent_group
            phase3_added += 1
        elif tc in code_to_group and fc not in code_to_group and fc in all_node_ids:
            parent_group = code_to_group[tc]
            if parent_group in docs_groups and fc not in docs_groups[parent_group]:
                continue
            code_to_group[fc] = parent_group
            phase3_added += 1

    print(f"  Phase 3 (법인주주): +{phase3_added}")

    # ── Phase 4: 공유 개인주주 ──
    person_groups = person_edges.group_by("person_name").agg(
        pl.col("to_code").unique().alias("companies"),
    ).filter(pl.col("companies").list.len() >= 2)

    phase4_added = 0
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
                if best_group in docs_groups and c not in docs_groups[best_group]:
                    continue
                code_to_group[c] = best_group
                phase4_added += 1

    print(f"  Phase 4 (공유주주): +{phase4_added}")

    # ── Phase 5: 이름 키워드 매칭 + 독립 ──
    _GROUP_KEYWORDS = {
        "삼성": ["삼성"], "현대차": ["현대", "기아"],
        "SK": ["SK", "에스케이"], "LG": ["LG", "엘지"],
        "롯데": ["롯데"], "한화": ["한화"],
        "GS": ["GS", "지에스"], "포스코": ["POSCO", "포스코"],
        "CJ": ["CJ", "씨제이"], "두산": ["두산"],
        "HD현대": ["HD현대", "한국조선해양"],
        "효성": ["효성"], "한솔": ["한솔"],
        "카카오": ["카카오"], "네이버": ["네이버", "NAVER"],
    }

    keyword_assigned = 0
    for node in list(all_node_ids - set(code_to_group.keys())):
        name = code_to_name.get(node, "")
        for group, keywords in _GROUP_KEYWORDS.items():
            matched = False
            for kw in keywords:
                if kw in name:
                    # docs에서 이 그룹의 멤버 목록을 알고 있다면, 그 목록에 없으면 skip
                    if group in docs_groups and node not in docs_groups[group]:
                        continue
                    code_to_group[node] = group
                    keyword_assigned += 1
                    matched = True
                    break
            if matched:
                break

    # 나머지 → 독립
    still_unclassified = all_node_ids - set(code_to_group.keys())
    for node in still_unclassified:
        code_to_group[node] = code_to_name.get(node, node)

    total_in_groups = sum(1 for n in all_node_ids
                         if code_to_group.get(n) not in {code_to_name.get(n, n)})
    print(f"  Phase 5 (키워드): +{keyword_assigned}, 독립: {len(still_unclassified)}")
    print(f"  최종: {len(all_node_ids)} nodes, {total_in_groups} in groups ({total_in_groups/len(all_node_ids):.0%})")

    return code_to_group


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 데이터 로드...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}
    listing_codes = set(listing["종목코드"].to_list())

    # investedCompany
    raw_inv = _m2.scan_all_invested()
    invest_edges = _m2.clean_and_build_edges(raw_inv, name_to_code)
    latest_year = invest_edges["year"].max()
    invest_deduped = _m3.deduplicate_edges(invest_edges, latest_year)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))

    # majorHolder
    raw_mh = _m6.scan_all_major_holders()
    corp_edges, person_edges = _m6.build_holder_edges(raw_mh, name_to_code, code_to_name)

    # 전체 노드
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

    # 2. docs ground truth
    print("\n2. docs ground truth 스캔...")
    docs_results = _m10.scan_all_affiliate_sections()
    docs_ground_truth = _m10.build_group_mapping(docs_results, name_to_code, code_to_name)
    print(f"   docs 매핑: {len(docs_ground_truth)} 종목")

    # docs 그룹 통계
    docs_groups_stat: dict[str, list[str]] = defaultdict(list)
    for code, group in docs_ground_truth.items():
        if code in listing_codes:
            docs_groups_stat[group].append(code)
    print(f"   docs 그룹 수: {len(docs_groups_stat)}")
    for g, members in sorted(docs_groups_stat.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"     {g}: {len(members)}개")

    # 3. docs-constrained 분류
    print("\n3. docs-constrained 그룹 분류...")
    code_to_group = classify_with_docs_constraint(
        invest_deduped, corp_edges, person_edges,
        all_node_ids, code_to_name, docs_ground_truth,
    )

    # 4. 결과 비교
    print(f"\n{'=' * 70}")
    print("결과 비교: 007 단독 vs docs-constrained")
    print("=" * 70)

    # 007 단독 실행
    code_to_group_007 = _m7.classify_groups(
        invest_deduped, corp_edges, person_edges, all_node_ids, code_to_name,
    )

    # 주요 그룹 비교
    compare_groups = ["삼성", "현대차", "SK", "LG", "한화", "롯데", "GS", "포스코",
                      "CJ", "두산", "HD현대", "카카오", "효성", "한솔", "한진칼"]

    print(f"\n  {'그룹':10s} {'007':>5s} {'docs제약':>7s} {'docs원본':>7s}")
    print(f"  {'-' * 35}")
    for g in compare_groups:
        c007 = sum(1 for n in all_node_ids if code_to_group_007.get(n) == g)
        c_new = sum(1 for n in all_node_ids if code_to_group.get(n) == g)
        c_docs = len(docs_groups_stat.get(g, []))
        marker = " ←" if c_new != c007 else ""
        print(f"  {g:10s} {c007:5d} {c_new:7d} {c_docs:7d}{marker}")

    # 삼성 상세 비교
    print(f"\n  삼성 상세:")
    samsung_007 = sorted(n for n in all_node_ids if code_to_group_007.get(n) == "삼성")
    samsung_new = sorted(n for n in all_node_ids if code_to_group.get(n) == "삼성")
    samsung_docs = sorted(c for c, g in docs_ground_truth.items() if g == "삼성" and c in all_node_ids)

    print(f"    007: {len(samsung_007)}개")
    print(f"    docs제약: {len(samsung_new)}개")
    print(f"    docs원본: {len(samsung_docs)}개")

    # 007에는 있지만 docs제약에서 빠진 종목
    removed = set(samsung_007) - set(samsung_new)
    if removed:
        print(f"\n    007에서 제거된 종목 ({len(removed)}개):")
        for c in sorted(removed):
            print(f"      {c} {code_to_name.get(c, c)}")

    # docs제약에만 있는 종목
    added = set(samsung_new) - set(samsung_007)
    if added:
        print(f"\n    docs제약에서 추가된 종목 ({len(added)}개):")
        for c in sorted(added):
            print(f"      {c} {code_to_name.get(c, c)}")

    # 전체 통계
    group_counts_new: dict[str, int] = defaultdict(int)
    for code in all_node_ids:
        group_counts_new[code_to_group.get(code, "?")] += 1

    multi_new = {g: c for g, c in group_counts_new.items() if c >= 2}
    indep_new = sum(1 for c in group_counts_new.values() if c == 1)

    group_counts_007: dict[str, int] = defaultdict(int)
    for code in all_node_ids:
        group_counts_007[code_to_group_007.get(code, "?")] += 1

    multi_007 = {g: c for g, c in group_counts_007.items() if c >= 2}
    indep_007 = sum(1 for c in group_counts_007.values() if c == 1)

    print(f"\n  전체 통계:")
    print(f"    {'':20s} {'007':>6s} {'docs제약':>8s}")
    print(f"    {'2명+ 그룹':20s} {len(multi_007):6d} {len(multi_new):8d}")
    print(f"    {'독립':20s} {indep_007:6d} {indep_new:8d}")
    print(f"    {'그룹 분류율':20s} {(len(all_node_ids)-indep_007)/len(all_node_ids):6.0%} {(len(all_node_ids)-indep_new)/len(all_node_ids):8.0%}")

    # 순환출자
    print("\n4. 순환출자 탐지...")
    cycles = _m7.detect_cycles(invest_deduped, code_to_name, max_length=6)
    print(f"   순환: {len(cycles)}개")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
