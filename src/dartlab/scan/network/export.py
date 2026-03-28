"""JSON 내보내기 — full, overview, ego (v4 보강 포맷)."""

from __future__ import annotations

from collections import Counter, defaultdict

import polars as pl

# ── 내부 빌더 ─────────────────────────────────────────────


def _build_enriched_edges(data: dict) -> list[dict]:
    """회사 엣지 — 모든 투자 목적(경영참여+단순투자+기타) 포함."""
    edges: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    # L1: investedCompany — 모든 목적
    listed = data["invest_edges"].filter(pl.col("is_listed") & pl.col("to_code").is_not_null())
    for row in listed.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "investment")
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            {
                "source": row["from_code"],
                "target": row["to_code"],
                "type": "investment",
                "purpose": row.get("purpose", ""),
                "ownershipPct": row.get("ownership_pct"),
            }
        )

    # L2: majorHolder 법인
    matched = data["corp_edges"].filter(pl.col("from_code").is_not_null())
    for row in matched.iter_rows(named=True):
        key = (row["from_code"], row["to_code"], "shareholder")
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            {
                "source": row["from_code"],
                "target": row["to_code"],
                "type": "shareholder",
                "ownershipPct": row.get("ownership_pct"),
            }
        )

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
        nodes.append(
            {
                "id": code,
                "label": meta.get("name", code),
                "type": "company",
                "group": data["code_to_group"].get(code, ""),
                "market": meta.get("market", ""),
                "industry": meta.get("industry", ""),
                "degree": ind + outd,
                "inDegree": ind,
                "outDegree": outd,
            }
        )
    return nodes


def _build_person_data(data: dict) -> tuple[list[dict], list[dict]]:
    """인물 노드 + 인물→회사 엣지."""
    person_edges = data["person_edges"]
    code_to_group = data["code_to_group"]
    all_nodes = data["all_node_ids"]
    company_names = set(data["code_to_name"].values())

    latest = person_edges.sort("year", descending=True).unique(subset=["person_name", "to_code"], keep="first")

    person_map: dict[str, list[dict]] = defaultdict(list)
    for row in latest.iter_rows(named=True):
        if row["person_name"] in company_names:
            continue
        tc = row["to_code"]
        if tc not in all_nodes:
            continue
        person_map[row["person_name"]].append(
            {
                "code": tc,
                "group": code_to_group.get(tc, ""),
                "pct": row.get("ownership_pct") or 0,
                "relate": row.get("relate", ""),
            }
        )

    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()

    for name, holdings in person_map.items():
        gh: dict[str, list[dict]] = defaultdict(list)
        for h in holdings:
            gh[h["group"]].append(h)
        for group, items in gh.items():
            unique_codes = {h["code"] for h in items}
            if len(unique_codes) < 2:
                continue
            pid = f"person_{name}_{group}"
            if pid in seen:
                continue
            seen.add(pid)
            nodes.append(
                {
                    "id": pid,
                    "label": name,
                    "type": "person",
                    "group": group,
                    "market": "",
                    "industry": "",
                    "degree": len(unique_codes),
                    "inDegree": 0,
                    "outDegree": len(unique_codes),
                }
            )
            for h in items:
                edges.append(
                    {
                        "source": pid,
                        "target": h["code"],
                        "type": "person_shareholder",
                        "ownershipPct": h["pct"] if h["pct"] > 0 else None,
                        "relate": h["relate"],
                    }
                )
    return nodes, edges


# ── public export 함수 ────────────────────────────────────


def export_full(data: dict) -> dict:
    """full JSON — 전체 노드+엣지+그룹+업종+인물+순환출자."""
    edges = _build_enriched_edges(data)
    nodes = _build_enriched_nodes(data, edges)

    # 인물 노드/엣지
    pn, pe = _build_person_data(data)
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
    cycles_out = [{"path": [data["code_to_name"].get(c, c) for c in cy], "codes": cy} for cy in data["cycles"]]

    cc = sum(1 for n in nodes if n["type"] == "company")
    pc = sum(1 for n in nodes if n["type"] == "person")

    edge_types = Counter(e["type"] for e in edges)
    purpose_counts = Counter(e.get("purpose", "") for e in edges if e["type"] == "investment")

    return {
        "meta": {
            "year": 2025,
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "companyCount": cc,
            "personCount": pc,
            "groupCount": len(groups),
            "industryCount": len(industries),
            "cycleCount": len(cycles_out),
            "edgeTypes": dict(edge_types),
            "investmentPurposes": dict(purpose_counts),
            "layers": ["investment", "shareholder", "person_shareholder"],
        },
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "industries": industries,
        "cycles": cycles_out,
    }


def export_overview(data: dict, full: dict) -> dict:
    """overview JSON — 그룹 슈퍼노드."""
    gi: dict[str, dict] = {}
    for node in full["nodes"]:
        if node["type"] != "company":
            continue
        g = node["group"]
        if g not in gi:
            gi[g] = {"id": g, "label": g, "memberCount": 0, "totalDegree": 0, "members": []}
        gi[g]["memberCount"] += 1
        gi[g]["totalDegree"] += node["degree"]
        gi[g]["members"].append(node["id"])

    ge: dict[tuple[str, str], dict] = {}
    ctg = data["code_to_group"]
    for edge in full["edges"]:
        sg, tg = ctg.get(edge["source"], ""), ctg.get(edge["target"], "")
        if sg == tg:
            continue
        key = (sg, tg) if sg < tg else (tg, sg)
        if key not in ge:
            ge[key] = {"source": key[0], "target": key[1], "weight": 0, "types": set()}
        ge[key]["weight"] += 1
        ge[key]["types"].add(edge["type"])

    edges_out = [
        {"source": e["source"], "target": e["target"], "weight": e["weight"], "types": sorted(e["types"])}
        for e in ge.values()
    ]
    super_nodes = [
        {"id": g, "label": g, "memberCount": info["memberCount"], "totalDegree": info["totalDegree"]}
        for g, info in sorted(gi.items(), key=lambda x: -x[1]["memberCount"])
        if info["memberCount"] >= 2
    ]

    return {
        "meta": {"type": "overview", "groupCount": len(super_nodes), "edgeCount": len(edges_out)},
        "nodes": super_nodes,
        "edges": edges_out,
    }


def export_ego(
    data: dict,
    full: dict,
    code: str,
    *,
    hops: int = 1,
    include_industry: bool = True,
    max_industry_peers: int = 10,
) -> dict:
    """ego 뷰 — 독립 회사면 같은 업종 이웃도 포함."""
    # BFS ego
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

    # 업종 이웃 추가 (연결 적은 회사)
    industry_peers_added = 0
    if include_industry and len(visited) <= 3:
        center_meta = data["listing_meta"].get(code, {})
        center_industry = center_meta.get("industry", "")
        if center_industry:
            peers = [
                n
                for n in full["nodes"]
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
    ego_edges = [e for e in full["edges"] if e["source"] in visited and e["target"] in visited]

    name = data["code_to_name"].get(code, code)
    center_meta = data["listing_meta"].get(code, {})

    return {
        "meta": {
            "type": "ego",
            "center": code,
            "centerName": name,
            "centerIndustry": center_meta.get("industry", ""),
            "hops": hops,
            "nodeCount": len(ego_nodes),
            "edgeCount": len(ego_edges),
            "industryPeersAdded": industry_peers_added,
        },
        "nodes": ego_nodes,
        "edges": ego_edges,
    }
