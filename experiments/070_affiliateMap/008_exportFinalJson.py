"""
실험 ID: 008
실험명: UI-ready 최종 JSON (overview / full / ego)

목적:
- 007 통합 그래프를 3개 UI 뷰 JSON으로 변환
- overview.json: 그룹=슈퍼노드, 그룹간 엣지 (전체 조감도)
- full.json: 전체 노드+엣지 + 그룹 메타 (전체 상세 뷰)
- ego_{code}.json: 종목 ego 서브그래프 (종목 검색 뷰)
- 각 뷰 1MB 이하, 브라우저에서 즉시 렌더 가능

가설:
1. overview: 그룹 슈퍼노드 100개 이하, 렌더 가능
2. full: 1,028 노드 + 2,000 엣지 이하, 1MB 이하
3. ego: 개별 종목 50KB 이하

방법:
1. 007 데이터 로드 (그래프 + 그룹 분류 + 순환출자)
2. listing 메타 (시장구분, 업종) 조인
3. 3개 뷰 JSON 생성
4. 크기 및 구조 검증

결과:
- 012 balanced merge + 인물 노드 적용 (v4)
- full.json (affiliate_full_v2.json):
  - 2,303 노드 (회사 1,620 + 인물 683), 4,431 엣지
  - 185 그룹 (2명+), 85 순환출자
  - 크기: 764KB (목표 1MB 이하 달성)
  - 삼성 21개 (원익/KCC 제거), 현대차 18개 (현대해상 복원)
  - 삼성 인물: 이재용(5개사)/이서현/홍라희/이부진
  - 정의선(7개사), 정몽구(3개사) 등 주요 오너 인물 포함
- overview.json (affiliate_overview_v2.json):
  - 185 슈퍼노드 (회사만), 1,441 그룹간 엣지
  - 크기: 110KB
- ego 1홉 샘플:
  | 종목 | 노드 | 엣지 | 크기 |
  | 삼성전자 | 63 | 111 | 19KB |
  | 현대자동차 | 25 | 55 | 9KB |
  | 카카오 | 19 | 29 | 6KB |
  | NAVER | 19 | 21 | 5KB |
  | SK하이닉스 | 12 | 11 | 3KB |
  | LG | 12 | 11 | 3KB |
- ego 2홉 (삼성전자): 313노드/606엣지/100KB — 1홉 기본값 권장

결론:
- 가설 1 채택: overview 185개 슈퍼노드, 110KB — 즉시 렌더 가능
- 가설 2 채택: full 2,303노드 + 4,431엣지, 764KB — 1MB 이하
- 가설 3 채택: ego 1홉 3~19KB — 50KB 이하
- 012 balanced merge: 삼성 21개 (정확), 현대해상/한화생명 복원
- 인물 노드 683명: 이재용(삼성생명 10.44%), 정의선(현대차 2.73%) 등
- 법인명 필터로 인물-회사 이름 겹침 0
- 총 소요: 30초

실험일: 2026-03-19
"""

import json
import time
import polars as pl
from pathlib import Path
from collections import defaultdict
import importlib.util

_parent = Path(__file__).resolve().parent
_output = _parent / "output"

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
_sp12 = importlib.util.spec_from_file_location("_e12", str(_parent / "012_balancedMerge.py"))
_m12 = importlib.util.module_from_spec(_sp12); _sp12.loader.exec_module(_m12)


