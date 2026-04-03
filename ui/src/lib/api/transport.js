/**
 * Transport 추상화 — 환경 감지로 HTTP/SSE 또는 VSCode postMessage 분기.
 *
 * 브라우저: fetch → SSE 스트리밍 (기존 방식)
 * VSCode webview: postMessage ↔ Extension Host (sseEvent 이벤트)
 */

export const isVSCode = typeof window !== "undefined"
	&& !!(/** @type {any} */ (window).__vscode || typeof (/** @type {any} */ (window)).acquireVsCodeApi === "function");

/** @type {import("./vscodeTransport.js").VSCodeBridge | null} */
let _bridge = null;

/** VSCode 브릿지 (lazy init) */
export function getVSCodeBridge() {
	if (!isVSCode) return null;
	if (_bridge) return _bridge;

	const win = /** @type {any} */ (window);
	const vscode = win.__vscode || win.acquireVsCodeApi();

	/** @type {Array<(msg: any) => void>} */
	const handlers = [];

	_bridge = {
		postMessage: (msg) => vscode.postMessage(JSON.parse(JSON.stringify(msg))),
		getState: () => vscode.getState(),
		setState: (state) => vscode.setState(state),
		onMessage: (handler) => {
			handlers.push(handler);
		},
		_handlers: handlers,
	};

	window.addEventListener("message", (e) => {
		for (const h of handlers) h(e.data);
	});

	return _bridge;
}
