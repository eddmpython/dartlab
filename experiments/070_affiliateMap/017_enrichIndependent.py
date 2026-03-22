"""
실험 ID: 017
실험명: 독립 회사 정보 보강 — 모든 상장사에 유용한 관계 정보 제공

목적:
- 현재 860개 독립 회사는 ego 검색 시 "독립"만 표시 → 사용자 가치 0
- 독립 회사라도 사용자에게 줄 수 있는 관계 정보 3가지 전략 실험:
  A. 단순투자 포함 엣지 — "삼성전자가 이 회사에 단순투자 중" 도 관계
  B. 공유 주주 네트워크 — "국민연금이 주주인 회사 30개" 도 관계
  C. 업종/섹터 클러스터 — 같은 업종의 이웃 회사 그룹

가설:
1. 전략 A: 단순투자 엣지 추가 시 독립 회사 중 30%+가 연결 획득
2. 전략 B: 공유 주주 네트워크로 독립 회사 중 50%+가 연결 획득
3. 전략 C: 업종 기반으로 100% 커버 가능 (모든 회사에 업종 있음)
4. 3가지 조합으로 "검색하면 항상 의미 있는 정보" 달성

방법:
1. 013 파이프라인 결과에서 독립 회사 목록 추출
2. 각 전략별 엣지/노드 추가 후 커버리지 측정
3. ego 뷰 샘플 생성 — 독립 회사도 풍부한 관계 정보 확인

결과 (실험 후 작성):
- 독립 회사: 844개 / 1,620개 (52%)
- 전략 A (단순투자 포함): 독립 723개 연결 (**86%**), 엣지 1,089건
  - 목적별: 단순투자 742, 기타 316, 경영참여 31
  - 대신증권 25건, 위드텍 23건, 서울보증보험 23건 등 증권/투자 회사가 허브
- 전략 B (공유 주주): 독립 489개 연결 (**58%**), 엣지 1,350건
  - 주요 문제: 동명이인 상위 (이재원 7사, 조재현 7사 — 실제 동일인 아닐 가능성)
  - 국민연금공단이 person으로 오분류 (classify_holder 개선 필요)
  - 정제 없이는 신뢰도 낮음
- 전략 C (업종 클러스터): 독립 844개 연결 (**100%**), 업종 144개
  - 모든 상장사에 업종 있음 → 100% 커버
  - 평균 업종 클러스터 크기 44.2개
  - TOP: 소프트웨어(70), 기계(60), 전자부품(50), 의약품(37)
- **통합**: A+B = 95%, A+B+C = **100%** (미커버 0개)

결론:
- 가설 1 채택: 전략 A 86% (목표 30% 대폭 초과)
- 가설 2 채택: 전략 B 58% (목표 50% 초과), 단 동명이인 정제 필요
- 가설 3 채택: 전략 C 100% (업종이 최종 안전망)
- 가설 4 채택: A+B+C 조합으로 100% 커버 달성
- **채택 우선순위**:
  1. **전략 A 즉시 채택** — 단순투자 엣지를 ego 뷰에 포함 (라벨만 다르게)
  2. **전략 C 즉시 채택** — 업종 클러스터를 ego 뷰의 fallback으로 제공
  3. **전략 B 보류** — 동명이인 정제(법인명 필터, 2자 한글 제외 등) 후 채택
- 사용자 경험 변화: "독립이라 정보 없음" → "단순투자로 연결된 회사 + 같은 업종 회사"

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


def get_independent_codes(
    code_to_group: dict[str, str],
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> set[str]:
    """독립 회사 코드 추출."""
    gc = Counter(code_to_group[n] for n in all_node_ids)
    return {n for n in all_node_ids if gc[code_to_group[n]] == 1}


# ═══════════════════════════════════════════════════════════════
# 전략 A: 단순투자 엣지 포함
# ═══════════════════════════════════════════════════════════════


def strategy_a_all_investments(
    invest_edges: pl.DataFrame,
    indep_codes: set[str],
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict:
    """단순투자 포함 모든 출자 엣지 → 독립 회사에 연결 추가."""
    # 모든 목적(경영참여+단순투자+기타) 상장사간 엣지
    all_listed = invest_edges.filter(
        pl.col("is_listed") & pl.col("to_code").is_not_null()
        & (pl.col("from_code") != pl.col("to_code"))
    )

    # 독립 회사가 연결된 엣지
    indep_connected: set[str] = set()
    edges_for_indep: list[dict] = []

    for row in all_listed.iter_rows(named=True):
        fc, tc = row["from_code"], row["to_code"]
        if fc in indep_codes or tc in indep_codes:
            if fc in indep_codes:
                indep_connected.add(fc)
            if tc in indep_codes:
                indep_connected.add(tc)
            edges_for_indep.append({
                "from": fc, "to": tc,
                "purpose": row.get("purpose", ""),
                "pct": row.get("ownership_pct"),
            })

    # 목적별 분류
    purpose_counts = Counter(e["purpose"] for e in edges_for_indep)

    print(f"\n전략 A: 단순투자 포함 전체 출자 엣지")
    print(f"  전체 상장사간 엣지: {all_listed.height:,}")
    print(f"  독립 회사 관련 엣지: {len(edges_for_indep):,}")
    print(f"  독립 회사 연결: {len(indep_connected)} / {len(indep_codes)} ({len(indep_connected)/max(len(indep_codes),1):.0%})")
    print(f"  목적별: {dict(purpose_counts)}")

    # 연결된 독립 회사 샘플
    if indep_connected:
        print(f"\n  연결된 독립 회사 샘플 (상위 10):")
        conn_edges_count = Counter()
        for e in edges_for_indep:
            if e["from"] in indep_codes:
                conn_edges_count[e["from"]] += 1
            if e["to"] in indep_codes:
                conn_edges_count[e["to"]] += 1
        for code, cnt in conn_edges_count.most_common(10):
            name = code_to_name.get(code, code)
            # 연결된 상대 회사
            neighbors = []
            for e in edges_for_indep:
                if e["from"] == code:
                    neighbors.append(f"→{code_to_name.get(e['to'], e['to'])}({e['purpose']})")
                elif e["to"] == code:
                    neighbors.append(f"←{code_to_name.get(e['from'], e['from'])}({e['purpose']})")
            print(f"    {name} ({cnt}건): {', '.join(neighbors[:3])}")

    return {
        "connected": indep_connected,
        "edges": edges_for_indep,
        "coverage": len(indep_connected) / max(len(indep_codes), 1),
    }


# ═══════════════════════════════════════════════════════════════
# 전략 B: 공유 주주 네트워크
# ═══════════════════════════════════════════════════════════════


def strategy_b_shared_holders(
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    indep_codes: set[str],
    all_node_ids: set[str],
    code_to_name: dict[str, str],
) -> dict:
    """공유 주주(법인+개인)로 독립 회사 연결."""
    # 1. 법인 주주 — 모든 법인 주주 엣지 (매칭된 것만)
    corp_matched = corp_edges.filter(pl.col("from_code").is_not_null())

    # 법인 주주가 같은 회사 → 연결
    holder_to_companies: dict[str, set[str]] = defaultdict(set)
    for row in corp_matched.iter_rows(named=True):
        holder = row["from_code"]
        target = row["to_code"]
        if target in all_node_ids:
            holder_to_companies[holder].add(target)

    # 2. 개인 주주 — 여러 회사의 개인 주주
    for row in person_edges.iter_rows(named=True):
        pname = row["person_name"]
        tc = row["to_code"]
        if tc in all_node_ids:
            holder_to_companies[f"person_{pname}"].add(tc)

    # 독립 회사가 공유 주주를 통해 연결되는 회사
    indep_connected: set[str] = set()
    shared_edges: list[dict] = []

    for holder, companies in holder_to_companies.items():
        if len(companies) < 2:
            continue
        indep_in_group = companies & indep_codes
        if not indep_in_group:
            continue
        others = companies - indep_in_group
        if not others:
            # 독립끼리만 공유 → 독립끼리라도 연결
            codes_list = sorted(indep_in_group)
            for i in range(len(codes_list)):
                for j in range(i + 1, len(codes_list)):
                    shared_edges.append({
                        "from": codes_list[i], "to": codes_list[j],
                        "holder": holder, "type": "shared_holder",
                    })
                    indep_connected.add(codes_list[i])
                    indep_connected.add(codes_list[j])
        else:
            for ic in indep_in_group:
                for oc in others:
                    shared_edges.append({
                        "from": ic, "to": oc,
                        "holder": holder, "type": "shared_holder",
                    })
                    indep_connected.add(ic)

    # 주요 공유 주주 분석
    top_holders = Counter()
    for e in shared_edges:
        top_holders[e["holder"]] += 1

    print(f"\n전략 B: 공유 주주 네트워크")
    print(f"  공유 주주 엣지: {len(shared_edges):,}")
    print(f"  독립 회사 연결: {len(indep_connected)} / {len(indep_codes)} ({len(indep_connected)/max(len(indep_codes),1):.0%})")

    print(f"\n  주요 공유 주주 TOP 15:")
    for holder, cnt in top_holders.most_common(15):
        if holder.startswith("person_"):
            label = holder.replace("person_", "") + " (개인)"
        else:
            label = code_to_name.get(holder, holder) + " (법인)"
        companies = holder_to_companies[holder]
        indep_in = companies & indep_codes
        print(f"    {label}: {len(companies)}개사 주주 (독립 {len(indep_in)}개), 엣지 {cnt}")

    return {
        "connected": indep_connected,
        "edges": shared_edges,
        "coverage": len(indep_connected) / max(len(indep_codes), 1),
    }


# ═══════════════════════════════════════════════════════════════
# 전략 C: 업종 클러스터
# ═══════════════════════════════════════════════════════════════


def strategy_c_industry_cluster(
    indep_codes: set[str],
    all_node_ids: set[str],
    code_to_name: dict[str, str],
    listing_meta: dict[str, dict],
) -> dict:
    """같은 업종의 회사끼리 클러스터."""
    # 업종별 회사 분류
    industry_groups: dict[str, set[str]] = defaultdict(set)
    no_industry: set[str] = set()

    for code in all_node_ids:
        meta = listing_meta.get(code, {})
        industry = meta.get("industry", "")
        if industry and industry != "":
            industry_groups[industry].add(code)
        else:
            no_industry.add(code)

    # 독립 회사의 업종 커버리지
    indep_with_industry = 0
    indep_industry_sizes: list[int] = []
    for code in indep_codes:
        meta = listing_meta.get(code, {})
        industry = meta.get("industry", "")
        if industry:
            indep_with_industry += 1
            indep_industry_sizes.append(len(industry_groups[industry]))

    print(f"\n전략 C: 업종 클러스터")
    print(f"  업종 수: {len(industry_groups)}")
    print(f"  업종 있는 회사: {sum(len(v) for v in industry_groups.values())} / {len(all_node_ids)}")
    print(f"  업종 없는 회사: {len(no_industry)}")
    print(f"  독립 회사 업종 커버: {indep_with_industry} / {len(indep_codes)} ({indep_with_industry/max(len(indep_codes),1):.0%})")

    if indep_industry_sizes:
        avg_size = sum(indep_industry_sizes) / len(indep_industry_sizes)
        print(f"  독립 회사의 평균 업종 클러스터 크기: {avg_size:.1f}")

    # 독립 회사가 많은 업종 TOP
    indep_per_industry: dict[str, int] = defaultdict(int)
    for code in indep_codes:
        meta = listing_meta.get(code, {})
        industry = meta.get("industry", "")
        if industry:
            indep_per_industry[industry] += 1

    print(f"\n  독립 회사 많은 업종 TOP 15:")
    for ind, cnt in sorted(indep_per_industry.items(), key=lambda x: -x[1])[:15]:
        total = len(industry_groups[ind])
        print(f"    {ind}: 독립 {cnt} / 전체 {total}")

    return {
        "connected": {c for c in indep_codes
                      if listing_meta.get(c, {}).get("industry", "")},
        "coverage": indep_with_industry / max(len(indep_codes), 1),
        "industry_groups": dict(industry_groups),
    }


# ═══════════════════════════════════════════════════════════════
# 통합 분석: 3가지 조합
# ═══════════════════════════════════════════════════════════════


def combined_analysis(
    indep_codes: set[str],
    result_a: dict,
    result_b: dict,
    result_c: dict,
    code_to_name: dict[str, str],
) -> None:
    """3가지 전략 조합 커버리지."""
    a_conn = result_a["connected"]
    b_conn = result_b["connected"]
    c_conn = result_c["connected"]

    ab = a_conn | b_conn
    abc = a_conn | b_conn | c_conn

    print(f"\n{'=' * 60}")
    print("통합 커버리지 분석")
    print("=" * 60)
    print(f"  독립 회사 총: {len(indep_codes)}")
    print(f"  A (단순투자 포함): {len(a_conn)} ({len(a_conn)/max(len(indep_codes),1):.0%})")
    print(f"  B (공유 주주):     {len(b_conn)} ({len(b_conn)/max(len(indep_codes),1):.0%})")
    print(f"  C (업종 클러스터): {len(c_conn)} ({len(c_conn)/max(len(indep_codes),1):.0%})")
    print(f"  A+B:              {len(ab)} ({len(ab)/max(len(indep_codes),1):.0%})")
    print(f"  A+B+C:            {len(abc)} ({len(abc)/max(len(indep_codes),1):.0%})")

    # 아무것도 안 걸리는 회사
    uncovered = indep_codes - abc
    print(f"\n  3가지 전부 미커버: {len(uncovered)}개")
    if uncovered:
        samples = sorted(uncovered)[:10]
        for code in samples:
            print(f"    {code} {code_to_name.get(code, '?')}")

    # ego 뷰 예시 — 독립 회사
    print(f"\n  독립 회사 ego 풍부도 예시:")
    for code in sorted(a_conn)[:5]:
        name = code_to_name.get(code, code)
        a_edges = sum(1 for e in result_a["edges"] if e["from"] == code or e["to"] == code)
        b_edges = sum(1 for e in result_b["edges"] if e["from"] == code or e["to"] == code)
        in_c = "Y" if code in c_conn else "N"
        print(f"    {name}: 출자관계 {a_edges}, 공유주주 {b_edges}, 업종 {in_c}")


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("파이프라인 실행...")
    data = _m13.build_graph()

    indep = get_independent_codes(data["code_to_group"], data["all_node_ids"], data["code_to_name"])
    print(f"\n독립 회사: {len(indep)}개 / {len(data['all_node_ids'])}개")

    # 전략 A
    print(f"\n{'=' * 60}")
    result_a = strategy_a_all_investments(
        data["invest_edges"], indep, data["all_node_ids"], data["code_to_name"],
    )

    # 전략 B
    print(f"\n{'=' * 60}")
    result_b = strategy_b_shared_holders(
        data["corp_edges"], data["person_edges"],
        indep, data["all_node_ids"], data["code_to_name"],
    )

    # 전략 C
    print(f"\n{'=' * 60}")
    result_c = strategy_c_industry_cluster(
        indep, data["all_node_ids"], data["code_to_name"], data["listing_meta"],
    )

    # 통합
    combined_analysis(indep, result_a, result_b, result_c, data["code_to_name"])

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
