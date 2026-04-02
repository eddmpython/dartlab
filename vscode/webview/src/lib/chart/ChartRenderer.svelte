<script>
  /**
   * ChartSpec JSON → 적절한 차트 컴포넌트로 dispatch.
   * VSCode webview 전용 — ErrorBoundary 없이 try-catch fallback.
   * @type {{ spec: object, class?: string }}
   */
  let { spec, class: className = '' } = $props();
</script>

{#if spec}
  <div class="dl-chart-container {className}">
    {#if spec.vizType === 'diagram' && spec.diagramType === 'mermaid'}
      <pre class="mermaid-source">{spec.source}</pre>
    {:else if spec.chartType === 'combo' || spec.chartType === 'bar' || spec.chartType === 'line'}
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
      <p class="chart-unsupported">지원하지 않는 차트 타입: {spec.chartType ?? spec.vizType}</p>
    {/if}
  </div>
{/if}

<style>
  .dl-chart-container {
    width: 100%;
    min-height: 200px;
    margin: 8px 0;
  }
  .chart-unsupported {
    font-size: 12px;
    color: var(--vscode-descriptionForeground, #888);
  }
  .mermaid-source {
    font-size: 11px;
    padding: 8px;
    background: var(--vscode-editor-background, #1e1e1e);
    border-radius: 4px;
    overflow-x: auto;
  }
</style>
