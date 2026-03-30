import { ChildProcess, spawn } from "child_process";
import * as vscode from "vscode";
import {
  MAX_RESTART_ATTEMPTS,
  OUTPUT_CHANNEL_NAME,
  RESTART_BACKOFF_MS,
} from "../constants";
import { waitForReady } from "./healthCheck";

export type ServerState = "stopped" | "starting" | "ready" | "error";

type StateListener = (state: ServerState) => void;

/** Manages the dartlab Python server as a child process. */
export class ProcessManager {
  private proc: ChildProcess | null = null;
  private _state: ServerState = "stopped";
  private restartCount = 0;
  private port = 0;
  private pythonPath = "";
  private output: vscode.OutputChannel;
  private listeners: StateListener[] = [];
  private disposed = false;

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
    for (const fn of this.listeners) {
      fn(s);
    }
  }

  /** Start the dartlab server. */
  async start(pythonPath: string, port: number): Promise<boolean> {
    if (this.disposed) {
      return false;
    }
    this.pythonPath = pythonPath;
    this.port = port;
    this.setState("starting");

    this.proc = spawn(
      pythonPath,
      ["-m", "dartlab.server", "--host", "127.0.0.1", "--port", String(port)],
      {
        stdio: ["pipe", "pipe", "pipe"],
        env: { ...process.env },
      },
    );

    this.proc.stdout?.on("data", (data: Buffer) => {
      this.output.append(data.toString());
    });
    this.proc.stderr?.on("data", (data: Buffer) => {
      this.output.append(data.toString());
    });

    this.proc.on("exit", (code) => {
      if (this.disposed) {
        return;
      }
      if (code !== 0 && code !== null) {
        this.output.appendLine(`[DartLab] Server exited with code ${code}`);
        if (this.restartCount < MAX_RESTART_ATTEMPTS) {
          this.restartCount++;
          this.output.appendLine(
            `[DartLab] Restarting (attempt ${this.restartCount}/${MAX_RESTART_ATTEMPTS})...`,
          );
          setTimeout(() => {
            this.start(this.pythonPath, this.port);
          }, RESTART_BACKOFF_MS * this.restartCount);
        } else {
          this.setState("error");
          vscode.window
            .showErrorMessage("DartLab server failed to start.", "Show Logs", "Restart")
            .then((choice) => {
              if (choice === "Show Logs") {
                this.output.show();
              } else if (choice === "Restart") {
                this.restartCount = 0;
                this.start(this.pythonPath, this.port);
              }
            });
        }
      } else {
        this.setState("stopped");
      }
    });

    // Wait for server to be ready
    const ready = await waitForReady(port);
    if (ready) {
      this.restartCount = 0;
      this.setState("ready");
      return true;
    }

    // Server didn't respond in time
    this.setState("error");
    return false;
  }

  /** Graceful shutdown. */
  async stop(): Promise<void> {
    if (!this.proc) {
      return;
    }
    const proc = this.proc;
    this.proc = null;

    // Try graceful kill
    proc.kill("SIGTERM");

    // Wait up to 5 seconds for exit
    await new Promise<void>((resolve) => {
      const timeout = setTimeout(() => {
        proc.kill("SIGKILL");
        resolve();
      }, 5_000);
      proc.on("exit", () => {
        clearTimeout(timeout);
        resolve();
      });
    });

    this.setState("stopped");
  }

  /** Restart the server. */
  async restart(): Promise<boolean> {
    this.restartCount = 0;
    await this.stop();
    return this.start(this.pythonPath, this.port);
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
