"""Search index pipeline planning helpers.

This module is intentionally IO-light: source owners still collect and publish
source artifacts, while search uses their manifests and catalog snapshots to
decide what can become a delta index.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import polars as pl

from dartlab.providers.dart.search.catalog import CATALOG_COLUMNS, diffCatalog, normalizeCatalogRows
from dartlab.providers.dart.search.sourceManifest import loadSourceManifest, validateSourceManifest

DELTA_CATALOG_COLUMNS: tuple[str, ...] = ("docKey", "source", "textHash", "metadataHash", "deleted")


def planCatalogDelta(
    previousRows: Iterable[dict[str, Any]] | pl.DataFrame,
    currentRows: Iterable[dict[str, Any]] | pl.DataFrame,
    sourceManifests: Iterable[dict[str, Any]],
    *,
    minSourceRetainedRatio: float = 0.8,
    expectedSources: Iterable[str] | None = None,
    requireFullSnapshot: bool = True,
) -> dict[str, Any]:
    """Plan a search delta from source manifests and catalog snapshots.

    Args:
        previousRows: Previous catalog snapshot rows.
        currentRows: Current catalog snapshot rows.
        sourceManifests: Source manifests produced by source-owner workflows.
        minSourceRetainedRatio: Reject a source if catalog rows fall below this
            ratio of the source manifest's totalRows.
        expectedSources: Optional source names that must be represented by
            valid manifests before catalog mode is allowed.
        requireFullSnapshot: True rejects ``snapshotScope != "full"``.

    Returns:
        dict: Dry-run summary with validity, errors, freshness, and delta counts.

    Raises:
        None.

    Example:
        >>> planCatalogDelta([], [{"source": "allFilings", "rcept_no": "1", "text": "a"}], [])["valid"]
        False
    """
    manifests = list(sourceManifests)
    errors: list[str] = []
    validSources: dict[str, dict[str, Any]] = {}
    for manifest in manifests:
        check = validateSourceManifest(manifest)
        if not check["valid"]:
            errors.extend(f"sourceManifest:{err}" for err in check["errors"])
            continue
        if requireFullSnapshot and manifest.get("snapshotScope") != "full":
            errors.append(f"sourceManifest:partialSnapshot:{manifest['source']}")
        validSources[str(manifest["source"])] = manifest

    for source in _normalizeSources(expectedSources):
        if source not in validSources:
            errors.append(f"sourceManifest:missingExpected:{source}")
            continue
        manifestRows = _int(validSources[source].get("totalRows"), 0)
        if manifestRows <= 0:
            errors.append(f"sourceManifest:emptyExpected:{source}")

    prev = _deltaCatalogFrame(previousRows)
    curr = _deltaCatalogFrame(currentRows)
    if curr.height == 0:
        errors.append("catalog:emptyCurrent")

    sourceCounts = _sourceCounts(curr)
    for source in _normalizeSources(expectedSources):
        if source in validSources and sourceCounts.get(source, 0) <= 0:
            errors.append(f"catalog:emptyExpected:{source}")
    for source, manifest in validSources.items():
        totalRows = _int(manifest.get("totalRows"), 0)
        actualRows = sourceCounts.get(source, 0)
        if totalRows > 0 and actualRows < int(totalRows * minSourceRetainedRatio):
            errors.append(f"catalogSourceDrop:{source}:{actualRows}/{totalRows}")

    if not validSources:
        errors.append("sourceManifest:noneValid")

    deltaSummary = _catalogDeltaSummary(prev, curr)
    changedDocs = deltaSummary["newDocs"] + deltaSummary["changedDocs"] + deltaSummary["deletedDocs"]
    return {
        "valid": not errors,
        "errors": errors,
        "sourceDataAsOf": {source: str(manifest.get("dataAsOf") or "") for source, manifest in validSources.items()},
        "sourceCounts": sourceCounts,
        "delta": deltaSummary,
        "changedDocs": changedDocs,
        "shouldBuildDelta": changedDocs > 0,
    }


def runCatalogDeltaDryRun(
    *,
    previousCatalogPath: str | Path | None,
    currentCatalogPath: str | Path,
    sourceManifestPaths: Iterable[str | Path],
    reportPath: str | Path | None = None,
    expectedSources: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Load catalog/manifest files and write a delta dry-run report.

    Args:
        previousCatalogPath: Previous catalog snapshot path. Missing/None means
            empty previous catalog.
        currentCatalogPath: Current catalog snapshot path.
        sourceManifestPaths: Source manifest JSON paths.
        reportPath: Optional JSON output path.
        expectedSources: Optional source names that must be represented by
            valid full snapshots.

    Returns:
        dict: Same shape as :func:`planCatalogDelta`.

    Raises:
        OSError: If the current catalog or report cannot be read/written.

    Example:
        >>> callable(runCatalogDeltaDryRun)
        True
    """
    manifests = []
    for path in sourceManifestPaths:
        manifest = loadSourceManifest(path)
        if manifest is not None:
            manifests.append(manifest)
        else:
            manifests.append({"source": "", "files": [], "totalRows": "invalid"})
    if _isParquetPath(currentCatalogPath) and (not previousCatalogPath or _isParquetPath(previousCatalogPath)):
        result = _planParquetCatalogDelta(
            previousCatalogPath=previousCatalogPath,
            currentCatalogPath=currentCatalogPath,
            sourceManifests=manifests,
            expectedSources=expectedSources,
        )
    else:
        previous = (
            _loadCatalog(previousCatalogPath, columns=DELTA_CATALOG_COLUMNS) if previousCatalogPath else pl.DataFrame()
        )
        current = _loadCatalog(currentCatalogPath, columns=DELTA_CATALOG_COLUMNS)
        result = planCatalogDelta(previous, current, manifests, expectedSources=expectedSources)
    if reportPath is not None:
        out = Path(reportPath)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return result


