"""Search catalog normalization and changed-set diff."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

import polars as pl

from dartlab.providers.dart.search.coerce import _int
from dartlab.providers.dart.search.freshness import normalizeSearchDate, periodToDataAsOf

CATALOG_COLUMNS: tuple[str, ...] = (
    "docKey",
    "source",
    "sourceRef",
    "sourcePriority",
    "rceptNo",
    "accession",
    "urlHash",
    "url",
    "sectionKey",
    "sectionOrder",
    "corpCode",
    "stockCode",
    "ticker",
    "companyName",
    "date",
    "reportName",
    "title",
    "searchText",
    "textHash",
    "metadataHash",
    "contentLen",
    "deleted",
    "sourceDataAsOf",
    "sourceAdapterVersion",
)


@dataclass(frozen=True)
class CatalogDelta:
    """Changed-set result for a source catalog snapshot."""

    new: pl.DataFrame
    changed: pl.DataFrame
    deleted: pl.DataFrame
    unchanged: pl.DataFrame
    summary: dict[str, int]


def normalizeCatalogRows(rows: Iterable[dict[str, Any]] | pl.DataFrame) -> pl.DataFrame:
    """Normalize source rows into the product catalog schema.

    Args:
        rows: Source rows or a Polars DataFrame.

    Returns:
        pl.DataFrame: Canonical catalog rows.

    Raises:
        None.

    Example:
        >>> normalizeCatalogRows([{"source": "allFilings", "rcept_no": "1", "text": "a"}]).height
        1
    """
    if isinstance(rows, pl.DataFrame) and set(CATALOG_COLUMNS).issubset(rows.columns):
        return rows.select(CATALOG_COLUMNS)
    rawRows = rows.iter_rows(named=True) if isinstance(rows, pl.DataFrame) else iter(rows)
    normalized = [_normalizeRow(dict(row)) for row in rawRows]
    if not normalized:
        return _emptyCatalogFrame()
    return pl.DataFrame(normalized).select(CATALOG_COLUMNS)


def diffCatalog(
    previous: Iterable[dict[str, Any]] | pl.DataFrame, current: Iterable[dict[str, Any]] | pl.DataFrame
) -> CatalogDelta:
    """Diff two catalog snapshots by docKey/textHash/metadataHash/deleted.

    Args:
        previous: Previous catalog snapshot.
        current: Current catalog snapshot.

    Returns:
        CatalogDelta: new/changed/deleted/unchanged frames and count summary.

    Raises:
        None.

    Example:
        >>> d = diffCatalog([], [{"source": "allFilings", "rcept_no": "1", "text": "a"}])
        >>> d.summary["newDocs"]
        1
    """
    prev = _byDocKey(normalizeCatalogRows(previous))
    curr = _byDocKey(normalizeCatalogRows(current))
    newRows: list[dict[str, Any]] = []
    changedRows: list[dict[str, Any]] = []
    deletedRows: list[dict[str, Any]] = []
    unchangedRows: list[dict[str, Any]] = []

    for key, row in curr.items():
        if _truthy(row.get("deleted")):
            deletedRows.append(row)
            continue
        old = prev.get(key)
        if old is None:
            newRows.append(row)
        elif _fingerprint(old) != _fingerprint(row):
            changedRows.append(row)
        else:
            unchangedRows.append(row)

    for key, row in prev.items():
        if key in curr:
            continue
        tombstone = dict(row)
        tombstone["deleted"] = True
        deletedRows.append(tombstone)

    summary = {
        "newDocs": len(newRows),
        "changedDocs": len(changedRows),
        "deletedDocs": len(deletedRows),
        "unchangedDocs": len(unchangedRows),
        "totalCurrentDocs": len(curr),
        "totalPreviousDocs": len(prev),
    }
    return CatalogDelta(
        new=_frame(newRows),
        changed=_frame(changedRows),
        deleted=_frame(deletedRows),
        unchanged=_frame(unchangedRows),
        summary=summary,
    )


def _normalizeRow(row: dict[str, Any]) -> dict[str, Any]:
    source = _canonicalSource(str(_first(row, "source") or ""))
    rceptNo = str(_first(row, "rceptNo", "rcept_no") or "")
    accession = str(_first(row, "accession") or (rceptNo if source == "edgarPanel" else ""))
    url = str(_first(row, "url", "articleUrl") or "")
    urlHash = str(_first(row, "urlHash", "url_hash") or (_sha1(url) if url else ""))
    sectionOrder = _int(_first(row, "sectionOrder", "section_order", "blockOrder"), 0)
    sectionKey = str(
        _first(row, "sectionKey", "section_key", "section_title", "sectionLeaf", "blockLeaf", "chapter") or sectionOrder
    )
    sourceRef = str(
        _first(row, "sourceRef", "source_ref") or _sourceRef(source, rceptNo, accession, urlHash, sectionOrder)
    )
    text = str(
        _first(row, "searchText", "text", "content", "section_content", "content_raw", "contentRaw", "title") or ""
    )
    title = str(_first(row, "title", "section_title", "report_nm", "reportName", "sectionLeaf", "chapter") or "")
    rowDate = normalizeSearchDate(
        _first(row, "date", "rcept_dt", "rceptDate", "filing_date", "filed_date", "filingDate", "filedAt")
    ) or periodToDataAsOf(row.get("period"))
    sourceDataAsOf = normalizeSearchDate(_first(row, "sourceDataAsOf", "source_data_as_of", "dataAsOf")) or rowDate
    out = {
        "docKey": str(_first(row, "docKey", "doc_key") or sourceRef),
        "source": source,
        "sourceRef": sourceRef,
        "sourcePriority": _int(_first(row, "sourcePriority", "source_priority"), _sourcePriority(source)),
        "rceptNo": rceptNo,
        "accession": accession,
        "urlHash": urlHash,
        "url": url,
        "sectionKey": sectionKey,
        "sectionOrder": sectionOrder,
        "corpCode": str(_first(row, "corpCode", "corp_code") or ""),
        "stockCode": str(_first(row, "stockCode", "stock_code") or ""),
        "ticker": str(_first(row, "ticker") or ""),
        "companyName": str(_first(row, "companyName", "corp_name", "corp") or ""),
        "date": rowDate,
        "reportName": str(_first(row, "reportName", "report_nm") or ""),
        "title": title,
        "searchText": text,
        "textHash": str(_first(row, "textHash", "text_hash") or _sha256(text)),
        "metadataHash": str(_first(row, "metadataHash", "metadata_hash") or ""),
        "contentLen": _int(_first(row, "contentLen", "content_len"), len(text)),
        "deleted": bool(_first(row, "deleted") or False),
        "sourceDataAsOf": sourceDataAsOf,
        "sourceAdapterVersion": str(_first(row, "sourceAdapterVersion", "source_adapter_version") or "v1"),
    }
    if not out["metadataHash"]:
        out["metadataHash"] = _metadataHash(out)
    return out


def _sourceRef(source: str, rceptNo: str, accession: str, urlHash: str, sectionOrder: int) -> str:
    if source == "newsPublic":
        return f"news:{urlHash or rceptNo}"
    if source == "edgarPanel":
        return f"edgar:panel:{accession or rceptNo}#section={sectionOrder}"
    if source == "dartPanel":
        return f"dart:panel:{rceptNo}#section={sectionOrder}"
    if source == "allFilings":
        return f"dart:allFilings:{rceptNo}#section={sectionOrder}"
    return f"{source}:{rceptNo or urlHash}#section={sectionOrder}"


def _canonicalSource(source: str) -> str:
    aliases = {
        "panel": "dartPanel",
        "edgar-panel": "edgarPanel",
        "news": "newsPublic",
        "newsHeadlines": "newsPublic",
    }
    return aliases.get(source, source or "allFilings")


def _sourcePriority(source: str) -> int:
    return {"dartPanel": 10, "edgarPanel": 10, "allFilings": 20, "newsPublic": 30}.get(source, 50)


def _fingerprint(row: dict[str, Any]) -> tuple[str, str, bool]:
    return (str(row.get("textHash") or ""), str(row.get("metadataHash") or ""), bool(row.get("deleted")))


def _byDocKey(df: pl.DataFrame) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in df.iter_rows(named=True):
        key = str(row.get("docKey") or "")
        if key:
            out[key] = dict(row)
    return out


def _frame(rows: list[dict[str, Any]]) -> pl.DataFrame:
    if not rows:
        return _emptyCatalogFrame()
    return pl.DataFrame(rows).select(CATALOG_COLUMNS)


def _emptyCatalogFrame() -> pl.DataFrame:
    return pl.DataFrame({name: [] for name in CATALOG_COLUMNS})


def _metadataHash(row: dict[str, Any]) -> str:
    payload = {k: row.get(k) for k in CATALOG_COLUMNS if k not in {"searchText", "textHash", "metadataHash"}}
    return _sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _sha1(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)
