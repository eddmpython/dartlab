"""Plotly 기반 재무 차트 도구.

Polars DataFrame → Plotly Figure 변환. .show(), .to_html(), .write_image() 가능.
LLM 의존성 없음. plotly는 optional dependency.

두 가지 경로:
1. **기존**: ``chart.revenue_trend(c).show()`` — Plotly Figure 직행
2. **ChartSpec**: ``chart.spec_revenue_trend(c)`` → JSON dict → ``chart.chart_from_spec(spec).show()``

ChartSpec JSON 프로토콜::

    {
        "chartType": "combo" | "radar" | "waterfall" | "sparkline" | "heatmap" | "pie",
        "title": str,
        "series": [{"name": str, "data": [number], "color": str, "type": "bar"|"line"}],
        "categories": [str],
        "options": {"unit": str, "stacked": bool, "maxValue": number, ...},
        "meta": {"source": str, "stockCode": str, "corpName": str}
    }

사용법::

    from dartlab.tools import chart

    c = Company("005930")

    # Plotly 직행 (기존)
    chart.revenue_trend(c).show()

    # ChartSpec 경로
    spec = chart.spec_revenue_trend(c)   # → dict
    fig = chart.chart_from_spec(spec)    # → Plotly Figure
    fig.show()

    # 자동 감지
    specs = chart.auto_chart(c)          # → list[dict]
"""

from __future__ import annotations

from typing import Any

import polars as pl

# ══════════════════════════════════════
# DartLab 컬러 팔레트
# ══════════════════════════════════════

COLORS = [
    "#ea4647",  # primary red
    "#fb923c",  # accent orange
    "#3b82f6",  # blue
    "#22c55e",  # green
    "#8b5cf6",  # purple
    "#06b6d4",  # cyan
    "#f59e0b",  # amber
    "#ec4899",  # pink
]


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
    exclude = set(exclude or [])
    return [c for c in df.columns if c not in exclude and df[c].dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32)]


# ══════════════════════════════════════
# 범용 차트
# ══════════════════════════════════════


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
            df: 시계열 DataFrame
            x: X축 컬럼 (기본 "year")
            y: Y축 컬럼(들). None이면 숫자 컬럼 전부.
            title: 차트 제목
            unit: Y축 단위 라벨
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
            stacked: True면 누적 바 차트
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
            labels: 항목 이름 리스트
            values: 증감 값 리스트 (마지막은 합계)
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


# ══════════════════════════════════════
# 재무 템플릿 차트
# ══════════════════════════════════════


def _extract_account_series(df: pl.DataFrame, keyword: str) -> dict[str, float | None]:
    """재무제표에서 계정명 키워드로 연도별 값 추출."""
    if "계정명" not in df.columns:
        return {}
    matched = df.filter(pl.col("계정명").str.contains(keyword))
    if matched.height == 0:
        return {}
    year_cols = sorted([c for c in df.columns if c.isdigit() and len(c) == 4])
    row = matched.row(0, named=True)
    return {yr: row.get(yr) for yr in year_cols if row.get(yr) is not None}


