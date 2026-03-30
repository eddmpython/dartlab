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

function buildCandidates(pythonPath?: string): SpawnCandidate[] {
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
  private output: vscode.OutputChannel;
  private disposed = false;

  // Request routing
  private currentCallbacks: StdioCallbacks | null = null;
  private currentRequestId: string | null = null;
  private statusListeners: Array<(data: Record<string, unknown>) => void> = [];
  private providerListeners: Array<(data: Record<string, unknown>) => void> = [];

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

  /** Start dartlab chat --stdio, trying multiple spawn candidates. */
  async start(pythonPath?: string): Promise<boolean> {
    if (this.disposed) return false;
    this.lastPythonPath = pythonPath;
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

    // All candidates failed
    this.setState("error");
    vscode.window.showErrorMessage(
      "DartLab: Could not start. Install dartlab: pip install dartlab",
      "Show Logs",
    ).then((c) => { if (c) this.showLogs(); });
    return false;
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
      this.output.appendLine(`[DartLab] spawn failed: ${err instanceof Error ? err.message : err}`);
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

    // Failed -- clean up
    this.output.appendLine(`[DartLab] failed: ${candidate.label} (stderr: ${this.stderrBuffer.trim().split("\n").pop() ?? ""})`);
    if (!exited) {
      try { this.proc?.kill("SIGKILL"); } catch { /* ignore */ }
    }
    this.proc = null;
    if (this.rl) { this.rl.close(); this.rl = null; }
    return false;
  }

  private waitForReady(): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      const onLine = (line: string) => {
        this.output.appendLine(`[stdout] ${line.slice(0, 200)}`);
        try {
          const msg = JSON.parse(line);
          if (msg.event === "ready") {
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
    const timeout = setTimeout(() => {
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

    if (this.currentCallbacks && (!id || id === this.currentRequestId)) {
      if (event === "done") {
        this.currentCallbacks.onEvent(event, data);
        this.currentCallbacks.onDone();
        this.currentCallbacks = null;
        this.currentRequestId = null;
      } else {
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

  setProvider(provider: string, model?: string, callback?: (data: Record<string, unknown>) => void): void {
    if (callback) this.providerListeners.push(callback);
    this.send({ type: "setProvider", provider, model });
  }

  ask(question: string, company: string | undefined, history: unknown[] | undefined, callbacks: StdioCallbacks): void {
    if (this.currentCallbacks) { this.currentCallbacks.onError("Cancelled"); this.currentCallbacks.onDone(); }
    const id = Date.now().toString(36);
    this.currentRequestId = id;
    this.currentCallbacks = callbacks;
    this.send({ id, type: "ask", question, company, history });
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
