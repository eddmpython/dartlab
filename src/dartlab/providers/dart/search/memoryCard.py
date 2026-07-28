"""LLM memory-card helpers for product search results."""

from __future__ import annotations

import json
from typing import Any

import polars as pl

from dartlab.providers.dart.search.coerce import _isFalse


def buildMemoryCards(df: pl.DataFrame, *, query: str = "", limit: int = 3) -> list[dict[str, Any]]:
    """Convert top answerable search rows into compact LLM memory cards.

    Args:
        df: Product search result DataFrame.
        query: Query that produced the results.
        limit: Maximum cards to return.

    Returns:
        list[dict[str, Any]]: LLM-ready evidence cards.

    Raises:
        None.

    Example:
        >>> buildMemoryCards(pl.DataFrame())
        []
    """
    if df is None or df.height == 0 or "info" in df.columns:
        return []
    cards: list[dict[str, Any]] = []
    for row in df.iter_rows(named=True):
        if _isFalse(row.get("answerable")):
            continue
        sourceRef = str(row.get("sourceRef") or "").strip()
        if not sourceRef:
            continue
        cards.append(
            {
                "query": query,
                "source": str(row.get("source") or ""),
                "sourceRef": sourceRef,
                "dataAsOf": str(row.get("dataAsOf") or ""),
                "snippet": str(row.get("snippet") or "")[:500],
                "fieldCards": _fieldCards(row.get("fieldCards")),
                "entityCards": _fieldCards(row.get("entityCards")),
            }
        )
        if len(cards) >= limit:
            break
    return cards


def buildMemoryCardSet(df: pl.DataFrame, *, query: str = "", limit: int = 3) -> dict[str, Any]:
    """Build a sourceRef set and evidence cards for one LLM turn.

    Args:
        df: Product search result DataFrame.
        query: Query that produced the results.
        limit: Maximum cards to include.

    Returns:
        dict[str, Any]: Query, sourceRefs, cards, and source freshness map.

    Raises:
        None.

    Example:
        >>> buildMemoryCardSet(pl.DataFrame())["sourceRefs"]
        []
    """
    cards = buildMemoryCards(df, query=query, limit=limit)
    return {
        "query": query,
        "sourceRefs": [card["sourceRef"] for card in cards],
        "cards": cards,
        "dataAsOfBySource": _dataAsOfBySource(cards),
    }


def _fieldCards(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if not isinstance(raw, str) or not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def _dataAsOfBySource(cards: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for card in cards:
        source = str(card.get("source") or "")
        dataAsOf = str(card.get("dataAsOf") or "")
        if source and dataAsOf:
            out[source] = max(out.get(source, ""), dataAsOf)
    return out