def revenue_trend(company: Any, *, n_years: int = 5) -> Any:
    """매출·영업이익·순이익 추세 차트.

    바: 매출액 | 라인: 영업이익률, 순이익률
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

    # 바: 매출, 영업이익, 순이익
    fig.add_trace(
        go.Bar(
            x=years,
            y=[rev.get(y) for y in years],
            name="매출액",
            marker_color=COLORS[2],
            opacity=0.7,
        )
    )
    fig.add_trace(
        go.Bar(
            x=years,
            y=[oi.get(y) for y in years],
            name="영업이익",
            marker_color=COLORS[1],
            opacity=0.7,
        )
    )
    fig.add_trace(
        go.Bar(
            x=years,
            y=[ni.get(y) for y in years],
            name="당기순이익",
            marker_color=COLORS[0],
            opacity=0.7,
        )
    )

    # 라인: 영업이익률
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
    return fig


def cashflow_pattern(company: Any, *, n_years: int = 5) -> Any:
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
    return fig


def dividend_analysis(company: Any) -> Any:
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
            go.Bar(
                x=df["year"].to_list(),
                y=df["dps"].to_list(),
                name="DPS(원)",
                marker_color=COLORS[2],
                opacity=0.7,
            )
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
    return fig


def balance_sheet_composition(company: Any, *, n_years: int = 5) -> Any:
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
    # 자산 side
    fig.add_trace(go.Bar(x=years, y=[ca.get(y) for y in years], name="유동자산", marker_color=COLORS[2]))
    fig.add_trace(go.Bar(x=years, y=[nca.get(y) for y in years], name="비유동자산", marker_color=COLORS[3]))

    fig.update_layout(
        title=f"{company.corpName} 자산 구성",
        barmode="stack",
        yaxis_title="(백만원)",
    )
    _apply_theme(fig)
    return fig


def profitability_ratios(company: Any, *, n_years: int = 5) -> Any:
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
    return fig


# ══════════════════════════════════════
# ChartSpec 프로토콜
# ══════════════════════════════════════

# 7영역 인사이트 상수
_AREA_NAMES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
_AREA_LABELS = {
    "performance": "성과",
    "profitability": "수익성",
    "health": "건전성",
    "cashflow": "현금흐름",
    "governance": "지배구조",
    "risk": "리스크",
    "opportunity": "기회",
}
_GRADE_MAP = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}


def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    """#RRGGBB → rgba(R,G,B,alpha) 변환."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color


def _meta(company: Any, source: str) -> dict:
    """ChartSpec meta 블록 생성."""
    return {
        "source": source,
        "stockCode": getattr(company, "stockCode", ""),
        "corpName": getattr(company, "corpName", ""),
    }


def _safe_val(v: Any) -> float:
    """None → 0, 나머지 float 변환."""
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


# ──────────────────────────────────────
# spec 함수 8종
# ──────────────────────────────────────


def spec_revenue_trend(company: Any, *, n_years: int = 5) -> dict | None:
    """IS 매출·영업이익·순이익 combo 차트 ChartSpec.

    실험 004 financeToComboSpec 흡수.
    """
    ann = getattr(company, "annual", None)
    if not ann:
        return None
    ann_data, ann_years = ann
    is_data = ann_data.get("IS", {})

    key_accounts = [
        ("매출액", ["sales", "revenue", "interest_income"]),
        ("영업이익", ["operating_income", "operating_profit"]),
        ("당기순이익", ["net_income", "profit_for_the_period", "profit_loss"]),
    ]
    chart_types = ["bar", "line", "line"]
    colors = [COLORS[2], COLORS[0], COLORS[3]]

    series = []
    for i, (label, candidates) in enumerate(key_accounts):
        vals = None
        for cand in candidates:
            if cand in is_data and any(v is not None for v in is_data[cand]):
                vals = is_data[cand]
                break
        if vals is None:
            continue
        recent = vals[-n_years:]
        series.append(
            {
                "name": label,
                "data": [_safe_val(v) for v in recent],
                "color": colors[i],
                "type": chart_types[i],
            }
        )

    if not series:
        return None
    return {
        "chartType": "combo",
        "title": f"{company.corpName} 손익 추이",
        "series": series,
        "categories": ann_years[-n_years:],
        "options": {"unit": "백만원"},
        "meta": _meta(company, "finance"),
    }


def spec_cashflow_waterfall(company: Any) -> dict | None:
    """CF 워터폴 브릿지 ChartSpec.

    실험 007 cashflowWaterfall 흡수.
    """
    ann = getattr(company, "annual", None)
    if not ann:
        return None
    ann_data, ann_years = ann
    cf_data = ann_data.get("CF", {})

    # 최신 연도 데이터 추출
    accts = {
        "cash_and_cash_equivalents_beginning": "기초현금",
        "operating_cashflow": "영업활동",
        "investing_cashflow": "투자활동",
        "financing_cashflow": "재무활동",
        "cash_and_cash_equivalents_ending": "기말현금",
    }
    vals = {}
    for key, label in accts.items():
        arr = cf_data.get(key, [])
        vals[label] = _safe_val(arr[-1]) if arr else 0.0

    if vals["기초현금"] == 0 and vals["영업활동"] == 0:
        return None

    labels = ["기초현금", "영업활동", "투자활동", "재무활동", "기말현금"]
    data = [vals[lb] for lb in labels]

    return {
        "chartType": "waterfall",
        "title": f"{company.corpName} 현금흐름 브릿지 ({ann_years[-1]})",
        "series": [{"name": "현금흐름", "data": data, "color": COLORS[2]}],
        "categories": labels,
        "options": {"unit": "백만원"},
        "meta": _meta(company, "finance"),
    }


