"""EDGAR universe account scan performance prototype.

The production owner opens one parquet per listed CIK and parses every fiscal
year in Python.  This attempt keeps its observable wide-frame contract while
moving filtering and per-year reduction into one source-native scan.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence

import polars as pl


@dataclass(frozen=True)
class EdgarScanContext:
    """Resolved runtime inputs for one EDGAR account scan.

    Summary
    -------
    Keep the runtime data root, ticker mapping, and account tags together.

    Description
    -----------
    ``listedPaths`` mirrors the production owner's early CIK guard.  It is not
    a newly baked dataset.  Every path still points at the runtime EDGAR SSOT.

    Parameters
    ----------
    allPaths:
        Every company-facts parquet found under the runtime EDGAR directory.
    listedPaths:
        Existing parquet paths whose filename CIK occurs in ``tickerMap``.
    tickerMap:
        Filename CIK to ticker mapping with the same last-row-wins rule as the
        production ``dict(zip(...))`` implementation.
    tagKeys:
        Lowercase US-GAAP tags mapped to the requested canonical account.

    Returns
    -------
    EdgarScanContext
        Immutable scan input manifest.

    Raises
    ------
    None
        Construction itself performs no validation.

    Examples
    --------
    ``context = runtimeContext("sales")``

    Notes
    -----
    The parquet's internal ``cik`` column is deliberately not an identity
    source.  At least one real file contains ``0000000000`` there, while the
    production owner correctly derives identity from the filename.

    See Also
    --------
    runtimeContext
        Resolve this manifest from DartLab runtime owners.
    """

    allPaths: tuple[Path, ...]
    listedPaths: tuple[Path, ...]
    tickerMap: dict[str, str]
    tagKeys: frozenset[str]


def runtimeContext(snakeId: str = "sales") -> EdgarScanContext:
    """Resolve EDGAR scan inputs through existing runtime owners.

    Summary
    -------
    Build a transient, source-referenced scan manifest.

    Description
    -----------
    The function delegates data location, ticker membership, and account tag
    mapping to their current owners.  It creates no persistent index or copy.

    Parameters
    ----------
    snakeId:
        Canonical DART account identifier, for example ``sales``.

    Returns
    -------
    EdgarScanContext
        Runtime paths and mappings required by the prototype engines.

    Raises
    ------
    FileNotFoundError
        Propagated if a required runtime data owner cannot resolve its source.

    Examples
    --------
    ``runtimeContext("sales").listedPaths``

    Notes
    -----
    ``listedPaths`` is the file-pruned equivalent of the production
    ``_EdgarFileProcessor`` guard, which checks filename CIK before reading.

    See Also
    --------
    scanDuckDbNative
        Consume the manifest with DuckDB source-native aggregation.
    """
    from dartlab.core.dataLoader import _dataDir
    from dartlab.core.edgarClient import loadTickers
    from dartlab.providers.edgar.finance.scanAccount import _buildEdgarTagKeys

    edgarDir = Path(_dataDir("edgar"))
    allPaths = tuple(sorted(edgarDir.glob("*.parquet")))
    tickers = loadTickers()
    tickerMap = dict(zip(tickers["cik"].to_list(), tickers["ticker"].to_list()))
    listedPaths = tuple(path for cik in tickerMap if (path := edgarDir / f"{cik}.parquet").exists())
    return EdgarScanContext(
        allPaths=allPaths,
        listedPaths=listedPaths,
        tickerMap=tickerMap,
        tagKeys=frozenset(_buildEdgarTagKeys(snakeId)),
    )


def _longToWide(longFrame: pl.DataFrame, tickerMap: dict[str, str]) -> pl.DataFrame:
    """Convert reduced filename-CIK rows to the production wide schema."""
    if longFrame.is_empty():
        return pl.DataFrame(schema={"stockCode": pl.Utf8})

    tickerFrame = pl.DataFrame(
        {
            "fileCik": list(tickerMap),
            "stockCode": list(tickerMap.values()),
        }
    )
    values = (
        longFrame.join(tickerFrame, on="fileCik", how="inner")
        .sort(["fileCik", "period"])
        .group_by(["stockCode", "period"], maintain_order=True)
        .agg(pl.col("amount").first())
    )
    result = values.pivot(on="period", index="stockCode", values="amount")
    periodCols = sorted((name for name in result.columns if name != "stockCode"), reverse=True)
    result = result.select(["stockCode", *periodCols])

    from dartlab.providers.edgar.finance.scanAccount import _joinCorpName

    return _joinCorpName(result)


def _yearRowsToWide(yearRows: pl.DataFrame, tickerMap: dict[str, str], *, freq: str) -> pl.DataFrame:
    """Apply the production annual or quarterly wide-frame semantics."""
    if yearRows.is_empty():
        return pl.DataFrame(schema={"stockCode": pl.Utf8})

    if freq == "Y":
        longFrame = (
            yearRows.filter(pl.col("fyVal").is_not_null())
            .with_columns(pl.col("fy").cast(pl.Utf8).alias("period"), pl.col("fyVal").alias("amount"))
            .select(["fileCik", "period", "amount"])
        )
        return _longToWide(longFrame, tickerMap)

    quarters = (
        yearRows.select(["fileCik", "fy", "q1", "q2", "q3"])
        .unpivot(
            index=["fileCik", "fy"],
            on=["q1", "q2", "q3"],
            variable_name="quarter",
            value_name="amount",
        )
        .filter(pl.col("amount").is_not_null())
        .with_columns((pl.col("fy").cast(pl.Utf8) + pl.col("quarter").str.to_uppercase()).alias("period"))
        .select(["fileCik", "period", "amount"])
    )
    fourth = (
        yearRows.filter(pl.col("fyVal").is_not_null())
        .with_columns(
            (pl.col("fy").cast(pl.Utf8) + pl.lit("Q4")).alias("period"),
            pl.when(
                pl.all_horizontal(
                    pl.col("q1").is_not_null(),
                    pl.col("q2").is_not_null(),
                    pl.col("q3").is_not_null(),
                )
            )
            .then(pl.col("fyVal") - (pl.col("q1") + pl.col("q2") + pl.col("q3")))
            .otherwise(pl.col("fyVal"))
            .alias("amount"),
        )
        .select(["fileCik", "period", "amount"])
    )
    return _longToWide(pl.concat([quarters, fourth]), tickerMap)


def scanDuckDbNative(
    context: EdgarScanContext,
    *,
    freq: Literal["Q", "Y"] = "Q",
    pruneListed: bool = True,
    threads: int = 4,
    memoryLimitMb: int = 512,
) -> pl.DataFrame:
    """Scan EDGAR parquet directly with one DuckDB reduction query.

    Summary
    -------
    Replace thousands of Python file jobs with one source-native aggregation.

    Description
    -----------
    DuckDB reads the runtime parquet paths, pushes projection and predicates to
    the source, and returns one row per filename CIK and fiscal year.  The SQL
    reproduces the production owner's selection rules: FY uses the first source
    row, Q1 through Q3 use the smallest absolute value with deterministic ties,
    and Q4 is FY less Q1 through Q3 only when all three quarters exist.

    Parameters
    ----------
    context:
        Runtime scan manifest.
    freq:
        ``Q`` for quarterly wide output or ``Y`` for annual output.
    pruneListed:
        Read only filename CIKs in the ticker map when true.
    threads:
        DuckDB worker count.
    memoryLimitMb:
        DuckDB memory limit before spill.

    Returns
    -------
    polars.DataFrame
        Production-compatible stockCode, corpName, and period columns.

    Raises
    ------
    duckdb.Error
        Propagated when the source scan or aggregation fails.

    Examples
    --------
    ``scanDuckDbNative(runtimeContext("sales"), freq="Q")``

    Notes
    -----
    ``filename`` is the CIK identity SSOT for parity with production.  The SQL
    result is bounded to company-year rows before crossing into Python.

    See Also
    --------
    scanPolarsNative
        Alternative source-native implementation using Polars streaming.
    """
    paths = context.listedPaths if pruneListed else context.allPaths
    if not paths or not context.tagKeys:
        return pl.DataFrame(schema={"stockCode": pl.Utf8})
    yearRows = _duckYearRows(paths, context.tagKeys, threads=threads, memoryLimitMb=memoryLimitMb)
    return _yearRowsToWide(yearRows, context.tickerMap, freq=freq)


_DUCK_YEAR_SQL = """
    SELECT
        regexp_extract(filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
        fy,
        arg_min(val, file_row_number)
            FILTER (WHERE fp = 'FY') AS fyVal,
        arg_min(
            val,
            struct_pack(absVal := abs(val), tieVal := val, rowNum := file_row_number)
        ) FILTER (WHERE fp = 'Q1') AS q1,
        arg_min(
            val,
            struct_pack(absVal := abs(val), tieVal := val, rowNum := file_row_number)
        ) FILTER (WHERE fp = 'Q2') AS q2,
        arg_min(
            val,
            struct_pack(absVal := abs(val), tieVal := val, rowNum := file_row_number)
        ) FILTER (WHERE fp = 'Q3') AS q3
    FROM read_parquet(?, filename = true, file_row_number = true)
    WHERE namespace = 'us-gaap'
      AND lower(tag) IN (SELECT unnest(?))
      AND starts_with(unit, 'USD')
      AND fy BETWEEN 2000 AND 2030
      AND fp IN ('FY', 'Q1', 'Q2', 'Q3')
    GROUP BY fileCik, fy
"""


def _duckYearRows(
    paths: Sequence[Path],
    tagKeys: Sequence[str] | frozenset[str],
    *,
    threads: int,
    memoryLimitMb: int,
) -> pl.DataFrame:
    """Reduce one path batch to filename-CIK and fiscal-year rows."""
    import duckdb

    connection = duckdb.connect(":memory:")
    try:
        connection.execute(f"PRAGMA threads={max(1, int(threads))}")
        connection.execute(f"PRAGMA memory_limit='{max(64, int(memoryLimitMb))}MB'")
        return connection.execute(
            _DUCK_YEAR_SQL,
            [[str(path) for path in paths], sorted(tagKeys)],
        ).pl()
    finally:
        connection.close()


def scanDuckDbBatched(
    context: EdgarScanContext,
    *,
    freq: Literal["Q", "Y"] = "Q",
    batchFiles: int = 512,
    threads: int = 4,
    memoryLimitMb: int = 64,
) -> pl.DataFrame:
    """Bound source metadata and buffers by scanning fixed file batches.

    Summary
    -------
    Read every listed file once while bounding each DuckDB source scan.

    Description
    -----------
    The single-query candidate registers all 6,758 paths at once.  This variant
    partitions that transient manifest, fully reduces each batch to company-year
    rows, closes its DuckDB connection, and concatenates only reduced results.

    Parameters
    ----------
    context:
        Runtime scan manifest.
    freq:
        ``Q`` or ``Y`` wide output frequency.
    batchFiles:
        Maximum parquet files registered by one DuckDB connection.
    threads:
        DuckDB workers per batch.
    memoryLimitMb:
        DuckDB spill threshold per batch.

    Returns
    -------
    polars.DataFrame
        Production-compatible wide frame.

    Raises
    ------
    ValueError
        If ``batchFiles`` is not positive.

    Examples
    --------
    ``scanDuckDbBatched(runtimeContext("sales"), batchFiles=512)``

    Notes
    -----
    No parquet is read twice.  The repeated unit is query setup, not source
    rows, and every intermediate crossing into Python is already reduced.

    See Also
    --------
    scanDuckDbNative
        One-query speed-oriented candidate.
    """
    if batchFiles <= 0:
        raise ValueError("batchFiles must be positive")
    if not context.listedPaths or not context.tagKeys:
        return pl.DataFrame(schema={"stockCode": pl.Utf8})
    parts = []
    for offset in range(0, len(context.listedPaths), batchFiles):
        paths = context.listedPaths[offset : offset + batchFiles]
        parts.append(_duckYearRows(paths, context.tagKeys, threads=threads, memoryLimitMb=memoryLimitMb))
    return _yearRowsToWide(pl.concat(parts), context.tickerMap, freq=freq)


def scanAccountsDuckDbNative(
    contexts: Mapping[str, EdgarScanContext],
    *,
    freq: Literal["Q", "Y"] = "Q",
    threads: int = 4,
    memoryLimitMb: int = 128,
) -> dict[str, pl.DataFrame]:
    """Fuse multiple canonical accounts into one parquet scan.

    Summary
    -------
    Scan the EDGAR universe once for every requested account.

    Description
    -----------
    A transient tag-to-measure relation is joined to the source scan.  The
    aggregation key includes ``measureId``, so overlapping tags retain the same
    independent semantics as separate ``scanAccount`` calls.  Wide frames are
    returned by measure only after the shared source reduction.

    Parameters
    ----------
    contexts:
        Ordered mapping of canonical measure ID to runtime context.
    freq:
        ``Q`` or ``Y`` output frequency.
    threads:
        DuckDB workers for the shared scan.
    memoryLimitMb:
        DuckDB spill threshold.

    Returns
    -------
    dict[str, polars.DataFrame]
        One production-compatible wide frame per requested measure.

    Raises
    ------
    ValueError
        If contexts do not share the same source paths and ticker mapping.

    Examples
    --------
    ``scanAccountsDuckDbNative({"sales": salesContext, "operating_profit": opContext})``

    Notes
    -----
    This is an internal owner-bulk candidate, not a new public axis.  A data
    workbench planner can split the returned mapping into request partitions.

    See Also
    --------
    scanDuckDbNative
        Single-account compatibility path.
    """
    import duckdb

    if not contexts:
        return {}
    items = list(contexts.items())
    first = items[0][1]
    if any(
        context.listedPaths != first.listedPaths or context.tickerMap != first.tickerMap for _, context in items[1:]
    ):
        raise ValueError("all account contexts must share one EDGAR source manifest")

    tagMap = pl.DataFrame(
        [{"tagLower": tag, "measureId": measureId} for measureId, context in items for tag in sorted(context.tagKeys)]
    ).unique()
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(f"PRAGMA threads={max(1, int(threads))}")
        connection.execute(f"PRAGMA memory_limit='{max(64, int(memoryLimitMb))}MB'")
        connection.register("requested_tags", tagMap)
        yearRows = connection.execute(
            """
            SELECT
                requested_tags.measureId,
                regexp_extract(source.filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
                source.fy,
                arg_min(source.val, source.file_row_number)
                    FILTER (WHERE source.fp = 'FY') AS fyVal,
                arg_min(
                    source.val,
                    struct_pack(
                        absVal := abs(source.val),
                        tieVal := source.val,
                        rowNum := source.file_row_number
                    )
                ) FILTER (WHERE source.fp = 'Q1') AS q1,
                arg_min(
                    source.val,
                    struct_pack(
                        absVal := abs(source.val),
                        tieVal := source.val,
                        rowNum := source.file_row_number
                    )
                ) FILTER (WHERE source.fp = 'Q2') AS q2,
                arg_min(
                    source.val,
                    struct_pack(
                        absVal := abs(source.val),
                        tieVal := source.val,
                        rowNum := source.file_row_number
                    )
                ) FILTER (WHERE source.fp = 'Q3') AS q3
            FROM read_parquet(?, filename = true, file_row_number = true) AS source
            JOIN requested_tags ON lower(source.tag) = requested_tags.tagLower
            WHERE source.namespace = 'us-gaap'
              AND starts_with(source.unit, 'USD')
              AND source.fy BETWEEN 2000 AND 2030
              AND source.fp IN ('FY', 'Q1', 'Q2', 'Q3')
            GROUP BY requested_tags.measureId, fileCik, source.fy
            """,
            [[str(path) for path in first.listedPaths]],
        ).pl()
    finally:
        connection.close()

    return {
        measureId: _yearRowsToWide(
            yearRows.filter(pl.col("measureId") == measureId).drop("measureId"),
            first.tickerMap,
            freq=freq,
        )
        for measureId, _ in items
    }


def scanPolarsNative(
    context: EdgarScanContext,
    *,
    freq: Literal["Q", "Y"] = "Q",
    pruneListed: bool = True,
) -> pl.DataFrame:
    """Scan all selected parquet files as one Polars lazy source.

    Summary
    -------
    Remove per-file Python dispatch while retaining Polars as the scan engine.

    Description
    -----------
    Polars performs a single lazy multi-file scan with filter and projection
    pushdown.  A global row index preserves the file-row ordering needed for FY
    first-value parity, then vectorized sorts reproduce quarterly selection.

    Parameters
    ----------
    context:
        Runtime scan manifest.
    freq:
        ``Q`` for quarterly wide output or ``Y`` for annual output.
    pruneListed:
        Read only filename CIKs in the ticker map when true.

    Returns
    -------
    polars.DataFrame
        Production-compatible stockCode, corpName, and period columns.

    Raises
    ------
    polars.exceptions.PolarsError
        Propagated when a parquet source cannot be scanned.

    Examples
    --------
    ``scanPolarsNative(runtimeContext("sales"), freq="Q")``

    Notes
    -----
    This arm materializes the roughly one million matched sales rows before the
    year reduction.  It is source-native but less memory-bounded than DuckDB.

    See Also
    --------
    scanDuckDbNative
        Source-native aggregation that crosses into Python after reduction.
    """
    paths = context.listedPaths if pruneListed else context.allPaths
    if not paths or not context.tagKeys:
        return pl.DataFrame(schema={"stockCode": pl.Utf8})

    matched = (
        pl.scan_parquet(
            [str(path) for path in paths],
            include_file_paths="_sourcePath",
            row_index_name="_sourceRow",
        )
        .filter(
            (pl.col("namespace") == "us-gaap")
            & pl.col("tag").str.to_lowercase().is_in(sorted(context.tagKeys))
            & pl.col("unit").str.starts_with("USD")
            & pl.col("fy").is_not_null()
            & (pl.col("fy") >= 2000)
            & (pl.col("fy") <= 2030)
            & pl.col("fp").is_in(["FY", "Q1", "Q2", "Q3"])
        )
        .select(["_sourcePath", "_sourceRow", "val", "fy", "fp"])
        .collect(engine="streaming")
        .with_columns(pl.col("_sourcePath").str.extract(r"([0-9]{10})[.]parquet$", 1).alias("fileCik"))
    )

    yearRows = _matchedToYearRows(matched)
    return _yearRowsToWide(yearRows, context.tickerMap, freq=freq)


def _matchedToYearRows(matched: pl.DataFrame) -> pl.DataFrame:
    """Reduce filtered source rows with production FY and quarter rules."""
    annual = (
        matched.filter((pl.col("fp") == "FY") & pl.col("val").is_not_null())
        .sort(["fileCik", "fy", "_sourceRow"])
        .unique(["fileCik", "fy"], keep="first", maintain_order=True)
        .select(["fileCik", "fy", pl.col("val").alias("fyVal")])
    )
    quarter = (
        matched.filter(pl.col("fp").is_in(["Q1", "Q2", "Q3"]) & pl.col("val").is_not_null())
        .with_columns(pl.col("val").abs().alias("_absVal"))
        .sort(["fileCik", "fy", "fp", "_absVal", "val", "_sourceRow"])
        .unique(["fileCik", "fy", "fp"], keep="first", maintain_order=True)
        .pivot(on="fp", index=["fileCik", "fy"], values="val")
    )
    quarter = quarter.rename({name: name.lower() for name in ("Q1", "Q2", "Q3") if name in quarter.columns})
    for name in ("q1", "q2", "q3"):
        if name not in quarter.columns:
            quarter = quarter.with_columns(pl.lit(None, dtype=pl.Float64).alias(name))
    yearRows = annual.join(quarter, on=["fileCik", "fy"], how="full", coalesce=True).select(
        ["fileCik", "fy", "fyVal", "q1", "q2", "q3"]
    )
    return yearRows


def scanArrowBatched(
    context: EdgarScanContext,
    *,
    freq: Literal["Q", "Y"] = "Q",
    batchFiles: int = 256,
    rowBatchSize: int = 65_536,
) -> pl.DataFrame:
    """Stream listed files through bounded Arrow dataset batches.

    Summary
    -------
    Combine Arrow predicate pushdown with bounded Polars reductions.

    Description
    -----------
    Each transient Arrow dataset contains at most ``batchFiles`` source files.
    The scanner yields record batches after source filtering.  Only that bounded
    slice is converted to Polars and reduced to company-year rows before the
    next source slice is opened.

    Parameters
    ----------
    context:
        Runtime scan manifest.
    freq:
        ``Q`` or ``Y`` wide output frequency.
    batchFiles:
        Maximum source fragments in one Arrow dataset.
    rowBatchSize:
        Maximum rows in one Arrow record batch.

    Returns
    -------
    polars.DataFrame
        Production-compatible wide frame.

    Raises
    ------
    ValueError
        If either batch size is not positive.

    Examples
    --------
    ``scanArrowBatched(runtimeContext("sales"), batchFiles=256)``

    Notes
    -----
    Every parquet belongs to exactly one source batch and is read once.  Unlike
    the all-file Polars arm, matched rows from separate source batches never
    coexist in memory before company-year reduction.

    See Also
    --------
    scanDuckDbBatched
        DuckDB spill-oriented bounded alternative.
    """
    if batchFiles <= 0 or rowBatchSize <= 0:
        raise ValueError("batch sizes must be positive")
    if not context.listedPaths or not context.tagKeys:
        return pl.DataFrame(schema={"stockCode": pl.Utf8})

    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.dataset as ds

    tagValues = pa.array(sorted(context.tagKeys))
    predicate = (
        (ds.field("namespace") == "us-gaap")
        & pc.is_in(pc.utf8_lower(ds.field("tag")), value_set=tagValues)
        & pc.starts_with(ds.field("unit"), pattern="USD")
        & ds.field("fy").is_valid()
        & (ds.field("fy") >= 2000)
        & (ds.field("fy") <= 2030)
        & ds.field("fp").isin(["FY", "Q1", "Q2", "Q3"])
    )
    reduced = []
    for offset in range(0, len(context.listedPaths), batchFiles):
        paths = context.listedPaths[offset : offset + batchFiles]
        dataset = ds.dataset([str(path) for path in paths], format="parquet")
        batches = [
            batch
            for batch in dataset.scanner(
                columns=["__filename", "val", "fy", "fp"],
                filter=predicate,
                batch_size=rowBatchSize,
                batch_readahead=1,
                fragment_readahead=1,
                use_threads=False,
            ).to_batches()
            if batch.num_rows
        ]
        if not batches:
            continue
        matched = (
            pl.from_arrow(pa.Table.from_batches(batches), rechunk=False)
            .rename({"__filename": "_sourcePath"})
            .with_row_index("_sourceRow")
            .with_columns(pl.col("_sourcePath").str.extract(r"([0-9]{10})[.]parquet$", 1).alias("fileCik"))
        )
        reduced.append(_matchedToYearRows(matched))
        pa.default_memory_pool().release_unused()
    if not reduced:
        return pl.DataFrame(schema={"stockCode": pl.Utf8})
    return _yearRowsToWide(pl.concat(reduced), context.tickerMap, freq=freq)


__all__ = [
    "EdgarScanContext",
    "runtimeContext",
    "scanArrowBatched",
    "scanAccountsDuckDbNative",
    "scanDuckDbBatched",
    "scanDuckDbNative",
    "scanPolarsNative",
]
