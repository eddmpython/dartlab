"""범용 DataFrame → Plotly Figure 차트.

Polars DataFrame을 받아서 Plotly Figure를 직접 반환한다.
Jupyter/Marimo에서 ``.show()`` 로 즉시 표시.

사용법::

    from dartlab.viz.charts import line, bar, pie, waterfall

    line(df, x="year", y=["매출액"])
    bar(df, x="year", y=["영업이익"], stacked=True)
    pie(df, names="부문", values="매출")
    waterfall(["기초현금", "영업", "투자", "재무", "기말"], [100, 50, -30, -10, 110])
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.viz.palette import COLORS

_PERIOD_COL_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _auto_emit(company: Any, generator_name: str) -> None:
    """AI 런타임에서 도메인 차트 호출 시 VizSpec 마커를 자동 emit.

    Jupyter에서는 stdout에 HTML 주석이 찍히지만 사용자에게 보이지 않는다.
    VSCode/CLI AI 런타임에서는 마커가 캡처되어 인터랙티브 차트로 렌더링된다.
    """
    try:
        from dartlab.viz import emit_chart
        from dartlab.viz import generators as gen

        fn = getattr(gen, generator_name, None)
        if fn is None:
            return
        spec = fn(company)
        if spec:
            emit_chart(spec)
    except (ImportError, AttributeError, KeyError, OSError, TypeError, ValueError):
        pass


def _ensure_plotly():
    """Lazy import with clear error."""
    try:
        import plotly.graph_objects as go

        return go
    except ImportError:
        raise ImportError("plotly 패키지가 필요합니다.\n  uv add dartlab[charts]") from None


def _apply_theme(fig) -> None:
    """DartLab 테마 적용."""
    fig.update_layout(
        font_family="Pretendard, -apple-system, sans-serif",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=40),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=1)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=1)


def _auto_numeric_cols(df: pl.DataFrame, exclude: list[str] | None = None) -> list[str]:
    """숫자 컬럼 자동 감지."""
    exclude_set = set(exclude or [])
    return [
        c for c in df.columns if c not in exclude_set and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]


# ── 범용 차트 ──


def line(
    df: pl.DataFrame,
    *,
    x: str = "year",
    y: str | list[str] | None = None,
    title: str | None = None,
    unit: str = "백만원",
) -> Any:
    """라인 차트.

    Args:
        df: 시계열 DataFrame.
        x: X축 컬럼 (기본 "year").
        y: Y축 컬럼(들). None이면 숫자 컬럼 전부.
        title: 차트 제목.
        unit: Y축 단위 라벨.
    """
    go = _ensure_plotly()

    if x not in df.columns:
        raise ValueError(f"'{x}' 컬럼이 DataFrame에 없습니다.")

    df_sorted = df.sort(x)
    x_vals = df_sorted[x].to_list()

    if isinstance(y, str):
        y = [y]
    if y is None:
        y = _auto_numeric_cols(df, exclude=[x])

    fig = go.Figure()
    for i, col in enumerate(y):
        if col not in df_sorted.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=df_sorted[col].to_list(),
                mode="lines+markers",
                name=col,
                line=dict(color=COLORS[i % len(COLORS)], width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title=title or "",
        xaxis_title=x,
        yaxis_title=f"({unit})" if unit else "",
    )
    _apply_theme(fig)
    return fig


def bar(
    df: pl.DataFrame,
    *,
    x: str = "year",
    y: str | list[str] | None = None,
    title: str | None = None,
    unit: str = "백만원",
    stacked: bool = False,
) -> Any:
    """바 차트.

    Args:
        stacked: True면 누적 바 차트.
    """
    go = _ensure_plotly()

    if x not in df.columns:
        raise ValueError(f"'{x}' 컬럼이 DataFrame에 없습니다.")

    df_sorted = df.sort(x)
    x_vals = [str(v) for v in df_sorted[x].to_list()]

    if isinstance(y, str):
        y = [y]
    if y is None:
        y = _auto_numeric_cols(df, exclude=[x])

    fig = go.Figure()
    for i, col in enumerate(y):
        if col not in df_sorted.columns:
            continue
        fig.add_trace(
            go.Bar(
                x=x_vals,
                y=df_sorted[col].to_list(),
                name=col,
                marker_color=COLORS[i % len(COLORS)],
            )
        )

    barmode = "stack" if stacked else "group"
    fig.update_layout(
        title=title or "",
        xaxis_title=x,
        yaxis_title=f"({unit})" if unit else "",
        barmode=barmode,
    )
    _apply_theme(fig)
    return fig


def pie(
    df: pl.DataFrame,
    *,
    names: str,
    values: str,
    title: str | None = None,
) -> Any:
    """파이 차트."""
    go = _ensure_plotly()

    fig = go.Figure(
        go.Pie(
            labels=df[names].to_list(),
            values=df[values].to_list(),
            marker=dict(colors=COLORS),
            textinfo="label+percent",
        )
    )
    fig.update_layout(title=title or "")
    _apply_theme(fig)
    return fig


def waterfall(
    labels: list[str],
    values: list[float],
    *,
    title: str | None = None,
    unit: str = "백만원",
) -> Any:
    """폭포 차트 (브릿지 분석용).

    Args:
        labels: 항목 이름 리스트.
        values: 증감 값 리스트 (마지막은 합계).
    """
    go = _ensure_plotly()

    measures = ["relative"] * (len(values) - 1) + ["total"]

    fig = go.Figure(
        go.Waterfall(
            x=labels,
            y=values,
            measure=measures,
            connector=dict(line=dict(color="#888", width=1)),
            increasing=dict(marker_color=COLORS[2]),
            decreasing=dict(marker_color=COLORS[0]),
            totals=dict(marker_color=COLORS[4]),
        )
    )
    fig.update_layout(
        title=title or "",
        yaxis_title=f"({unit})" if unit else "",
    )
    _apply_theme(fig)
    return fig


# ── 재무 템플릿 차트 ──


def _extract_account_series(df: pl.DataFrame, keyword: str) -> dict[str, float | None]:
    """재무제표에서 계정명 키워드로 연도별 값 추출."""
    if "계정명" not in df.columns:
        return {}
    matched = df.filter(pl.col("계정명").str.contains(keyword))
    if matched.height == 0:
        return {}
    year_cols = sorted([c for c in df.columns if _PERIOD_COL_RE.match(c)])
    row = matched.row(0, named=True)
    return {yr: row.get(yr) for yr in year_cols if row.get(yr) is not None}


def revenue(company: Any, *, n_years: int = 5) -> Any:
    """매출·영업이익·순이익 추세 차트 (바+라인 combo).

    Args:
        company: Company 객체.
        n_years: 표시 연도 수.
    """
    go = _ensure_plotly()
    from plotly.subplots import make_subplots

    is_df = getattr(company, "IS", None)
    if is_df is None:
        raise ValueError("IS (손익계산서) 데이터가 없습니다.")

    rev = _extract_account_series(is_df, "매출액")
    oi = _extract_account_series(is_df, "영업이익")
    ni = _extract_account_series(is_df, "당기순이익")

    years = sorted(rev.keys())[-n_years:]
    if not years:
        raise ValueError("매출 데이터를 찾을 수 없습니다.")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(x=years, y=[rev.get(y) for y in years], name="매출액", marker_color=COLORS[2], opacity=0.7))
    fig.add_trace(go.Bar(x=years, y=[oi.get(y) for y in years], name="영업이익", marker_color=COLORS[1], opacity=0.7))
    fig.add_trace(go.Bar(x=years, y=[ni.get(y) for y in years], name="당기순이익", marker_color=COLORS[0], opacity=0.7))

    margins = []
    for y in years:
        r = rev.get(y)
        o = oi.get(y)
        if r and r != 0 and o is not None:
            margins.append(round(o / r * 100, 1))
        else:
            margins.append(None)

    fig.add_trace(
        go.Scatter(
            x=years,
            y=margins,
            name="영업이익률(%)",
            mode="lines+markers",
            line=dict(color=COLORS[4], width=2, dash="dot"),
            marker=dict(size=8),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"{company.corpName} 매출·이익 추세",
        barmode="group",
        yaxis_title="(백만원)",
    )
    fig.update_yaxes(title_text="(%)", secondary_y=True)
    _apply_theme(fig)
    _auto_emit(company, "spec_revenue_trend")
    return fig


def cashflow(company: Any, *, n_years: int = 5) -> Any:
    """영업CF/투자CF/재무CF 패턴 차트."""
    go = _ensure_plotly()

    cf_df = getattr(company, "CF", None)
    if cf_df is None:
        raise ValueError("CF (현금흐름표) 데이터가 없습니다.")

    op = _extract_account_series(cf_df, "영업활동")
    inv = _extract_account_series(cf_df, "투자활동")
    fin = _extract_account_series(cf_df, "재무활동")

    years = sorted(set(op.keys()) | set(inv.keys()) | set(fin.keys()))[-n_years:]
    if not years:
        raise ValueError("현금흐름 데이터를 찾을 수 없습니다.")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=[op.get(y) for y in years], name="영업활동CF", marker_color=COLORS[2]))
    fig.add_trace(go.Bar(x=years, y=[inv.get(y) for y in years], name="투자활동CF", marker_color=COLORS[0]))
    fig.add_trace(go.Bar(x=years, y=[fin.get(y) for y in years], name="재무활동CF", marker_color=COLORS[1]))

    fig.update_layout(
        title=f"{company.corpName} 현금흐름 패턴",
        barmode="group",
        yaxis_title="(백만원)",
    )
    _apply_theme(fig)
    _auto_emit(company, "spec_cashflow_waterfall")
    return fig


def dividend(company: Any) -> Any:
    """DPS + 배당수익률 + 배당성향 차트."""
    go = _ensure_plotly()
    from plotly.subplots import make_subplots

    div_df = getattr(company, "dividend", None)
    if div_df is None:
        raise ValueError("dividend (배당) 데이터가 없습니다.")

    if "year" not in div_df.columns:
        raise ValueError("year 컬럼이 없습니다.")

    df = div_df.sort("year")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "dps" in df.columns:
        fig.add_trace(
            go.Bar(x=df["year"].to_list(), y=df["dps"].to_list(), name="DPS(원)", marker_color=COLORS[2], opacity=0.7)
        )

    if "dividendYield" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["year"].to_list(),
                y=df["dividendYield"].to_list(),
                name="배당수익률(%)",
                mode="lines+markers",
                line=dict(color=COLORS[0], width=2),
            ),
            secondary_y=True,
        )

    if "payoutRatio" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["year"].to_list(),
                y=df["payoutRatio"].to_list(),
                name="배당성향(%)",
                mode="lines+markers",
                line=dict(color=COLORS[1], width=2, dash="dot"),
            ),
            secondary_y=True,
        )

    fig.update_layout(title=f"{company.corpName} 배당 분석")
    fig.update_yaxes(title_text="DPS (원)", secondary_y=False)
    fig.update_yaxes(title_text="(%)", secondary_y=True)
    _apply_theme(fig)
    _auto_emit(company, "spec_dividend")
    return fig


def balance_sheet(company: Any, *, n_years: int = 5) -> Any:
    """자산/부채/자본 구성 누적 바 차트."""
    go = _ensure_plotly()

    bs_df = getattr(company, "BS", None)
    if bs_df is None:
        raise ValueError("BS (재무상태표) 데이터가 없습니다.")

    ca = _extract_account_series(bs_df, "유동자산")
    nca = _extract_account_series(bs_df, "비유동자산")

    years = sorted(set(ca.keys()) | set(nca.keys()))[-n_years:]
    if not years:
        raise ValueError("재무상태표 데이터를 찾을 수 없습니다.")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=[ca.get(y) for y in years], name="유동자산", marker_color=COLORS[2]))
    fig.add_trace(go.Bar(x=years, y=[nca.get(y) for y in years], name="비유동자산", marker_color=COLORS[3]))

    fig.update_layout(
        title=f"{company.corpName} 자산 구성",
        barmode="stack",
        yaxis_title="(백만원)",
    )
    _apply_theme(fig)
    _auto_emit(company, "spec_balance_sheet")
    return fig


def profitability(company: Any, *, n_years: int = 5) -> Any:
    """영업이익률·순이익률·ROE 추세 라인 차트."""
    go = _ensure_plotly()

    from dartlab.tools.table import ratio_table as _ratio_table

    bs_df = getattr(company, "BS", None)
    is_df = getattr(company, "IS", None)
    if bs_df is None or is_df is None:
        raise ValueError("BS, IS 데이터가 필요합니다.")

    ratios = _ratio_table(bs_df, is_df)
    if ratios.height == 0:
        raise ValueError("재무비율 계산 실패.")

    ratios = ratios.sort("year").tail(n_years)
    years = ratios["year"].to_list()

    fig = go.Figure()
    for i, col in enumerate(["영업이익률", "순이익률", "ROE"]):
        if col in ratios.columns:
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=ratios[col].to_list(),
                    name=f"{col}(%)",
                    mode="lines+markers",
                    line=dict(color=COLORS[i], width=2),
                    marker=dict(size=7),
                )
            )

    fig.update_layout(
        title=f"{company.corpName} 수익성 추이",
        yaxis_title="(%)",
    )
    _apply_theme(fig)
    _auto_emit(company, "spec_profitability")
    return fig


# ── 하위호환 alias ──
revenue_trend = revenue
cashflow_pattern = cashflow
dividend_analysis = dividend
balance_sheet_composition = balance_sheet
profitability_ratios = profitability
