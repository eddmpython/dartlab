"""Report parquet에서 apiType별 DataFrame 추출 + 정제."""

from __future__ import annotations

import polars as pl

from dartlab.engines.dart.report.types import (
    API_TYPE_LABELS,
    KEEP_META_COLS,
    META_DROP_COLS,
    PREFERRED_QUARTER,
    QUARTER_MAP,
    STR_OVERRIDE_COLS,
    ReportResult,
)


def extractRaw(
    stockCode: str,
    apiType: str,
) -> pl.DataFrame | None:
    """report parquet에서 apiType으로 필터 → null 컬럼 제거 → 정렬.

    Args:
        stockCode: 종목코드 (예: "005930")
        apiType: API 타입 (예: "dividend", "employee")

    Returns:
        정제된 DataFrame 또는 None (데이터 없음).
    """
    from dartlab.core.dataLoader import loadData

    df = loadData(stockCode, category="report")
    if df is None or df.is_empty():
        return None

    sub = df.filter(pl.col("apiType") == apiType)
    if sub.is_empty():
        return None

    dropCols = []
    for c in sub.columns:
        if c in META_DROP_COLS:
            dropCols.append(c)
            continue
        if c in KEEP_META_COLS:
            continue
        if sub[c].null_count() == sub.height:
            dropCols.append(c)

    sub = sub.drop(dropCols)

    sub = sub.with_columns(pl.col("year").cast(pl.Int32))
    sub = sub.with_columns(
        pl.col("quarter").replace(QUARTER_MAP).cast(pl.Int32).alias("quarterNum")
    )

    sub = sub.filter(pl.col("stlm_dt").is_not_null())
    sub = sub.sort(["year", "quarterNum"])

    return sub


def extractClean(
    stockCode: str,
    apiType: str,
) -> pl.DataFrame | None:
    """extractRaw + 숫자 변환 적용."""
    df = extractRaw(stockCode, apiType)
    if df is None:
        return None

    overrides = STR_OVERRIDE_COLS.get(apiType, set())
    return _castNumeric(df, overrides)


def extractAnnual(
    stockCode: str,
    apiType: str,
    quarterNum: int | None = None,
) -> pl.DataFrame | None:
    """연도별 데이터 추출 (특정 분기 기준).

    Args:
        stockCode: 종목코드
        apiType: API 타입
        quarterNum: 기준 분기 (None이면 PREFERRED_QUARTER에서 자동 결정)

    Returns:
        연간 DataFrame 또는 None.
    """
    df = extractClean(stockCode, apiType)
    if df is None:
        return None

    if quarterNum is None:
        quarterNum = PREFERRED_QUARTER.get(apiType, 2)

    annual = df.filter(pl.col("quarterNum") == quarterNum)

    if annual.is_empty() and quarterNum == 2:
        annual = df.filter(pl.col("quarterNum") == 4)
    elif annual.is_empty() and quarterNum == 4:
        annual = df.filter(pl.col("quarterNum") == 2)

    if annual.is_empty():
        return None

    return annual


def extractResult(
    stockCode: str,
    apiType: str,
    quarterNum: int | None = None,
) -> ReportResult | None:
    """apiType별 ReportResult 반환."""
    df = extractAnnual(stockCode, apiType, quarterNum)
    if df is None:
        return None

    years = sorted(df["year"].unique().to_list())

    return ReportResult(
        apiType=apiType,
        label=API_TYPE_LABELS.get(apiType, apiType),
        df=df,
        years=years,
        nYears=len(years),
    )


def _castNumeric(
    df: pl.DataFrame,
    strOverrides: set[str] | None = None,
) -> pl.DataFrame:
    """문자열 컬럼 중 숫자 변환 가능한 것을 Float64로 변환."""
    if strOverrides is None:
        strOverrides = set()

    skip = KEEP_META_COLS | {"quarterNum"} | strOverrides

    for c in df.columns:
        if c in skip:
            continue
        if df[c].dtype != pl.Utf8:
            continue

        stripped = df[c].str.strip_chars().str.replace_all(",", "")
        cleanedSeries = stripped.to_frame("_v").select(
            pl.when((pl.col("_v") == "-") | (pl.col("_v") == ""))
            .then(pl.lit(None))
            .otherwise(pl.col("_v"))
            .alias("_v")
        ).to_series()

        numSeries = cleanedSeries.cast(pl.Float64, strict=False)
        nonNullOriginal = cleanedSeries.drop_nulls().len()
        nonNullConverted = numSeries.drop_nulls().len()

        if nonNullOriginal > 0 and nonNullConverted / nonNullOriginal >= 0.7:
            df = df.with_columns(numSeries.alias(c))

    return df
