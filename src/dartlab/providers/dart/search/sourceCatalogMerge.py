"""Merge partial source-owner updates into full search source catalogs."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

import polars as pl

from dartlab.providers.dart.search.catalog import CATALOG_COLUMNS, normalizeCatalogRows
from dartlab.providers.dart.search.sourceManifest import SOURCE_MANIFEST_SOURCES


def writeMergedSourceCatalogArtifacts(
    source: str,
    files: Iterable[str | Path],
    *,
    previousCatalog: str | Path,
    previousManifest: Mapping[str, Any],
    outDir: str | Path,
    producer: str = "searchSourceCatalog",
    sourceVersion: str = "v1",
    schemaVersion: str = "2026-06",
    minFiles: int = 0,
    minRows: int = 0,
    minCatalogRows: int = 0,
    producerRun: Mapping[str, Any] | None = None,
    maxFileDropRatio: float = 0.05,
    maxRowDropRatio: float = 0.05,
    maxCatalogRowDropRatio: float = 0.05,
) -> dict[str, Path]:
    """Merge changed source files into a previous full source catalog.

    Args:
        source: Search source name.
        files: Changed parquet files available in the current source-owner run.
        previousCatalog: Prior full ``{source}.catalog_snapshot.parquet``.
        previousManifest: Prior full source manifest.
        outDir: Output directory.
        producer: Pipeline stage name.
        sourceVersion: Source adapter version.
        schemaVersion: Source parquet schema version.
        minFiles: Minimum merged file count.
        minRows: Minimum merged catalog rows.
        minCatalogRows: Minimum merged catalog rows.
        producerRun: Optional workflow/run lineage for durable productization
            evidence.
        maxFileDropRatio: Maximum accepted file-count drop vs previous manifest.
        maxRowDropRatio: Maximum accepted row-count drop vs previous manifest.
        maxCatalogRowDropRatio: Maximum accepted catalog-row drop vs previous
            manifest completeness evidence.

    Returns:
        dict[str, Path]: Written manifest and catalog paths.

    Raises:
        ValueError: When previous artifacts are missing or completeness fails.

    Example:
        >>> callable(writeMergedSourceCatalogArtifacts)
        True
    """
    from dartlab.providers.dart.search.sourceCatalog import (
        _intOrZero,
        _writeCatalogSnapshot,
        buildSourceManifest,
        validateSourceCatalogCompleteness,
    )

    if source not in SOURCE_MANIFEST_SOURCES:
        raise ValueError(f"unknown search source: {source}")
    prevCatalogPath = Path(previousCatalog)
    if not prevCatalogPath.exists():
        raise ValueError(f"previous source catalog not found: {prevCatalogPath}")
    if not previousManifest:
        raise ValueError(f"previous source manifest required for {source}")

    paths = [Path(path) for path in files]
    out = Path(outDir)
    out.mkdir(parents=True, exist_ok=True)
    manifestPath = out / f"{source}.source_manifest.json"
    catalogPath = out / f"{source}.catalog_snapshot.parquet"
    tmpDeltaPath = catalogPath.with_name(f"{catalogPath.name}.delta.tmp")
    tmpCatalogPath = catalogPath.with_name(f"{catalogPath.name}.tmp")
    for tmp in (tmpDeltaPath, tmpCatalogPath):
        if tmp.exists():
            tmp.unlink()

    deltaManifest = buildSourceManifest(
        source,
        paths,
        producer=producer,
        sourceVersion=sourceVersion,
        schemaVersion=schemaVersion,
        snapshotScope="partial",
        producerRun=producerRun,
    )
    try:
        deltaRows = _writeCatalogSnapshot(
            source,
            paths,
            tmpDeltaPath,
            sourceDataAsOf=str(deltaManifest.get("dataAsOf") or previousManifest.get("dataAsOf") or ""),
            sourceAdapterVersion=sourceVersion,
        )
        previousFrame = normalizeCatalogRows(pl.read_parquet(prevCatalogPath))
        deltaFrame = normalizeCatalogRows(pl.read_parquet(tmpDeltaPath))
        merged = mergeSourceCatalogSnapshot(source, previousFrame, deltaFrame, changedFiles=paths)
        merged.write_parquet(tmpCatalogPath)
    except Exception:
        for tmp in (tmpDeltaPath, tmpCatalogPath):
            if tmp.exists():
                tmp.unlink()
        raise

    catalogRows = merged.height
    manifest = _mergedSourceManifest(
        source,
        previousManifest=previousManifest,
        deltaManifest=deltaManifest,
        catalogRows=catalogRows,
        catalogDataAsOf=_catalogDataAsOf(merged),
        producer=producer,
        sourceVersion=sourceVersion,
        schemaVersion=schemaVersion,
        producerRun=producerRun,
    )
    completeness = validateSourceCatalogCompleteness(
        manifest,
        catalogRows=catalogRows,
        minFiles=minFiles,
        minRows=minRows,
        minCatalogRows=minCatalogRows,
        previousManifest=previousManifest,
        maxFileDropRatio=maxFileDropRatio,
        maxRowDropRatio=maxRowDropRatio,
        maxCatalogRowDropRatio=maxCatalogRowDropRatio,
    )
    manifest["completenessCheck"] = completeness
    manifest["deltaSource"] = {
        "snapshotScope": "partial",
        "fileCount": len(deltaManifest.get("files") or []),
        "rawRows": _intOrZero(deltaManifest.get("totalRows")),
        "catalogRows": int(deltaRows),
        "dataAsOf": str(deltaManifest.get("dataAsOf") or ""),
    }
    if not completeness["valid"]:
        for tmp in (tmpDeltaPath, tmpCatalogPath):
            if tmp.exists():
                tmp.unlink()
        raise ValueError(f"source catalog completeness failed: {','.join(completeness['errors'])}")
    tmpCatalogPath.replace(catalogPath)
    manifestPath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if tmpDeltaPath.exists():
        tmpDeltaPath.unlink()
    return {"manifest": manifestPath, "catalog": catalogPath}


def mergeSourceCatalogSnapshot(
    source: str,
    previousCatalog: pl.DataFrame,
    changedCatalog: pl.DataFrame,
    *,
    changedFiles: Iterable[str | Path] = (),
) -> pl.DataFrame:
    """Upsert a changed source catalog subset into a previous full snapshot.

    Args:
        source: Search source name.
        previousCatalog: Previous full catalog rows.
        changedCatalog: Catalog rows produced from changed source files.
        changedFiles: Source files represented by ``changedCatalog``.

    Returns:
        pl.DataFrame: Merged full catalog snapshot.

    Raises:
        None.

    Example:
        >>> mergeSourceCatalogSnapshot("newsPublic", normalizeCatalogRows([]), normalizeCatalogRows([])).height
        0
    """
    previous = normalizeCatalogRows(previousCatalog)
    changed = normalizeCatalogRows(changedCatalog)
    if previous.height == 0:
        return changed.filter(~pl.col("deleted")).select(CATALOG_COLUMNS)
    if changed.height == 0:
        return _dropReplacedPartitions(source, previous, changed, changedFiles).select(CATALOG_COLUMNS)

    liveChanged = changed.filter(~pl.col("deleted"))
    changedDocKeys = _catalogStringSet(changed, "docKey")
    keep = previous
    if changedDocKeys:
        keep = keep.filter(~pl.col("docKey").is_in(sorted(changedDocKeys)))
    keep = _dropReplacedPartitions(source, keep, liveChanged, changedFiles)
    if liveChanged.height == 0:
        return keep.select(CATALOG_COLUMNS)
    merged = pl.concat([keep.select(CATALOG_COLUMNS), liveChanged.select(CATALOG_COLUMNS)], how="vertical")
    return merged.unique(subset=["docKey"], keep="last", maintain_order=True).select(CATALOG_COLUMNS)


def _mergedSourceManifest(
    source: str,
    *,
    previousManifest: Mapping[str, Any],
    deltaManifest: Mapping[str, Any],
    catalogRows: int,
    catalogDataAsOf: str,
    producer: str,
    sourceVersion: str,
    schemaVersion: str,
    producerRun: Mapping[str, Any] | None,
) -> dict[str, Any]:
    from dartlab.providers.dart.search.sourceCatalog import _intOrZero

    files = _mergeManifestFiles(previousManifest, deltaManifest, source=source)
    rawRows = sum(_intOrZero(row.get("rowCount")) for row in files)
    dataAsOf = catalogDataAsOf or max(
        [
            str(previousManifest.get("dataAsOf") or ""),
            str(deltaManifest.get("dataAsOf") or ""),
            *[str(row.get("maxDate") or "") for row in files],
        ]
    )
    manifest: dict[str, Any] = {
        "source": source,
        "sourceVersion": sourceVersion,
        "schemaVersion": schemaVersion,
        "snapshotScope": "full",
        "dataAsOf": dataAsOf,
        "builtAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": files,
        "rawRows": rawRows,
        "totalRows": int(catalogRows),
        "changedRows": _intOrZero(deltaManifest.get("totalRows")),
        "deletedRows": _intOrZero(deltaManifest.get("deletedRows")),
        "producer": producer,
        "previousManifestId": _manifestIdentity(previousManifest),
    }
    if producerRun:
        manifest["producerRun"] = {str(key): value for key, value in producerRun.items() if value is not None}
    return manifest


def _mergeManifestFiles(
    previousManifest: Mapping[str, Any],
    deltaManifest: Mapping[str, Any],
    *,
    source: str,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in previousManifest.get("files") or []:
        if not isinstance(row, Mapping):
            continue
        path = _manifestFileKey(row, source=source)
        if path:
            merged[path] = {**row, "path": path}
    for row in deltaManifest.get("files") or []:
        if not isinstance(row, Mapping):
            continue
        path = _manifestFileKey(row, source=source)
        if path:
            merged[path] = {**row, "path": path}
    return [merged[key] for key in sorted(merged)]


def _manifestFileKey(row: Mapping[str, Any], *, source: str) -> str:
    path = str(row.get("path") or "").replace("\\", "/")
    if path and source in {"dartPanel", "edgarPanel"}:
        provider = "dart" if source == "dartPanel" else "edgar"
        return f"{provider}/panel/{Path(path).name}"
    return path


def _manifestIdentity(manifest: Mapping[str, Any]) -> str:
    payload = {
        "source": manifest.get("source"),
        "snapshotScope": manifest.get("snapshotScope"),
        "dataAsOf": manifest.get("dataAsOf"),
        "builtAt": manifest.get("builtAt"),
        "totalRows": manifest.get("totalRows"),
        "files": [
            {
                "path": row.get("path"),
                "hash": row.get("hash"),
                "rowCount": row.get("rowCount"),
            }
            for row in manifest.get("files") or []
            if isinstance(row, Mapping)
        ],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _dropReplacedPartitions(
    source: str,
    previous: pl.DataFrame,
    changed: pl.DataFrame,
    changedFiles: Iterable[str | Path],
) -> pl.DataFrame:
    if previous.height == 0:
        return previous
    if source == "dartPanel":
        stockCodes = {Path(path).stem for path in changedFiles if Path(path).stem}
        return _filterOut(previous, "stockCode", stockCodes)
    if source == "edgarPanel":
        tickers = {Path(path).stem for path in changedFiles if Path(path).stem}
        return _filterOut(previous, "ticker", tickers)
    if source == "newsPublic":
        return previous
    return previous


def _filterOut(frame: pl.DataFrame, column: str, values: set[str]) -> pl.DataFrame:
    if not values or column not in frame.columns:
        return frame
    return frame.filter(~pl.col(column).cast(pl.Utf8).is_in(sorted(values)))


def _catalogDataAsOf(frame: pl.DataFrame) -> str:
    if frame.height == 0:
        return ""
    columns = [column for column in ("sourceDataAsOf", "date") if column in frame.columns]
    if not columns:
        return ""
    values: list[str] = []
    for column in columns:
        values.extend(
            str(value) for value in frame.get_column(column).cast(pl.Utf8).to_list() if value not in (None, "")
        )
    return max(values, default="")


def _catalogStringSet(frame: pl.DataFrame, column: str) -> set[str]:
    if column not in frame.columns or frame.height == 0:
        return set()
    return {str(value) for value in frame.get_column(column).to_list() if value not in (None, "")}
