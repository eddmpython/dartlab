"""EDGAR finance parquet 스캔 실행과 결과 조립.

DuckDB 경로와 파일 loop 경로, 두 실행 전략을 소유한다. 계정 이름 해석은
``taxonomy``, 공개 호출 계약은 ``api`` 가 맡는다.
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

from dartlab.providers.edgar.finance.scanAccount.sql import (
    _DUCKDB_BATCH_MEMORY_LIMIT_MB,
    _DUCKDB_BATCH_THREADS,
    _DUCKDB_BATCH_YEAR_SQL,
    _DUCKDB_MEMORY_LIMIT_MB,
    _DUCKDB_THREADS,
    _DUCKDB_YEAR_SQL,
)
from dartlab.providers.edgar.finance.scanAccount.taxonomy import (
    _joinCorpName,
)
from dartlab.providers.edgar.finance.scanAccount.types import (
    EdgarScanError,
    EdgarScanExecutionError,
    EdgarScanMappingError,
    EdgarScanStorageError,
    _TaxonomyTagKeys,
    _TickerUniverse,
)

_log = logging.getLogger(__name__)


class _EdgarFileProcessor:
    """EDGAR parquet 파일별 처리."""

    __slots__ = ("tagKeys", "freq", "cikToTicker", "isInstant")

    def __init__(
        self,
        tagKeys: _TaxonomyTagKeys,
        *,
        freq: str,
        cikToTicker: dict[str, str],
        isInstant: bool,
    ):
        self.tagKeys = tagKeys
        self.freq = freq
        self.cikToTicker = cikToTicker
        self.isInstant = isInstant

    def __call__(self, pf: Path) -> pl.DataFrame | None:
        cik = pf.stem
        ticker = self.cikToTicker.get(cik)
        if ticker is None:
            raise EdgarScanMappingError(
                "file_loop_mapping",
                f"listed shard CIK has no ticker mapping: {cik}",
                source=str(pf),
            )

        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    (
                        (
                            (pl.col("namespace") == "us-gaap")
                            & pl.col("tag").str.to_lowercase().is_in(self.tagKeys.usGaap)
                        )
                        | (
                            (pl.col("namespace") == "ifrs-full")
                            & pl.col("tag").str.to_lowercase().is_in(self.tagKeys.ifrsFull)
                        )
                    )
                    & pl.col("unit").str.starts_with("USD")
                    & pl.col("fy").is_not_null()
                    & (pl.col("fy") >= 2000)
                    & (pl.col("fy") <= 2030)
                )
                .select(
                    [
                        "namespace",
                        "tag",
                        "val",
                        "fy",
                        "fp",
                        "start",
                        "end",
                        "filed",
                    ]
                )
                .collect(engine="streaming")
            )
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise EdgarScanStorageError(
                "file_loop_read",
                f"companyfacts shard read failed: {type(exc).__name__}: {exc}",
                source=str(pf),
            ) from exc

        if df.is_empty():
            return None
        namespaces = df["namespace"].unique().to_list() if "namespace" in df.columns else []
        if "us-gaap" in namespaces:
            df = df.filter(pl.col("namespace") == "us-gaap")
            priority = {tag: index for index, tag in enumerate(self.tagKeys.usGaap)}
            common = self.tagKeys.usGaapCommon
        elif "ifrs-full" in namespaces:
            df = df.filter(pl.col("namespace") == "ifrs-full")
            priority = {tag: index for index, tag in enumerate(self.tagKeys.ifrsFull)}
            common = self.tagKeys.ifrsFullCommon
        else:
            return None
        df = df.with_columns(
            pl.col("tag")
            .str.to_lowercase()
            .replace_strict(priority, default=len(priority), return_dtype=pl.Int32)
            .alias("_tagPriority"),
            pl.when(pl.col("tag").str.to_lowercase().is_in(common)).then(0).otherwise(1).alias("_fallbackRank"),
        )

        if self.freq == "Y":
            return self._parseAnnual(df, ticker)
        return self._parseQuarterly(df, ticker)

    def _parseAnnual(self, df: pl.DataFrame, ticker: str) -> pl.DataFrame | None:
        """연간: FY 값."""
        fy = df.filter(pl.col("fp") == "FY")
        if fy.is_empty():
            return None

        rows = []
        for year in fy["fy"].unique().sort().to_list():
            value = self._bestContextValue(
                fy.filter(pl.col("fy") == year),
                annual=True,
            )
            if value is not None:
                rows.append(
                    {
                        "stockCode": ticker,
                        "period": str(year),
                        "amount": value,
                    }
                )
        return pl.DataFrame(rows) if rows else None

    def _parseQuarterly(self, df: pl.DataFrame, ticker: str) -> pl.DataFrame | None:
        """분기: FY + frame 기반 standalone Q1-Q3에서 Q4를 역산한다."""
        rows: list[dict] = []

        for fy in df["fy"].unique().sort().to_list():
            yearDf = df.filter(pl.col("fy") == fy)

            # Q1-Q3: standalone = frame이 있는 행 (CYxxxxQn 형태)
            qVals: dict[str, float] = {}
            for fp in ["Q1", "Q2", "Q3"]:
                fpDf = yearDf.filter(pl.col("fp") == fp)
                if fpDf.is_empty():
                    continue
                standalone = self._bestContextValue(fpDf, annual=False)
                if standalone is not None:
                    qNum = fp[1]
                    qVals[f"Q{qNum}"] = standalone
                    rows.append(
                        {
                            "stockCode": ticker,
                            "period": f"{fy}Q{qNum}",
                            "amount": standalone,
                        }
                    )

            # Q4 = FY - Q1 - Q2 - Q3
            fyDf = yearDf.filter(pl.col("fp") == "FY")
            if not fyDf.is_empty():
                fyAmount = self._bestContextValue(fyDf, annual=True)
                if fyAmount is not None:
                    if self.isInstant:
                        rows.append({"stockCode": ticker, "period": f"{fy}Q4", "amount": fyAmount})
                    elif len(qVals) == 3:
                        q4 = fyAmount - sum(qVals.values())
                        rows.append({"stockCode": ticker, "period": f"{fy}Q4", "amount": q4})

        return pl.DataFrame(rows) if rows else None

    @staticmethod
    def _bestContextValue(df: pl.DataFrame, *, annual: bool) -> float | None:
        """정상 duration과 최신 종료일을 우선해 단일 fact 값을 고른다."""

        work = df.filter(pl.col("val").is_not_null())
        if work.is_empty():
            return None
        work = work.sort("filed", descending=True).unique(
            subset=["tag", "start", "end"],
            keep="first",
            maintain_order=True,
        )
        duration = (pl.col("end") - pl.col("start")).dt.total_days()
        lower, upper = (250, 450) if annual else (45, 140)
        work = work.with_columns(
            pl.when(pl.col("start").is_null() | duration.is_between(lower, upper))
            .then(0)
            .otherwise(1)
            .alias("_durationInvalid")
        )
        work = work.with_columns(pl.col("val").abs().alias("_absVal"))
        sortCols = [
            "_durationInvalid",
            "end",
            "_fallbackRank",
            "_absVal",
            "_tagPriority",
            "filed",
        ]
        descending = [False, True, False, True, False, True]
        selected = work.sort(sortCols, descending=descending)
        return float(selected["val"][0])


def _listedParquetFiles(edgarDir: Path, cikToTicker: dict[str, str]) -> list[Path]:
    """ticker map에 등재되고 실제 존재하는 filename CIK 파일만 반환한다."""
    return [path for cik in sorted(cikToTicker) if (path := edgarDir / f"{cik}.parquet").is_file()]


def _resultFromLong(
    longFrame: pl.DataFrame,
    cikToTicker: dict[str, str],
    tickerToTitle: dict[str, str],
) -> pl.DataFrame:
    """filename CIK long rows를 기존 wide 반환 계약으로 변환한다."""
    if longFrame.is_empty():
        return pl.DataFrame({"stockCode": []})

    tickerFrame = pl.DataFrame(
        {
            "fileCik": list(cikToTicker),
            "stockCode": list(cikToTicker.values()),
        }
    )
    values = (
        longFrame.join(tickerFrame, on="fileCik", how="inner")
        .sort(["fileCik", "period"])
        .group_by(["stockCode", "period"], maintain_order=True)
        .agg(pl.col("amount").first())
    )
    if values.is_empty():
        return pl.DataFrame({"stockCode": []})

    result = values.pivot(on="period", index="stockCode", values="amount")
    periodCols = sorted((name for name in result.columns if name != "stockCode"), reverse=True)
    return _joinCorpName(result.select(["stockCode", *periodCols]), tickerToTitle)


def _resultFromYearRows(
    yearRows: pl.DataFrame,
    cikToTicker: dict[str, str],
    tickerToTitle: dict[str, str],
    *,
    freq: str,
    isInstant: bool,
) -> pl.DataFrame:
    """DuckDB company-year rows에 기존 annual과 quarterly 규칙을 적용한다."""
    if yearRows.is_empty():
        return pl.DataFrame({"stockCode": []})

    if freq == "Y":
        longFrame = (
            yearRows.filter(pl.col("fyFirst").is_not_null() | pl.col("fyVal").is_not_null())
            .with_columns(
                pl.col("fy").cast(pl.Utf8).alias("period"),
                pl.coalesce("fyFirst", "fyVal").alias("amount"),
            )
            .select(["fileCik", "period", "amount"])
        )
        return _resultFromLong(longFrame, cikToTicker, tickerToTitle)

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
    if isInstant:
        fourth = yearRows.filter(pl.col("fyVal").is_not_null()).with_columns(pl.col("fyVal").alias("amount"))
    else:
        fourth = yearRows.filter(
            pl.col("fyVal").is_not_null()
            & pl.col("q1").is_not_null()
            & pl.col("q2").is_not_null()
            & pl.col("q3").is_not_null()
        ).with_columns((pl.col("fyVal") - (pl.col("q1") + pl.col("q2") + pl.col("q3"))).alias("amount"))
    fourth = fourth.with_columns((pl.col("fy").cast(pl.Utf8) + pl.lit("Q4")).alias("period")).select(
        ["fileCik", "period", "amount"]
    )
    return _resultFromLong(pl.concat([quarters, fourth]), cikToTicker, tickerToTitle)


def _scanAccountDuckDb(
    parquetFiles: list[Path],
    tagKeys: _TaxonomyTagKeys,
    tickerUniverse: _TickerUniverse,
    *,
    freq: str,
    isInstant: bool,
) -> pl.DataFrame:
    """listed EDGAR parquet를 bounded DuckDB source aggregation으로 조회한다."""
    try:
        import duckdb
    except ImportError as exc:
        raise EdgarScanExecutionError("duckdb_import", f"{type(exc).__name__}: {exc}") from exc

    if not parquetFiles:
        return pl.DataFrame({"stockCode": []})

    try:
        connection = duckdb.connect(":memory:")
        connection.execute(f"PRAGMA threads={_DUCKDB_THREADS}")
        connection.execute(f"PRAGMA memory_limit='{_DUCKDB_MEMORY_LIMIT_MB}MB'")
        yearRows = connection.execute(
            _DUCKDB_YEAR_SQL,
            [
                list(tagKeys.usGaap),
                list(tagKeys.ifrsFull),
                sorted(tagKeys.usGaapCommon),
                sorted(tagKeys.ifrsFullCommon),
                [str(path) for path in parquetFiles],
                list(tagKeys.usGaap),
                list(tagKeys.ifrsFull),
            ],
        ).pl()
    except duckdb.Error as exc:
        raise EdgarScanExecutionError("duckdb_query", f"{type(exc).__name__}: {exc}") from exc
    finally:
        if "connection" in locals():
            connection.close()

    try:
        return _resultFromYearRows(
            yearRows,
            tickerUniverse.cikToTicker,
            tickerUniverse.tickerToTitle,
            freq=freq,
            isInstant=isInstant,
        )
    except EdgarScanError:
        raise
    except (OSError, RuntimeError, pl.exceptions.PolarsError) as exc:
        raise EdgarScanExecutionError(
            "duckdb_transform",
            f"result transform failed: {type(exc).__name__}: {exc}",
        ) from exc


def _scanAccountsDuckDb(
    parquetFiles: list[Path],
    tagKeysBySnakeId: dict[str, _TaxonomyTagKeys],
    tickerUniverse: _TickerUniverse,
    *,
    freq: str,
    instantBySnakeId: dict[str, bool],
) -> dict[str, pl.DataFrame]:
    """여러 계정을 한 DuckDB source scan으로 조회한다."""

    try:
        import duckdb
    except ImportError as exc:
        raise EdgarScanExecutionError("duckdb_import", f"{type(exc).__name__}: {exc}") from exc

    empty = {snakeId: pl.DataFrame({"stockCode": []}) for snakeId in tagKeysBySnakeId}
    if not parquetFiles or not tagKeysBySnakeId:
        return empty

    tagRows: list[tuple[str, str, str, int, int]] = []
    for snakeId, tagKeys in tagKeysBySnakeId.items():
        tagRows.extend(
            (
                snakeId,
                "us-gaap",
                tag,
                priority,
                0 if tag in tagKeys.usGaapCommon else 1,
            )
            for priority, tag in enumerate(tagKeys.usGaap)
        )
        tagRows.extend(
            (
                snakeId,
                "ifrs-full",
                tag,
                priority,
                0 if tag in tagKeys.ifrsFullCommon else 1,
            )
            for priority, tag in enumerate(tagKeys.ifrsFull)
        )
    if not tagRows:
        return empty

    try:
        connection = duckdb.connect(":memory:")
        connection.execute(f"PRAGMA threads={_DUCKDB_BATCH_THREADS}")
        connection.execute(f"PRAGMA memory_limit='{_DUCKDB_BATCH_MEMORY_LIMIT_MB}MB'")
        connection.execute("PRAGMA preserve_insertion_order=false")
        connection.execute(
            "CREATE TEMP TABLE batchTags "
            "(snakeId VARCHAR, namespace VARCHAR, tag VARCHAR, priority INTEGER, "
            "fallbackRank INTEGER)"
        )
        connection.executemany("INSERT INTO batchTags VALUES (?, ?, ?, ?, ?)", tagRows)
        yearRows = connection.execute(
            _DUCKDB_BATCH_YEAR_SQL,
            [[str(path) for path in parquetFiles]],
        ).pl()
    except duckdb.Error as exc:
        raise EdgarScanExecutionError("duckdb_batch_query", f"{type(exc).__name__}: {exc}") from exc
    finally:
        if "connection" in locals():
            connection.close()

    try:
        results = dict(empty)
        for snakeId in tagKeysBySnakeId:
            accountRows = yearRows.filter(pl.col("snakeId") == snakeId).drop("snakeId")
            results[snakeId] = _resultFromYearRows(
                accountRows,
                tickerUniverse.cikToTicker,
                tickerUniverse.tickerToTitle,
                freq=freq,
                isInstant=instantBySnakeId[snakeId],
            )
        return results
    except EdgarScanError:
        raise
    except (OSError, RuntimeError, pl.exceptions.PolarsError) as exc:
        raise EdgarScanExecutionError(
            "duckdb_batch_transform",
            f"batch result transform failed: {type(exc).__name__}: {exc}",
        ) from exc


def _scanAccountFileLoop(
    parquetFiles: list[Path],
    tagKeys: _TaxonomyTagKeys,
    tickerUniverse: _TickerUniverse,
    *,
    freq: str,
    isInstant: bool,
) -> pl.DataFrame:
    """기존 파일별 ThreadPool 구현을 fallback으로 실행한다."""
    try:
        processor = _EdgarFileProcessor(
            tagKeys,
            freq=freq,
            cikToTicker=tickerUniverse.cikToTicker,
            isInstant=isInstant,
        )
        with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as pool:
            chunks = [result for result in pool.map(processor, parquetFiles) if result is not None]

        if not chunks:
            return pl.DataFrame({"stockCode": []})

        allDf = pl.concat(chunks).group_by(["stockCode", "period"]).agg(pl.col("amount").first())
        result = allDf.pivot(on="period", index="stockCode", values="amount")
        periodCols = sorted((name for name in result.columns if name != "stockCode"), reverse=True)
        return _joinCorpName(result.select(["stockCode", *periodCols]), tickerUniverse.tickerToTitle)
    except EdgarScanError:
        raise
    except (OSError, RuntimeError, pl.exceptions.PolarsError) as exc:
        raise EdgarScanExecutionError(
            "file_loop_transform",
            f"result transform failed: {type(exc).__name__}: {exc}",
        ) from exc
