<script lang="ts">
  interface TemplateInfo {
    name: string;
    description: string;
    source: "builtin" | "user";
  }

  type AnalysisMode = "ask" | "analysis" | "review";

  interface Props {
    disabled?: boolean;
    onsubmit: (text: string, modules?: string[], mode?: string) => void;
    onstop?: () => void;
    oncommand?: (cmd: string) => void;
    streaming?: boolean;
    templates?: TemplateInfo[];
    analysisMode?: AnalysisMode;
    onModeChange?: (mode: AnalysisMode) => void;
    watchlist?: Array<{code: string; name: string}>;
  }

  let { disabled = false, onsubmit, onstop, oncommand, streaming = false, templates = [], analysisMode = "ask", onModeChange, watchlist = [] }: Props = $props();

  const MODE_CYCLE: AnalysisMode[] = ["ask", "analysis", "review"];
  const MODE_LABELS: Record<AnalysisMode, string> = { ask: "질문", analysis: "분석", review: "보고서" };
  const MODE_COLORS: Record<AnalysisMode, string> = { ask: "var(--dl-primary, #ea4647)", analysis: "#3b82f6", review: "#34d399" };

  function cycleMode() {
    const idx = MODE_CYCLE.indexOf(analysisMode);
    const next = MODE_CYCLE[(idx + 1) % MODE_CYCLE.length];
    onModeChange?.(next);
  }
  let inputText = $state("");
  let textareaEl: HTMLTextAreaElement | undefined = $state();
  let showSlash = $state(false);
  let slashIdx = $state(0);

  // 모듈 선택 (multi-select, 최대 3개)
  let selectedModules: string[] = $state(
    JSON.parse(localStorage.getItem("dartlab-modules") || "[]")
  );

  function toggleModule(name: string) {
    if (selectedModules.includes(name)) {
      selectedModules = selectedModules.filter(m => m !== name);
    } else if (selectedModules.length < 3) {
      selectedModules = [...selectedModules, name];
    }
    localStorage.setItem("dartlab-modules", JSON.stringify(selectedModules));
  }

  // @ Mention popup
  let showMention = $state(false);
  let mentionIdx = $state(0);
  let mentionQuery = $state("");

  const AXES = [
    { label: "수익성", value: "@수익성" },
    { label: "안정성", value: "@안정성" },
    { label: "성장성", value: "@성장성" },
    { label: "현금흐름", value: "@현금흐름" },
    { label: "밸류에이션", value: "@밸류에이션" },
    { label: "비용구조", value: "@비용구조" },
    { label: "자본배분", value: "@자본배분" },
  ];

  let mentionItems = $derived(() => {
    const q = mentionQuery.toLowerCase();
    const wl = watchlist.map(w => ({ label: `${w.name} (${w.code})`, value: `@${w.code}` }));
    const all = [...wl, ...AXES];
    return q ? all.filter(i => i.label.toLowerCase().includes(q) || i.value.toLowerCase().includes(q)) : all;
  });

  function insertMention(item: { label: string; value: string }) {
    // Replace @query with the mention value
    const atIdx = inputText.lastIndexOf("@");
    if (atIdx >= 0) {
      inputText = inputText.slice(0, atIdx) + item.value + " ";
    }
    showMention = false;
    mentionQuery = "";
    mentionIdx = 0;
    textareaEl?.focus();
  }

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
    // @ mention nav
    const mList = mentionItems();
    if (showMention && mList.length) {
      if (e.key === "ArrowDown") { e.preventDefault(); mentionIdx = (mentionIdx + 1) % mList.length; return; }
      if (e.key === "ArrowUp") { e.preventDefault(); mentionIdx = (mentionIdx - 1 + mList.length) % mList.length; return; }
      if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); insertMention(mList[mentionIdx]); return; }
      if (e.key === "Escape") { e.preventDefault(); showMention = false; return; }
    }
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
    onsubmit(t, selectedModules.length ? selectedModules : undefined, analysisMode !== "ask" ? analysisMode : undefined);
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

    // @ mention detection
    const atIdx = inputText.lastIndexOf("@");
    if (atIdx >= 0 && !inputText.startsWith("/")) {
      mentionQuery = inputText.slice(atIdx + 1);
      const items = mentionItems();
      showMention = items.length > 0;
      if (showMention) mentionIdx = 0;
    } else {
      showMention = false;
    }
  }
