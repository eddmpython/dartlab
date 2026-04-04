<script lang="ts">
  interface Props {
    providerLabel?: string;
    modelLabel?: string;
    contextPercent?: number;
    streaming?: boolean;
    elapsed?: number;
    tokenEstimate?: number;
  }

  let {
    providerLabel = "",
    modelLabel = "",
    contextPercent = 0,
    streaming = false,
    elapsed = 0,
    tokenEstimate = 0,
  }: Props = $props();

  function formatTokens(n: number): string {
    if (n < 1000) return `${n}`;
    return `${(n / 1000).toFixed(1)}k`;
  }
</script>

<div class="status-line">
  <div class="status-left">
    {#if providerLabel && providerLabel !== "none"}
      <span class="status-model">{providerLabel}{#if modelLabel} / {modelLabel}{/if}</span>
    {/if}
  </div>

  <div class="status-center">
    {#if contextPercent > 0}
      <div class="ctx-gauge" title="Context {contextPercent}%">
        <div
          class="ctx-bar"
          class:warn={contextPercent >= 50 && contextPercent < 80}
          class:danger={contextPercent >= 80}
          style="width: {Math.min(contextPercent, 100)}%"
        ></div>
      </div>
      <span class="ctx-pct">{contextPercent}%</span>
    {/if}
  </div>

  <div class="status-right">
    {#if streaming && elapsed > 0}
      <span class="status-duration">{elapsed}s</span>
    {/if}
    {#if tokenEstimate > 0}
      <span class="status-tokens">~{formatTokens(tokenEstimate)} tok</span>
    {/if}
  </div>
</div>

<style>
  .status-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 22px;
    padding: 0 12px;
    border-top: 1px solid var(--vscode-panel-border);
    background: var(--vscode-statusBar-background, var(--vscode-editor-background));
    color: var(--vscode-statusBar-foreground, var(--vscode-descriptionForeground));
    font-size: 11px;
    flex-shrink: 0;
    z-index: 30;
  }
  .status-left, .status-right {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .status-center {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .status-model {
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 10px;
    opacity: 0.7;
  }
  .ctx-gauge {
    width: 60px;
    height: 4px;
    border-radius: 2px;
    background: rgba(128,128,128,0.2);
    overflow: hidden;
  }
  .ctx-bar {
    height: 100%;
    background: #34d399;
    transition: width 0.3s;
  }
  .ctx-bar.warn { background: #fbbf24; }
  .ctx-bar.danger { background: var(--dl-primary, #ea4647); }
  .ctx-pct {
    font-size: 10px;
    opacity: 0.6;
    font-family: var(--vscode-editor-font-family, monospace);
  }
  .status-duration {
    font-family: var(--vscode-editor-font-family, monospace);
    opacity: 0.7;
  }
  .status-tokens {
    font-family: var(--vscode-editor-font-family, monospace);
    opacity: 0.5;
  }
</style>
