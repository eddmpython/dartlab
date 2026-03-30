<script lang="ts">
  import MessageBubble from "./MessageBubble.svelte";
  import ChatInput from "./ChatInput.svelte";
  import WelcomeView from "./WelcomeView.svelte";
  import ChatHeader from "./ChatHeader.svelte";
  import { createMessageId, createSseHandler, type Message } from "../api/sseHandler";
  import * as client from "../api/client";
  import { onMessage, getState, setState } from "../vscode";

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

  // Restore state
  const saved = getState<PanelState>();
  let conversations: Conversation[] = $state(saved?.conversations ?? []);
  let activeConversationId: string | null = $state(saved?.activeConversationId ?? null);

  let serverState = $state("starting");
  let streaming = $state(false);
  let messagesEl: HTMLDivElement | undefined = $state();

  let currentHandler: ReturnType<typeof createSseHandler> | null = null;

  let messages = $derived(
    conversations.find(c => c.id === activeConversationId)?.messages ?? []
  );

  function persist() {
    const state: PanelState = { conversations, activeConversationId };
    setState(state);
    // Backup to Extension Host globalState
    client.syncConversations(state);
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function newConversation(): string {
    const conv: Conversation = {
      id: createMessageId(),
      title: "New conversation",
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    conversations = [conv, ...conversations];
    activeConversationId = conv.id;
    persist();
    return conv.id;
  }

  function updateActiveMessages(msgs: Message[]) {
    const idx = conversations.findIndex(c => c.id === activeConversationId);
    if (idx < 0) return;
    conversations[idx] = { ...conversations[idx], messages: msgs, updatedAt: Date.now() };
    // Auto-title
    if (!conversations[idx].title || conversations[idx].title === "New conversation") {
      const first = msgs.find(m => m.role === "user");
      if (first) {
        conversations[idx].title = first.text.slice(0, 40) + (first.text.length > 40 ? "..." : "");
      }
    }
    conversations = [...conversations];
    persist();
  }

  function updateTitleFromMeta(meta: Record<string, unknown>) {
    const idx = conversations.findIndex(c => c.id === activeConversationId);
    if (idx < 0) return;
    const company = meta.company as string | undefined;
    if (company && conversations[idx].title === "New conversation") {
      conversations[idx].title = `${company} analysis`;
      conversations = [...conversations];
      persist();
    }
  }

  function selectConversation(id: string) {
    if (streaming) return;
    activeConversationId = id;
    persist();
    scrollToBottom();
  }

  function deleteConversation(id: string) {
    conversations = conversations.filter(c => c.id !== id);
    if (activeConversationId === id) {
      activeConversationId = conversations[0]?.id ?? null;
    }
    persist();
  }

  function handleNewChat() {
    if (streaming) return;
    newConversation();
      }

  function handleSubmit(text: string) {
    if (!activeConversationId) newConversation();
    
    const currentMessages = [...messages];

    const userMsg: Message = {
      id: createMessageId(),
      role: "user",
      text,
      loading: false,
      error: false,
    };
    currentMessages.push(userMsg);

    const assistantMsg: Message = {
      id: createMessageId(),
      role: "assistant",
      text: "",
      loading: true,
      error: false,
      startedAt: Date.now(),
    };
    currentMessages.push(assistantMsg);

    streaming = true;
    updateActiveMessages(currentMessages);
    scrollToBottom();

    const history = currentMessages
      .slice(0, -2)
      .filter(m => m.text)
      .map(m => ({ role: m.role, text: m.text }));

    currentHandler = createSseHandler(
      () => {
        const msgs = conversations.find(c => c.id === activeConversationId)?.messages ?? [];
        return msgs[msgs.length - 1];
      },
      (patch) => {
        const conv = conversations.find(c => c.id === activeConversationId);
        if (!conv) return;
        const msgs = [...conv.messages];
        const last = msgs.length - 1;
        msgs[last] = { ...msgs[last], ...patch };
        updateActiveMessages(msgs);
        scrollToBottom();
      },
      () => {
        streaming = false;
        currentHandler = null;
        persist();
      },
    );

    client.ask(text, undefined, history);
  }

  function handleStop() {
    client.stopStream();
    streaming = false;
  }

  function handleSlashCommand(cmd: string) {
    switch (cmd) {
      case "settings":
      case "model":
      case "provider":
        // TODO: open settings via Extension Host command
        break;
      case "new":
        handleNewChat();
        break;
      case "clear":
        if (activeConversationId) deleteConversation(activeConversationId);
        break;
      case "resume":
        // Trigger history dropdown in header -- dispatch custom event
        window.dispatchEvent(new CustomEvent("dartlab:openHistory"));
        break;
      case "help": {
        // Show help as a system message
        if (!activeConversationId) newConversation();
        const helpText = [
          "**Available commands:**",
          "- `/model` -- Change AI model",
          "- `/provider` -- Change AI provider",
          "- `/settings` -- Open AI settings panel",
          "- `/resume` -- Resume a past conversation",
          "- `/new` -- Start new conversation",
          "- `/clear` -- Clear current conversation",
          "- `/help` -- Show this help",
        ].join("\n");
        const helpMsg: Message = {
          id: createMessageId(),
          role: "assistant",
          text: helpText,
          loading: false,
          error: false,
        };
        const conv = conversations.find(c => c.id === activeConversationId);
        if (conv) updateActiveMessages([...conv.messages, helpMsg]);
        break;
      }
    }
  }

  // Extension Host messages
  onMessage((msg: unknown) => {
    const m = msg as Record<string, unknown>;
    switch (m.type) {
      case "sseEvent":
        currentHandler?.handleEvent(m.event as string, m.data);
        // Update title from meta event
        if (m.event === "meta" && m.data) {
          updateTitleFromMeta(m.data as Record<string, unknown>);
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
        if (payload.id) selectConversation(payload.id);
        break;
      }
    }
  });

  client.ready();
</script>

<div class="chat-panel">
  <ChatHeader {serverState} />

  {#if messages.length === 0}
    <WelcomeView {serverState} onsubmit={handleSubmit} />
  {:else}
    <div class="messages" bind:this={messagesEl}>
      {#each messages as message (message.id)}
        <MessageBubble {message} />
      {/each}
    </div>
  {/if}

  <ChatInput
    disabled={serverState !== "ready"}
    {streaming}
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
    overflow: hidden;
  }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 8px 20px 40px;
  }
</style>
