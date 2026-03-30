/** SSE proxy -- fetches /api/ask from Python server, relays events to callback. */

export interface SseCallbacks {
  onEvent: (event: string, data: unknown) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export class SseProxy {
  private controller: AbortController | null = null;

  async stream(
    port: number,
    body: Record<string, unknown>,
    callbacks: SseCallbacks,
  ): Promise<void> {
    this.abort();
    this.controller = new AbortController();

    const url = `http://127.0.0.1:${port}/api/ask`;
    console.log("[DartLab SSE] POST", url, JSON.stringify(body));

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, stream: true }),
        signal: this.controller.signal,
      });

      console.log("[DartLab SSE] Response status:", res.status);

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        console.error("[DartLab SSE] Error response:", text);
        callbacks.onError(`Server returned ${res.status}: ${text}`);
        return;
      }

      if (!res.body) {
        console.error("[DartLab SSE] No response body");
        callbacks.onError("No response body");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent: string | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            const raw = line.slice(5).trim();
            if (currentEvent) {
              try {
                const data = JSON.parse(raw);
                console.log("[DartLab SSE] Event:", currentEvent, typeof data === "object" ? JSON.stringify(data).slice(0, 100) : data);
                callbacks.onEvent(currentEvent, data);
              } catch {
                // data might be plain text, try wrapping
                console.log("[DartLab SSE] Non-JSON data for event:", currentEvent, raw.slice(0, 80));
                callbacks.onEvent(currentEvent, { text: raw });
              }
              currentEvent = null;
            }
          }
        }
      }

      console.log("[DartLab SSE] Stream ended normally");
      callbacks.onDone();
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") {
        console.log("[DartLab SSE] Aborted by user");
        callbacks.onDone();
      } else {
        const msg = err instanceof Error ? err.message : "Unknown error";
        console.error("[DartLab SSE] Error:", msg);
        callbacks.onError(msg);
      }
    } finally {
      this.controller = null;
    }
  }

  abort(): void {
    this.controller?.abort();
    this.controller = null;
  }
}
