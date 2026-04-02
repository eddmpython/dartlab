"""ChartSpec JSON → Plotly Figure 변환기.

모든 chartType을 Plotly로 변환한다.
sparkline/heatmap 등 특수 타입도 지원.

사용법::

    from dartlab.viz.plotly import from_spec

    spec = {"chartType": "combo", "title": "...", "series": [...], ...}
    fig = from_spec(spec)
    fig.show()
"""

from __future__ import annotations

from typing import Any

from dartlab.viz.palette import COLORS


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


def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    """#RRGGBB → rgba(R,G,B,alpha) 변환."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color


def from_spec(spec: dict) -> Any:
    """ChartSpec JSON → Plotly Figure.

    Args:
        spec: ChartSpec dict.

    Returns:
        Plotly Figure 객체.
    """
    go = _ensure_plotly()
    ct = spec.get("chartType", "")

    if ct in ("combo", "bar", "line"):
        return _combo(go, spec)
    if ct == "radar":
        return _radar(go, spec)
    if ct == "waterfall":
        return _waterfall(go, spec)
    if ct == "heatmap":
        return _heatmap(go, spec)
    if ct == "sparkline":
        return _sparkline(go, spec)
    if ct == "pie":
        return _pie(go, spec)

    # fallback: line
    return _combo(go, spec)


# ── 변환기 ──


def _combo(go, spec: dict) -> Any:
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


def _radar(go, spec: dict) -> Any:
    """radar ChartSpec → Plotly Scatterpolar."""
    series_list = spec.get("series", [])
    categories = spec.get("categories", [])
    max_val = spec.get("options", {}).get("maxValue", 5)

    fig = go.Figure()
    for s in series_list:
        data = s.get("data", [])
        color = s.get("color", COLORS[0])
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


def _waterfall(go, spec: dict) -> Any:
    """waterfall ChartSpec → Plotly Waterfall."""
    categories = spec.get("categories", [])
    series_list = spec.get("series", [])
    data = series_list[0].get("data", []) if series_list else []

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


def _heatmap(go, spec: dict) -> Any:
    """heatmap ChartSpec → Plotly horizontal bar."""
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


def _sparkline(go, spec: dict) -> Any:
    """sparkline ChartSpec → Plotly Figure (서브플롯 격자)."""
    from plotly.subplots import make_subplots

    series_list = spec.get("series", [])
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


def _pie(go, spec: dict) -> Any:
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