def spec_balance_sheet(company: Any, *, n_years: int = 5) -> dict | None:
    """BS 유동/비유동 자산 stacked bar ChartSpec."""
    ann = getattr(company, "annual", None)
    if not ann:
        return None
    ann_data, ann_years = ann
    bs_data = ann_data.get("BS", {})

    accounts = [
        ("유동자산", "current_assets", COLORS[2]),
        ("비유동자산", "noncurrent_assets", COLORS[3]),
    ]
    series = []
    for label, key, color in accounts:
        arr = bs_data.get(key, [])
        if not arr:
            continue
        recent = arr[-n_years:]
        series.append(
            {
                "name": label,
                "data": [_safe_val(v) for v in recent],
                "color": color,
                "type": "bar",
                "stack": "assets",
            }
        )

    if not series:
        return None
    return {
        "chartType": "bar",
        "title": f"{company.corpName} 자산 구성",
        "series": series,
        "categories": ann_years[-n_years:],
        "options": {"unit": "백만원", "stacked": True},
        "meta": _meta(company, "finance"),
    }


def spec_profitability(company: Any, *, n_years: int = 5) -> dict | None:
    """수익성 비율 라인 ChartSpec (ratioSeries 기반)."""
    rs = getattr(company, "ratioSeries", None)
    if rs is None:
        return None
    if isinstance(rs, tuple) and len(rs) == 2:
        ratio_dict = rs[0].get("RATIO", {})
        periods = rs[1]
    else:
        return None

    metrics = [
        ("ROE", "roe", COLORS[0]),
        ("영업이익률", "operatingMargin", COLORS[2]),
        ("순이익률", "netMargin", COLORS[3]),
    ]
    series = []
    for label, key, color in metrics:
        vals = ratio_dict.get(key, [])
        if not vals or not any(v is not None for v in vals):
            continue
        recent = vals[-n_years * 4 :]  # 분기별이므로
        series.append(
            {
                "name": label,
                "data": [_safe_val(v) for v in recent],
                "color": color,
                "type": "line",
            }
        )

    if not series:
        return None
    return {
        "chartType": "line",
        "title": f"{company.corpName} 수익성 추이",
        "series": series,
        "categories": periods[-len(series[0]["data"]) :],
        "options": {"unit": "%"},
        "meta": _meta(company, "finance"),
    }


def spec_dividend(company: Any) -> dict | None:
    """배당 시계열 combo ChartSpec.

    report.dividend (DataFrame with year, dps 등) 또는
    show("dividend") 결과에서 배당 데이터를 추출한다.
    """
    # 1차: report.dividend 시도
    div_df = None
    report = getattr(company, "report", None)
    if report is not None:
        div_obj = getattr(report, "dividend", None)
        if div_obj is not None:
            # ReportDividend.df 또는 직접 DataFrame
            if hasattr(div_obj, "df"):
                div_df = div_obj.df
            elif hasattr(div_obj, "columns"):
                div_df = div_obj

    # 2차: company.dividend 직접 시도
    if div_df is None:
        div_df = getattr(company, "dividend", None)

    if div_df is None or not hasattr(div_df, "columns"):
        return None
    if "year" not in div_df.columns or "dps" not in div_df.columns:
        return None

    df = div_df.sort("year")
    years = [str(y) for y in df["year"].to_list()]
    dps_vals = [_safe_val(v) for v in df["dps"].to_list()]

    if not years or all(v == 0 for v in dps_vals):
        return None

    series = [{"name": "DPS(원)", "data": dps_vals, "color": COLORS[2], "type": "bar"}]

    if "dividendYield" in df.columns:
        series.append(
            {
                "name": "배당수익률(%)",
                "data": [_safe_val(v) for v in df["dividendYield"].to_list()],
                "color": COLORS[0],
                "type": "line",
            }
        )

    return {
        "chartType": "combo",
        "title": f"{company.corpName} 배당 분석",
        "series": series,
        "categories": years,
        "options": {"unit": "원", "secondaryY": ["배당수익률(%)"]},
        "meta": _meta(company, "finance"),
    }


