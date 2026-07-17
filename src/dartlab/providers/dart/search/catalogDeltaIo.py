"""Disk-bounded parquet operations for search catalog deltas.

Catalog snapshots contain the full searchable text and can be hundreds of MB.
Loading two snapshots and converting them to Python dictionaries multiplies RSS
until a GitHub hosted runner is killed.  This module keeps joins on the compact
fingerprint columns and materializes only the changed rows.
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl

from dartlab.providers.dart.search.catalog import CATALOG_COLUMNS

_FINGERPRINT_COLUMNS = ("docKey", "textHash", "metadataHash", "deleted")
_CONTENT_COLUMNS = (
    "docKey",
    "rcept_no",
    "section_order",
    "corp_code",
    "corp_name",
    "stock_code",
    "rcept_dt",
    "report_nm",
    "section_title",
    "section_content",
    "source",
    "sourceRef",
    "sourceDataAsOf",
    "url",
    "deleted",
)


def isCanonicalCatalogParquet(path: str | Path | None) -> bool:
    """Return whether a parquet already has the canonical catalog schema.

    Args:
        path: Candidate parquet path.

    Returns:
        True when every canonical catalog column is present.

    Raises:
        None. Missing and corrupt files return False.

    Example:
        >>> isCanonicalCatalogParquet("missing.parquet")
        False
    """
    if path is None or not Path(path).exists() or Path(path).suffix.lower() != ".parquet":
        return False
    try:
        return set(CATALOG_COLUMNS).issubset(pl.read_parquet_schema(path))
    except (OSError, pl.exceptions.PolarsError):
        return False


def catalogDeltaSummaryFromPaths(previousPath: str | Path | None, currentPath: str | Path) -> dict[str, int]:
    """Return catalog delta counts without loading either text payload.

    Args:
        previousPath: Immutable main catalog snapshot, or None for bootstrap.
        currentPath: Current canonical catalog snapshot.

    Returns:
        New, changed, deleted, unchanged, and total row counts.

    Raises:
        ValueError: When a catalog lacks canonical columns.
        OSError: When parquet metadata cannot be read.

    Example:
        >>> callable(catalogDeltaSummaryFromPaths)
        True
    """
    current = _fingerprints(currentPath)
    totalCurrent = _count(current)
    if previousPath is None or not Path(previousPath).exists():
        deletedCurrent = _scalar(current.select(_deletedExpr().sum()))
        return {
            "newDocs": totalCurrent - deletedCurrent,
            "changedDocs": 0,
            "deletedDocs": deletedCurrent,
            "unchangedDocs": 0,
            "totalCurrentDocs": totalCurrent,
            "totalPreviousDocs": 0,
        }

    previous = _fingerprints(previousPath)
    previousTagged = previous.select(
        "docKey",
        pl.col("textHash").alias("__previousTextHash"),
        pl.col("metadataHash").alias("__previousMetadataHash"),
        pl.col("deleted").alias("__previousDeleted"),
        pl.lit(True).alias("__previousExists"),
    )
    joined = current.join(previousTagged, on="docKey", how="left")
    deleted = _deletedExpr()
    previousExists = pl.col("__previousExists").fill_null(False)
    same = (
        (pl.col("textHash") == pl.col("__previousTextHash"))
        & (pl.col("metadataHash") == pl.col("__previousMetadataHash"))
        & (deleted == pl.col("__previousDeleted").fill_null(False))
    ).fill_null(False)
    metrics = joined.select(
        ((~deleted) & (~previousExists)).sum().alias("newDocs"),
        ((~deleted) & previousExists & (~same)).sum().alias("changedDocs"),
        deleted.sum().alias("deletedCurrentDocs"),
        ((~deleted) & previousExists & same).sum().alias("unchangedDocs"),
    ).collect(engine="streaming")
    row = metrics.row(0, named=True)
    missing = _count(previous.join(current.select("docKey"), on="docKey", how="anti"))
    return {
        "newDocs": int(row["newDocs"] or 0),
        "changedDocs": int(row["changedDocs"] or 0),
        "deletedDocs": int(row["deletedCurrentDocs"] or 0) + missing,
        "unchangedDocs": int(row["unchangedDocs"] or 0),
        "totalCurrentDocs": totalCurrent,
        "totalPreviousDocs": _count(previous),
    }


def exportDeltaRowsForContentIndexFromPaths(
    previousPath: str | Path,
    currentPath: str | Path,
) -> pl.DataFrame:
    """Materialize only changed rows and tombstones from two parquet snapshots.

    Args:
        previousPath: Immutable main catalog snapshot.
        currentPath: Current canonical catalog snapshot.

    Returns:
        Field-index compatible changed rows and deletion tombstones.

    Raises:
        ValueError: When a catalog lacks canonical columns.
        OSError: When parquet input cannot be read.

    Example:
        >>> callable(exportDeltaRowsForContentIndexFromPaths)
        True
    """
    current = _catalog(currentPath)
    previous = _catalog(previousPath)
    currentFingerprints = _fingerprints(currentPath)
    previousTagged = _fingerprints(previousPath).select(
        "docKey",
        pl.col("textHash").alias("__previousTextHash"),
        pl.col("metadataHash").alias("__previousMetadataHash"),
        pl.col("deleted").alias("__previousDeleted"),
        pl.lit(True).alias("__previousExists"),
    )
    tagged = current.join(previousTagged, on="docKey", how="left")
    deleted = _deletedExpr()
    previousExists = pl.col("__previousExists").fill_null(False)
    same = (
        (pl.col("textHash") == pl.col("__previousTextHash"))
        & (pl.col("metadataHash") == pl.col("__previousMetadataHash"))
        & (deleted == pl.col("__previousDeleted").fill_null(False))
    ).fill_null(False)
    changed = tagged.filter(deleted | (~previousExists) | (~same)).select(CATALOG_COLUMNS)
    tombstones = (
        previous.join(currentFingerprints.select("docKey"), on="docKey", how="anti")
        .with_columns(pl.lit("").alias("searchText"), pl.lit(True).alias("deleted"))
        .select(CATALOG_COLUMNS)
    )
    return pl.concat([_contentRows(changed), _contentRows(tombstones)], how="vertical_relaxed").collect(
        engine="streaming"
    )


def activeCatalogRowsFromPath(path: str | Path) -> int:
    """Count active rows using parquet projection only.

    Args:
        path: Canonical catalog parquet path.

    Returns:
        Number of rows not marked deleted.

    Raises:
        ValueError: When the catalog lacks canonical columns.
        OSError: When parquet input cannot be read.

    Example:
        >>> callable(activeCatalogRowsFromPath)
        True
    """
    catalog = _catalog(path)
    return _count(catalog.filter(~_deletedExpr()))


def sourceCountsFromPath(path: str | Path) -> dict[str, int]:
    """Count rows per source without reading searchable text.

    Args:
        path: Canonical catalog parquet path.

    Returns:
        Mapping from canonical source name to row count.

    Raises:
        OSError: When parquet input cannot be read.

    Example:
        >>> callable(sourceCountsFromPath)
        True
    """
    rows = (
        pl.scan_parquet(path)
        .select(pl.col("source").cast(pl.Utf8).fill_null(""))
        .group_by("source")
        .len()
        .collect(engine="streaming")
    )
    return {str(row["source"]): int(row["len"]) for row in rows.iter_rows(named=True)}


def filterCatalogByDate(sourcePath: str | Path, outPath: str | Path, sinceDate: str) -> int:
    """Stream a date-filtered canonical catalog to an atomically replaced parquet.

    Args:
        sourcePath: Full canonical catalog parquet.
        outPath: Destination parquet replaced atomically.
        sinceDate: Inclusive YYYYMMDD lower bound.

    Returns:
        Number of rows written.

    Raises:
        ValueError: When the catalog lacks canonical columns.
        OSError: When the destination cannot be replaced.

    Example:
        >>> callable(filterCatalogByDate)
        True
    """
    out = Path(outPath)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.name}.tmp")
    tmp.unlink(missing_ok=True)
    filtered = _catalog(sourcePath).filter(
        pl.col("date").cast(pl.Utf8).fill_null("").str.replace_all("-", "") >= str(sinceDate)
    )
    filtered.sink_parquet(tmp, compression="zstd", maintain_order=False)
    os.replace(tmp, out)
    return _count(_catalog(out))


def _catalog(path: str | Path) -> pl.LazyFrame:
    schema = set(pl.read_parquet_schema(path))
    missing = [column for column in CATALOG_COLUMNS if column not in schema]
    if missing:
        raise ValueError(f"catalog missing canonical columns: {','.join(missing)}")
    return pl.scan_parquet(path).select(CATALOG_COLUMNS)


def _fingerprints(path: str | Path) -> pl.LazyFrame:
    return _catalog(path).select(_FINGERPRINT_COLUMNS)


def _contentRows(catalog: pl.LazyFrame) -> pl.LazyFrame:
    source = pl.col("source").cast(pl.Utf8).fill_null("")
    runtimeSource = (
        pl.when(source == "dartPanel")
        .then(pl.lit("panel"))
        .when(source == "edgarPanel")
        .then(pl.lit("edgar-panel"))
        .when(source == "newsPublic")
        .then(pl.lit("news"))
        .otherwise(source)
    )
    deleted = _deletedExpr()
    text = pl.col("searchText").cast(pl.Utf8).fill_null("")
    return catalog.select(
        _text("docKey").alias("docKey"),
        _firstText("rceptNo", "sourceRef").alias("rcept_no"),
        pl.col("sectionOrder").cast(pl.Int64, strict=False).fill_null(0).alias("section_order"),
        _text("corpCode").alias("corp_code"),
        _text("companyName").alias("corp_name"),
        _text("stockCode").alias("stock_code"),
        _text("date").alias("rcept_dt"),
        _text("reportName").alias("report_nm"),
        _firstText("title", "sectionKey").alias("section_title"),
        pl.when(deleted).then(pl.lit("")).otherwise(text).alias("section_content"),
        runtimeSource.alias("source"),
        _text("sourceRef").alias("sourceRef"),
        _firstText("sourceDataAsOf", "date").alias("sourceDataAsOf"),
        pl.when(source == "newsPublic").then(_text("url")).otherwise(pl.lit("")).alias("url"),
        deleted.alias("deleted"),
    ).select(_CONTENT_COLUMNS)


def _text(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Utf8, strict=False).fill_null("")


def _firstText(primary: str, fallback: str) -> pl.Expr:
    value = _text(primary)
    return pl.when(value != "").then(value).otherwise(_text(fallback))


def _deletedExpr() -> pl.Expr:
    return pl.col("deleted").cast(pl.Boolean, strict=False).fill_null(False)


def _count(frame: pl.LazyFrame) -> int:
    return int(frame.select(pl.len()).collect(engine="streaming").item() or 0)


def _scalar(frame: pl.LazyFrame) -> int:
    return int(frame.collect(engine="streaming").item() or 0)
