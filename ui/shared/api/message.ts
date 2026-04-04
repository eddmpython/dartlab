/** Shared message types — Claude Code ContentBlock 패턴 */

export interface ContentBlock {
  type: "text" | "code_execution" | "tool_call" | "chart";
  // text
  text?: string;
  // code_execution
  code?: string;
  result?: string;
  status?: "executing" | "done";
  round?: number;
  maxRounds?: number;
  // tool_call
  name?: string;
  arguments?: unknown;
  toolResult?: unknown;
  // chart
  spec?: unknown;
  _ts?: number;
  _resultTs?: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  blocks: ContentBlock[];
  loading: boolean;
  error: boolean;
  meta?: Record<string, unknown>;
  snapshot?: Record<string, unknown>;
  contexts?: Array<{ module: string; label: string; text: string }>;
  toolEvents?: Array<{ type: string; name: string; arguments?: unknown; result?: unknown; [k: string]: unknown }>;
  systemPrompt?: string;
  userContent?: string;
  errorAction?: string;
  errorGuide?: string;
  codeRounds?: Array<{ round: number; maxRounds: number; status: string; code?: string; result?: string }>;
  duration?: number;
  startedAt?: number;
}

export function createMessageId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}
