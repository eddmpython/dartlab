"""
실험 ID: 014
실험명: well-known dict 자동 추출 — 하드코딩 의존 제거

목적:
- 현재 _WELL_KNOWN(80+코드), _WELL_KNOWN_EXT(+46코드)가 수작업 하드코딩
- docs ground truth + majorHolder 20%+ 패턴에서 자동으로 그룹 seed를 추출
- 수작업 dict와 자동 추출 결과를 비교하여 자동화 가능성 검증
- 목표: 자동 추출이 수작업의 90%+ 커버

가설:
1. docs 계열회사 현황만으로 159개 코드(=phase 0) 자동 추출 가능
2. majorHolder 법인주주 20%+ 연결로 추가 40개+ 코드 자동 추출 가능
3. 자동 + docs 조합이 수작업 _WELL_KNOWN_EXT 126개의 90%+ 커버

방법:
1. 013 파이프라인의 scan_affiliate_docs() → docs 기반 seed
2. majorHolder 법인주주에서 ownership 20%+ & 양측 상장사 → 추가 seed
3. 수작업 dict와 비교 (missing / surplus 분석)
4. 자동 seed로 classify_balanced() 실행, 결과 비교

결과 (실험 후 작성):
- Step 1 (docs): 159 codes — 그대로 사용
- Step 2 (majorHolder 20%+): +12 codes — docs 그룹에 20%+ 출자 연결
- Step 3 (새 그룹): +520 codes — 20%+ 양측 상장사 쌍 → 너무 공격적
- 총 자동 seed: 691 codes
- 수작업(127) vs 자동(691): 겹침 101, 미싱 26, 커버리지 79.5%
- 미싱 26개: HLB 3개, 금융지주 3개, 한솔 2개, 롯데 2개 등 (docs 미수록)
- 라벨 불일치 7개: 케이티→KT, 다우기술→다우 등 정규화 문제
- 자동 seed 분류 결과:
  | 그룹 | 자동 | 012기준 | 차이 |
  | 삼성 | 21 | 21 | = |
  | 현대차 | 20 | 18 | +2 |
  | SK | 21 | 21 | = |
  | KT | 2 | 9 | -7 |
  독립: 690 (43%) vs 012의 849 (52%)
  2명+ 그룹: 304 vs 012의 185

결론:
- 가설 1 채택: docs만으로 159개 자동 추출 (Phase 0과 동일)
- 가설 2 부분 채택: majorHolder 20%+로 +12 (목표 40+ 미달)
- 가설 3 부분 채택: 커버리지 79.5% (목표 90% 미달)
- **핵심 결론**: docs가 없는 그룹(HLB, 금융지주, 셀트리온 등)은 자동 추출 불가
  → 최소한의 수작업 보충 dict(~25개)는 필요
  → 하지만 80개→25개로 축소 가능 (docs 미수록 그룹만 보충)
- Step 3(520개 새 그룹)은 과잉 → 독립 감소 효과는 있으나 정확도 검증 필요
- 패키지 이관 시 전략:
  1. docs ground truth 자동 추출 (159개) = primary
  2. majorHolder 20%+ 확장 (12개) = secondary
  3. 나머지 26개는 수작업 보충 dict = fallback
  4. 총 하드코딩: 80+46 → 26개로 80% 축소

실험일: 2026-03-19
"""

# 013 통합 파이프라인에서 필요한 함수 import
import importlib.util
import time
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

_parent = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("_m13", str(_parent / "013_consolidatedPipeline.py"))
_m13 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_m13)


