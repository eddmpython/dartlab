<script lang="ts">
  import * as client from "../api/client";

  interface ProviderInfo {
    id: string;
    label: string;
    description?: string;
    freeTier: string;
    authKind?: string;
    signupUrl?: string;
  }

  interface Props {
    serverState: string;
    providerLabel?: string;
    modelLabel?: string;
    providers?: ProviderInfo[];
  }

  let { serverState, providerLabel = "", modelLabel = "", providers = [] }: Props = $props();
  let showDropdown = $state(false);

  function selectProvider(p: ProviderInfo) {
    if (p.authKind === "api_key") {
      client.requestCredential(p.id, p.signupUrl);
    } else {
      client.setProvider(p.id);
    }
    showDropdown = false;
  }

  function toggleDropdown() {
    showDropdown = !showDropdown;
  }

  function handleClickOutside(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest(".provider-area")) {
      showDropdown = false;
    }
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="header" onclick={handleClickOutside}>
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
    <div class="provider-area">
      <button class="provider-btn" onclick={toggleDropdown}>
        {#if providerLabel && providerLabel !== "none"}
          {providerLabel}{#if modelLabel} / {modelLabel}{/if}
        {:else}
          프로바이더 선택
        {/if}
        <svg class="chevron" class:open={showDropdown} width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M4 6l4 4 4-4"/></svg>
      </button>

      {#if showDropdown && providers.length > 0}
        <div class="dropdown">
          {#each providers as p}
            <button
              class="dropdown-item"
              class:active={p.id === providerLabel}
              onclick={() => selectProvider(p)}
            >
              <span class="item-label">{p.label}</span>
              {#if p.freeTier}
                <span class="item-free">{p.freeTier}</span>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </div>
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

  /* Provider dropdown */
  .provider-area {
    position: relative;
  }
  .provider-btn {
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 3px;
    border: none;
    background: var(--vscode-badge-background);
    color: var(--vscode-badge-foreground);
    cursor: pointer;
  }
  .provider-btn:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .chevron {
    transition: transform 0.15s;
    opacity: 0.6;
  }
  .chevron.open {
    transform: rotate(180deg);
  }
  .dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 4px;
    min-width: 200px;
    max-height: 300px;
    overflow-y: auto;
    background: var(--vscode-menu-background, var(--vscode-editorWidget-background));
    border: 1px solid var(--vscode-menu-border, var(--vscode-panel-border));
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,.3);
    z-index: 100;
    padding: 4px 0;
  }
  .dropdown-item {
    display: flex;
    flex-direction: column;
    gap: 1px;
    width: 100%;
    padding: 6px 10px;
    border: none;
    background: transparent;
    color: var(--vscode-foreground);
    font: inherit;
    font-size: 12px;
    cursor: pointer;
    text-align: left;
  }
  .dropdown-item:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .dropdown-item.active {
    background: var(--vscode-list-activeSelectionBackground);
    color: var(--vscode-list-activeSelectionForeground);
  }
  .item-label {
    font-weight: 500;
  }
  .item-free {
    font-size: 10px;
    color: #34d399;
  }

</style>