def _planParquetCatalogDelta(
    *,
    previousCatalogPath: str | Path | None,
    currentCatalogPath: str | Path,
    sourceManifests: list[dict[str, Any]],
    expectedSources: Iterable[str] | None,
    minSourceRetainedRatio: float = 0.8,
) -> dict[str, Any]:
    """Validate parquet catalogs with fingerprint-only, streaming operations."""
    from dartlab.providers.dart.search.catalogDeltaIo import (
        catalogDeltaSummaryFromPaths,
        sourceCountsFromPath,
    )

    errors: list[str] = []
    validSources: dict[str, dict[str, Any]] = {}
    for manifest in sourceManifests:
        check = validateSourceManifest(manifest)
        if not check["valid"]:
            errors.extend(f"sourceManifest:{error}" for error in check["errors"])
            continue
        if manifest.get("snapshotScope") != "full":
            errors.append(f"sourceManifest:partialSnapshot:{manifest['source']}")
        validSources[str(manifest["source"])] = manifest

    sourceCounts = sourceCountsFromPath(currentCatalogPath)
    for source in _normalizeSources(expectedSources):
        manifest = validSources.get(source)
        if manifest is None:
            errors.append(f"sourceManifest:missingExpected:{source}")
            continue
        manifestRows = _int(manifest.get("totalRows"), 0)
        if manifestRows <= 0:
            errors.append(f"sourceManifest:emptyExpected:{source}")
        if sourceCounts.get(source, 0) <= 0:
            errors.append(f"catalog:emptyExpected:{source}")

    for source, manifest in validSources.items():
        totalRows = _int(manifest.get("totalRows"), 0)
        actualRows = sourceCounts.get(source, 0)
        if totalRows > 0 and actualRows < int(totalRows * minSourceRetainedRatio):
            errors.append(f"catalogSourceDrop:{source}:{actualRows}/{totalRows}")
    if not validSources:
        errors.append("sourceManifest:noneValid")

    summary = catalogDeltaSummaryFromPaths(previousCatalogPath, currentCatalogPath)
    if summary["totalCurrentDocs"] == 0:
        errors.append("catalog:emptyCurrent")
    changedDocs = summary["newDocs"] + summary["changedDocs"] + summary["deletedDocs"]
    return {
        "valid": not errors,
        "errors": errors,
        "sourceDataAsOf": {source: str(manifest.get("dataAsOf") or "") for source, manifest in validSources.items()},
        "sourceCounts": sourceCounts,
        "delta": summary,
        "changedDocs": changedDocs,
        "shouldBuildDelta": changedDocs > 0,
    }


