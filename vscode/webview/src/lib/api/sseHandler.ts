/** SSE event handler — content blocks 구조 (Claude Code 패턴 벤치마킹) */

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
  text: string;             // 호환용 — 모든 text block의 합
  blocks: ContentBlock[];   // Claude Code 패턴 — 핵심 렌더링 대상
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

export function createSseHandler(
  getMessage: () => Message,
  updateMessage: (patch: Partial<Message>) => void,
  onDone: () => void,
) {
  let chunkBuffer = "";
  let chunkRafId: number | null = null;
  let done = false;

  function callOnDone() {
    if (done) return;
    done = true;
    onDone();
  }

  /** text chunk를 blocks 배열에 추가 */
  function appendTextToBlocks(text: string) {
    if (!text) return;
    const msg = getMessage();
    const blocks = [...(msg.blocks ?? [])];
    const last = blocks[blocks.length - 1];
    if (last?.type === "text") {
      last.text = (last.text ?? "") + text;
    } else {
      blocks.push({ type: "text", text });
    }
    updateMessage({ text: msg.text + text, blocks });
  }

  function flushChunks() {
    chunkRafId = null;
    if (!chunkBuffer) return;
    const batch = chunkBuffer;
    chunkBuffer = "";
    appendTextToBlocks(batch);
  }

  return {
    handleEvent(event: string, data: unknown) {
      const d = data as Record<string, unknown>;

      switch (event) {
        case "meta":
          updateMessage({ meta: d });
          break;

        case "snapshot":
          updateMessage({ snapshot: d });
          break;

        case "context": {
          const msg = getMessage();
          const contexts = [...(msg.contexts ?? [])];
          contexts.push(d as Message["contexts"] extends (infer T)[] | undefined ? T : never);
          updateMessage({ contexts });
          break;
        }

        case "system_prompt":
          updateMessage({
            systemPrompt: (d as { text?: string }).text ?? undefined,
            userContent: (d as { userContent?: string }).userContent ?? undefined,
          });
          break;

        case "chunk":
          chunkBuffer += (d as { text: string }).text ?? "";
          if (chunkRafId === null) {
            chunkRafId = requestAnimationFrame(flushChunks);
          }
          break;

        case "tool_call": {
          // blocks에 tool_call block 추가
          const msg = getMessage();
          const blocks = [...(msg.blocks ?? [])];
          blocks.push({
            type: "tool_call",
            name: (d as { name: string }).name,
            arguments: (d as { arguments?: unknown }).arguments,
            _ts: Date.now(),
          });
          // 기존 호환
          const events = [...(msg.toolEvents ?? [])];
          events.push({ type: "call", _ts: Date.now(), ...(d as Record<string, unknown>) } as any);
          updateMessage({ blocks, toolEvents: events });
          break;
        }

        case "tool_result": {
          // blocks에서 마지막 tool_call 찾아서 result 추가
          const msg = getMessage();
          const blocks = [...(msg.blocks ?? [])];
          for (let i = blocks.length - 1; i >= 0; i--) {
            if (blocks[i].type === "tool_call" && !blocks[i].toolResult) {
              blocks[i] = { ...blocks[i], toolResult: (d as { result?: unknown }).result, _resultTs: Date.now() };
              break;
            }
          }
          // 기존 호환
          const events = [...(msg.toolEvents ?? [])];
          events.push({ type: "result", _ts: Date.now(), ...(d as Record<string, unknown>) } as any);
          updateMessage({ blocks, toolEvents: events });
          break;
        }

        case "code_round": {
          const cr = d as { round: number; maxRounds: number; status: string; code?: string; result?: string };
          const msg = getMessage();
          const blocks = [...(msg.blocks ?? [])];

          if (cr.status === "executing") {
            // 새 code_execution block 추가
            blocks.push({
              type: "code_execution",
              code: cr.code,
              status: "executing",
              round: cr.round,
              maxRounds: cr.maxRounds,
            });
          } else if (cr.status === "done") {
            // 기존 executing block 찾아서 업데이트
            for (let i = blocks.length - 1; i >= 0; i--) {
              if (blocks[i].type === "code_execution" && blocks[i].round === cr.round) {
                blocks[i] = { ...blocks[i], code: cr.code, result: cr.result, status: "done" };
                break;
              }
            }
          }

          // 기존 호환
          const rounds = [...(msg.codeRounds ?? [])];
          const idx = rounds.findIndex(r => r.round === cr.round);
          if (idx >= 0) rounds[idx] = cr;
          else rounds.push(cr);
          updateMessage({ blocks, codeRounds: rounds });
          break;
        }

        case "chart": {
          const msg = getMessage();
          const blocks = [...(msg.blocks ?? [])];
          const charts = (d as { charts?: unknown[] }).charts ?? [];
          for (const spec of charts) {
            blocks.push({ type: "chart", spec, _ts: Date.now() });
          }
          updateMessage({ blocks });
          break;
        }

        case "done":
          flushChunks();
          updateMessage({
            loading: false,
            duration: Date.now() - (getMessage().startedAt ?? Date.now()),
          });
          callOnDone();
          break;

        case "error":
          flushChunks();
          updateMessage({
            loading: false,
            error: true,
            errorAction: (d as { action?: string }).action,
            errorGuide: (d as { guide?: string }).guide,
            text:
              getMessage().text +
              "\n\n**Error:** " +
              ((d as { error?: string }).error ?? "Unknown error"),
          });
          break;
      }
    },

    handleStreamEnd() {
      flushChunks();
      const msg = getMessage();
      if (msg.loading) {
        updateMessage({ loading: false });
      }
      callOnDone();
    },

    handleStreamError(error: string) {
      flushChunks();
      updateMessage({
        loading: false,
        error: true,
        text: getMessage().text + "\n\n**Error:** " + error,
      });
      callOnDone();
    },
  };
}
