<script>
  /**
   * heatmap ChartSpec → SVG 히트맵 차트.
   * diff 밀도(1-row 객체배열) + 일반 matrix(숫자 2D) 양쪽 지원.
   */
  import { scaleBand, scaleLinear } from 'd3-scale';

  let { spec } = $props();

  const MARGIN = { top: 32, right: 16, bottom: 24, left: 120 };

  // ── 데이터 정규화: 두 포맷 모두 지원 ──
  // Format A (diff heatmap): series[0].data = [{topic, changeRate, intensity}, ...]
  // Format B (matrix): series = [{name, data: [num, num, ...]}, ...]

  let normalized = $derived.by(() => {
    const raw = spec?.series || [];
    if (!raw.length) return { rows: [], cols: [], matrix: [] };

    const first = raw[0];
    const firstData = first.data || [];

    // Format A: 객체 배열 (diff heatmap)
    if (firstData.length > 0 && typeof firstData[0] === 'object' && !Array.isArray(firstData[0]) && firstData[0] !== null) {
      const items = firstData;
      const cols = items.map((d) => d.topic || d.label || '');
      const vals = items.map((d) => {
        const v = d.changeRate ?? d.value ?? 0;
        return typeof v === 'number' ? v : parseFloat(v) || 0;
      });
      return {
        rows: [first.name || '변화율'],
        cols,
        matrix: [vals],
        intensities: items.map((d) => d.intensity),
      };
    }

    // Format B: 일반 matrix
    const cols = spec?.categories || [];
    const rows = raw.map((s) => s.name);
    const matrix = raw.map((s) => (s.data || []).map((v) => (typeof v === 'number' ? v : parseFloat(v) || 0)));
    return { rows, cols, matrix };
  });

  let { rows, cols, matrix } = $derived(normalized);

  let allVals = $derived.by(() => {
    const vals = [];
    for (const row of matrix) {
      for (const v of row) {
        if (v != null) vals.push(Math.abs(v));
      }
    }
    return vals;
  });

  let maxVal = $derived(Math.max(0.01, ...allVals));

  // 동적 크기
  let cellH = $derived(Math.max(24, Math.min(36, 240 / (rows.length || 1))));
  let cellW = $derived(Math.max(32, Math.min(80, 600 / (cols.length || 1))));
  let plotW = $derived(cellW * cols.length);
  let plotH = $derived(cellH * rows.length);
  let WIDTH = $derived(MARGIN.left + plotW + MARGIN.right);
  let HEIGHT = $derived(MARGIN.top + plotH + MARGIN.bottom);

  let xScale = $derived(scaleBand().domain(cols).range([0, plotW]).padding(0.05));
  let yScale = $derived(scaleBand().domain(rows).range([0, plotH]).padding(0.05));
  let colorScale = $derived(scaleLinear().domain([0, maxVal]).range([0, 1]));

  // colorScale 설정 (spec.options.colorScale 지원)
  function cellColor(v, intensity) {
    if (v == null) return '#1a1e2a';
    // intensity 기반 색상 (diff heatmap용)
    if (intensity) {
      const colorMap = spec?.options?.colorScale || {};
      if (intensity === 'high') return colorMap.high || '#ea4647';
      if (intensity === 'medium') return colorMap.medium || '#f59e0b';
      return colorMap.low || '#22c55e';
    }
    // 숫자 기반 그라디언트
    const t = colorScale(Math.abs(v));
    const r = Math.round(30 + t * 204);
    const g = Math.round(30 + t * (-30));
    const b = Math.round(42 + t * 29);
    return `rgb(${r},${g},${b})`;
  }

  function formatVal(v) {
    if (v == null) return '-';
    if (typeof v === 'number') {
      if (Math.abs(v) < 0.01) return '0';
      if (Math.abs(v) < 1) return (v * 100).toFixed(0) + '%';
      return v.toFixed(1);
    }
    return String(v);
  }
</script>

<div class="w-full overflow-x-auto">
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-2">{spec.title}</h4>
  {/if}
  <svg viewBox="0 0 {WIDTH} {HEIGHT}" class="w-full h-auto" style="min-width:{Math.min(WIDTH, 600)}px">
    <g transform="translate({MARGIN.left},{MARGIN.top})">
      <!-- Column headers -->
      {#each cols as cat}
        <text
          x={xScale(cat) + xScale.bandwidth() / 2}
          y="-6"
          text-anchor="middle"
          fill="#9ca3af"
          font-size="9"
          transform="rotate(-30, {xScale(cat) + xScale.bandwidth() / 2}, -6)"
        >
          {cat.length > 10 ? cat.slice(0, 9) + '…' : cat}
        </text>
      {/each}

      <!-- Row labels -->
      {#each rows as label}
        <text x="-8" y={yScale(label) + yScale.bandwidth() / 2} dy="0.35em" text-anchor="end" fill="#9ca3af" font-size="10">
          {label.length > 14 ? label.slice(0, 13) + '…' : label}
        </text>
      {/each}

      <!-- Cells -->
      {#each matrix as row, ri}
        {#each row as v, ci}
          {#if ci < cols.length}
            {@const intensity = normalized.intensities?.[ci]}
            <rect
              x={xScale(cols[ci])}
              y={yScale(rows[ri])}
              width={xScale.bandwidth()}
              height={yScale.bandwidth()}
              fill={cellColor(v, intensity)}
              rx="2"
              opacity="0.9"
            >
              <title>{rows[ri]} × {cols[ci]}: {formatVal(v)}</title>
            </rect>
            {#if v != null && xScale.bandwidth() > 24}
              <text
                x={xScale(cols[ci]) + xScale.bandwidth() / 2}
                y={yScale(rows[ri]) + yScale.bandwidth() / 2}
                dy="0.35em"
                text-anchor="middle"
                fill="#e5e7eb"
                font-size="9"
              >
                {formatVal(v)}
              </text>
            {/if}
          {/if}
        {/each}
      {/each}
    </g>
  </svg>
</div>
