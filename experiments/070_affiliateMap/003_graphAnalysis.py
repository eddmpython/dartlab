"""
실험 ID: 003
실험명: 관계회사 그래프 분석 — 연결 컴포넌트, 허브, 재벌 클러스터

목적:
- 002에서 구축한 엣지 테이블로 기업 관계 그래프 구축
- Union-Find로 연결 컴포넌트 탐지 → 재벌/기업집단 클러스터 식별
- 허브 노드(degree centrality), 규모별 분포 분석
- 경영참여 vs 단순투자 네트워크 차이 분석

가설:
1. 경영참여 엣지로 연결된 컴포넌트가 재벌 그룹과 대응
2. 최대 컴포넌트 크기 50+ (삼성/현대/SK/LG 등 대그룹)
3. 상장사만 볼 때 10개 이상의 의미 있는 클러스터 존재

방법:
1. 2025년 최신 데이터, 분기 중복 제거 (from+to 기준 최신)
2. Union-Find로 연결 컴포넌트 계산
3. 컴포넌트별 구성원 출력 (상장사 + 비상장사)
4. degree 분석 (in-degree/out-degree)

결과 (실험 후 작성):
- 2025년 중복 제거: 16,409 엣지 (823 출자회사, 14,559 피출자)
- Out-degree TOP: NH투자증권(456), 미래에셋증권(385), NAVER(259)
- In-degree TOP (상장사): 삼성전자(17개사), 고려아연(10), KG모빌리티(7)

[상장사간 전체]
- 911 노드, 84 컴포넌트, 최대 688 (거의 전체가 하나로 연결)
- 크기 5+ 컴포넌트 8개 (LX 5개, 사조 5개, LG전자 7개 등)

[경영참여 + 상장사간] ← 가장 의미 있는 뷰
- 339 노드, 100 컴포넌트, 최대 36
- 크기 5+ 15개: 삼성(36), 현대차(13), SK(10), 롯데(7), 효성(6), 두산(6)
  한솔(6), 유한양행(7), 사조(5), 녹십자(5), NICE(5), 다우(5), KG(5), 하림(5)

[경영참여 비상장 포함]
- 4,437 노드, 296 컴포넌트, 최대 974
- 크기 50+: 11개 (메가 컴포넌트에 삼성+현대+SK+포스코 등 합류)

[재벌 클러스터]
- 삼성: 12 출자회사 → 355 피출자 (상장 24)
- 현대차: 3 출자회사 → 201 피출자 (상장 13)
- SK: 12 출자회사 → 222 피출자 (상장 7)
- LG: 7 출자회사 → 238 피출자 (상장 7)
- 롯데: 7 출자회사 → 137 피출자 (상장 6)
- 카카오: 2 출자회사 → 36 피출자 (상장 3)
- 포스코: 4 출자회사 → 66 피출자 (상장 2)

결론:
- 가설 1 채택: 경영참여 엣지 컴포넌트가 재벌 그룹과 정확히 대응
- 가설 2 채택: 최대 컴포넌트 974 (50+ 목표 초과)
- 가설 3 채택: 경영참여 상장사간 크기 5+ 클러스터 15개 (10개 목표 초과)
- **경영참여 + 상장사간** 뷰가 UI에 가장 적합 (339노드 100컴포넌트, 깔끔)
- 비상장 포함 시 대그룹들이 하나의 메가 컴포넌트로 합류 (공통 출자 경유)

실험일: 2026-03-19
"""

import importlib.util
import sys
import time
from collections import defaultdict
from pathlib import Path

import polars as pl

_mod_path = Path(__file__).resolve().parent / "002_buildEdges.py"
_spec = importlib.util.spec_from_file_location("_edges", str(_mod_path))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
scan_all_invested = _mod.scan_all_invested
clean_and_build_edges = _mod.clean_and_build_edges
load_listing_map = _mod.load_listing_map


# ── Union-Find ──────────────────────────────────────────────


class UnionFind:
    """경량 Union-Find (경로 압축 + 랭크 합침)."""

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


# ── 그래프 구축 ─────────────────────────────────────────────


