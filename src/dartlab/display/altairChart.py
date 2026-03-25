"""Altair 기반 경량 차트 (Plotly 대안, 2MB vs 14MB)."""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.display._detect import hasAltair

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")

COLORS = [
    "#ea4647",
    "#fb923c",
    "#3b82f6",
    "#22c55e",
    "#8b5cf6",
    "#06b6d4",
    "#f59e0b",
    "#ec4899",
]


def _periodColumns(df: pl.DataFrame) -> list[str]:
    """기간 컬럼 추출 (오래된 순)."""
    cols = [c for c in df.columns if _PERIOD_RE.match(c)]
    return sorted(cols)


def _labelColumn(df: pl.DataFrame) -> str | None:
    """계정명 컬럼 찾기."""
    for candidate in ("계정명", "label", "account_nm", "topic"):
        if candidate in df.columns:
            return candidate
    return None


def timeseriesChart(df: pl.DataFrame, *, y: list[str] | None = None, topic: str = "") -> Any:
    """재무 시계열 → Altair Chart."""
    if not hasAltair():
        msg = "altair 패키지가 필요합니다: pip install dartlab[altair]"
        raise ImportError(msg)

    import altair as alt

    periodCols = _periodColumns(df)
    labelCol = _labelColumn(df)

    if not periodCols:
        msg = "기간 컬럼을 찾을 수 없습니다"
        raise ValueError(msg)

    # y 컬럼 결정: 지정되지 않으면 label 컬럼 기준으로 전체 행
    if y and labelCol:
        filtered = df.filter(pl.col(labelCol).is_in(y))
    else:
        filtered = df

    # long format 변환
    rows: list[dict] = []
    for row in filtered.iter_rows(named=True):
        name = str(row.get(labelCol, "")) if labelCol else "value"
        for col in periodCols:
            val = row.get(col)
            if val is not None and isinstance(val, (int, float)):
                rows.append({"기간": col, "계정": name, "값": float(val)})

    if not rows:
        msg = "차트 데이터가 없습니다"
        raise ValueError(msg)

    longDf = pl.DataFrame(rows)
    pandasDf = longDf.to_pandas()

    # 계정 수에 따라 bar vs line
    accounts = pandasDf["계정"].unique()
    if len(accounts) <= 3:
        chart = (
            alt.Chart(pandasDf)
            .mark_bar(opacity=0.8)
            .encode(
                x=alt.X("기간:N", sort=periodCols, title="기간"),
                y=alt.Y("값:Q", title="금액"),
                color=alt.Color("계정:N", scale=alt.Scale(range=COLORS[: len(accounts)])),
                xOffset="계정:N",
                tooltip=["기간", "계정", "값"],
            )
        )
    else:
        chart = (
            alt.Chart(pandasDf)
            .mark_line(point=True)
            .encode(
                x=alt.X("기간:N", sort=periodCols, title="기간"),
                y=alt.Y("값:Q", title="금액"),
                color=alt.Color("계정:N", scale=alt.Scale(range=COLORS[: len(accounts)])),
                tooltip=["기간", "계정", "값"],
            )
        )

    title = topic if topic else "재무 시계열"
    chart = chart.properties(title=title, width=500, height=300)

    return chart


def ratioChart(ratios: list[dict], *, topic: str = "재무비율 추이") -> Any:
    """비율 시계열 dict list → Altair Chart."""
    if not hasAltair():
        msg = "altair 패키지가 필요합니다: pip install dartlab[altair]"
        raise ImportError(msg)

    import altair as alt

    pandasDf = pl.DataFrame(ratios).to_pandas()

    if "year" not in pandasDf.columns or "value" not in pandasDf.columns:
        msg = "year, value 컬럼이 필요합니다"
        raise ValueError(msg)

    nameCol = "name" if "name" in pandasDf.columns else None

    if nameCol:
        chart = (
            alt.Chart(pandasDf)
            .mark_line(point=True)
            .encode(
                x=alt.X("year:N", title="연도"),
                y=alt.Y("value:Q", title="값"),
                color=alt.Color(f"{nameCol}:N", scale=alt.Scale(range=COLORS)),
                tooltip=["year", nameCol, "value"],
            )
        )
    else:
        chart = (
            alt.Chart(pandasDf)
            .mark_line(point=True)
            .encode(
                x=alt.X("year:N", title="연도"),
                y=alt.Y("value:Q", title="값"),
                tooltip=["year", "value"],
            )
        )

    return chart.properties(title=topic, width=500, height=300)
