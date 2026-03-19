<script>
  /**
   * heatmap ChartSpec → SVG 히트맵 차트.
   * diff 밀도, 섹터별 비교 등에 사용.
   */
  import { scaleBand, scaleLinear } from 'd3-scale';

  let { spec } = $props();

  const MARGIN = { top: 32, right: 16, bottom: 24, left: 120 };

  let series = $derived(spec?.series || []);
  let categories = $derived(spec?.categories || []);
  let rowLabels = $derived(series.map((s) => s.name));

  let allVals = $derived.by(() => {
    const vals = [];
    for (const s of series) {
      for (const v of s.data || []) {
        if (v != null) vals.push(Math.abs(v));
      }
    }
    return vals;
  });

  let maxVal = $derived(Math.max(1, ...allVals));

  // 동적 크기
  let cellH = $derived(Math.max(20, Math.min(32, 240 / (rowLabels.length || 1))));
  let cellW = $derived(Math.max(28, Math.min(60, 400 / (categories.length || 1))));
  let plotW = $derived(cellW * categories.length);
  let plotH = $derived(cellH * rowLabels.length);
  let WIDTH = $derived(MARGIN.left + plotW + MARGIN.right);
  let HEIGHT = $derived(MARGIN.top + plotH + MARGIN.bottom);

  let xScale = $derived(scaleBand().domain(categories).range([0, plotW]).padding(0.05));
  let yScale = $derived(scaleBand().domain(rowLabels).range([0, plotH]).padding(0.05));
  let colorScale = $derived(scaleLinear().domain([0, maxVal]).range([0, 1]));

  function cellColor(v) {
    if (v == null) return '#1a1e2a';
    const t = colorScale(Math.abs(v));
    // blue → red gradient
    const r = Math.round(30 + t * 204);
    const g = Math.round(30 + t * (-30));
    const b = Math.round(42 + t * (29));
    return `rgb(${r},${g},${b})`;
  }
</script>

<div class="w-full overflow-x-auto">
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-2">{spec.title}</h4>
  {/if}
  <svg viewBox="0 0 {WIDTH} {HEIGHT}" class="w-full h-auto" style="min-width:{WIDTH}px">
    <g transform="translate({MARGIN.left},{MARGIN.top})">
      <!-- Column headers -->
      {#each categories as cat}
        <text x={xScale(cat) + xScale.bandwidth() / 2} y="-6" text-anchor="middle" fill="#9ca3af" font-size="10">
          {cat}
        </text>
      {/each}

      <!-- Row labels -->
      {#each rowLabels as label}
        <text x="-8" y={yScale(label) + yScale.bandwidth() / 2} dy="0.35em" text-anchor="end" fill="#9ca3af" font-size="10">
          {label.length > 14 ? label.slice(0, 13) + '…' : label}
        </text>
      {/each}

      <!-- Cells -->
      {#each series as s, si}
        {#each s.data as v, ci}
          {#if ci < categories.length}
            <rect x={xScale(categories[ci])} y={yScale(s.name)} width={xScale.bandwidth()} height={yScale.bandwidth()}
              fill={cellColor(v)} rx="2" opacity="0.9">
              <title>{s.name} × {categories[ci]}: {v ?? '-'}</title>
            </rect>
            {#if v != null}
              <text x={xScale(categories[ci]) + xScale.bandwidth() / 2} y={yScale(s.name) + yScale.bandwidth() / 2}
                dy="0.35em" text-anchor="middle" fill="#e5e7eb" font-size="9">
                {typeof v === 'number' ? v.toFixed(1) : v}
              </text>
            {/if}
          {/if}
        {/each}
      {/each}
    </g>
  </svg>
</div>