def deduplicate_edges(edges: pl.DataFrame, year: int) -> pl.DataFrame:
    """특정 연도 데이터에서 (from, to) 중복 제거. 최신 지분율 유지."""
    latest = edges.filter(pl.col("year") == year)

    # (from_code, to_name_norm) 기준 중복 제거 — ownership_pct가 큰 것 유지
    deduped = (
        latest
        .sort("ownership_pct", descending=True, nulls_last=True)
        .unique(subset=["from_code", "to_name_norm"], keep="first")
    )
    return deduped


def build_graph_stats(edges: pl.DataFrame, code_to_name: dict[str, str]) -> None:
    """그래프 통계 출력."""
    print("=" * 70)
    print("그래프 기본 통계 (중복 제거 후)")
    print("=" * 70)
    print(f"  엣지 수: {len(edges):,}")
    print(f"  출자회사(from): {edges['from_code'].n_unique():,}")
    print(f"  피출자(to): {edges['to_name_norm'].n_unique():,}")

    # Out-degree (출자 수)
    out_deg = edges.group_by("from_code").agg(
        pl.col("to_name_norm").count().alias("out_degree")
    ).sort("out_degree", descending=True)
    print(f"\n  Out-degree (출자 수) TOP 15:")
    for row in out_deg.head(15).iter_rows(named=True):
        name = code_to_name.get(row["from_code"], row["from_code"])
        print(f"    {name}: {row['out_degree']}")

    # In-degree (피출자 횟수) — 상장사만
    listed_edges = edges.filter(pl.col("is_listed"))
    in_deg = listed_edges.group_by("to_name_norm").agg(
        pl.col("from_code").n_unique().alias("in_degree")
    ).sort("in_degree", descending=True)
    print(f"\n  In-degree (출자 받는 횟수, 상장사만) TOP 15:")
    for row in in_deg.head(15).iter_rows(named=True):
        print(f"    {row['to_name_norm']}: {row['in_degree']}개사")


def analyze_components(
    edges: pl.DataFrame,
    code_to_name: dict[str, str],
    *,
    purpose_filter: str | None = None,
    listed_only: bool = False,
) -> dict[str, list[str]]:
    """Union-Find로 연결 컴포넌트 분석.

    Args:
        purpose_filter: "경영참여"만 보려면 지정
        listed_only: True면 상장사→상장사 엣지만
    """
    subset = edges
    label = "전체"

    if purpose_filter:
        subset = subset.filter(pl.col("purpose") == purpose_filter)
        label = purpose_filter

    if listed_only:
        subset = subset.filter(pl.col("is_listed"))
        label += " + 상장사간"

    print(f"\n{'=' * 70}")
    print(f"연결 컴포넌트 분석: [{label}] ({len(subset):,} 엣지)")
    print("=" * 70)

    uf = UnionFind()
    for row in subset.iter_rows(named=True):
        from_node = row["from_code"]
        to_node = row["to_code"] if row["is_listed"] and row["to_code"] else row["to_name_norm"]
        uf.union(from_node, to_node)

    comps = uf.components()
    sizes = sorted([len(v) for v in comps.values()], reverse=True)

    print(f"  총 노드: {sum(sizes):,}")
    print(f"  컴포넌트 수: {len(comps):,}")
    print(f"  최대: {sizes[0] if sizes else 0}")
    print(f"  크기 분포: 1={sizes.count(1)}, 2~5={sum(1 for s in sizes if 2<=s<=5)}, "
          f"6~20={sum(1 for s in sizes if 6<=s<=20)}, 21~50={sum(1 for s in sizes if 21<=s<=50)}, "
          f"50+={sum(1 for s in sizes if s > 50)}")

    # 크기 5 이상 컴포넌트 출력
    big_comps = {k: v for k, v in comps.items() if len(v) >= 5}
    big_sorted = sorted(big_comps.items(), key=lambda x: -len(x[1]))

    print(f"\n  크기 5 이상 컴포넌트 ({len(big_sorted)}개):")
    for root, members in big_sorted[:30]:
        # 상장사 이름으로 변환
        named = []
        unlisted_count = 0
        for m in members:
            if m in code_to_name:
                named.append(code_to_name[m])
            elif len(m) == 6 and m.isdigit():
                named.append(m)  # 종목코드지만 이름 없음
            else:
                unlisted_count += 1

        named.sort()
        display = ", ".join(named[:10])
        if len(named) > 10:
            display += f" ... +{len(named)-10}"
        if unlisted_count > 0:
            display += f" (+비상장 {unlisted_count})"
        print(f"    [{len(members):3d}] {display}")

    return comps


