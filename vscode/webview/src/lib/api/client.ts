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

export function search(query: string) {
  postMessage({ type: "search", payload: { query } });
}

export function getStatus() {
  postMessage({ type: "getStatus" });
}

export function getProfile() {
  postMessage({ type: "getProfile" });
}

export function getModels(provider: string) {
  postMessage({ type: "getModels", payload: { provider } });
}

export function updateProfile(data: Record<string, unknown>) {
  postMessage({ type: "updateProfile", payload: data });
}

export function updateSecret(provider: string, key: string, action: "set" | "delete") {
  postMessage({ type: "updateSecret", payload: { provider, key, action } });
}

export function syncConversations(data: unknown) {
  postMessage({ type: "syncConversations", payload: data });
}

export function ready() {
  postMessage({ type: "ready" });
}
