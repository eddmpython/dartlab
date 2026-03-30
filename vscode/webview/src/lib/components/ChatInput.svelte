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
  let showSlashMenu = $state(false);
  let selectedSlashIdx = $state(0);

  interface SlashCmd { name: string; label: string; desc: string; }

  const slashCommands: SlashCmd[] = [
    { name: "model", label: "/model", desc: "Change AI model" },
    { name: "provider", label: "/provider", desc: "Change AI provider" },
    { name: "settings", label: "/settings", desc: "Open settings" },
    { name: "resume", label: "/resume", desc: "Resume conversation" },
    { name: "new", label: "/new", desc: "New conversation" },
    { name: "clear", label: "/clear", desc: "Clear conversation" },
    { name: "help", label: "/help", desc: "Show commands" },
  ];

  const filteredCmds = $derived(() => {
    if (!inputText.startsWith("/")) return [];
    const q = inputText.slice(1).toLowerCase();
    return q ? slashCommands.filter(c => c.name.startsWith(q)) : slashCommands;
  });

  function handleKeydown(e: KeyboardEvent) {
    const cmds = filteredCmds();
    if (showSlashMenu && cmds.length > 0) {
      if (e.key === "ArrowDown") { e.preventDefault(); selectedSlashIdx = (selectedSlashIdx + 1) % cmds.length; return; }
      if (e.key === "ArrowUp") { e.preventDefault(); selectedSlashIdx = (selectedSlashIdx - 1 + cmds.length) % cmds.length; return; }
      if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); runSlash(cmds[selectedSlashIdx]); return; }
      if (e.key === "Escape") { e.preventDefault(); showSlashMenu = false; return; }
    }
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  }

  function runSlash(cmd: SlashCmd) {
    inputText = "";
    showSlashMenu = false;
    selectedSlashIdx = 0;
    oncommand?.(cmd.name);
  }

  function submit() {
    const text = inputText.trim();
    if (!text || disabled) return;
    if (text.startsWith("/")) {
      const cmd = slashCommands.find(c => c.name === text.slice(1).toLowerCase());
      if (cmd) { runSlash(cmd); return; }
    }
    onsubmit(text);
    inputText = "";
    if (textareaEl) textareaEl.style.height = "auto";
  }

  function handleBtnClick() {
    if (streaming) { onstop?.(); }
    else { submit(); }
  }

  function handleInput() {
    if (textareaEl) {
      textareaEl.style.height = "auto";
      textareaEl.style.height = Math.min(textareaEl.scrollHeight, 200) + "px";
    }
    const cmds = filteredCmds();
    showSlashMenu = inputText.startsWith("/") && cmds.length > 0;
    if (showSlashMenu) selectedSlashIdx = 0;
  }
</script>

<div class="input-area">
  {#if showSlashMenu}
    <div class="slash-menu">
      {#each filteredCmds() as cmd, i}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="slash-item" class:selected={i === selectedSlashIdx} onclick={() => runSlash(cmd)}>
          <span class="slash-name">{cmd.label}</span>
          <span class="slash-desc">{cmd.desc}</span>
        </div>
      {/each}
    </div>
  {/if}

  <div class="input-box">
    <textarea
      bind:this={textareaEl}
      bind:value={inputText}
      onkeydown={handleKeydown}
      oninput={handleInput}
      placeholder="Ask about a company..."
      rows="1"
      disabled={disabled && !streaming}
    ></textarea>
    <button
      class="send-btn"
      class:streaming
      onclick={handleBtnClick}
      disabled={disabled && !streaming}
      aria-label={streaming ? "Stop" : "Send"}
    >
      {#if streaming}
        <!-- stop icon (square) -->
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="3" y="3" width="10" height="10" rx="2"/></svg>
      {:else}
        <!-- send icon (arrow) -->
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M3 3l14 7-14 7V12l8-2-8-2V3z"/></svg>
      {/if}
    </button>
  </div>
</div>

<style>
  .input-area {
    padding: 0 20px 12px;
    position: relative;
  }

  .input-box {
    display: flex;
    flex-direction: row;
    align-items: flex-end;
    border: 1px solid var(--vscode-input-border);
    border-radius: 8px;
    background: var(--vscode-input-background);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    transition: border-color 0.15s, box-shadow 0.15s;
    padding: 0;
    position: relative;
  }
  .input-box:focus-within {
    border-color: var(--dl-primary, #ea4647);
    box-shadow: 0 0 0 3px rgba(234, 70, 71, 0.12), 0 1px 2px rgba(234, 70, 71, 0.2);
  }

  textarea {
    flex: 1;
    resize: none;
    border: none;
    background: transparent;
    color: var(--vscode-input-foreground);
    font-family: inherit;
    font-size: inherit;
    line-height: 1.5;
    padding: 10px 14px;
    outline: none;
    overflow-y: auto;
    max-height: 200px;
    min-height: 1.5em;
    word-break: break-word;
  }
  textarea::placeholder {
    color: var(--vscode-input-placeholderForeground);
  }

  .send-btn {
    display: flex;
    cursor: pointer;
    border: none;
    border-radius: 5px;
    justify-content: center;
    align-items: center;
    width: 26px;
    height: 26px;
    flex-shrink: 0;
    margin: 0 6px 8px 0;
    background-color: var(--dl-primary-dark, #c83232);
    color: #faf9f5;
    transition: filter 0.1s;
  }
  .send-btn:hover:not(:disabled) { filter: brightness(1.1); }
  .send-btn:active:not(:disabled) { filter: brightness(0.9); }
  .send-btn:disabled { cursor: not-allowed; opacity: 0.4; }
  .send-btn.streaming { background-color: var(--dl-primary, #ea4647); }

  /* slash menu */
  .slash-menu {
    position: absolute;
    bottom: 100%;
    left: 20px;
    right: 20px;
    background: var(--vscode-editorWidget-background);
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.3);
    overflow: hidden;
    margin-bottom: 4px;
  }
  .slash-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    cursor: pointer;
    font-size: 12px;
  }
  .slash-item:hover, .slash-item.selected {
    background: var(--vscode-list-hoverBackground);
  }
  .slash-name {
    font-weight: 600;
    font-family: var(--vscode-editor-font-family);
    min-width: 80px;
    color: var(--dl-primary-light, #f87171);
  }
  .slash-desc {
    color: var(--vscode-descriptionForeground);
  }
</style>
