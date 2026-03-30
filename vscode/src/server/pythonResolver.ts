import { execFile } from "child_process";
import * as vscode from "vscode";

export interface PythonInfo {
  path: string;
  version: string;
  dartlabVersion: string | null;
}

function exec(cmd: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { timeout: 10_000 }, (err, stdout) => {
      if (err) reject(err);
      else resolve(stdout.trim());
    });
  });
}

async function tryPython(pythonPath: string): Promise<PythonInfo | null> {
  try {
    const version = await exec(pythonPath, [
      "-c",
      "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')",
    ]);
    if (!version) return null;

    let dartlabVersion: string | null = null;
    try {
      dartlabVersion = await exec(pythonPath, [
        "-c",
        "import dartlab; print(dartlab.__version__)",
      ]);
    } catch {
      // dartlab not installed
    }

    return { path: pythonPath, version, dartlabVersion };
  } catch {
    return null;
  }
}

/** Detect Python using VSCode's own mechanisms. */
export async function detectPython(): Promise<PythonInfo | null> {
  // 1. User setting (explicit override)
  const configured = vscode.workspace
    .getConfiguration("dartlab")
    .get<string>("pythonPath");
  if (configured) {
    const info = await tryPython(configured);
    if (info) return info;
  }

  // 2. ms-python extension API (VSCode manages .venv automatically)
  try {
    const msPython = vscode.extensions.getExtension("ms-python.python");
    if (msPython) {
      if (!msPython.isActive) await msPython.activate();
      const api = msPython.exports;
      const workspaceFolder = vscode.workspace.workspaceFolders?.[0];

      // Try getActiveEnvironmentPath + resolveEnvironment
      const envPath = api?.environments?.getActiveEnvironmentPath?.(workspaceFolder?.uri);
      if (envPath?.path) {
        const resolved = await api.environments.resolveEnvironment?.(envPath);
        if (resolved?.path) {
          const info = await tryPython(resolved.path);
          if (info) return info;
        }
        const info = await tryPython(envPath.path);
        if (info) return info;
      }
    }
  } catch {
    // ms-python not installed or API not available
  }

  // 3. Workspace .venv direct probe (no ms-python needed)
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (workspaceFolders?.length) {
    const root = workspaceFolders[0].uri.fsPath;
    const venvPaths = process.platform === "win32"
      ? [`${root}\\.venv\\Scripts\\python.exe`]
      : [`${root}/.venv/bin/python`, `${root}/.venv/bin/python3`];

    for (const p of venvPaths) {
      const info = await tryPython(p);
      if (info) return info;
    }
  }

  // 4. PATH candidates (last resort)
  const candidates = process.platform === "win32"
    ? ["python", "python3", "py"]
    : ["python3", "python"];

  for (const cmd of candidates) {
    const info = await tryPython(cmd);
    if (info) return info;
  }

  return null;
}
