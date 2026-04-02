/**
 * StdioProxy -- dartlab CLI child process + JSON Lines protocol.
 * Claude Code / Codex pattern: spawn + stdin/stdout.
 * Auto-restart with exponential backoff + healthcheck.
 * Fallback chain: uv run → python -m dartlab → dartlab CLI.
 */

import { ChildProcess, spawn } from "child_process";
import { createInterface, Interface } from "readline";
import * as vscode from "vscode";
import { OUTPUT_CHANNEL_NAME } from "../constants";

export type ServerState = "stopped" | "starting" | "ready" | "error";
type StateListener = (state: ServerState) => void;

export interface StdioCallbacks {
  onEvent: (event: string, data: unknown) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

const MAX_RESTARTS = 3;
const BACKOFF_BASE_MS = 1_000;
const HEALTH_INTERVAL_MS = 60_000;
const HEALTH_TIMEOUT_MS = 10_000;
const READY_TIMEOUT_MS = 30_000;

/** Command candidates to spawn dartlab chat --stdio. */
interface SpawnCandidate {
  cmd: string;
  args: string[];
  label: string;
}

interface FailedAttempt {
  label: string;
  reason: string;
}

export function buildCandidates(pythonPath?: string): SpawnCandidate[] {
  const candidates: SpawnCandidate[] = [];

  // 1. Explicit python path
  if (pythonPath) {
    candidates.push({
      cmd: pythonPath,
      args: ["-X", "utf8", "-m", "dartlab", "chat", "--stdio"],
      label: `${pythonPath} -m dartlab`,
    });
  }

  // 2. uv run (in uv-managed projects)
  candidates.push({
    cmd: "uv",
    args: ["run", "python", "-X", "utf8", "-m", "dartlab", "chat", "--stdio"],
    label: "uv run python -m dartlab",
  });

  // 3. python -m dartlab (pip installed)
  for (const py of ["python", "python3"]) {
    candidates.push({
      cmd: py,
      args: ["-X", "utf8", "-m", "dartlab", "chat", "--stdio"],
      label: `${py} -m dartlab`,
    });
  }

  // 4. dartlab CLI entry point (pip install dartlab)
  candidates.push({
    cmd: "dartlab",
    args: ["chat", "--stdio"],
    label: "dartlab chat --stdio",
  });

  return candidates;
}

export class StdioProxy {
  private proc: ChildProcess | null = null;
  private rl: Interface | null = null;
  private _state: ServerState = "stopped";
  private listeners: StateListener[] = [];
  readonly output: vscode.OutputChannel;
  private disposed = false;

  // Request routing
  private currentCallbacks: StdioCallbacks | null = null;
  private currentRequestId: string | null = null;
  private statusListeners: Array<(data: Record<string, unknown>) => void> = [];
  private providerListeners: Array<(data: Record<string, unknown>) => void> = [];
  onTemplates?: (data: Record<string, unknown>) => void;
  onOAuthResult?: (data: Record<string, unknown>) => void;
  currentVersion = "unknown";

  // Auto-restart
  private restartCount = 0;
  private lastPythonPath?: string;
  private lastWorkingCandidate?: SpawnCandidate;
  private healthTimer: ReturnType<typeof setInterval> | null = null;
  private stderrBuffer = "";

  constructor() {
    this.output = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
  }

  get state(): ServerState { return this._state; }

  onStateChange(fn: StateListener): vscode.Disposable {
    this.listeners.push(fn);
    return new vscode.Disposable(() => {
      this.listeners = this.listeners.filter(l => l !== fn);
    });
  }

  private setState(s: ServerState) {
    this._state = s;
    for (const fn of this.listeners) fn(s);
  }

  // Diagnostic tracking
  private failedAttempts: FailedAttempt[] = [];
  currentDiag: Record<string, unknown> = {};

