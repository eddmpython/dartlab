<script lang="ts">
  import type { Message } from "../api/sseHandler";
  import * as client from "../api/client";
  import { postMessage } from "../vscode";
  import { createIncrementalRenderer } from "../markdown/renderer";
  import { createStreamSplitter } from "../markdown/contentSplitter";

  interface Props {
    message: Message;
    isLast?: boolean;
    onregenerate?: () => void;
    oncopy?: () => void;
  }
  let { message, isLast = false, onregenerate, oncopy }: Props = $props();
  const render = createIncrementalRenderer();
  const splitter = createStreamSplitter();

  // Split streaming content into committed (safe HTML) and draft (raw pre)
  let split = $derived.by(() => {
    if (message.role !== "assistant" || !message.text) {
      return { committed: "", draft: "", draftType: "none" as const };
    }
    return splitter.split(message.text, message.loading);
  });

  let committedHtml = $derived(split.committed ? render(split.committed) : "");

  // Tool events: interleave call/result pairs
  let toolPairs = $derived.by(() => {
    const events = message.toolEvents ?? [];
    const pairs: Array<{ call: Record<string, unknown>; result?: Record<string, unknown> }> = [];
    for (const ev of events) {
      if (ev.type === "call") {
        pairs.push({ call: ev });
      } else if (ev.type === "result" && pairs.length > 0) {
        const last = pairs[pairs.length - 1];
        if (!last.result) last.result = ev;
      }
    }
    return pairs;
  });

  // Active tool (last call without result while loading)
  let activeTool = $derived.by(() => {
    if (!message.loading) return null;
    const events = message.toolEvents ?? [];
    if (events.length === 0) return null;
    const last = events[events.length - 1];
    if (last.type === "call") return last;
    return null;
  });

  // Loading phase
  let loadingPhase = $derived.by(() => {
    if (!message.loading) return "";
    if (message.text) return "generating";
    if (message.toolEvents?.length) return "tools";
    if (message.contexts?.length) return "context";
    if (message.snapshot) return "snapshot";
    if (message.meta) return "analyzing";
    return "thinking";
  });

  // Elapsed seconds
  let elapsed = $state(0);
  let timer: ReturnType<typeof setInterval> | undefined;
  $effect(() => {
    if (message.loading && message.startedAt) {
      elapsed = Math.floor((Date.now() - message.startedAt) / 1000);
      timer = setInterval(() => {
        elapsed = Math.floor((Date.now() - (message.startedAt ?? Date.now())) / 1000);
      }, 1000);
      return () => { if (timer) clearInterval(timer); };
    } else {
      if (timer) clearInterval(timer);
    }
  });

  // Collapse state for tool results
  let collapsedTools: Record<number, boolean> = $state({});
  function toggleTool(idx: number) {
    collapsedTools[idx] = !collapsedTools[idx];
    collapsedTools = { ...collapsedTools };
  }

  // Copy code block
  function copyCode(e: MouseEvent) {
    const btn = (e.target as HTMLElement).closest(".copy-btn");
    if (!btn) return;
    const pre = btn.closest(".code-block-wrap")?.querySelector("code");
    if (!pre) return;
    navigator.clipboard.writeText(pre.textContent ?? "");
    btn.classList.add("copied");
    setTimeout(() => btn.classList.remove("copied"), 2000);
  }

  // Wrap code blocks with copy button after render
  function wrapCodeBlocks(html: string): string {
    return html.replace(
      /<pre class="code-block">/g,
      '<div class="code-block-wrap"><button class="copy-btn" title="Copy"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="5" width="8" height="8" rx="1.5"/><path d="M3 11V3h8"/></svg></button><pre class="code-block">'
    ).replace(/<\/pre>/g, '</pre></div>');
  }

  let finalCommittedHtml = $derived(wrapCodeBlocks(committedHtml));

  function formatToolArg(args: unknown): string {
    if (!args) return "";
    if (typeof args === "string") return args;
    try {
      const obj = typeof args === "object" ? args : JSON.parse(String(args));
      const entries = Object.entries(obj as Record<string, unknown>);
      return entries.map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(", ");
    } catch {
      return String(args);
    }
  }

  function truncate(s: string, max: number): string {
    return s.length > max ? s.slice(0, max) + "..." : s;
  }

  function formatDuration(ms: number): string {
    const s = ms / 1000;
    return s < 1 ? "<1s" : `${s.toFixed(1)}s`;
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="msg" class:user={message.role === "user"}>
  {#if message.role === "user"}
    <div class="user-wrap">
      <div class="user-text">{message.text}</div>
    </div>
  {:else}
    <!-- Meta badge row -->
    {#if message.meta}
      {@const meta = message.meta}
      <div class="meta-badges">
        {#if meta.company}
          <span class="badge badge-company">{meta.company}</span>
        {/if}
        {#if meta.market}
          <span class="badge">{meta.market}</span>
        {/if}
        {#if meta.dataYearRange}
          <span class="badge">{meta.dataYearRange}</span>
        {/if}
        {#if meta.dialogueMode}
          <span class="badge">{meta.dialogueMode}</span>
        {/if}
      </div>
    {/if}

    <!-- Snapshot card -->
    {#if message.snapshot}
      {@const snap = message.snapshot}
      <div class="snapshot-card">
        {#if snap.items && Array.isArray(snap.items)}
          <div class="snapshot-grid">
            {#each snap.items as item}
              <div class="snapshot-item" class:good={item.status === "good"} class:danger={item.status === "danger"} class:caution={item.status === "caution"}>
                <span class="snapshot-label">{item.label}</span>
                <span class="snapshot-value">{item.value}</span>
              </div>
            {/each}
          </div>
        {/if}
        {#if snap.grades && typeof snap.grades === "object"}
          <div class="snapshot-grades">
            {#each Object.entries(snap.grades) as [area, grade]}
              <span class="grade-badge grade-{String(grade).toLowerCase()}">{area} {grade}</span>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Context badges (data modules used) -->
    {#if message.contexts?.length}
      <div class="context-badges">
        <svg class="ctx-icon" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M3 3h10v2H3V3zm0 4h10v2H3V7zm0 4h7v2H3v-2z"/></svg>
        {#each message.contexts as ctx}
          <span class="badge badge-ctx">{ctx.label || ctx.module}</span>
        {/each}
      </div>
    {/if}

    <!-- Loading: step-by-step progress (Claude Code style spinner) -->
    {#if message.loading && !message.text}
      <div class="loading-block">
        <div class="spinner-row">
          <div class="spinner"></div>
          <span class="spinner-label">
            {#if loadingPhase === "thinking"}
              Thinking...
            {:else if loadingPhase === "analyzing"}
              Analyzing {message.meta?.company ?? ""}...
            {:else if loadingPhase === "snapshot"}
              Loading key metrics...
            {:else if loadingPhase === "context"}
              Loading data modules ({message.contexts?.length ?? 0})...
            {:else if loadingPhase === "tools"}
              {#if activeTool}
                Running {activeTool.name}...
              {:else}
                Processing tools...
              {/if}
            {:else}
              Generating response...
            {/if}
          </span>
          {#if elapsed > 0}
            <span class="elapsed">{elapsed}s</span>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Tool events inline (Claude Code style) -->
    {#if toolPairs.length > 0}
      <div class="tool-section">
        {#each toolPairs as pair, i}
          <div class="tool-block">
            <button class="tool-header" onclick={() => toggleTool(i)}>
              <svg class="tool-chevron" class:open={!collapsedTools[i]} width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                <path d="M6 4l4 4-4 4"/>
              </svg>
              <span class="tool-icon">
                {#if pair.result}
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" class="tool-ok"><path d="M6.5 12L2 7.5l1.4-1.4L6.5 9.2l6.1-6.1L14 4.5z"/></svg>
                {:else}
                  <div class="tool-spinner-sm"></div>
                {/if}
              </span>
              <span class="tool-name">{pair.call.name}</span>
              <span class="tool-args">{truncate(formatToolArg(pair.call.arguments), 60)}</span>
            </button>
            {#if !collapsedTools[i] && pair.result}
              <div class="tool-result">
                <pre>{truncate(typeof pair.result.result === "string" ? pair.result.result : JSON.stringify(pair.result.result, null, 2), 2000)}</pre>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <!-- Active tool spinner (no result yet, while also generating text) -->
    {#if activeTool && message.text}
      <div class="active-tool-row">
        <div class="tool-spinner-sm"></div>
        <span class="active-tool-label">Running {activeTool.name}...</span>
      </div>
    {/if}

    <!-- Committed content (rendered markdown) -->
    {#if split.committed}
      <div class="content" onclick={copyCode}>{@html finalCommittedHtml}</div>
    {/if}

    <!-- Draft content (still streaming, show as raw) -->
    {#if split.draft}
      <div class="draft" class:draft-code={split.draftType === "code"} class:draft-table={split.draftType === "table"}>
        {#if split.draftType === "code"}
          <span class="draft-label">Code block...</span>
        {:else if split.draftType === "table"}
          <span class="draft-label">Building table...</span>
        {/if}
        <pre class="draft-pre">{split.draft}</pre>
      </div>
    {/if}

    <!-- Streaming cursor -->
    {#if message.loading && message.text}
      <span class="cursor"></span>
    {/if}

    <!-- Error with guide + provider switch -->
    {#if message.error}
      <div class="error-block">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v3.5M8 10.5v.5"/></svg>
        <span>Error</span>
      </div>

      {#if message.text && message.text.includes("**Error:**")}
        <div class="error-guide">
          {@html render(message.text.split("**Error:**").pop()?.trim() ?? "")}
        </div>
      {/if}

      {#if message.errorAction === "relogin" || message.errorAction === "config"}
        <div class="error-switch">
          <span class="error-switch-label">
            {message.errorAction === "relogin" ? "인증 만료." : "API 키 필요."}
            다른 provider를 선택하세요:
          </span>
          <div class="error-switch-btns">
            {#each [
              { id: "gemini", label: "Gemini (무료)" },
              { id: "groq", label: "Groq (무료)" },
              { id: "cerebras", label: "Cerebras (무료)" },
              { id: "mistral", label: "Mistral (무료)" },
            ] as p}
              <button class="switch-btn" onclick={() => {
                postMessage({ type: "log", message: `switch-provider: ${p.id}` });
                client.setProvider(p.id);
              }}>{p.label}</button>
            {/each}
          </div>
        </div>
      {:else if message.errorAction === "retry"}
        <div class="error-switch">
          <button class="switch-btn" onclick={onregenerate}>재시도</button>
        </div>
      {/if}
    {/if}

    <!-- Completion footer + action buttons -->
    {#if !message.loading && message.text && !message.error}
      <div class="footer-meta">
        {#if message.duration}
          <span class="footer-duration">{formatDuration(message.duration)}</span>
        {/if}
        {#if message.contexts?.length}
          <span class="footer-sep">|</span>
          <span class="footer-modules">{message.contexts.length} modules</span>
        {/if}
        {#if message.toolEvents?.length}
          <span class="footer-sep">|</span>
          <span class="footer-tools">{message.toolEvents.filter(e => e.type === "call").length} tools</span>
        {/if}

        <span class="footer-spacer"></span>

        {#if oncopy}
          <button class="action-btn" onclick={oncopy} title="Copy response">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="5" width="8" height="8" rx="1.5"/><path d="M3 11V3h8"/></svg>
          </button>
        {/if}
        {#if onregenerate}
          <button class="action-btn" onclick={onregenerate} title="Regenerate">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 8a6 6 0 0110.9-3.5M14 8a6 6 0 01-10.9 3.5"/><path d="M14 2v4h-4M2 14v-4h4"/></svg>
          </button>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  /* === Message container === */
  .msg {
    color: var(--vscode-foreground);
    display: flex;
    position: relative;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
    padding: 8px 0;
    width: 100%;
    max-width: 100%;
  }
  .msg:first-child { padding-top: 0; }

  /* === User message (Claude Code exact) === */
  .user-wrap {
    display: inline-block;
    position: relative;
    margin: 4px 0;
  }
  .user-wrap:first-child { margin-top: 0; }
  .user-text {
    white-space: pre-wrap;
    word-break: break-word;
    border: 1px solid var(--vscode-inlineChatInput-border, var(--vscode-input-border));
    border-radius: var(--corner-radius-medium);
    background-color: var(--vscode-input-background);
    display: inline-block;
    overflow-x: hidden;
    overflow-y: hidden;
    user-select: text;
    max-width: 100%;
    padding: 4px 6px;
  }

  /* === Meta badges === */
  .meta-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 6px;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 11px;
    background: var(--vscode-badge-background);
    color: var(--vscode-badge-foreground);
  }
  .badge-company {
    background: color-mix(in srgb, var(--dl-primary) 15%, transparent);
    color: var(--dl-primary-light);
    font-weight: 600;
  }

  /* === Snapshot card === */
  .snapshot-card {
    border: 1px solid var(--vscode-panel-border);
    border-radius: var(--corner-radius-medium);
    padding: 8px 10px;
    margin-bottom: 8px;
    background: var(--vscode-editorWidget-background);
  }
  .snapshot-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 6px;
  }
  .snapshot-item {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }
  .snapshot-label {
    font-size: 10px;
    color: var(--vscode-descriptionForeground);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .snapshot-value {
    font-size: 13px;
    font-weight: 600;
  }
  .snapshot-item.good .snapshot-value { color: #34d399; }
  .snapshot-item.danger .snapshot-value { color: #f87171; }
  .snapshot-item.caution .snapshot-value { color: #fbbf24; }
  .snapshot-grades {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid var(--vscode-panel-border);
  }
  .grade-badge {
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 3px;
    font-weight: 600;
    background: var(--vscode-badge-background);
    color: var(--vscode-badge-foreground);
  }
  .grade-badge.grade-a { background: #065f46; color: #6ee7b7; }
  .grade-badge.grade-b { background: #1e3a5f; color: #93c5fd; }
  .grade-badge.grade-c { background: #78350f; color: #fde68a; }
  .grade-badge.grade-d { background: #7c2d12; color: #fdba74; }
  .grade-badge.grade-f { background: #7f1d1d; color: #fca5a5; }

  /* === Context badges === */
  .context-badges {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
    margin-bottom: 6px;
  }
  .ctx-icon {
    color: var(--vscode-descriptionForeground);
    flex-shrink: 0;
  }
  .badge-ctx {
    font-size: 10px;
    background: var(--vscode-textCodeBlock-background);
    color: var(--vscode-descriptionForeground);
  }

  /* === Loading block (Claude Code spinner style) === */
  .loading-block {
    padding: 4px 0;
  }
  .spinner-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid var(--vscode-descriptionForeground);
    border-top-color: var(--dl-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner-label {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
  }
  .elapsed {
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    opacity: 0.6;
    margin-left: auto;
  }

  /* === Tool events (Claude Code inline style) === */
  .tool-section {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 6px 0;
  }
  .tool-block {
    border-radius: var(--corner-radius-small);
    overflow: hidden;
  }
  .tool-header {
    display: flex;
    align-items: center;
    gap: 4px;
    width: 100%;
    padding: 3px 6px;
    border: none;
    border-radius: var(--corner-radius-small);
    background: var(--vscode-textCodeBlock-background);
    color: var(--vscode-foreground);
    font: inherit;
    font-size: 12px;
    cursor: pointer;
    text-align: left;
  }
  .tool-header:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .tool-chevron {
    flex-shrink: 0;
    transition: transform 0.15s;
    color: var(--vscode-descriptionForeground);
  }
  .tool-chevron.open {
    transform: rotate(90deg);
  }
  .tool-icon {
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }
  .tool-ok {
    color: #34d399;
  }
  .tool-name {
    font-weight: 600;
    font-family: var(--vscode-editor-font-family, monospace);
    color: var(--dl-primary-light);
  }
  .tool-args {
    color: var(--vscode-descriptionForeground);
    font-size: 11px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .tool-result {
    border-left: 2px solid var(--vscode-panel-border);
    margin-left: 14px;
    padding: 4px 8px;
  }
  .tool-result pre {
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
    max-height: 200px;
    overflow-y: auto;
  }
  .tool-spinner-sm {
    width: 10px;
    height: 10px;
    border: 1.5px solid var(--vscode-descriptionForeground);
    border-top-color: var(--dl-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
  }

  /* Active tool while generating */
  .active-tool-row {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 0;
    margin-bottom: 4px;
  }
  .active-tool-label {
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
  }

  /* === Content (rendered markdown) === */
  .content {
    line-height: 1.5;
    word-break: break-word;
  }
  .content :global(pre) {
    background: var(--vscode-textCodeBlock-background);
    border-radius: var(--corner-radius-medium);
    padding: 8px 12px;
    overflow-x: auto;
    margin: 8px 0;
  }
  .content :global(code) {
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: var(--vscode-editor-font-size, 12px);
  }
  .content :global(:not(pre) > code) {
    background: var(--vscode-textCodeBlock-background);
    padding: 1px 4px;
    border-radius: 3px;
  }
  .content :global(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    font-size: 12px;
  }
  .content :global(th), .content :global(td) {
    border: 1px solid var(--vscode-panel-border);
    padding: 4px 8px;
    text-align: left;
  }
  .content :global(th) {
    background: var(--vscode-editorGroupHeader-tabsBackground);
    font-weight: 600;
  }
  .content :global(p) { margin: 6px 0; }
  .content :global(p:first-child) { margin-top: 0; }
  .content :global(ul), .content :global(ol) { padding-left: 20px; margin: 4px 0; }
  .content :global(h1) { font-size: 1.3em; margin: 12px 0 6px; }
  .content :global(h2) { font-size: 1.15em; margin: 12px 0 6px; }
  .content :global(h3) { font-size: 1.05em; margin: 12px 0 6px; }
  .content :global(blockquote) {
    margin: 6px 0; padding: 4px 12px;
    border-left: 3px solid var(--vscode-focusBorder);
    color: var(--vscode-descriptionForeground);
  }
  /* Number highlights */
  .content :global(.num-highlight) {
    color: var(--dl-accent, #fb923c);
    font-weight: 600;
  }

  /* Code block copy button */
  .content :global(.code-block-wrap) {
    position: relative;
  }
  .content :global(.copy-btn) {
    position: absolute;
    top: 4px;
    right: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--vscode-descriptionForeground);
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s, background 0.15s;
    z-index: 1;
  }
  .content :global(.code-block-wrap:hover .copy-btn) {
    opacity: 0.7;
  }
  .content :global(.copy-btn:hover) {
    opacity: 1 !important;
    background: var(--vscode-toolbar-hoverBackground);
  }
  .content :global(.copy-btn.copied) {
    opacity: 1 !important;
    color: #34d399;
  }

  /* === Draft (streaming incomplete blocks) === */
  .draft {
    margin: 4px 0;
    padding: 6px 8px;
    border-radius: var(--corner-radius-small);
    background: var(--vscode-textCodeBlock-background);
    border-left: 2px solid var(--vscode-descriptionForeground);
  }
  .draft-code {
    border-left-color: var(--dl-primary);
  }
  .draft-table {
    border-left-color: var(--dl-accent);
  }
  .draft-label {
    font-size: 10px;
    color: var(--vscode-descriptionForeground);
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-bottom: 2px;
    display: block;
  }
  .draft-pre {
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: var(--vscode-editor-font-size, 12px);
    color: var(--vscode-descriptionForeground);
    margin: 0;
    white-space: pre-wrap;
    word-break: break-all;
  }

  /* Streaming cursor */
  .cursor {
    display: inline-block;
    width: 2px;
    height: 14px;
    background: var(--dl-primary);
    margin-left: 1px;
    animation: blink 1s step-end infinite;
    vertical-align: text-bottom;
  }
  @keyframes blink {
    50% { opacity: 0; }
  }

  /* === Error === */
  .error-block {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
    padding: 4px 8px;
    border-radius: var(--corner-radius-small);
    background: color-mix(in srgb, var(--dl-primary) 10%, transparent);
    color: var(--dl-primary-light);
    font-size: 12px;
  }
  .error-icon {
    color: var(--dl-primary);
    flex-shrink: 0;
  }

  /* === Footer meta === */
  .footer-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    padding-top: 4px;
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    opacity: 0.7;
  }
  .footer-sep { opacity: 0.4; }
  .footer-duration { font-family: var(--vscode-editor-font-family, monospace); }
  .footer-spacer { flex: 1; }

  /* === Action buttons (copy/regenerate) === */
  .action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--vscode-descriptionForeground);
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
  }
  .footer-meta:hover .action-btn { opacity: 0.7; }
  .action-btn:hover { opacity: 1 !important; background: var(--vscode-toolbar-hoverBackground); }

  /* === Error guide === */
  .error-guide {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    padding: 6px 8px;
    margin: 4px 0;
    border-radius: var(--corner-radius-small);
    background: var(--vscode-textCodeBlock-background);
    line-height: 1.6;
    white-space: pre-wrap;
  }
  .error-guide :global(a) { color: var(--vscode-textLink-foreground); }

  /* === Error provider switch === */
  .error-switch {
    margin-top: 6px;
    padding: 6px 8px;
    border-radius: var(--corner-radius-small);
    background: var(--vscode-textCodeBlock-background);
  }
  .error-switch-label {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    display: block;
    margin-bottom: 6px;
  }
  .error-switch-btns {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .switch-btn {
    padding: 3px 10px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 4px;
    background: transparent;
    color: var(--vscode-foreground);
    font-size: 11px;
    cursor: pointer;
  }
  .switch-btn:hover {
    background: var(--vscode-list-hoverBackground);
    border-color: var(--dl-primary);
    color: var(--dl-primary-light);
  }

</style>
