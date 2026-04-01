import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = process.cwd();

describe("Build smoke", () => {
	it("keeps build output materialized for deploy previews", () => {
		const buildIndex = path.join(ROOT, "build/index.html");
		expect(existsSync(buildIndex)).toBe(true);

		const html = readFileSync(buildIndex, "utf8");
		expect(html).toContain("/assets/index-");
		expect(html).toContain("<div id=\"app\"></div>");
	});
});
