"""dartlab.viz — 통합 시각화 엔진.

차트(ChartSpec), 다이어그램(Mermaid), AI 시각화 emit을 하나의 엔진에서 관리한다.

사용법::

    import dartlab

    # Company → ChartSpec 자동 생성
    specs = dartlab.viz.auto_chart(c)
    spec = dartlab.viz.spec_revenue_trend(c)

    # DataFrame → Plotly Figure (Jupyter용)
    dartlab.viz.line(df, x="year", y=["매출액"])
    dartlab.viz.bar(df, x="year", y=["영업이익"])
    dartlab.viz.revenue(c).show()

    # AI 코드에서 차트/다이어그램 출력
    from dartlab.viz import emit_chart, emit_diagram
    emit_chart({"chartType": "combo", "title": "...", ...})
    emit_diagram("mermaid", "graph LR\\n  A-->B")

    # ChartSpec → Plotly Figure 변환
    from dartlab.viz.plotly import from_spec
    fig = from_spec(spec)
"""

from __future__ import annotations

import json

# ── 팔레트 ──
from dartlab.viz.palette import COLORS  # noqa: F401

# ── VizSpec ──
from dartlab.viz.spec import VizSpec  # noqa: F401

# ── Company → ChartSpec 생성기 ──
from dartlab.viz.generators import (  # noqa: F401
    auto_chart,
    spec_balance_sheet,
    spec_cashflow_waterfall,
    spec_diff_heatmap,
    spec_dividend,
    spec_insight_radar,
    spec_profitability,
    spec_ratio_sparklines,
    spec_revenue_trend,
    SPEC_GENERATORS,
)

# ── DataFrame → Plotly Figure (Jupyter) ──
from dartlab.viz.charts import (  # noqa: F401
    line,
    bar,
    pie,
    waterfall,
    revenue,
    cashflow,
    dividend as dividend_chart,
    balance_sheet as balance_sheet_chart,
    profitability as profitability_chart,
    # 하위호환 alias
    revenue_trend,
    cashflow_pattern,
    dividend_analysis,
    balance_sheet_composition,
    profitability_ratios,
)

# ── ChartSpec → Plotly Figure 변환 ──
from dartlab.viz.plotly import from_spec as chart_from_spec  # noqa: F401

# ── AI stdout 마커 추출 ──
from dartlab.viz.extract import extract_viz_specs  # noqa: F401


# ══════════════════════════════════════
# AI 코드용 emit 함수
# ══════════════════════════════════════

_MARKER_START = "<!--DARTLAB_VIZ:"
_MARKER_END = ":VIZ_END-->"


def emit_chart(spec: dict) -> None:
    """AI 코드에서 차트 출력.

    런타임이 stdout에서 마커를 자동 추출하여 CHART 이벤트로 전환한다.

    Args:
        spec: ChartSpec dict. chartType, title, series, categories 필수.

    Example::

        emit_chart({
            "chartType": "combo",
            "title": "삼성전자 매출 추이",
            "series": [{"name": "매출", "data": [100, 120, 150], "type": "bar"}],
            "categories": ["2022", "2023", "2024"],
        })
    """
    spec.setdefault("vizType", "chart")
    print(f"{_MARKER_START}{json.dumps(spec, ensure_ascii=False)}{_MARKER_END}")


def emit_diagram(diagram_type: str, source: str, *, title: str = "") -> None:
    """AI 코드에서 다이어그램 출력.

    Args:
        diagram_type: 다이어그램 종류 ("mermaid" 등).
        source: 다이어그램 소스 코드.
        title: 제목 (선택).

    Example::

        emit_diagram("mermaid", "graph LR\\n  매출-->영업이익-->순이익-->FCF")
    """
    spec = {
        "vizType": "diagram",
        "diagramType": diagram_type,
        "source": source,
        "title": title,
    }
    print(f"{_MARKER_START}{json.dumps(spec, ensure_ascii=False)}{_MARKER_END}")


__all__ = [
    # palette
    "COLORS",
    # spec
    "VizSpec",
    # generators
    "auto_chart",
    "spec_revenue_trend",
    "spec_cashflow_waterfall",
    "spec_balance_sheet",
    "spec_profitability",
    "spec_dividend",
    "spec_insight_radar",
    "spec_ratio_sparklines",
    "spec_diff_heatmap",
    "SPEC_GENERATORS",
    # charts (Plotly)
    "line",
    "bar",
    "pie",
    "waterfall",
    "revenue",
    "cashflow",
    "dividend_chart",
    "balance_sheet_chart",
    "profitability_chart",
    # plotly
    "chart_from_spec",
    # extract
    "extract_viz_specs",
    # emit
    "emit_chart",
    "emit_diagram",
]
