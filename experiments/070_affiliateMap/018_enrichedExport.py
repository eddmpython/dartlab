"""
실험 ID: 018
실험명: 보강 JSON 내보내기 — 단순투자 + 업종 클러스터 포함

목적:
- 017의 전략 A(단순투자 엣지) + C(업종 클러스터) 적용
- 모든 상장사의 ego 뷰가 유용한 정보를 제공하도록 보강
- full JSON에 industry 기반 클러스터 메타 추가
- ego 뷰에 단순투자 엣지 + 같은 업종 이웃 포함

가설:
1. 보강 full JSON ≤ 2MB (크기 제약 유지)
2. 독립 회사 ego 뷰에서 평균 5+ 연결
3. 검증 테스트 40/40 유지 (기존 그룹 분류 불변)

방법:
1. 013 파이프라인 기반 + 단순투자 엣지 추가
2. 노드에 industry 메타 추가 (이미 있음)
3. ego 함수 보강: 독립 회사면 같은 업종 이웃도 포함
4. full JSON, overview, ego 샘플 재생성

결과 (실험 후 작성):
- full v4: 2,306노드, 4,437엣지, 785KB (≤ 2MB ✓)
  - 엣지 타입: investment 1,885 (단순투자 982 + 기타 505 + 경영참여 398), shareholder 813, person 1,739
  - 185그룹, 116업종 클러스터
- ego 샘플:
  - 대기업: 삼성전자 63노드, 현대차 25노드, 카카오 19노드 (기존과 동일)
  - 독립: 대한방직 5노드(+업종3), 현대약품 13노드(+업종10), 우주일렉트로 10노드(+업종10)
- 독립 851개 ego 전수 조사:
  - 평균 노드: 9.9 (가설 5+ 대폭 초과 ✓)
  - 1노드(자기만): 0개 (0%) — 전원 연결 보유
  - 2~5노드: 179개 (21%)
  - 6~10노드: 116개 (14%)
  - 11+노드: 556개 (65%)
- 검증: 40/40 PASS (그룹 분류 완전 불변 ✓)
- 소요: 51초

결론:
- 가설 1 채택: full v4 785KB (≤ 2MB)
- 가설 2 채택: 독립 ego 평균 9.9노드 (5+ 대폭 초과)
- 가설 3 채택: 40/40 PASS
- 핵심 성과: 독립 851개 중 1노드 회사 0개 → 100% 사용자에게 유용한 정보 제공
- 전략 A(단순투자 엣지)가 핵심 기여 — 경영참여 398 외에 단순투자+기타 1,487 엣지 추가
- 전략 C(업종 클러스터)는 fallback으로 작동 — 연결 적은 회사에 같은 업종 이웃 보충
- 채택: v4 포맷을 패키지 이관 시 기본으로 사용

실험일: 2026-03-19
"""

import json
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


def _build_enriched_edges(data: dict) -> list[dict]:
    """기존 엣지 + 단순투자 엣지 포함."""
    edges: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    # L1: investedCompany — 모든 목적 (경영참여+단순투자+기타)
    listed = data["invest_edges"].filter(
        pl.col("is_listed") & pl.col("to_code").is_not_null()
    )
    for row in listed.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "investment")
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "source": row["from_code"], "target": row["to_code"],
            "type": "investment", "purpose": row.get("purpose", ""),
            "ownershipPct": row.get("ownership_pct"),
        })

    # L2: majorHolder 법인
    matched = data["corp_edges"].filter(pl.col("from_code").is_not_null())
    for row in matched.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "shareholder")
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "source": row["from_code"], "target": row["to_code"],
            "type": "shareholder", "ownershipPct": row.get("ownership_pct"),
        })

    return edges


def _build_enriched_nodes(data: dict, edges: list[dict]) -> list[dict]:
    """degree 재계산 + industry 메타."""
    in_deg: dict[str, int] = defaultdict(int)
    out_deg: dict[str, int] = defaultdict(int)
    for e in edges:
        if e["type"] != "person_shareholder":
            out_deg[e["source"]] += 1
            in_deg[e["target"]] += 1

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
    return nodes


