"""한국 상장사 관계 지도 — 출자/지분/인적 관계 그래프.

Public API:
    build_graph()        → data dict (전체 파이프라인)
    export_full(data)    → full JSON dict
    export_overview(data, full) → overview JSON dict
    export_ego(data, full, code) → ego JSON dict
"""

from __future__ import annotations

import time

import polars as pl

from dartlab.engines.dart.affiliate.classifier import classify_balanced
from dartlab.engines.dart.affiliate.cycles import detect_cycles
from dartlab.engines.dart.affiliate.edges import (
    build_holder_edges,
    build_invest_edges,
    deduplicate_edges,
)
from dartlab.engines.dart.affiliate.export import (
    export_ego,
    export_full,
    export_overview,
)
from dartlab.engines.dart.affiliate.scanner import (
    load_listing,
    scan_invested,
    scan_major_holders,
)
from dartlab.engines.dart.affiliate.scanner import (
    scan_affiliate_docs as _scan_affiliate_docs_fn,
)


def build_graph(*, verbose: bool = True) -> dict:
    """전체 파이프라인 실행 → data dict.

    Returns:
        dict with keys: listing_meta, code_to_name, code_to_group,
        invest_edges, corp_edges, person_edges, all_node_ids, cycles
    """
    t0 = time.perf_counter()

    def _log(msg: str) -> None:
        if verbose:
            print(msg)

    _log("1. 상장사 목록...")
    name_to_code, code_to_name, listing_codes, listing_meta = load_listing()

    _log("2. investedCompany 스캔...")
    raw_inv = scan_invested()
    invest_edges = build_invest_edges(raw_inv, name_to_code, code_to_name)
    invest_deduped = deduplicate_edges(invest_edges)
    invest_deduped = invest_deduped.filter(pl.col("from_code") != pl.col("to_code"))
    _log(f"   → {len(invest_deduped):,} edges")

    _log("3. majorHolder 스캔...")
    raw_mh = scan_major_holders()
    corp_edges, person_edges = build_holder_edges(raw_mh, name_to_code)
    _log(f"   → corp {len(corp_edges):,}, person {len(person_edges):,}")

    # 노드 수집
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
    _log(f"   → {len(all_node_ids)} 상장사 노드")

    _log("4. docs ground truth...")
    docs_gt = _scan_affiliate_docs_fn(name_to_code, code_to_name)
    _log(f"   → {len(docs_gt)} 종목 매핑")

    _log("5. 균형 분류...")
    code_to_group = classify_balanced(
        invest_deduped,
        corp_edges,
        person_edges,
        all_node_ids,
        code_to_name,
        docs_gt,
        verbose=verbose,
    )

    _log("6. 순환출자 탐지...")
    cycles = detect_cycles(invest_deduped, code_to_name, max_length=6)
    _log(f"   → {len(cycles)}개")

    elapsed = time.perf_counter() - t0
    _log(f"\n파이프라인 완료: {elapsed:.1f}초")

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


__all__ = [
    "build_graph",
    "export_full",
    "export_overview",
    "export_ego",
]
