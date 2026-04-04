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

  interface ConversationInfo {
    id: string;
    title: string;
    createdAt: number;
    updatedAt: number;
    messageCount: number;
  }

  interface Props {
    serverState: string;
    providerLabel?: string;
    modelLabel?: string;
    providers?: ProviderInfo[];
    conversations?: ConversationInfo[];
    activeConversationId?: string | null;
    onSelectConversation?: (id: string) => void;
    onNewConversation?: () => void;
    onDeleteConversation?: (id: string) => void;
    onRenameConversation?: (id: string, title: string) => void;
  }

  let {
    serverState,
    providerLabel = "",
    modelLabel = "",
    providers = [],
    conversations = [],
    activeConversationId = null,
    onSelectConversation,
    onNewConversation,
    onDeleteConversation,
    onRenameConversation,
  }: Props = $props();

  let showProviderDropdown = $state(false);
  let showSessionDropdown = $state(false);
  let sessionSearch = $state("");
  let editingId = $state<string | null>(null);
  let editingTitle = $state("");

  // Active conversation title
  let activeTitle = $derived(
    conversations.find(c => c.id === activeConversationId)?.title ?? "New conversation"
  );

  // Time grouping
  function timeGroup(ts: number): string {
    const now = Date.now();
    const diff = now - ts;
    const day = 86400000;
    if (diff < day) return "Today";
    if (diff < 2 * day) return "Yesterday";
    if (diff < 7 * day) return "Last 7 days";
    return "Older";
  }

  // Filter + group conversations
  let groupedConversations = $derived(() => {
    const q = sessionSearch.toLowerCase();
    const filtered = q
      ? conversations.filter(c => c.title.toLowerCase().includes(q))
      : conversations;

    const groups: Record<string, ConversationInfo[]> = {};
    for (const c of filtered) {
      const g = timeGroup(c.updatedAt);
      (groups[g] ??= []).push(c);
    }
    // Preserve order
    const order = ["Today", "Yesterday", "Last 7 days", "Older"];
    return order.filter(g => groups[g]?.length).map(g => ({ label: g, items: groups[g] }));
  });

  function selectProvider(p: ProviderInfo) {
    if (p.authKind === "api_key") {
      client.requestCredential(p.id, p.signupUrl);
    } else {
      client.setProvider(p.id);
    }
    showProviderDropdown = false;
  }

  function selectSession(id: string) {
    showSessionDropdown = false;
    sessionSearch = "";
    onSelectConversation?.(id);
  }

  function startRename(c: ConversationInfo) {
    editingId = c.id;
    editingTitle = c.title;
  }

  function commitRename() {
    if (editingId && editingTitle.trim()) {
      onRenameConversation?.(editingId, editingTitle.trim());
    }
    editingId = null;
    editingTitle = "";
  }

  function handleRenameKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") { e.preventDefault(); commitRename(); }
    if (e.key === "Escape") { editingId = null; }
  }

  function handleClickOutside(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest(".provider-area")) showProviderDropdown = false;
    if (!target.closest(".session-area")) { showSessionDropdown = false; sessionSearch = ""; }
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
    {:else}
      <span class="status-text">Connecting...</span>
    {/if}

    <!-- Session dropdown (Claude Code pattern: past conversations) -->
    <div class="session-area">
      <button class="session-btn" onclick={() => showSessionDropdown = !showSessionDropdown}>
        <span class="session-title">{activeTitle.length > 28 ? activeTitle.slice(0, 26) + "..." : activeTitle}</span>
        <svg class="chevron" class:open={showSessionDropdown} width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M4 6l4 4 4-4"/></svg>
      </button>

      {#if showSessionDropdown}
        <div class="session-dropdown">
          <div class="session-dropdown-header">
            <button class="new-conv-btn" onclick={() => { showSessionDropdown = false; onNewConversation?.(); }}>
              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
              New conversation
            </button>
            {#if conversations.length > 5}
              <input
                class="session-search"
                type="text"
                placeholder="Search..."
                bind:value={sessionSearch}
                onclick={(e) => e.stopPropagation()}
              />
            {/if}
          </div>

          <div class="session-list">
            {#each groupedConversations() as group}
              <div class="session-group-label">{group.label}</div>
              {#each group.items as c}
                <div
                  class="session-item"
                  class:active={c.id === activeConversationId}
                  onclick={() => selectSession(c.id)}
                >
                  {#if editingId === c.id}
                    <!-- svelte-ignore a11y_autofocus -->
                    <input
                      class="rename-input"
                      bind:value={editingTitle}
                      onblur={commitRename}
                      onkeydown={handleRenameKeydown}
                      onclick={(e) => e.stopPropagation()}
                      autofocus
                    />
                  {:else}
                    <span class="session-item-title">{c.title}</span>
                    <div class="session-item-actions">
                      <button class="session-action" title="Rename" onclick={(e) => { e.stopPropagation(); startRename(c); }}>
                        <svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor"><path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z"/></svg>
                      </button>
                      <button class="session-action delete" title="Delete" onclick={(e) => { e.stopPropagation(); onDeleteConversation?.(c.id); }}>
                        <svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor"><path d="M5 2V1h6v1h4v1H1V2h4zm1 3v8h1V5H6zm3 0v8h1V5H9zM3 4v10h10V4H3z"/></svg>
                      </button>
                    </div>
                  {/if}
                </div>
              {/each}
            {/each}
            {#if conversations.length === 0}
              <div class="session-empty">No conversations yet</div>
            {/if}
          </div>
        </div>
      {/if}
    </div>
  </div>

  <div class="header-right">
    <div class="provider-area">
      <button class="provider-btn" onclick={() => showProviderDropdown = !showProviderDropdown}>
        {#if providerLabel && providerLabel !== "none"}
          {providerLabel}{#if modelLabel} / {modelLabel}{/if}
        {:else}
          Provider
        {/if}
        <svg class="chevron" class:open={showProviderDropdown} width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M4 6l4 4 4-4"/></svg>
      </button>

      {#if showProviderDropdown && providers.length > 0}
        <div class="dropdown">
          {#each providers as p}
            <button
              class="dropdown-item"
              class:active={p.id === providerLabel}
              onclick={() => selectProvider(p)}
            >
              <span class="item-label">{p.label}</span>
              {#if p.description}
                <span class="item-desc">{p.description}</span>
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
    min-width: 0;
    flex: 1;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--vscode-descriptionForeground);
    flex-shrink: 0;
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

  /* Session dropdown */
  .session-area {
    position: relative;
    min-width: 0;
    flex: 1;
  }
  .session-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    padding: 2px 6px;
    border-radius: 4px;
    border: none;
    background: transparent;
    color: var(--vscode-foreground);
    cursor: pointer;
    min-width: 0;
    max-width: 100%;
  }
  .session-btn:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .session-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 500;
  }
  .session-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    margin-top: 4px;
    min-width: 280px;
    max-width: 360px;
    max-height: 400px;
    background: var(--vscode-menu-background, var(--vscode-editorWidget-background));
    border: 1px solid var(--vscode-menu-border, var(--vscode-panel-border));
    border-radius: 6px;
    box-shadow: 0 4px 16px rgba(0,0,0,.35);
    z-index: 200;
    display: flex;
    flex-direction: column;
  }
  .session-dropdown-header {
    padding: 6px 8px;
    border-bottom: 1px solid var(--vscode-panel-border);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .new-conv-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 6px 8px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--vscode-foreground);
    font-size: 12px;
    cursor: pointer;
    font-weight: 500;
  }
  .new-conv-btn:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .session-search {
    width: 100%;
    padding: 4px 8px;
    border: 1px solid var(--vscode-input-border);
    border-radius: 4px;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    font-size: 11px;
    outline: none;
  }
  .session-search:focus {
    border-color: var(--dl-primary);
  }
  .session-list {
    overflow-y: auto;
    padding: 4px 0;
  }
  .session-group-label {
    padding: 4px 12px 2px;
    font-size: 10px;
    font-weight: 600;
    color: var(--vscode-descriptionForeground);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .session-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 12px;
    cursor: pointer;
    font-size: 12px;
    color: var(--vscode-foreground);
    min-height: 28px;
  }
  .session-item:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .session-item.active {
    background: var(--vscode-list-activeSelectionBackground);
    color: var(--vscode-list-activeSelectionForeground);
  }
  .session-item-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
  }
  .session-item-actions {
    display: none;
    gap: 2px;
    flex-shrink: 0;
  }
  .session-item:hover .session-item-actions {
    display: flex;
  }
  .session-action {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border: none;
    border-radius: 3px;
    background: transparent;
    color: var(--vscode-descriptionForeground);
    cursor: pointer;
  }
  .session-action:hover {
    background: var(--vscode-list-hoverBackground);
    color: var(--vscode-foreground);
  }
  .session-action.delete:hover {
    color: var(--dl-primary, #ea4647);
  }
  .rename-input {
    flex: 1;
    padding: 2px 6px;
    border: 1px solid var(--dl-primary);
    border-radius: 3px;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    font-size: 12px;
    outline: none;
  }
  .session-empty {
    padding: 12px;
    text-align: center;
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
  }

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
    flex-shrink: 0;
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
  .item-desc {
    font-size: 10px;
    color: var(--vscode-descriptionForeground);
  }
</style>
