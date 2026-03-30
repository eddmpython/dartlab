<script lang="ts">
  interface Props {
    serverState: string;
    onsubmit: (text: string) => void;
  }

  let { serverState, onsubmit }: Props = $props();

  const avatarSrc = document.getElementById("app")?.dataset.avatar ?? "";

  const examples = [
    { code: "005930", label: "Samsung" },
    { code: "AAPL", label: "Apple" },
    { code: "000660", label: "SK Hynix" },
  ];
</script>

<div class="welcome">
  <div class="hero">
    {#if avatarSrc}
      <img src={avatarSrc} alt="DartLab" width="64" height="64" class="avatar" />
    {:else}
      <div class="avatar-placeholder">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" fill="var(--dl-primary)" opacity="0.15"/>
          <text x="16" y="20" text-anchor="middle" fill="var(--dl-primary)" font-size="12" font-weight="bold">DL</text>
        </svg>
      </div>
    {/if}
    <h2>DartLab</h2>
    <p class="tagline">AI-powered corporate analysis</p>
  </div>

  {#if serverState === "starting"}
    <div class="status-card">
      <div class="loading-dots"><span></span><span></span><span></span></div>
      <span>Starting server...</span>
    </div>
  {:else if serverState === "error"}
    <div class="status-card error">
      Server failed to start. Run "DartLab: Show Server Logs" for details.
    </div>
  {:else if serverState === "ready"}
    <div class="prompt-section">
      <p class="prompt-hint">Enter a stock code or company name</p>
      <div class="example-list">
        {#each examples as ex}
          <button class="example-btn" onclick={() => onsubmit(ex.code)}>
            <span class="example-code">{ex.code}</span>
            <span class="example-label">{ex.label}</span>
          </button>
        {/each}
      </div>
    </div>
  {:else}
    <div class="status-card">Waiting for server...</div>
  {/if}
</div>

<style>
  .welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px var(--dl-spacing-lg);
    text-align: center;
    flex: 1;
    min-height: 0;
  }
  .hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 24px;
  }
  .avatar {
    border-radius: 50%;
    margin-bottom: 12px;
    box-shadow: 0 0 20px rgba(234, 70, 71, 0.15);
  }
  .avatar-placeholder {
    margin-bottom: 12px;
  }
  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: var(--vscode-editor-foreground);
  }
  .tagline {
    margin: 4px 0 0;
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
  }

  /* Status */
  .status-card {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: var(--dl-radius-md);
    background: var(--vscode-textCodeBlock-background);
    color: var(--vscode-descriptionForeground);
    font-size: 13px;
  }
  .status-card.error {
    color: var(--dl-primary);
    border-left: 3px solid var(--dl-primary);
  }
  .loading-dots {
    display: flex;
    gap: 3px;
  }
  .loading-dots span {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--dl-primary);
    animation: bounce 1.2s infinite;
  }
  .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
  .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
    30% { opacity: 1; transform: translateY(-3px); }
  }

  /* Examples */
  .prompt-section {
    width: 100%;
    max-width: 240px;
  }
  .prompt-hint {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    margin: 0 0 12px;
  }
  .example-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .example-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: var(--dl-radius-md);
    background: transparent;
    color: var(--vscode-editor-foreground);
    cursor: pointer;
    text-align: left;
    transition: border-color 0.15s, background 0.15s;
  }
  .example-btn:hover {
    background: var(--vscode-list-hoverBackground);
    border-color: var(--dl-primary);
  }
  .example-code {
    font-family: var(--vscode-editor-font-family);
    font-weight: 600;
    color: var(--dl-primary-light);
    font-size: 13px;
  }
  .example-label {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
  }
</style>
