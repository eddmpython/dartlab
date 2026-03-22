"""
실험 ID: 004
실험명: UI 레이어용 JSON 데이터 생성 — 노드/엣지/메타

목적:
- 003에서 분석한 그래프 데이터를 UI에서 소비할 수 있는 JSON으로 변환
- 3가지 뷰 제공:
  A) 경영참여 + 상장사간 (compact, 339 노드)
  B) 전체 상장사간 (medium, 911 노드)
  C) 재벌 클러스터별 (비상장 포함, 상세)
- force-directed graph (D3.js / vis.js / Cytoscape.js) 소비 포맷

가설:
1. 경영참여 상장사간 뷰 JSON이 1MB 이하로 UI에서 충분히 렌더 가능
2. 노드에 시장구분/업종/그룹 라벨을 붙이면 시각적 클러스터 구분 가능
3. 재벌별 서브그래프 추출이 UI 필터로 활용 가능

방법:
1. listing 메타 (시장구분, 업종, 지역) 노드에 부착
2. Union-Find로 그룹 라벨 자동 부여
3. JSON 스키마: {nodes: [...], edges: [...], meta: {...}}
4. 파일 크기 + 노드/엣지 수 검증

결과 (실험 후 작성):
- 뷰 A (경영참여+상장사간): 339 nodes, 273 edges → 101KB
- 뷰 B (전체 상장사간): 911 nodes, 1,058 edges → 310KB
- 뷰 C (재벌 클러스터 19개): 1,903 nodes, 1,924 edges → 619KB
- 통합 파일: 713KB
- 재벌 그룹 TOP5: 삼성(360n/380e), LG(244/238), 현대차(243/275), SK(232/227), 롯데(139/137)
- 노드 속성: id, label, isListed, market, industry, group
- 엣지 속성: source, target, purpose, ownershipPct, bookValue
- 총 소요: 6.0초

결론:
- 가설 1 채택: 경영참여 상장사간 101KB (1MB 이하, 프론트에서 여유롭게 렌더 가능)
- 가설 2 채택: group 라벨로 삼성/현대/SK/LG 등 시각적 클러스터 구분 가능
- 가설 3 채택: 19개 재벌 서브그래프, UI 드롭다운 필터로 활용 가능
- 3개 뷰가 모두 D3/Cytoscape/vis.js 소비 포맷 (nodes+edges array)

실험일: 2026-03-19
"""

import importlib.util
import json
import time
from collections import defaultdict
from pathlib import Path

import polars as pl

# 002, 003 임포트
_parent = Path(__file__).resolve().parent
_spec2 = importlib.util.spec_from_file_location("_e2", str(_parent / "002_buildEdges.py"))
_m2 = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_m2)

_spec3 = importlib.util.spec_from_file_location("_e3", str(_parent / "003_graphAnalysis.py"))
_m3 = importlib.util.module_from_spec(_spec3)
_spec3.loader.exec_module(_m3)


# ── 그룹 라벨링 ─────────────────────────────────────────────

# 재벌 키워드 → 그룹명 (경영참여 기반 클러스터와 대응)
_GROUP_KEYWORDS: dict[str, list[str]] = {
    "삼성": ["삼성", "Samsung", "SAMSUNG"],
    "현대차": ["현대자동차", "현대모비스", "기아", "현대건설", "현대글로비스", "현대로템",
              "현대오토에버", "현대위아", "현대제철", "현대차증권"],
    "SK": ["SK", "에스케이"],
    "LG": ["LG", "엘지"],
    "롯데": ["롯데", "LOTTE"],
    "한화": ["한화", "Hanwha"],
    "GS": ["GS"],
    "HD현대": ["HD현대", "현대중공업", "HD한국조선"],
    "포스코": ["포스코", "POSCO"],
    "CJ": ["CJ", "씨제이"],
    "두산": ["두산", "Doosan"],
    "LS": ["LS", "엘에스"],
    "카카오": ["카카오", "Kakao"],
    "네이버": ["NAVER", "네이버"],
    "효성": ["효성"],
    "한솔": ["한솔"],
    "사조": ["사조"],
    "녹십자": ["녹십자", "지씨셀", "지씨지놈"],
    "하림": ["하림", "팜스코", "선진", "팬오션"],
    "KG": ["KG"],
}


def _detect_group(name: str) -> str | None:
    """회사명으로 재벌그룹 추정."""
    for group, keywords in _GROUP_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return group
    return None