def spec_insight_radar(company: Any) -> dict | None:
    """7영역 인사이트 레이더 ChartSpec.

    실험 006 insightToRadarSpec 흡수.
    """
    insights = getattr(company, "insights", None)
    if insights is None or not hasattr(insights, "performance"):
        return None

    grades = {}
    for name in _AREA_NAMES:
        area = getattr(insights, name, None)
        grades[name] = area.grade if area and hasattr(area, "grade") else "F"

    categories = [_AREA_LABELS.get(n, n) for n in _AREA_NAMES]
    data = [_GRADE_MAP.get(grades[n], 0) for n in _AREA_NAMES]

    return {
        "chartType": "radar",
        "title": f"{company.corpName} 투자 인사이트",
        "series": [{"name": company.corpName, "data": data, "color": COLORS[0]}],
        "categories": categories,
        "options": {"maxValue": 5},
        "meta": _meta(company, "insight"),
    }


def spec_ratio_sparklines(company: Any) -> dict | None:
    """비율 스파크라인 배열 ChartSpec.

    실험 005 ratioSparklines 흡수.
    """
    from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES

    rs = getattr(company, "ratioSeries", None)
    if rs is None:
        return None
    if isinstance(rs, tuple) and len(rs) == 2:
        ratio_dict = rs[0].get("RATIO", {})
        periods = rs[1]
    else:
        return None

    sparklines = []
    for cat_name, fields in RATIO_CATEGORIES:
        cat_items = []
        for field_name in fields:
            vals = ratio_dict.get(field_name, [])
            if not vals:
                continue
            valid_count = sum(1 for v in vals if v is not None)
            if valid_count < 2:
                continue
            latest = next((v for v in reversed(vals) if v is not None), None)
            recent_valid = [v for v in vals[-8:] if v is not None]
            trend = (
                "up"
                if len(recent_valid) >= 2 and recent_valid[-1] > recent_valid[-2]
                else ("down" if len(recent_valid) >= 2 else "neutral")
            )
            cat_items.append(
                {
                    "field": field_name,
                    "values": [_safe_val(v) for v in vals[-20:]],
                    "latest": latest,
                    "trend": trend,
                }
            )
        if cat_items:
            sparklines.append({"category": cat_name, "metrics": cat_items[:3]})

    if not sparklines:
        return None
    return {
        "chartType": "sparkline",
        "title": f"{company.corpName} 비율 스파크라인",
        "series": sparklines,  # 특수 구조: category별 metrics 배열
        "categories": periods[-20:],
        "options": {},
        "meta": _meta(company, "finance"),
    }


def spec_diff_heatmap(company: Any) -> dict | None:
    """diff 변화 밀도 히트맵 ChartSpec.

    실험 008 diffHeatmap 흡수.
    """
    try:
        diff_df = company.diff()
    except (AttributeError, TypeError, OSError):
        return None
    if diff_df is None or not hasattr(diff_df, "shape") or diff_df.shape[0] == 0:
        return None

    change_rates = {}
    for row in diff_df.iter_rows(named=True):
        topic = row["topic"]
        rate = row.get("changeRate", 0) or 0
        change_rates[topic] = float(rate)

    sorted_topics = sorted(change_rates.items(), key=lambda x: x[1], reverse=True)[:30]
    heatmap_data = []
    for topic, rate in sorted_topics:
        intensity = "high" if rate >= 0.5 else ("medium" if rate >= 0.2 else "low")
        heatmap_data.append({"topic": topic, "changeRate": round(rate, 4), "intensity": intensity})

    return {
        "chartType": "heatmap",
        "title": f"{company.corpName} 공시 변화 밀도",
        "series": [{"name": "변화율", "data": heatmap_data}],  # 특수 구조
        "categories": [d["topic"] for d in heatmap_data],
        "options": {"colorScale": {"low": "#22c55e", "medium": "#f59e0b", "high": "#ea4647"}},
        "meta": _meta(company, "docs"),
    }


