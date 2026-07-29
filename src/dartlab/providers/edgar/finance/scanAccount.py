"""전종목 EDGAR 단일 계정/비율 시계열 배치 추출.

EDGAR finance parquet({cik}.parquet)를 병렬 스캔하여
특정 snakeId 하나의 전종목 × 기간 시계열 DataFrame을 반환한다.

연간: FY 직접값 (IS/CF=연간합계, BS=시점잔액)
분기: FY + Q1-Q3 standalone (기존 pivot 로직 재활용)
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from dartlab.core.accounts.aliases import SNAKEID_ALIASES
from dartlab.core.accounts.data import loadAccounts
from dartlab.providers.edgar.finance.mapper import EDGAR_TO_DART_ALIASES, EdgarMapper

_log = logging.getLogger(__name__)

_DUCKDB_THREADS = 4
_DUCKDB_MEMORY_LIMIT_MB = 192
_DUCKDB_BATCH_THREADS = 2
_DUCKDB_BATCH_MEMORY_LIMIT_MB = 256
_DUCKDB_BATCH_ACCOUNT_LIMIT = 3
_DUCKDB_YEAR_SQL = """
    WITH matched AS (
        SELECT
            regexp_extract(filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
            namespace,
            lower(tag) AS tag,
            val,
            fy,
            fp,
            start,
            "end",
            filed,
            file_row_number,
            CASE namespace
                WHEN 'us-gaap' THEN list_position(?, lower(tag))
                ELSE list_position(?, lower(tag))
            END AS tagPriority,
            CASE namespace
                WHEN 'us-gaap' THEN
                    CASE WHEN lower(tag) IN (SELECT unnest(?)) THEN 0 ELSE 1 END
                ELSE
                    CASE WHEN lower(tag) IN (SELECT unnest(?)) THEN 0 ELSE 1 END
            END AS fallbackRank,
            min(CASE namespace WHEN 'us-gaap' THEN 0 ELSE 1 END)
                OVER (PARTITION BY filename) AS selectedNamespace
        FROM read_parquet(?, filename = true, file_row_number = true)
        WHERE (
                (namespace = 'us-gaap' AND lower(tag) IN (SELECT unnest(?)))
                OR
                (namespace = 'ifrs-full' AND lower(tag) IN (SELECT unnest(?)))
              )
          AND starts_with(unit, 'USD')
          AND fy BETWEEN 2000 AND 2030
          AND fp IN ('FY', 'Q1', 'Q2', 'Q3')
    ),
    deduped AS (
        SELECT *
        FROM matched
        QUALIFY row_number() OVER (
            PARTITION BY fileCik, fy, fp, namespace, tag, start, "end"
            ORDER BY (val IS NULL), filed DESC, file_row_number
        ) = 1
    )
    SELECT
        fileCik,
        fy,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'FY') AS fyFirst,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        )
            FILTER (WHERE fp = 'FY') AS fyVal,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q1') AS q1,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q2') AS q2,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q3') AS q3
    FROM deduped
    WHERE (namespace = 'us-gaap' AND selectedNamespace = 0)
       OR (namespace = 'ifrs-full' AND selectedNamespace = 1)
    GROUP BY fileCik, fy
