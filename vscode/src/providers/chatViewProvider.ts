import * as vscode from "vscode";
import { VIEW_ID } from "../constants";
import type { ExtensionMessage } from "../bridge/messageProtocol";
import { ChatWebviewBase } from "./chatWebviewBase";
import { ProcessManager } from "../server/processManager";

/** WebviewViewProvider for the DartLab sidebar chat. */
export class ChatViewProvider implements vscode.WebviewViewProvider {
  private view?: vscode.WebviewView;
  private base: ChatWebviewBase;

  constructor(
    context: vscode.ExtensionContext,
    processManager: ProcessManager,
    port: () => number,
  ) {
    this.base = new ChatWebviewBase(
      context.extensionUri,
      processManager,
      port,
      context.globalState,
    );
  }

  static register(
    context: vscode.ExtensionContext,
    processManager: ProcessManager,
    port: () => number,
  ): ChatViewProvider {
    const provider = new ChatViewProvider(context, processManager, port);
    context.subscriptions.push(
      vscode.window.registerWebviewViewProvider(VIEW_ID, provider, {
        webviewOptions: { retainContextWhenHidden: true },
      }),
    );
    return provider;
  }

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;
    this.base.setup(webviewView.webview, (msg) => this.postMessage(msg));
    webviewView.onDidDispose(() => this.base.dispose());
  }

  postMessage(msg: ExtensionMessage): void {
    this.view?.webview.postMessage(msg);
  }

  /** Focus the sidebar view. */
  focus(): void {
    if (this.view) {
      this.view.show(true);
    }
  }
}