</script>

<div class="input-area">
  {#if showMention}
    <div class="slash-menu">
      {#each mentionItems() as item, i}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="slash-item" class:sel={i === mentionIdx} onclick={() => insertMention(item)}>
          <span class="slash-name">{item.value}</span>
          <span class="slash-desc">{item.label}</span>
        </div>
      {/each}
    </div>
  {/if}

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
  <div class="input-box" style="--focus-ring-color: {MODE_COLORS[analysisMode]}">
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
      <div class="footer-left">
        <button class="mode-pill" style="--mode-color: {MODE_COLORS[analysisMode]}" onclick={cycleMode} title="분석 모드 전환">
          {MODE_LABELS[analysisMode]}
        </button>
        {#if !streaming}
          {#each templates as t}
            <button
              class="tmpl-btn"
              class:selected={selectedModules.includes(t.name)}
              onclick={() => toggleModule(t.name)}
              title={t.description || t.name}
            >{t.name}</button>
          {/each}
          {#if templates.length === 0}
            {#each [
              { label: "수익성", q: "수익성 분석" },
              { label: "밸류에이션", q: "밸류에이션 분석" },
              { label: "전망", q: "매출 전망 분석" },
              { label: "비교", q: "동종업계 비교" },
            ] as t}
              <button class="tmpl-btn" onclick={() => { inputText = t.q; textareaEl?.focus(); }}>{t.label}</button>
            {/each}
          {/if}
        {/if}
      </div>
      <!-- exact Claude Code: .sendButton_gGYT1w -->
      <button class="send-btn" class:streaming onclick={btnClick} disabled={disabled && !streaming} aria-label={streaming ? "Stop" : "Send"} style="background-color: {streaming ? 'var(--dl-primary)' : MODE_COLORS[analysisMode]}">
        {#if streaming}
          <svg class="stop-icon" viewBox="0 0 16 16" fill="currentColor"><rect x="3" y="3" width="10" height="10" rx="2"/></svg>
        {:else}
          <svg class="send-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 16V4M10 4l-5 5M10 4l5 5"/></svg>
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  .input-area {
    padding: 0;
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
    border-color: var(--focus-ring-color, var(--dl-primary));
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--focus-ring-color, var(--dl-primary)) 12%, transparent), 0 1px 2px color-mix(in srgb, var(--focus-ring-color, var(--dl-primary)), transparent 80%);
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
  .footer-left {
    flex: 1;
    display: flex;
    gap: 3px;
    overflow: hidden;
  }
  .tmpl-btn {
    padding: 1px 6px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 3px;
    background: transparent;
    color: var(--vscode-descriptionForeground);
    font-size: 10px;
    cursor: pointer;
    white-space: nowrap;
    transition: border-color 0.15s, color 0.15s;
  }
  .tmpl-btn:hover {
    border-color: var(--dl-primary);
    color: var(--dl-primary-light);
  }
  .tmpl-btn.selected {
    background: var(--dl-primary);
    color: var(--vscode-editor-background);
    border-color: var(--dl-primary);
  }

  /* Claude Code: .sendButton_gGYT1w — round circle + up arrow */
  .send-btn {
    cursor: pointer;
    display: flex;
    border: none;
    border-radius: 50%;
    justify-content: center;
    align-items: center;
    width: 28px;
    height: 28px;
    color: #faf9f5;
    background-color: var(--dl-primary-dark, #c83232);
    flex-shrink: 0;
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

  /* Claude Code: footerButton mode pill */
  .mode-pill {
    appearance: none;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border: 1px solid var(--mode-color);
    border-radius: 4px;
    background: color-mix(in srgb, var(--mode-color) 15%, transparent);
    color: var(--mode-color);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    flex-shrink: 0;
  }
  .mode-pill:hover {
    background: color-mix(in srgb, var(--mode-color) 25%, transparent);
  }
</style>
