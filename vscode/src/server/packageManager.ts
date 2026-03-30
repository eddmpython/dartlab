import { execFile } from "child_process";
import * as vscode from "vscode";

/** Check if a newer dartlab version is available on PyPI. */
export async function checkPyPiVersion(): Promise<string | null> {
  try {
    const res = await fetch("https://pypi.org/pypi/dartlab/json", {
      signal: AbortSignal.timeout(5_000),
    });
    if (!res.ok) {
      return null;
    }
    const data = (await res.json()) as { info?: { version?: string } };
    return data.info?.version ?? null;
  } catch {
    return null;
  }
}

/** Install or upgrade dartlab via pip. Returns true on success. */
export async function installDartlab(
  pythonPath: string,
  upgrade: boolean = false,
): Promise<boolean> {
  const args = ["-m", "pip", "install"];
  if (upgrade) {
    args.push("--upgrade");
  }
  args.push("dartlab");

  return new Promise((resolve) => {
    const proc = execFile(
      pythonPath,
      args,
      { timeout: 120_000 },
      (err) => {
        resolve(!err);
      },
    );
    // Stream output to progress
    proc.stdout?.on("data", (data: Buffer) => {
      vscode.window.setStatusBarMessage(`DartLab: ${data.toString().trim()}`, 3000);
    });
  });
}

/** Compare semver strings. Returns true if remote > local. */
export function isNewer(local: string, remote: string): boolean {
  const parse = (v: string) => v.split(".").map(Number);
  const l = parse(local);
  const r = parse(remote);
  for (let i = 0; i < 3; i++) {
    if ((r[i] ?? 0) > (l[i] ?? 0)) {
      return true;
    }
    if ((r[i] ?? 0) < (l[i] ?? 0)) {
      return false;
    }
  }
  return false;
}
