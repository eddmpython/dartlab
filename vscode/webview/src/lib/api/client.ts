/** PostMessage-based API client for communicating with Extension Host. */
import { postMessage } from "../vscode";

/** Strip Svelte $state proxies -- postMessage requires plain objects. */
function plain<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

export function ask(
  question: string,
  company?: string,
  history?: Array<{ role: string; text: string }>,
  modules?: string[],
) {
  postMessage(plain({
    type: "ask",
    payload: { question, company, history, modules },
  }));
}

export function listTemplates() {
  postMessage({ type: "listTemplates" });
}

export function stopStream() {
  postMessage({ type: "stopStream" });
}

export function syncConversations(data: unknown) {
  postMessage(plain({ type: "syncConversations", payload: data }));
}

export function setProvider(provider: string, model?: string) {
  postMessage({ type: "setProvider", payload: { provider, model } });
}

export function ready() {
  postMessage({ type: "ready" });
}
