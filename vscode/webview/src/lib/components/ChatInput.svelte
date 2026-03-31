<script lang="ts">
  interface Props {
    disabled?: boolean;
    onsubmit: (text: string) => void;
    onstop?: () => void;
    oncommand?: (cmd: string) => void;
    streaming?: boolean;
  }

  let { disabled = false, onsubmit, onstop, oncommand, streaming = false }: Props = $props();
  let inputText = $state("");
  let textareaEl: HTMLTextAreaElement | undefined = $state();
  let showSlash = $state(false);
  let slashIdx = $state(0);

  // Input history (↑↓ arrows)
  let history: string[] = $state([]);
  let historyIdx = $state(-1);

  const cmds = [
    { name: "model", label: "/model", desc: "Change AI model" },
    { name: "provider", label: "/provider", desc: "Change AI provider" },
    { name: "settings", label: "/settings", desc: "Open settings" },
    { name: "resume", label: "/resume", desc: "Resume conversation" },
    { name: "new", label: "/new", desc: "New conversation" },
    { name: "clear", label: "/clear", desc: "Clear conversation" },
    { name: "help", label: "/help", desc: "Show commands" },
  ];

  const filtered = $derived(() => {
    if (!inputText.startsWith("/")) return [];
    const q = inputText.slice(1).toLowerCase();
    return q ? cmds.filter(c => c.name.startsWith(q)) : cmds;
  });

  function handleKeydown(e: KeyboardEvent) {
    const list = filtered();
    if (showSlash && list.length) {
      if (e.key === "ArrowDown") { e.preventDefault(); slashIdx = (slashIdx + 1) % list.length; return; }
      if (e.key === "ArrowUp") { e.preventDefault(); slashIdx = (slashIdx - 1 + list.length) % list.length; return; }
      if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); execSlash(list[slashIdx]); return; }
      if (e.key === "Escape") { e.preventDefault(); showSlash = false; return; }
    }
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
    if (e.key === "Escape" && streaming) { e.preventDefault(); onstop?.(); }
    // Input history: ↑ previous, ↓ next
    if (e.key === "ArrowUp" && !inputText.includes("\n") && history.length > 0) {
      e.preventDefault();
      if (historyIdx < history.length - 1) historyIdx++;
      inputText = history[historyIdx];
    }
    if (e.key === "ArrowDown" && !inputText.includes("\n") && historyIdx >= 0) {
      e.preventDefault();
      historyIdx--;
      inputText = historyIdx >= 0 ? history[historyIdx] : "";
    }
  }

  function execSlash(c: typeof cmds[0]) { inputText = ""; showSlash = false; slashIdx = 0; oncommand?.(c.name); }

  function submit() {
    const t = inputText.trim();
    if (!t || disabled) return;
    if (t.startsWith("/")) { const c = cmds.find(x => x.name === t.slice(1).toLowerCase()); if (c) { execSlash(c); return; } }
    onsubmit(t);
    history = [t, ...history.slice(0, 49)]; // keep last 50
    historyIdx = -1;
    inputText = "";
    if (textareaEl) textareaEl.style.height = "auto";
  }

  function btnClick() { streaming ? onstop?.() : submit(); }

  function handleInput() {
    if (textareaEl) { textareaEl.style.height = "auto"; textareaEl.style.height = Math.min(textareaEl.scrollHeight, 200) + "px"; }
    const list = filtered();
    showSlash = inputText.startsWith("/") && list.length > 0;
    if (showSlash) slashIdx = 0;
  }
</script>

