<script>
  /**
   * combo/bar/line ChartSpec → SVG bar+line 차트.
   * LayerChart의 Chart + Axis + Bars/Spline 사용.
   */
  import { scaleLinear, scaleBand, scalePoint } from 'd3-scale';
  import { COLORS } from './colors.js';

  let { spec } = $props();

  const WIDTH = 560;
  const HEIGHT = 280;
  const MARGIN = { top: 32, right: 16, bottom: 40, left: 64 };
  const plotW = WIDTH - MARGIN.left - MARGIN.right;
  const plotH = HEIGHT - MARGIN.top - MARGIN.bottom;

  let barSeries = $derived((spec?.series || []).filter((s) => s.type === 'bar' || (!s.type && spec?.chartType !== 'line')));
  let lineSeries = $derived((spec?.series || []).filter((s) => s.type === 'line' || (s.type == null && spec?.chartType === 'line')));
  let categories = $derived(spec?.categories || []);

  let allVals = $derived.by(() => {
    const vals = [];
    for (const s of spec?.series || []) {
      for (const v of s.data || []) {
        if (v != null) vals.push(v);
      }
    }
    return vals;
  });

  let yMin = $derived(Math.min(0, ...allVals));
  let yMax = $derived(Math.max(0, ...allVals));
  let yPad = $derived((yMax - yMin) * 0.1 || 1);

  let xScale = $derived(scaleBand().domain(categories).range([0, plotW]).padding(0.3));
  let xPoint = $derived(scalePoint().domain(categories).range([0, plotW]).padding(0.5));
  let yScale = $derived(scaleLinear().domain([yMin - yPad, yMax + yPad]).range([plotH, 0]).nice());

  let barWidth = $derived.by(() => {
    const bw = xScale.bandwidth();
    const n = barSeries.length || 1;
    return bw / n;
  });

  function linePath(data) {
    return data
      .map((v, i) => {
        const x = xPoint(categories[i]);
        const y = yScale(v ?? 0);
        return `${i === 0 ? 'M' : 'L'}${x},${y}`;
      })
      .join(' ');
  }

  function formatNum(v) {
    if (v == null) return '';
    if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(1)}억`;
    if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(0)}만`;
    return v.toLocaleString();
  }

  let yTicks = $derived.by(() => {
    const domain = yScale.domain();
    return yScale.ticks(5).filter((t) => t >= domain[0] && t <= domain[1]);
  });
</script>

<div class="w-full">
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-2">{spec.title}</h4>
  {/if}
  <svg viewBox="0 0 {WIDTH} {HEIGHT}" class="w-full h-auto">
    <g transform="translate({MARGIN.left},{MARGIN.top})">
      <!-- Grid -->
      {#each yTicks as tick}
        <line x1="0" y1={yScale(tick)} x2={plotW} y2={yScale(tick)} stroke="#2a2e3a" stroke-width="1" />
        <text x="-8" y={yScale(tick)} dy="0.35em" text-anchor="end" fill="#6b7280" font-size="10">
          {formatNum(tick)}
        </text>
      {/each}

      <!-- Zero line -->
      {#if yMin < 0}
        <line x1="0" y1={yScale(0)} x2={plotW} y2={yScale(0)} stroke="#4b5563" stroke-width="1" />
      {/if}

      <!-- Bars -->
      {#each barSeries as s, si}
        {#each s.data as v, i}
          {@const x = xScale(categories[i]) + si * barWidth}
          {@const y = v >= 0 ? yScale(v) : yScale(0)}
          {@const h = Math.abs(yScale(v) - yScale(0))}
          <rect {x} {y} width={barWidth - 2} height={h} fill={s.color || COLORS[si]} rx="2" opacity="0.85">
            <title>{s.name}: {v?.toLocaleString()}</title>
          </rect>
        {/each}
      {/each}

      <!-- Lines -->
      {#each lineSeries as s, si}
        <path d={linePath(s.data)} fill="none" stroke={s.color || COLORS[si + barSeries.length]} stroke-width="2" />
        {#each s.data as v, i}
          <circle cx={xPoint(categories[i])} cy={yScale(v ?? 0)} r="3.5"
            fill={s.color || COLORS[si + barSeries.length]} stroke="#1a1e2a" stroke-width="1.5">
            <title>{s.name}: {v?.toLocaleString()}</title>
          </circle>
        {/each}
      {/each}

      <!-- X axis labels -->
      {#each categories as cat, i}
        <text x={xScale(cat) + xScale.bandwidth() / 2} y={plotH + 20} text-anchor="middle" fill="#9ca3af" font-size="11">
          {cat}
        </text>
      {/each}
    </g>

    <!-- Legend -->
    <g transform="translate({MARGIN.left},{8})">
      {#each (spec?.series || []) as s, i}
        <g transform="translate({i * 100},0)">
          <rect width="12" height="3" fill={s.color || COLORS[i]} rx="1" y="-1" />
          <text x="16" y="0" dy="0.35em" fill="#d1d5db" font-size="10">{s.name}</text>
        </g>
      {/each}
    </g>
  </svg>
  {#if spec?.options?.unit}
    <p class="text-[10px] text-zinc-500 text-right mt-1">단위: {spec.options.unit}</p>
  {/if}
</div>
