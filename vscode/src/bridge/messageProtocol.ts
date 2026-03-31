/** Messages from WebView to Extension Host. */
export type WebViewMessage =
  | { type: "ask"; payload: AskPayload }
  | { type: "stopStream" }
  | { type: "setProvider"; payload: { provider: string; model?: string } }
  | { type: "syncConversations"; payload: unknown }
  | { type: "ready" };

export interface AskPayload {
  question: string;
  company?: string;
  history?: HistoryMessage[];
}

export interface HistoryMessage {
  role: "user" | "assistant";
  text: string;
}

/** Messages from Extension Host to WebView. */
export type ExtensionMessage =
  | { type: "sseEvent"; event: string; data: unknown }
  | { type: "streamEnd" }
  | { type: "streamError"; error: string }
  | { type: "profile"; payload: unknown }
  | { type: "serverState"; state: "starting" | "ready" | "error" | "stopped" }
  | { type: "restoreConversations"; payload: unknown }
  | { type: "selectConversation"; payload: { id: string } }
  | { type: "newConversation" };
