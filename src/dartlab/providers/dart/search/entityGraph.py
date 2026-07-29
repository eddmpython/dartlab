"""Entity graph catalog enrichment for product search rows."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from dartlab.providers.dart.search.coerce import _nameKey

_log = logging.getLogger(__name__)

ENTITY_GRAPH_CATALOG_NAME = "entityGraphCatalog.parquet"
_CATALOG_FILENAMES: tuple[str, ...] = (
    ENTITY_GRAPH_CATALOG_NAME,
    "graph_catalog.parquet",
)
_CATALOG_CACHE: dict[str, tuple[float, pl.DataFrame | None]] = {}


def attachEntityGraphCards(
    df: pl.DataFrame,
    *,
    catalog: pl.DataFrame | None = None,
    maxRows: int = 10,
    maxNeighbors: int = 4,
) -> pl.DataFrame:
    """Attach bounded entity graph cards to search result rows.

    Args:
        df: Product search result DataFrame.
        catalog: Optional preloaded entity graph catalog. When omitted, the
            runtime catalog path is discovered from environment/data artifacts.
        maxRows: Maximum result rows to enrich.
        maxNeighbors: Maximum neighbor cards per resolved entity.

    Returns:
        pl.DataFrame: Search rows with optional ``entityCards`` metadata.

    Raises:
        None.

    Example:
        >>> attachEntityGraphCards(pl.DataFrame()).height
        0
    """
    if df is None or df.height == 0 or "info" in df.columns:
        return df
    graphCatalog = catalog if catalog is not None else loadEntityGraphCatalog()
    if graphCatalog is None or graphCatalog.height == 0:
        return df

    resolver = _CatalogResolver(graphCatalog)
    rows = []
    for rank, row in enumerate(df.iter_rows(named=True), start=1):
        out = dict(row)
        if rank <= maxRows:
            entity = resolver.resolveRow(out)
            cards = buildEntityCards(entity, sourceRef=str(out.get("sourceRef") or ""), maxNeighbors=maxNeighbors)
            out["entityResolved"] = entity is not None
            out["entityStockCode"] = str(entity.get("stockCode") or "") if entity else ""
            out["entityCardCount"] = len(cards)
            out["entityCards"] = json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
        rows.append(out)
    return pl.DataFrame(rows)


def loadEntityGraphCatalog(path: str | Path | None = None) -> pl.DataFrame | None:
    """Load the optional entity graph catalog from disk.

    Args:
        path: Explicit parquet path. When omitted, discovery checks
            ``DARTLAB_SEARCH_ENTITY_GRAPH_CATALOG`` and active search index
            artifact locations.

    Returns:
        pl.DataFrame | None: Catalog rows, or None when unavailable.

    Raises:
        None. Invalid/missing catalogs degrade to no enrichment.

    Example:
        >>> loadEntityGraphCatalog("missing.parquet") is None
        True
    """
    catalogPath = Path(path) if path is not None else _discoverCatalogPath()
    if catalogPath is None or not catalogPath.exists():
        return None
    try:
        mtime = catalogPath.stat().st_mtime
    except OSError:
        return None
    cacheKey = str(catalogPath.resolve())
    cached = _CATALOG_CACHE.get(cacheKey)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        catalog = pl.read_parquet(catalogPath)
    except (OSError, pl.exceptions.PolarsError) as exc:
        _log.warning(
            "entity graph catalog 비활성화: path=%s, error=%s: %s",
            catalogPath,
            type(exc).__name__,
            exc,
        )
        catalog = None
    _CATALOG_CACHE[cacheKey] = (mtime, catalog)
    return catalog


def buildEntityCards(
    entity: Mapping[str, Any] | None,
    *,
    sourceRef: str = "",
    maxNeighbors: int = 4,
) -> list[dict[str, str]]:
    """Build compact graph cards for one resolved entity row.

    Args:
        entity: Catalog row dictionary.
        sourceRef: Search result sourceRef to keep card provenance attached to
            the initiating document hit.
        maxNeighbors: Maximum peer/supply-chain cards.

    Returns:
        list[dict[str, str]]: JSON-serializable entity cards.

    Raises:
        None.

    Example:
        >>> buildEntityCards(None)
        []
    """
    if not entity:
        return []
    cards: list[dict[str, str]] = []

    def add(label: str, value: Any, *, evidence: str = "") -> None:
        """Append one entity card when a value exists.

        Args:
            label: Card label.
            value: Card value.
            evidence: Optional evidence text.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> cards = []
        """
        if value in (None, ""):
            return
        card = {"label": label, "value": str(value)}
        if evidence:
            card["evidence"] = evidence
        if sourceRef:
            card["sourceRef"] = sourceRef
        cards.append(card)

    name = str(entity.get("corpName") or "")
    code = str(entity.get("stockCode") or "")
    grade = str(entity.get("grade") or "")
    weakAxis = str(entity.get("weakAxis") or "")
    stageName = str(entity.get("stageName") or "")
    chainName = str(entity.get("chainName") or "")
    dataAsOf = str(entity.get("dataAsOf") or entity.get("generatedAt") or "")

    add("entity", f"{name}({code})")
    add("creditWeakAxis", " / ".join(part for part in (grade, weakAxis) if part))
    add("industryStage", " / ".join(part for part in (chainName, stageName) if part))
    add("entityGraphDataAsOf", dataAsOf)

    for peer in _jsonList(entity.get("neighborsJson"))[: max(0, int(maxNeighbors))]:
        peerName = str(peer.get("corpName") or "")
        peerCode = str(peer.get("stockCode") or "")
        peerGrade = str(peer.get("grade") or "")
        peerAxis = str(peer.get("weakAxis") or "")
        peerStage = str(peer.get("stageName") or "")
        evidence = " / ".join(part for part in (peerGrade, peerAxis, peerStage) if part)
        add(f"peer:{peerName}", f"{peerName}({peerCode})", evidence=evidence)
    return cards


def _discoverCatalogPath() -> Path | None:
    explicit = os.environ.get("DARTLAB_SEARCH_ENTITY_GRAPH_CATALOG")
    if explicit:
        return Path(explicit)

    from dartlab.providers.dart.search.fieldIndex import _activeIndexDir

    active = _activeIndexDir()
    candidates = [active / name for name in _CATALOG_FILENAMES]
    parent = active.parent
    candidates.extend(parent / name for name in _CATALOG_FILENAMES)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


class _CatalogResolver:
    """Resolve search rows into graph catalog entities."""

    def __init__(self, catalog: pl.DataFrame) -> None:
        self.byCode: dict[str, dict[str, Any]] = {}
        self.byName: dict[str, dict[str, Any]] = {}
        for row in catalog.iter_rows(named=True):
            code = _stockCode(row.get("stockCode") or row.get("stock_code"))
            if code:
                self.byCode[code] = row
            key = _nameKey(row.get("corpName") or row.get("corp_name"))
            if key and key not in self.byName:
                self.byName[key] = row

    def resolveRow(self, row: Mapping[str, Any]) -> dict[str, Any] | None:
        """Resolve a search result row to one catalog row.

        Args:
            row: Search result row.

        Returns:
            dict[str, Any] | None: Matching catalog row, or None.

        Raises:
            None.

        Example:
            >>> _CatalogResolver(pl.DataFrame()).resolveRow({})
        """
        for key in ("stock_code", "stockCode", "entityStockCode", "code"):
            code = _stockCode(row.get(key))
            if code and code in self.byCode:
                return self.byCode[code]
        for key in ("corp_name", "corpName", "companyName", "company_name"):
            nameKey = _nameKey(row.get(key))
            if nameKey and nameKey in self.byName:
                return self.byName[nameKey]
        return None


def _stockCode(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 6:
        return digits
    if text.isdigit() and len(text) <= 6:
        return text.zfill(6)
    return text


def _jsonList(raw: Any) -> list[dict[str, Any]]:
    if raw in (None, ""):
        return []
    if isinstance(raw, list):
        return [dict(row) for row in raw if isinstance(row, Mapping)]
    try:
        data = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [dict(row) for row in data if isinstance(row, Mapping)]
