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

    vscode.commands.registerCommand(CMD.diagnostics, () => {
      const out = stdioProxy.output;
      out.appendLine("");
      out.appendLine("=== DartLab 진단 정보 ===");
      out.appendLine(`상태: ${stdioProxy.state}`);
      out.appendLine(`버전: ${stdioProxy.currentVersion}`);
      const diag = stdioProxy.currentDiag;
      if (diag.python) out.appendLine(`Python: ${diag.python}`);
      if (diag.aiProvider) out.appendLine(`AI Provider: ${diag.aiProvider}`);
      if (diag.dataDir) out.appendLine(`데이터 경로: ${diag.dataDir}`);
      out.appendLine(`DART API 키: ${diag.dartKey ? "설정됨" : "미설정"}`);
      const pythonPath = vscode.workspace.getConfiguration("dartlab").get<string>("pythonPath");
      out.appendLine(`Python 경로 설정: ${pythonPath || "(자동 감지)"}`);
      out.appendLine("========================");
      out.show();
    }),
  );
}
