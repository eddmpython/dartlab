<script lang="ts">
  import MessageBubble from "./MessageBubble.svelte";
  import ChatInput from "./ChatInput.svelte";
  import ChatHeader from "./ChatHeader.svelte";
  import { createMessageId, createSseHandler, type Message } from "../api/sseHandler";
  import * as client from "../api/client";
  import { onMessage, getState, setState, postMessage } from "../vscode";

  interface Conversation {
    id: string;
    title: string;
    messages: Message[];
    createdAt: number;
    updatedAt: number;
  }

  interface PanelState {
    conversations: Conversation[];
    activeConversationId: string | null;
  }

  const saved = getState<PanelState>();
  let conversations: Conversation[] = $state(saved?.conversations ?? []);
  let activeConversationId: string | null = $state(saved?.activeConversationId ?? null);
  let serverState = $state("starting");
  let providerLabel = $state("");
  let modelLabel = $state("");
  let providers: Array<{id: string; label: string; freeTier: string}> = $state([]);
  let streaming = $state(false);
  let availableTemplates: Array<{ name: string; description: string; source: "builtin" | "user" }> = $state([]);
  let messagesEl: HTMLDivElement | undefined = $state();
  let currentHandler: ReturnType<typeof createSseHandler> | null = null;

  // Watchlist (favorite stocks)
  let watchlist: Array<{code: string; name: string}> = $state(
    JSON.parse(localStorage.getItem("dartlab-watchlist") || "[]")
  );
  function addToWatchlist(code: string, name: string) {
    if (watchlist.some(w => w.code === code)) return;
    watchlist = [...watchlist, { code, name }];
    localStorage.setItem("dartlab-watchlist", JSON.stringify(watchlist));
  }
  function removeFromWatchlist(code: string) {
    watchlist = watchlist.filter(w => w.code !== code);
    localStorage.setItem("dartlab-watchlist", JSON.stringify(watchlist));
  }

  // Scroll tracking
  let showJumpToLatest = $state(false);
  let followStream = $state(true);

  let messages = $derived(
    conversations.find(c => c.id === activeConversationId)?.messages ?? []
  );

  function persist() {
    const state: PanelState = { conversations, activeConversationId };
    setState(state);
    client.syncConversations(state);
  }

  function scrollToBottom() {
    if (!followStream) return;
    requestAnimationFrame(() => {
      if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function jumpToLatest() {
    followStream = true;
    showJumpToLatest = false;
    requestAnimationFrame(() => {
      if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function handleScroll() {
    if (!messagesEl) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesEl;
    const nearBottom = scrollHeight - scrollTop - clientHeight < 96;
    followStream = nearBottom;
    showJumpToLatest = !nearBottom && messages.length > 3;
  }

  function getConv(): Conversation | undefined {
    return conversations.find(c => c.id === activeConversationId);
  }

  function ensureConversation(): string {
    if (activeConversationId && getConv()) return activeConversationId;
    const id = createMessageId();
    conversations = [{
      id,
      title: "New conversation",
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }, ...conversations];
    activeConversationId = id;
    persist();
    return id;
  }

  let persistTimer: ReturnType<typeof setTimeout> | null = null;
  function debouncedPersist() {
    if (persistTimer) clearTimeout(persistTimer);
    persistTimer = setTimeout(() => { persistTimer = null; persist(); }, 500);
  }

  function updateMessages(convId: string, msgs: Message[]) {
    const idx = conversations.findIndex(c => c.id === convId);
    if (idx < 0) return;
    const conv = conversations[idx];
    conv.messages = msgs;
    conv.updatedAt = Date.now();
    if (conv.title === "New conversation") {
      const first = msgs.find(m => m.role === "user");
      if (first) conv.title = first.text.slice(0, 40) + (first.text.length > 40 ? "..." : "");
    }
    conversations = [...conversations];
    debouncedPersist();
  }

  function handleSubmit(text: string, modules?: string[]) {
    // Guard: prevent double submit
    if (streaming) return;
    streaming = true;

    const convId = ensureConversation();
    const conv = conversations.find(c => c.id === convId);
    if (!conv) { streaming = false; return; }

    const msgs = [...conv.messages];
    msgs.push({ id: createMessageId(), role: "user", text, loading: false, error: false });
    msgs.push({ id: createMessageId(), role: "assistant", text: "", loading: true, error: false, startedAt: Date.now() });

    const history = msgs.slice(0, -2).filter(m => m.text).map(m => ({ role: m.role, text: m.text }));

    // Set up handler BEFORE updating messages (which triggers re-render)
    currentHandler = createSseHandler(
      () => {
        const c = conversations.find(c => c.id === convId);
        return c?.messages[c.messages.length - 1] ?? { id: "", role: "assistant" as const, text: "", loading: true, error: false };
      },
      (patch) => {
        const c = conversations.find(c => c.id === convId);
        if (!c) return;
        const m = [...c.messages];
        m[m.length - 1] = { ...m[m.length - 1], ...patch };
        updateMessages(convId, m);
        scrollToBottom();
      },
      () => {
        streaming = false;
        currentHandler = null;
        persist();
      },
    );

    // Send ask BEFORE updating UI (so message goes out immediately)
    client.ask(text, text, history, modules);

    // Now update UI
    followStream = true;
    updateMessages(convId, msgs);
    scrollToBottom();
  }

  function handleRegenerate() {
    if (streaming) return;
    const conv = getConv();
    if (!conv || conv.messages.length < 2) return;
    // Find last user message
    const lastUserIdx = [...conv.messages].reverse().findIndex(m => m.role === "user");
    if (lastUserIdx < 0) return;
    const lastUser = conv.messages[conv.messages.length - 1 - lastUserIdx];
    // Remove last assistant message
    const msgs = conv.messages.slice(0, conv.messages.length - 1 - lastUserIdx);
    updateMessages(conv.id, msgs);
    handleSubmit(lastUser.text);
  }

  function handleEditResend(msgIndex: number, newText: string) {
    if (streaming || !newText) return;
    const conv = getConv();
    if (!conv) return;
    // Keep messages up to (not including) the edited message, then resubmit
    const msgs = conv.messages.slice(0, msgIndex);
    updateMessages(conv.id, msgs);
    handleSubmit(newText);
  }

  function handleCopyResponse() {
    const conv = getConv();
    if (!conv) return;
    const lastAssistant = [...conv.messages].reverse().find(m => m.role === "assistant" && m.text);
    if (lastAssistant) navigator.clipboard.writeText(lastAssistant.text);
  }

  function handleStop() {
    client.stopStream();
    streaming = false;
    currentHandler = null;
  }

  function handleSlashCommand(cmd: string) {
    if (cmd === "new") {
      if (!streaming) { activeConversationId = null; ensureConversation(); }
    } else if (cmd === "clear") {
      if (activeConversationId) {
        conversations = conversations.filter(c => c.id !== activeConversationId);
        activeConversationId = conversations[0]?.id ?? null;
        persist();
      }
    } else if (cmd === "help") {
      const convId = ensureConversation();
      const conv = conversations.find(c => c.id === convId)!;
      updateMessages(convId, [...conv.messages, {
        id: createMessageId(), role: "assistant",
        text: "**명령어:** `/new` 새 대화 · `/clear` 대화 삭제 · `/help` 도움말\n\n**단축키:**\n- `Enter` 전송 · `Shift+Enter` 줄바꿈\n- `Escape` 응답 중단\n- `Ctrl+Shift+D` 패널 열기\n\n종목코드(005930) 또는 회사명을 입력하세요.",
        loading: false, error: false,
      }]);
    }
  }

  onMessage((msg: unknown) => {
    const m = msg as Record<string, unknown>;
    switch (m.type) {
      case "sseEvent":
        currentHandler?.handleEvent(m.event as string, m.data);
        if (m.event === "meta" && m.data) {
          const company = (m.data as Record<string, unknown>).company as string | undefined;
          if (company && activeConversationId) {
            const conv = getConv();
            if (conv && conv.title === "New conversation") {
              conv.title = company;
              conversations = [...conversations];
              persist();
            }
          }
        }
        break;
      case "streamEnd":
        currentHandler?.handleStreamEnd();
        break;
      case "streamError":
        currentHandler?.handleStreamError(m.error as string);
        break;
      case "serverState":
        serverState = m.state as string;
        break;
      case "profile": {
        const p = m.payload as Record<string, unknown> | null;
        if (p?.provider) providerLabel = String(p.provider);
        if (p?.model) modelLabel = String(p.model);
        if (Array.isArray(p?.providers)) providers = p.providers as typeof providers;
        break;
      }
      case "restoreConversations": {
        const restored = m.payload as PanelState | null;
        if (restored && conversations.length === 0) {
          conversations = restored.conversations ?? [];
          activeConversationId = restored.activeConversationId ?? null;
          setState<PanelState>({ conversations, activeConversationId });
        }
        break;
      }
      case "selectConversation": {
        const payload = m.payload as { id: string };
        if (payload.id && !streaming) {
          activeConversationId = payload.id;
          persist();
          jumpToLatest();
        }
        break;
      }
      case "newConversation": {
        if (!streaming) {
          activeConversationId = null;
          ensureConversation();
        }
        break;
      }
      case "templates": {
        const payload = m.payload as Array<{ name: string; description: string; source: "builtin" | "user" }>;
        if (Array.isArray(payload)) {
          availableTemplates = payload;
        }
        break;
      }
    }
  });

  client.ready();
  // 시작 시 템플릿 목록 요청
  client.listTemplates();
</script>

<div class="chat-panel">
  <ChatHeader {serverState} {providerLabel} {modelLabel} {providers} />

  {#if messages.length === 0 && !streaming}
    {@const avatarSrc = document.getElementById("app")?.dataset.avatar ?? ""}
    <div class="welcome">
      {#if avatarSrc}
        <img src={avatarSrc} alt="DartLab" width="56" height="56" class="welcome-avatar" />
      {/if}
      <h2 class="welcome-title">DartLab</h2>
      <p class="welcome-text">종목코드 또는 회사명을 입력하세요</p>
      {#if !providerLabel || providerLabel === "none"}
        <div class="welcome-setup">
          <p class="welcome-setup-label">무료로 시작하기</p>
          <div class="welcome-setup-btns">
            {#each [
              { id: "gemini", label: "Gemini" },
              { id: "groq", label: "Groq" },
              { id: "cerebras", label: "Cerebras" },
            ] as p}
              <button class="setup-btn" onclick={() => client.setProvider(p.id)}>{p.label}</button>
            {/each}
          </div>
        </div>
      {:else}
        <p class="welcome-sub">예: 005930, 삼성전자, AAPL</p>
        {#if watchlist.length > 0}
          <div class="watchlist">
            <span class="watchlist-label">관심종목</span>
            <div class="watchlist-items">
              {#each watchlist as w}
                <button class="watchlist-btn" onclick={() => handleSubmit(`${w.code} 종합분석`)}>
                  <span class="wl-name">{w.name}</span>
                  <span class="wl-code">{w.code}</span>
                </button>
              {/each}
            </div>
          </div>
        {/if}
      {/if}
    </div>
  {/if}

  <div class="messages-wrap">
    <div class="messages" bind:this={messagesEl} onscroll={handleScroll}>
      {#each messages as message, i (message.id)}
        <MessageBubble
          {message}
          isLast={i === messages.length - 1}
          onregenerate={i === messages.length - 1 && !message.loading && message.role === "assistant" ? handleRegenerate : undefined}
          oncopy={i === messages.length - 1 && !message.loading && message.role === "assistant" ? handleCopyResponse : undefined}
          onedit={!streaming && message.role === "user" ? (newText) => handleEditResend(i, newText) : undefined}
          onaddwatch={message.role === "assistant" && message.meta?.stockCode ? addToWatchlist : undefined}
          isWatched={!!message.meta?.stockCode && watchlist.some(w => w.code === String(message.meta?.stockCode))}
        />
      {/each}
    </div>

    {#if showJumpToLatest}
      <button class="jump-btn" onclick={jumpToLatest}>
        <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 12l-4-4h8z"/></svg>
        Latest
      </button>
    {/if}
  </div>

  <ChatInput
    disabled={serverState !== "ready"}
    {streaming}
    templates={availableTemplates}
    onsubmit={handleSubmit}
    onstop={handleStop}
    oncommand={handleSlashCommand}
  />
</div>

<style>
  .chat-panel {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100%;
    overflow: hidden;
  }
  .welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: 24px 16px;
    text-align: center;
  }
  .welcome-avatar {
    border-radius: 50%;
    margin-bottom: 12px;
    box-shadow: 0 0 20px rgba(234, 70, 71, 0.15);
  }
  .welcome-title {
    margin: 0 0 8px;
    font-size: 20px;
    font-weight: 700;
    color: var(--vscode-editor-foreground);
  }
  .welcome-text {
    font-size: 13px;
    color: var(--vscode-descriptionForeground);
    margin: 0 0 6px;
  }
  .welcome-sub {
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    opacity: 0.6;
    margin: 0;
  }
  .watchlist {
    margin-top: 12px;
  }
  .watchlist-label {
    font-size: 11px;
    color: var(--vscode-descriptionForeground);
    display: block;
    margin-bottom: 6px;
  }
  .watchlist-items {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .watchlist-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    background: transparent;
    color: var(--vscode-foreground);
    font-size: 12px;
    cursor: pointer;
  }
  .watchlist-btn:hover {
    background: var(--vscode-list-hoverBackground);
    border-color: var(--dl-primary);
  }
  .wl-name { font-weight: 500; }
  .wl-code { font-size: 10px; color: var(--vscode-descriptionForeground); font-family: var(--vscode-editor-font-family); }
  .welcome-setup {
    margin-top: 12px;
    padding: 10px 16px;
    border-radius: 8px;
    background: var(--vscode-editorWidget-background);
    border: 1px solid var(--vscode-panel-border);
  }
  .welcome-setup-label {
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    margin: 0 0 8px;
  }
  .welcome-setup-btns {
    display: flex;
    gap: 6px;
  }
  .setup-btn {
    padding: 5px 14px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 6px;
    background: transparent;
    color: var(--vscode-foreground);
    font-size: 12px;
    cursor: pointer;
  }
  .setup-btn:hover {
    background: var(--vscode-list-hoverBackground);
    border-color: var(--dl-primary);
  }
  .messages-wrap {
    flex: 1;
    position: relative;
    overflow: hidden;
    min-height: 0;
  }
  .messages {
    height: 100%;
    overflow-y: auto;
    padding: 12px 16px 40px;
    width: 100%;
  }
  .jump-btn {
    position: absolute;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border: 1px solid var(--vscode-panel-border);
    border-radius: 12px;
    background: var(--vscode-editorWidget-background);
    color: var(--vscode-foreground);
    font-size: 11px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,.3);
    z-index: 10;
  }
  .jump-btn:hover {
    background: var(--vscode-list-hoverBackground);
  }
</style>
