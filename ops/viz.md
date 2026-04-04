# Viz

통합 시각화 엔진. 차트·다이어그램을 하나의 패키지에서 관리한다.

| 항목 | 내용 |
|------|------|
| 레이어 | 교차 관심사 (guide/와 동일 위치) |
| 진입점 | `dartlab.viz`, `emit_chart()`, `emit_diagram()` |
| 소비 | Company(finance, docs), analysis(insight), AI runtime |
| 생산 | review(ChartBlock), AI(CHART 이벤트), Jupyter(Plotly Figure) |
| 프로토콜 | VizSpec (ChartSpec JSON 100% 하위호환) |

## VizSpec 프로토콜

기존 ChartSpec JSON과 동일. `vizType` 필드로 chart/diagram 분기.

```json
{
    "chartType": "combo|bar|line|radar|waterfall|heatmap|sparkline|pie",
    "title": "str",
    "series": [{"name": "str", "data": [number], "color": "str", "type": "bar|line"}],
    "categories": ["str"],
    "options": {"unit": "str", "stacked": bool},
    "meta": {"source": "str", "stockCode": "str", "corpName": "str"}
}
```

diagram일 때: `{"vizType": "diagram", "diagramType": "mermaid", "source": "...", "title": "..."}`

## AI → 차트 파이프라인

```
AI 코드 실행 → emit_chart() → stdout 마커 → extract_viz_specs() → CHART 이벤트 → SSE → 클라이언트
```

- `emit_chart(spec)` — ChartSpec dict를 stdout 마커로 출력
- `emit_diagram(type, source)` — 다이어그램 소스를 stdout 마커로 출력
- `extract_viz_specs(stdout)` — 마커 추출 + 텍스트 정제
- `AnalysisEvent("chart", {"charts": [spec]})` — SSE로 전달

## Company → ChartSpec 자동 생성기 8종

| 함수 | chartType | 소스 |
|------|-----------|------|
| `spec_revenue_trend` | combo | IS annual |
| `spec_cashflow_waterfall` | waterfall | CF annual |
| `spec_balance_sheet` | bar (stacked) | BS annual |
| `spec_profitability` | line | ratioSeries |
| `spec_dividend` | combo | report.dividend |
| `spec_insight_radar` | radar | insights |
| `spec_ratio_sparklines` | sparkline | ratioSeries |
| `spec_diff_heatmap` | heatmap | diff() |

## 렌더링 대상

| 대상 | 방식 |
|------|------|
| **VSCode Extension** | SSE chart 이벤트 → Svelte ChartRenderer (SVG) |
| **Web UI (SPA)** | SSE chart 이벤트 → Svelte ChartRenderer (SVG) |
| **Jupyter/Marimo** | `VizSpec.toPlotly()` → Plotly Figure |
| **Review (터미널)** | `[chart: title]` 플레이스홀더 |
| **Review (HTML)** | `<div class="dl-chart" data-spec='...'/>` |
| **Review (JSON)** | spec dict 그대로 |

## 컬러 팔레트

8색. Python `viz/palette.py` + JS `ui/shared/chart/colors.ts` 동일 값 유지.

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/viz/__init__.py` | 공개 API (emit_chart, emit_diagram, VizSpec, COLORS, auto_chart, ...) |
| `src/dartlab/viz/spec.py` | VizSpec dataclass |
| `src/dartlab/viz/palette.py` | COLORS 단일 원천 |
| `src/dartlab/viz/plotly.py` | ChartSpec → Plotly Figure 변환 |
| `src/dartlab/viz/extract.py` | AI stdout 마커 추출 |
| `src/dartlab/viz/generators.py` | Company → ChartSpec 8종 |
| `src/dartlab/viz/charts/` | DataFrame → Plotly Figure (line, bar, pie, waterfall, revenue, ...) |
| `src/dartlab/review/blocks.py` | ChartBlock 타입 |
| `ui/shared/chart/` | Svelte SVG 차트 컴포넌트 (source of truth, web/vscode 공유) |
