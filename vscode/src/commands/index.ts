import * as vscode from "vscode";
import { CMD } from "../constants";
import { ProcessManager } from "../server/processManager";
import { ChatPanelManager } from "../providers/chatPanelManager";

export function registerCommands(
  context: vscode.ExtensionContext,
  processManager: ProcessManager,
  chatPanelManager: ChatPanelManager,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(CMD.restart, async () => {
      const ok = await processManager.restart();
      if (ok) vscode.window.showInformationMessage("DartLab server restarted.");
    }),

    vscode.commands.registerCommand(CMD.showLogs, () => {
      processManager.showLogs();
    }),

    vscode.commands.registerCommand(CMD.open, () => {
      chatPanelManager.open();
    }),

    vscode.commands.registerCommand(CMD.settings, async () => {
      await vscode.commands.executeCommand("workbench.action.openSettings", "dartlab");
    }),
  );
}
