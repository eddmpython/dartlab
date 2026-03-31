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

    webviewView.webview.onDidReceiveMessage((msg: { type: string; id?: string; name?: string }) => {
      if (msg.type === "newSession") {
        this.onOpenCallback?.();
      } else if (msg.type === "openSession" && msg.id) {
        this.onOpenCallback?.(msg.id);
      } else if (msg.type === "deleteSession" && msg.id) {
        this.deleteSession(msg.id);
      } else if (msg.type === "renameSession" && msg.id && msg.name) {
        this.renameSession(msg.id, msg.name);
      }
    });
  }

  private renameSession(id: string, name: string): void {
    const state = this.globalState.get(STORAGE_KEY_CONVERSATIONS) as StoredState | undefined;
    if (!state) return;
    const conv = state.conversations.find(c => c.id === id);
    if (conv) conv.title = name;
    this.globalState.update(STORAGE_KEY_CONVERSATIONS, state);
    this.refresh();
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

    let sessionsHtml: string;
    if (state.conversations.length === 0) {
      sessionsHtml = `<div class="empty">No conversations yet</div>`;
    } else {
      // Group by time (Claude Code style)
      const now = Date.now();
      const DAY = 86400000;
      const groups: Record<string, StoredConversation[]> = {};
      const groupOrder = ["Today", "Yesterday", "This Week", "Older"];
      for (const c of state.conversations) {
        const diff = now - c.updatedAt;
        let group: string;
        if (diff < DAY) group = "Today";
        else if (diff < DAY * 2) group = "Yesterday";
        else if (diff < DAY * 7) group = "This Week";
        else group = "Older";
        (groups[group] ??= []).push(c);
      }
      sessionsHtml = groupOrder
        .filter(g => groups[g]?.length)
        .map(g => {
          const header = `<div class="group-header">${g}</div>`;
          const items = groups[g].map(c => {
            const isActive = c.id === state.activeConversationId;
            const time = formatRelativeTime(c.updatedAt);
            return `<button class="session${isActive ? " active" : ""}" data-id="${c.id}">
              <span class="name">${escapeHtml(c.title)}</span>
              <span class="meta">
                <span class="time">${time}</span>
                <span class="actions">
                  <span class="ren" data-ren="${c.id}" title="Rename">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9.5 2.5l2 2-7 7H2.5v-2z"/></svg>
                  </span>
                  <span class="del" data-del="${c.id}" title="Delete">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4l6 6M10 4l-6 6"/></svg>
                  </span>
                </span>
              </span>
            </button>`;
          }).join("");
          return header + items;
        }).join("");
    }

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
  .ren, .del { display: flex; align-items: center; cursor: pointer; padding: 2px; border-radius: 4px; color: var(--vscode-descriptionForeground); }
  .ren:hover { color: var(--vscode-foreground); }
  .del:hover { color: var(--vscode-errorForeground); }
  .empty { padding: 20px 12px; text-align: center; color: var(--vscode-descriptionForeground); font-size: 12px; }
  .group-header { padding: 6px 8px 2px; font-size: 11px; font-weight: 600; color: var(--vscode-descriptionForeground); text-transform: uppercase; letter-spacing: 0.03em; }
  .search-input {
    display: block; width: calc(100% - 16px); margin: 4px 8px; padding: 4px 8px;
    border: 1px solid var(--vscode-input-border); border-radius: 4px;
    background: var(--vscode-input-background); color: var(--vscode-input-foreground);
    font: inherit; font-size: 12px; outline: none;
  }
  .search-input:focus { border-color: var(--vscode-focusBorder); }
  .search-input::placeholder { color: var(--vscode-input-placeholderForeground); }
</style>
</head><body>
  <button class="new-btn" id="newBtn">
    <svg class="new-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="8" y1="3" x2="8" y2="13"/><line x1="3" y1="8" x2="13" y2="8"/></svg>
    새 대화
  </button>
  <input class="search-input" id="searchInput" type="text" placeholder="검색..." />
  <div class="list">${sessionsHtml}</div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    document.getElementById('newBtn').addEventListener('click', () => vscode.postMessage({ type: 'newSession' }));
    document.querySelectorAll('.session').forEach(el => {
      el.addEventListener('click', (e) => {
        if (e.target.closest('.del') || e.target.closest('.ren')) return;
        vscode.postMessage({ type: 'openSession', id: el.dataset.id });
      });
    });
    document.querySelectorAll('.ren').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        const name = prompt('세션 이름:');
        if (name && name.trim()) vscode.postMessage({ type: 'renameSession', id: el.dataset.ren, name: name.trim() });
      });
    });
    document.querySelectorAll('.del').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        vscode.postMessage({ type: 'deleteSession', id: el.dataset.del });
      });
    });
    // Search filter
    document.getElementById('searchInput').addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      document.querySelectorAll('.session').forEach(el => {
        const name = el.querySelector('.name')?.textContent?.toLowerCase() || '';
        el.style.display = name.includes(q) ? '' : 'none';
      });
      document.querySelectorAll('.group-header').forEach(el => {
        const next = [];
        let sib = el.nextElementSibling;
        while (sib && sib.classList.contains('session')) { next.push(sib); sib = sib.nextElementSibling; }
        const anyVisible = next.some(s => s.style.display !== 'none');
        el.style.display = anyVisible ? '' : 'none';
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