def export_enriched_full(data: dict) -> dict:
    """보강 full.json — 단순투자 엣지 포함."""
    edges = _build_enriched_edges(data)
    nodes = _build_enriched_nodes(data, edges)

    # 인물 노드/엣지
    pn, pe = _m13._build_person_data(data)
    nodes.extend(pn)
    edges.extend(pe)

    # 그룹 메타
    gm: dict[str, list[str]] = defaultdict(list)
    for code in data["all_node_ids"]:
        gm[data["code_to_group"].get(code, "")].append(code)
    groups = [
        {"name": g, "rank": r, "memberCount": len(m), "members": sorted(m)}
        for r, (g, m) in enumerate(sorted(gm.items(), key=lambda x: -len(x[1])), 1)
        if len(m) >= 2
    ]

    # 업종 클러스터 메타
    industry_groups: dict[str, list[str]] = defaultdict(list)
    for code in data["all_node_ids"]:
        meta = data["listing_meta"].get(code, {})
        ind = meta.get("industry", "")
        if ind:
            industry_groups[ind].append(code)
    industries = [
        {"name": ind, "memberCount": len(members), "members": sorted(members)}
        for ind, members in sorted(industry_groups.items(), key=lambda x: -len(x[1]))
        if len(members) >= 2
    ]

    # 순환출자
    cycles_out = [
        {"path": [data["code_to_name"].get(c, c) for c in cy], "codes": cy}
        for cy in data["cycles"]
    ]

    cc = sum(1 for n in nodes if n["type"] == "company")
    pc = sum(1 for n in nodes if n["type"] == "person")

    # 엣지 타입별 통계
    edge_types = Counter(e["type"] for e in edges)
    purpose_counts = Counter(
        e.get("purpose", "") for e in edges if e["type"] == "investment"
    )

    return {
        "meta": {
            "year": 2025,
            "nodeCount": len(nodes), "edgeCount": len(edges),
            "companyCount": cc, "personCount": pc,
            "groupCount": len(groups), "industryCount": len(industries),
            "cycleCount": len(cycles_out),
            "edgeTypes": dict(edge_types),
            "investmentPurposes": dict(purpose_counts),
            "layers": ["investment", "shareholder", "person_shareholder"],
        },
        "nodes": nodes, "edges": edges,
        "groups": groups, "industries": industries,
        "cycles": cycles_out,
    }


def export_enriched_ego(
    data: dict,
    full: dict,
    code: str,
    *,
    hops: int = 1,
    include_industry: bool = True,
    max_industry_peers: int = 10,
) -> dict:
    """보강 ego 뷰 — 독립 회사면 같은 업종 이웃도 포함."""
    # 기본 BFS ego
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

    # 업종 이웃 추가 (엣지로 연결된 이웃이 적을 때)
    industry_peers_added = 0
    if include_industry and len(visited) <= 3:
        # 연결이 적은 회사 → 같은 업종 회사를 추가
        center_meta = data["listing_meta"].get(code, {})
        center_industry = center_meta.get("industry", "")
        if center_industry:
            # 같은 업종에서 degree 높은 순
            nl = {n["id"]: n for n in full["nodes"]}
            peers = [
                n for n in full["nodes"]
                if n["type"] == "company"
                and n.get("industry") == center_industry
                and n["id"] != code
                and n["id"] not in visited
            ]
            peers.sort(key=lambda n: n["degree"], reverse=True)
            for p in peers[:max_industry_peers]:
                visited.add(p["id"])
                industry_peers_added += 1

    # 서브그래프 추출
    nl = {n["id"]: n for n in full["nodes"]}
    ego_nodes = [nl[nid] for nid in sorted(visited) if nid in nl]
    ego_edges = [
        e for e in full["edges"]
        if e["source"] in visited and e["target"] in visited
    ]

    name = data["code_to_name"].get(code, code)
    center_meta = data["listing_meta"].get(code, {})

    return {
        "meta": {
            "type": "ego", "center": code, "centerName": name,
            "centerIndustry": center_meta.get("industry", ""),
            "hops": hops,
            "nodeCount": len(ego_nodes), "edgeCount": len(ego_edges),
            "industryPeersAdded": industry_peers_added,
        },
        "nodes": ego_nodes, "edges": ego_edges,
    }