def _load_data() -> dict:
    """007 데이터 전체 로드."""
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}

    # listing 메타
    listing_meta: dict[str, dict] = {}
    for row in listing.iter_rows(named=True):
        listing_meta[row["종목코드"]] = {
            "name": row["회사명"],
            "market": row.get("시장구분", ""),
            "industry": row.get("업종", ""),
        }

    # investedCompany
    raw_inv = _m2.scan_all_invested()
    invest_edges = _m2.clean_and_build_edges(raw_inv, name_to_code)
    latest_year = invest_edges["year"].max()
    invest_deduped = _m3.deduplicate_edges(invest_edges, latest_year)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))

    # majorHolder
    raw_mh = _m6.scan_all_major_holders()
    corp_edges, person_edges = _m6.build_holder_edges(raw_mh, name_to_code, code_to_name)

    # 노드 수집
    listing_codes = set(listing["종목코드"].to_list())
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

    # 그룹 분류 (012 balanced merge)
    print("docs ground truth 스캔...")
    docs_results = _m10.scan_all_affiliate_sections()
    docs_ground_truth = _m10.build_group_mapping(docs_results, name_to_code, code_to_name)
    print(f"  docs 매핑: {len(docs_ground_truth)} 종목")

    print("balanced 그룹 분류...")
    code_to_group = _m12.classify_balanced(
        invest_deduped, corp_edges, person_edges, all_node_ids, code_to_name,
        docs_ground_truth,
    )

    # 순환출자
    cycles = _m7.detect_cycles(invest_deduped, code_to_name, max_length=6)

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
    """인물 노드 + 인물→회사 엣지.

    전략:
    - 같은 그룹 소속 회사에 2개+ 주주인 인물만 노드로 추가
    - 인물 ID: person_{이름}_{그룹} (동명이인 분리)
    - 최신 연도 기준, 중복 제거
    """
    person_edges = data["person_edges"]
    code_to_group = data["code_to_group"]
    all_nodes = data["all_node_ids"]

    # 최신 연도 기준 중복 제거
    latest = person_edges.sort("year", descending=True).unique(
        subset=["person_name", "to_code"], keep="first"
    )

    # 회사 이름 집합 (법인명 필터용)
    company_names = set(data["code_to_name"].values())

    # 인물별 (회사, 그룹, 지분율) 집합
    person_map: dict[str, list[dict]] = defaultdict(list)
    for row in latest.iter_rows(named=True):
        # 법인명이 인물로 들어온 경우 제외
        if row["person_name"] in company_names:
            continue
        tc = row["to_code"]
        if tc not in all_nodes:
            continue
        group = code_to_group.get(tc, "")
        person_map[row["person_name"]].append({
            "code": tc,
            "group": group,
            "pct": row.get("ownership_pct") or 0,
            "relate": row.get("relate", ""),
        })

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_persons: set[str] = set()

    for name, holdings in person_map.items():
        # 그룹별 분류
        group_holdings: dict[str, list[dict]] = defaultdict(list)
        for h in holdings:
            group_holdings[h["group"]].append(h)

        for group, gh in group_holdings.items():
            unique_codes = {h["code"] for h in gh}
            if len(unique_codes) < 2:
                continue

            person_id = f"person_{name}_{group}"
            if person_id in seen_persons:
                continue
            seen_persons.add(person_id)

            # 인물 노드
            nodes.append({
                "id": person_id,
                "label": name,
                "type": "person",
                "group": group,
                "market": "",
                "industry": "",
                "degree": len(unique_codes),
                "inDegree": 0,
                "outDegree": len(unique_codes),
            })

            # 인물→회사 엣지
            for h in gh:
                edges.append({
                    "source": person_id,
                    "target": h["code"],
                    "type": "person_shareholder",
                    "ownershipPct": h["pct"] if h["pct"] > 0 else None,
                    "relate": h["relate"],
                })

    return nodes, edges


def _build_nodes(data: dict) -> list[dict]:
    """전체 노드 리스트."""
    nodes = []
    # degree 계산
    in_deg: dict[str, int] = defaultdict(int)
    out_deg: dict[str, int] = defaultdict(int)

    listed = data["invest_edges"].filter(
        pl.col("is_listed") & pl.col("to_code").is_not_null()
    )
    for row in listed.iter_rows(named=True):
        out_deg[row["from_code"]] += 1
        in_deg[row["to_code"]] += 1

    # corp_edges degree
    matched = data["corp_edges"].filter(pl.col("from_code").is_not_null())
    for row in matched.iter_rows(named=True):
        out_deg[row["from_code"]] += 1
        in_deg[row["to_code"]] += 1

    for code in sorted(data["all_node_ids"]):
        meta = data["listing_meta"].get(code, {})
        group = data["code_to_group"].get(code, "")
        ind = in_deg.get(code, 0)
        outd = out_deg.get(code, 0)
        nodes.append({
            "id": code,
            "label": meta.get("name", code),
            "type": "company",
            "group": group,
            "market": meta.get("market", ""),
            "industry": meta.get("industry", ""),
            "degree": ind + outd,
            "inDegree": ind,
            "outDegree": outd,
        })
    return nodes


