/**
 * VSCode webview transport — postMessage 기반 통신.
 * Extension Host가 SSE 이벤트를 파싱 후 sseEvent로 전달.
 */
import { getVSCodeBridge } from "./transport.js";

/**
 * @typedef {Object} VSCodeBridge
 * @property {(msg: any) => void} postMessage
 * @property {() => any} getState
 * @property {(state: any) => void} setState
 * @property {(handler: (msg: any) => void) => void} onMessage
 * @property {Array<(msg: any) => void>} _handlers
 */

/**
 * askStream의 VSCode 구현 — postMessage로 질문 전송, sseEvent 리스닝.
 * 콜백 인터페이스는 HTTP 버전과 동일.
 */
export function askStreamVSCode(company, question, options = {}, callbacks, history = null) {
	const bridge = getVSCodeBridge();
	if (!bridge) {
		callbacks.onError?.("VSCode 환경이 아닙니다");
		return { abort: () => {} };
	}

	const payload = { question, ...options };
	if (company) payload.company = company;
	if (history?.length > 0) payload.history = history;
	if (options.modules?.length > 0) payload.modules = options.modules;

	let done = false;

	/** SSE 이벤트 핸들러 */
	function handleMessage(msg) {
		if (done) return;
		const { type, event, data } = msg;

		if (type === "sseEvent") {
			switch (event) {
				case "meta": callbacks.onMeta?.(data); break;
				case "snapshot": callbacks.onSnapshot?.(data); break;
				case "context": callbacks.onContext?.(data); break;
				case "system_prompt": callbacks.onSystemPrompt?.(data); break;
				case "tool_call": callbacks.onToolCall?.(data); break;
				case "tool_result": callbacks.onToolResult?.(data); break;
				case "chunk": callbacks.onChunk?.(data?.text); break;
				case "code_round": callbacks.onCodeRound?.(data); break;
				case "chart": callbacks.onChart?.(data); break;
				case "ui_action": callbacks.onUiAction?.(data); break;
				case "error": callbacks.onError?.(data?.error, data?.action, data?.detail); break;
				case "done":
					cleanup();
					callbacks.onDone?.(data);
					break;
			}
		} else if (type === "streamEnd") {
			if (!done) { cleanup(); callbacks.onDone?.(); }
		} else if (type === "streamError") {
			cleanup();
			callbacks.onError?.(msg.error);
		}
	}

	// 메시지 리스너 등록 (window 이벤트 직접 사용 — 정리 가능하게)
	function listener(e) { handleMessage(e.data); }
	window.addEventListener("message", listener);

	bridge.postMessage({ type: "ask", payload });

	function cleanup() {
		done = true;
		window.removeEventListener("message", listener);
	}

	return {
		abort: () => {
			cleanup();
			bridge.postMessage({ type: "stopStream" });
		},
	};
}

/** VSCode에서 provider/status 관련 통신 */
export function fetchStatusVSCode() {
	const bridge = getVSCodeBridge();
	if (!bridge) return Promise.resolve(null);

	return new Promise((resolve) => {
		function handler(msg) {
			if (msg.type === "serverState" || msg.type === "profile") {
				resolve(msg);
			}
		}
		bridge.onMessage(handler);
		bridge.postMessage({ type: "ready" });
		// 타임아웃 fallback
		setTimeout(() => resolve(null), 5000);
	});
}

export function setProviderVSCode(provider, model) {
	const bridge = getVSCodeBridge();
	bridge?.postMessage({ type: "setProvider", payload: { provider, model } });
}

export function requestCredentialVSCode(provider, signupUrl) {
	const bridge = getVSCodeBridge();
	bridge?.postMessage({ type: "requestCredential", payload: { provider, signupUrl } });
}

export function syncConversationsVSCode(data) {
	const bridge = getVSCodeBridge();
	bridge?.postMessage({ type: "syncConversations", payload: JSON.parse(JSON.stringify(data)) });
}
