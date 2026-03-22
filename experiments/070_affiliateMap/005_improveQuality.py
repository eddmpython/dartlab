"""
실험 ID: 005
실험명: 데이터 품질 개선 — 그룹 자동 분류 + 노이즈 제거 + 사용자 뷰

목적:
- 003에서 키워드 기반 그룹 분류 → 연결 컴포넌트 기반 자동 그룹으로 전환
- 자기참조/노이즈 제거
- 사용자가 실제로 쓸 수 있는 3가지 뷰 설계:
  1. ego view: 특정 종목 중심 1~2홉 네트워크
  2. group view: 재벌 그룹 서브그래프
  3. overview: 그룹 간 관계 (그룹을 하나의 슈퍼노드로)

가설:
1. Union-Find 컴포넌트로 그룹 분류하면 미분류율 0%
2. 그룹 라벨을 허브 노드(최다 out-degree) 이름으로 자동 부여 가능
3. ego view는 어떤 종목이든 20초 이내 생성 가능

방법:
1. 경영참여 엣지로 Union-Find → 컴포넌트 = 그룹
2. 그룹 라벨: 컴포넌트 내 최다 out-degree 노드의 '그룹 접두사'
3. 자기참조 + (주1)/(주3) 노이즈 제거
4. ego view / group view / overview JSON 각각 생성

결과 (실험 후 작성):
- Union-Find 자동 그룹: 97개 그룹, 337/910 분류 (37%) — 경영참여 엣지만으로는 부족
- 문제: 단순투자 노드(573개)는 경영참여 컴포넌트에 안 들어감
- ego view 삼성전자: 170 nodes, 212 edges (44KB)
  - 출자 22건: 레인보우로보틱스(35%), 삼성바이오(31.2%), 삼성전기(23.7%)
  - 피출자 17건: 삼성생명(8.51%), 삼성물산(4.4%)
  - 2홉 173건: 간접 연결 (삼성생명→삼성중공업 등)
- ego view 현대자동차: 68 nodes, 87 edges (18KB)
- ego view 카카오: 19 nodes, 20 edges (5KB)
- ego view NAVER: 108 nodes, 119 edges (26KB)
- overview: 97 그룹, 30 그룹간 엣지 (삼성→기아 2건 등)
- 통합 JSON: 247KB

결론:
- 가설 1 기각: 경영참여만으로 Union-Find하면 37% 분류 (0% 미분류 목표 미달)
  → 경영참여 뷰(339 nodes)에서는 100% 분류. 전체 뷰(910)에서만 미분류
- 가설 2 부분 채택: well-known 오버라이드 + 허브 이름 접미사 제거로 삼성/LG/롯데 OK
  → 하지만 "기아"(현대차), "SK디스커버리"(SK) 같은 오명명 발생
- 가설 3 채택: ego view 5초 이내 생성 (20초 목표 초과)

핵심 결론:
- **경영참여 상장사간 뷰**(339 nodes, 273 edges)가 사용자용 메인 뷰로 적합
- **ego view가 킬러 기능** — 종목 검색 → 1~2홉 관계 지도
- 단순투자 포함 전체 뷰(910 nodes)는 그룹 분류 없이 쓰면 스파게티
- 2홉+단순투자 ego는 노드 과다 → 경영참여만 or 1홉 제한 필요
- well-known 오버라이드 dict를 30~50개로 늘리면 주요 그룹 커버 가능

실험일: 2026-03-19
"""

import json
import re
import time
import polars as pl
from pathlib import Path
from collections import defaultdict
import importlib.util

_parent = Path(__file__).resolve().parent
_spec2 = importlib.util.spec_from_file_location("_e2", str(_parent / "002_buildEdges.py"))
_m2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_m2)

_spec3 = importlib.util.spec_from_file_location("_e3", str(_parent / "003_graphAnalysis.py"))
_m3 = importlib.util.module_from_spec(_spec3)
_spec3.loader.exec_module(_m3)


# ── 그룹 자동 분류 (Union-Find 기반) ────────────────────────