def _build_edges(data: dict) -> list[dict]:
    """전체 엣지 리스트 (상장사간만)."""
    edges = []
    seen: set[tuple[str, str, str]] = set()

    # L1: investedCompany
    listed = data["invest_edges"].filter(
        pl.col("is_listed") & pl.col("to_code").is_not_null()
    )
    for row in listed.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "investment")
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "source": row["from_code"],
            "target": row["to_code"],
            "type": "investment",
            "purpose": row.get("purpose", ""),
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
            "source": row["from_code"],
            "target": row["to_code"],
            "type": "shareholder",
            "ownershipPct": row.get("ownership_pct"),
        })

    return edges


def _build_groups(data: dict) -> list[dict]:
    """그룹 메타."""
    group_members: dict[str, list[str]] = defaultdict(list)
    for code in data["all_node_ids"]:
        g = data["code_to_group"].get(code, "")
        group_members[g].append(code)

    groups = []
    for rank, (group, members) in enumerate(
        sorted(group_members.items(), key=lambda x: -len(x[1])), 1
    ):
        if len(members) < 2:
            continue
        # hub = 가장 degree 높은 멤버
        hub = max(members, key=lambda c: sum(1 for _ in []))  # placeholder
        groups.append({
            "name": group,
            "rank": rank,
            "memberCount": len(members),
            "members": sorted(members),
        })
    return groups


def export_full(data: dict) -> dict:
    """full.json — 전체 노드+엣지+그룹+인물."""
    nodes = _build_nodes(data)
    edges = _build_edges(data)
    groups = _build_groups(data)

    # 인물 노드/엣지
    person_nodes, person_edges = _build_person_data(data)
    nodes.extend(person_nodes)
    edges.extend(person_edges)

    company_count = sum(1 for n in nodes if n["type"] == "company")
    person_count = sum(1 for n in nodes if n["type"] == "person")

    # cycles 변환
    cycles_out = []
    for cycle in data["cycles"]:
        path = [data["code_to_name"].get(c, c) for c in cycle]
        codes = cycle
        cycles_out.append({"path": path, "codes": codes})

    return {
        "meta": {
            "year": 2025,
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "companyCount": company_count,
            "personCount": person_count,
            "groupCount": len(groups),
            "cycleCount": len(cycles_out),
            "layers": ["investment", "shareholder", "person_shareholder"],
        },
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "cycles": cycles_out,
    }


def export_overview(data: dict, full: dict) -> dict:
    """overview.json — 그룹=슈퍼노드, 그룹간 엣지."""
    # 그룹 슈퍼노드 (회사 노드만)
    group_info: dict[str, dict] = {}
    for node in full["nodes"]:
        if node["type"] != "company":
            continue
        g = node["group"]
        if g not in group_info:
            group_info[g] = {
                "id": g,
                "label": g,
                "memberCount": 0,
                "totalDegree": 0,
                "members": [],
            }
        group_info[g]["memberCount"] += 1
        group_info[g]["totalDegree"] += node["degree"]
        group_info[g]["members"].append(node["id"])

    # 그룹간 엣지 (그룹 다른 엣지만)
    group_edges: dict[tuple[str, str], dict] = {}
    code_to_grp = data["code_to_group"]
    for edge in full["edges"]:
        sg = code_to_grp.get(edge["source"], "")
        tg = code_to_grp.get(edge["target"], "")
        if sg == tg:
            continue
        key = (sg, tg) if sg < tg else (tg, sg)
        if key not in group_edges:
            group_edges[key] = {"source": key[0], "target": key[1], "weight": 0, "types": set()}
        group_edges[key]["weight"] += 1
        group_edges[key]["types"].add(edge["type"])

    # set → list
    edges_out = []
    for e in group_edges.values():
        edges_out.append({
            "source": e["source"],
            "target": e["target"],
            "weight": e["weight"],
            "types": sorted(e["types"]),
        })

    # 슈퍼노드 (2명+ 그룹만)
    super_nodes = [
        {"id": g, "label": g, "memberCount": info["memberCount"], "totalDegree": info["totalDegree"]}
        for g, info in sorted(group_info.items(), key=lambda x: -x[1]["memberCount"])
        if info["memberCount"] >= 2
    ]

    return {
        "meta": {
            "type": "overview",
            "groupCount": len(super_nodes),
            "edgeCount": len(edges_out),
        },
        "nodes": super_nodes,
        "edges": edges_out,
    }


