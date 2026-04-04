import { describe, it, expect } from "vitest";
import { buildCandidates } from "../bridge/stdioProxy";

describe("buildCandidates", () => {
  it("returns uv, python, python3, dartlab without pythonPath", () => {
    const candidates = buildCandidates();
    const labels = candidates.map((c) => c.label);

    expect(labels).toContain("uv run python -m dartlab");
    expect(labels).toContain("python -m dartlab");
    expect(labels).toContain("python3 -m dartlab");
    expect(labels).toContain("dartlab chat --stdio");
  });

  it("puts explicit pythonPath first", () => {
    const candidates = buildCandidates("/usr/bin/python3.12");
    expect(candidates[0].cmd).toBe("/usr/bin/python3.12");
    expect(candidates[0].args).toContain("-m");
    expect(candidates[0].args).toContain("dartlab");
  });

  it("uv candidate uses 'run' subcommand", () => {
    const candidates = buildCandidates();
    const uv = candidates.find((c) => c.cmd === "uv");
    expect(uv).toBeDefined();
    expect(uv!.args[0]).toBe("run");
  });

  it("dartlab CLI candidate uses chat --stdio", () => {
    const candidates = buildCandidates();
    const dl = candidates.find((c) => c.cmd === "dartlab");
    expect(dl).toBeDefined();
    expect(dl!.args).toEqual(["chat", "--stdio"]);
  });
});
