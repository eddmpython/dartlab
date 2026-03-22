# 실험 003: Svelte 차트 컴포넌트 POC 설계

실험일: 2026-03-19

## 목적
001(LayerChart 2.0 채택)과 002(데이터 형상 카탈로그) 결과를 바탕으로,
실제 Svelte 컴포넌트 구조·props 인터페이스·테마 연동 방안을 설계한다.

## 기술 스택
- **LayerChart 2.0** (`layerchart@next`) — Svelte 5 runes 네이티브
- Svelte 5, Vite 6, Tailwind 4
- 설치: `npm install layerchart@next`

## ChartSpec 프로토콜 (Python↔Svelte 공유 데이터 포맷)

```typescript
interface ChartSpec {
  chartType: "line" | "bar" | "combo" | "radar" | "waterfall" | "sparkline" | "heatmap";
  title?: string;
  series: Array<{
    name: string;
    data: number[];
    color?: string;
    type?: "bar" | "line";  // combo 차트용
  }>;
  categories: string[];      // x축 라벨 (기간)
  options?: {
    stacked?: boolean;
    secondaryY?: string[];   // 보조 Y축 시리즈 이름
    unit?: string;           // "백만원", "%", "배" 등
    maxValue?: number;       // radar용
  };
}
```

## 컴포넌트 아키텍처

### 파일 구조
```
src/dartlab/ui/src/lib/
├── chart/
│   ├── colors.js           # DartLab 컬러 팔레트 (chart.py에서 계승)
│   ├── ChartRenderer.svelte # ChartSpec → 차트 디스패처
│   ├── TrendChart.svelte    # bar+line 콤보 (재무 시계열)
│   ├── SparklineRow.svelte  # 인라인 미니 차트 (비율 테이블용)
│   ├── RadarChart.svelte    # 7축 레이더 (인사이트 등급)
│   ├── WaterfallChart.svelte# CF 분해
│   └── HeatmapChart.svelte  # diff 밀도 / sections 커버리지
```

### 컬러 팔레트 (`chart/colors.js`)
```javascript
// chart.py COLORS에서 계승
export const COLORS = [
  "#ea4647",  // primary red
  "#fb923c",  // accent orange
  "#3b82f6",  // blue
  "#22c55e",  // green
  "#8b5cf6",  // purple
  "#06b6d4",  // cyan
  "#f59e0b",  // amber
  "#ec4899",  // pink
];

// 다크 모드용 (기존 dl-* CSS 변수 연동)
export const CHART_THEME = {
  gridColor: "var(--dl-border, #e5e7eb)",
  textColor: "var(--dl-text, #374151)",
  bgColor: "var(--dl-bg, #ffffff)",
};
```

### ChartRenderer.svelte (디스패처)
```svelte
<script>
  let { spec } = $props();
</script>

{#if spec.chartType === "combo" || spec.chartType === "bar" || spec.chartType === "line"}
  <TrendChart {spec} />
{:else if spec.chartType === "radar"}
  <RadarChart {spec} />
{:else if spec.chartType === "waterfall"}
  <WaterfallChart {spec} />
{:else if spec.chartType === "sparkline"}
  <SparklineRow {spec} />
{:else if spec.chartType === "heatmap"}
  <HeatmapChart {spec} />
{/if}
```

### TrendChart.svelte (핵심 — 재무 시계열)
```svelte
<script>
  import { Chart, Svg, Bar, Line, Axis, Tooltip } from "layerchart";
  import { scaleBand, scaleLinear } from "d3-scale";
  import { COLORS } from "./colors.js";

  let { spec } = $props();

  // ChartSpec → LayerChart 데이터 변환
  let chartData = $derived(
    spec.categories.map((cat, i) => {
      const point = { category: cat };
      spec.series.forEach((s, si) => {
        point[s.name] = s.data[i];
      });
      return point;
    })
  );

  let barSeries = $derived(spec.series.filter(s => s.type !== "line"));
  let lineSeries = $derived(spec.series.filter(s => s.type === "line"));
</script>

<div class="w-full h-80">
  <Chart data={chartData} x="category" padding={{ left: 60, bottom: 40, right: 20, top: 20 }}>
    <Svg>
      <Axis placement="bottom" />
      <Axis placement="left" label={spec.options?.unit} />

      {#each barSeries as s, i}
        <Bar y={s.name} fill={s.color || COLORS[i]} />
      {/each}

      {#each lineSeries as s, i}
        <Line y={s.name} stroke={s.color || COLORS[barSeries.length + i]} strokeWidth={2} />
      {/each}
    </Svg>
    <Tooltip />
  </Chart>
</div>

{#if spec.title}
  <p class="text-center text-sm text-gray-500 mt-2">{spec.title}</p>
{/if}
```