def build_nodes(
    edges: pl.DataFrame,
    listing: pl.DataFrame,
    code_to_name: dict[str, str],
    *,
    listed_only: bool = True,
) -> list[dict]:
    """노드 리스트 생성."""
    # listing 메타
    listing_meta: dict[str, dict] = {}
    for row in listing.iter_rows(named=True):
        listing_meta[row["종목코드"]] = {
            "market": row["시장구분"],
            "industry": row["업종"],
            "region": row["지역"],
        }

    # 엣지에서 모든 노드 수집
    node_ids: set[str] = set()
    for row in edges.iter_rows(named=True):
        node_ids.add(row["from_code"])
        if listed_only:
            if row["is_listed"] and row["to_code"]:
                node_ids.add(row["to_code"])
        else:
            node_ids.add(row["to_code"] if row["to_code"] else row["to_name_norm"])

    # 노드 구축
    nodes = []
    for nid in sorted(node_ids):
        is_stock = len(nid) == 6 and nid.isdigit()
        name = code_to_name.get(nid, nid)
        meta = listing_meta.get(nid, {})
        group = _detect_group(name)

        node: dict = {
            "id": nid,
            "label": name,
            "isListed": is_stock and nid in listing_meta,
        }
        if meta.get("market"):
            node["market"] = meta["market"]
        if meta.get("industry"):
            node["industry"] = meta["industry"]
        if group:
            node["group"] = group

        # 출자 관계에서 size 힌트 (out-degree)
        nodes.append(node)

    return nodes


def build_edge_list(
    edges: pl.DataFrame,
    *,
    listed_only: bool = True,
) -> list[dict]:
    """엣지 리스트 생성."""
    result = []
    seen: set[tuple] = set()

    for row in edges.iter_rows(named=True):
        from_id = row["from_code"]

        if listed_only:
            if not row["is_listed"] or not row["to_code"]:
                continue
            to_id = row["to_code"]
        else:
            to_id = row["to_code"] if row["to_code"] else row["to_name_norm"]

        key = (from_id, to_id)
        if key in seen:
            continue
        seen.add(key)

        edge: dict = {
            "source": from_id,
            "target": to_id,
            "purpose": row["purpose"],
        }
        if row["ownership_pct"] is not None:
            edge["ownershipPct"] = round(row["ownership_pct"], 2)
        if row["book_value"] is not None and row["book_value"] > 0:
            edge["bookValue"] = int(row["book_value"])

        result.append(edge)

    return result


def build_chaebol_subgraphs(
    edges: pl.DataFrame,
    listing: pl.DataFrame,
    code_to_name: dict[str, str],
) -> dict[str, dict]:
    """재벌별 서브그래프 (비상장 포함)."""
    listing_meta = {
        row["종목코드"]: row for row in listing.iter_rows(named=True)
    }

    mgmt = edges.filter(pl.col("purpose") == "경영참여")
    subgraphs: dict[str, dict] = {}

    for group_name, keywords in _GROUP_KEYWORDS.items():
        # 그룹 출자회사 찾기
        group_from: set[str] = set()
        for row in mgmt.iter_rows(named=True):
            from_name = code_to_name.get(row["from_code"], "")
            if any(kw in from_name for kw in keywords):
                group_from.add(row["from_code"])

        if not group_from:
            continue

        group_edges = mgmt.filter(pl.col("from_code").is_in(list(group_from)))

        # 노드 수집
        nodes = []
        node_ids: set[str] = set()
        for row in group_edges.iter_rows(named=True):
            # from
            if row["from_code"] not in node_ids:
                node_ids.add(row["from_code"])
                name = code_to_name.get(row["from_code"], row["from_code"])
                nodes.append({
                    "id": row["from_code"],
                    "label": name,
                    "isListed": True,
                    "role": "investor",
                })
            # to
            to_id = row["to_code"] if row["to_code"] else row["to_name_norm"]
            if to_id not in node_ids:
                node_ids.add(to_id)
                nodes.append({
                    "id": to_id,
                    "label": row["to_name_norm"],
                    "isListed": row["is_listed"],
                    "role": "investee",
                })

        # 엣지
        edge_list = []
        seen: set[tuple] = set()
        for row in group_edges.iter_rows(named=True):
            to_id = row["to_code"] if row["to_code"] else row["to_name_norm"]
            key = (row["from_code"], to_id)
            if key in seen:
                continue
            seen.add(key)
            e: dict = {"source": row["from_code"], "target": to_id}
            if row["ownership_pct"] is not None:
                e["ownershipPct"] = round(row["ownership_pct"], 2)
            if row["book_value"] is not None and row["book_value"] > 0:
                e["bookValue"] = int(row["book_value"])
            edge_list.append(e)

        subgraphs[group_name] = {
            "group": group_name,
            "investorCount": len(group_from),
            "nodeCount": len(nodes),
            "edgeCount": len(edge_list),
            "listedCount": sum(1 for n in nodes if n["isListed"]),
            "nodes": nodes,
            "edges": edge_list,
        }

    return subgraphs


