"""재무 테이블 가공 도구.

Polars DataFrame을 받아 YoY 변동, 재무비율, 요약통계 등을 계산한다.
LLM 의존성 없이 독립 동작. 보고서 생성·차트 데이터 준비에 사용.

사용법::

    from dartlab.tools import table

    c = Company("005930")
    table.yoy_change(c.dividend, value_cols=["dps"])
    table.ratio_table(c.BS, c.IS)
    table.summary_stats(c.dividend)
"""

from __future__ import annotations

import math

import polars as pl

# ══════════════════════════════════════
# YoY 변동 계산
# ══════════════════════════════════════


def yoy_change(
    df: pl.DataFrame,
    *,
    year_col: str = "year",
    value_cols: list[str] | None = None,
    pct: bool = True,
) -> pl.DataFrame:
    """시계열 DataFrame에 YoY 변동 컬럼 추가.

    Args:
            df: year 컬럼이 있는 시계열 DataFrame
            year_col: 연도 컬럼명
            value_cols: YoY 계산할 컬럼들. None이면 숫자 컬럼 전부.
            pct: True면 % 변동, False면 절대 변동

    Returns:
            원본 + '{col}_YoY' 컬럼이 추가된 DataFrame
    """
    if year_col not in df.columns:
        return df

    df = df.sort(year_col)

    if value_cols is None:
        value_cols = [
            c for c in df.columns if c != year_col and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
        ]

    for col in value_cols:
        if col not in df.columns:
            continue
        prev = pl.col(col).shift(1)
        if pct:
            yoy_expr = ((pl.col(col) - prev) / prev.abs() * 100).round(1)
        else:
            yoy_expr = (pl.col(col) - prev).round(0)
        df = df.with_columns(yoy_expr.alias(f"{col}_YoY"))

    return df


# ══════════════════════════════════════
# 재무비율 계산
# ══════════════════════════════════════


def _find_row_value(df: pl.DataFrame, keyword: str, year_col: str) -> float | None:
    """계정명 부분매칭으로 값 추출."""
    if "계정명" not in df.columns:
        return None
    matched = df.filter(pl.col("계정명").str.contains(keyword))
    if matched.height == 0:
        return None
    val = matched.row(0, named=True).get(year_col)
    return float(val) if isinstance(val, (int, float)) and val is not None else None


