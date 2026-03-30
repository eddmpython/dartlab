import { execFile } from "child_process";
import * as vscode from "vscode";

/** Result of Python detection. */
export interface PythonInfo {
  path: string;
  version: string;
  dartlabVersion: string | null;
}

function exec(cmd: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { timeout: 10_000 }, (err, stdout) => {
      if (err) {
        reject(err);
      } else {
        resolve(stdout.trim());
      }
    });
  });
}

/** Try a single Python path. Returns PythonInfo or null. */
async function tryPython(pythonPath: string): Promise<PythonInfo | null> {
  try {
    const version = await exec(pythonPath, [
      "-c",
      "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')",
    ]);
    if (!version) {
      return null;
    }

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

/** Detect a usable Python interpreter. */
export async function detectPython(): Promise<PythonInfo | null> {
  // 1. User setting
  const configured = vscode.workspace
    .getConfiguration("dartlab")
    .get<string>("pythonPath");
  if (configured) {
    const info = await tryPython(configured);
    if (info) {
      return info;
    }
  }

  // 2. ms-python extension active interpreter
  const msPython = vscode.extensions.getExtension("ms-python.python");
  if (msPython?.isActive) {
    try {
      const api = msPython.exports;
      const envPath = api?.environments?.getActiveEnvironmentPath?.();
      if (envPath?.path) {
        const info = await tryPython(envPath.path);
        if (info) {
          return info;
        }
      }
    } catch {
      // ms-python API not available
    }
  }

  // 3. python.defaultInterpreterPath
  const defaultPath = vscode.workspace
    .getConfiguration("python")
    .get<string>("defaultInterpreterPath");
  if (defaultPath) {
    const info = await tryPython(defaultPath);
    if (info) {
      return info;
    }
  }

  // 4. PATH candidates
  const candidates =
    process.platform === "win32"
      ? ["python", "python3", "py"]
      : ["python3", "python"];

  for (const cmd of candidates) {
    const info = await tryPython(cmd);
    if (info) {
      return info;
    }
  }

  return null;
}