def _isParquetPath(path: str | Path) -> bool:
    from dartlab.providers.dart.search.catalogDeltaIo import isCanonicalCatalogParquet

    return isCanonicalCatalogParquet(path)


def exportDeltaRowsForContentIndex(
    previousRows: Iterable[dict[str, Any]] | pl.DataFrame,
    currentRows: Iterable[dict[str, Any]] | pl.DataFrame,
) -> pl.DataFrame:
    """Export new/changed rows and deletion tombstones as fieldIndex delta input.

    Args:
        previousRows: Previous catalog snapshot rows.
        currentRows: Current catalog snapshot rows. Rows must include searchable
            text through `searchText`, `text`, `section_content`, `content`, or
            `title`.

    Returns:
        pl.DataFrame: Rows compatible with `buildContentSegment`.

    Raises:
        None.

    Example:
        >>> exportDeltaRowsForContentIndex([], [{"source": "allFilings", "rcept_no": "1", "text": "a"}]).height
        1
    """
    delta = diffCatalog(previousRows, currentRows)
    rows = []
    for frame in (delta.new, delta.changed):
        for row in frame.iter_rows(named=True):
            contentRow = _catalogRowToContentRow(dict(row))
            contentRow["deleted"] = False
            rows.append(contentRow)
    for row in delta.deleted.iter_rows(named=True):
        contentRow = _catalogRowToContentRow(dict(row))
        contentRow["section_content"] = ""
        contentRow["deleted"] = True
        rows.append(contentRow)
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def exportCatalogRowsForContentIndex(rows: Iterable[dict[str, Any]] | pl.DataFrame) -> pl.DataFrame:
    """Export current catalog rows as fieldIndex build input.

    Args:
        rows: Catalog snapshot rows. Deleted rows are skipped.

    Returns:
        pl.DataFrame: Rows compatible with `buildContentSegment`.

    Raises:
        None.

    Example:
        >>> exportCatalogRowsForContentIndex([{"source": "allFilings", "rcept_no": "1", "text": "a"}]).height
        1
    """
    catalog = normalizeCatalogRows(rows)
    out = [_catalogRowToContentRow(dict(row)) for row in catalog.iter_rows(named=True) if not row.get("deleted")]
    return pl.DataFrame(out) if out else pl.DataFrame()


def _loadCatalog(path: str | Path | None, *, columns: Iterable[str] | None = None) -> pl.DataFrame:
    if path is None:
        return pl.DataFrame()
    p = Path(path)
    if not p.exists():
        return pl.DataFrame()
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        wanted = list(columns or [])
        if wanted:
            try:
                schema = set(pl.scan_parquet(p).collect_schema().names())
            except (pl.exceptions.PolarsError, OSError):
                schema = set()
            if set(wanted).issubset(schema):
                return pl.read_parquet(p, columns=wanted)
        return pl.read_parquet(p)
    if suffix == ".jsonl":
        rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
        return pl.DataFrame(rows) if rows else pl.DataFrame()
    if suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return pl.DataFrame(data)
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            return pl.DataFrame(data["rows"])
    raise ValueError(f"unsupported catalog format: {p}")


