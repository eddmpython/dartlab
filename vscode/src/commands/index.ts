import * as vscode from "vscode";
import { CMD } from "../constants";
import { StdioProxy } from "../bridge/stdioProxy";
import { ChatPanelManager } from "../providers/chatPanelManager";

export function registerCommands(
  context: vscode.ExtensionContext,
  stdioProxy: StdioProxy,
  chatPanelManager: ChatPanelManager,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(CMD.restart, async () => {
      const pythonPath = vscode.workspace.getConfiguration("dartlab").get<string>("pythonPath") || undefined;
      const ok = await stdioProxy.restart(pythonPath);
      if (ok) vscode.window.showInformationMessage("DartLab restarted.");
    }),

    vscode.commands.registerCommand(CMD.showLogs, () => {
      stdioProxy.showLogs();
    }),

    vscode.commands.registerCommand(CMD.open, () => {
      chatPanelManager.open();
    }),

    vscode.commands.registerCommand(CMD.settings, async () => {
      await vscode.commands.executeCommand("workbench.action.openSettings", "dartlab");
    }),

    vscode.commands.registerCommand(CMD.newConversation, () => {
      chatPanelManager.open();
    }),

    vscode.commands.registerCommand(CMD.focus, () => {
      chatPanelManager.open();
    }),
  );
}