<div class="input-area">
  {#if showSlash}
    <div class="slash-menu">
      {#each filtered() as c, i}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="slash-item" class:sel={i === slashIdx} onclick={() => execSlash(c)}>
          <span class="slash-name">{c.label}</span>
          <span class="slash-desc">{c.desc}</span>
        </div>
      {/each}
    </div>
  {/if}

  <!-- exact Claude Code: .inputContainer_cKsPxg -->
  <div class="input-box">
    <div class="input-row">
      <!-- exact Claude Code: .messageInput_cKsPxg -->
      <textarea
        bind:this={textareaEl}
        bind:value={inputText}
        onkeydown={handleKeydown}
        oninput={handleInput}
        placeholder="종목코드 또는 회사명 (005930, 삼성전자)"
        rows="1"
        disabled={disabled && !streaming}
      ></textarea>
    </div>
    <!-- exact Claude Code: .inputFooter_gGYT1w -->
    <div class="input-footer">
      <div class="footer-left"></div>
      <!-- exact Claude Code: .sendButton_gGYT1w -->
      <button class="send-btn" class:streaming onclick={btnClick} disabled={disabled && !streaming} aria-label={streaming ? "Stop" : "Send"}>
        {#if streaming}
          <svg class="stop-icon" viewBox="0 0 16 16" fill="currentColor"><rect x="3" y="3" width="10" height="10" rx="2"/></svg>
        {:else}
          <svg class="send-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M3 3l14 7-14 7V12l8-2-8-2V3z"/></svg>
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  .input-area {
    padding: 0 16px 12px;
    position: relative;
    width: 100%;
    max-width: 100%;
  }

  /* exact Claude Code: .inputContainer_cKsPxg */
  .input-box {
    background: var(--vscode-menu-background, var(--vscode-input-background));
    border: 1px solid var(--vscode-inlineChatInput-border, var(--vscode-input-border));
    border-radius: var(--corner-radius-large);
    color: var(--vscode-input-foreground);
    display: flex;
    position: relative;
    flex-direction: column;
    min-width: 0;
    margin: 0;
    padding: 0;
    box-shadow: 0 1px 2px #0000001a;
  }
  .input-box:focus-within {
    border-color: var(--dl-primary);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--dl-primary) 12%, transparent), 0 1px 2px color-mix(in srgb, var(--dl-primary), transparent 80%);
  }

  .input-row {
    position: relative;
    display: flex;
  }

  /* exact Claude Code: .messageInput_cKsPxg */
  textarea {
    outline: none;
    overflow-y: auto;
    overflow-wrap: break-word;
    word-break: break-word;
    scrollbar-gutter: stable;
    position: relative;
    user-select: text;
    caret-color: var(--vscode-input-foreground);
    color: var(--vscode-input-foreground);
    background: transparent;
    border: none;
    z-index: 1;
    flex: 1;
    align-self: stretch;
    min-height: 1.5em;
    max-height: 200px;
    padding: 10px 14px;
    font-family: inherit;
    font-size: inherit;
    line-height: 1.5;
    resize: none;
  }
  textarea::placeholder {
    color: var(--vscode-input-placeholderForeground);
  }
  textarea:focus { outline: none; }

  /* exact Claude Code: .inputFooter_gGYT1w */
  .input-footer {
    display: flex;
    color: var(--vscode-descriptionForeground);
    border-top: .5px solid var(--vscode-inlineChatInput-border, var(--vscode-input-border));
    z-index: 6;
    align-items: center;
    gap: 6px;
    min-width: 0;
    padding: 5px;
  }
  .footer-left { flex: 1; }

  /* exact Claude Code: .sendButton_gGYT1w */
  .send-btn {
    cursor: pointer;
    display: flex;
    border: none;
    border-radius: 5px;
    justify-content: center;
    align-items: center;
    width: 26px;
    height: 26px;
    color: #faf9f5;
    background-color: var(--dl-primary-dark, #c83232);
  }
  .send-btn:hover:not(:disabled) { filter: brightness(1.1); }
  .send-btn:active:not(:disabled) { filter: brightness(.9); }
  .send-btn:disabled { cursor: not-allowed; opacity: .4; }
  .send-btn.streaming { background-color: var(--dl-primary, #ea4647); }

  .send-icon { display: block; flex-shrink: 0; width: 20px; height: 20px; }
  .stop-icon { display: block; width: 16px; height: 16px; }

  /* slash menu */
  .slash-menu {
    position: absolute; bottom: 100%; left: 0; right: 0;
    background: var(--vscode-menu-background, var(--vscode-editorWidget-background));
    border: 1px solid var(--vscode-menu-border, var(--vscode-panel-border));
    border-radius: var(--corner-radius-medium);
    box-shadow: 0 -4px 12px rgba(0,0,0,.3);
    overflow: hidden; margin-bottom: 4px;
  }
  .slash-item {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 10px; cursor: pointer; font-size: 12px;
  }
  .slash-item:hover, .slash-item.sel { background: var(--vscode-list-hoverBackground); }
  .slash-name { font-weight: 600; font-family: var(--vscode-editor-font-family); min-width: 80px; color: var(--dl-primary-light); }
  .slash-desc { color: var(--vscode-descriptionForeground); }
</style>
