/**
 * stdio E2E test -- actually spawns `dartlab chat --stdio` and verifies
 * the JSON Lines protocol works end-to-end.
 * No vscode mock needed -- pure child_process test.
 */
import { describe, it, expect } from "vitest";
import { spawn } from "child_process";
import { createInterface } from "readline";

/** Spawn dartlab chat --stdio and collect events until done/exit. */
function spawnStdio(
  input: string[],
  timeoutMs = 20_000,
): Promise<Array<{ event: string; data: Record<string, unknown>; id?: string }>> {
  return new Promise((resolve, reject) => {
    const events: Array<{ event: string; data: Record<string, unknown>; id?: string }> = [];
    const proc = spawn("dartlab", ["chat", "--stdio"], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    const rl = createInterface({ input: proc.stdout!, crlfDelay: Infinity });
    const timeout = setTimeout(() => {
      proc.kill("SIGKILL");
      reject(new Error(`Timeout after ${timeoutMs}ms. Got events: ${JSON.stringify(events.map(e => e.event))}`));
    }, timeoutMs);

    rl.on("line", (line) => {
      try {
        const msg = JSON.parse(line);
        events.push(msg);
      } catch { /* non-JSON */ }
    });

    proc.on("exit", () => {
      clearTimeout(timeout);
      resolve(events);
    });

    proc.on("error", (err) => {
      clearTimeout(timeout);
      reject(err);
    });

    // Write input lines then close stdin
    for (const line of input) {
      proc.stdin!.write(line + "\n");
    }
    proc.stdin!.end();
  });
}

describe("dartlab chat --stdio protocol", () => {
  it("emits ready on startup", async () => {
    const events = await spawnStdio(['{"type":"exit"}']);
    expect(events.length).toBeGreaterThanOrEqual(1);
    expect(events[0].event).toBe("ready");
    expect(events[0].data).toHaveProperty("version");
  });

  it("responds to ping with pong", async () => {
    const events = await spawnStdio([
      '{"type":"ping"}',
      '{"type":"exit"}',
    ]);
    const eventNames = events.map((e) => e.event);
    expect(eventNames).toContain("ready");
    expect(eventNames).toContain("pong");
  });

  it("returns status with provider info", async () => {
    const events = await spawnStdio([
      '{"type":"status"}',
      '{"type":"exit"}',
    ]);
    const status = events.find((e) => e.event === "status");
    expect(status).toBeDefined();
    expect(status!.data).toHaveProperty("provider");
    expect(status!.data).toHaveProperty("ready");
  });

  it("handles setProvider", async () => {
    const events = await spawnStdio([
      '{"type":"setProvider","provider":"gemini","model":"gemini-2.5-flash"}',
      '{"type":"exit"}',
    ]);
    const changed = events.find((e) => e.event === "providerChanged");
    expect(changed).toBeDefined();
    expect(changed!.data.provider).toBe("gemini");
    expect(changed!.data.model).toBe("gemini-2.5-flash");
  });

  it("ask emits meta and done (at minimum)", async () => {
    const events = await spawnStdio([
      '{"id":"t1","type":"ask","question":"hi"}',
      '{"type":"exit"}',
    ], 30_000);

    const eventNames = events.map((e) => e.event);
    expect(eventNames).toContain("ready");
    expect(eventNames).toContain("meta");
    expect(eventNames).toContain("done");

    // done should have matching id
    const done = events.find((e) => e.event === "done" && e.id === "t1");
    expect(done).toBeDefined();
  });

  it("ask with question produces chunks or error", async () => {
    const events = await spawnStdio([
      '{"id":"t2","type":"ask","question":"hello"}',
      '{"type":"exit"}',
    ], 30_000);

    const t2Events = events.filter((e) => e.id === "t2");
    const eventNames = t2Events.map((e) => e.event);

    // Should have meta
    expect(eventNames).toContain("meta");

    // Should have either chunks (success) or error (no provider)
    const hasChunks = eventNames.includes("chunk");
    const hasError = eventNames.includes("error");
    expect(hasChunks || hasError).toBe(true);

    // Should end with done
    expect(eventNames[eventNames.length - 1]).toBe("done");
  });
});