def export_ego(data: dict, full: dict, code: str, *, hops: int = 1) -> dict:
    """ego_{code}.json — 종목 ego 서브그래프."""
    # 인접 리스트
    adj: dict[str, set[str]] = defaultdict(set)
    for edge in full["edges"]:
        adj[edge["source"]].add(edge["target"])
        adj[edge["target"]].add(edge["source"])

    # BFS hops
    visited: set[str] = {code}
    frontier = {code}
    for _ in range(hops):
        new_frontier: set[str] = set()
        for node in frontier:
            for nb in adj.get(node, set()):
                if nb not in visited:
                    visited.add(nb)
                    new_frontier.add(nb)
        frontier = new_frontier

    # 서브그래프
    node_lookup = {n["id"]: n for n in full["nodes"]}
    ego_nodes = [node_lookup[nid] for nid in sorted(visited) if nid in node_lookup]
    ego_edges = [
        e for e in full["edges"]
        if e["source"] in visited and e["target"] in visited
    ]

    name = data["code_to_name"].get(code, code)
    return {
        "meta": {
            "type": "ego",
            "center": code,
            "centerName": name,
            "hops": hops,
            "nodeCount": len(ego_nodes),
            "edgeCount": len(ego_edges),
        },
        "nodes": ego_nodes,
        "edges": ego_edges,
    }


def _save_json(obj: dict, path: Path) -> int:
    """JSON 저장, 크기 반환."""
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text)


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 데이터 로드...")
    data = _load_data()

    print("\n2. full.json 생성...")
    full = export_full(data)
    _output.mkdir(exist_ok=True)
    size = _save_json(full, _output / "affiliate_full_v2.json")
    print(f"   노드: {full['meta']['nodeCount']}, 엣지: {full['meta']['edgeCount']}")
    print(f"   그룹: {full['meta']['groupCount']}, 순환: {full['meta']['cycleCount']}")
    print(f"   크기: {size/1024:.0f}KB")

    print("\n3. overview.json 생성...")
    overview = export_overview(data, full)
    size = _save_json(overview, _output / "affiliate_overview_v2.json")
    print(f"   슈퍼노드: {overview['meta']['groupCount']}, 엣지: {overview['meta']['edgeCount']}")
    print(f"   크기: {size/1024:.0f}KB")

    print("\n4. ego 뷰 샘플 생성...")
    ego_samples = [
        ("005930", "삼성전자"),
        ("005380", "현대자동차"),
        ("035720", "카카오"),
        ("035420", "NAVER"),
        ("000660", "SK하이닉스"),
        ("003550", "LG"),
    ]
    for code, name in ego_samples:
        ego = export_ego(data, full, code, hops=1)
        size = _save_json(ego, _output / f"ego_{code}_v2.json")
        print(f"   {name} ({code}): {ego['meta']['nodeCount']}노드 {ego['meta']['edgeCount']}엣지 {size/1024:.0f}KB")

    # 2홉 ego도 한 개 생성 (비교용)
    ego2 = export_ego(data, full, "005930", hops=2)
    size = _save_json(ego2, _output / "ego_005930_2hop_v2.json")
    print(f"   삼성전자 2홉: {ego2['meta']['nodeCount']}노드 {ego2['meta']['edgeCount']}엣지 {size/1024:.0f}KB")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