"""
_DUCKDB_BATCH_YEAR_SQL = """
    WITH matched AS (
        SELECT
            batchTags.snakeId,
            regexp_extract(facts.filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
            facts.namespace,
            lower(facts.tag) AS tag,
            facts.val,
            facts.fy,
            facts.fp,
            facts.start,
            facts."end",
            facts.filed,
            facts.file_row_number,
            batchTags.priority AS tagPriority,
            batchTags.fallbackRank AS fallbackRank,
            min(CASE facts.namespace WHEN 'us-gaap' THEN 0 ELSE 1 END)
                OVER (PARTITION BY facts.filename, batchTags.snakeId) AS selectedNamespace
        FROM read_parquet(?, filename = true, file_row_number = true) AS facts
        INNER JOIN batchTags
            ON facts.namespace = batchTags.namespace
           AND lower(facts.tag) = batchTags.tag
        WHERE starts_with(facts.unit, 'USD')
          AND facts.fy BETWEEN 2000 AND 2030
          AND facts.fp IN ('FY', 'Q1', 'Q2', 'Q3')
    ),
    deduped AS (
        SELECT *
        FROM matched
        QUALIFY row_number() OVER (
            PARTITION BY snakeId, fileCik, fy, fp, namespace, tag, start, "end"
            ORDER BY (val IS NULL), filed DESC, file_row_number
        ) = 1
    )
    SELECT
        snakeId,
        fileCik,
        fy,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'FY') AS fyFirst,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 250 AND 450 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        )
            FILTER (WHERE fp = 'FY') AS fyVal,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q1') AS q1,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q2') AS q2,
        arg_min(
            val,
            struct_pack(
                durationInvalid := CASE
                    WHEN start IS NULL THEN 0
                    WHEN date_diff('day', start, "end") BETWEEN 45 AND 140 THEN 0
                    ELSE 1
                END,
                endRank := -epoch(coalesce("end", DATE '1900-01-01')),
                fallbackRank := fallbackRank,
                absRank := -abs(val),
                tagPriority := tagPriority,
                tieVal := val,
                filedRank := -epoch(coalesce(filed, DATE '1900-01-01')),
                rowNum := file_row_number
            )
        ) FILTER (WHERE fp = 'Q3') AS q3
    FROM deduped
    WHERE (namespace = 'us-gaap' AND selectedNamespace = 0)
       OR (namespace = 'ifrs-full' AND selectedNamespace = 1)
    GROUP BY snakeId, fileCik, fy
