import * as vscode from "vscode";
import type { WebViewMessage, ExtensionMessage } from "../bridge/messageProtocol";
import { SseProxy } from "../bridge/sseProxy";
import { ProcessManager } from "../server/processManager";
import { STORAGE_KEY_CONVERSATIONS } from "../constants";

/** Shared logic for sidebar ChatViewProvider and editor-tab ChatPanelManager. */
export class ChatWebviewBase {
  private sseProxy = new SseProxy();
  private stateListener?: vscode.Disposable;

  constructor(
    readonly extensionUri: vscode.Uri,
    readonly processManager: ProcessManager,
    readonly port: () => number,
    private readonly globalState: vscode.Memento,
    private readonly onHistoryChanged?: () => void,
  ) {}

  /** Configure a webview (sidebar or panel) with scripts, html, and message handling. */
  setup(webview: vscode.Webview, postMessage: (msg: ExtensionMessage) => void): void {
    webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(this.extensionUri, "dist", "webview"),
        vscode.Uri.joinPath(this.extensionUri, "resources"),
      ],
    };

    webview.html = this.getHtml(webview);

    webview.onDidReceiveMessage((msg: WebViewMessage) =>
      this.onMessage(msg, postMessage),
    );

    postMessage({
      type: "serverState",
      state: this.processManager.state,
    });

    this.stateListener = this.processManager.onStateChange((state) => {
      postMessage({ type: "serverState", state });
    });
  }

  dispose(): void {
    this.sseProxy.abort();
    this.stateListener?.dispose();
  }

  private async onMessage(
    msg: WebViewMessage,
    postMessage: (msg: ExtensionMessage) => void,
  ): Promise<void> {
    const port = this.port();

    switch (msg.type) {
      case "ask":
        this.sseProxy.stream(
          port,
          {
            question: msg.payload.question,
            company: msg.payload.company,
            provider: msg.payload.provider,
            model: msg.payload.model,
            history: msg.payload.history,
          },
          {
            onEvent: (event, data) => postMessage({ type: "sseEvent", event, data }),
            onDone: () => postMessage({ type: "streamEnd" }),
            onError: (error) => postMessage({ type: "streamError", error }),
          },
        );
        break;

      case "stopStream":
        this.sseProxy.abort();
        break;

      case "search": {
        try {
          const res = await fetch(
            `http://127.0.0.1:${port}/api/search?q=${encodeURIComponent(msg.payload.query)}`,
          );
          const data = await res.json();
          postMessage({
            type: "searchResults",
            payload: (data as { results?: unknown[] }).results ?? [],
          });
        } catch {
          postMessage({ type: "searchResults", payload: [] });
        }
        break;
      }

      case "getStatus": {
        try {
          const res = await fetch(`http://127.0.0.1:${port}/api/status?probe=0`);
          const data = await res.json();
          postMessage({ type: "status", payload: data });
        } catch {
          postMessage({ type: "status", payload: null });
        }
        break;
      }

      case "getProfile": {
        try {
          const res = await fetch(`http://127.0.0.1:${port}/api/ai/profile`);
          const data = await res.json();
          postMessage({ type: "profile", payload: data });
        } catch {
          postMessage({ type: "profile", payload: null });
        }
        break;
      }

      case "updateProfile": {
        try {
          await fetch(`http://127.0.0.1:${port}/api/ai/profile`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(msg.payload),
          });
          // Re-fetch and send updated profile
          const res = await fetch(`http://127.0.0.1:${port}/api/ai/profile`);
          const data = await res.json();
          postMessage({ type: "profile", payload: data });
        } catch {
          postMessage({ type: "profile", payload: null });
        }
        break;
      }

      case "updateSecret": {
        try {
          await fetch(`http://127.0.0.1:${port}/api/ai/profile/secrets`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(msg.payload),
          });
          // Re-fetch profile to reflect new auth state
          const res = await fetch(`http://127.0.0.1:${port}/api/ai/profile`);
          const data = await res.json();
          postMessage({ type: "profile", payload: data });
        } catch {
          postMessage({ type: "profile", payload: null });
        }
        break;
      }

      case "getModels": {
        try {
          const res = await fetch(
            `http://127.0.0.1:${port}/api/models/${msg.payload.provider}`,
          );
          const data = (await res.json()) as { models?: string[] };
          postMessage({ type: "models", payload: { models: data.models ?? [] } });
        } catch {
          postMessage({ type: "models", payload: { models: [] } });
        }
        break;
      }

      case "syncConversations": {
        // WebView → Extension Host: backup conversations to globalState
        await this.globalState.update(STORAGE_KEY_CONVERSATIONS, msg.payload);
        this.onHistoryChanged?.();
        break;
      }

      case "ready": {
        postMessage({
          type: "serverState",
          state: this.processManager.state,
        });
        // Restore conversations from globalState
        const saved = this.globalState.get(STORAGE_KEY_CONVERSATIONS);
        if (saved) {
          postMessage({ type: "restoreConversations", payload: saved });
        }
        break;
      }
    }
  }

  getHtml(webview: vscode.Webview): string {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "dist", "webview", "main.js"),
    );
    const styleUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "dist", "webview", "main.css"),
    );
    const avatarUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "resources", "icon.png"),
    );
    const nonce = getNonce();

    return /* html */ `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}'; font-src ${webview.cspSource}; img-src ${webview.cspSource};">
  <link rel="stylesheet" href="${styleUri}">
  <title>DartLab</title>
</head>
<body>
  <div id="app" data-avatar="${avatarUri}"></div>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
  }
}

function getNonce(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let nonce = "";
  for (let i = 0; i < 32; i++) {
    nonce += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return nonce;
}