def ratio_table(
    bs: pl.DataFrame,
    is_: pl.DataFrame,
    *,
    cf: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """BS·IS·CF에서 핵심 재무비율 계산.

    Returns:
            year | 부채비율 | 유동비율 | 영업이익률 | 순이익률 | ROE | ROA
    """
    year_cols = sorted(
        [c for c in bs.columns if c.isdigit() and len(c) == 4],
        reverse=True,
    )
    if not year_cols:
        return pl.DataFrame()

    rows = []
    for yr in year_cols:
        row: dict[str, float | int | None] = {"year": int(yr)}

        debt = _find_row_value(bs, "부채총계", yr)
        equity = _find_row_value(bs, "자본총계", yr)
        total_asset = _find_row_value(bs, "자산총계", yr)
        ca = _find_row_value(bs, "유동자산", yr)
        cl = _find_row_value(bs, "유동부채", yr)

        rev = _find_row_value(is_, "매출액", yr)
        oi = _find_row_value(is_, "영업이익", yr)
        ni = _find_row_value(is_, "당기순이익", yr)

        row["부채비율"] = round(debt / equity * 100, 1) if debt and equity and equity != 0 else None
        row["유동비율"] = round(ca / cl * 100, 1) if ca and cl and cl != 0 else None
        row["영업이익률"] = round(oi / rev * 100, 1) if oi is not None and rev and rev != 0 else None
        row["순이익률"] = round(ni / rev * 100, 1) if ni is not None and rev and rev != 0 else None
        row["ROE"] = round(ni / equity * 100, 1) if ni is not None and equity and equity != 0 else None
        row["ROA"] = round(ni / total_asset * 100, 1) if ni is not None and total_asset and total_asset != 0 else None

        rows.append(row)

    return pl.DataFrame(rows)


# ══════════════════════════════════════
# 요약 통계
# ══════════════════════════════════════


def summary_stats(
    df: pl.DataFrame,
    *,
    value_cols: list[str] | None = None,
    year_col: str = "year",
) -> pl.DataFrame:
    """시계열 컬럼의 요약 통계 (mean, min, max, std, CAGR, trend).

    Returns:
            metric | mean | min | max | std | cagr | latest | trend
    """
    if year_col not in df.columns:
        return pl.DataFrame()

    df_sorted = df.sort(year_col)

    if value_cols is None:
        value_cols = [
            c for c in df.columns if c != year_col and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
        ]

    rows = []
    for col in value_cols:
        if col not in df.columns:
            continue
        series = df_sorted[col].drop_nulls()
        if series.len() == 0:
            continue

        values = series.to_list()
        mean_val = series.mean()
        min_val = series.min()
        max_val = series.max()
        std_val = series.std() if series.len() > 1 else 0
        latest = values[-1]

        # CAGR
        cagr = None
        if len(values) >= 2 and values[0] and values[0] > 0 and values[-1] > 0:
            n = len(values) - 1
            cagr = round(((values[-1] / values[0]) ** (1 / n) - 1) * 100, 1)

        # Trend
        if len(values) >= 3:
            recent_3 = values[-3:]
            if all(recent_3[i] <= recent_3[i + 1] for i in range(len(recent_3) - 1)):
                trend = "상승"
            elif all(recent_3[i] >= recent_3[i + 1] for i in range(len(recent_3) - 1)):
                trend = "하락"
            else:
                trend = "변동"
        else:
            trend = "-"

        rows.append(
            {
                "metric": col,
                "mean": round(mean_val, 1) if mean_val is not None else None,
                "min": round(min_val, 1) if min_val is not None else None,
                "max": round(max_val, 1) if max_val is not None else None,
                "std": round(std_val, 1) if std_val is not None else None,
                "cagr": cagr,
                "latest": round(latest, 1) if isinstance(latest, float) else latest,
                "trend": trend,
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


# ══════════════════════════════════════
# 피벗
# ══════════════════════════════════════


def pivot_accounts(
    df: pl.DataFrame,
    *,
    account_col: str = "계정명",
) -> pl.DataFrame:
    """재무제표를 피벗: 행=연도, 열=계정명.

    입력: 계정명 | 2024 | 2023 | 2022
    출력: year | 매출액 | 영업이익 | ...
    """
    if account_col not in df.columns:
        return df

    year_cols = sorted(
        [c for c in df.columns if c.isdigit() and len(c) == 4],
    )
    if not year_cols:
        return df

    accounts = df[account_col].to_list()
    rows = []
    for yr in year_cols:
        row: dict[str, int | float | None] = {"year": int(yr)}
        for i, acct in enumerate(accounts):
            val = df.row(i, named=True).get(yr)
            row[acct] = val
        rows.append(row)

    return pl.DataFrame(rows)


# ══════════════════════════════════════
# 한국어 포맷
# ══════════════════════════════════════


def format_korean(
    df: pl.DataFrame,
    *,
    unit: str = "백만원",
    cols: list[str] | None = None,
) -> pl.DataFrame:
    """숫자 컬럼을 한국어 단위로 변환 (12.3억원, 1.2조원 등).

    Args:
            df: 변환할 DataFrame
            unit: 원본 단위 ("백만원" → 억/조 변환)
            cols: 변환할 컬럼. None이면 숫자 컬럼 전부.

    Returns:
            문자열 컬럼으로 변환된 DataFrame
    """
    if cols is None:
        cols = [c for c in df.columns if df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)]

    result = df
    for col in cols:
        if col not in result.columns:
            continue
        formatted = result[col].map_elements(
            lambda v: _format_korean_number(v, unit) if v is not None else "-",
            return_dtype=pl.Utf8,
        )
        result = result.with_columns(formatted.alias(col))

    return result


def _format_korean_number(value: float | int, unit: str = "백만원") -> str:
    """숫자를 한국어 단위로 변환."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"

    # 백만원 → 실제 금액 변환
    if unit == "백만원":
        actual = value  # 이미 백만원 단위
        if abs(actual) >= 1_000_000:
            return f"{actual / 1_000_000:.1f}조원"
        elif abs(actual) >= 100:
            return f"{actual / 100:.1f}억원"
        else:
            return f"{actual:.0f}백만원"
    elif unit == "원":
        if abs(value) >= 100_000_000:
            return f"{value / 100_000_000:.1f}억원"
        elif abs(value) >= 10_000:
            return f"{value / 10_000:.0f}만원"
        else:
            return f"{value:,.0f}원"
    else:
        return f"{value:,.0f}"


# ══════════════════════════════════════
# 성장률 매트릭스
# ══════════════════════════════════════


def growth_matrix(
    df: pl.DataFrame,
    *,
    year_col: str = "year",
    value_cols: list[str] | None = None,
) -> pl.DataFrame:
    """다기간 CAGR 매트릭스: 1Y, 2Y, 3Y, 5Y 복합성장률.

    Returns:
            metric | 1Y | 2Y | 3Y | 5Y
    """
    if year_col not in df.columns:
        return pl.DataFrame()

    df_sorted = df.sort(year_col)

    if value_cols is None:
        value_cols = [
            c for c in df.columns if c != year_col and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
        ]

    rows = []
    for col in value_cols:
        if col not in df.columns:
            continue
        series = df_sorted[col].drop_nulls().to_list()
        if len(series) < 2:
            continue

        row: dict[str, str | float | None] = {"metric": col}
        for period_name, n in [("1Y", 1), ("2Y", 2), ("3Y", 3), ("5Y", 5)]:
            if len(series) > n and series[-(n + 1)] and series[-(n + 1)] > 0 and series[-1] > 0:
                cagr = ((series[-1] / series[-(n + 1)]) ** (1 / n) - 1) * 100
                row[period_name] = round(cagr, 1)
            else:
                row[period_name] = None

        rows.append(row)

    return pl.DataFrame(rows) if rows else pl.DataFrame()
