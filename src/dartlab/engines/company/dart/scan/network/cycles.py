"""순환출자 DFS 탐지."""

from __future__ import annotations

from collections import defaultdict

import polars as pl


def detect_cycles(
    invest_edges: pl.DataFrame,
    code_to_name: dict[str, str],
    *,
    max_length: int = 6,
) -> list[list[str]]:
    """상장사간 directed graph에서 순환출자 DFS 탐지."""
    adj: dict[str, list[str]] = defaultdict(list)
    listed = invest_edges.filter(
        pl.col("is_listed") & pl.col("to_code").is_not_null() & (pl.col("from_code") != pl.col("to_code"))
    )
    for row in listed.iter_rows(named=True):
        adj[row["from_code"]].append(row["to_code"])

    cycles: list[list[str]] = []
    visited_global: set[str] = set()

    def dfs(node: str, path: list[str], path_set: set[str]) -> None:
        if len(path) > max_length:
            return
        for nb in adj.get(node, []):
            if nb == path[0] and len(path) >= 2:
                cycles.append(path + [nb])
            elif nb not in path_set and nb not in visited_global:
                path.append(nb)
                path_set.add(nb)
                dfs(nb, path, path_set)
                path.pop()
                path_set.discard(nb)

    for start in sorted(adj.keys()):
        if start in visited_global:
            continue
        dfs(start, [start], {start})
        visited_global.add(start)

    unique: list[list[str]] = []
    seen: set[frozenset[str]] = set()
    for cycle in cycles:
        key = frozenset(cycle[:-1])
        if key not in seen:
            seen.add(key)
            unique.append(cycle)
    return unique