# 유명 재벌 라벨 오버라이드 (허브 노드 이름에서 자동 추출이 어려운 경우)
_WELL_KNOWN_GROUPS: dict[str, str] = {
    "005930": "삼성",     # 삼성전자
    "005380": "현대차",   # 현대자동차
    "000270": "기아",     # 기아 → 현대차로 합류
    "051910": "LG",      # LG화학
    "066570": "LG",      # LG전자
    "003550": "LG",      # LG
    "034730": "SK",      # SK
    "017670": "SK",      # SK텔레콤
    "023530": "롯데",    # 롯데지주
    "004170": "신세계",   # 신세계
    "001040": "CJ",      # CJ
    "009150": "삼성",    # 삼성전기
    "032830": "삼성",    # 삼성생명
    "006400": "삼성",    # 삼성SDI
    "028260": "삼성",    # 삼성물산
    "010950": "S-Oil",
    "000720": "현대건설",
    "004020": "현대제철",
    "012330": "현대모비스",
    "003490": "대한항공",
    "180640": "한진",    # 한진칼
}


def auto_group_label(members: list[str], code_to_name: dict[str, str], out_degrees: dict[str, int]) -> str:
    """컴포넌트 멤버에서 그룹 라벨 자동 추출.

    1. 잘 알려진 종목코드가 있으면 그 그룹명
    2. 아니면 최다 out-degree 멤버의 회사명에서 접두사 추출
    """
    # well-known 먼저
    for code in members:
        if code in _WELL_KNOWN_GROUPS:
            return _WELL_KNOWN_GROUPS[code]

    # 최다 out-degree 멤버
    hub = max(members, key=lambda m: out_degrees.get(m, 0))
    name = code_to_name.get(hub, hub)

    # 회사명에서 그룹 접두사 추출 (첫 단어)
    # "한솔홀딩스" → "한솔", "사조대림" → "사조"
    for suffix in ["홀딩스", "지주", "그룹", "금융지주"]:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[:-len(suffix)]

    # 2~3글자면 그대로 사용
    if len(name) <= 4:
        return name

    return name


def build_improved_graph(
    edges: pl.DataFrame,
    listing: pl.DataFrame,
    code_to_name: dict[str, str],
) -> dict:
    """개선된 그래프 데이터 생성."""
    listing_meta = {
        row["종목코드"]: {
            "market": row["시장구분"],
            "industry": row["업종"],
        }
        for row in listing.iter_rows(named=True)
    }

    # 1. 자기참조 제거
    edges = edges.filter(pl.col("from_code") != pl.col("to_code"))

    # 2. 비상장 노드 이름 정규화 — (주1) 등 제거
    # (이건 to_name_norm 에서 처리)

    # 3. 경영참여 상장사간 엣지로 Union-Find
    mgmt_listed = edges.filter(
        (pl.col("purpose") == "경영참여") & pl.col("is_listed")
    )

    uf = _m3.UnionFind()
    for row in mgmt_listed.iter_rows(named=True):
        uf.union(row["from_code"], row["to_code"])

    comps = uf.components()

    # out-degree 계산
    out_deg: dict[str, int] = defaultdict(int)
    for row in mgmt_listed.iter_rows(named=True):
        out_deg[row["from_code"]] += 1

    # 그룹 라벨링
    code_to_group: dict[str, str] = {}
    group_members: dict[str, list[str]] = {}

    for root, members in comps.items():
        label = auto_group_label(members, code_to_name, out_deg)
        for m in members:
            code_to_group[m] = label
        group_members[label] = group_members.get(label, []) + members

    # 4. 전체 상장사간 엣지 (경영참여 그룹 + 단순투자도 포함)
    all_listed = edges.filter(pl.col("is_listed"))

    # 경영참여 그룹에 없는 노드도 단순투자로 등장 → "기타" 그룹
    all_node_ids: set[str] = set()
    for row in all_listed.iter_rows(named=True):
        all_node_ids.add(row["from_code"])
        if row["to_code"]:
            all_node_ids.add(row["to_code"])

    # 5. 노드 구축
    nodes = []
    for nid in sorted(all_node_ids):
        name = code_to_name.get(nid, nid)
        meta = listing_meta.get(nid, {})
        group = code_to_group.get(nid)

        node: dict = {
            "id": nid,
            "label": name,
            "isListed": nid in listing_meta,
        }
        if meta.get("market"):
            node["market"] = meta["market"]
        if meta.get("industry"):
            node["industry"] = meta["industry"]
        if group:
            node["group"] = group
        nodes.append(node)

    # 6. 엣지 구축
    edge_list = []
    seen: set[tuple] = set()
    for row in all_listed.iter_rows(named=True):
        if not row["to_code"]:
            continue
        if row["from_code"] == row["to_code"]:
            continue
        key = (row["from_code"], row["to_code"])
        if key in seen:
            continue
        seen.add(key)

        e: dict = {
            "source": row["from_code"],
            "target": row["to_code"],
            "purpose": row["purpose"],
        }
        if row["ownership_pct"] is not None:
            e["ownershipPct"] = round(row["ownership_pct"], 2)
        if row["book_value"] is not None and row["book_value"] > 0:
            e["bookValue"] = int(row["book_value"])
        edge_list.append(e)

    # 그룹 통계
    group_counts: dict[str, int] = defaultdict(int)
    for n in nodes:
        group_counts[n.get("group", "(미분류)")] += 1

    return {
        "nodes": nodes,
        "edges": edge_list,
        "groups": dict(group_counts),
        "code_to_group": code_to_group,
    }


