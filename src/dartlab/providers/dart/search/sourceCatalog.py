"""Build search source manifests and catalog snapshots from local parquet files."""

from __future__ import annotations

import html
import json
import re
import time
from glob import glob
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import polars as pl

from dartlab.core.utils.fileDigest import fileHash
from dartlab.providers.dart.search.catalog import normalizeCatalogRows
from dartlab.providers.dart.search.freshness import DEFAULT_DATE_COLUMNS, normalizeSearchDate, periodToDataAsOf
from dartlab.providers.dart.search.sourceManifest import SOURCE_MANIFEST_SOURCES

DATE_COLUMNS: tuple[str, ...] = DEFAULT_DATE_COLUMNS
PANEL_CATALOG_SOURCES = {"dartPanel", "edgarPanel"}
PANEL_TEXT_LIMIT = 4000
PANEL_SECTION_LIMIT = 2000

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_BLOCK_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)

CATALOG_INPUT_COLUMNS: tuple[str, ...] = (
    "source",
    "sourceRef",
    "source_ref",
    "sourcePriority",
    "source_priority",
    "rceptNo",
    "rcept_no",
    "accession",
    "url",
    "articleUrl",
    "urlHash",
    "url_hash",
    "sectionKey",
    "section_key",
    "section_title",
    "sectionLeaf",
    "blockLeaf",
    "chapter",
    "sectionOrder",
    "section_order",
    "blockOrder",
    "corpCode",
    "corp_code",
    "stockCode",
    "stock_code",
    "ticker",
    "companyName",
    "corp_name",
    "corp",
    "date",
    "rcept_dt",
    "rceptDate",
    "filing_date",
    "filed_date",
    "filingDate",
    "filedAt",
    "captured_at",
    "published",
    "acceptanceDateTime",
    "period",
    "reportName",
    "report_nm",
    "title",
    "searchText",
    "text",
    "content",
    "section_content",
    "content_raw",
    "contentRaw",
    "textHash",
    "text_hash",
    "metadataHash",
    "metadata_hash",
    "contentLen",
    "content_len",
    "deleted",
    "sourceDataAsOf",
    "source_data_as_of",
    "dataAsOf",
    "sourceAdapterVersion",
    "source_adapter_version",
    "fetch_status",
)


def discoverSourceFiles(patterns: Iterable[str | Path]) -> list[Path]:
    """Resolve parquet file patterns for a source snapshot.

    Args:
        patterns: File paths or glob patterns.

    Returns:
        list[Path]: Existing parquet files, sorted and de-duplicated.

    Raises:
        None.

    Example:
        >>> discoverSourceFiles([])
        []
    """
    out: dict[str, Path] = {}
    for raw in patterns:
        text = str(raw)
        if not text:
            continue
        matches = (
            [Path(path) for path in sorted(glob(text, recursive=True))]
            if any(ch in text for ch in "*?[")
            else [Path(text)]
        )
        for path in matches:
            if path.is_file() and path.suffix.lower() == ".parquet":
                out[str(path.resolve())] = path
    return [out[key] for key in sorted(out)]


