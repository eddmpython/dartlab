<script lang="ts">
  import ChatPanel from "./lib/components/ChatPanel.svelte";
</script>

<ChatPanel />

<style>
  :global(:root) {
    /* DartLab brand — landing primary */
    --dl-primary: #ea4647;
    --dl-primary-dark: #c83232;
    --dl-primary-light: #f87171;
    --dl-accent: #fb923c;
    --dl-accent-light: #fdba74;
    /* layout tokens */
    --dl-spacing-xs: 4px;
    --dl-spacing-sm: 8px;
    --dl-spacing-md: 12px;
    --dl-spacing-lg: 16px;
    --dl-radius-sm: 4px;
    --dl-radius-md: 6px;
    --dl-radius-lg: 8px;
  }
  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: var(--vscode-sideBar-background);
    color: var(--vscode-editor-foreground);
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
  }
  :global(*) {
    box-sizing: border-box;
  }
  :global(a) {
    color: var(--dl-primary-light);
  }
  :global(a:hover) {
    color: var(--dl-primary);
  }
  /* scrollbar */
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
  :global(::-webkit-scrollbar-thumb:hover) {
    background: var(--vscode-scrollbarSlider-hoverBackground);
  }
</style>
