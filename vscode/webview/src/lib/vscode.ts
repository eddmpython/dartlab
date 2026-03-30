/** VSCode WebView API wrapper. */

interface VsCodeApi {
  postMessage(msg: unknown): void;
  getState(): unknown;
  setState(state: unknown): void;
}

// acquireVsCodeApi is injected by VSCode and can only be called once.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const vscode: VsCodeApi = (window as any).acquireVsCodeApi();

export function postMessage(msg: unknown): void {
  // Debug: also send log to extension host
  const m = msg as Record<string, unknown>;
  if (m.type !== "log") {
    vscode.postMessage({ type: "log", message: `postMessage: type=${m.type}` });
  }
  vscode.postMessage(msg);
}

export function getState<T>(): T | undefined {
  return vscode.getState() as T | undefined;
}

export function setState<T>(state: T): void {
  vscode.setState(state);
}

/** Listen for messages from Extension Host. */
export function onMessage(handler: (msg: unknown) => void): void {
  window.addEventListener("message", (e) => handler(e.data));
}