### SparklineRow.svelte (인라인 비율 차트)
```svelte
<script>
  import { Chart, Svg, Line, Area } from "layerchart";
  import { COLORS } from "./colors.js";

  let { values = [], label = "", color = COLORS[2], width = 120, height = 32 } = $props();

  let data = $derived(values.map((v, i) => ({ x: i, y: v })).filter(d => d.y != null));
  let latest = $derived(values.filter(v => v != null).at(-1));
  let trend = $derived(() => {
    const valid = values.filter(v => v != null);
    if (valid.length < 2) return "neutral";
    return valid.at(-1) > valid.at(-2) ? "up" : "down";
  });
</script>

<div class="inline-flex items-center gap-2">
  <span class="text-xs text-gray-500 w-20 truncate">{label}</span>
  <div style:width="{width}px" style:height="{height}px">
    <Chart data={data} x="x" y="y" padding={{ top: 4, bottom: 4 }}>
      <Svg>
        <Area fill="{color}20" />
        <Line stroke={color} strokeWidth={1.5} />
      </Svg>
    </Chart>
  </div>
  <span class="text-xs font-mono w-16 text-right">
    {latest != null ? latest.toFixed(1) : "—"}
  </span>
</div>
```

### RadarChart.svelte (인사이트 등급)
```svelte
<script>
  import { Chart, Svg, Radar, RadarAxis } from "layerchart";
  import { COLORS } from "./colors.js";

  let { spec } = $props();

  let data = $derived(
    spec.categories.map((cat, i) => ({
      axis: cat,
      value: spec.series[0].data[i],
    }))
  );
</script>

<div class="w-full max-w-md mx-auto aspect-square">
  <Chart data={data} x="axis" y="value" yDomain={[0, spec.options?.maxValue || 5]}>
    <Svg>
      <RadarAxis />
      <Radar fill="{COLORS[0]}30" stroke={COLORS[0]} strokeWidth={2} />
    </Svg>
  </Chart>
</div>
```

## 통합 전략 (기존 컴포넌트와 연결)

### 1. TopicRenderer — 재무 topic 표/차트 토글

```svelte
<!-- TopicRenderer.svelte 내부, 재무 블록 영역 -->
{#if block.kind === "finance"}
  <div class="flex gap-2 mb-2">
    <button onclick={() => viewMode = "table"} class:active={viewMode === "table"}>표</button>
    <button onclick={() => viewMode = "chart"} class:active={viewMode === "chart"}>차트</button>
  </div>

  {#if viewMode === "table"}
    <TableRenderer {block} />
  {:else}
    <ChartRenderer spec={financeToChartSpec(block)} />
  {/if}
{/if}
```

**financeToChartSpec 변환 함수:**
```javascript
function financeToChartSpec(block) {
  const keyRows = ["매출액", "영업이익", "당기순이익"];
  const periods = block.meta.periods.slice(0, 8).reverse(); // 최신→과거 역전
  const series = keyRows
    .map(rowName => {
      const row = block.data.rows.find(r => r["계정명"] === rowName);
      if (!row) return null;
      return {
        name: rowName,
        data: periods.map(p => row[p] ?? null),
        type: rowName === "매출액" ? "bar" : "line",
      };
    })
    .filter(Boolean);

  return {
    chartType: "combo",
    series,
    categories: periods,
    options: { unit: block.meta.scale ? `${block.meta.scale}원` : "원" },
  };
}
```

### 2. InsightDashboard — 레이더 차트 추가

```svelte
<!-- InsightDashboard.svelte 상단에 레이더 추가 -->
{#if insightData?.grades}
  <RadarChart spec={{
    chartType: "radar",
    series: [{ name: "등급", data: Object.values(insightData.grades).map(gradeToNum) }],
    categories: Object.keys(insightData.grades),
    options: { maxValue: 5 },
  }} />
{/if}
```

### 3. 비율 테이블 — 스파크라인 행

```svelte
<!-- ratios DataFrame의 각 행에 스파크라인 추가 -->
{#each ratioRows as row}
  <tr>
    <td>{row.label}</td>
    <SparklineRow values={row.values} label={row.label} />
    <td>{row.latest}</td>
  </tr>
{/each}
```

## 서버 API 변경 (최소)

**새 엔드포인트 불필요** — 기존 `/viewer/{topic}` 응답의 `block.data`에서 ChartSpec을 프론트엔드가 직접 생성.

유일한 추가: `/api/company/{code}/insights` 응답에 이미 `grades` dict가 있으므로 RadarChart에 바로 사용.

## 다크 테마 연동

LayerChart는 SVG 기반이므로 CSS 변수로 직접 제어:
```css
:global(.dark) .chart-container {
  --chart-grid: #374151;
  --chart-text: #d1d5db;
  --chart-bg: #1f2937;
}
```

## 검증 계획

1. `npm install layerchart@next` → 빌드 통과 확인
2. 삼성전자 IS 데이터로 TrendChart 렌더링 → 스크린샷
3. 인사이트 등급으로 RadarChart 렌더링 → 스크린샷
4. `npm run build` 전후 번들 사이즈 비교
5. 다크 모드 전환 시 차트 테마 자동 적용 확인

## 결론

- LayerChart 2.0은 Svelte 5 $state/$derived와 자연스럽게 통합됨
- ChartSpec 프로토콜로 Python(chart.py) ↔ Server ↔ Svelte 3계층 데이터 흐름 통일
- 서버 API 변경 없이 프론트엔드만으로 Phase 2 전체 차트 구현 가능
- 기존 TopicRenderer/InsightDashboard에 토글/추가 방식으로 비파괴적 통합
