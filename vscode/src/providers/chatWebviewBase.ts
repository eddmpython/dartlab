import * as vscode from "vscode";
import type { WebViewMessage, ExtensionMessage } from "../bridge/messageProtocol";
import { StdioProxy } from "../bridge/stdioProxy";
import { STORAGE_KEY_CONVERSATIONS } from "../constants";

/** Shared logic for sidebar and editor-tab webview panels. */
export class ChatWebviewBase {
  private stateListener?: vscode.Disposable;

  constructor(
    readonly extensionUri: vscode.Uri,
    readonly stdioProxy: StdioProxy,
    private readonly globalState: vscode.Memento,
    private readonly onHistoryChanged?: () => void,
  ) {}

  /** Configure a webview with scripts, html, and message handling. */
  setup(webview: vscode.Webview, postMessage: (msg: ExtensionMessage) => void): void {
    webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(this.extensionUri, "dist", "webview"),
        vscode.Uri.joinPath(this.extensionUri, "resources"),
      ],
    };

    webview.html = this.getHtml(webview);

    webview.onDidReceiveMessage((msg: unknown) => {
      const m = msg as Record<string, unknown>;
      if (m.type === "__console__") {
        this.log(`[webview:${m.level}] ${((m.args as string[]) || []).join(" ")}`);
      } else if (m.type === "log") {
        this.log(`[webview] ${m.message}`);
      } else {
        this.log(`[webview→ext] type=${m.type}`);
        this.onMessage(m as WebViewMessage, postMessage);
      }
    });

    postMessage({
      type: "serverState",
      state: this.stdioProxy.state,
    });

    this.stateListener = this.stdioProxy.onStateChange((state) => {
      postMessage({ type: "serverState", state });
    });

    // templates 이벤트를 webview에 전달
    this.stdioProxy.onTemplates = (data) => {
      const templates = (data as Record<string, unknown>).templates || [];
      postMessage({ type: "templates", payload: templates as any });
    };
  }

  private log(msg: string): void {
    this.stdioProxy.output.appendLine(msg);
  }

  dispose(): void {
    this.stateListener?.dispose();
  }

  private async onMessage(
    msg: WebViewMessage,
    postMessage: (msg: ExtensionMessage) => void,
  ): Promise<void> {
    switch (msg.type) {
      case "ask":
        this.stdioProxy.ask(
          msg.payload.question,
          msg.payload.company,
          msg.payload.history,
          {
            onEvent: (event, data) => postMessage({ type: "sseEvent", event, data }),
            onDone: () => postMessage({ type: "streamEnd" }),
            onError: (error) => postMessage({ type: "streamError", error }),
          },
          msg.payload.modules,
        );
        break;

      case "listTemplates":
        this.stdioProxy.listTemplates();
        break;

      case "stopStream":
        this.stdioProxy.cancelCurrent();
        break;

      case "openSettings":
        vscode.commands.executeCommand("workbench.action.openSettings", "dartlab");
        break;

      case "setProvider":
        this.stdioProxy.setProvider(
          msg.payload.provider,
          msg.payload.model,
          undefined,
          (data) => {
            if (data._needCredential) {
              // 키가 필요한데 없음 → webview에 needCredential 전달
              postMessage({
                type: "needCredential",
                payload: {
                  provider: data.provider as string,
                  signupUrl: data.signupUrl as string | undefined,
                  label: data.label as string | undefined,
                },
              });
            } else {
              postMessage({ type: "profile", payload: data });
            }
          },
        );
        break;

      case "requestCredential": {
        const { provider, signupUrl } = msg.payload;
        // 먼저 키 발급 페이지 열기
        if (signupUrl) {
          vscode.env.openExternal(vscode.Uri.parse(signupUrl));
        }
        // API 키 입력 다이얼로그
        const apiKey = await vscode.window.showInputBox({
          title: `${provider} API Key`,
          prompt: signupUrl
            ? `위 브라우저에서 키를 발급받고 여기에 붙여넣으세요`
            : `${provider} API 키를 입력하세요`,
          password: true,
          ignoreFocusOut: true,
        });
        if (apiKey) {
          this.stdioProxy.setProvider(
            provider,
            undefined,
            apiKey,
            (data) => postMessage({ type: "profile", payload: data }),
          );
        }
        break;
      }

      case "openExternal":
        vscode.env.openExternal(vscode.Uri.parse(msg.payload.url));
        break;

      case "syncConversations": {
        await this.globalState.update(STORAGE_KEY_CONVERSATIONS, msg.payload);
        this.onHistoryChanged?.();
        break;
      }

      case "ready": {
        postMessage({
          type: "serverState",
          state: this.stdioProxy.state,
        });
        // Restore conversations from globalState
        const saved = this.globalState.get(STORAGE_KEY_CONVERSATIONS);
        if (saved) {
          postMessage({ type: "restoreConversations", payload: saved });
        }
        // Send provider status
        this.stdioProxy.requestStatus((data) => {
          postMessage({ type: "profile", payload: data });
        });
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
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}' 'unsafe-eval'; font-src ${webview.cspSource}; img-src ${webview.cspSource};">
  <link rel="stylesheet" href="${styleUri}">
  <title>DartLab</title>
</head>
<body>
  <noscript>JavaScript is required.</noscript>
  <div id="app" data-avatar="${avatarUri}"></div>
  <script nonce="${nonce}">
    (function(){
      var vs=acquireVsCodeApi();
      window.__vscode=vs;
      var orig={log:console.log,warn:console.warn,error:console.error};
      ['log','warn','error'].forEach(function(l){
        console[l]=function(){
          orig[l].apply(console,arguments);
          try{vs.postMessage({type:'__console__',level:l,args:Array.from(arguments).map(function(a){try{return JSON.stringify(a)}catch(e){return String(a)}})})}catch(e){}
        };
      });
      window.onerror=function(m,s,l,c,e){
        vs.postMessage({type:'__console__',level:'error',args:[JSON.stringify({message:String(m),source:s,line:l,column:c,stack:e&&e.stack})]});
      };
    })();
  </script>
  <script type="module" nonce="${nonce}" src="${scriptUri}"></script>
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