# ──────────────────────────────────────
# ChartSpec → Plotly Figure 변환기
# ──────────────────────────────────────

_SPEC_GENERATORS = {
    "revenue_trend": spec_revenue_trend,
    "cashflow": spec_cashflow_waterfall,
    "balance_sheet": spec_balance_sheet,
    "profitability": spec_profitability,
    "dividend": spec_dividend,
    "insight_radar": spec_insight_radar,
    "ratio_sparklines": spec_ratio_sparklines,
    "diff_heatmap": spec_diff_heatmap,
}


def chart_from_spec(spec: dict) -> Any:
    """ChartSpec JSON → Plotly Figure.

    모든 chartType을 Plotly로 변환한다.
    sparkline/heatmap 등 특수 타입도 지원.
    """
    go = _ensure_plotly()
    ct = spec.get("chartType", "")

    if ct in ("combo", "bar", "line"):
        return _combo_from_spec(go, spec)
    if ct == "radar":
        return _radar_from_spec(go, spec)
    if ct == "waterfall":
        return _waterfall_from_spec(go, spec)
    if ct == "heatmap":
        return _heatmap_from_spec(go, spec)
    if ct == "sparkline":
        return _sparkline_from_spec(go, spec)
    if ct == "pie":
        return _pie_from_spec(go, spec)

    # fallback: line
    return _combo_from_spec(go, spec)


def _combo_from_spec(go, spec: dict) -> Any:
    """combo/bar/line ChartSpec → Plotly Figure."""
    from plotly.subplots import make_subplots

    series_list = spec.get("series", [])
    categories = spec.get("categories", [])
    opts = spec.get("options", {})
    has_secondary = bool(opts.get("secondaryY"))

    fig = make_subplots(specs=[[{"secondary_y": True}]]) if has_secondary else go.Figure()
    secondary_names = set(opts.get("secondaryY", []))

    for s in series_list:
        stype = s.get("type", "bar")
        name = s.get("name", "")
        data = s.get("data", [])
        color = s.get("color", COLORS[0])
        on_secondary = name in secondary_names

        if stype == "bar":
            trace = go.Bar(
                x=[str(c) for c in categories],
                y=data,
                name=name,
                marker_color=color,
                opacity=0.8,
            )
        else:
            trace = go.Scatter(
                x=[str(c) for c in categories],
                y=data,
                name=name,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=6),
            )

        if has_secondary:
            fig.add_trace(trace, secondary_y=on_secondary)
        else:
            fig.add_trace(trace)

    barmode = "stack" if opts.get("stacked") else "group"
    fig.update_layout(
        title=spec.get("title", ""),
        barmode=barmode,
        yaxis_title=f"({opts.get('unit', '')})" if opts.get("unit") else "",
    )
    _apply_theme(fig)
    return fig


def _radar_from_spec(go, spec: dict) -> Any:
    """radar ChartSpec → Plotly Scatterpolar."""
    series_list = spec.get("series", [])
    categories = spec.get("categories", [])
    max_val = spec.get("options", {}).get("maxValue", 5)

    fig = go.Figure()
    for s in series_list:
        data = s.get("data", [])
        # 닫힌 다각형: 첫 값 반복
        color = s.get("color", COLORS[0])
        # rgba 변환 (Plotly가 8자리 hex 미지원)
        fill_rgba = _hex_to_rgba(color, 0.2)
        fig.add_trace(
            go.Scatterpolar(
                r=data + [data[0]] if data else [],
                theta=categories + [categories[0]] if categories else [],
                fill="toself",
                name=s.get("name", ""),
                line=dict(color=color),
                fillcolor=fill_rgba,
            )
        )

    fig.update_layout(
        title=spec.get("title", ""),
        polar=dict(radialaxis=dict(visible=True, range=[0, max_val])),
    )
    _apply_theme(fig)
    return fig


