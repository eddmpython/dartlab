<script>
  /**
   * ChartSpec JSON → 적절한 차트 컴포넌트로 dispatch.
   * ErrorBoundary로 감싸서 차트 렌더링 실패 시 crash 방지.
   * @type {{ spec: object, class?: string }}
   */
  import { ErrorBoundary } from "$lib/components/ui/error-boundary/index.js";

  let { spec, class: className = '' } = $props();
</script>

{#if spec}
  <div class="dl-chart-container {className}">
    <ErrorBoundary title="차트를 표시할 수 없습니다">
      {#if spec.chartType === 'combo' || spec.chartType === 'bar' || spec.chartType === 'line'}
        {#await import('./TrendChart.svelte') then { default: TrendChart }}
          <TrendChart {spec} />
        {/await}
      {:else if spec.chartType === 'radar'}
        {#await import('./RadarChart.svelte') then { default: RadarChart }}
          <RadarChart {spec} />
        {/await}
      {:else if spec.chartType === 'waterfall'}
        {#await import('./WaterfallChart.svelte') then { default: WaterfallChart }}
          <WaterfallChart {spec} />
        {/await}
      {:else if spec.chartType === 'heatmap'}
        {#await import('./HeatmapChart.svelte') then { default: HeatmapChart }}
          <HeatmapChart {spec} />
        {/await}
      {:else}
        <p class="text-sm text-zinc-500">지원하지 않는 차트 타입: {spec.chartType}</p>
      {/if}
    </ErrorBoundary>
  </div>
{/if}

<style>
  .dl-chart-container {
    width: 100%;
    min-height: 200px;
  }
</style>
