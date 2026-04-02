"""VizSpec — 통합 시각화 스펙 프로토콜.

기존 ChartSpec JSON과 100% 하위호환.
``vizType`` 필드로 chart / diagram 분기.

ChartSpec JSON 프로토콜::

    {
        "chartType": "combo" | "bar" | "line" | "radar" | "waterfall"
                     | "heatmap" | "sparkline" | "pie",
        "title": str,
        "series": [{"name": str, "data": [number], "color": str, "type": "bar"|"line"}],
        "categories": [str],
        "options": {"unit": str, "stacked": bool, "maxValue": number, ...},
        "meta": {"source": str, "stockCode": str, "corpName": str}
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VizSpec:
    """통합 시각화 스펙.

    vizType:
        - ``"chart"``: 데이터 차트 (combo/bar/line/radar/waterfall/heatmap/sparkline/pie)
        - ``"diagram"``: 다이어그램 (mermaid 등)

    chart 모드일 때 ``toDict()`` 출력은 기존 ChartSpec JSON과 동일
    → Svelte ``ChartRenderer`` 변경 0줄.
    """

    vizType: str = "chart"

    # ── chart ──
    chartType: str = ""
    title: str = ""
    series: list[dict[str, Any]] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    # ── diagram ──
    diagramType: str = ""
    source: str = ""

    # ── 변환 ──

    def toDict(self) -> dict[str, Any]:
        """ChartSpec 호환 JSON dict.

        vizType=chart → 기존 ChartSpec 필드만 포함 (하위호환).
        vizType=diagram → vizType, diagramType, source, title, meta.
        """
        if self.vizType == "diagram":
            return {
                "vizType": "diagram",
                "diagramType": self.diagramType,
                "source": self.source,
                "title": self.title,
                "meta": self.meta,
            }
        return {
            "chartType": self.chartType,
            "title": self.title,
            "series": self.series,
            "categories": self.categories,
            "options": self.options,
            "meta": self.meta,
        }

    def toJson(self) -> str:
        """JSON 문자열."""
        return json.dumps(self.toDict(), ensure_ascii=False, default=str)

    def toPlotly(self) -> Any:
        """Plotly Figure (lazy import).

        Raises:
            ImportError: plotly 미설치 시.
        """
        from dartlab.viz.plotly import from_spec

        return from_spec(self.toDict())

    def toHtml(self) -> str:
        """Plotly HTML (CDN, fragment)."""
        fig = self.toPlotly()
        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    @staticmethod
    def fromDict(d: dict[str, Any]) -> "VizSpec":
        """dict → VizSpec 변환."""
        viz_type = d.get("vizType", "chart")
        if viz_type == "diagram":
            return VizSpec(
                vizType="diagram",
                diagramType=d.get("diagramType", ""),
                source=d.get("source", ""),
                title=d.get("title", ""),
                meta=d.get("meta", {}),
            )
        return VizSpec(
            vizType="chart",
            chartType=d.get("chartType", ""),
            title=d.get("title", ""),
            series=d.get("series", []),
            categories=d.get("categories", []),
            options=d.get("options", {}),
            meta=d.get("meta", {}),
        )
