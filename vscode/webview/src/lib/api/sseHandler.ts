/** SSE event handler — ported from ui/src/lib/ai/chatStream.js */

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
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
  codeRounds?: Array<{ round: number; maxRounds: number; status: string }>;
  duration?: number;
  startedAt?: number;
}

export function createMessageId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

/** Creates SSE event callbacks that update a message in-place.
 *  Ported from chatStream.js createAskStreamCallbacks pattern. */
export function createSseHandler(
  getMessage: () => Message,
  updateMessage: (patch: Partial<Message>) => void,
  onDone: () => void,
) {
  let chunkBuffer = "";
  let chunkRafId: number | null = null;

  function flushChunks() {
    chunkRafId = null;
    if (!chunkBuffer) return;
    const msg = getMessage();
    updateMessage({ text: msg.text + chunkBuffer });
    chunkBuffer = "";
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
          const msg = getMessage();
          const events = [...(msg.toolEvents ?? [])];
          events.push({ type: "call", _ts: Date.now(), ...(d as Record<string, unknown>) } as any);
          updateMessage({ toolEvents: events });
          break;
        }

        case "tool_result": {
          const msg = getMessage();
          const events = [...(msg.toolEvents ?? [])];
          events.push({ type: "result", _ts: Date.now(), ...(d as Record<string, unknown>) } as any);
          updateMessage({ toolEvents: events });
          break;
        }

        case "code_round": {
          const msg = getMessage();
          const rounds = [...(msg.codeRounds ?? [])];
          rounds.push(d as { round: number; maxRounds: number; status: string });
          updateMessage({ codeRounds: rounds });
          break;
        }

        case "done":
          flushChunks();
          updateMessage({
            loading: false,
            duration: Date.now() - (getMessage().startedAt ?? Date.now()),
          });
          onDone();
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
      onDone();
    },

    handleStreamError(error: string) {
      flushChunks();
      updateMessage({
        loading: false,
        error: true,
        text: getMessage().text + "\n\n**Error:** " + error,
      });
      onDone();
    },
  };
}
