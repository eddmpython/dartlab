import * as vscode from "vscode";
import { EXT_ID } from "./constants";
import { StdioProxy } from "./bridge/stdioProxy";
import { detectPython } from "./server/pythonResolver";
import { checkPyPiVersion, installDartlab, isNewer } from "./server/packageManager";
import { ChatPanelManager } from "./providers/chatPanelManager";
import { SidebarViewProvider } from "./providers/sidebarViewProvider";
import { registerCommands } from "./commands/index";

let stdioProxy: StdioProxy;
let statusBarItem: vscode.StatusBarItem;

export async function activate(
  context: vscode.ExtensionContext,
): Promise<void> {
  stdioProxy = new StdioProxy();
  context.subscriptions.push({ dispose: () => stdioProxy.dispose() });

  // Status bar
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100,
  );
  statusBarItem.command = `${EXT_ID}.showLogs`;
  statusBarItem.text = "$(loading~spin) DartLab";
  statusBarItem.tooltip = "DartLab: Starting...";
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // Track state on status bar
  stdioProxy.onStateChange((state) => {
    switch (state) {
      case "starting":
        statusBarItem.text = "$(loading~spin) DartLab";
        statusBarItem.tooltip = "DartLab: Starting...";
        break;
      case "ready":
        statusBarItem.text = "$(check) DartLab";
        statusBarItem.tooltip = "DartLab: Ready";
        break;
      case "error":
        statusBarItem.text = "$(warning) DartLab";
        statusBarItem.tooltip = "DartLab: Error";
        break;
      case "stopped":
        statusBarItem.text = "$(circle-slash) DartLab";
        statusBarItem.tooltip = "DartLab: Stopped";
        break;
    }
  });

  // Editor tab: chat panel
  const chatPanelManager = new ChatPanelManager(context, stdioProxy);

  // Sidebar: session list
  const sidebarProvider = SidebarViewProvider.register(context, (id?: string) => {
    chatPanelManager.open(id);
  });
  chatPanelManager.setSidebarRefresh(() => sidebarProvider.refresh());

  // Register commands
  registerCommands(context, stdioProxy, chatPanelManager);

  // Auto-register MCP server for Claude Code / Codex / Copilot
  ensureMcpConfig();

  // Auto-start
  const autoStart = vscode.workspace
    .getConfiguration("dartlab")
    .get<boolean>("autoStart", true);

  if (autoStart) {
    startProcess(context);
  }
}

/** Auto-register dartlab MCP server. */
async function ensureMcpConfig(): Promise<void> {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders?.length) return;

  const root = workspaceFolders[0].uri;
  const dartlabEntry = {
    command: "uv",
    args: ["run", "python", "-X", "utf8", "-m", "dartlab.mcp"],
  };

  await ensureMcpFile(
    vscode.Uri.joinPath(root, ".mcp.json"),
    "mcpServers",
    dartlabEntry,
  );

  const vscodeDirUri = vscode.Uri.joinPath(root, ".vscode");
  try { await vscode.workspace.fs.createDirectory(vscodeDirUri); } catch { /* exists */ }
  await ensureMcpFile(
    vscode.Uri.joinPath(root, ".vscode", "mcp.json"),
    "servers",
    dartlabEntry,
  );
}

async function ensureMcpFile(
  uri: vscode.Uri,
  serversKey: string,
  entry: Record<string, unknown>,
): Promise<void> {
  try {
    const raw = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString("utf8");
    const config = JSON.parse(raw);
    if (config?.[serversKey]?.dartlab) return;
    config[serversKey] = config[serversKey] ?? {};
    config[serversKey].dartlab = entry;
    await vscode.workspace.fs.writeFile(uri, Buffer.from(JSON.stringify(config, null, 2), "utf8"));
  } catch {
    const config = { [serversKey]: { dartlab: entry } };
    await vscode.workspace.fs.writeFile(uri, Buffer.from(JSON.stringify(config, null, 2), "utf8"));
  }
}

async function startProcess(
  context: vscode.ExtensionContext,
): Promise<void> {
  // 1. Detect Python
  const python = await detectPython();
  if (!python) {
    statusBarItem.text = "$(error) DartLab";
    statusBarItem.tooltip = "DartLab: Python not found";
    const choice = await vscode.window.showErrorMessage(
      "DartLab requires Python 3.12+.",
      "Open Settings",
    );
    if (choice === "Open Settings") {
      vscode.commands.executeCommand("workbench.action.openSettings", "dartlab.pythonPath");
    }
    return;
  }

  // 2. Check dartlab installation
  if (!python.dartlabVersion) {
    const choice = await vscode.window.showInformationMessage(
      "dartlab is not installed. Install now?",
      "Install",
      "Cancel",
    );
    if (choice !== "Install") return;
    const ok = await installDartlab(python.path);
    if (!ok) {
      vscode.window.showErrorMessage("Failed to install dartlab.");
      return;
    }
  }

  // 3. Async update check
  checkPyPiVersion().then((latestVersion) => {
    if (latestVersion && python.dartlabVersion && isNewer(python.dartlabVersion, latestVersion)) {
      vscode.window
        .showInformationMessage(
          `dartlab ${latestVersion} available (current: ${python.dartlabVersion}).`,
          "Update",
          "Later",
        )
        .then((choice) => {
          if (choice === "Update") {
            installDartlab(python.path, true);
          }
        });
    }
  });

  // 4. Start stdio process
  const ready = await stdioProxy.start(python.path);
  if (!ready) {
    vscode.window
      .showErrorMessage("DartLab failed to start.", "Show Logs", "Retry")
      .then((choice) => {
        if (choice === "Show Logs") stdioProxy.showLogs();
        else if (choice === "Retry") startProcess(context);
      });
  }
}

export function deactivate(): void {
  stdioProxy?.dispose();
}
