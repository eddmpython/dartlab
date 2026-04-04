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

        // "에러" → error 시나리오
        if (q.includes("에러")) {
          setTimeout(() => dispatch({ type: "sseEvent", event: "meta", data: {} }), 100);
          setTimeout(() => dispatch({ type: "sseEvent", event: "error", data: { error: "Mock 에러: 인증 만료", action: "relogin", guide: "dartlab.setup(\"gemini\")으로 재인증하세요." } }), 200);
          setTimeout(() => {
            dispatch({ type: "sseEvent", event: "done", data: {} });
            dispatch({ type: "streamEnd" });
          }, 300);
          return;
        }

        // "분석" → code_round 시나리오 (Claude Code 패턴 테스트)
        if (q.includes("분석")) {
          setTimeout(() => dispatch({ type: "sseEvent", event: "meta", data: { company: "SK하이닉스", stockCode: "000660", market: "KOSPI" } }), 100);
          setTimeout(() => dispatch({ type: "sseEvent", event: "snapshot", data: { items: [{ label: "시가총액", value: "180.5조", status: "good" }, { label: "PER", value: "8.2x", status: "good" }, { label: "부채비율", value: "72.3%", status: "caution" }], grades: { 수익성: "A", 안정성: "B", 성장성: "A" } } }), 150);
          setTimeout(() => dispatch({ type: "sseEvent", event: "chunk", data: { text: "SK하이닉스의 재무 안정성을 분석하겠습니다.\n\n" } }), 200);
          setTimeout(() => dispatch({ type: "sseEvent", event: "chunk", data: { text: "```python\nc = dartlab.Company(\"000660\")\nr = c.analysis(\"financial\", \"안정성\")\nprint(r)\n```\n" } }), 300);
          setTimeout(() => dispatch({ type: "sseEvent", event: "code_round", data: { round: 1, maxRounds: 3, status: "executing", code: "c = dartlab.Company(\"000660\")\nr = c.analysis(\"financial\", \"안정성\")\nprint(r)" } }), 500);
          setTimeout(() => dispatch({ type: "sseEvent", event: "code_round", data: { round: 1, maxRounds: 3, status: "done", code: "c = dartlab.Company(\"000660\")\nr = c.analysis(\"financial\", \"안정성\")\nprint(r)", result: "\n\n[실행 결과]\n\n| 지표 | 2022 | 2023 | 2024 |\n|------|------|------|------|\n| 부채비율 | 85.3% | 78.1% | 72.3% |\n| 유동비율 | 1.82 | 1.95 | 2.12 |\n| 이자보상배율 | 3.2x | 4.8x | 8.1x |\n\n" } }), 800);
          setTimeout(() => dispatch({ type: "sseEvent", event: "chunk", data: { text: "\n## 종합 해석\n\n하이닉스는 **부채 구조가 개선**되고 있습니다:\n\n- 부채비율 85% → 72%로 꾸준히 하락\n- 유동비율 2.12로 단기 상환 여력 충분\n- 이자보상배율 8.1x로 이자 부담 매우 낮음\n\n**안정성 등급: B+** (양호)\n" } }), 1200);
          setTimeout(() => {
            dispatch({ type: "sseEvent", event: "done", data: {} });
            dispatch({ type: "streamEnd" });
          }, 1400);
          return;
        }

        // 기본 mock 응답
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
      } else if (m.type === "listTemplates") {
        setTimeout(() => dispatch({ type: "templates", payload: [
          { name: "financial", description: "재무 분석", source: "builtin" },
          { name: "valuation", description: "밸류에이션", source: "builtin" },
        ]}), 50);
      } else if (m.type === "stopStream") {
        console.log("[mock] stream stopped");
      } else if (m.type === "setProvider") {
        const p = m.payload as Record<string, unknown>;
        setTimeout(() => dispatch({ type: "profile", payload: { provider: p.provider, model: "mock-model", providers: [] } }), 50);
      } else if (m.type === "requestCredential") {
        const p = m.payload as Record<string, unknown>;
        console.log("[mock] credential requested for", p.provider);
        setTimeout(() => dispatch({ type: "profile", payload: { provider: p.provider, model: "mock-model" } }), 200);
      } else if (m.type === "openExternal") {
        const p = m.payload as Record<string, unknown>;
        console.log("[mock] openExternal:", p.url);
      } else if (m.type === "openSettings") {
        console.log("[mock] openSettings");
      } else if (m.type === "pasteOAuthToken" || m.type === "pasteOAuthCode") {
        console.log("[mock]", m.type);
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