def _save_json(obj: dict, path: Path) -> int:
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text)


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("파이프라인 실행...")
    data = _m13.build_graph()

    # 보강 full 생성
    print("\n보강 full.json 생성...")
    full = export_enriched_full(data)
    output_dir = _parent / "output"
    output_dir.mkdir(exist_ok=True)
    size = _save_json(full, output_dir / "affiliate_full_v4.json")
    print(f"  노드: {full['meta']['nodeCount']}, 엣지: {full['meta']['edgeCount']}")
    print(f"  엣지 타입: {full['meta']['edgeTypes']}")
    print(f"  투자 목적: {full['meta']['investmentPurposes']}")
    print(f"  그룹: {full['meta']['groupCount']}, 업종: {full['meta']['industryCount']}")
    print(f"  크기: {size/1024:.0f}KB")

    # overview (기존과 동일)
    overview = _m13.export_overview(data, full)
    size = _save_json(overview, output_dir / "affiliate_overview_v4.json")
    print(f"\n  overview: {overview['meta']['groupCount']}그룹, {size/1024:.0f}KB")

    # ego 샘플 — 대기업 + 독립 회사
    print("\nego 뷰 샘플:")
    ego_samples = [
        ("005930", "삼성전자"),
        ("005380", "현대자동차"),
        ("035720", "카카오"),
        # 독립 회사 샘플
        ("001070", "대한방직"),
        ("004310", "현대약품"),
        ("065680", "우주일렉트로"),
        ("140410", "메지온"),
        ("032640", "LG유플러스"),
    ]
    for code, name in ego_samples:
        ego = export_enriched_ego(data, full, code, hops=1)
        size = _save_json(ego, output_dir / f"ego_{code}_v4.json")
        ip = ego["meta"]["industryPeersAdded"]
        ind = ego["meta"].get("centerIndustry", "")
        extra = f" +업종{ip}" if ip > 0 else ""
        print(f"  {name:15s}: {ego['meta']['nodeCount']:3d}노드 {ego['meta']['edgeCount']:3d}엣지 {size/1024:.0f}KB [{ind}]{extra}")

    # 독립 회사 ego 풍부도 전수 조사
    print("\n독립 회사 ego 풍부도 전수 조사...")
    gc = Counter(data["code_to_group"][n] for n in data["all_node_ids"])
    indep_codes = [n for n in data["all_node_ids"] if gc[data["code_to_group"][n]] == 1]

    ego_sizes: list[int] = []
    zero_connection: int = 0
    for code in indep_codes:
        ego = export_enriched_ego(data, full, code, hops=1)
        n_count = ego["meta"]["nodeCount"]
        ego_sizes.append(n_count)
        if n_count <= 1:
            zero_connection += 1

    avg_nodes = sum(ego_sizes) / max(len(ego_sizes), 1)
    print(f"  독립 {len(indep_codes)}개 ego 평균 노드: {avg_nodes:.1f}")
    print(f"  1노드(자기만): {zero_connection}개 ({zero_connection/max(len(indep_codes),1):.0%})")
    print(f"  2~5노드: {sum(1 for s in ego_sizes if 2<=s<=5)}개")
    print(f"  6~10노드: {sum(1 for s in ego_sizes if 6<=s<=10)}개")
    print(f"  11+노드: {sum(1 for s in ego_sizes if s>=11)}개")

    # 검증
    print(f"\n{'=' * 60}")
    print("검증 테스트 (기존 그룹 분류 불변 확인)")
    print("=" * 60)
    p, f, _ = _m15.run_validation(
        data["code_to_group"], data["code_to_name"],
        data["all_node_ids"], data["cycles"],
    )
    print(f"\n→ {p} PASS / {f} FAIL")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
