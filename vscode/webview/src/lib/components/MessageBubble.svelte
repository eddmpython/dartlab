<script lang="ts">
  import type { Message } from "../api/sseHandler";
  import { createIncrementalRenderer } from "../markdown/renderer";

  interface Props {
    message: Message;
  }

  let { message }: Props = $props();
  const render = createIncrementalRenderer();

  let renderedHtml = $derived(
    message.role === "assistant" && message.text ? render(message.text) : ""
  );
</script>

<div class="message">
  {#if message.role === "user"}
    <div class="user-msg-container">
      <div class="user-msg">{message.text}</div>
    </div>
  {:else}
    {#if message.text}
      <div class="content">{@html renderedHtml}</div>
    {/if}
    {#if message.loading && !message.text}
      <div class="loading"><span></span><span></span><span></span></div>
    {/if}
  {/if}
</div>

<style>
  .message {
    color: var(--vscode-foreground);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0;
    padding: 8px 0;
    position: relative;
  }

  .user-msg-container {
    display: inline-block;
    position: relative;
    margin: 4px 0;
  }

  .user-msg {
    white-space: pre-wrap;
    word-break: break-word;
    border: 1px solid var(--vscode-input-border);
    border-radius: 6px;
    background-color: var(--vscode-input-background);
    display: inline-block;
    overflow: hidden;
    user-select: text;
    max-width: 100%;
    padding: 4px 6px;
  }

  /* assistant: no decoration at all */
  .content {
    line-height: 1.5;
    word-break: break-word;
  }
  .content :global(pre.code-block) {
    background: var(--vscode-textCodeBlock-background);
    border-radius: 6px;
    padding: 8px 12px;
    overflow-x: auto;
    margin: 8px 0;
    border: 1px solid var(--vscode-panel-border);
  }
  .content :global(code) {
    font-family: var(--vscode-editor-font-family);
    font-size: calc(var(--vscode-editor-font-size, 13px) - 1px);
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
  .content :global(th),
  .content :global(td) {
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
  .content :global(h1) { font-size: 16px; margin: 12px 0 6px; }
  .content :global(h2) { font-size: 14px; margin: 12px 0 6px; }
  .content :global(h3) { font-size: 13px; margin: 12px 0 6px; }
  .content :global(blockquote) {
    margin: 6px 0; padding: 4px 12px;
    border-left: 3px solid var(--vscode-focusBorder);
    color: var(--vscode-descriptionForeground);
  }
  .content :global(hr) {
    border: none; border-top: 1px solid var(--vscode-panel-border); margin: 12px 0;
  }
  .content :global(.num-highlight) {
    color: var(--dl-primary-light, #f87171);
    font-weight: 600;
  }

  .loading {
    display: flex;
    gap: 3px;
    padding: 4px 0;
  }
  .loading span {
    width: 4px; height: 4px; border-radius: 50%;
    background: var(--vscode-descriptionForeground);
    animation: bounce 1.2s infinite;
  }
  .loading span:nth-child(2) { animation-delay: 0.2s; }
  .loading span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
    30% { opacity: 1; transform: translateY(-3px); }
  }
</style>