def _waterfall_from_spec(go, spec: dict) -> Any:
    """waterfall ChartSpec → Plotly Waterfall."""
    categories = spec.get("categories", [])
    series_list = spec.get("series", [])
    data = series_list[0].get("data", []) if series_list else []

    # 첫 항목과 마지막을 total, 나머지는 relative
    measures = []
    for i in range(len(data)):
        if i == 0 or i == len(data) - 1:
            measures.append("total")
        else:
            measures.append("relative")

    fig = go.Figure(
        go.Waterfall(
            x=categories,
            y=data,
            measure=measures,
            connector=dict(line=dict(color="#888", width=1)),
            increasing=dict(marker_color=COLORS[2]),
            decreasing=dict(marker_color=COLORS[0]),
            totals=dict(marker_color=COLORS[4]),
        )
    )
    unit = spec.get("options", {}).get("unit", "")
    fig.update_layout(
        title=spec.get("title", ""),
        yaxis_title=f"({unit})" if unit else "",
    )
    _apply_theme(fig)
    return fig


def _heatmap_from_spec(go, spec: dict) -> Any:
    """heatmap ChartSpec → Plotly Heatmap."""
    series_list = spec.get("series", [])
    heatmap_data = series_list[0].get("data", []) if series_list else []

    topics = [d.get("topic", "") for d in heatmap_data]
    rates = [d.get("changeRate", 0) for d in heatmap_data]

    fig = go.Figure(
        go.Bar(
            x=rates,
            y=topics,
            orientation="h",
            marker_color=[COLORS[0] if r >= 0.5 else COLORS[6] if r >= 0.2 else COLORS[3] for r in rates],
        )
    )
    fig.update_layout(
        title=spec.get("title", ""),
        xaxis_title="변화율",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(topics) * 25),
    )
    _apply_theme(fig)
    return fig


def _sparkline_from_spec(go, spec: dict) -> Any:
    """sparkline ChartSpec → Plotly Figure (서브플롯 격자)."""
    from plotly.subplots import make_subplots

    series_list = spec.get("series", [])
    # series는 category별 metrics 배열
    total_metrics = sum(len(cat.get("metrics", [])) for cat in series_list)
    if total_metrics == 0:
        return go.Figure()

    cols = 3
    rows = (total_metrics + cols - 1) // cols
    titles = []
    for cat in series_list:
        for m in cat.get("metrics", []):
            titles.append(f"{cat['category']}/{m['field']}")

    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titles[: rows * cols])

    idx = 0
    for cat in series_list:
        for m in cat.get("metrics", []):
            r = idx // cols + 1
            c_col = idx % cols + 1
            vals = m.get("values", [])
            color = COLORS[3] if m.get("trend") == "up" else COLORS[0] if m.get("trend") == "down" else COLORS[5]
            fig.add_trace(
                go.Scatter(
                    y=vals,
                    mode="lines",
                    line=dict(color=color, width=1.5),
                    showlegend=False,
                ),
                row=r,
                col=c_col,
            )
            idx += 1

    fig.update_layout(
        title=spec.get("title", ""),
        height=max(300, rows * 120),
        showlegend=False,
    )
    _apply_theme(fig)
    return fig


def _pie_from_spec(go, spec: dict) -> Any:
    """pie ChartSpec → Plotly Pie."""
    series_list = spec.get("series", [])
    categories = spec.get("categories", [])
    data = series_list[0].get("data", []) if series_list else []

    fig = go.Figure(
        go.Pie(
            labels=categories,
            values=data,
            marker=dict(colors=COLORS[: len(categories)]),
            textinfo="label+percent",
        )
    )
    fig.update_layout(title=spec.get("title", ""))
    _apply_theme(fig)
    return fig


# ──────────────────────────────────────
# 자동 차트 감지
# ──────────────────────────────────────


def auto_chart(company: Any) -> list[dict]:
    """사용 가능한 모든 차트의 ChartSpec 리스트를 자동 생성.

    데이터가 없는 차트는 건너뛴다.

    Returns:
        list[dict]: 유효한 ChartSpec JSON 리스트
    """
    specs = []
    for gen in [
        spec_revenue_trend,
        spec_balance_sheet,
        spec_profitability,
        spec_cashflow_waterfall,
        spec_dividend,
        spec_insight_radar,
        spec_ratio_sparklines,
        spec_diff_heatmap,
    ]:
        try:
            s = gen(company)
            if s is not None:
                specs.append(s)
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            continue
    return specs
