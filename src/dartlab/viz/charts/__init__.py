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

from dartlab.core.palette import COLORS
from dartlab.viz.renderers.plotly import _applyTheme, _ensurePlotly

_PERIOD_COL_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _autoEmit(company: Any, generatorName: str) -> None:
    """AI 런타임에서 도메인 차트 호출 시 VizSpec 마커를 자동 emit.

    Jupyter에서는 stdout에 HTML 주석이 찍히지만 사용자에게 보이지 않는다.
    CLI AI 런타임에서는 마커가 캡처되어 인터랙티브 차트로 렌더링된다.
    """
    try:
        from dartlab.viz import emitChart
        from dartlab.viz import generators as gen

        fn = getattr(gen, generatorName, None)
        if fn is None:
            return
        spec = fn(company)
        if spec:
            emitChart(spec)
    except (ImportError, AttributeError, KeyError, OSError, TypeError, ValueError):
        pass


def _autoNumericCols(df: pl.DataFrame, exclude: list[str] | None = None) -> list[str]:
    """숫자 컬럼 자동 감지."""
    exclude_set = set(exclude or [])
    return [
        c for c in df.columns if c not in exclude_set and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)
    ]


def _findRowValue(df: pl.DataFrame, keyword: str, yearCol: str) -> float | None:
    labelCol = "항목" if "항목" in df.columns else None
    if labelCol is None:
        return None
    matched = df.filter(pl.col(labelCol).str.contains(keyword))
    if matched.height == 0:
        return None
    val = matched.row(0, named=True).get(yearCol)
    return float(val) if isinstance(val, (int, float)) and val is not None else None


def _ratioTable(bs: pl.DataFrame, is_: pl.DataFrame) -> pl.DataFrame:
    year_cols = sorted([c for c in bs.columns if _PERIOD_COL_RE.match(c)], reverse=True)
    if not year_cols:
        return pl.DataFrame()

    rows = []
    for year in year_cols:
        equity = _findRowValue(bs, "자본총계", year)
        total_asset = _findRowValue(bs, "자산총계", year)
        revenue = _findRowValue(is_, "매출액", year)
        operating_income = _findRowValue(is_, "영업이익", year)
        net_income = _findRowValue(is_, "당기순이익", year)

        rows.append(
            {
                "year": year,
                "영업이익률": (
                    round(operating_income / revenue * 100, 1)
                    if operating_income is not None and revenue and revenue != 0
                    else None
                ),
                "순이익률": (
                    round(net_income / revenue * 100, 1)
                    if net_income is not None and revenue and revenue != 0
                    else None
                ),
                "ROE": (
                    round(net_income / equity * 100, 1) if net_income is not None and equity and equity != 0 else None
                ),
                "ROA": (
                    round(net_income / total_asset * 100, 1)
                    if net_income is not None and total_asset and total_asset != 0
                    else None
                ),
            }
        )

    return pl.DataFrame(rows)


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
    go = _ensurePlotly()

    if x not in df.columns:
        raise ValueError(f"'{x}' 컬럼이 DataFrame에 없습니다.")

    df_sorted = df.sort(x)
    x_vals = df_sorted[x].to_list()

    if isinstance(y, str):
        y = [y]
    if y is None:
        y = _autoNumericCols(df, exclude=[x])

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
    _applyTheme(fig)
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
    go = _ensurePlotly()

    if x not in df.columns:
        raise ValueError(f"'{x}' 컬럼이 DataFrame에 없습니다.")

    df_sorted = df.sort(x)
    x_vals = [str(v) for v in df_sorted[x].to_list()]

    if isinstance(y, str):
        y = [y]
    if y is None:
        y = _autoNumericCols(df, exclude=[x])

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
    _applyTheme(fig)
    return fig


def pie(
    df: pl.DataFrame,
    *,
    names: str,
    values: str,
    title: str | None = None,
) -> Any:
    """파이 차트."""
    go = _ensurePlotly()

    fig = go.Figure(
        go.Pie(
            labels=df[names].to_list(),
            values=df[values].to_list(),
            marker=dict(colors=COLORS),
            textinfo="label+percent",
        )
    )
    fig.update_layout(title=title or "")
    _applyTheme(fig)
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
    go = _ensurePlotly()

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
    _applyTheme(fig)
    return fig


# ── 재무 템플릿 차트 ──


def _statementFrame(company: Any, axis: str, label: str) -> pl.DataFrame:
    """공개 계약 `panel` 로 재무제표 한 장을 얻는다. 없으면 ValueError.

    예전에는 `company.IS` 처럼 속성으로 읽었다. 그 이름들은 공개 계약에서 빠졌고 지금은
    존재하지 않는다. `getattr(..., None)` 이 늘 None 을 돌려주니 아래 차트 다섯이 전부
    "데이터가 없습니다" 로 죽고 있었다. 회사에 자료가 있고 없고와 무관하게 항상 그랬다.
    """
    try:
        df = company.panel(axis)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{axis} ({label}) 데이터가 없습니다.") from exc
    if df is None or getattr(df, "height", 0) == 0:
        raise ValueError(f"{axis} ({label}) 데이터가 없습니다.")
    return df


