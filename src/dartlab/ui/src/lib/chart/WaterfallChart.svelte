<script>
  /**
   * waterfall ChartSpec → 반응형 인터랙티브 SVG 워터폴 차트.
   * 현금흐름 브릿지 등에 사용. ResizeObserver 반응형 + 호버 하이라이트.
   */
  import { scaleLinear, scaleBand } from 'd3-scale';
  import { COLORS } from './colors.js';

  let { spec } = $props();

  // ── 반응형 ──
  let containerEl = $state(null);
  let containerWidth = $state(480);

  $effect(() => {
    if (!containerEl) return;
    const ro = new ResizeObserver(([entry]) => {
      containerWidth = entry.contentRect.width;
    });
    ro.observe(containerEl);
    return () => ro.disconnect();
  });

  const HEIGHT = 280;
  const MARGIN = { top: 32, right: 16, bottom: 56, left: 72 };
  let plotW = $derived(containerWidth - MARGIN.left - MARGIN.right);
  let plotH = $derived(HEIGHT - MARGIN.top - MARGIN.bottom);

  let series = $derived(spec?.series?.[0] || { data: [], name: '' });
  let categories = $derived(spec?.categories || []);
  let data = $derived(series.data || []);

  // 누적값 계산
  let bars = $derived.by(() => {
    const result = [];
    let running = 0;
    for (let i = 0; i < data.length; i++) {
      const v = data[i] ?? 0;
      const isTotal = i === 0 || i === data.length - 1;
      if (isTotal) {
        result.push({ start: 0, end: v, value: v, isTotal: true });
        running = v;
      } else {
        result.push({ start: running, end: running + v, value: v, isTotal: false });
        running += v;
      }
    }
    return result;
  });

  let allEnds = $derived(bars.flatMap((b) => [b.start, b.end]));
  let yMin = $derived(Math.min(0, ...allEnds));
  let yMax = $derived(Math.max(0, ...allEnds));
  let yPad = $derived((yMax - yMin) * 0.1 || 1);

  let xScale = $derived(scaleBand().domain(categories).range([0, plotW]).padding(0.25));
  let yScale = $derived(scaleLinear().domain([yMin - yPad, yMax + yPad]).range([plotH, 0]).nice());

  function barColor(bar) {
    if (bar.isTotal) return '#6b7280';
    return bar.value >= 0 ? COLORS[2] : COLORS[0];
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

  // ── 호버 ──
  let hoverIndex = $state(-1);

  function onMouseMove(e) {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const mouseX = e.clientX - rect.left - MARGIN.left;
    let minDist = Infinity;
    let closestIdx = -1;
    for (let i = 0; i < categories.length; i++) {
      const cx = xScale(categories[i]) + xScale.bandwidth() / 2;
      const dist = Math.abs(mouseX - cx);
      if (dist < minDist) { minDist = dist; closestIdx = i; }
    }
    hoverIndex = closestIdx;
  }

  function onMouseLeave() { hoverIndex = -1; }
</script>

<div class="w-full" bind:this={containerEl}>
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-2">{spec.title}</h4>
  {/if}
  <svg
    viewBox="0 0 {containerWidth} {HEIGHT}"
    class="w-full h-auto"
    onmousemove={onMouseMove}
    onmouseleave={onMouseLeave}
  >
    <g transform="translate({MARGIN.left},{MARGIN.top})">
      <!-- Grid -->
      {#each yTicks as tick}
        <line x1="0" y1={yScale(tick)} x2={plotW} y2={yScale(tick)} stroke="#2a2e3a" stroke-width="1" />
        <text x="-8" y={yScale(tick)} dy="0.35em" text-anchor="end" fill="#6b7280" font-size="10">
          {formatNum(tick)}
        </text>
      {/each}

      <!-- Zero line -->
      <line x1="0" y1={yScale(0)} x2={plotW} y2={yScale(0)} stroke="#4b5563" stroke-width="1" />

      <!-- 크로스헤어 -->
      {#if hoverIndex >= 0}
        {@const cx = xScale(categories[hoverIndex]) + xScale.bandwidth() / 2}
        <line x1={cx} y1={0} x2={cx} y2={plotH} stroke="#6b7280" stroke-width="1" stroke-dasharray="3,3" opacity="0.5" />
      {/if}

      <!-- Bars + connectors -->
      {#each bars as bar, i}
        {@const x = xScale(categories[i])}
        {@const top = Math.min(yScale(bar.start), yScale(bar.end))}
        {@const h = Math.abs(yScale(bar.start) - yScale(bar.end))}
        <rect
          {x}
          y={top}
          width={xScale.bandwidth()}
          height={Math.max(h, 1)}
          fill={barColor(bar)}
          rx="2"
          opacity={hoverIndex === -1 || hoverIndex === i ? 0.85 : 0.35}
          class="transition-opacity duration-150"
        />

        <!-- Value label -->
        <text
          x={x + xScale.bandwidth() / 2}
          y={top - 4}
          text-anchor="middle"
          fill={hoverIndex === i ? '#f1f5f9' : '#d1d5db'}
          font-size="9"
          font-weight={hoverIndex === i ? '600' : '400'}
        >
          {bar.value >= 0 ? '+' : ''}{formatNum(bar.value)}
        </text>

        <!-- Connector to next bar -->
        {#if i < bars.length - 1 && !bar.isTotal}
          <line x1={x + xScale.bandwidth()} y1={yScale(bar.end)} x2={xScale(categories[i + 1])}
            y2={yScale(bar.end)} stroke="#4b5563" stroke-width="1" stroke-dasharray="3,2" />
        {/if}
      {/each}

      <!-- X axis labels -->
      {#each categories as cat, i}
        <text
          x={xScale(cat) + xScale.bandwidth() / 2}
          y={plotH + 16}
          text-anchor="middle"
          fill={hoverIndex === i ? '#e5e7eb' : '#9ca3af'}
          font-size="10"
          font-weight={hoverIndex === i ? '600' : '400'}
        >
          {cat}
        </text>
      {/each}
    </g>
  </svg>

  <!-- 호버 툴팁 -->
  {#if hoverIndex >= 0}
    <div class="relative">
      <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-dl-bg-card/95 border border-dl-border/60 rounded-lg px-3 py-2 shadow-xl text-[11px] whitespace-nowrap z-10 animate-fadeIn pointer-events-none backdrop-blur-sm">
        <div class="font-medium text-dl-text mb-1">{categories[hoverIndex]}</div>
        <div class="flex items-center gap-2 text-dl-text-muted">
          <span class="inline-block w-2 h-2 rounded-sm" style="background: {barColor(bars[hoverIndex])}"></span>
          <span>{bars[hoverIndex].isTotal ? '합계' : series.name || '변동'}</span>
          <span class="ml-auto font-mono text-dl-text">
            {bars[hoverIndex].value >= 0 ? '+' : ''}{formatNum(bars[hoverIndex].value)}
          </span>
        </div>
      </div>
    </div>
  {/if}

  {#if spec?.options?.unit}
    <p class="text-[10px] text-zinc-500 text-right mt-1">단위: {spec.options.unit}</p>
  {/if}
</div>
