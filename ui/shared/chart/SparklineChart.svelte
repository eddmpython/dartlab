<script>
  /**
   * sparkline ChartSpec → CSS grid 스파크라인 배열.
   * spec_ratio_sparklines() 출력용.
   *
   * series 포맷: [{category: "수익성", metrics: [{field, values, latest, trend}, ...]}, ...]
   */
  import { scaleLinear } from 'd3-scale';
  import { COLORS } from './colors.js';

  let { spec } = $props();

  let groups = $derived(spec?.series || []);

  const SPARK_W = 80;
  const SPARK_H = 28;

  function sparkPath(values) {
    if (!values || values.length < 2) return '';
    const valid = values.filter((v) => v != null);
    if (valid.length < 2) return '';
    const yMin = Math.min(...valid);
    const yMax = Math.max(...valid);
    const yRange = yMax - yMin || 1;
    const xStep = SPARK_W / (values.length - 1);

    return values
      .map((v, i) => {
        if (v == null) return null;
        const x = i * xStep;
        const y = SPARK_H - ((v - yMin) / yRange) * (SPARK_H - 4) - 2;
        return `${x},${y}`;
      })
      .filter(Boolean)
      .map((pt, i) => `${i === 0 ? 'M' : 'L'}${pt}`)
      .join(' ');
  }

  function trendColor(trend) {
    if (trend === 'up') return '#22c55e';
    if (trend === 'down') return '#ef4444';
    return '#6b7280';
  }

  function formatLatest(v) {
    if (v == null) return '-';
    if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(0)}만`;
    if (Math.abs(v) >= 100) return v.toFixed(0);
    if (Math.abs(v) >= 1) return v.toFixed(1);
    return v.toFixed(2);
  }

  // field를 읽기 좋은 라벨로 변환 (camelCase → 공백)
  function fieldLabel(field) {
    return field
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (s) => s.toUpperCase())
      .trim();
  }
</script>

<div class="w-full">
  {#if spec?.title}
    <h4 class="text-sm font-medium text-zinc-300 mb-3">{spec.title}</h4>
  {/if}

  {#each groups as group, gi}
    <div class="mb-3">
      <div class="text-[11px] font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">{group.category}</div>
      <div class="grid gap-2" style="grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))">
        {#each group.metrics || [] as metric, mi}
          <div class="flex items-center gap-2 px-2 py-1.5 rounded-md bg-zinc-800/40 border border-zinc-700/30">
            <!-- Sparkline SVG -->
            <svg width={SPARK_W} height={SPARK_H} class="flex-shrink-0">
              <path
                d={sparkPath(metric.values)}
                fill="none"
                stroke={trendColor(metric.trend)}
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <!-- Latest point dot -->
              {#if metric.values?.length > 0}
                {@const lastVal = metric.values[metric.values.length - 1]}
                {@const valid = metric.values.filter((v) => v != null)}
                {@const yMin = Math.min(...valid)}
                {@const yMax = Math.max(...valid)}
                {@const yRange = yMax - yMin || 1}
                {#if lastVal != null}
                  <circle
                    cx={SPARK_W}
                    cy={SPARK_H - ((lastVal - yMin) / yRange) * (SPARK_H - 4) - 2}
                    r="2.5"
                    fill={trendColor(metric.trend)}
                  />
                {/if}
              {/if}
            </svg>
            <!-- Label + value -->
            <div class="flex flex-col min-w-0">
              <span class="text-[10px] text-zinc-500 truncate">{fieldLabel(metric.field)}</span>
              <span class="text-xs font-mono" style="color: {trendColor(metric.trend)}">
                {formatLatest(metric.latest)}
                {#if metric.trend === 'up'}↑{:else if metric.trend === 'down'}↓{/if}
              </span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/each}
</div>