def buildSourceManifest(
    source: str,
    files: Iterable[str | Path],
    *,
    producer: str = "searchSourceCatalog",
    sourceVersion: str = "v1",
    schemaVersion: str = "2026-06",
    snapshotScope: str = "full",
    changedRows: int | None = None,
    deletedRows: int = 0,
    producerRun: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a source manifest from parquet files.

    Args:
        source: Search source name, such as ``allFilings`` or ``newsPublic``.
        files: Parquet files that belong to this source.
        producer: Pipeline stage name.
        sourceVersion: Source adapter version.
        schemaVersion: Source parquet schema version.
        snapshotScope: ``"full"`` when files represent the complete source
            snapshot, ``"partial"`` for non-canonical changed subsets.
        changedRows: Optional changed row count. Defaults to total rows.
        deletedRows: Tombstone or deleted row count.
        producerRun: Optional workflow/run lineage for the source owner that
            created this manifest.

    Returns:
        dict[str, Any]: Source manifest payload.

    Raises:
        ValueError: When source is unknown.

    Example:
        >>> buildSourceManifest("allFilings", [])["totalRows"]
        0
    """
    if source not in SOURCE_MANIFEST_SOURCES:
        raise ValueError(f"unknown search source: {source}")
    paths = [Path(path) for path in files]
    fileRows = [_fileManifest(path, source=source) for path in paths]
    totalRows = sum(int(row.get("rowCount") or 0) for row in fileRows)
    dataAsOf = max((str(row.get("maxDate") or "") for row in fileRows), default="")
    manifest = {
        "source": source,
        "sourceVersion": sourceVersion,
        "schemaVersion": schemaVersion,
        "snapshotScope": snapshotScope,
        "dataAsOf": dataAsOf,
        "builtAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": fileRows,
        "totalRows": totalRows,
        "changedRows": totalRows if changedRows is None else int(changedRows),
        "deletedRows": int(deletedRows),
        "producer": producer,
    }
    if producerRun:
        manifest["producerRun"] = {str(key): value for key, value in producerRun.items() if value is not None}
    return manifest


def buildCatalogSnapshot(
    source: str,
    files: Iterable[str | Path],
    *,
    sourceDataAsOf: str = "",
    sourceAdapterVersion: str = "v1",
) -> pl.DataFrame:
    """Build a normalized search catalog snapshot for one source.

    Args:
        source: Search source name.
        files: Parquet files to read.
        sourceDataAsOf: Freshness value copied into catalog rows.
        sourceAdapterVersion: Source adapter version copied into catalog rows.

    Returns:
        pl.DataFrame: Catalog rows in product schema.

    Raises:
        pl.PolarsError: If a parquet file cannot be read.

    Example:
        >>> buildCatalogSnapshot("allFilings", []).height
        0
    """
    rows: list[dict[str, Any]] = []
    for path in files:
        df = pl.read_parquet(path)
        if df.height == 0:
            continue
        for row in df.iter_rows(named=True):
            out = dict(row)
            out["source"] = source
            out.setdefault("sourceDataAsOf", sourceDataAsOf)
            out.setdefault("sourceAdapterVersion", sourceAdapterVersion)
            rows.append(out)
    return normalizeCatalogRows(rows)


def writeSourceCatalogArtifacts(
    source: str,
    files: Iterable[str | Path],
    *,
    outDir: str | Path,
    producer: str = "searchSourceCatalog",
    sourceVersion: str = "v1",
    schemaVersion: str = "2026-06",
    snapshotScope: str = "full",
    minFiles: int = 0,
    minRows: int = 0,
    minCatalogRows: int = 0,
    allowEmptyFullSnapshot: bool = False,
    producerRun: Mapping[str, Any] | None = None,
    previousManifest: Mapping[str, Any] | None = None,
    maxFileDropRatio: float = 0.05,
    maxRowDropRatio: float = 0.05,
    maxCatalogRowDropRatio: float = 0.05,
) -> dict[str, Path]:
    """Write source manifest and catalog snapshot for search delta workflows.

    Args:
        source: Search source name.
        files: Parquet files to read.
        outDir: Output directory.
        producer: Pipeline stage name.
        sourceVersion: Source adapter version.
        schemaVersion: Source parquet schema version.
        snapshotScope: ``"full"`` when files represent the complete source
            snapshot. Partial snapshots are not canonical search catalog inputs.
        minFiles: Minimum source parquet files required.
        minRows: Minimum source parquet rows required.
        minCatalogRows: Minimum normalized catalog rows required.
        allowEmptyFullSnapshot: True permits an empty ``snapshotScope=full``
            artifact. Product source workflows should not use this for canonical
            sources.
        producerRun: Optional workflow/run lineage for durable productization
            evidence.
        previousManifest: Optional prior full source manifest. When supplied,
            full snapshots cannot silently drop files or rows beyond the
            configured ratios.
        maxFileDropRatio: Maximum accepted file-count drop vs previous manifest.
        maxRowDropRatio: Maximum accepted row-count drop vs previous manifest.
        maxCatalogRowDropRatio: Maximum accepted catalog-row drop vs previous
            manifest completeness evidence.

    Returns:
        dict[str, Path]: Written manifest and catalog paths.

    Raises:
        OSError: When output files cannot be written.
        ValueError: When source is unknown or completeness checks fail.

    Example:
        >>> callable(writeSourceCatalogArtifacts)
        True
    """
    paths = [Path(path) for path in files]
    out = Path(outDir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = buildSourceManifest(
        source,
        paths,
        producer=producer,
        sourceVersion=sourceVersion,
        schemaVersion=schemaVersion,
        snapshotScope=snapshotScope,
        producerRun=producerRun,
    )
    manifestPath = out / f"{source}.source_manifest.json"
    catalogPath = out / f"{source}.catalog_snapshot.parquet"
    tmpCatalogPath = catalogPath.with_name(f"{catalogPath.name}.tmp")
    if tmpCatalogPath.exists():
        tmpCatalogPath.unlink()
    try:
        catalogRows = _writeCatalogSnapshot(
            source,
            paths,
            tmpCatalogPath,
            sourceDataAsOf=str(manifest.get("dataAsOf") or ""),
            sourceAdapterVersion=sourceVersion,
        )
    except Exception:
        if tmpCatalogPath.exists():
            tmpCatalogPath.unlink()
        raise
    if int(manifest.get("totalRows") or 0) != int(catalogRows):
        manifest["rawRows"] = manifest["totalRows"]
        manifest["totalRows"] = catalogRows
        manifest["changedRows"] = catalogRows
    completeness = validateSourceCatalogCompleteness(
        manifest,
        catalogRows=catalogRows,
        minFiles=minFiles,
        minRows=minRows,
        minCatalogRows=minCatalogRows,
        allowEmptyFullSnapshot=allowEmptyFullSnapshot,
        previousManifest=previousManifest,
        maxFileDropRatio=maxFileDropRatio,
        maxRowDropRatio=maxRowDropRatio,
        maxCatalogRowDropRatio=maxCatalogRowDropRatio,
    )
    manifest["completenessCheck"] = completeness
    if not completeness["valid"]:
        if tmpCatalogPath.exists():
            tmpCatalogPath.unlink()
        raise ValueError(f"source catalog completeness failed: {','.join(completeness['errors'])}")
    tmpCatalogPath.replace(catalogPath)
    manifestPath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"manifest": manifestPath, "catalog": catalogPath}


def validateSourceCatalogCompleteness(
    manifest: Mapping[str, Any],
    *,
    catalogRows: int,
    minFiles: int = 0,
    minRows: int = 0,
    minCatalogRows: int = 0,
    allowEmptyFullSnapshot: bool = False,
    previousManifest: Mapping[str, Any] | None = None,
    maxFileDropRatio: float = 0.05,
    maxRowDropRatio: float = 0.05,
    maxCatalogRowDropRatio: float = 0.05,
) -> dict[str, Any]:
    """Validate source catalog completeness thresholds.

    Args:
        manifest: Source manifest payload.
        catalogRows: Number of normalized catalog rows.
        minFiles: Minimum source parquet file count.
        minRows: Minimum source parquet row count.
        minCatalogRows: Minimum normalized catalog row count.
        allowEmptyFullSnapshot: True suppresses the built-in empty full snapshot
            guard. Canonical product sources should keep this False.
        previousManifest: Optional previous full manifest used as a monotonicity
            guard for source-owner jobs that run on ephemeral partial trees.
        maxFileDropRatio: Maximum accepted file-count drop vs previous manifest.
        maxRowDropRatio: Maximum accepted row-count drop vs previous manifest.
        maxCatalogRowDropRatio: Maximum accepted catalog-row drop vs previous
            manifest completeness evidence.

    Returns:
        dict[str, Any]: Validation report with ``valid`` and ``errors``.

    Raises:
        None.

    Example:
        >>> validateSourceCatalogCompleteness({"snapshotScope": "full", "files": [], "totalRows": 0}, catalogRows=0)["valid"]
        False
    """
    files = manifest.get("files") or []
    fileCount = len(files) if isinstance(files, list) else 0
    totalRows = _intOrZero(manifest.get("totalRows"))
    snapshotScope = str(manifest.get("snapshotScope") or "")
    errors: list[str] = []
    if snapshotScope == "full" and not allowEmptyFullSnapshot:
        if fileCount <= 0:
            errors.append("emptyFullSnapshot:files")
        if totalRows <= 0:
            errors.append("emptyFullSnapshot:rows")
        if catalogRows <= 0:
            errors.append("emptyFullSnapshot:catalogRows")
    if fileCount < int(minFiles):
        errors.append(f"minFiles:{fileCount}/{int(minFiles)}")
    if totalRows < int(minRows):
        errors.append(f"minRows:{totalRows}/{int(minRows)}")
    if int(catalogRows) < int(minCatalogRows):
        errors.append(f"minCatalogRows:{int(catalogRows)}/{int(minCatalogRows)}")
    previous = _previousSnapshotSummary(previousManifest)
    if snapshotScope == "full" and previous:
        previousScope = str(previous.get("snapshotScope") or "")
        if previousScope and previousScope != "full":
            errors.append(f"previousManifest:notFull:{previousScope}")
        errors.extend(
            _dropErrors(
                fileCount=fileCount,
                totalRows=totalRows,
                catalogRows=int(catalogRows),
                previous=previous,
                maxFileDropRatio=maxFileDropRatio,
                maxRowDropRatio=maxRowDropRatio,
                maxCatalogRowDropRatio=maxCatalogRowDropRatio,
            )
        )
    return {
        "valid": not errors,
        "errors": errors,
        "fileCount": fileCount,
        "totalRows": totalRows,
        "catalogRows": int(catalogRows),
        "minFiles": int(minFiles),
        "minRows": int(minRows),
        "minCatalogRows": int(minCatalogRows),
        "allowEmptyFullSnapshot": bool(allowEmptyFullSnapshot),
        "maxFileDropRatio": float(maxFileDropRatio),
        "maxRowDropRatio": float(maxRowDropRatio),
        "maxCatalogRowDropRatio": float(maxCatalogRowDropRatio),
        "previous": previous,
    }


def _previousSnapshotSummary(previousManifest: Mapping[str, Any] | None) -> dict[str, Any]:
    if not previousManifest:
        return {}
    files = previousManifest.get("files") or []
    completeness = previousManifest.get("completenessCheck")
    if not isinstance(completeness, Mapping):
        completeness = {}
    return {
        "source": str(previousManifest.get("source") or ""),
        "snapshotScope": str(previousManifest.get("snapshotScope") or ""),
        "dataAsOf": str(previousManifest.get("dataAsOf") or ""),
        "builtAt": str(previousManifest.get("builtAt") or ""),
        "fileCount": len(files) if isinstance(files, list) else 0,
        "totalRows": _intOrZero(previousManifest.get("totalRows")),
        "catalogRows": _intOrZero(completeness.get("catalogRows")) or _intOrZero(previousManifest.get("totalRows")),
    }


def _dropErrors(
    *,
    fileCount: int,
    totalRows: int,
    catalogRows: int,
    previous: Mapping[str, Any],
    maxFileDropRatio: float,
    maxRowDropRatio: float,
    maxCatalogRowDropRatio: float,
) -> list[str]:
    checks = (
        ("previousFileDrop", int(fileCount), _intOrZero(previous.get("fileCount")), float(maxFileDropRatio)),
        ("previousRowDrop", int(totalRows), _intOrZero(previous.get("totalRows")), float(maxRowDropRatio)),
        (
            "previousCatalogRowDrop",
            int(catalogRows),
            _intOrZero(previous.get("catalogRows")),
            float(maxCatalogRowDropRatio),
        ),
    )
    out: list[str] = []
    for name, current, prior, maxDropRatio in checks:
        if prior <= 0:
            continue
        minRetained = prior * (1.0 - max(0.0, maxDropRatio))
        if current < minRetained:
            out.append(f"{name}:{current}/{prior}:maxDrop={maxDropRatio:g}")
    return out


def _fileManifest(path: Path, *, source: str) -> dict[str, Any]:
    rowCount, minDate, maxDate = _fileStats(path, source=source)
    return {
        "path": path.as_posix(),
        "sizeBytes": path.stat().st_size if path.exists() else 0,
        "hash": fileHash(path) if path.exists() else "",
        "rowCount": rowCount,
        "minDate": minDate,
        "maxDate": maxDate,
    }


def _iterCatalogFrames(
    source: str,
    files: Iterable[str | Path],
    *,
    sourceDataAsOf: str,
    sourceAdapterVersion: str,
    batchSize: int = 2048,
) -> Iterator[pl.DataFrame]:
    if source in PANEL_CATALOG_SOURCES:
        yield from _iterPanelCatalogFrames(
            source,
            files,
            sourceDataAsOf=sourceDataAsOf,
            sourceAdapterVersion=sourceAdapterVersion,
        )
        return

    import pyarrow.parquet as pq

    for rawPath in files:
        parquet = pq.ParquetFile(rawPath)
        available = set(parquet.schema_arrow.names)
        columns = [name for name in CATALOG_INPUT_COLUMNS if name in available]
        for batch in parquet.iter_batches(batch_size=batchSize, columns=columns or None):
            if batch.num_rows == 0:
                continue
            rows: list[dict[str, Any]] = []
            for row in batch.to_pylist():
                out = dict(row)
                if source == "allFilings" and not _isUsableAllFilingsRow(out):
                    continue
                if source == "allFilings":
                    text = _stripPanelText(str(out.get("content_raw") or out.get("contentRaw") or ""))
                    if not text:
                        continue
                    out["content_raw"] = text
                out["source"] = source
                out.setdefault("sourceDataAsOf", sourceDataAsOf)
                out.setdefault("sourceAdapterVersion", sourceAdapterVersion)
                rows.append(out)
            frame = normalizeCatalogRows(rows)
            if frame.height:
                yield frame


def _iterPanelCatalogFrames(
    source: str,
    files: Iterable[str | Path],
    *,
    sourceDataAsOf: str,
    sourceAdapterVersion: str,
) -> Iterator[pl.DataFrame]:
    for rawPath in files:
        path = Path(rawPath)
        try:
            schema = set(pl.scan_parquet(path).collect_schema().names())
        except (pl.exceptions.PolarsError, OSError):
            continue
        if not {"rceptNo", "contentRaw"}.issubset(schema):
            continue
        readCols = [
            col for col in ("rceptNo", "period", "contentRaw", "sectionLeaf", "corp", *DATE_COLUMNS) if col in schema
        ]
        try:
            df = pl.read_parquet(path, columns=readCols)
        except (pl.exceptions.PolarsError, OSError):
            continue
        if df.height == 0:
            continue
        for col in ("period", "sectionLeaf", "corp"):
            if col not in df.columns:
                df = df.with_columns(pl.lit("").alias(col))
        try:
            rolled = (
                df.with_columns(pl.col("contentRaw").cast(pl.Utf8).str.slice(0, PANEL_SECTION_LIMIT))
                .group_by("rceptNo", maintain_order=True)
                .agg(
                    pl.col("contentRaw").alias("parts"),
                    pl.col("sectionLeaf").first().alias("sectionLeaf"),
                    pl.col("period").first().alias("period"),
                    pl.col("corp").first().alias("corp"),
                    *[pl.col(col).first().alias(col) for col in DATE_COLUMNS if col in df.columns],
                )
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        rows: list[dict[str, Any]] = []
        code = path.stem
        for row in rolled.iter_rows(named=True):
            rceptNo = str(row.get("rceptNo") or "")
            if not rceptNo:
                continue
            parts = row.get("parts") or []
            text = _stripPanelText(" ".join(part for part in parts if part))
            if not text:
                continue
            dataAsOf = _sourceDataAsOfFromPanelRow(row, source=source, rceptNo=rceptNo)
            out: dict[str, Any] = {
                "source": source,
                "rceptNo": rceptNo,
                "sectionOrder": 0,
                "period": str(row.get("period") or ""),
                "sectionLeaf": str(row.get("sectionLeaf") or ""),
                "contentRaw": text,
                "date": dataAsOf,
                "sourceDataAsOf": dataAsOf or sourceDataAsOf,
                "sourceAdapterVersion": sourceAdapterVersion,
            }
            if source == "edgarPanel":
                out["ticker"] = code
                out["accession"] = rceptNo
                out["companyName"] = str(row.get("corp") or code)
            else:
                out["stockCode"] = code
                out["companyName"] = str(row.get("corp") or code)
            rows.append(out)
        frame = normalizeCatalogRows(rows)
        if frame.height:
            yield frame


def _sourceDataAsOfFromPanelRow(row: Mapping[str, Any], *, source: str, rceptNo: str) -> str:
    explicit = normalizeSearchDate(next((row.get(col) for col in DATE_COLUMNS if row.get(col)), ""))
    if explicit:
        return explicit
    if source == "edgarPanel":
        return periodToDataAsOf(row.get("period"))
    return rceptNo[:8] if len(rceptNo) >= 8 else periodToDataAsOf(row.get("period"))


def _stripPanelText(raw: str) -> str:
    if not raw:
        return ""
    text = html.unescape(raw[: PANEL_TEXT_LIMIT * 4])
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", _BLOCK_RE.sub(" ", text))).strip()[:PANEL_TEXT_LIMIT]


def _writeCatalogSnapshot(
    source: str,
    files: Iterable[str | Path],
    path: Path,
    *,
    sourceDataAsOf: str,
    sourceAdapterVersion: str,
) -> int:
    import pyarrow.parquet as pq

    path.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    totalRows = 0
    seenDocKeys: set[str] = set()
    sourceFiles = list(files)
    if source == "allFilings":
        sourceFiles = list(reversed(sourceFiles))
    try:
        for frame in _iterCatalogFrames(
            source,
            sourceFiles,
            sourceDataAsOf=sourceDataAsOf,
            sourceAdapterVersion=sourceAdapterVersion,
        ):
            frame = _dropSeenDocKeys(frame, seenDocKeys)
            if frame.height == 0:
                continue
            table = frame.to_arrow()
            if writer is None:
                writer = pq.ParquetWriter(str(path), table.schema, compression="zstd")
            writer.write_table(table)
            totalRows += frame.height
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        normalizeCatalogRows([]).write_parquet(path)
    return totalRows


def _dropSeenDocKeys(frame: pl.DataFrame, seenDocKeys: set[str]) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in frame.iter_rows(named=True):
        key = str(row.get("docKey") or "")
        if key and key in seenDocKeys:
            continue
        if key:
            seenDocKeys.add(key)
        rows.append(dict(row))
    if not rows:
        return normalizeCatalogRows([])
    return pl.DataFrame(rows).select(frame.columns)


def _isUsableAllFilingsRow(row: Mapping[str, Any]) -> bool:
    status = str(row.get("fetch_status") or "ok").strip().lower()
    if status != "ok":
        return False
    text = row.get("content_raw") or row.get("contentRaw") or row.get("searchText") or row.get("text")
    return bool(str(text or "").strip())


def _fileStats(path: Path, *, source: str) -> tuple[int, str, str]:
    if not path.exists():
        return 0, "", ""
    lf = pl.scan_parquet(path)
    columns = set(lf.collect_schema().names())
    dateColumn = next((name for name in DATE_COLUMNS if name in columns), None)
    if dateColumn is None:
        if source == "dartPanel" and "rceptNo" in columns:
            row = (
                lf.select(
                    pl.len().alias("rowCount"),
                    pl.col("rceptNo").cast(pl.Utf8, strict=False).str.slice(0, 8).min().alias("minDate"),
                    pl.col("rceptNo").cast(pl.Utf8, strict=False).str.slice(0, 8).max().alias("maxDate"),
                )
                .collect()
                .row(0, named=True)
            )
            return (
                int(row["rowCount"]),
                normalizeSearchDate(row.get("minDate")),
                normalizeSearchDate(row.get("maxDate")),
            )
        if "period" in columns:
            row = (
                lf.select(
                    pl.len().alias("rowCount"),
                    pl.col("period").cast(pl.Utf8, strict=False).min().alias("minPeriod"),
                    pl.col("period").cast(pl.Utf8, strict=False).max().alias("maxPeriod"),
                )
                .collect()
                .row(0, named=True)
            )
            return (
                int(row["rowCount"]),
                periodToDataAsOf(row.get("minPeriod")),
                periodToDataAsOf(row.get("maxPeriod")),
            )
        row = lf.select(pl.len().alias("rowCount")).collect().row(0, named=True)
        return int(row["rowCount"]), "", ""
    row = (
        lf.select(
            pl.len().alias("rowCount"),
            pl.col(dateColumn).cast(pl.Utf8, strict=False).min().alias("minDate"),
            pl.col(dateColumn).cast(pl.Utf8, strict=False).max().alias("maxDate"),
        )
        .collect()
        .row(0, named=True)
    )
    return int(row["rowCount"]), normalizeSearchDate(row.get("minDate")), normalizeSearchDate(row.get("maxDate"))


def _intOrZero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