def export_json(data: dict, path: Path, label: str) -> None:
    """JSON 파일 저장 + 크기 출력."""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    size_kb = len(text.encode("utf-8")) / 1024
    print(f"  {label}: {path.name} ({size_kb:.0f}KB, {data.get('meta', {}).get('nodeCount', '?')} nodes, {data.get('meta', {}).get('edgeCount', '?')} edges)")


if __name__ == "__main__":
    t0 = time.perf_counter()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)

    print("1. 데이터 로드...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}
    raw = _m2.scan_all_invested()
    edges = _m2.clean_and_build_edges(raw, name_to_code)

    latest_year = edges["year"].max()
    deduped = _m3.deduplicate_edges(edges, latest_year)
    print(f"   {latest_year}년 중복 제거: {len(deduped):,} 엣지")

    # ── A) 경영참여 + 상장사간 (compact) ──
    print("\n2. 뷰 A: 경영참여 + 상장사간...")
    mgmt_listed = deduped.filter(
        (pl.col("purpose") == "경영참여") & pl.col("is_listed")
    )
    nodes_a = build_nodes(mgmt_listed, listing, code_to_name, listed_only=True)
    edges_a = build_edge_list(mgmt_listed, listed_only=True)
    data_a = {
        "meta": {
            "view": "management_listed",
            "year": latest_year,
            "description": "경영참여 출자, 상장사 간 네트워크",
            "nodeCount": len(nodes_a),
            "edgeCount": len(edges_a),
        },
        "nodes": nodes_a,
        "edges": edges_a,
    }
    export_json(data_a, out_dir / "affiliate_mgmt_listed.json", "A")

    # ── B) 전체 상장사간 ──
    print("\n3. 뷰 B: 전체 상장사간...")
    all_listed = deduped.filter(pl.col("is_listed"))
    nodes_b = build_nodes(all_listed, listing, code_to_name, listed_only=True)
    edges_b = build_edge_list(all_listed, listed_only=True)
    data_b = {
        "meta": {
            "view": "all_listed",
            "year": latest_year,
            "description": "전체 출자 (경영참여+단순투자), 상장사 간 네트워크",
            "nodeCount": len(nodes_b),
            "edgeCount": len(edges_b),
        },
        "nodes": nodes_b,
        "edges": edges_b,
    }
    export_json(data_b, out_dir / "affiliate_all_listed.json", "B")

    # ── C) 재벌 클러스터별 ──
    print("\n4. 뷰 C: 재벌 클러스터별 서브그래프...")
    subgraphs = build_chaebol_subgraphs(deduped, listing, code_to_name)
    data_c = {
        "meta": {
            "view": "chaebol_subgraphs",
            "year": latest_year,
            "description": "재벌 그룹별 경영참여 출자 네트워크 (비상장 포함)",
            "groupCount": len(subgraphs),
            "totalNodes": sum(g["nodeCount"] for g in subgraphs.values()),
            "totalEdges": sum(g["edgeCount"] for g in subgraphs.values()),
        },
        "groups": subgraphs,
    }
    # meta에 nodeCount/edgeCount도 추가
    data_c["meta"]["nodeCount"] = data_c["meta"]["totalNodes"]
    data_c["meta"]["edgeCount"] = data_c["meta"]["totalEdges"]
    export_json(data_c, out_dir / "affiliate_chaebol.json", "C")

    # 재벌별 요약
    print(f"\n  재벌 그룹 {len(subgraphs)}개:")
    for name, g in sorted(subgraphs.items(), key=lambda x: -x[1]["nodeCount"]):
        print(f"    {name:8s}: {g['nodeCount']:4d} nodes, {g['edgeCount']:4d} edges (상장 {g['listedCount']})")

    # ── D) 전체 통합 (3개 뷰 하나의 파일) ──
    print("\n5. 통합 파일...")
    combined = {
        "meta": {
            "year": latest_year,
            "generatedAt": "2026-03-19",
            "views": ["management_listed", "all_listed", "chaebol_subgraphs"],
        },
        "managementListed": data_a,
        "allListed": data_b,
        "chaebolSubgraphs": data_c,
    }
    combined_text = json.dumps(combined, ensure_ascii=False)
    combined_path = out_dir / "affiliate_graph.json"
    combined_path.write_text(combined_text, encoding="utf-8")
    size_kb = len(combined_text.encode("utf-8")) / 1024
    print(f"  통합: {combined_path.name} ({size_kb:.0f}KB)")

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
