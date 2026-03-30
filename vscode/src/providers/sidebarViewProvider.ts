import * as vscode from "vscode";
import { SIDEBAR_VIEW_ID, STORAGE_KEY_CONVERSATIONS } from "../constants";

interface StoredConversation {
  id: string;
  title: string;
  updatedAt: number;
}

interface StoredState {
  conversations: StoredConversation[];
  activeConversationId: string | null;
}

/** Sidebar WebView showing session list (Claude Code style). */
export class SidebarViewProvider implements vscode.WebviewViewProvider {
  private view?: vscode.WebviewView;
  private onOpenCallback?: (id?: string) => void;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly globalState: vscode.Memento,
  ) {}

  static register(
    context: vscode.ExtensionContext,
    onOpen: (id?: string) => void,
  ): SidebarViewProvider {
    const provider = new SidebarViewProvider(context.extensionUri, context.globalState);
    provider.onOpenCallback = onOpen;
    context.subscriptions.push(
      vscode.window.registerWebviewViewProvider(SIDEBAR_VIEW_ID, provider, {
        webviewOptions: { retainContextWhenHidden: true },
      }),
    );
    return provider;
  }

  refresh(): void {
    if (!this.view) return;
    this.view.webview.html = this.getHtml(this.view.webview);
  }

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;
    webviewView.webview.options = { enableScripts: true };
    webviewView.webview.html = this.getHtml(webviewView.webview);

    webviewView.webview.onDidReceiveMessage((msg: { type: string; id?: string }) => {
      if (msg.type === "newSession") {
        this.onOpenCallback?.();
      } else if (msg.type === "openSession" && msg.id) {
        this.onOpenCallback?.(msg.id);
      } else if (msg.type === "deleteSession" && msg.id) {
        this.deleteSession(msg.id);
      }
    });
  }

  private deleteSession(id: string): void {
    const state = this.globalState.get(STORAGE_KEY_CONVERSATIONS) as StoredState | undefined;
    if (!state) return;
    state.conversations = state.conversations.filter(c => c.id !== id);
    if (state.activeConversationId === id) {
      state.activeConversationId = state.conversations[0]?.id ?? null;
    }
    this.globalState.update(STORAGE_KEY_CONVERSATIONS, state);
    this.refresh();
  }

  private getState(): StoredState {
    return (this.globalState.get(STORAGE_KEY_CONVERSATIONS) as StoredState) ?? {
      conversations: [],
      activeConversationId: null,
    };
  }

  private getHtml(_webview: vscode.Webview): string {
    const state = this.getState();
    const nonce = getNonce();

    const sessionsHtml = state.conversations.length === 0
      ? `<div class="empty">No conversations yet</div>`
      : state.conversations.map(c => {
          const isActive = c.id === state.activeConversationId;
          const time = formatRelativeTime(c.updatedAt);
          return `<button class="session${isActive ? " active" : ""}" data-id="${c.id}">
            <span class="name">${escapeHtml(c.title)}</span>
            <span class="meta">
              <span class="time">${time}</span>
              <span class="actions">
                <span class="del" data-del="${c.id}" title="Delete">
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4l6 6M10 4l-6 6"/></svg>
                </span>
              </span>
            </span>
          </button>`;
        }).join("");

    return `<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';">
<style nonce="${nonce}">
  body { margin: 0; padding: 0; font-family: var(--vscode-font-family); font-size: var(--vscode-font-size); color: var(--vscode-foreground); }
  .new-btn {
    display: flex; align-items: center; gap: 6px;
    width: 100%; padding: 10px 12px;
    border: none; border-bottom: 1px solid var(--vscode-panel-border);
    background: transparent; color: var(--vscode-foreground);
    font: inherit; font-weight: 500; cursor: pointer;
  }
  .new-btn:hover { background: var(--vscode-list-hoverBackground); }
  .new-icon { width: 16px; height: 16px; }
  .list { display: flex; flex-direction: column; gap: 2px; padding: 0; }
  .session {
    display: flex; align-items: center; gap: 8px;
    width: 100%; height: 28px; padding: 0 8px;
    border: none; border-radius: 6px;
    background: transparent; color: var(--vscode-foreground);
    font: inherit; cursor: pointer; text-align: left;
  }
  .session:hover { background: var(--vscode-list-hoverBackground); }
  .session.active { background: var(--vscode-list-activeSelectionBackground); color: var(--vscode-list-activeSelectionForeground); }
  .session.active .name { font-weight: 600; }
  .name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .meta { display: grid; place-items: center end; flex-shrink: 0; margin-left: auto; }
  .time { opacity: 0.7; font-size: 0.9em; grid-area: 1/1; }
  .actions { grid-area: 1/1; display: flex; gap: 2px; visibility: hidden; }
  .session:hover .time { visibility: hidden; }
  .session:hover .actions { visibility: visible; }
  .del { display: flex; align-items: center; cursor: pointer; padding: 2px; border-radius: 4px; color: var(--vscode-descriptionForeground); }
  .del:hover { color: var(--vscode-errorForeground); }
  .empty { padding: 20px 12px; text-align: center; color: var(--vscode-descriptionForeground); font-size: 12px; }
</style>
</head><body>
  <button class="new-btn" id="newBtn">
    <svg class="new-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="8" y1="3" x2="8" y2="13"/><line x1="3" y1="8" x2="13" y2="8"/></svg>
    New Session
  </button>
  <div class="list">${sessionsHtml}</div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    document.getElementById('newBtn').addEventListener('click', () => vscode.postMessage({ type: 'newSession' }));
    document.querySelectorAll('.session').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target.closest('.del')) return;
        vscode.postMessage({ type: 'openSession', id: el.dataset.id });
      });
    });
    document.querySelectorAll('.del').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        vscode.postMessage({ type: 'deleteSession', id: el.dataset.del });
      });
    });
  </script>
</body></html>`;
  }
}

function getNonce(): string {
  const c = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let n = "";
  for (let i = 0; i < 32; i++) n += c.charAt(Math.floor(Math.random() * c.length));
  return n;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function formatRelativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const min = Math.floor(diff / 60000);
  if (min < 1) return "now";
  if (min < 60) return `${min}m`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h`;
  const d = Math.floor(hr / 24);
  return `${d}d`;
}
