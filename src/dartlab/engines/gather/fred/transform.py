"""FRED 시계열 변환 — YoY, MoM, diff, MA, normalize, correlation, lead-lag.

모든 함수는 Polars DataFrame을 받아 Polars DataFrame을 반환.
입력 형식:
- 단일: (date, value)
- 복수: (date, col1, col2, ...)
"""

from __future__ import annotations

import polars as pl


def yoy(df: pl.DataFrame, col: str = "value") -> pl.DataFrame:
    """전년 동기 대비 변화율 (%).

    12개월 전 값 대비 퍼센트 변화. 월별 데이터 기준.
    분기별 데이터는 4행 전, 연간은 1행 전.
    """
    period = _infer_period(df)
    return df.with_columns(
        ((pl.col(col) / pl.col(col).shift(period) - 1) * 100)
        .alias(f"{col}_yoy")
    )


def mom(df: pl.DataFrame, col: str = "value") -> pl.DataFrame:
    """전월 대비 변화율 (%). 일별 데이터는 전일 대비."""
    return df.with_columns(
        ((pl.col(col) / pl.col(col).shift(1) - 1) * 100)
        .alias(f"{col}_mom")
    )


def diff(df: pl.DataFrame, col: str = "value", periods: int = 1) -> pl.DataFrame:
    """차분 (현재 값 - N기간 전 값)."""
    return df.with_columns(
        (pl.col(col) - pl.col(col).shift(periods))
        .alias(f"{col}_diff{periods}")
    )


def moving_average(df: pl.DataFrame, col: str = "value", window: int = 12) -> pl.DataFrame:
    """이동평균."""
    return df.with_columns(
        pl.col(col).rolling_mean(window_size=window)
        .alias(f"{col}_ma{window}")
    )


def normalize(df: pl.DataFrame, col: str = "value", base_date: str | None = None) -> pl.DataFrame:
    """기준일 = 100 정규화.

    Args:
        base_date: 기준일 (YYYY-MM-DD). None이면 첫 번째 유효값.
    """
    if base_date is not None:
        from datetime import datetime
        target = datetime.strptime(base_date, "%Y-%m-%d").date()
        base_row = df.filter(pl.col("date") == target)
        if base_row.is_empty():
            # 가장 가까운 날짜
            base_row = df.filter(pl.col("date") <= target).tail(1)
        if base_row.is_empty():
            base_row = df.head(1)
        base_val = base_row[col][0]
    else:
        non_null = df.filter(pl.col(col).is_not_null())
        if non_null.is_empty():
            return df.with_columns(pl.lit(None).alias(f"{col}_norm"))
        base_val = non_null[col][0]

    if base_val is None or base_val == 0:
        return df.with_columns(pl.lit(None).alias(f"{col}_norm"))

    return df.with_columns(
        (pl.col(col) / base_val * 100).alias(f"{col}_norm")
    )


def normalize_multi(df: pl.DataFrame, base_date: str | None = None) -> pl.DataFrame:
    """wide DataFrame의 모든 값 컬럼을 기준일=100 정규화.

    date 컬럼 제외한 모든 수치 컬럼을 정규화.
    """
    result = df.clone()
    for col in df.columns:
        if col == "date":
            continue
        if df[col].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32):
            temp = df.select("date", col)
            normed = normalize(temp, col=col, base_date=base_date)
            norm_col = f"{col}_norm"
            if norm_col in normed.columns:
                result = result.with_columns(normed[norm_col].alias(col))
    return result


def correlation(df: pl.DataFrame, method: str = "pearson") -> pl.DataFrame:
    """복수 시계열 간 상관행렬.

    Args:
        df: wide DataFrame (date, col1, col2, ...).
        method: "pearson" (기본). Polars 기본 지원.

    Returns:
        상관행렬 DataFrame (column, col1, col2, ...).
    """
    value_cols = [c for c in df.columns if c != "date"]
    if len(value_cols) < 2:
        return pl.DataFrame()

    # null 제거 후 상관 계산
    clean = df.select(value_cols).drop_nulls()

    n = len(value_cols)
    rows: list[dict] = []
    for i in range(n):
        row: dict = {"column": value_cols[i]}
        for j in range(n):
            if i == j:
                row[value_cols[j]] = 1.0
            else:
                corr_val = clean.select(
                    pl.corr(value_cols[i], value_cols[j])
                ).item()
                row[value_cols[j]] = round(corr_val, 4) if corr_val is not None else None
        rows.append(row)

    return pl.DataFrame(rows)


def lead_lag(
    df: pl.DataFrame,
    col_a: str,
    col_b: str,
    *,
    max_lag: int = 12,
) -> pl.DataFrame:
    """선행/후행 상관분석.

    col_a를 기준으로 col_b를 -max_lag ~ +max_lag 시프트하여 상관계수 측정.
    양수 lag = col_b가 col_a보다 후행, 음수 = col_b가 선행.

    Returns:
        DataFrame (lag, correlation).
    """
    clean = df.select(col_a, col_b).drop_nulls()
    a = clean[col_a]
    b = clean[col_b]

    lags: list[int] = []
    corrs: list[float | None] = []

    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            corr_val = clean.select(pl.corr(col_a, col_b)).item()
        elif lag > 0:
            shifted = pl.DataFrame({col_a: a[lag:], col_b: b[:len(b) - lag]})
            if shifted.height < 3:
                corr_val = None
            else:
                corr_val = shifted.select(pl.corr(col_a, col_b)).item()
        else:
            shift_abs = abs(lag)
            shifted = pl.DataFrame({col_a: a[:len(a) - shift_abs], col_b: b[shift_abs:]})
            if shifted.height < 3:
                corr_val = None
            else:
                corr_val = shifted.select(pl.corr(col_a, col_b)).item()

        lags.append(lag)
        corrs.append(round(corr_val, 4) if corr_val is not None else None)

    return pl.DataFrame({"lag": lags, "correlation": corrs})


# ── internal ──


def _infer_period(df: pl.DataFrame) -> int:
    """데이터 간격 추론 → YoY 기간 결정.

    - 일별: 252 (영업일)
    - 주별: 52
    - 월별: 12
    - 분기별: 4
    - 연간: 1
    """
    if df.height < 3:
        return 1

    dates = df["date"].drop_nulls()
    if dates.dtype == pl.Date:
        diffs = dates.diff().drop_nulls()
        median_days = diffs.cast(pl.Int64).median()
        if median_days is None:
            return 12
        if median_days <= 5:
            return 252  # daily → ~1 year
        if median_days <= 10:
            return 52  # weekly
        if median_days <= 45:
            return 12  # monthly
        if median_days <= 120:
            return 4  # quarterly
        return 1  # annual

    return 12  # default
