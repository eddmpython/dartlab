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
from pathlib import Path

import polars as pl

from dartlab.providers.edgar.finance.mapper import EDGAR_TO_DART_ALIASES, EdgarMapper

_log = logging.getLogger(__name__)

_DUCKDB_THREADS = 4
_DUCKDB_MEMORY_LIMIT_MB = 64
_DUCKDB_YEAR_SQL = """
    SELECT
        regexp_extract(filename, '([0-9]{10})[.]parquet$', 1) AS fileCik,
        fy,
        first(val ORDER BY file_row_number)
            FILTER (WHERE fp = 'FY') AS fyFirst,
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


def _buildEdgarTagKeys(dartSnakeId: str) -> set[str]:
    """dartSnakeId에 매핑되는 모든 EDGAR XBRL tag를 수집."""
    tagMap = EdgarMapper.tagMap()

    # DART alias → EDGAR snakeId 역매핑
    edgarIds = {dartSnakeId}
    for edgarSid, dartSid in EDGAR_TO_DART_ALIASES.items():
        if dartSid == dartSnakeId:
            edgarIds.add(edgarSid)

    tags: set[str] = set()
    for tag, sid in tagMap.items():
        if sid in edgarIds:
            tags.add(tag)

    return tags


def _joinCorpName(df: pl.DataFrame) -> pl.DataFrame:
    """ticker에 회사명(corpName) 매핑."""
    try:
        from dartlab.core.edgarClient import loadTickers

        tickers = loadTickers().select(
            pl.col("ticker").alias("stockCode"),
            pl.col("title").alias("corpName"),
        )
        periodCols = [c for c in df.columns if c != "stockCode"]
        return df.join(tickers, on="stockCode", how="left").select(["stockCode", "corpName"] + periodCols)
    except (ImportError, OSError, pl.exceptions.PolarsError):
        return df


class _EdgarFileProcessor:
    """EDGAR parquet 파일별 처리."""

    __slots__ = ("tagKeys", "freq", "cikToTicker")

    def __init__(self, tagKeys: set[str], *, freq: str, cikToTicker: dict[str, str]):
        self.tagKeys = list(tagKeys)
        self.freq = freq
        self.cikToTicker = cikToTicker

    def __call__(self, pf: Path) -> pl.DataFrame | None:
        cik = pf.stem
        ticker = self.cikToTicker.get(cik)
        if ticker is None:
            return None

        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    (pl.col("namespace") == "us-gaap")
                    & pl.col("tag").str.to_lowercase().is_in(self.tagKeys)
                    & pl.col("unit").str.starts_with("USD")
                    & pl.col("fy").is_not_null()
                    & (pl.col("fy") >= 2000)
                    & (pl.col("fy") <= 2030)
                )
                .select(["tag", "val", "fy", "fp"])
                .collect(engine="streaming")
            )
        except (pl.exceptions.PolarsError, OSError):
            return None

        if df.is_empty():
            return None

        if self.freq == "Y":
            return self._parseAnnual(df, ticker)
        return self._parseQuarterly(df, ticker)

    def _parseAnnual(self, df: pl.DataFrame, ticker: str) -> pl.DataFrame | None:
        """연간: FY 값."""
        fy = df.filter(pl.col("fp") == "FY")
        if fy.is_empty():
            return None

        # 연도별 첫 값
        agg = fy.group_by("fy").agg(pl.col("val").first()).sort("fy")
        rows = []
        for row in agg.iter_rows(named=True):
            if row["val"] is not None:
                rows.append(
                    {
                        "stockCode": ticker,
                        "period": str(row["fy"]),
                        "amount": float(row["val"]),
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
                # standalone 선택: 기간이 짧은(~90일) 행 우선
                vals = fpDf["val"].drop_nulls().to_list()
                if vals:
                    # 가장 작은 양수값이 standalone일 가능성 높음 (YTD > standalone)
                    absVals = [(abs(v), v) for v in vals if v is not None]
                    if absVals:
                        standalone = min(absVals)[1]
                        qNum = fp[1]
                        qVals[f"Q{qNum}"] = standalone
                        rows.append({"stockCode": ticker, "period": f"{fy}Q{qNum}", "amount": standalone})

            # Q4 = FY - Q1 - Q2 - Q3
            fyDf = yearDf.filter(pl.col("fp") == "FY")
            if not fyDf.is_empty():
                fyVal = fyDf["val"].drop_nulls().to_list()
                if fyVal:
                    fyAmount = fyVal[0]
                    if len(qVals) == 3:
                        q4 = fyAmount - sum(qVals.values())
                        rows.append({"stockCode": ticker, "period": f"{fy}Q4", "amount": q4})
                    else:
                        rows.append({"stockCode": ticker, "period": f"{fy}Q4", "amount": fyAmount})

        return pl.DataFrame(rows) if rows else None


def _listedParquetFiles(edgarDir: Path, cikToTicker: dict[str, str]) -> list[Path]:
    """ticker map에 등재되고 실제 존재하는 filename CIK 파일만 반환한다."""
    return [path for cik in sorted(cikToTicker) if (path := edgarDir / f"{cik}.parquet").is_file()]


def _resultFromLong(longFrame: pl.DataFrame, cikToTicker: dict[str, str]) -> pl.DataFrame:
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
    return _joinCorpName(result.select(["stockCode", *periodCols]))


def _resultFromYearRows(
    yearRows: pl.DataFrame,
    cikToTicker: dict[str, str],
    *,
    freq: str,
) -> pl.DataFrame:
    """DuckDB company-year rows에 기존 annual과 quarterly 규칙을 적용한다."""
    if yearRows.is_empty():
        return pl.DataFrame({"stockCode": []})

    if freq == "Y":
        longFrame = (
            yearRows.filter(pl.col("fyFirst").is_not_null())
            .with_columns(
                pl.col("fy").cast(pl.Utf8).alias("period"),
                pl.col("fyFirst").alias("amount"),
            )
            .select(["fileCik", "period", "amount"])
        )
        return _resultFromLong(longFrame, cikToTicker)

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
    return _resultFromLong(pl.concat([quarters, fourth]), cikToTicker)


def _scanAccountDuckDb(
    parquetFiles: list[Path],
    tagKeys: set[str],
    cikToTicker: dict[str, str],
    *,
    freq: str,
) -> pl.DataFrame:
    """listed EDGAR parquet를 bounded DuckDB source aggregation으로 조회한다."""
    import duckdb

    if not parquetFiles:
        return pl.DataFrame({"stockCode": []})

    connection = duckdb.connect(":memory:")
    try:
        connection.execute(f"PRAGMA threads={_DUCKDB_THREADS}")
        connection.execute(f"PRAGMA memory_limit='{_DUCKDB_MEMORY_LIMIT_MB}MB'")
        yearRows = connection.execute(
            _DUCKDB_YEAR_SQL,
            [[str(path) for path in parquetFiles], sorted(tagKeys)],
        ).pl()
    finally:
        connection.close()

    return _resultFromYearRows(yearRows, cikToTicker, freq=freq)


def _scanAccountFileLoop(
    parquetFiles: list[Path],
    tagKeys: set[str],
    cikToTicker: dict[str, str],
    *,
    freq: str,
) -> pl.DataFrame:
    """기존 파일별 ThreadPool 구현을 fallback으로 실행한다."""
    processor = _EdgarFileProcessor(tagKeys, freq=freq, cikToTicker=cikToTicker)
    with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as pool:
        chunks = [result for result in pool.map(processor, parquetFiles) if result is not None]

    if not chunks:
        return pl.DataFrame({"stockCode": []})

    allDf = pl.concat(chunks).group_by(["stockCode", "period"]).agg(pl.col("amount").first())
    result = allDf.pivot(on="period", index="stockCode", values="amount")
    periodCols = sorted((name for name in result.columns if name != "stockCode"), reverse=True)
    return _joinCorpName(result.select(["stockCode", *periodCols]))


def scanAccount(
    dartSnakeId: str,
    *,
    freq: str = "Q",
) -> pl.DataFrame:
    """전종목 EDGAR 단일 계정 시계열. US 패리티 atomic primitive.

    DART ``scanAccount`` 와 동치다. 동일 snakeId 호출 시 동일 schema 의 wide DataFrame
    반환. 내부적으로 ``_buildEdgarTagKeys`` 가 DART snakeId → us-gaap concept set
    매핑 (``sales`` → ``{"Revenues", "RevenueFromContractWithCustomer*", "SalesRevenueNet"}`` 등).

    parquet source-native 처리:
      - ticker map에 존재하는 filename CIK 파일만 source manifest에 포함.
      - DuckDB 4 threads, 64 MiB limit로 filter와 company-year aggregation.
      - DuckDB 비가용 또는 실패 시 기존 ThreadPool file-loop로 안전하게 fallback.
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
        없음. parquet 부재 또는 tagKeys 매칭 0 시 빈 DataFrame.

    Example:
        >>> df = scanAccount("sales", freq="Y")
        >>> df.sort("2025", descending=True).head(10)
              / 가변 기간 컬럼 (float). freq="Q": ``"YYYYQn"`` / freq="Y": ``"YYYY"``.
            - row ≤ SEC 등록 ticker 수 (~10K).
            - 빈 DataFrame: parquet 부재 또는 tagKeys 매칭 0.
        Prerequisites:
            - ``edgar/*.parquet`` (companyfacts XBRL 정규화본).
            - ``_buildEdgarTagKeys`` 의 us-gaap concept 매핑 사전.
            - SEC tickers.parquet 또는 SEC API origin (CIK ↔ ticker).
        Freshness:
            - SEC EDGAR XBRL 분기 마감 후 ~45 일 (10-Q) / ~60 일 (10-K).
            - parquet 은 SEC ``data.sec.gov/api/xbrl/companyfacts`` nightly pull.
        Dataflow:
            - dartSnakeId → ``_buildEdgarTagKeys`` (us-gaap concept set)
            - → ticker map filename CIK pruning
            - → DuckDB source-native filter + company-year aggregation
            - → 실패 시 ``_EdgarFileProcessor`` ThreadPool fallback
            - → period pivot wide (latest 좌측) → ``_joinCorpName`` → pl.DataFrame.
        TargetMarkets:
            - US (SEC EDGAR). NYSE/NASDAQ/AMEX/OTC SEC 등록 + 10-K/10-Q 정기공시.
    """
    from dartlab.core.dataLoader import _dataDir

    edgarDir = Path(_dataDir("edgar"))
    parquetFiles = sorted(edgarDir.glob("*.parquet"))

    if not parquetFiles:
        _log.warning("EDGAR finance parquet 없음: %s", edgarDir)
        return pl.DataFrame({"stockCode": []})

    # CIK → ticker 매핑
    try:
        from dartlab.core.edgarClient import loadTickers

        tickerDf = loadTickers()
        cikToTicker = dict(
            zip(
                tickerDf["cik"].to_list(),
                tickerDf["ticker"].to_list(),
            )
        )
    except (ImportError, OSError):
        cikToTicker = {}

    tagKeys = _buildEdgarTagKeys(dartSnakeId)
    if not tagKeys:
        _log.warning("EDGAR에서 '%s'에 매핑되는 tag 없음", dartSnakeId)
        return pl.DataFrame({"stockCode": []})

    listedFiles = _listedParquetFiles(edgarDir, cikToTicker)
    _log.info(
        "scanAccount(edgar, '%s', freq=%s): listed %d/%d 파일 source-native scan",
        dartSnakeId,
        freq,
        len(listedFiles),
        len(parquetFiles),
    )

    try:
        result = _scanAccountDuckDb(listedFiles, tagKeys, cikToTicker, freq=freq)
    except Exception as exc:
        _log.warning("scanAccount(edgar) DuckDB 실패, file-loop fallback: %s", exc)
        result = _scanAccountFileLoop(parquetFiles, tagKeys, cikToTicker, freq=freq)

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
    numer = scanAccount(defn["numer"], freq=freq)
    denom = scanAccount(defn["denom"], freq=freq)

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