def build_ego_view(
    edges: pl.DataFrame,
    code_to_name: dict[str, str],
    listing_meta: dict[str, dict],
    stock_code: str,
    *,
    hops: int = 2,
) -> dict:
    """특정 종목 중심 ego 네트워크."""
    all_listed = edges.filter(pl.col("is_listed"))

    # 엣지를 adjacency로 변환
    adj: dict[str, list[dict]] = defaultdict(list)
    for row in all_listed.iter_rows(named=True):
        if not row["to_code"] or row["from_code"] == row["to_code"]:
            continue
        adj[row["from_code"]].append(row)
        # 역방향도 (피출자→출자 방향으로 탐색)
        adj[row["to_code"]].append(row)

    # BFS
    visited: set[str] = {stock_code}
    frontier: set[str] = {stock_code}
    collected_edges: list[dict] = []

    for hop in range(hops):
        next_frontier: set[str] = set()
        for node in frontier:
            for row in adj.get(node, []):
                other = row["to_code"] if row["from_code"] == node else row["from_code"]
                if other and other not in visited:
                    next_frontier.add(other)
                    visited.add(other)
                # 엣지 수집
                key = (row["from_code"], row["to_code"])
                collected_edges.append(key)
        frontier = next_frontier

    # 중복 제거
    unique_edges: set[tuple] = set()
    for key in collected_edges:
        unique_edges.add(key)

    # 노드/엣지 조립
    nodes = []
    for nid in sorted(visited):
        name = code_to_name.get(nid, nid)
        meta = listing_meta.get(nid, {})
        node: dict = {
            "id": nid,
            "label": name,
            "isCenter": nid == stock_code,
        }
        if meta.get("market"):
            node["market"] = meta["market"]
        nodes.append(node)

    edge_list = []
    for row in all_listed.iter_rows(named=True):
        if not row["to_code"] or row["from_code"] == row["to_code"]:
            continue
        key = (row["from_code"], row["to_code"])
        if key not in unique_edges:
            continue
        if row["from_code"] not in visited or row["to_code"] not in visited:
            continue
        unique_edges.discard(key)  # 중복 방지
        e: dict = {
            "source": row["from_code"],
            "target": row["to_code"],
            "purpose": row["purpose"],
        }
        if row["ownership_pct"] is not None:
            e["ownershipPct"] = round(row["ownership_pct"], 2)
        edge_list.append(e)

    return {
        "meta": {
            "center": stock_code,
            "centerLabel": code_to_name.get(stock_code, stock_code),
            "hops": hops,
            "nodeCount": len(nodes),
            "edgeCount": len(edge_list),
        },
        "nodes": nodes,
        "edges": edge_list,
    }


