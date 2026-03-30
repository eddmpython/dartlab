<script lang="ts">
  interface Props {
    serverState: string;
  }

  let { serverState }: Props = $props();
</script>

{#if serverState !== "ready"}
  <div class="header">
    {#if serverState === "starting"}
      <span class="status-text">Starting server...</span>
    {:else if serverState === "error"}
      <span class="status-text error">Server error</span>
    {:else}
      <span class="status-text">Connecting...</span>
    {/if}
  </div>
{/if}

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px 20px;
    border-bottom: 1px solid var(--vscode-panel-border);
    background: var(--vscode-editor-background);
  }
  .status-text {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
  }
  .status-text.error {
    color: var(--dl-primary, #ea4647);
  }
</style>