def auto_extract_seeds(
    docs_gt: dict[str, str],
    corp_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """docs + majorHolder 20%+에서 well-known seed 자동 추출.

    Strategy:
    1. docs_gt 그대로 → 기본 seed (159개)
    2. docs_gt의 그룹 멤버끼리 majorHolder 법인 20%+ → 같은 그룹에 추가
    3. docs_gt 없는 그룹도, 법인주주 20%+ 양방향 연결이면 새 그룹 seed
    """
    auto_seeds: dict[str, str] = {}

    # Step 1: docs ground truth 그대로
    for code, group in docs_gt.items():
        if code in all_node_ids:
            auto_seeds[code] = group

    step1 = len(auto_seeds)
    print(f"  Step 1 (docs): {step1} codes")

    # Step 2: majorHolder 법인주주 20%+에서 확장
    matched = corp_edges.filter(
        pl.col("from_code").is_not_null()
        & (pl.col("ownership_pct") >= 20)
    )

    step2_added = 0
    for row in matched.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        pct = row.get("ownership_pct") or 0

        # 이미 seed에 있는 코드가 20%+ 출자 → target도 같은 그룹
        if fc in auto_seeds and tc not in auto_seeds and tc in all_node_ids:
            auto_seeds[tc] = auto_seeds[fc]
            step2_added += 1
        elif tc in auto_seeds and fc not in auto_seeds and fc in all_node_ids:
            auto_seeds[fc] = auto_seeds[tc]
            step2_added += 1

    print(f"  Step 2 (majorHolder 20%+): +{step2_added} codes")

    # Step 3: docs에 없지만, 법인주주 20%+로 연결된 상장사 쌍 → 새 그룹
    # 양방향(A→B 20%+, B는 상장사) → A-B 같은 그룹
    step3_added = 0
    for row in matched.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        if fc not in auto_seeds and tc not in auto_seeds:
            if fc in all_node_ids and tc in all_node_ids:
                # 새 그룹: 이름 기반 라벨
                label = _m13._label_group([fc, tc], code_to_name)
                auto_seeds[fc] = label
                auto_seeds[tc] = label
                step3_added += 2

    print(f"  Step 3 (새 그룹 법인주주 20%+): +{step3_added} codes")
    print(f"  총 자동 seed: {len(auto_seeds)} codes")

    return auto_seeds


def compare_with_manual(
    auto_seeds: dict[str, str],
    code_to_name: dict[str, str],
) -> None:
    """자동 추출 결과를 수작업 _WELL_KNOWN_EXT와 비교."""
    manual = _m13._WELL_KNOWN_EXT

    manual_codes = set(manual.keys())
    auto_codes = set(auto_seeds.keys())

    # 수작업에 있고 자동에 없는
    missing = manual_codes - auto_codes
    # 자동에 있고 수작업에 없는
    surplus = auto_codes - manual_codes
    # 양쪽 다 있는
    overlap = manual_codes & auto_codes

    print(f"\n{'=' * 60}")
    print("수작업 vs 자동 비교")
    print("=" * 60)
    print(f"  수작업: {len(manual_codes)}, 자동: {len(auto_codes)}")
    print(f"  겹침: {len(overlap)}, 미싱: {len(missing)}, 잉여: {len(surplus)}")
    print(f"  커버리지: {len(overlap) / max(len(manual_codes), 1):.1%}")

    # 미싱 상세
    if missing:
        print(f"\n  수작업에만 있는 ({len(missing)}개):")
        for code in sorted(missing):
            name = code_to_name.get(code, "?")
            group = manual[code]
            print(f"    {code} {name:20s} → {group}")

    # 그룹 라벨 불일치
    label_mismatch = 0
    for code in overlap:
        if manual[code] != auto_seeds[code]:
            label_mismatch += 1
    print(f"\n  라벨 불일치: {label_mismatch}개 (겹치는 {len(overlap)}개 중)")
    if label_mismatch > 0:
        for code in sorted(overlap):
            if manual[code] != auto_seeds[code]:
                name = code_to_name.get(code, "?")
                print(f"    {code} {name}: 수작업={manual[code]}, 자동={auto_seeds[code]}")


def test_auto_classification(
    auto_seeds: dict[str, str],
    invest_edges: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """자동 seed로 classify_balanced 실행, 수작업과 결과 비교."""
    print(f"\n{'=' * 60}")
    print("자동 seed 기반 분류 테스트")
    print("=" * 60)

    # auto_seeds를 docs_ground_truth로 사용
    # (classify_balanced의 Phase 0은 docs, Phase 1은 _WELL_KNOWN_EXT를 사용하는데,
    #  여기서는 auto_seeds를 docs로 넣고 _WELL_KNOWN_EXT는 비활성화)
    # → 대신 013의 classify_balanced를 그대로 쓰되, docs_ground_truth에 auto_seeds를 넣는다

    code_to_group = _m13.classify_balanced(
        invest_edges, corp_edges, person_edges,
        all_node_ids, code_to_name, auto_seeds,
    )

    gc = Counter(code_to_group[n] for n in all_node_ids)
    compare = ["삼성", "현대차", "SK", "LG", "한화", "롯데", "GS", "효성",
               "현대백화점", "KT", "HD현대", "대한항공", "포스코", "CJ", "두산"]

    print(f"\n  {'그룹':12s} {'자동':>5s} {'012기준':>7s}")
    print(f"  {'-' * 30}")
    ref = {"삼성": 21, "현대차": 18, "SK": 21, "LG": 10, "한화": 12,
           "롯데": 11, "GS": 11, "효성": 11, "현대백화점": 13, "KT": 9,
           "HD현대": 7, "대한항공": 6, "포스코": 4, "CJ": 6, "두산": 7}
    for g in compare:
        c = gc.get(g, 0)
        r = ref.get(g, 0)
        diff = "" if c == r else f" ({'+'if c>r else ''}{c-r})"
        if c > 0 or r > 0:
            print(f"  {g:12s} {c:5d} {r:7d}{diff}")

    indep = sum(1 for c in gc.values() if c == 1)
    multi = sum(1 for c in gc.values() if c >= 2)
    print(f"\n  2명+ 그룹: {multi}, 독립: {indep} ({indep/len(all_node_ids):.0%})")

    return code_to_group


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 데이터 로드 (013 파이프라인)...")
    name_to_code, code_to_name, listing_codes = _m13.load_listing()

    raw_inv = _m13.scan_invested()
    invest_edges = _m13.build_invest_edges(raw_inv, name_to_code, code_to_name)
    invest_deduped = _m13.deduplicate_edges(invest_edges)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))

    raw_mh = _m13.scan_major_holders()
    corp_edges, person_edges = _m13.build_holder_edges(raw_mh, name_to_code)

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

    print("2. docs ground truth...")
    docs_gt = _m13.scan_affiliate_docs(name_to_code, code_to_name)
    print(f"   → {len(docs_gt)} 종목")

    print("\n3. 자동 seed 추출...")
    auto_seeds = auto_extract_seeds(docs_gt, corp_edges, all_node_ids, code_to_name)

    print("\n4. 수작업 비교...")
    compare_with_manual(auto_seeds, code_to_name)

    print("\n5. 자동 seed 분류 테스트...")
    auto_groups = test_auto_classification(
        auto_seeds, invest_deduped, corp_edges, person_edges,
        all_node_ids, code_to_name,
    )

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