def _deltaCatalogFrame(rows: Iterable[dict[str, Any]] | pl.DataFrame) -> pl.DataFrame:
    if isinstance(rows, pl.DataFrame):
        if rows.height == 0:
            return pl.DataFrame({name: [] for name in DELTA_CATALOG_COLUMNS})
        if set(DELTA_CATALOG_COLUMNS).issubset(rows.columns):
            return rows.select(DELTA_CATALOG_COLUMNS)
        if set(CATALOG_COLUMNS).issubset(rows.columns):
            return rows.select(DELTA_CATALOG_COLUMNS)
    return normalizeCatalogRows(rows).select(DELTA_CATALOG_COLUMNS)


def _catalogDeltaSummary(previous: pl.DataFrame, current: pl.DataFrame) -> dict[str, int]:
    prev = _fingerprintMap(previous)
    currKeys: set[str] = set()
    newDocs = 0
    changedDocs = 0
    deletedDocs = 0
    unchangedDocs = 0
    for row in current.iter_rows(named=True):
        key = str(row.get("docKey") or "")
        if not key:
            continue
        if key in currKeys:
            continue
        currKeys.add(key)
        currFingerprint = _fingerprint(row)
        oldFingerprint = prev.get(key)
        if bool(row.get("deleted")):
            deletedDocs += 1
        elif oldFingerprint is None:
            newDocs += 1
        elif oldFingerprint != currFingerprint:
            changedDocs += 1
        else:
            unchangedDocs += 1
    deletedDocs += len(set(prev) - currKeys)
    return {
        "newDocs": newDocs,
        "changedDocs": changedDocs,
        "deletedDocs": deletedDocs,
        "unchangedDocs": unchangedDocs,
        "totalCurrentDocs": len(currKeys),
        "totalPreviousDocs": len(prev),
    }


def _fingerprintMap(df: pl.DataFrame) -> dict[str, tuple[str, str, bool]]:
    out: dict[str, tuple[str, str, bool]] = {}
    if df.height == 0:
        return out
    for row in df.iter_rows(named=True):
        key = str(row.get("docKey") or "")
        if key:
            out[key] = _fingerprint(row)
    return out


def _fingerprint(row: dict[str, Any]) -> tuple[str, str, bool]:
    return (str(row.get("textHash") or ""), str(row.get("metadataHash") or ""), bool(row.get("deleted")))


def _catalogRowToContentRow(row: dict[str, Any]) -> dict[str, Any]:
    source = str(row.get("source") or "")
    return {
        "docKey": str(row.get("docKey") or ""),
        "rcept_no": str(row.get("rceptNo") or row.get("sourceRef") or ""),
        "section_order": int(row.get("sectionOrder") or 0),
        "corp_code": str(row.get("corpCode") or ""),
        "corp_name": str(row.get("companyName") or ""),
        "stock_code": str(row.get("stockCode") or ""),
        "rcept_dt": str(row.get("date") or ""),
        "report_nm": str(row.get("reportName") or ""),
        "section_title": str(row.get("title") or row.get("sectionKey") or ""),
        "section_content": str(row.get("searchText") or ""),
        "source": _runtimeSource(source),
        "sourceRef": str(row.get("sourceRef") or ""),
        "sourceDataAsOf": str(row.get("sourceDataAsOf") or row.get("date") or ""),
        "url": _runtimeUrl(source, row),
        "deleted": bool(row.get("deleted")),
    }


def _runtimeSource(source: str) -> str:
    return {"dartPanel": "panel", "edgarPanel": "edgar-panel", "newsPublic": "news"}.get(source, source)


def _runtimeUrl(source: str, row: dict[str, Any]) -> str:
    if source == "newsPublic":
        return str(row.get("url") or "")
    return ""


def _sourceCounts(catalog: pl.DataFrame) -> dict[str, int]:
    if catalog.height == 0 or "source" not in catalog.columns:
        return {}
    out: dict[str, int] = {}
    for row in catalog.group_by("source").len().iter_rows(named=True):
        out[str(row.get("source") or "")] = int(row.get("len") or 0)
    return out


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalizeSources(sources: Iterable[str] | None) -> list[str]:
    if sources is None:
        return []
    out: list[str] = []
    for source in sources:
        value = str(source).strip()
        if value and value not in out:
            out.append(value)
    return out
