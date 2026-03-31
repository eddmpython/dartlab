/** Bridge -- VSCode webview와 브라우저 모드 자동 감지. */

interface Bridge {
  postMessage(msg: unknown): void;
  getState<T>(): T | undefined;
  setState<T>(state: T): void;
  onMessage(handler: (msg: unknown) => void): void;
}

const isVSCode = !!(window as any).__vscode || typeof (window as any).acquireVsCodeApi === "function";

function createVSCodeBridge(): Bridge {
  // Use pre-acquired API from inline script, or acquire fresh
  const vscode = (window as any).__vscode || (window as any).acquireVsCodeApi();
  return {
    postMessage: (msg) => vscode.postMessage(msg),
    getState: <T>() => vscode.getState() as T | undefined,
    setState: <T>(state: T) => vscode.setState(state),
    onMessage: (handler) => {
      window.addEventListener("message", (e) => handler(e.data));
    },
  };
}

function createMockBridge(): Bridge {
  console.log("[dartlab] Browser dev mode -- mock bridge active");
  const handlers: Array<(msg: unknown) => void> = [];

  function dispatch(msg: unknown) {
    for (const h of handlers) h(msg);
  }

  return {
    postMessage: (msg) => {
      const m = msg as Record<string, unknown>;
      console.log("[mock] →", m.type, msg);

      if (m.type === "ready") {
        setTimeout(() => {
          dispatch({ type: "serverState", state: "ready" });
          dispatch({ type: "profile", payload: { provider: "mock", model: "mock-dev", ready: true } });
        }, 50);
      } else if (m.type === "ask") {
        const p = m.payload as Record<string, unknown>;
        const q = (p?.question as string) || "";
        // mock streaming response
        setTimeout(() => dispatch({ type: "sseEvent", event: "meta", data: { company: "Mock기업", stockCode: "000000" } }), 100);
        setTimeout(() => dispatch({ type: "sseEvent", event: "chunk", data: { text: `"${q}"에 대한 ` } }), 200);
        setTimeout(() => dispatch({ type: "sseEvent", event: "chunk", data: { text: "mock 응답입니다. " } }), 300);
        setTimeout(() => dispatch({ type: "sseEvent", event: "chunk", data: { text: "브라우저 dev 모드에서 정상 동작 중." } }), 400);
        setTimeout(() => {
          dispatch({ type: "sseEvent", event: "done", data: {} });
          dispatch({ type: "streamEnd" });
        }, 500);
      } else if (m.type === "syncConversations") {
        // persist to localStorage
        try { localStorage.setItem("dartlab-convs", JSON.stringify(m.payload)); } catch {}
      }
    },
    getState: <T>() => {
      try {
        const s = localStorage.getItem("dartlab-state");
        return s ? (JSON.parse(s) as T) : undefined;
      } catch { return undefined; }
    },
    setState: <T>(state: T) => {
      try { localStorage.setItem("dartlab-state", JSON.stringify(state)); } catch {}
    },
    onMessage: (handler) => {
      handlers.push(handler);
    },
  };
}

const bridge: Bridge = isVSCode ? createVSCodeBridge() : createMockBridge();

export function postMessage(msg: unknown): void {
  bridge.postMessage(msg);
}

export function getState<T>(): T | undefined {
  return bridge.getState<T>();
}

export function setState<T>(state: T): void {
  bridge.setState(state);
}

export function onMessage(handler: (msg: unknown) => void): void {
  bridge.onMessage(handler);
}
