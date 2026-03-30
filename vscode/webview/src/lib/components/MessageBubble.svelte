<script lang="ts">
  import type { Message } from "../api/sseHandler";
  import { createIncrementalRenderer } from "../markdown/renderer";

  interface Props { message: Message; }
  let { message }: Props = $props();
  const render = createIncrementalRenderer();
  let html = $derived(message.role === "assistant" && message.text ? render(message.text) : "");
</script>

<!-- Claude Code: .message { padding: 8px 0; gap: 0; align-items: flex-start } -->
<div class="msg">
  {#if message.role === "user"}
    <!-- Claude Code: .userMessageContainer { display: inline-block; margin: 4px 0 } -->
    <div class="user-wrap">
      <!-- Claude Code: .userMessage { border: 1px solid input-border; border-radius: 6px; bg: input-bg; padding: 4px 6px } -->
      <div class="user-text">{message.text}</div>
    </div>
  {:else}
    {#if message.text}
      <div class="content">{@html html}</div>
    {/if}
    {#if message.loading && !message.text}
      <div class="dots"><span></span><span></span><span></span></div>
    {/if}
  {/if}
</div>

<style>
  /* exact Claude Code: .message_07S1Yg */
  .msg {
    color: var(--vscode-foreground);
    display: flex;
    position: relative;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
    padding: 8px 0;
  }
  .msg:first-child { padding-top: 0; }

  /* exact Claude Code: .userMessageContainer_07S1Yg */
  .user-wrap {
    display: inline-block;
    position: relative;
    margin: 4px 0;
  }
  .user-wrap:first-child { margin-top: 0; }

  /* exact Claude Code: .userMessage_07S1Yg */
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

  /* assistant: NO styling, just text */
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

  .dots { display: flex; gap: 3px; padding: 4px 0; }
  .dots span {
    width: 4px; height: 4px; border-radius: 50%;
    background: var(--vscode-descriptionForeground);
    animation: b 1.2s infinite;
  }
  .dots span:nth-child(2) { animation-delay: .2s; }
  .dots span:nth-child(3) { animation-delay: .4s; }
  @keyframes b {
    0%, 60%, 100% { opacity: .3; transform: translateY(0); }
    30% { opacity: 1; transform: translateY(-3px); }
  }
</style>