"""


class EdgarScanError(RuntimeError):
    """EDGAR bulk finance scan의 원천 또는 실행 실패."""

    def __init__(self, stage: str, message: str, *, source: str | None = None) -> None:
        self.stage = stage
        self.source = source
        sourceLabel = f", source={source}" if source else ""
        super().__init__(f"EDGAR scan failed: stage={stage}{sourceLabel}: {message}")


class EdgarScanMappingError(EdgarScanError):
    """CIK, ticker, company title universe 계약 실패."""


class EdgarScanStorageError(EdgarScanError):
    """listed companyfacts shard 읽기 또는 schema 실패."""


class EdgarScanExecutionError(EdgarScanError):
    """DuckDB와 검증 fallback 실행 실패."""

    def __init__(
        self,
        stage: str,
        message: str,
        *,
        source: str | None = None,
        primaryError: BaseException | None = None,
    ) -> None:
        self.primaryError = primaryError
        super().__init__(stage, message, source=source)


@dataclass(frozen=True)
class _TaxonomyTagKeys:
    usGaap: tuple[str, ...]
    ifrsFull: tuple[str, ...]
    usGaapCommon: frozenset[str] = frozenset()
    ifrsFullCommon: frozenset[str] = frozenset()

    @property
    def empty(self) -> bool:
        """두 taxonomy 모두 concept가 없는지 반환.

        Args:
            없음.

        Returns:
            US GAAP과 IFRS concept set이 모두 비었으면 True.

        Raises:
            없음.

        Example:
            >>> _TaxonomyTagKeys((), ()).empty
            True
        """
        return not self.usGaap and not self.ifrsFull


@dataclass(frozen=True)
class _TickerUniverse:
    cikToTicker: dict[str, str]
    tickerToTitle: dict[str, str]


def _canonicalSnakeId(snakeId: str) -> str:
    seen: set[str] = set()
    current = snakeId
    while current not in seen and current in SNAKEID_ALIASES:
        seen.add(current)
        current = SNAKEID_ALIASES[current]
    return current


def _buildEdgarTagKeys(dartSnakeId: str) -> _TaxonomyTagKeys:
    """snakeId에 대응하는 US GAAP과 IFRS concept key를 SSOT에서 파생."""
    try:
        tagMap = EdgarMapper.tagMap()
        mappings = loadAccounts().get("mappings", {})
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise EdgarScanMappingError(
            "account_mapping",
            f"account SSOT load failed: {type(exc).__name__}: {exc}",
        ) from exc
    target = _canonicalSnakeId(dartSnakeId)

    edgarIds = {dartSnakeId, target}
    for edgarSid, dartSid in EDGAR_TO_DART_ALIASES.items():
        if _canonicalSnakeId(dartSid) == target:
            edgarIds.add(edgarSid)

    usGaap: set[str] = set()
    for tag, sid in tagMap.items():
        if sid in edgarIds or _canonicalSnakeId(sid) == target:
            usGaap.add(tag.lower())

    ifrsFull: set[str] = set()
    for concept, sid in mappings.items():
        if (
            concept
            and concept[0].isupper()
            and concept.isascii()
            and concept.isalnum()
            and _canonicalSnakeId(str(sid)) == target
        ):
            ifrsFull.add(concept.lower())

    preferred: list[str] = []
    for account in loadAccounts().get("edgar", {}).get("accounts", []):
        if _canonicalSnakeId(str(account.get("snakeId", ""))) != target:
            continue
        for tag in account.get("commonTags", []):
            tagLower = str(tag).lower()
            if tagLower not in preferred:
                preferred.append(tagLower)
    usGaap.update(preferred)
    ifrsFull.update(preferred)

    def prioritized(tags: set[str]) -> tuple[str, ...]:
        """common tag를 먼저 두고 learned tag를 결정적으로 뒤에 둔다."""

        primary = [tag for tag in preferred if tag in tags]
        return tuple([*primary, *sorted(tags - set(primary))])

    common = frozenset(preferred)
    return _TaxonomyTagKeys(
        prioritized(usGaap),
        prioritized(ifrsFull),
        common,
        common,
    )


def _loadTickerUniverse() -> _TickerUniverse:
    """SEC ticker universe를 검증하고 CIK 기준 대표 ticker로 정규화."""
    try:
        from dartlab.core.edgarClient import loadTickers

        tickerFrame = loadTickers()
    except (ImportError, OSError, RuntimeError, pl.exceptions.PolarsError) as exc:
        raise EdgarScanMappingError(
            "ticker_universe",
            f"ticker universe load failed: {type(exc).__name__}: {exc}",
        ) from exc

    if not isinstance(tickerFrame, pl.DataFrame):
        raise EdgarScanMappingError(
            "ticker_universe",
            f"ticker universe must be DataFrame, got {type(tickerFrame).__name__}",
        )
    required = {"ticker", "cik", "title"}
    missing = sorted(required - set(tickerFrame.columns))
    if missing:
        raise EdgarScanMappingError("ticker_universe", f"missing columns: {missing}")
    if tickerFrame.is_empty():
        raise EdgarScanMappingError("ticker_universe", "ticker universe is empty")

    cikToTicker: dict[str, str] = {}
    tickerToTitle: dict[str, str] = {}
    for rowIndex, row in enumerate(tickerFrame.select("ticker", "cik", "title").iter_rows(named=True)):
        ticker = str(row["ticker"] or "").strip().upper()
        cikRaw = str(row["cik"] or "").strip()
        if not ticker or not cikRaw.isdigit() or len(cikRaw) > 10:
            raise EdgarScanMappingError(
                "ticker_universe",
                f"invalid row={rowIndex}, ticker={ticker!r}, cik={cikRaw!r}",
            )
        cik = cikRaw.zfill(10)
        title = str(row["title"] or ticker).strip() or ticker
        cikToTicker.setdefault(cik, ticker)
        tickerToTitle.setdefault(ticker, title)

    return _TickerUniverse(cikToTicker, tickerToTitle)


def _joinCorpName(
    df: pl.DataFrame,
    tickerToTitle: dict[str, str] | None = None,
) -> pl.DataFrame:
    """검증된 ticker universe로 corpName을 추가."""
    if df.is_empty():
        return df
    if "stockCode" not in df.columns:
        raise EdgarScanMappingError("corp_name_join", "result has no stockCode column")
    if tickerToTitle is None:
        tickerToTitle = _loadTickerUniverse().tickerToTitle

    missing = sorted(set(df["stockCode"].drop_nulls().to_list()) - set(tickerToTitle))
    if missing:
        raise EdgarScanMappingError(
            "corp_name_join",
            f"result tickers are absent from ticker universe: {missing[:10]}",
        )
    titles = pl.DataFrame(
        {
            "stockCode": list(tickerToTitle),
            "corpName": list(tickerToTitle.values()),
        }
    )
    periodCols = [column for column in df.columns if column != "stockCode"]
    return df.join(titles, on="stockCode", how="left").select(["stockCode", "corpName", *periodCols])


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


def scanAccounts(
    dartSnakeIds: list[str],
    *,
    freq: str = "Q",
) -> dict[str, pl.DataFrame]:
    """전종목 EDGAR 여러 계정을 bounded source batch로 반환한다.

    Args:
        dartSnakeIds: 서로 함께 비교할 DART canonical snakeId 목록.
        freq: ``"Q"`` 분기 또는 ``"Y"`` 연간.

    Returns:
        입력 snakeId를 key로 하고 각 계정 wide DataFrame을 값으로 갖는 dict.
        메모리 피크를 제한하기 위해 최대 3계정씩 같은 source scan을 공유한다.

    Raises:
        ValueError: 계정 목록이나 freq가 잘못된 경우.
        EdgarScanError: ticker, parquet 또는 batch 실행 실패.

    Example:
        >>> frames = scanAccounts(["sales", "operating_profit"], freq="Y")
        >>> sorted(frames)
        ['operating_profit', 'sales']
    """

    if not isinstance(dartSnakeIds, list) or not dartSnakeIds:
        raise ValueError("dartSnakeIds는 비어 있지 않은 문자열 list여야 합니다")
    if any(not isinstance(snakeId, str) or not snakeId.strip() for snakeId in dartSnakeIds):
        raise ValueError("dartSnakeIds는 비어 있지 않은 문자열만 포함해야 합니다")
    snakeIds = list(dict.fromkeys(snakeId.strip() for snakeId in dartSnakeIds))
    freq = str(freq).upper()
    if freq not in {"Q", "Y"}:
        raise ValueError(f"freq는 'Q' 또는 'Y'여야 합니다: {freq!r}")

    from dartlab.core.dataLoader import _dataDir

    edgarDir = Path(_dataDir("edgar"))
    parquetFiles = sorted(edgarDir.glob("*.parquet"))
    empty = {snakeId: pl.DataFrame({"stockCode": []}) for snakeId in snakeIds}
    if not parquetFiles:
        _log.warning("EDGAR finance parquet 없음: %s", edgarDir)
        return empty

    tagKeysBySnakeId: dict[str, _TaxonomyTagKeys] = {}
    for snakeId in snakeIds:
        tagKeys = _buildEdgarTagKeys(snakeId)
        if tagKeys.empty:
            _log.warning("EDGAR에서 '%s'에 매핑되는 tag 없음", snakeId)
            continue
        tagKeysBySnakeId[snakeId] = tagKeys
    if not tagKeysBySnakeId:
        return empty

    tickerUniverse = _loadTickerUniverse()
    listedFiles = _listedParquetFiles(edgarDir, tickerUniverse.cikToTicker)
    if not listedFiles:
        raise EdgarScanMappingError(
            "listed_shard_join",
            f"local parquet {len(parquetFiles)}개 중 ticker universe와 연결된 shard가 없습니다",
            source=str(edgarDir),
        )
    instantBySnakeId = {snakeId: EdgarMapper.getAccountStmt(snakeId) == "BS" for snakeId in tagKeysBySnakeId}

    batch: dict[str, pl.DataFrame] = {}
    tagItems = list(tagKeysBySnakeId.items())
    for offset in range(0, len(tagItems), _DUCKDB_BATCH_ACCOUNT_LIMIT):
        chunk = dict(tagItems[offset : offset + _DUCKDB_BATCH_ACCOUNT_LIMIT])
        try:
            batch.update(
                _scanAccountsDuckDb(
                    listedFiles,
                    chunk,
                    tickerUniverse,
                    freq=freq,
                    instantBySnakeId=instantBySnakeId,
                )
            )
        except EdgarScanExecutionError as batchError:
            _log.warning(
                "scanAccounts(edgar) %d계정 batch 실패, 단일 계정 fallback: %s",
                len(chunk),
                batchError,
            )
            try:
                for snakeId in chunk:
                    batch[snakeId] = scanAccount(snakeId, freq=freq)
            except (EdgarScanError, OSError, RuntimeError, pl.exceptions.PolarsError) as fallbackError:
                raise EdgarScanExecutionError(
                    "batch_fallback",
                    f"single-account fallback failed: {type(fallbackError).__name__}: {fallbackError}",
                    source=str(edgarDir),
                    primaryError=batchError,
                ) from fallbackError

    return {snakeId: batch.get(snakeId, empty[snakeId]) for snakeId in snakeIds}


def scanAccount(
    dartSnakeId: str,
    *,
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 EDGAR 단일 계정 시계열. US 패리티 atomic primitive.

    DART ``scanAccount`` 와 동치다. 동일 snakeId 호출 시 동일 schema 의 wide DataFrame
    반환. 내부적으로 ``_buildEdgarTagKeys`` 가 DART snakeId를 US GAAP과 IFRS concept set으로
    분리 매핑한다.

    parquet source-native 처리:
      - ticker map에 존재하는 filename CIK 파일만 source manifest에 포함.
      - DuckDB threads와 memory limit를 명시해 filter와 company-year aggregation.
      - DuckDB 비가용 또는 실패 시 검증된 ThreadPool file-loop로 fallback.
      - fallback도 실패하면 DuckDB 원인과 shard 원인을 ``EdgarScanExecutionError``에 보존.
      - period pivot wide → ``stockCode + 기간 컬럼들`` (최신 period 좌측).
      - ``_joinCorpName`` 으로 corpName 추가.

    Args:
        dartSnakeId: DART canonical snakeId (예: ``"sales"`` / ``"operating_profit"`` /
            ``"total_assets"``). DART scanAccount 와 호환되는 키 사용. provider 간 동일
            호출 가능. 미매핑 snakeId 호출 시 빈 DataFrame + warning.
        freq: ``"Q"`` 분기 wide (default) / ``"Y"`` 연간 wide. Company 엔진 freq 와 일치.

    Returns:
        pl.DataFrame. ``stockCode`` (=ticker) / ``corpName`` (str) + 기간 컬럼들
        (``"2025Q4"`` / ... / ``"2019Q1"``, 최신 좌측). row ~10K (SEC 등록 ticker 전체).

    Raises:
        ValueError: freq 또는 snakeId 입력이 잘못된 경우.
        EdgarScanMappingError: ticker universe schema 또는 CIK 연결 실패.
        EdgarScanStorageError: listed companyfacts shard 손상.
        EdgarScanExecutionError: DuckDB와 file-loop fallback이 모두 실패.

    Example:
        >>> df = scanAccount("sales", freq="Y")
        >>> df.sort("2025", descending=True).head(10)
              / 가변 기간 컬럼 (float). freq="Q": ``"YYYYQn"`` / freq="Y": ``"YYYY"``.
            - row ≤ SEC 등록 ticker 수 (~10K).
            - 빈 DataFrame: parquet 부재 또는 tagKeys 매칭 0.
        Prerequisites:
            - ``edgar/*.parquet`` (companyfacts XBRL 정규화본).
            - ``_buildEdgarTagKeys`` 의 US GAAP 및 IFRS concept 매핑 사전.
            - SEC tickers.parquet 또는 SEC API origin (CIK ↔ ticker).
        Freshness:
            - SEC EDGAR XBRL 분기 마감 후 ~45 일 (10-Q) / ~60 일 (10-K).
            - parquet 은 SEC ``data.sec.gov/api/xbrl/companyfacts`` nightly pull.
        Dataflow:
            - dartSnakeId → ``_buildEdgarTagKeys`` (US GAAP 및 IFRS concept set)
            - → ticker map filename CIK pruning
            - → DuckDB source-native filter + company-year aggregation
            - → 실패 시 ``_EdgarFileProcessor`` ThreadPool fallback
            - → period pivot wide (latest 좌측) → ``_joinCorpName`` → pl.DataFrame.
        TargetMarkets:
            - US (SEC EDGAR). NYSE/NASDAQ/AMEX/OTC SEC 등록 + 10-K/10-Q 정기공시.
    """
    from dartlab.core.dataLoader import _dataDir

    if not isinstance(dartSnakeId, str) or not dartSnakeId.strip():
        raise ValueError("dartSnakeId는 비어 있지 않은 문자열이어야 합니다")
    freq = str(freq).upper()
    if freq not in {"Q", "Y"}:
        raise ValueError(f"freq는 'Q' 또는 'Y'여야 합니다: {freq!r}")

    edgarDir = Path(_dataDir("edgar"))
    parquetFiles = sorted(edgarDir.glob("*.parquet"))

    if not parquetFiles:
        _log.warning("EDGAR finance parquet 없음: %s", edgarDir)
        return pl.DataFrame({"stockCode": []})

    tagKeys = _buildEdgarTagKeys(dartSnakeId)
    if tagKeys.empty:
        _log.warning("EDGAR에서 '%s'에 매핑되는 tag 없음", dartSnakeId)
        return pl.DataFrame({"stockCode": []})

    tickerUniverse = _loadTickerUniverse()
    listedFiles = _listedParquetFiles(edgarDir, tickerUniverse.cikToTicker)
    if not listedFiles:
        raise EdgarScanMappingError(
            "listed_shard_join",
            f"local parquet {len(parquetFiles)}개 중 ticker universe와 연결된 shard가 없습니다",
            source=str(edgarDir),
        )
    stmt = EdgarMapper.getAccountStmt(dartSnakeId)
    isInstant = stmt == "BS"
    _log.info(
        "scanAccount(edgar, '%s', freq=%s, stmt=%s): listed %d/%d 파일 source-native scan",
        dartSnakeId,
        freq,
        stmt or "unknown",
        len(listedFiles),
        len(parquetFiles),
    )

    try:
        result = _scanAccountDuckDb(
            listedFiles,
            tagKeys,
            tickerUniverse,
            freq=freq,
            isInstant=isInstant,
        )
    except EdgarScanExecutionError as duckError:
        _log.warning(
            "scanAccount(edgar) DuckDB 실패, file-loop fallback: %s: %s",
            type(duckError.__cause__).__name__ if duckError.__cause__ else type(duckError).__name__,
            duckError,
        )
        try:
            result = _scanAccountFileLoop(
                listedFiles,
                tagKeys,
                tickerUniverse,
                freq=freq,
                isInstant=isInstant,
            )
        except (EdgarScanError, OSError, RuntimeError, pl.exceptions.PolarsError) as fallbackError:
            raise EdgarScanExecutionError(
                "fallback",
                f"file-loop failed after DuckDB failure: {type(fallbackError).__name__}: {fallbackError}",
                source=str(edgarDir),
                primaryError=duckError,
            ) from fallbackError

    periodCount = len([name for name in result.columns if name not in ("stockCode", "corpName")])
    _log.info("scanAccount(edgar): %d종목 × %d기간", result.height, periodCount)
    return result


