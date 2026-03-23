import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { chooseStreamFlushIndex, createStreamSmoother } from "../lib/chat/streamSmoother.js";

describe("streamSmoother", () => {
	beforeEach(() => {
		vi.useFakeTimers();
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it("prefers sentence boundaries when a complete sentence is available", () => {
		const text = "삼성전자는 좋은 회사입니다. 다음 분기 실적도 보겠습니다";
		const index = chooseStreamFlushIndex(text, { minChunkLength: 4, targetChunkLength: 10 }, false);

		expect(text.slice(0, index)).toBe("삼성전자는 좋은 회사입니다. ");
		expect(text.slice(index)).toBe("다음 분기 실적도 보겠습니다");
	});

	it("flushes buffered text after the hold limit even without punctuation", () => {
		const outputs = [];
		const smoother = createStreamSmoother((chunk) => outputs.push(chunk), {
			cadenceMs: 48,
			maxHoldMs: 180,
			minChunkLength: 4,
			targetChunkLength: 10,
			maxChunkLength: 24,
		});

		smoother.push("현금흐름과 ");
		vi.advanceTimersByTime(96);
		expect(outputs).toEqual([]);

		smoother.push("수익성이 ");
		vi.advanceTimersByTime(144);
		expect(outputs).toEqual(["현금흐름과 수익성이 "]);
		expect(smoother.getBufferedText()).toBe("");
	});

	it("flushes the remaining draft immediately on completion", () => {
		const outputs = [];
		const smoother = createStreamSmoother((chunk) => outputs.push(chunk), {
			cadenceMs: 48,
			maxHoldMs: 180,
			minChunkLength: 4,
			targetChunkLength: 10,
			maxChunkLength: 24,
		});

		smoother.push("HBM 증설");
		expect(outputs).toEqual([]);

		smoother.flush();
		expect(outputs).toEqual(["HBM 증설"]);
		expect(smoother.getBufferedText()).toBe("");
	});
});
