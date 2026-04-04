<script lang="ts">
  import type { Message } from "../api/sseHandler";
  import * as client from "../api/client";
  import { createIncrementalRenderer } from "../markdown/renderer";
  import ChartRenderer from "../chart/ChartRenderer.svelte";

  interface Props {
    message: Message;
    isLast?: boolean;
    onregenerate?: () => void;
    oncopy?: () => void;
    onedit?: (newText: string) => void;
    onaddwatch?: (code: string, name: string) => void;
    isWatched?: boolean;
  }
  let { message, isLast = false, onregenerate, oncopy, onedit, onaddwatch, isWatched = false }: Props = $props();
  let editing = $state(false);
  let editText = $state("");
  const render = createIncrementalRenderer();

  // blocks 기반 렌더링 — displayText/split/toolPairs 불필요 (Claude Code 패턴)

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

  // Block expand/collapse (기본 접힘 — Claude Code 패턴)
  let expandedBlocks: Record<number, boolean> = $state({});
  function toggleBlock(idx: number) {
    expandedBlocks[idx] = !expandedBlocks[idx];
    expandedBlocks = { ...expandedBlocks };
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

  // finalCommittedHtml 삭제 — blocks 렌더링에서 직접 render() + wrapCodeBlocks() 호출

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

  const TOOL_LABELS: Record<string, string> = {
    companyInsights: "인사이트",
    companyFinancials: "재무제표",
    companyRatios: "재무비율",
    companyAnalysis: "분석",
    companyValuation: "밸류에이션",
    companyForecast: "전망",
    companyReview: "보고서",
    companyShow: "공시 원문",
    companyDiff: "변경 비교",
    companyGovernance: "지배구조",
    companyAudit: "감사",
    companyProfile: "프로필",
    companySections: "섹션",
    companyTopics: "토픽",
    marketScan: "시장 스캔",
    searchCompany: "검색",
  };

  function toolLabel(name: string): string {
    return TOOL_LABELS[name] || name;
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="msg" class:user={message.role === "user"} class:dot-success={!message.loading && !message.error && message.role === "assistant"} class:dot-failure={message.error} class:dot-progress={message.loading && message.role === "assistant"}>
  {#if message.role === "user"}
    <div class="user-wrap">
      {#if editing}
        <div class="user-edit">
          <textarea class="edit-area" bind:value={editText} onkeydown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); editing = false; onedit?.(editText.trim()); }
            if (e.key === "Escape") { editing = false; }
          }}></textarea>
          <div class="edit-actions">
            <button class="edit-btn save" onclick={() => { editing = false; onedit?.(editText.trim()); }}>전송</button>
            <button class="edit-btn cancel" onclick={() => { editing = false; }}>취소</button>
          </div>
        </div>
      {:else}
        <div class="user-text">{message.text}</div>
        {#if onedit}
          <button class="user-edit-btn" onclick={() => { editText = message.text; editing = true; }} title="편집">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11.5 1.5l3 3-9 9H2.5v-3z"/></svg>
          </button>
        {/if}
      {/if}
    </div>
  {:else}
    <!-- Meta badge row -->
    {#if message.meta}
      {@const meta = message.meta}
      <div class="meta-badges">
        {#if meta.company}
          <span class="badge badge-company">{meta.company}</span>
          {#if onaddwatch && meta.stockCode && !isWatched}
            <button class="watch-btn" onclick={() => onaddwatch(String(meta.stockCode), String(meta.company))} title="관심종목 추가">☆</button>
          {:else if isWatched}
            <span class="watch-btn watched" title="관심종목">★</span>
          {/if}
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

    <!-- Loading spinner (아무 content가 없을 때) -->
    {#if message.loading && (!message.blocks?.length || message.blocks.every(b => !b.text && b.type === "text"))}
      {@const lastTool = [...(message.blocks ?? [])].reverse().find(b => b.type === "tool_call" && !b.toolResult)}
      {@const lastCode = [...(message.blocks ?? [])].reverse().find(b => b.type === "code_execution" && b.status === "executing")}
      <div class="loading-block">
        <div class="spinner-row">
          <div class="spinner"></div>
          <span class="spinner-label">
            {#if lastCode}
              코드 실행 중 (라운드 {lastCode.round ?? "?"}/{lastCode.maxRounds ?? "?"})...
            {:else if lastTool?.name}
              {toolLabel(lastTool.name)} 호출 중...
            {:else if loadingPhase === "thinking"}
              분석 준비 중...
            {:else if loadingPhase === "analyzing"}
              {message.meta?.company ?? ""} 로드 중...
            {:else if loadingPhase === "snapshot"}
              핵심 수치 확인 중...
            {:else if loadingPhase === "context"}
              데이터 로드 중 ({message.contexts?.length ?? 0}개)...
            {:else}
              응답 생성 중...
            {/if}
          </span>
          {#if elapsed > 0}
            <span class="elapsed">{elapsed}s</span>
          {/if}
        </div>
      </div>
    {/if}

    <!-- ═══ Content Blocks 순회 렌더링 (Claude Code FO0 패턴) ═══ -->
    <!-- Fallback: blocks가 없으면 기존 text 렌더링 -->
    {#if (!message.blocks || message.blocks.length === 0) && message.text}
      <div class="content" onclick={copyCode}>{@html wrapCodeBlocks(render(message.text))}</div>
    {/if}
    {#each message.blocks ?? [] as block, blockIdx}

      <!-- TEXT BLOCK (code_round가 있으면 python 코드블록 제거) -->
      {#if block.type === "text" && block.text}
        {@const cleanText = block.text
          .replace(/```python\s*\n[\s\S]*?```\s*\n*/g, "")
          .replace(/```python\s*\n[\s\S]*$/g, "")
          .replace(/\n*\[실행 결과\][\s\S]*?(?=\n##|\n\n[A-Za-z가-힣]|$)/g, "")
          .trim()}
        {#if cleanText}
          <div class="content" onclick={copyCode}>{@html wrapCodeBlocks(render(cleanText))}</div>
        {/if}
      {/if}

      <!-- CODE EXECUTION BLOCK (Claude Code tool_use 패턴) -->
      {#if block.type === "code_execution"}
        {@const expanded = expandedBlocks[blockIdx] === true}
        {@const firstLine = block.code?.split('\n').find((l: string) => l.trim() && !l.trim().startsWith('#') && !l.trim().startsWith('import')) || block.code?.split('\n')[0] || ''}
        <div class="tool-block">
          <button class="tool-header" onclick={() => toggleBlock(blockIdx)}>
            <svg class="tool-chevron" class:open={expanded} width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
              <path d="M6 4l4 4-4 4"/>
            </svg>
            {#if block.status === "executing"}
              <div class="tool-spinner-sm"></div>
            {:else}
              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" class="tool-ok"><path d="M6.5 12L2 7.5l1.4-1.4L6.5 9.2l6.1-6.1L14 4.5z"/></svg>
            {/if}
            <span class="tool-args">{truncate(firstLine, 100)}</span>
            {#if block.status === "done"}
              <span class="tool-annotation">완료</span>
            {/if}
          </button>
          {#if expanded}
            <div class="tool-body">
              {#if block.code}
                <div class="tool-body-row">
                  <div class="tool-body-label">IN</div>
                  <div class="tool-body-content"><pre>{block.code}</pre></div>
                </div>
              {/if}
              {#if block.result}
                <div class="tool-body-row">
                  <div class="tool-body-label">OUT</div>
                  <div class="tool-body-content">{@html render(block.result)}</div>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/if}

      <!-- CHART BLOCK -->
      {#if block.type === "chart" && block.spec}
        <div class="chart-block">
          <ChartRenderer spec={block.spec} />
        </div>
      {/if}

      <!-- TOOL CALL BLOCK -->
      {#if block.type === "tool_call"}
        {@const expanded = expandedBlocks[blockIdx] === true}
        {@const isError = block.toolResult != null && typeof block.toolResult === "string" && (block.toolResult as string).toLowerCase().includes("error")}
        {@const toolDuration = block._ts && block._resultTs ? block._resultTs - block._ts : 0}
        <div class="tool-block">
          <button class="tool-header" onclick={() => toggleBlock(blockIdx)}>
            <svg class="tool-chevron" class:open={expanded} width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
              <path d="M6 4l4 4-4 4"/>
            </svg>
            {#if block.toolResult != null && isError}
              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" class="tool-err"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm3.5 9.1L10.1 11.5 8 9.4l-2.1 2.1-1.4-1.4L6.6 8 4.5 5.9l1.4-1.4L8 6.6l2.1-2.1 1.4 1.4L9.4 8l2.1 2.1z"/></svg>
            {:else if block.toolResult != null}
              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" class="tool-ok"><path d="M6.5 12L2 7.5l1.4-1.4L6.5 9.2l6.1-6.1L14 4.5z"/></svg>
            {:else}
              <div class="tool-spinner-sm"></div>
            {/if}
            <span class="tool-name">{toolLabel(block.name ?? "")}</span>
            <span class="tool-args">{truncate(formatToolArg(block.arguments), 60)}</span>
            {#if toolDuration > 0}
              <span class="tool-time">{(toolDuration / 1000).toFixed(1)}s</span>
            {/if}
          </button>
          {#if expanded && block.toolResult != null}
            <div class="tool-body">
              <div class="tool-body-row">
                <div class="tool-body-label">OUT</div>
                <div class="tool-body-content"><pre>{truncate(typeof block.toolResult === "string" ? block.toolResult : JSON.stringify(block.toolResult, null, 2), 2000)}</pre></div>
              </div>
            </div>
          {/if}
        </div>
      {/if}

    {/each}

    <!-- 스트리밍 커서 -->
    {#if message.loading && message.blocks?.some(b => b.type === "text" && b.text)}
      {@const lastBlock = message.blocks?.[message.blocks.length - 1]}
      {#if lastBlock?.type === "text"}
        <span class="cursor"></span>
      {:else if lastBlock?.type === "code_execution" && lastBlock.status === "executing"}
        <!-- 코드 실행 중 — 커서 안 보임 -->
      {:else}
        <span class="cursor"></span>
      {/if}
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

      {#if message.errorGuide}
        <div class="error-guide-detail">
          {@html render(message.errorGuide)}
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
              { id: "gemini", label: "Gemini" },
              { id: "groq", label: "Groq" },
              { id: "cerebras", label: "Cerebras" },
              { id: "ollama", label: "Ollama (로컬)" },
            ] as p}
              <button class="switch-btn" onclick={(e) => {
                const btn = e.currentTarget as HTMLButtonElement;
                btn.disabled = true;
                btn.textContent = p.label + " ✓";
                // 다른 버튼도 비활성화
                btn.parentElement?.querySelectorAll(".switch-btn").forEach((b) => {
                  if (b !== btn) (b as HTMLButtonElement).disabled = true;
                });
                client.setProvider(p.id);
                if (onregenerate) setTimeout(onregenerate, 800);
              }}>{p.label}</button>
            {/each}
          </div>
          <p class="error-hint">API 키 설정이 필요합니다. Ollama는 로컬에서 바로 사용 가능.</p>
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
        {#if message.text}
          {@const korean = (message.text.match(/[\uac00-\ud7af]/g) || []).length}
          {@const rest = message.text.length - korean}
          {@const tokens = Math.round(korean * 1.5 + rest / 3.5)}
          <span class="footer-sep">|</span>
          <span class="footer-tokens">~{tokens.toLocaleString()} tok</span>
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
  /* === Message container (Claude Code timeline 정밀 벤치마킹) === */
  .msg {
    color: var(--vscode-foreground);
    display: flex;
    position: relative;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
    padding: 8px 0 8px 30px;
    width: 100%;
    max-width: 100%;
    user-select: text;
  }
  .msg:first-child { padding-top: 0; }
  .msg.user { padding-left: 0; }

  /* Timeline dot (Claude Code 정확한 값: 7px, left:9px, top:15px) */
  .msg:not(.user)::before {
    content: "";
    position: absolute;
    background-color: var(--vscode-descriptionForeground);
    z-index: 1;
    border-radius: 50%;
    width: 7px;
    height: 7px;
    top: 15px;
    left: 9px;
  }
  .msg:not(.user).dot-success::before { background-color: #74c991; }
  .msg:not(.user).dot-failure::before { background-color: #c74e39; }
  /* Claude Code: 진행 중이면 dot blink (opacity 0↔1) */
  .msg:not(.user).dot-progress::before { animation: blink 1s linear infinite; }

  /* Timeline 세로선 (Claude Code: 1px, left:12px) */
  .msg:not(.user)::after {
    content: "";
    position: absolute;
    background-color: var(--vscode-sideBarActivityBarTop-border, rgba(128,128,128,0.2));
    width: 1px;
    top: 0;
    bottom: 0;
    left: 12px;
  }
  /* 첫 번째 assistant: 세로선 top을 dot 아래부터 */
  .msg:not(.user):first-of-type::after { top: 18px; }
  /* 마지막 assistant: 세로선 bottom을 dot 위까지 */
  .msg:not(.user):last-of-type::after { height: 18px; }

  /* === User message (Claude Code exact) === */
  .user-wrap {
    display: inline-block;
    position: relative;
    margin: 4px 24px 4px 0;
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

  /* === User message edit === */
  .user-edit {
    width: 100%;
  }
  .edit-area {
    width: 100%;
    min-height: 40px;
    padding: 6px 8px;
    border: 1px solid var(--dl-primary);
    border-radius: var(--corner-radius-medium);
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    font: inherit;
    resize: vertical;
  }
  .edit-actions {
    display: flex;
    gap: 4px;
    margin-top: 4px;
  }
  .edit-btn {
    padding: 2px 10px;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
  }
  .edit-btn.save { background: var(--dl-primary); color: #fff; }
  .edit-btn.cancel { background: transparent; color: var(--vscode-descriptionForeground); border: 1px solid var(--vscode-panel-border); }
  .user-edit-btn {
    position: absolute;
    top: 2px;
    right: -20px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border: none;
    border-radius: 3px;
    background: transparent;
    color: var(--vscode-descriptionForeground);
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
  }
  .user-wrap:hover .user-edit-btn { opacity: 0.6; }
  .user-edit-btn:hover { opacity: 1 !important; background: var(--vscode-toolbar-hoverBackground); }

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
  .watch-btn {
    border: none;
    background: transparent;
    color: var(--vscode-descriptionForeground);
    cursor: pointer;
    font-size: 14px;
    padding: 0 2px;
    line-height: 1;
  }
  .watch-btn:hover { color: #fbbf24; }
  .watch-btn.watched { color: #fbbf24; cursor: default; }
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

  /* === Tool events (Claude Code .toolItem pattern) === */
  .tool-section {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 8px 0;
  }
  .tool-block {
    border: 0.5px solid var(--vscode-widget-border, rgba(128,128,128,0.2));
    border-radius: 5px;
    overflow: hidden;
    background: var(--vscode-textCodeBlock-background);
  }
  .tool-header {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 4px 8px;
    border: none;
    background: none;
    color: var(--vscode-foreground);
    font: inherit;
    font-size: 13px;
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
    color: #74c991;
  }
  .tool-err {
    color: #c74e39;
  }
  /* Claude Code .toolAnnotation 패턴 */
  .tool-annotation {
    color: #74c991;
    background-color: #74c99133;
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 11px;
    margin-left: auto;
    flex-shrink: 0;
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
  .tool-time {
    color: var(--vscode-descriptionForeground);
    font-size: 10px;
    opacity: 0.6;
    margin-left: auto;
    flex-shrink: 0;
    font-family: var(--vscode-editor-font-family, monospace);
  }
  /* Claude Code .toolBody 패턴 */
  .tool-body {
    border-top: 0.5px solid var(--vscode-widget-border, rgba(128,128,128,0.15));
    display: grid;
    grid-template-columns: max-content 1fr;
  }
  .tool-body-row {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: subgrid;
    border-top: 0.5px solid var(--vscode-widget-border, rgba(128,128,128,0.1));
    padding: 4px;
  }
  .tool-body-row:first-child {
    border-top: none;
  }
  .tool-body-label {
    grid-column: 1;
    color: var(--vscode-descriptionForeground);
    opacity: 0.5;
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 0.85em;
    padding: 4px 8px 4px 4px;
    text-align: left;
  }
  .tool-body-content {
    grid-column: 2;
    white-space: pre-wrap;
    word-break: break-word;
    padding: 4px;
    max-height: 200px;
    overflow-y: auto;
    overflow-x: auto;
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 0.85em;
    color: var(--vscode-editor-foreground);
  }
  .tool-body-content pre {
    margin: 0;
    font-family: inherit;
    font-size: inherit;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .tool-body-content :global(table) {
    border-collapse: collapse;
    width: 100%;
    font-size: 12px;
  }
  .tool-body-content :global(th),
  .tool-body-content :global(td) {
    padding: 4px 8px;
    border: 0.5px solid var(--vscode-widget-border, rgba(128,128,128,0.2));
    text-align: left;
  }
  .tool-body-content :global(th) {
    background: var(--vscode-textCodeBlock-background);
    font-weight: 600;
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

  /* === Content (rendered markdown -- polished) === */
  .content {
    line-height: 1.6;
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
  /* Table -- clean, readable, scrollable */
  .content :global(table) {
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    width: max-content;
    min-width: 100%;
    margin: 10px 0;
    font-size: 12px;
    display: block;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
  }
  .content :global(th), .content :global(td) {
    border-bottom: 1px solid var(--vscode-panel-border);
    border-right: 1px solid color-mix(in srgb, var(--vscode-panel-border) 40%, transparent);
    padding: 7px 14px;
    text-align: left;
    white-space: nowrap;
  }
  .content :global(th:last-child), .content :global(td:last-child) {
    border-right: none;
  }
  .content :global(td) {
    font-family: var(--vscode-editor-font-family, monospace);
    font-size: 11.5px;
  }
  .content :global(th) {
    background: var(--vscode-editorGroupHeader-tabsBackground);
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.03em;
    position: sticky;
    top: 0;
    z-index: 1;
    border-bottom: 2px solid var(--vscode-panel-border);
  }
  .content :global(tr:nth-child(even) td) {
    background: color-mix(in srgb, var(--vscode-editorGroupHeader-tabsBackground) 40%, transparent);
  }
  .content :global(tr:hover td) {
    background: var(--vscode-list-hoverBackground);
  }
  .content :global(.table-wrap) {
    position: relative;
    margin: 10px 0;
  }
  .content :global(.table-dl-btn) {
    position: absolute;
    top: -2px;
    right: 4px;
    padding: 1px 6px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 3px;
    background: var(--vscode-editorWidget-background);
    color: var(--vscode-descriptionForeground);
    font-size: 10px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
    z-index: 2;
  }
  .content :global(.table-wrap:hover .table-dl-btn) {
    opacity: 0.7;
  }
  .content :global(.table-dl-btn:hover) {
    opacity: 1 !important;
    border-color: var(--dl-primary);
    color: var(--dl-primary-light);
  }
  .content :global(p) { margin: 8px 0; }
  .content :global(p:first-child) { margin-top: 0; }
  .content :global(ul), .content :global(ol) { padding-left: 20px; margin: 4px 0; }
  .content :global(h1) { font-size: 1.4em; margin: 16px 0 8px; padding-bottom: 4px; border-bottom: 1px solid var(--vscode-panel-border); }
  .content :global(h2) { font-size: 1.2em; margin: 14px 0 6px; padding-bottom: 3px; border-bottom: 1px solid var(--vscode-panel-border); }
  .content :global(h3) { font-size: 1.05em; margin: 12px 0 6px; font-weight: 600; }
  .content :global(blockquote) {
    margin: 8px 0; padding: 6px 14px;
    border-left: 3px solid var(--dl-primary, #ea4647);
    background: color-mix(in srgb, var(--vscode-textCodeBlock-background) 50%, transparent);
    color: var(--vscode-descriptionForeground);
    border-radius: 0 4px 4px 0;
  }
  .content :global(strong) { color: var(--vscode-foreground); }
  .content :global(hr) { border: none; border-top: 1px solid var(--vscode-panel-border); margin: 12px 0; }

  /* Code fold (details/summary) */
  .content :global(.code-fold) {
    margin: 8px 0;
    border: 1px solid var(--vscode-panel-border);
    border-radius: var(--corner-radius-medium);
    overflow: hidden;
  }
  .content :global(.code-fold-summary) {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 6px 10px;
    background: var(--vscode-textCodeBlock-background);
    cursor: pointer;
    font-size: 12px;
    user-select: none;
    list-style: none;
  }
  .content :global(.code-fold-summary::-webkit-details-marker) { display: none; }
  .content :global(.code-fold[open] .code-fold-icon) { transform: rotate(90deg); }
  .content :global(.code-fold-icon) { transition: transform 0.15s; color: var(--vscode-descriptionForeground); }
  .content :global(.code-fold-label) { font-weight: 600; color: var(--dl-primary-light, #f87171); font-family: var(--vscode-editor-font-family, monospace); }
  .content :global(.code-fold-hint) { color: var(--vscode-descriptionForeground); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .content :global(.code-fold pre) { margin: 0; border-radius: 0; border-left: none; }
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

  /* Code writing spinner (hide code while streaming) */
  .code-writing {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    margin: 6px 0;
    border-radius: var(--corner-radius-medium);
    background: var(--vscode-textCodeBlock-background);
    border-left: 3px solid var(--dl-primary, #ea4647);
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
  }

  /* Inline code execution indicator */
  .inline-exec {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 8px;
    margin: 4px 0;
    border-radius: var(--corner-radius-small);
    background: var(--vscode-textCodeBlock-background);
    font-size: 12px;
    color: var(--dl-accent, #fb923c);
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
  .footer-tokens { font-family: var(--vscode-editor-font-family, monospace); opacity: 0.6; }
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

  .error-guide-detail {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    padding: 8px 10px;
    margin: 4px 0;
    border-radius: var(--corner-radius-small);
    background: var(--vscode-inputValidation-infoBackground, rgba(0, 100, 200, 0.08));
    border-left: 2px solid var(--vscode-textLink-foreground);
    line-height: 1.6;
    white-space: pre-wrap;
  }
  .error-guide-detail :global(a) { color: var(--vscode-textLink-foreground); }
  .error-guide-detail :global(code) {
    background: var(--vscode-textCodeBlock-background);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 11px;
  }

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
  .error-hint {
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    margin: 6px 0 0;
    opacity: 0.7;
  }

</style>
