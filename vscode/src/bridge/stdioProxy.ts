/**
 * StdioProxy -- dartlab CLI child process와 JSON Lines로 통신.
 * Claude Code 패턴: child process spawn + stdin/stdout.
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

export class StdioProxy {
  private proc: ChildProcess | null = null;
  private rl: Interface | null = null;
  private _state: ServerState = "stopped";
  private listeners: StateListener[] = [];
  private output: vscode.OutputChannel;
  private disposed = false;
  private currentCallbacks: StdioCallbacks | null = null;
  private currentRequestId: string | null = null;

  constructor() {
    this.output = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
  }

  get state(): ServerState {
    return this._state;
  }

  onStateChange(fn: StateListener): vscode.Disposable {
    this.listeners.push(fn);
    return new vscode.Disposable(() => {
      this.listeners = this.listeners.filter((l) => l !== fn);
    });
  }

  private setState(s: ServerState) {
    this._state = s;
    for (const fn of this.listeners) fn(s);
  }

  /** Start dartlab chat --stdio child process. */
  async start(pythonPath: string): Promise<boolean> {
    if (this.disposed) return false;
    this.setState("starting");

    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

    this.proc = spawn(
      pythonPath,
      ["-X", "utf8", "-m", "dartlab", "chat", "--stdio"],
      {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env },
        ...(cwd ? { cwd } : {}),
      },
    );

    // Stderr → output channel (logs, not protocol)
    this.proc.stderr?.on("data", (data: Buffer) => {
      this.output.append(data.toString());
    });

    this.proc.on("exit", (code) => {
      if (this.disposed) return;
      this.output.appendLine(`[DartLab] Process exited with code ${code}`);
      this.rl = null;
      this.proc = null;
      if (this._state === "ready") {
        // Unexpected exit -- try restart
        this.setState("error");
      } else {
        this.setState("stopped");
      }
    });

    // Read stdout line by line (JSON Lines protocol)
    this.rl = createInterface({ input: this.proc.stdout!, crlfDelay: Infinity });

    return new Promise<boolean>((resolve) => {
      const timeout = setTimeout(() => {
        this.output.appendLine("[DartLab] Timeout waiting for ready signal");
        this.setState("error");
        resolve(false);
      }, 30_000);

      const onLine = (line: string) => {
        this.output.appendLine(`[stdout] ${line.slice(0, 200)}`);
        try {
          const msg = JSON.parse(line);
          if (msg.event === "ready") {
            clearTimeout(timeout);
            this.setState("ready");
            // Switch to normal message handler
            this.rl?.removeListener("line", onLine);
            this.rl?.on("line", (l) => this.handleLine(l));
            resolve(true);
          }
        } catch {
          // Non-JSON line, ignore
        }
      };

      this.rl!.on("line", onLine);
    });
  }

  /** Send a JSON message to stdin. */
  private send(msg: Record<string, unknown>): void {
    if (!this.proc?.stdin?.writable) return;
    const line = JSON.stringify(msg) + "\n";
    this.proc.stdin.write(line);
  }

  /** Handle a JSON line from stdout. */
  private handleLine(line: string): void {
    this.output.appendLine(`[stdout] ${line.slice(0, 200)}`);

    let msg: Record<string, unknown>;
    try {
      msg = JSON.parse(line);
    } catch {
      return; // Non-JSON line
    }

    const event = msg.event as string;
    const data = msg.data;
    const id = msg.id as string | undefined;

    // Route to current request callbacks
    if (this.currentCallbacks && (!id || id === this.currentRequestId)) {
      if (event === "done" || event === "error") {
        this.currentCallbacks.onEvent(event, data);
        this.currentCallbacks.onDone();
        this.currentCallbacks = null;
        this.currentRequestId = null;
      } else {
        this.currentCallbacks.onEvent(event, data);
      }
    }

    // Status responses (no request context)
    if (event === "status") {
      // Broadcast to any status listeners
      for (const fn of this.statusListeners) fn(data as Record<string, unknown>);
    }
  }

  private statusListeners: Array<(data: Record<string, unknown>) => void> = [];

  /** Request provider status. */
  requestStatus(callback: (data: Record<string, unknown>) => void): void {
    this.statusListeners.push(callback);
    this.send({ type: "status" });
    // Auto-remove after response
    setTimeout(() => {
      this.statusListeners = this.statusListeners.filter((l) => l !== callback);
    }, 5000);
  }

  /** Send an ask request. */
  ask(
    question: string,
    company: string | undefined,
    history: unknown[] | undefined,
    callbacks: StdioCallbacks,
  ): void {
    // Cancel previous request
    if (this.currentCallbacks) {
      this.currentCallbacks.onError("Cancelled by new request");
      this.currentCallbacks.onDone();
    }

    const id = Date.now().toString(36);
    this.currentRequestId = id;
    this.currentCallbacks = callbacks;

    this.send({
      id,
      type: "ask",
      question,
      company,
      history,
    });
  }

  /** Cancel current request (by sending a new status to flush). */
  cancelCurrent(): void {
    if (this.currentCallbacks) {
      this.currentCallbacks.onDone();
      this.currentCallbacks = null;
      this.currentRequestId = null;
    }
  }

  /** Restart the process. */
  async restart(pythonPath: string): Promise<boolean> {
    await this.stop();
    return this.start(pythonPath);
  }

  async stop(): Promise<void> {
    if (!this.proc) return;

    // Try graceful exit
    try {
      this.send({ type: "exit" });
    } catch { /* ignore */ }

    const proc = this.proc;
    this.proc = null;
    this.rl = null;

    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => {
        proc.kill("SIGKILL");
        resolve();
      }, 3_000);
      proc.on("exit", () => {
        clearTimeout(timeout);
        resolve();
      });
    });

    this.setState("stopped");
  }

  showLogs(): void {
    this.output.show();
  }

  dispose(): void {
    this.disposed = true;
    this.stop();
    this.output.dispose();
  }
}