def build_overview(graph: dict) -> dict:
    """그룹을 슈퍼노드로 압축한 조감도."""
    code_to_group = graph["code_to_group"]

    # 그룹 간 엣지 집계
    group_edges: dict[tuple, dict] = {}
    for e in graph["edges"]:
        src_group = code_to_group.get(e["source"], "(미분류)")
        tgt_group = code_to_group.get(e["target"], "(미분류)")
        if src_group == tgt_group:
            continue  # 그룹 내부 엣지 제외
        key = (src_group, tgt_group)
        if key not in group_edges:
            group_edges[key] = {"count": 0, "totalPct": 0, "pctCount": 0}
        group_edges[key]["count"] += 1
        if e.get("ownershipPct"):
            group_edges[key]["totalPct"] += e["ownershipPct"]
            group_edges[key]["pctCount"] += 1

    # 그룹 노드
    group_counts = graph["groups"]
    group_nodes = []
    for g, cnt in sorted(group_counts.items(), key=lambda x: -x[1]):
        if g == "(미분류)":
            continue
        group_nodes.append({
            "id": g,
            "label": g,
            "memberCount": cnt,
        })

    # 그룹 엣지 (미분류 제외)
    overview_edges = []
    for (src, tgt), info in group_edges.items():
        if src == "(미분류)" or tgt == "(미분류)":
            continue
        e = {
            "source": src,
            "target": tgt,
            "edgeCount": info["count"],
        }
        if info["pctCount"] > 0:
            e["avgOwnershipPct"] = round(info["totalPct"] / info["pctCount"], 1)
        overview_edges.append(e)

    overview_edges.sort(key=lambda x: -x["edgeCount"])

    return {
        "meta": {
            "view": "group_overview",
            "groupCount": len(group_nodes),
            "interGroupEdges": len(overview_edges),
        },
        "nodes": group_nodes,
        "edges": overview_edges,
    }


if __name__ == "__main__":
    t0 = time.perf_counter()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)

    print("1. 데이터 로드...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}
    listing_meta = {
        row["종목코드"]: {"market": row["시장구분"], "industry": row["업종"]}
        for row in listing.iter_rows(named=True)
    }
    raw = _m2.scan_all_invested()
    edges = _m2.clean_and_build_edges(raw, name_to_code)
    latest_year = edges["year"].max()
    deduped = _m3.deduplicate_edges(edges, latest_year)
    print(f"   {latest_year}년 엣지: {len(deduped):,}")

    # 2. 개선된 그래프
    print("\n2. 그래프 개선 (자동 그룹, 노이즈 제거)...")
    graph = build_improved_graph(deduped, listing, code_to_name)
    print(f"   노드: {len(graph['nodes'])}, 엣지: {len(graph['edges'])}")

    # 그룹 분류 현황
    classified = sum(1 for n in graph["nodes"] if n.get("group"))
    total = len(graph["nodes"])
    print(f"   그룹 분류: {classified}/{total} ({classified/total:.0%})")
    print(f"   그룹 수: {len([g for g in graph['groups'] if g != '(미분류)'])}")
    print(f"   그룹 분포:")
    for g, cnt in sorted(graph["groups"].items(), key=lambda x: -x[1])[:20]:
        print(f"     {g:15s}: {cnt}")

    # 3. Ego views
    print("\n3. Ego views...")
    test_codes = [
        ("005930", "삼성전자"),
        ("005380", "현대자동차"),
        ("035720", "카카오"),
        ("035420", "NAVER"),
    ]
    for code, label in test_codes:
        ego = build_ego_view(deduped, code_to_name, listing_meta, code, hops=2)
        path = out_dir / f"ego_{code}.json"
        text = json.dumps(ego, ensure_ascii=False, indent=2)
        path.write_text(text, encoding="utf-8")
        size = len(text.encode("utf-8")) / 1024
        print(f"   {label}: {ego['meta']['nodeCount']} nodes, {ego['meta']['edgeCount']} edges ({size:.0f}KB)")

    # 4. Overview
    print("\n4. Overview (그룹 슈퍼노드)...")
    overview = build_overview(graph)
    path = out_dir / "overview.json"
    text = json.dumps(overview, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    print(f"   {overview['meta']['groupCount']} groups, {overview['meta']['interGroupEdges']} inter-group edges")
    print(f"   그룹간 엣지 TOP 10:")
    for e in overview["edges"][:10]:
        avg = f" (avg {e['avgOwnershipPct']}%)" if "avgOwnershipPct" in e else ""
        print(f"     {e['source']} → {e['target']}: {e['edgeCount']}건{avg}")

    # 5. 최종 통합 JSON
    print("\n5. 최종 통합 JSON...")
    final = {
        "meta": {
            "year": latest_year,
            "generatedAt": "2026-03-19",
            "views": ["full", "overview", "ego"],
            "totalNodes": len(graph["nodes"]),
            "totalEdges": len(graph["edges"]),
            "groupCount": overview["meta"]["groupCount"],
        },
        "full": {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
        },
        "overview": overview,
    }
    final_path = out_dir / "affiliate_v2.json"
    final_text = json.dumps(final, ensure_ascii=False)
    final_path.write_text(final_text, encoding="utf-8")
    size = len(final_text.encode("utf-8")) / 1024
    print(f"   {final_path.name}: {size:.0f}KB")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