  /** Start dartlab chat --stdio, trying multiple spawn candidates. */
  async start(pythonPath?: string): Promise<boolean> {
    if (this.disposed) return false;
    this.lastPythonPath = pythonPath;
    this.failedAttempts = [];
    this.setState("starting");

    // If we have a previously working candidate, try it first
    if (this.lastWorkingCandidate) {
      const ok = await this.trySpawn(this.lastWorkingCandidate);
      if (ok) return true;
      this.lastWorkingCandidate = undefined;
    }

    // Try each candidate
    const candidates = buildCandidates(pythonPath);
    for (const candidate of candidates) {
      const ok = await this.trySpawn(candidate);
      if (ok) {
        this.lastWorkingCandidate = candidate;
        return true;
      }
    }

    // All candidates failed — build diagnostic message
    this.setState("error");
    this.output.appendLine("");
    this.output.appendLine("=== DartLab 시작 실패 진단 ===");
    for (const attempt of this.failedAttempts) {
      this.output.appendLine(`  ${attempt.label}: ${attempt.reason}`);
    }
    this.output.appendLine("");
    this.output.appendLine("해결 방법:");
    this.output.appendLine("  1. dartlab 설치: pip install dartlab (또는 uv pip install dartlab)");
    this.output.appendLine("  2. Python 3.12 이상 필요");
    this.output.appendLine("  3. 설정 > dartlab.pythonPath에 Python 경로 직접 지정 가능");
    this.output.appendLine("========================");

    const failureType = this.classifyPrimaryFailure();
    const primaryReason = this.diagnosePrimaryFailureMessage(failureType);

    if (failureType === "not_installed" || failureType === "upgrade_needed") {
      // 자동 설치/업그레이드 제안
      const action = failureType === "not_installed" ? "자동 설치" : "자동 업그레이드";
      vscode.window.showErrorMessage(
        `DartLab 시작 실패: ${primaryReason}`,
        action, "로그 보기",
      ).then((c) => {
        if (c === action) this.autoInstallAndRestart(failureType === "upgrade_needed");
        else if (c === "로그 보기") this.showLogs();
      });
    } else if (failureType === "no_python") {
      vscode.window.showErrorMessage(
        `DartLab 시작 실패: ${primaryReason}`,
        "Python 설치", "로그 보기",
      ).then((c) => {
        if (c === "Python 설치") vscode.env.openExternal(vscode.Uri.parse("https://www.python.org/downloads/"));
        else if (c === "로그 보기") this.showLogs();
      });
    } else {
      vscode.window.showErrorMessage(
        `DartLab 시작 실패: ${primaryReason}`,
        "로그 보기",
      ).then((c) => { if (c) this.showLogs(); });
    }
    return false;
  }

  /** Auto-install dartlab and restart server. */
  private autoInstallAndRestart(upgrade: boolean): void {
    const installCmd = this.pickInstallCommand(upgrade);
    this.output.appendLine(`[DartLab] 자동 설치 시작: ${installCmd}`);
    this.setState("starting");

    const terminal = vscode.window.createTerminal({ name: "DartLab Install", hideFromUser: false });
    terminal.show();
    // PowerShell 5.x는 && 미지원 → ; 사용
    const sep = process.platform === "win32" ? " ; " : " && ";
    terminal.sendText(`${installCmd}${sep}exit`);

    const disposable = vscode.window.onDidCloseTerminal((t) => {
      if (t !== terminal) return;
      disposable.dispose();
      this.output.appendLine("[DartLab] 설치 완료 — 재시작 시도");
      this.restartCount = 0;
      this.lastWorkingCandidate = undefined;
      this.start(this.lastPythonPath);
    });
  }

  /** Choose install command based on what's available. */
  private pickInstallCommand(upgrade: boolean): string {
    const flag = upgrade ? " --upgrade" : "";
    // uv가 후보에서 ENOENT가 아니었으면 uv 사용
    const uvFailed = this.failedAttempts.find(a => a.label.startsWith("uv "));
    if (uvFailed && !uvFailed.reason.includes("찾을 수 없음")) {
      return `uv pip install${flag} dartlab`;
    }
    // python이 있으면 pip 사용
    const pyFailed = this.failedAttempts.find(a => a.label.startsWith("python "));
    if (pyFailed && !pyFailed.reason.includes("찾을 수 없음")) {
      return `python -m pip install${flag} dartlab`;
    }
    // fallback
    return `pip install${flag} dartlab`;
  }

