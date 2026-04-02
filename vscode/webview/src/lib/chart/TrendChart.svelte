<script>
  /**
   * combo/bar/line ChartSpec → 반응형 인터랙티브 SVG 차트.
   * d3-scale 기반 렌더링 + 호버 툴팁 + 크로스헤어 + ResizeObserver 반응형.
   * 브러시 줌, 휠 줌, 범례 클릭 토글.
   */
  import { scaleLinear, scaleBand, scalePoint } from 'd3-scale';
  import { COLORS } from './colors.js';

  let { spec } = $props();

  // ── 반응형: ResizeObserver로 컨테이너 크기 추적 ──
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
  const MARGIN = { top: 32, right: 16, bottom: 40, left: 64 };
  let plotW = $derived(containerWidth - MARGIN.left - MARGIN.right);
  let plotH = $derived(HEIGHT - MARGIN.top - MARGIN.bottom);

  // ── 줌/브러시 상태 ──
  let zoomRange = $state(null); // { start, end } — category indices
  let brushStart = $state(null); // px
  let brushEnd = $state(null);   // px
  let isBrushing = $state(false);

  // ── 범례 토글 ──
  let hiddenSeries = $state(new Set());

  function toggleSeries(idx, e) {
    const newSet = new Set(hiddenSeries);
    if (e.shiftKey) {
      // Shift+클릭: 솔로 (이것만 보기 / 전체 보기)
      const allOthersHidden = allSeries.every((_, i) => i === idx || newSet.has(i));
      if (allOthersHidden) {
        newSet.clear(); // 전체 보기
      } else {
        newSet.clear();
        allSeries.forEach((_, i) => { if (i !== idx) newSet.add(i); });
      }
    } else {
      if (newSet.has(idx)) newSet.delete(idx);
      else if (newSet.size < allSeries.length - 1) newSet.add(idx); // 최소 1개 유지
    }
    hiddenSeries = newSet;
  }

  // ── 줌 적용된 카테고리/시리즈 ──
  let rawCategories = $derived(spec?.categories || []);
  let categories = $derived.by(() => {
    if (!zoomRange) return rawCategories;
    return rawCategories.slice(zoomRange.start, zoomRange.end + 1);
  });

  let allSeries = $derived(spec?.series || []);
  let visibleSeries = $derived(allSeries.filter((_, i) => !hiddenSeries.has(i)));

  let barSeries = $derived(visibleSeries.filter((s) => s.type === 'bar' || (!s.type && spec?.chartType !== 'line')));
  let lineSeries = $derived(visibleSeries.filter((s) => s.type === 'line' || (s.type == null && spec?.chartType === 'line')));

  // 줌 범위에 맞는 데이터만
  function sliceData(data) {
    if (!zoomRange) return data || [];
    return (data || []).slice(zoomRange.start, zoomRange.end + 1);
  }

  let allVals = $derived.by(() => {
    const vals = [];
    for (const s of visibleSeries) {
      for (const v of sliceData(s.data)) {
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
    const d = sliceData(data);
    return d
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

  // ── 호버 인터랙션 ──
  let hoverIndex = $state(-1);

  function getMouseX(e) {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    return e.clientX - rect.left - MARGIN.left;
  }

  function findClosestIndex(mouseX) {
    let minDist = Infinity;
    let closestIdx = -1;
    for (let i = 0; i < categories.length; i++) {
      const cx = xScale(categories[i]) + xScale.bandwidth() / 2;
      const dist = Math.abs(mouseX - cx);
      if (dist < minDist) {
        minDist = dist;
        closestIdx = i;
      }
    }
    return closestIdx;
  }

  function onMouseMove(e) {
    if (isBrushing) {
      brushEnd = getMouseX(e);
      return;
    }
    hoverIndex = findClosestIndex(getMouseX(e));
  }

  function onMouseLeave() {
    if (!isBrushing) hoverIndex = -1;
  }

  // ── 브러시 줌 ──
  function onPointerDown(e) {
    if (e.button !== 0) return;
    const mouseX = getMouseX(e);
    brushStart = mouseX;
    brushEnd = mouseX;
    isBrushing = true;
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e) {
    if (!isBrushing) {
      onMouseMove(e);
      return;
    }
    brushEnd = getMouseX(e);
  }

  function onPointerUp(e) {
    if (!isBrushing) return;
    isBrushing = false;
    e.currentTarget.releasePointerCapture(e.pointerId);

    const left = Math.min(brushStart, brushEnd);
    const right = Math.max(brushStart, brushEnd);
    // 최소 20px 드래그만 줌으로 인정
    if (right - left < 20) {
      brushStart = null;
      brushEnd = null;
      return;
    }

    const startIdx = findClosestIndex(left);
    const endIdx = findClosestIndex(right);
    if (startIdx >= 0 && endIdx >= 0 && startIdx !== endIdx) {
      const base = zoomRange?.start || 0;
      zoomRange = { start: base + startIdx, end: base + endIdx };
    }
    brushStart = null;
    brushEnd = null;
    hoverIndex = -1;
  }

  function resetZoom() {
    zoomRange = null;
  }

  function onDblClick() {
    resetZoom();
  }

  // ── 휠 줌 ──
  function onWheel(e) {
    e.preventDefault();
    const total = rawCategories.length;
    if (total <= 2) return;

    const cur = zoomRange || { start: 0, end: total - 1 };
    const delta = e.deltaY > 0 ? 1 : -1; // zoom out : zoom in
    const newStart = Math.max(0, cur.start + delta);
    const newEnd = Math.min(total - 1, cur.end - delta);
    if (newEnd - newStart < 1) return; // 최소 2개 카테고리
    if (newStart === 0 && newEnd === total - 1) {
      zoomRange = null;
    } else {
      zoomRange = { start: newStart, end: newEnd };
    }
  }

  let isZoomed = $derived(zoomRange != null);
</script>

<div class="w-full" bind:this={containerEl}>
  {#if spec?.title}
    <div class="flex items-center justify-between mb-2">
      <h4 class="text-sm font-medium text-zinc-300">{spec.title}</h4>
      {#if isZoomed}
        <button
          class="text-[10px] px-2 py-0.5 rounded-full bg-dl-accent/10 text-dl-accent border border-dl-accent/20 hover:bg-dl-accent/20 transition-colors"
          onclick={resetZoom}
        >
          줌 초기화
        </button>
      {/if}
    </div>
  {/if}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <svg
    viewBox="0 0 {containerWidth} {HEIGHT}"
    class="w-full h-auto select-none"
    onpointermove={onPointerMove}
    onpointerdown={onPointerDown}
    onpointerup={onPointerUp}
    onmouseleave={onMouseLeave}
    ondblclick={onDblClick}
    onwheel={onWheel}
    style="touch-action: none"
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
      {#if yMin < 0}
        <line x1="0" y1={yScale(0)} x2={plotW} y2={yScale(0)} stroke="#4b5563" stroke-width="1" />
      {/if}

      <!-- 브러시 선택 영역 -->
      {#if isBrushing && brushStart != null && brushEnd != null}
        {@const bLeft = Math.min(brushStart, brushEnd)}
        {@const bWidth = Math.abs(brushEnd - brushStart)}
        <rect
          x={bLeft}
          y={0}
          width={bWidth}
          height={plotH}
          fill="var(--color-dl-accent, #60a5fa)"
          opacity="0.12"
          rx="2"
        />
      {/if}

      <!-- 크로스헤어 (호버 시) -->
      {#if hoverIndex >= 0 && !isBrushing}
        {@const cx = xScale(categories[hoverIndex]) + xScale.bandwidth() / 2}
        <line x1={cx} y1={0} x2={cx} y2={plotH} stroke="#6b7280" stroke-width="1" stroke-dasharray="3,3" opacity="0.5" />
        <rect
          x={xScale(categories[hoverIndex]) - 2}
          y={0}
          width={xScale.bandwidth() + 4}
          height={plotH}
          fill="white"
          opacity="0.03"
          rx="2"
        />
      {/if}

      <!-- Bars -->
      {#each barSeries as s, si}
        {@const origIdx = allSeries.indexOf(s)}
        {#each sliceData(s.data) as v, i}
          {@const x = xScale(categories[i]) + si * barWidth}
          {@const y = v >= 0 ? yScale(v) : yScale(0)}
          {@const h = Math.abs(yScale(v) - yScale(0))}
          <rect
            {x}
            {y}
            width={barWidth - 2}
            height={h}
            fill={s.color || COLORS[origIdx]}
            rx="2"
            opacity={hoverIndex === -1 || hoverIndex === i ? 0.85 : 0.35}
            class="transition-opacity duration-150"
          />
        {/each}
      {/each}

      <!-- Lines -->
      {#each lineSeries as s, si}
        {@const origIdx = allSeries.indexOf(s)}
        <path d={linePath(s.data)} fill="none" stroke={s.color || COLORS[origIdx]} stroke-width="2" />
        {#each sliceData(s.data) as v, i}
          <circle
            cx={xPoint(categories[i])}
            cy={yScale(v ?? 0)}
            r={hoverIndex === i ? 5 : 3.5}
            fill={s.color || COLORS[origIdx]}
            stroke="#1a1e2a"
            stroke-width="1.5"
            class="transition-all duration-150"
          />
        {/each}
      {/each}

      <!-- X axis labels -->
      {#each categories as cat, i}
        <text
          x={xScale(cat) + xScale.bandwidth() / 2}
          y={plotH + 20}
          text-anchor="middle"
          fill={hoverIndex === i ? '#e5e7eb' : '#9ca3af'}
          font-size="11"
          font-weight={hoverIndex === i ? '600' : '400'}
          class="transition-all duration-150"
        >
          {cat}
        </text>
      {/each}
    </g>

    <!-- Legend (클릭 토글) -->
    <g transform="translate({MARGIN.left},{8})">
      {#each allSeries as s, i}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <g
          transform="translate({i * 100},0)"
          onclick={(e) => toggleSeries(i, e)}
          class="cursor-pointer"
          opacity={hiddenSeries.has(i) ? 0.3 : 1}
          role="button"
          tabindex="0"
          aria-label="{s.name} {hiddenSeries.has(i) ? '숨김' : '표시'}"
        >
          <rect width="12" height="3" fill={s.color || COLORS[i]} rx="1" y="-1" />
          <text x="16" y="0" dy="0.35em" fill={hiddenSeries.has(i) ? '#6b7280' : '#d1d5db'} font-size="10">{s.name}</text>
        </g>
      {/each}
    </g>
  </svg>

  <!-- 호버 툴팁 -->
  {#if hoverIndex >= 0 && !isBrushing}
    <div class="relative">
      <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-dl-bg-card/95 border border-dl-border/60 rounded-lg px-3 py-2 shadow-xl text-[11px] whitespace-nowrap z-10 animate-fadeIn pointer-events-none backdrop-blur-sm">
        <div class="font-medium text-dl-text mb-1">{categories[hoverIndex]}</div>
        {#each visibleSeries as s}
          {@const origIdx = allSeries.indexOf(s)}
          <div class="flex items-center gap-2 text-dl-text-muted">
            <span class="inline-block w-2 h-2 rounded-sm" style="background: {s.color || COLORS[origIdx]}"></span>
            <span>{s.name}</span>
            <span class="ml-auto font-mono text-dl-text">{formatNum(sliceData(s.data)[hoverIndex])}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if spec?.options?.unit}
    <p class="text-[10px] text-zinc-500 text-right mt-1">단위: {spec.options.unit}</p>
  {/if}
</div>
