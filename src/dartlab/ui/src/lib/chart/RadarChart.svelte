<script>
  /**
   * radar ChartSpec → SVG 7축 레이더 차트.
   * d3-scale 없이 순수 삼각함수로 극좌표 계산.
   */
  import { COLORS } from './colors.js';

  let { spec } = $props();

  const SIZE = 300;
  const CX = SIZE / 2;
  const CY = SIZE / 2;
  const R = 110;
  const LEVELS = 5;

  let series = $derived(spec?.series || []);
  let categories = $derived(spec?.categories || []);
  let maxVal = $derived(spec?.options?.maxValue || 5);
  let n = $derived(categories.length || 1);

  function angle(i) {
    return (Math.PI * 2 * i) / n - Math.PI / 2;
  }

  function pt(i, val) {
    const a = angle(i);
    const r = (val / maxVal) * R;
    return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
  }

  function polygonPoints(data) {
    return data.map((v, i) => pt(i, v ?? 0).join(',')).join(' ');
  }

  function levelPoints(level) {
    const r = (level / LEVELS) * R;
    return Array.from({ length: n }, (_, i) => {
      const a = angle(i);
      return `${CX + r * Math.cos(a)},${CY + r * Math.sin(a)}`;
    }).join(' ');
  }

  function labelPos(i) {
    const a = angle(i);
    const pad = 18;
    return [CX + (R + pad) * Math.cos(a), CY + (R + pad) * Math.sin(a)];
  }
</script>

<div class="w-full">
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-2">{spec.title}</h4>
  {/if}
  <svg viewBox="0 0 {SIZE} {SIZE}" class="w-full h-auto max-w-[320px] mx-auto">
    <!-- Grid levels -->
    {#each Array.from({ length: LEVELS }, (_, i) => i + 1) as level}
      <polygon points={levelPoints(level)} fill="none" stroke="#2a2e3a" stroke-width="1" />
    {/each}

    <!-- Axis lines -->
    {#each categories as _, i}
      <line x1={CX} y1={CY} x2={pt(i, maxVal)[0]} y2={pt(i, maxVal)[1]} stroke="#2a2e3a" stroke-width="1" />
    {/each}

    <!-- Data polygons -->
    {#each series as s, si}
      <polygon points={polygonPoints(s.data)} fill={s.color || COLORS[si]} fill-opacity="0.2"
        stroke={s.color || COLORS[si]} stroke-width="2" />
      {#each s.data as v, i}
        {@const p = pt(i, v ?? 0)}
        <circle cx={p[0]} cy={p[1]} r="3.5" fill={s.color || COLORS[si]} stroke="#1a1e2a" stroke-width="1.5">
          <title>{categories[i]}: {v}</title>
        </circle>
      {/each}
    {/each}

    <!-- Labels -->
    {#each categories as cat, i}
      {@const lp = labelPos(i)}
      <text x={lp[0]} y={lp[1]} text-anchor="middle" dominant-baseline="central"
        fill="#9ca3af" font-size="11">{cat}</text>
    {/each}
  </svg>
</div>