  /** Classify the primary failure type. */
  private classifyPrimaryFailure(): "not_installed" | "upgrade_needed" | "no_python" | "unknown" {
    const reasons = this.failedAttempts.map(a => a.reason);
    if (reasons.some(r => r.includes("미설치"))) return "not_installed";
    if (reasons.some(r => r.includes("업그레이드"))) return "upgrade_needed";
    if (reasons.every(r => r.includes("찾을 수 없음"))) return "no_python";
    return "unknown";
  }

  private diagnosePrimaryFailureMessage(type: string): string {
    switch (type) {
      case "not_installed": return "dartlab 패키지 미설치";
      case "upgrade_needed": return "dartlab 업그레이드 필요";
      case "no_python": return "Python을 찾을 수 없음 — Python 3.12+ 설치 필요";
      default: return "dartlab 서버를 시작할 수 없음 — 로그를 확인하세요";
    }
  }

  /** Try spawning a single candidate. Returns true if ready signal received. */
  private async trySpawn(candidate: SpawnCandidate): Promise<boolean> {
    this.stderrBuffer = "";
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    this.output.appendLine(`[DartLab] trying: ${candidate.label} (cwd: ${cwd ?? "none"})`);

    // Clean up previous attempt
    if (this.proc) {
      try { this.proc.kill("SIGKILL"); } catch { /* ignore */ }
      this.proc = null;
    }
    if (this.rl) {
      this.rl.close();
      this.rl = null;
    }

    try {
      this.proc = spawn(candidate.cmd, candidate.args, {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env },
        ...(cwd ? { cwd } : {}),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      this.output.appendLine(`[DartLab] spawn failed: ${msg}`);
      this.failedAttempts.push({ label: candidate.label, reason: this.classifyError(msg, "") });
      return false;
    }

    // Collect stderr
    this.proc.stderr?.on("data", (data: Buffer) => {
      const text = data.toString();
      this.output.append(text);
      this.stderrBuffer = (this.stderrBuffer + text).slice(-2048);
    });

    // Handle immediate exit (wrong command, module not found, etc.)
    let exited = false;
    const exitPromise = new Promise<number>((resolve) => {
      this.proc!.on("exit", (code) => {
        exited = true;
        resolve(code ?? -1);
      });
      this.proc!.on("error", (err) => {
        this.output.appendLine(`[DartLab] error: ${err.message}`);
        exited = true;
        resolve(-1);
      });
    });

    // Set up readline
    if (!this.proc.stdout) {
      this.output.appendLine("[DartLab] no stdout");
      return false;
    }
    this.rl = createInterface({ input: this.proc.stdout, crlfDelay: Infinity });

    // Wait for ready signal OR process exit
    const ready = await Promise.race([
      this.waitForReady(),
      exitPromise.then(() => false),
      new Promise<false>((resolve) => setTimeout(() => resolve(false), READY_TIMEOUT_MS)),
    ]);

    if (ready) {
      this.output.appendLine(`[DartLab] ready via: ${candidate.label}`);
      this.restartCount = 0;
      this.setupExitHandler();
      this.startHealthCheck();
      this.setState("ready");
      return true;
    }

    // Failed -- clean up and record diagnosis
    const lastStderr = this.stderrBuffer.trim();
    this.output.appendLine(`[DartLab] failed: ${candidate.label} (stderr: ${lastStderr.split("\n").pop() ?? ""})`);
    this.failedAttempts.push({ label: candidate.label, reason: this.classifyError("", lastStderr) });
    if (!exited) {
      try { this.proc?.kill("SIGKILL"); } catch { /* ignore */ }
    }
    this.proc = null;
    if (this.rl) { this.rl.close(); this.rl = null; }
    return false;
  }

  /** Classify spawn failure into a Korean diagnostic reason. */
  private classifyError(spawnError: string, stderr: string): string {
    const combined = spawnError + " " + stderr;
    if (combined.includes("ENOENT")) return "명령어를 찾을 수 없음 (Python/uv 미설치)";
    if (combined.includes("No module named dartlab.__main__")) return "dartlab 업그레이드 필요 — pip install -U dartlab";
    if (combined.includes("No module named dartlab")) return "dartlab 패키지 미설치";
    if (combined.includes("No module named")) return `모듈 없음: ${combined.match(/No module named (\S+)/)?.[1] ?? ""}`;
    if (combined.includes("SyntaxError")) return "Python 버전 불일치 (3.12+ 필요)";
    if (combined.includes("Permission")) return "권한 오류";
    if (!spawnError && !stderr.trim()) return "응답 대기 시간 초과 (30초)";
    return stderr.trim().split("\n").pop()?.slice(0, 120) ?? "알 수 없는 오류";
  }

  private waitForReady(): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      const onLine = (line: string) => {
        this.output.appendLine(`[stdout] ${line.slice(0, 200)}`);
        try {
          const msg = JSON.parse(line);
          if (msg.event === "ready") {
            const d = msg.data ?? {};
            this.currentVersion = d.version ?? "unknown";
            this.currentDiag = d;
            this.output.appendLine(`[DartLab] 진단: Python ${d.python ?? "?"}, provider=${d.aiProvider ?? "?"}, dartKey=${d.dartKey ?? "?"}`);
            this.rl?.removeListener("line", onLine);
            this.rl?.on("line", (l) => this.handleLine(l));
            resolve(true);
          }
        } catch { /* non-JSON, ignore */ }
      };
      this.rl!.on("line", onLine);
    });
  }

  private setupExitHandler(): void {
    this.proc?.removeAllListeners("exit");
    this.proc?.removeAllListeners("error");

    this.proc?.on("exit", (code) => {
      if (this.disposed) return;
      this.output.appendLine(`[DartLab] process exited: code=${code}`);
      this.rl = null;
      this.proc = null;
      this.stopHealthCheck();

      // Notify current request
      if (this.currentCallbacks) {
        this.currentCallbacks.onError("Process exited unexpectedly");
        this.currentCallbacks.onDone();
        this.currentCallbacks = null;
        this.currentRequestId = null;
      }

      // Auto-restart with backoff
      if (this.restartCount < MAX_RESTARTS) {
        this.restartCount++;
        const delay = BACKOFF_BASE_MS * Math.pow(2, this.restartCount - 1);
        this.output.appendLine(`[DartLab] auto-restart ${this.restartCount}/${MAX_RESTARTS} in ${delay}ms`);
        this.setState("starting");
        setTimeout(() => {
          if (!this.disposed) this.start(this.lastPythonPath);
        }, delay);
      } else {
        this.setState("error");
        vscode.window.showErrorMessage(
          "DartLab process crashed. Check logs.",
          "Show Logs", "Retry",
        ).then((c) => {
          if (c === "Show Logs") this.showLogs();
          else if (c === "Retry") { this.restartCount = 0; this.start(this.lastPythonPath); }
        });
      }
    });
  }

  // --- Healthcheck ---

  private startHealthCheck(): void {
    this.stopHealthCheck();
    this.healthTimer = setInterval(() => this.ping(), HEALTH_INTERVAL_MS);
  }

  private stopHealthCheck(): void {
    if (this.healthTimer) { clearInterval(this.healthTimer); this.healthTimer = null; }
  }

  private _pongCallback: (() => void) | null = null;

  private ping(): void {
    if (this._state !== "ready" || !this.proc?.stdin?.writable) return;
    // Don't ping while a request is in progress (code execution can take 60s+)
    if (this.currentCallbacks) return;
    const timeout = setTimeout(() => {
      // Double-check: still no active request?
      if (this.currentCallbacks) { clearTimeout(timeout); return; }
      this.output.appendLine("[DartLab] healthcheck timeout -- killing process");
      this.proc?.kill("SIGKILL");
    }, HEALTH_TIMEOUT_MS);
    this._pongCallback = () => clearTimeout(timeout);
    this.send({ type: "ping" });
  }

  // --- Communication ---

  private send(msg: Record<string, unknown>): void {
    if (!this.proc?.stdin?.writable) return;
    this.proc.stdin.write(JSON.stringify(msg) + "\n");
  }

  private handleLine(line: string): void {
    this.output.appendLine(`[stdout] ${line.slice(0, 200)}`);
    let msg: Record<string, unknown>;
    try { msg = JSON.parse(line); } catch { return; }

    const event = msg.event as string;
    const data = msg.data as Record<string, unknown>;
    const id = msg.id as string | undefined;

    if (event === "pong") { this._pongCallback?.(); this._pongCallback = null; return; }
    if (event === "status") { for (const fn of this.statusListeners) fn(data); this.statusListeners = []; return; }
    if (event === "providerChanged") { for (const fn of this.providerListeners) fn(data); this.providerListeners = []; return; }
    if (event === "needCredential") { for (const fn of this.providerListeners) fn({ ...data, _needCredential: true }); this.providerListeners = []; return; }
    if (event === "oauthStart") { for (const fn of this.providerListeners) fn({ ...data, _oauthStart: true }); this.providerListeners = []; return; }
    if (event === "oauthResult") { this.onOAuthResult?.(data); return; }
    if (event === "templates") { this.onTemplates?.(data); return; }

    if (this.currentCallbacks) {
      if (event === "done") {
        // Always honor done — even if id mismatches (prevent stuck state)
        this.currentCallbacks.onEvent(event, data);
        this.currentCallbacks.onDone();
        this.currentCallbacks = null;
        this.currentRequestId = null;
      } else if (!id || id === this.currentRequestId) {
        this.currentCallbacks.onEvent(event, data);
      }
    }
  }

  // --- Public API ---

  requestStatus(callback: (data: Record<string, unknown>) => void): void {
    this.statusListeners.push(callback);
    this.send({ type: "status" });
    setTimeout(() => { this.statusListeners = this.statusListeners.filter(l => l !== callback); }, 5000);
  }

  setProvider(provider: string, model?: string, apiKey?: string, callback?: (data: Record<string, unknown>) => void): void {
    if (callback) this.providerListeners.push(callback);
    const msg: Record<string, unknown> = { type: "setProvider", provider, model };
    if (apiKey) msg.apiKey = apiKey;
    this.send(msg);
  }

  ask(question: string, company: string | undefined, history: unknown[] | undefined, callbacks: StdioCallbacks, modules?: string[]): void {
    if (this.currentCallbacks) { this.currentCallbacks.onError("Cancelled"); this.currentCallbacks.onDone(); }
    const id = Date.now().toString(36);
    this.currentRequestId = id;
    this.currentCallbacks = callbacks;
    this.send({ id, type: "ask", question, company, history, modules });
  }

  listTemplates(): void {
    this.send({ type: "listTemplates" });
  }

  cancelCurrent(): void {
    if (this.currentCallbacks) { this.currentCallbacks.onDone(); this.currentCallbacks = null; this.currentRequestId = null; }
  }

  async restart(pythonPath?: string): Promise<boolean> {
    this.restartCount = 0;
    this.lastWorkingCandidate = undefined;
    await this.stop();
    return this.start(pythonPath ?? this.lastPythonPath);
  }

  async stop(): Promise<void> {
    this.stopHealthCheck();
    if (!this.proc) return;
    try { this.send({ type: "exit" }); } catch { /* ignore */ }
    const proc = this.proc;
    this.proc = null;
    if (this.rl) { this.rl.close(); this.rl = null; }
    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => { proc.kill("SIGKILL"); resolve(); }, 3_000);
      proc.on("exit", () => { clearTimeout(timeout); resolve(); });
    });
    this.setState("stopped");
  }

  showLogs(): void { this.output.show(); }

  dispose(): void { this.disposed = true; this.stop(); this.output.dispose(); }
}