# ── scanRatio (EDGAR) ─────────────────────────────────────────

# DART 비율 정의 재활용
from dartlab.providers.dart.finance.scanAccount import _RATIO_DEFS


def scanRatio(
    ratioName: str,
    *,
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 EDGAR 재무비율 시계열.

    Args:
        ratioName: 비율 식별자. scanRatioList() 참조.
        freq: "Q" 분기 (기본) · "Y" 연간. Company 엔진과 일치.

    Returns:
        stockCode | corpName | 기간컬럼들... DataFrame.

    Raises:
        ValueError: 지원하지 않는 ratioName.
        EdgarScanError: 구성 계정의 ticker universe, 저장소 또는 scan 실행 실패.

    Example:
        >>> scanRatio("debt_ratio", freq="Y")
    """
    if ratioName not in _RATIO_DEFS:
        available = ", ".join(sorted(_RATIO_DEFS))
        msg = f"지원하지 않는 비율: '{ratioName}'. 사용 가능: {available}"
        raise ValueError(msg)

    defn = _RATIO_DEFS[ratioName]

    if defn.get("yoy"):
        return _calcYoyRatio(defn, freq=freq)
    return _calcSimpleRatio(defn, freq=freq)


def _calcSimpleRatio(defn: dict, *, freq: str = "Q") -> pl.DataFrame:
    """분자/분모 비율 계산."""
    accountFrames = scanAccounts([defn["numer"], defn["denom"]], freq=freq)
    numer = accountFrames[defn["numer"]]
    denom = accountFrames[defn["denom"]]

    numerCols = [c for c in numer.columns if c not in ("stockCode", "corpName")]
    denomCols = [c for c in denom.columns if c not in ("stockCode", "corpName")]
    commonCols = sorted(set(numerCols) & set(denomCols), reverse=True)

    if not commonCols:
        return pl.DataFrame({"stockCode": []})

    joined = numer.select(["stockCode"] + commonCols).join(
        denom.select(["stockCode"] + commonCols),
        on="stockCode",
        suffix="_d",
    )

    isPct = defn.get("pct", False)
    multiplier = 100.0 if isPct else 1.0

    resultExprs = [pl.col("stockCode")]
    for y in commonCols:
        expr = (
            pl.when((pl.col(f"{y}_d") != 0) & pl.col(f"{y}_d").is_not_null() & pl.col(y).is_not_null())
            .then((pl.col(y) / pl.col(f"{y}_d") * multiplier).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(y)
        )
        resultExprs.append(expr)

    result = joined.select(resultExprs)
    return _joinCorpName(result)


def _calcYoyRatio(defn: dict, *, freq: str = "Q") -> pl.DataFrame:
    """YoY 성장률 계산."""
    base = scanAccount(defn["base"], freq=freq)
    periodCols = sorted(c for c in base.columns if c not in ("stockCode", "corpName"))

    if len(periodCols) < 2:
        return pl.DataFrame({"stockCode": []})

    resultExprs = [pl.col("stockCode")]
    for i in range(1, len(periodCols)):
        cur = periodCols[i]
        prev = periodCols[i - 1]
        expr = (
            pl.when((pl.col(prev) != 0) & pl.col(prev).is_not_null() & pl.col(cur).is_not_null())
            .then(((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(cur)
        )
        resultExprs.append(expr)

    yoyCols = [periodCols[i] for i in range(1, len(periodCols))]
    result = base.select(resultExprs).select(["stockCode"] + list(reversed(yoyCols)))
    return _joinCorpName(result)
