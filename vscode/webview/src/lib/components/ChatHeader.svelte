<script lang="ts">
  interface Props {
    serverState: string;
    providerLabel?: string;
    modelLabel?: string;
  }

  let { serverState, providerLabel = "", modelLabel = "" }: Props = $props();
</script>

<div class="header">
  <div class="header-left">
    {#if serverState === "starting"}
      <div class="status-dot starting"></div>
      <span class="status-text">Starting...</span>
    {:else if serverState === "error"}
      <div class="status-dot error"></div>
      <span class="status-text error">Error</span>
    {:else if serverState === "stopped"}
      <div class="status-dot stopped"></div>
      <span class="status-text">Stopped</span>
    {:else if serverState === "ready"}
      <div class="status-dot ready"></div>
      <span class="status-text">Ready</span>
    {:else}
      <span class="status-text">Connecting...</span>
    {/if}
  </div>
  <div class="header-right">
    {#if providerLabel}
      <span class="provider-badge">{providerLabel}{#if modelLabel} / {modelLabel}{/if}</span>
    {/if}
    <span class="mcp-badge">MCP</span>
  </div>
</div>

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 12px;
    border-bottom: 1px solid var(--vscode-panel-border);
    min-height: 28px;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--vscode-descriptionForeground);
  }
  .status-dot.starting {
    background: #fbbf24;
    animation: pulse 1.5s infinite;
  }
  .status-dot.ready { background: #34d399; }
  .status-dot.error { background: var(--dl-primary, #ea4647); }
  .status-dot.stopped { opacity: 0.4; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  .status-text {
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
  }
  .status-text.error { color: var(--dl-primary); }
  .provider-badge {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 3px;
    background: var(--vscode-badge-background);
    color: var(--vscode-badge-foreground);
  }
  .mcp-badge {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 3px;
    background: color-mix(in srgb, #34d399 15%, transparent);
    color: #34d399;
    font-weight: 600;
  }
</style>