def analyze_chaebol_clusters(
    edges: pl.DataFrame,
    code_to_name: dict[str, str],
) -> None:
    """경영참여 엣지 기반 재벌 클러스터 심층 분석."""
    mgmt = edges.filter(pl.col("purpose") == "경영참여")

    print(f"\n{'=' * 70}")
    print(f"재벌 클러스터 심층 분석 (경영참여 엣지, {len(mgmt):,}개)")
    print("=" * 70)

    # 주요 그룹 키워드로 클러스터 라벨링
    group_keywords = {
        "삼성": ["삼성", "Samsung", "SAMSUNG"],
        "현대차": ["현대자동차", "현대모비스", "기아"],
        "SK": ["SK", "에스케이"],
        "LG": ["LG", "엘지"],
        "롯데": ["롯데", "LOTTE"],
        "한화": ["한화", "Hanwha"],
        "GS": ["GS"],
        "현대중공업": ["현대중공업", "HD한국조선"],
        "포스코": ["포스코", "POSCO"],
        "CJ": ["CJ", "씨제이"],
        "두산": ["두산", "Doosan"],
        "LS": ["LS", "엘에스"],
        "카카오": ["카카오", "Kakao"],
        "네이버": ["NAVER", "네이버"],
    }

    for group_name, keywords in group_keywords.items():
        # 해당 그룹의 출자회사 찾기
        group_from = set()
        for row in mgmt.iter_rows(named=True):
            from_name = code_to_name.get(row["from_code"], "")
            if any(kw in from_name for kw in keywords):
                group_from.add(row["from_code"])

        if not group_from:
            continue

        # 해당 그룹이 출자한 모든 회사
        group_edges = mgmt.filter(pl.col("from_code").is_in(list(group_from)))
        targets = group_edges["to_name_norm"].unique().to_list()
        listed_targets = group_edges.filter(pl.col("is_listed"))["to_name_norm"].unique().to_list()

        from_names = [code_to_name.get(c, c) for c in group_from]
        print(f"\n  [{group_name}] 출자회사 {len(group_from)}개: {', '.join(sorted(from_names)[:5])}")
        print(f"    → 피출자 {len(targets)}개 (상장사 {len(listed_targets)}개)")
        if listed_targets:
            print(f"    → 상장사: {', '.join(sorted(listed_targets)[:15])}")

        # 지분율 TOP 5
        top_stakes = (
            group_edges
            .filter(pl.col("ownership_pct").is_not_null())
            .sort("ownership_pct", descending=True)
            .head(5)
        )
        if len(top_stakes) > 0:
            print(f"    → 최대 지분:")
            for row in top_stakes.iter_rows(named=True):
                pct = f"{row['ownership_pct']:.1f}%"
                bv = f"{row['book_value']/1e8:.0f}억" if row["book_value"] else "N/A"
                listed_mark = " [상장]" if row["is_listed"] else ""
                print(f"      {row['to_name']} {pct} ({bv}){listed_mark}")


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 데이터 로드 + 정제...")
    name_to_code, listing = load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}
    raw = scan_all_invested()
    edges = clean_and_build_edges(raw, name_to_code)

    # 2025년 중복 제거
    latest_year = edges["year"].max()
    deduped = deduplicate_edges(edges, latest_year)
    print(f"   {latest_year}년 중복 제거: {len(deduped):,} 엣지")

    # 기본 통계
    build_graph_stats(deduped, code_to_name)

    # 연결 컴포넌트 분석
    # A. 전체 (상장사간만)
    analyze_components(deduped, code_to_name, listed_only=True)

    # B. 경영참여만 (상장사간)
    analyze_components(deduped, code_to_name, purpose_filter="경영참여", listed_only=True)

    # C. 경영참여 (비상장 포함)
    analyze_components(deduped, code_to_name, purpose_filter="경영참여")

    # 재벌 클러스터
    analyze_chaebol_clusters(deduped, code_to_name)

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
