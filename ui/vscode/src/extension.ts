import * as vscode from "vscode";
import { EXT_ID } from "./constants";
import { StdioProxy } from "./bridge/stdioProxy";
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

  stdioProxy.onStateChange((state) => {
    switch (state) {
      case "starting":
        statusBarItem.text = "$(loading~spin) DartLab";
        statusBarItem.tooltip = "DartLab: Starting...";
        break;
      case "ready": {
        statusBarItem.text = "$(check) DartLab";
        const diag = stdioProxy.currentDiag;
        const pyVer = diag.python ? `, Python ${diag.python}` : "";
        const prov = diag.aiProvider && diag.aiProvider !== "none" ? `, ${diag.aiProvider}` : "";
        statusBarItem.tooltip = `DartLab: Ready (v${stdioProxy.currentVersion}${pyVer}${prov})`;
        checkForUpdate(context, stdioProxy.currentVersion);
        break;
      }
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

  const chatPanelManager = new ChatPanelManager(context, stdioProxy);
  const sidebarProvider = SidebarViewProvider.register(context, (id?: string) => {
    chatPanelManager.open(id);
  });
  chatPanelManager.setSidebarRefresh(() => sidebarProvider.refresh());
  registerCommands(context, stdioProxy, chatPanelManager);

  // Auto-register MCP
  ensureMcpConfig();

  // Auto-start
  if (vscode.workspace.getConfiguration("dartlab").get<boolean>("autoStart", true)) {
    // pythonPath 설정이 있으면 그걸 쓰고, 없으면 uv run (undefined)
    const pythonPath = vscode.workspace.getConfiguration("dartlab").get<string>("pythonPath") || undefined;
    const ready = await stdioProxy.start(pythonPath);
    if (ready) {
      // 첫 실행 시 provider 미설정이면 안내
      const shownKey = "dartlab.providerGuideShown";
      if (!context.globalState.get<boolean>(shownKey)) {
        const diag = stdioProxy.currentDiag;
        if (!diag.aiProvider || diag.aiProvider === "none") {
          context.globalState.update(shownKey, true);
          vscode.window.showInformationMessage(
            "DartLab 시작됨. AI 분석을 사용하려면 provider를 설정하세요.",
            "설정 열기",
          ).then((c) => {
            if (c) vscode.commands.executeCommand(`${EXT_ID}.settings`);
          });
        }
      }
    }
  }
}

async function ensureMcpConfig(): Promise<void> {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders?.length) return;

  const root = workspaceFolders[0].uri;
  const entry = {
    command: "uv",
    args: ["run", "python", "-X", "utf8", "-m", "dartlab.mcp"],
  };

  await writeMcpEntry(vscode.Uri.joinPath(root, ".mcp.json"), "mcpServers", entry);

  const vscodeDir = vscode.Uri.joinPath(root, ".vscode");
  try { await vscode.workspace.fs.createDirectory(vscodeDir); } catch { /* exists */ }
  await writeMcpEntry(vscode.Uri.joinPath(root, ".vscode", "mcp.json"), "servers", entry);
}

async function writeMcpEntry(
  uri: vscode.Uri,
  key: string,
  entry: Record<string, unknown>,
): Promise<void> {
  try {
    const raw = Buffer.from(await vscode.workspace.fs.readFile(uri)).toString("utf8");
    const cfg = JSON.parse(raw);
    if (cfg?.[key]?.dartlab) return;
    cfg[key] = cfg[key] ?? {};
    cfg[key].dartlab = entry;
    await vscode.workspace.fs.writeFile(uri, Buffer.from(JSON.stringify(cfg, null, 2), "utf8"));
  } catch {
    await vscode.workspace.fs.writeFile(
      uri,
      Buffer.from(JSON.stringify({ [key]: { dartlab: entry } }, null, 2), "utf8"),
    );
  }
}

const LAST_UPDATE_CHECK_KEY = "dartlab.lastUpdateCheck";
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

async function checkForUpdate(context: vscode.ExtensionContext, currentVersion: string): Promise<void> {
  if (!currentVersion || currentVersion === "unknown") return;

  const lastCheck = context.globalState.get<number>(LAST_UPDATE_CHECK_KEY, 0);
  if (Date.now() - lastCheck < ONE_DAY_MS) return;
  await context.globalState.update(LAST_UPDATE_CHECK_KEY, Date.now());

  try {
    const resp = await fetch("https://pypi.org/pypi/dartlab/json");
    if (!resp.ok) return;
    const data = await resp.json() as { info: { version: string } };
    const latest = data.info.version;
    if (!latest || latest === currentVersion) return;

    // 자동 업데이트: 백그라운드 터미널에서 uv pip install
    const terminal = vscode.window.createTerminal({ name: "DartLab Update", hideFromUser: true });
    terminal.sendText("uv pip install --upgrade dartlab && exit");
    vscode.window.showInformationMessage(`dartlab ${latest}으로 업데이트 중... (현재 ${currentVersion})`);

    // 업데이트 완료 후 dartlab 프로세스 재시작
    const disposable = vscode.window.onDidCloseTerminal((t) => {
      if (t === terminal) {
        disposable.dispose();
        stdioProxy.restart();
        vscode.window.showInformationMessage(`dartlab ${latest} 업데이트 완료. 재시작됨.`);
      }
    });
  } catch {
    // 네트워크 에러 무시
  }
}

export function deactivate(): void {
  stdioProxy?.dispose();
}
