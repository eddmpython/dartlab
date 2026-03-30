<script lang="ts">
  import ChatPanel from "./lib/components/ChatPanel.svelte";
</script>

<ChatPanel />

<style>
  :global(:root) {
    /* DartLab brand (replaces Claude orange) */
    --dl-primary: #ea4647;
    --dl-primary-dark: #c83232;
    --dl-primary-light: #f87171;
    --dl-accent: #fb923c;
    /* Claude Code layout tokens */
    --corner-radius-small: 4px;
    --corner-radius-medium: 6px;
    --corner-radius-large: 8px;
    --app-spacing-small: 4px;
    --app-spacing-medium: 8px;
    --app-spacing-large: 12px;
  }
  :global(html) {
    display: flex;
    overscroll-behavior: none;
    position: relative;
    flex: 1;
    height: 100%;
  }
  :global(body) {
    display: flex;
    overscroll-behavior: none;
    font-size: var(--vscode-chat-font-size, 13px);
    font-family: var(--vscode-chat-font-family);
    flex: 1;
    max-width: 100%;
    margin: 0;
    padding: 0;
  }
  :global(#app) {
    display: flex;
    flex: 1;
    max-width: 100%;
  }
  :global(*) {
    box-sizing: border-box;
  }
  :global(a) {
    color: var(--vscode-textLink-foreground);
  }
  :global(::-webkit-scrollbar) {
    width: 6px;
  }
  :global(::-webkit-scrollbar-track) {
    background: transparent;
  }
  :global(::-webkit-scrollbar-thumb) {
    background: var(--vscode-scrollbarSlider-background);
    border-radius: 3px;
  }
</style>
