<script lang="ts">
  import * as client from "../api/client";
  import { onMessage } from "../vscode";

  interface Props {
    onclose: () => void;
  }

  let { onclose }: Props = $props();

  interface ProviderInfo {
    id: string;
    label: string;
    auth: string;
    authenticated: boolean;
    models?: string[];
  }

  interface Profile {
    provider: string | null;
    model: string | null;
    temperature: number;
    providers: ProviderInfo[];
  }

  let profile: Profile | null = $state(null);
  let models: string[] = $state([]);
  let selectedProvider = $state("");
  let selectedModel = $state("");
  let apiKeyInput = $state("");
  let saving = $state(false);

  // Load profile on mount
  client.getProfile();

  onMessage((msg: unknown) => {
    const m = msg as Record<string, unknown>;
    if (m.type === "profile" && m.payload) {
      const p = m.payload as Profile;
      profile = p;
      if (!selectedProvider && p.provider) selectedProvider = p.provider;
      if (!selectedModel && p.model) selectedModel = p.model;
      // Auto-load models for current provider
      if (selectedProvider) client.getModels(selectedProvider);
    }
    if (m.type === "models") {
      const payload = m.payload as { models: string[] };
      models = payload.models;
    }
  });

  function handleProviderChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    selectedProvider = target.value;
    selectedModel = "";
    models = [];
    client.getModels(selectedProvider);
  }

  function handleModelChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    selectedModel = target.value;
  }

  function applySettings() {
    saving = true;
    client.updateProfile({
      provider: selectedProvider || undefined,
      model: selectedModel || undefined,
    });
    setTimeout(() => { saving = false; }, 500);
  }

  function saveApiKey() {
    if (!apiKeyInput.trim() || !selectedProvider) return;
    client.updateSecret(selectedProvider, apiKeyInput.trim(), "set");
    apiKeyInput = "";
  }

  function getAuthLabel(provider: ProviderInfo): string {
    if (provider.authenticated) return "Connected";
    if (provider.auth === "none") return "No auth needed";
    if (provider.auth === "oauth") return "Login required";
    return "API key required";
  }

  const currentProvider = $derived(
    profile?.providers.find(p => p.id === selectedProvider)
  );
</script>

<div class="settings-panel">
  <div class="settings-header">
    <span class="settings-title">AI Settings</span>
    <button class="close-btn" onclick={onclose} aria-label="Close">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
        <line x1="3" y1="3" x2="11" y2="11"/>
        <line x1="11" y1="3" x2="3" y2="11"/>
      </svg>
    </button>
  </div>

  {#if !profile}
    <div class="loading">Loading...</div>
  {:else}
    <!-- Provider -->
    <div class="field">
      <label class="field-label" for="dl-provider">Provider</label>
      <select id="dl-provider" class="field-select" value={selectedProvider} onchange={handleProviderChange}>
        <option value="">Select provider...</option>
        {#each profile.providers as p}
          <option value={p.id}>{p.label}</option>
        {/each}
      </select>
    </div>

    <!-- Auth status -->
    {#if currentProvider}
      <div class="auth-status" class:connected={currentProvider.authenticated}>
        <span class="auth-dot"></span>
        {getAuthLabel(currentProvider)}
      </div>

      <!-- API key input (for api_key auth) -->
      {#if currentProvider.auth === "api_key" && !currentProvider.authenticated}
        <div class="field">
          <label class="field-label" for="dl-apikey">API Key</label>
          <div class="key-row">
            <input
              id="dl-apikey"
              type="password"
              class="field-input"
              bind:value={apiKeyInput}
              placeholder="Enter API key..."
            />
            <button class="save-key-btn" onclick={saveApiKey} disabled={!apiKeyInput.trim()}>
              Save
            </button>
          </div>
        </div>
      {/if}
    {/if}

    <!-- Model -->
    <div class="field">
      <label class="field-label" for="dl-model">Model</label>
      <select id="dl-model" class="field-select" value={selectedModel} onchange={handleModelChange} disabled={models.length === 0}>
        <option value="">{models.length === 0 ? "Select provider first" : "Select model..."}</option>
        {#each models as m}
          <option value={m}>{m}</option>
        {/each}
      </select>
    </div>

    <!-- Apply -->
    <button class="apply-btn" onclick={applySettings} disabled={saving}>
      {saving ? "Saving..." : "Apply"}
    </button>
  {/if}
</div>

<style>
  .settings-panel {
    border-bottom: 1px solid var(--vscode-panel-border);
    padding: var(--dl-spacing-md);
    background: var(--vscode-editorWidget-background);
  }
  .settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--dl-spacing-md);
  }
  .settings-title {
    font-size: 13px;
    font-weight: 600;
  }
  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border: none;
    border-radius: var(--dl-radius-sm);
    background: transparent;
    color: var(--vscode-editor-foreground);
    cursor: pointer;
    opacity: 0.6;
  }
  .close-btn:hover { opacity: 1; }

  .loading {
    color: var(--vscode-descriptionForeground);
    font-size: 12px;
    padding: 8px 0;
  }

  .field {
    margin-bottom: var(--dl-spacing-sm);
  }
  .field-label {
    display: block;
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .field-select, .field-input {
    width: 100%;
    padding: 5px 8px;
    border: 1px solid var(--vscode-input-border);
    border-radius: var(--dl-radius-sm);
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    font-size: 12px;
    font-family: var(--vscode-font-family);
    outline: none;
  }
  .field-select:focus, .field-input:focus {
    border-color: var(--dl-primary);
  }

  .auth-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    margin-bottom: var(--dl-spacing-sm);
  }
  .auth-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--dl-primary);
  }
  .auth-status.connected .auth-dot {
    background: #34d399;
  }

  .key-row {
    display: flex;
    gap: 4px;
  }
  .key-row .field-input { flex: 1; }
  .save-key-btn {
    padding: 4px 10px;
    border: none;
    border-radius: var(--dl-radius-sm);
    background: var(--dl-primary);
    color: #fff;
    font-size: 11px;
    cursor: pointer;
    white-space: nowrap;
  }
  .save-key-btn:disabled {
    opacity: 0.4;
    cursor: default;
  }

  .apply-btn {
    width: 100%;
    padding: 6px;
    margin-top: var(--dl-spacing-sm);
    border: none;
    border-radius: var(--dl-radius-md);
    background: var(--dl-primary);
    color: #fff;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.15s;
  }
  .apply-btn:hover:not(:disabled) {
    background: var(--dl-primary-dark);
  }
  .apply-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
