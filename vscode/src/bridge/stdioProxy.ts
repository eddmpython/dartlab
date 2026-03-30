/**
 * StdioProxy -- dartlab CLI child process + JSON Lines protocol.
 * Claude Code pattern: spawn + stdin/stdout.
 * Auto-restart with exponential backoff + healthcheck.
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

  /** Start dartlab chat --stdio child process. */
  async start(pythonPath?: string): Promise<boolean> {
    if (this.disposed) return false;
    this.lastPythonPath = pythonPath;
    this.setState("starting");
    this.stderrBuffer = "";

    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const cmd = pythonPath || "uv";
    const args = pythonPath
      ? ["-X", "utf8", "-m", "dartlab", "chat", "--stdio"]
      : ["run", "python", "-X", "utf8", "-m", "dartlab", "chat", "--stdio"];

    this.output.appendLine(`[DartLab] spawn: ${cmd} ${args.join(" ")} (cwd: ${cwd ?? "none"})`);

    try {
      this.proc = spawn(cmd, args, {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env },
        ...(cwd ? { cwd } : {}),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      this.output.appendLine(`[DartLab] spawn failed: ${msg}`);
      this.setState("error");
      return false;
    }

    // Collect stderr for error diagnosis
    this.proc.stderr?.on("data", (data: Buffer) => {
      const text = data.toString();
      this.output.append(text);
      this.stderrBuffer += text;
      // Keep only last 2KB
      if (this.stderrBuffer.length > 2048) {
        this.stderrBuffer = this.stderrBuffer.slice(-2048);
      }
    });

    this.proc.on("error", (err) => {
      this.output.appendLine(`[DartLab] process error: ${err.message}`);
      this.handleProcessExit(-1);
    });

    this.proc.on("exit", (code) => {
      this.output.appendLine(`[DartLab] process exited: code=${code}`);
      this.handleProcessExit(code ?? -1);
    });

    // Read stdout JSON lines
    this.rl = createInterface({ input: this.proc.stdout!, crlfDelay: Infinity });

    const ready = await this.waitForReady();
    if (ready) {
      this.restartCount = 0;
      this.startHealthCheck();
    }
    return ready;
  }

  private waitForReady(): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      const timeout = setTimeout(() => {
        this.output.appendLine("[DartLab] timeout waiting for ready signal");
        this.setState("error");
        resolve(false);
      }, READY_TIMEOUT_MS);

      const onLine = (line: string) => {
        this.output.appendLine(`[stdout] ${line.slice(0, 200)}`);
        try {
          const msg = JSON.parse(line);
          if (msg.event === "ready") {
            clearTimeout(timeout);
            this.setState("ready");
            this.rl?.removeListener("line", onLine);
            this.rl?.on("line", (l) => this.handleLine(l));
            resolve(true);
          }
        } catch { /* non-JSON, ignore */ }
      };

      this.rl!.on("line", onLine);
    });
  }

  private handleProcessExit(code: number): void {
    if (this.disposed) return;

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
    if (this._state === "ready" && this.restartCount < MAX_RESTARTS) {
      this.restartCount++;
      const delay = BACKOFF_BASE_MS * Math.pow(2, this.restartCount - 1);
      this.output.appendLine(`[DartLab] auto-restart ${this.restartCount}/${MAX_RESTARTS} in ${delay}ms`);
      this.setState("starting");
      setTimeout(() => {
        if (!this.disposed) this.start(this.lastPythonPath);
      }, delay);
    } else {
      this.setState("error");
      this.showStartupError(code);
    }
  }

  private showStartupError(code: number): void {
    let detail = "";
    const stderr = this.stderrBuffer.toLowerCase();

    if (stderr.includes("no module named") && stderr.includes("dartlab")) {
      detail = "dartlab is not installed. Run: pip install dartlab";
    } else if (stderr.includes("no module named uv") || stderr.includes("'uv' is not recognized") || code === 9009) {
      detail = "uv is required. Install: https://docs.astral.sh/uv/";
    } else if (stderr.includes("python") && stderr.includes("not found")) {
      detail = "Python 3.12+ is required.";
    } else if (this.stderrBuffer.trim()) {
      detail = this.stderrBuffer.trim().split("\n").pop() || "Unknown error";
    } else {
      detail = `Process exited with code ${code}`;
    }

    vscode.window.showErrorMessage(
      `DartLab: ${detail}`,
      "Show Logs", "Retry",
    ).then((choice) => {
      if (choice === "Show Logs") this.showLogs();
      else if (choice === "Retry") {
        this.restartCount = 0;
        this.start(this.lastPythonPath);
      }
    });
  }

  // --- Healthcheck ---

  private startHealthCheck(): void {
    this.stopHealthCheck();
    this.healthTimer = setInterval(() => this.ping(), HEALTH_INTERVAL_MS);
  }

  private stopHealthCheck(): void {
    if (this.healthTimer) {
      clearInterval(this.healthTimer);
      this.healthTimer = null;
    }
  }

  private ping(): void {
    if (this._state !== "ready" || !this.proc?.stdin?.writable) return;

    const timeout = setTimeout(() => {
      this.output.appendLine("[DartLab] healthcheck timeout -- killing process");
      this.proc?.kill("SIGKILL");
    }, HEALTH_TIMEOUT_MS);

    // pong listener is handled in handleLine
    const onPong = () => clearTimeout(timeout);
    this._pongCallback = onPong;

    this.send({ type: "ping" });
  }

  private _pongCallback: (() => void) | null = null;

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

    // Pong response
    if (event === "pong") {
      this._pongCallback?.();
      this._pongCallback = null;
      return;
    }

    // Status response
    if (event === "status") {
      for (const fn of this.statusListeners) fn(data);
      this.statusListeners = [];
      return;
    }

    // Provider changed
    if (event === "providerChanged") {
      for (const fn of this.providerListeners) fn(data);
      this.providerListeners = [];
      return;
    }

    // Route to current request callbacks
    if (this.currentCallbacks && (!id || id === this.currentRequestId)) {
      if (event === "done") {
        this.currentCallbacks.onEvent(event, data);
        this.currentCallbacks.onDone();
        this.currentCallbacks = null;
        this.currentRequestId = null;
      } else if (event === "error") {
        this.currentCallbacks.onEvent(event, data);
        // Don't clear -- wait for done event
      } else {
        this.currentCallbacks.onEvent(event, data);
      }
    }
  }

  // --- Public API ---

  requestStatus(callback: (data: Record<string, unknown>) => void): void {
    this.statusListeners.push(callback);
    this.send({ type: "status" });
    setTimeout(() => {
      this.statusListeners = this.statusListeners.filter(l => l !== callback);
    }, 5000);
  }

  setProvider(provider: string, model?: string, callback?: (data: Record<string, unknown>) => void): void {
    if (callback) this.providerListeners.push(callback);
    this.send({ type: "setProvider", provider, model });
  }

  ask(
    question: string,
    company: string | undefined,
    history: unknown[] | undefined,
    callbacks: StdioCallbacks,
  ): void {
    // Cancel previous
    if (this.currentCallbacks) {
      this.currentCallbacks.onError("Cancelled");
      this.currentCallbacks.onDone();
    }

    const id = Date.now().toString(36);
    this.currentRequestId = id;
    this.currentCallbacks = callbacks;

    this.send({ id, type: "ask", question, company, history });
  }

  cancelCurrent(): void {
    if (this.currentCallbacks) {
      this.currentCallbacks.onDone();
      this.currentCallbacks = null;
      this.currentRequestId = null;
    }
  }

  async restart(pythonPath?: string): Promise<boolean> {
    this.restartCount = 0;
    await this.stop();
    return this.start(pythonPath ?? this.lastPythonPath);
  }

  async stop(): Promise<void> {
    this.stopHealthCheck();
    if (!this.proc) return;

    try { this.send({ type: "exit" }); } catch { /* ignore */ }

    const proc = this.proc;
    this.proc = null;
    this.rl = null;

    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => { proc.kill("SIGKILL"); resolve(); }, 3_000);
      proc.on("exit", () => { clearTimeout(timeout); resolve(); });
    });

    this.setState("stopped");
  }

  showLogs(): void { this.output.show(); }

  dispose(): void {
    this.disposed = true;
    this.stop();
    this.output.dispose();
  }
}
