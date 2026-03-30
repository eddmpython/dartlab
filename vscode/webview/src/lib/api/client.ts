/** PostMessage-based API client for communicating with Extension Host. */
import { postMessage } from "../vscode";

export function ask(
  question: string,
  company?: string,
  history?: Array<{ role: string; text: string }>,
) {
  postMessage({
    type: "ask",
    payload: { question, company, history },
  });
}

export function stopStream() {
  postMessage({ type: "stopStream" });
}

export function syncConversations(data: unknown) {
  postMessage({ type: "syncConversations", payload: data });
}

export function setProvider(provider: string, model?: string) {
  postMessage({ type: "setProvider", payload: { provider, model } });
}

export function ready() {
  postMessage({ type: "ready" });
}
