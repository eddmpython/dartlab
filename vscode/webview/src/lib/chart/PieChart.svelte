<script>
  /**
   * pie ChartSpec → SVG 도넛/파이 차트.
   * series[0].data = 값 배열, categories = 라벨.
   */
  import { COLORS } from './colors.js';

  let { spec } = $props();

  const SIZE = 240;
  const CX = SIZE / 2;
  const CY = SIZE / 2;
  const OUTER_R = 100;
  const INNER_R = 50; // donut

  let labels = $derived(spec?.categories || []);
  let values = $derived((spec?.series?.[0]?.data || []).map((v) => Math.max(0, v ?? 0)));
  let total = $derived(values.reduce((s, v) => s + v, 0) || 1);

  let slices = $derived.by(() => {
    const result = [];
    let startAngle = -Math.PI / 2;
    for (let i = 0; i < values.length; i++) {
      const ratio = values[i] / total;
      const angle = ratio * Math.PI * 2;
      const endAngle = startAngle + angle;
      const midAngle = startAngle + angle / 2;
      const color = spec?.series?.[0]?.colors?.[i] || COLORS[i % COLORS.length];

      // SVG arc path
      const largeArc = angle > Math.PI ? 1 : 0;
      const x1o = CX + OUTER_R * Math.cos(startAngle);
      const y1o = CY + OUTER_R * Math.sin(startAngle);
      const x2o = CX + OUTER_R * Math.cos(endAngle);
      const y2o = CY + OUTER_R * Math.sin(endAngle);
      const x1i = CX + INNER_R * Math.cos(endAngle);
      const y1i = CY + INNER_R * Math.sin(endAngle);
      const x2i = CX + INNER_R * Math.cos(startAngle);
      const y2i = CY + INNER_R * Math.sin(startAngle);

      const path = [
        `M${x1o},${y1o}`,
        `A${OUTER_R},${OUTER_R} 0 ${largeArc} 1 ${x2o},${y2o}`,
        `L${x1i},${y1i}`,
        `A${INNER_R},${INNER_R} 0 ${largeArc} 0 ${x2i},${y2i}`,
        'Z',
      ].join(' ');

      result.push({
        path,
        color,
        label: labels[i] || `#${i + 1}`,
        value: values[i],
        pct: (ratio * 100).toFixed(1),
        midAngle,
      });

      startAngle = endAngle;
    }
    return result;
  });

  let hoverIndex = $state(-1);

  function formatNum(v) {
    if (v == null) return '';
    if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(1)}억`;
    if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(0)}만`;
    return v.toLocaleString();
  }
</script>

<div class="w-full flex flex-col items-center">
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-2">{spec.title}</h4>
  {/if}

  <div class="flex items-start gap-4 flex-wrap justify-center">
    <!-- Pie SVG -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <svg width={SIZE} height={SIZE} viewBox="0 0 {SIZE} {SIZE}" class="flex-shrink-0">
      {#each slices as slice, i}
        <path
          d={slice.path}
          fill={slice.color}
          opacity={hoverIndex === -1 || hoverIndex === i ? 0.85 : 0.35}
          class="transition-opacity duration-150 cursor-pointer"
          onmouseenter={() => (hoverIndex = i)}
          onmouseleave={() => (hoverIndex = -1)}
        >
          <title>{slice.label}: {formatNum(slice.value)} ({slice.pct}%)</title>
        </path>
      {/each}

      <!-- Center text (hover) -->
      {#if hoverIndex >= 0}
        <text x={CX} y={CY - 6} text-anchor="middle" fill="#e5e7eb" font-size="11" font-weight="500">
          {slices[hoverIndex].label}
        </text>
        <text x={CX} y={CY + 10} text-anchor="middle" fill="#9ca3af" font-size="10">
          {slices[hoverIndex].pct}%
        </text>
      {/if}
    </svg>

    <!-- Legend -->
    <div class="flex flex-col gap-1 py-2">
      {#each slices as slice, i}
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="flex items-center gap-2 text-[11px] cursor-pointer"
          onmouseenter={() => (hoverIndex = i)}
          onmouseleave={() => (hoverIndex = -1)}
          class:opacity-40={hoverIndex !== -1 && hoverIndex !== i}
        >
          <span class="w-2.5 h-2.5 rounded-sm flex-shrink-0" style="background: {slice.color}"></span>
          <span class="text-zinc-300 truncate max-w-[120px]">{slice.label}</span>
          <span class="text-zinc-500 font-mono ml-auto">{slice.pct}%</span>
        </div>
      {/each}
    </div>
  </div>

  {#if spec?.options?.unit}
    <p class="text-[10px] text-zinc-500 mt-1">단위: {spec.options.unit}</p>
  {/if}
</div>
