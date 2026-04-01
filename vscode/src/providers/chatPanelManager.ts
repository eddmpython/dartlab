import * as vscode from "vscode";
import type { ExtensionMessage } from "../bridge/messageProtocol";
import { ChatWebviewBase } from "./chatWebviewBase";
import { StdioProxy } from "../bridge/stdioProxy";

/** Manages DartLab chat as an editor tab (WebviewPanel). */
export class ChatPanelManager {
  private panel?: vscode.WebviewPanel;
  private base: ChatWebviewBase;
  private sidebarRefresh?: () => void;

  constructor(
    private readonly context: vscode.ExtensionContext,
    private readonly stdioProxy: StdioProxy,
  ) {
    this.base = this.createBase();
  }

  setSidebarRefresh(fn: () => void): void {
    this.sidebarRefresh = fn;
  }

  private createBase(): ChatWebviewBase {
    return new ChatWebviewBase(
      this.context.extensionUri,
      this.stdioProxy,
      this.context.globalState,
      () => this.sidebarRefresh?.(),
    );
  }

  open(conversationId?: string): void {
    if (this.panel) {
      this.panel.reveal();
      if (conversationId) {
        this.postMessage({ type: "selectConversation", payload: { id: conversationId } });
      } else {
        this.postMessage({ type: "newConversation" });
      }
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      "dartlab.chat",
      "DartLab",
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [
          vscode.Uri.joinPath(this.context.extensionUri, "dist", "webview"),
          vscode.Uri.joinPath(this.context.extensionUri, "resources"),
        ],
      },
    );

    this.base.setup(this.panel.webview, (msg) => this.postMessage(msg));

    this.panel.iconPath = vscode.Uri.joinPath(
      this.context.extensionUri, "resources", "icon.svg",
    );

    this.panel.onDidDispose(() => {
      this.base.dispose();
      this.panel = undefined;
      this.base = this.createBase();
    });

    if (conversationId) {
      setTimeout(() => {
        this.postMessage({ type: "selectConversation", payload: { id: conversationId } });
      }, 500);
    } else {
      // New conversation requested — send after webview initializes
      setTimeout(() => {
        this.postMessage({ type: "newConversation" });
      }, 500);
    }
  }

  postMessage(msg: ExtensionMessage): void {
    this.panel?.webview.postMessage(msg);
  }
}
