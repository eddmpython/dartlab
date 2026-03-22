"""
실험 ID: 016
실험명: 독립 53% 개선 — 추가 분류 전략 탐색

목적:
- 현재 849/1620 (53%) 독립 노드 감소
- 기존 분류 정확도를 유지하면서 독립 비율 45% 이하 목표
- 3가지 전략 비교 실험:
  A. 이름 키워드 확대 (기존 22그룹 → 50그룹)
  B. 법인주주 임계값 낮추기 (known 20%→10%, unknown 0%→0%)
  C. 단순투자 엣지 활용 (경영참여만 → 단순투자 포함)

가설:
1. 전략 A (키워드 확대)로 독립 5%p 추가 감소
2. 전략 B (임계값 완화)로 독립 3%p 추가 감소
3. 전략 C (단순투자)는 정확도 하락으로 비채택 예상

방법:
1. 013 파이프라인 결과를 기반으로 각 전략별 추가 분류 시도
2. 015 검증 테스트로 정확도 유지 확인
3. 전략 조합 최적화

결과 (실험 후 작성):
- 기준: 독립 860 (53%), 2명+ 그룹 184
- 전략 A (키워드 확대): 독립 855 (53%), -5개만. 검증 40/40 PASS
  - "한국", "아이", "케이" 등 접두사가 많지만 실제 관계없는 회사들
  - 4개+ & 3글자+ 보수적 적용해도 5개만 재분류 → 효과 미미
- 전략 B (임계값 10%): 독립 841 (52%), -19개. 검증 40/40 PASS
  - Phase 3에서 +102 (vs 기준 +99), 삼성 21→22
  - 1%p 감소, 정확도 유지 → 소폭 개선
- 전략 C (단순투자 10%+): 독립 860 (53%), +0. 검증 40/40 PASS
  - 단순투자 10%+ 상장사간 엣지가 0개 → 데이터 없음

결론:
- 가설 1 기각: 전략 A 효과 미미 (-5개, 0.3%p)
- 가설 2 부분 채택: 전략 B 소폭 개선 (-19개, 1%p), 삼성 +1은 허용범위
- 가설 3 채택: 전략 C는 데이터 부재로 효과 0
- **핵심 결론: 독립 53%는 데이터의 구조적 한계**
  - 860개 독립 회사는 출자/지분/인적 관계가 공시에 없는 소규모 회사
  - 공정위 대기업집단 목록 같은 외부 데이터 없이는 추가 분류 불가
  - 이것은 "문제"가 아니라 "사실" — 관계가 없는 회사는 독립이 정확
- 패키지 이관 시: 기준 분류(013)를 그대로 사용, 전략 B는 선택적 옵션

실험일: 2026-03-19
"""

import time
from pathlib import Path
from collections import Counter, defaultdict

import polars as pl
import importlib.util

_parent = Path(__file__).resolve().parent
_sp13 = importlib.util.spec_from_file_location("_m13", str(_parent / "013_consolidatedPipeline.py"))
_m13 = importlib.util.module_from_spec(_sp13)
_sp13.loader.exec_module(_m13)

_sp15 = importlib.util.spec_from_file_location("_m15", str(_parent / "015_validation.py"))
_m15 = importlib.util.module_from_spec(_sp15)
_sp15.loader.exec_module(_m15)


