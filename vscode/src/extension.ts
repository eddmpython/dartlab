import * as vscode from "vscode";
import { DEFAULT_PORT, EXT_ID, PERIODIC_HEALTH_MS, STORAGE_KEY_CONVERSATIONS } from "./constants";
import { ProcessManager } from "./server/processManager";
import { detectPython } from "./server/pythonResolver";
import { checkPyPiVersion, installDartlab, isNewer } from "./server/packageManager";
import { findAvailablePort } from "./server/portManager";
import { ping } from "./server/healthCheck";
import { ChatPanelManager } from "./providers/chatPanelManager";
import { SidebarViewProvider } from "./providers/sidebarViewProvider";
import { registerCommands } from "./commands/index";

let processManager: ProcessManager;
let currentPort: number = DEFAULT_PORT;
let healthInterval: ReturnType<typeof setInterval> | null = null;
let statusBarItem: vscode.StatusBarItem;

export async function activate(
  context: vscode.ExtensionContext,
): Promise<void> {
  processManager = new ProcessManager();
  context.subscriptions.push({ dispose: () => processManager.dispose() });

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

  // Track server state on status bar
  processManager.onStateChange((state) => {
    switch (state) {
      case "starting":
        statusBarItem.text = "$(loading~spin) DartLab";
        statusBarItem.tooltip = "DartLab: Starting server...";
        break;
      case "ready":
        statusBarItem.text = "$(check) DartLab";
        statusBarItem.tooltip = `DartLab: Ready (port ${currentPort})`;
        break;
      case "error":
        statusBarItem.text = "$(warning) DartLab";
        statusBarItem.tooltip = "DartLab: Server error";
        break;
      case "stopped":
        statusBarItem.text = "$(circle-slash) DartLab";
        statusBarItem.tooltip = "DartLab: Stopped";
        break;
    }
  });

  // Editor tab: chat panel
  const chatPanelManager = new ChatPanelManager(
    context,
    processManager,
    () => currentPort,
  );

  // Sidebar: session list (Claude Code style)
  const sidebarProvider = SidebarViewProvider.register(context, (id?: string) => {
    chatPanelManager.open(id);
  });

  // Link panel to sidebar for refresh
  chatPanelManager.setSidebarRefresh(() => sidebarProvider.refresh());

  // Register commands
  registerCommands(context, processManager, chatPanelManager);

  // Auto-start if enabled
  const autoStart = vscode.workspace
    .getConfiguration("dartlab")
    .get<boolean>("autoStart", true);

  if (autoStart) {
    startServer(context);
  }
}

async function startServer(
  context: vscode.ExtensionContext,
): Promise<void> {
  // 1. Detect Python
  const python = await detectPython();
  if (!python) {
    statusBarItem.text = "$(error) DartLab";
    statusBarItem.tooltip = "DartLab: Python not found";
    const choice = await vscode.window.showErrorMessage(
      "DartLab requires Python 3.12+. Please install Python or configure the path.",
      "Open Settings",
    );
    if (choice === "Open Settings") {
      vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "dartlab.pythonPath",
      );
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
      vscode.window.showErrorMessage(
        "Failed to install dartlab. Check the output for details.",
      );
      return;
    }
    const updated = await detectPython();
    if (updated) python.dartlabVersion = updated.dartlabVersion;
  }

  // 3. Async update check (non-blocking)
  checkPyPiVersion().then((latestVersion) => {
    if (
      latestVersion &&
      python.dartlabVersion &&
      isNewer(python.dartlabVersion, latestVersion)
    ) {
      vscode.window
        .showInformationMessage(
          `dartlab ${latestVersion} is available (current: ${python.dartlabVersion}).`,
          "Update",
          "Later",
        )
        .then((choice) => {
          if (choice === "Update") {
            installDartlab(python.path, true).then((ok) => {
              if (ok) {
                vscode.window.showInformationMessage(
                  "dartlab updated. Restart server to apply.",
                  "Restart",
                ).then((c) => {
                  if (c === "Restart") processManager.restart();
                });
              }
            });
          }
        });
    }
  });

  // 4. Find available port
  const preferredPort = vscode.workspace
    .getConfiguration("dartlab")
    .get<number>("serverPort", DEFAULT_PORT);
  currentPort = await findAvailablePort(preferredPort);

  // 5. Start server
  const ready = await processManager.start(python.path, currentPort);
  if (ready) {
    // 6. Periodic health check
    healthInterval = setInterval(async () => {
      const alive = await ping(currentPort);
      if (!alive && processManager.state === "ready") {
        processManager.restart();
      }
    }, PERIODIC_HEALTH_MS);
    context.subscriptions.push({
      dispose: () => {
        if (healthInterval) clearInterval(healthInterval);
      },
    });
  }
}

export function deactivate(): void {
  if (healthInterval) clearInterval(healthInterval);
  processManager?.dispose();
}
