/** Messages from WebView to Extension Host. */
export type WebViewMessage =
  | { type: "ask"; payload: AskPayload }
  | { type: "stopStream" }
  | { type: "search"; payload: { query: string } }
  | { type: "getStatus" }
  | { type: "getProfile" }
  | { type: "updateProfile"; payload: Record<string, unknown> }
  | { type: "updateSecret"; payload: { provider: string; key: string; action: "set" | "delete" } }
  | { type: "openReport"; payload: { company: string; stockCode: string } }
  | { type: "openSettings" }
  | { type: "getModels"; payload: { provider: string } }
  | { type: "syncConversations"; payload: unknown }
  | { type: "ready" };

export interface AskPayload {
  question: string;
  company?: string;
  provider?: string;
  model?: string;
  history?: HistoryMessage[];
}

export interface HistoryMessage {
  role: "user" | "assistant";
  text: string;
  meta?: Record<string, unknown>;
}

/** Messages from Extension Host to WebView. */
export type ExtensionMessage =
  | { type: "sseEvent"; event: string; data: unknown }
  | { type: "streamEnd" }
  | { type: "streamError"; error: string }
  | { type: "status"; payload: unknown }
  | { type: "profile"; payload: unknown }
  | { type: "searchResults"; payload: unknown[] }
  | { type: "models"; payload: { models: string[] } }
  | { type: "serverState"; state: "starting" | "ready" | "error" | "stopped" }
  | { type: "restoreConversations"; payload: unknown }
  | { type: "selectConversation"; payload: { id: string } }
  | { type: "pythonStatus"; payload: PythonStatusPayload }
  | { type: "installProgress"; payload: { stage: string; message: string } };

export interface PythonStatusPayload {
  found: boolean;
  version: string | null;
  dartlabVersion: string | null;
  needsUpdate: boolean;
  latestVersion: string | null;
}