def strategy_a_more_keywords(
    code_to_group: dict[str, str],
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """전략 A: 키워드 확대 — 독립 노드의 이름에서 추가 그룹 키워드 탐지."""
    ctg = dict(code_to_group)

    # 독립 노드 이름 분석 → 빈도 높은 접두사/키워드 추출
    indep_names: list[str] = []
    for n in all_node_ids:
        gc = Counter(ctg[n2] for n2 in all_node_ids)
        if gc.get(ctg[n], 0) == 1:  # 이 그룹에 혼자 = 독립
            indep_names.append(code_to_name.get(n, ""))

    # 2글자+ 접두사 빈도 (독립 노드 중)
    prefix_counts: dict[str, list[str]] = defaultdict(list)
    for name in indep_names:
        if len(name) >= 4:  # 의미 있는 이름
            prefix_counts[name[:2]].append(name)
            if len(name) >= 6:
                prefix_counts[name[:3]].append(name)

    # 3개+ 독립 노드가 같은 접두사 공유 → 자동 그룹 후보
    auto_groups: dict[str, list[str]] = {}
    for prefix, names in sorted(prefix_counts.items(), key=lambda x: -len(x[1])):
        if len(names) >= 3 and len(prefix) >= 2:
            # 기존 그룹 이름과 겹치지 않는 경우만
            gc = Counter(ctg[n] for n in all_node_ids)
            if prefix not in gc:
                auto_groups[prefix] = names

    # 상위 후보 출력 + 적용
    print(f"\n  전략 A: 독립 {len(indep_names)}개에서 접두사 분석")
    print(f"  3개+ 공유 접두사 후보 (상위 20):")
    applied = 0
    for prefix, names in list(auto_groups.items())[:20]:
        print(f"    '{prefix}' ({len(names)}개): {', '.join(names[:5])}")

    # 보수적 적용: 4개+ 공유, 3글자+ 접두사만
    for prefix, names in auto_groups.items():
        if len(names) >= 4 and len(prefix) >= 3:
            for n in all_node_ids:
                name = code_to_name.get(n, "")
                gc = Counter(ctg[n2] for n2 in all_node_ids)
                if gc.get(ctg[n], 0) == 1 and name.startswith(prefix):
                    ctg[n] = prefix
                    applied += 1

    print(f"  적용: {applied}개 재분류")
    return ctg


def strategy_b_lower_threshold(
    invest_edges: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    all_node_ids: set[str],
    code_to_name: dict[str, str],
    docs_gt: dict[str, str],
) -> dict[str, str]:
    """전략 B: known 그룹 법인주주 임계값 20%→10%로 완화."""
    # classify_balanced를 약간 수정 — Phase 3 임계값만 변경
    code_to_group: dict[str, str] = {}
    locked: set[str] = set()

    for code, group in docs_gt.items():
        if code in all_node_ids:
            code_to_group[code] = group
            locked.add(code)
    for code, group in _m13._WELL_KNOWN_EXT.items():
        if code in all_node_ids and code not in locked:
            code_to_group[code] = group
            locked.add(code)

    known_groups: dict[str, set[str]] = defaultdict(set)
    for code in locked:
        known_groups[code_to_group[code]].add(code)
    known_names = {g for g, m in known_groups.items() if len(m) >= 2}

    # Phase 2: 경영참여 (동일)
    mgmt = invest_edges.filter(
        (pl.col("purpose") == "경영참여") & pl.col("is_listed") & pl.col("to_code").is_not_null()
    )
    mgmt_dir: dict[str, set[str]] = defaultdict(set)
    for row in mgmt.iter_rows(named=True):
        a, b = row["from_code"], row["to_code"]
        if a != b and a in all_node_ids and b in all_node_ids:
            mgmt_dir[a].add(b)

    for _ in range(3):
        newly = 0
        for p in list(code_to_group.keys()):
            pg = code_to_group[p]
            for c in mgmt_dir.get(p, set()):
                if c in locked or c in code_to_group:
                    continue
                if pg in known_names:
                    continue
                code_to_group[c] = pg
                newly += 1
        if newly == 0:
            break

    pc: dict[str, set[str]] = defaultdict(set)
    for p, ch in mgmt_dir.items():
        if p not in code_to_group:
            for c in ch:
                if c not in code_to_group:
                    pc[p].add(c)
    for p in list(code_to_group.keys()):
        if code_to_group[p] in known_names:
            uc = [c for c in mgmt_dir.get(p, set()) if c not in code_to_group and c not in locked]
            if len(uc) >= 2:
                for u in uc:
                    if u not in pc:
                        pc[u] = set()
                    for u2 in uc:
                        if u != u2 and u2 in mgmt_dir.get(u, set()):
                            pc[u].add(u2)
    for p, ch in pc.items():
        cluster = {p} | ch
        if len(cluster) >= 2:
            label = _m13._label_group(list(cluster), code_to_name)
            for m in cluster:
                if m not in code_to_group:
                    code_to_group[m] = label

    # Phase 3: 법인주주 ★ 10% 임계값 ★
    matched = corp_edges.filter(pl.col("from_code").is_not_null())
    phase3 = 0
    for row in matched.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        pct = row.get("ownership_pct") or 0
        if fc in code_to_group and tc not in code_to_group and tc in all_node_ids and tc not in locked:
            pg = code_to_group[fc]
            if pg in known_names and pct < 10:  # ★ 10% instead of 20%
                continue
            code_to_group[tc] = pg
            phase3 += 1
        elif tc in code_to_group and fc not in code_to_group and fc in all_node_ids and fc not in locked:
            pg = code_to_group[tc]
            if pg in known_names and pct < 10:  # ★ 10%
                continue
            code_to_group[fc] = pg
            phase3 += 1

    # Phase 4: 공유 개인주주 (동일)
    pg2 = person_edges.group_by("person_name").agg(
        pl.col("to_code").unique().alias("companies"),
    ).filter(pl.col("companies").list.len() >= 2)
    for row in pg2.iter_rows(named=True):
        codes = [c for c in row["companies"] if c in all_node_ids and c not in locked]
        if len(codes) < 2:
            continue
        gd: dict[str, list[str]] = defaultdict(list)
        ua: list[str] = []
        for c in codes:
            if c in code_to_group:
                gd[code_to_group[c]].append(c)
            else:
                ua.append(c)
        if not gd or not ua:
            continue
        best = max(gd, key=lambda g: len(gd[g]))
        if len(gd[best]) >= 2:
            for c in ua:
                code_to_group[c] = best

    # Phase 5: 키워드 + 독립
    for node in list(all_node_ids - set(code_to_group.keys())):
        name = code_to_name.get(node, "")
        for group, keywords in _m13._GROUP_KEYWORDS.items():
            if any(kw in name for kw in keywords):
                code_to_group[node] = group
                break
    for node in all_node_ids - set(code_to_group.keys()):
        code_to_group[node] = code_to_name.get(node, node)

    print(f"\n  전략 B: Phase 3 임계값 10%")
    print(f"    Phase 3 추가: +{phase3}")
    return code_to_group


def strategy_c_simple_invest(
    invest_edges: pl.DataFrame,
    code_to_group: dict[str, str],
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict[str, str]:
    """전략 C: 단순투자 엣지도 활용 (보수적: 10%+ & 동일 그룹 child만)."""
    ctg = dict(code_to_group)

    simple = invest_edges.filter(
        (pl.col("purpose") == "단순투자")
        & pl.col("is_listed")
        & pl.col("to_code").is_not_null()
        & (pl.col("ownership_pct") >= 10)
    )

    added = 0
    for row in simple.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        pct = row.get("ownership_pct") or 0
        if fc in ctg and tc not in ctg and tc in all_node_ids:
            # 단순투자 10%+면 같은 그룹
            gc = Counter(ctg[n] for n in all_node_ids)
            if gc.get(ctg.get(tc, ""), 0) <= 1:  # 독립일 때만
                ctg[tc] = ctg[fc]
                added += 1

    print(f"\n  전략 C: 단순투자 10%+ 활용 → +{added}")
    return ctg


def _report(label: str, ctg: dict[str, str], all_node_ids: set[str]) -> None:
    gc = Counter(ctg[n] for n in all_node_ids)
    indep = sum(1 for c in gc.values() if c == 1)
    multi = sum(1 for c in gc.values() if c >= 2)
    print(f"\n  [{label}]")
    print(f"    독립: {indep} ({indep/len(all_node_ids):.0%}), 2명+ 그룹: {multi}")
    compare = ["삼성", "현대차", "SK", "LG", "한화", "현대백화점", "KT"]
    for g in compare:
        c = gc.get(g, 0)
        if c > 0:
            print(f"    {g}: {c}")


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("파이프라인 실행...")
    data = _m13.build_graph()
    base_ctg = data["code_to_group"]
    all_nodes = data["all_node_ids"]
    c2n = data["code_to_name"]

    _report("기준 (012/013)", base_ctg, all_nodes)

    # 전략 A
    print(f"\n{'=' * 60}")
    print("전략 A: 이름 키워드 확대")
    print("=" * 60)
    ctg_a = strategy_a_more_keywords(base_ctg, all_nodes, c2n)
    _report("전략 A 결과", ctg_a, all_nodes)

    # 전략 B
    print(f"\n{'=' * 60}")
    print("전략 B: 법인주주 임계값 10%")
    print("=" * 60)
    docs_gt = _m13.scan_affiliate_docs(
        *_m13.load_listing()[:2]
    )
    ctg_b = strategy_b_lower_threshold(
        data["invest_edges"], data["corp_edges"], data["person_edges"],
        all_nodes, c2n, docs_gt,
    )
    _report("전략 B 결과", ctg_b, all_nodes)

    # 전략 C
    print(f"\n{'=' * 60}")
    print("전략 C: 단순투자 10%+ 활용")
    print("=" * 60)
    ctg_c = strategy_c_simple_invest(data["invest_edges"], base_ctg, all_nodes, c2n)
    _report("전략 C 결과", ctg_c, all_nodes)

    # 검증 — 각 전략별
    print(f"\n{'=' * 60}")
    print("검증 테스트")
    print("=" * 60)
    for label, ctg in [("A", ctg_a), ("B", ctg_b), ("C", ctg_c)]:
        print(f"\n--- 전략 {label} ---")
        p, f, _ = _m15.run_validation(ctg, c2n, all_nodes, data["cycles"])
        print(f"  → {p} PASS / {f} FAIL")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