def _extractAccountSeries(df: pl.DataFrame, keyword: str) -> dict[str, float | None]:
    """재무제표에서 항목 키워드로 연도별 값 추출."""
    labelCol = "항목" if "항목" in df.columns else None
    if labelCol is None:
        return {}
    matched = df.filter(pl.col(labelCol).str.contains(keyword))
    if matched.height == 0:
        return {}
    year_cols = sorted([c for c in df.columns if _PERIOD_COL_RE.match(c)])
    row = matched.row(0, named=True)
    return {yr: row.get(yr) for yr in year_cols if row.get(yr) is not None}


def revenue(company: Any, *, nYears: int = 5) -> Any:
    """매출·영업이익·순이익 추세 차트 (바+라인 combo).

    Args:
        company: Company 객체.
        n_years: 표시 연도 수.
    """
    go = _ensurePlotly()
    from plotly.subplots import make_subplots

    isDf = _statementFrame(company, "IS", "손익계산서")

    rev = _extractAccountSeries(isDf, "매출액")
    oi = _extractAccountSeries(isDf, "영업이익")
    ni = _extractAccountSeries(isDf, "당기순이익")

    years = sorted(rev.keys())[-nYears:]
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
    _applyTheme(fig)
    _autoEmit(company, "spec_revenue_trend")
    return fig


def cashflow(company: Any, *, nYears: int = 5) -> Any:
    """영업CF/투자CF/재무CF 패턴 차트."""
    go = _ensurePlotly()

    cf_df = _statementFrame(company, "CF", "현금흐름표")

    op = _extractAccountSeries(cf_df, "영업활동")
    inv = _extractAccountSeries(cf_df, "투자활동")
    fin = _extractAccountSeries(cf_df, "재무활동")

    years = sorted(set(op.keys()) | set(inv.keys()) | set(fin.keys()))[-nYears:]
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
    _applyTheme(fig)
    _autoEmit(company, "spec_cashflow_waterfall")
    return fig


def dividend(company: Any) -> Any:
    """DPS 와 배당수익률 차트 (현재 시점).

    옛 구현은 `company.dividend` 속성에서 연도별 표를 기대했다. 그 이름은 공개 계약에서
    빠졌고, 지금 남은 배당 공급원은 `capital` 축의 현재 시점 한 행이다 (DPS · 배당수익률).
    연도별 시계열은 계약 표면에 아직 없다. 없는 것을 지어내지 않고 있는 것만 그린다.
    """
    go = _ensurePlotly()
    from plotly.subplots import make_subplots

    try:
        df = company.capital()
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("배당 데이터가 없습니다.") from exc
    if df is None or getattr(df, "height", 0) == 0:
        raise ValueError("배당 데이터가 없습니다.")

    row = df.row(0, named=True)
    dps = row.get("DPS")
    dividendYield = row.get("배당수익률")
    if dps is None and dividendYield is None:
        raise ValueError("배당 데이터가 없습니다.")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if dps is not None:
        fig.add_trace(go.Bar(x=["현재"], y=[dps], name="DPS(원)", marker_color=COLORS[2], opacity=0.7))

    if dividendYield is not None:
        fig.add_trace(
            go.Scatter(
                x=["현재"],
                y=[dividendYield],
                name="배당수익률(%)",
                mode="lines+markers",
                line=dict(color=COLORS[0], width=2),
            ),
            secondary_y=True,
        )

    fig.update_layout(title=f"{company.corpName} 배당 분석")
    fig.update_yaxes(title_text="DPS (원)", secondary_y=False)
    fig.update_yaxes(title_text="(%)", secondary_y=True)
    _applyTheme(fig)
    _autoEmit(company, "spec_dividend")
    return fig


def balanceSheet(company: Any, *, nYears: int = 5) -> Any:
    """자산/부채/자본 구성 누적 바 차트."""
    go = _ensurePlotly()

    bs_df = _statementFrame(company, "BS", "재무상태표")

    ca = _extractAccountSeries(bs_df, "유동자산")
    nca = _extractAccountSeries(bs_df, "비유동자산")

    years = sorted(set(ca.keys()) | set(nca.keys()))[-nYears:]
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
    _applyTheme(fig)
    _autoEmit(company, "spec_balance_sheet")
    return fig


def profitability(company: Any, *, nYears: int = 5) -> Any:
    """영업이익률·순이익률·ROE 추세 라인 차트."""
    go = _ensurePlotly()

    bs_df = _statementFrame(company, "BS", "재무상태표")
    isDf = _statementFrame(company, "IS", "손익계산서")

    ratios = _ratioTable(bs_df, isDf)
    if ratios.height == 0:
        raise ValueError("재무비율 계산 실패.")

    ratios = ratios.sort("year").tail(nYears)
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
    _applyTheme(fig)
    _autoEmit(company, "spec_profitability")
    return fig


# ── 하위호환 alias ──
revenueTrend = revenue
cashflowPattern = cashflow
dividendAnalysis = dividend
balanceSheetComposition = balanceSheet
profitabilityRatios = profitability
