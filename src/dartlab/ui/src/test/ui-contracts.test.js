import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = process.cwd();

function read(relativePath) {
	return readFileSync(path.join(ROOT, relativePath), "utf8");
}

describe("UI contracts", () => {
	it("keeps workspace evidence state as a first-class store contract", () => {
		const source = read("src/lib/stores/workspace.svelte.js");

		expect(source).toContain("activeEvidenceSection");
		expect(source).toContain("selectedEvidenceIndex");
		expect(source).toContain("function openEvidence(section, index = null)");
		expect(source).toContain("function clearEvidenceSelection()");
		expect(source).toContain('if (activeTab !== "evidence")');
		expect(source).toContain("selectedEvidenceIndex = Number.isInteger(index) ? index : null");
	});

	it("routes message transparency clicks into the shared evidence workflow", () => {
		const appSource = read("src/App.svelte");
		const chatAreaSource = read("src/lib/components/ChatArea.svelte");
		const messageSource = read("src/lib/components/MessageBubble.svelte");

		expect(appSource).toContain("function handleOpenEvidence(section, index = null)");
		expect(appSource).toContain("workspace.openEvidence(section, index)");
		expect(appSource).toContain("onOpenEvidence={handleOpenEvidence}");

		expect(chatAreaSource).toContain("onOpenEvidence");
		expect(chatAreaSource).toContain("onOpenEvidence={onOpenEvidence}");

		expect(messageSource).toContain('onOpenEvidence("contexts", idx)');
		expect(messageSource).toContain('onOpenEvidence("snapshot")');
		expect(messageSource).toContain('onOpenEvidence(event?.type === "result" ? "tool-results" : "tool-calls", idx)');
		expect(messageSource).toContain('onOpenEvidence("system")');
		expect(messageSource).toContain('onOpenEvidence("input")');
	});

	it("keeps the workspace evidence panel readable and drill-down capable", () => {
		const source = read("src/lib/components/DataExplorer.svelte");

		expect(source).toContain('data-evidence-section="snapshot"');
		expect(source).toContain('data-evidence-section="contexts"');
		expect(source).toContain('data-evidence-section="tool-calls"');
		expect(source).toContain('data-evidence-section="tool-results"');
		expect(source).toContain("tool-result");
		expect(source).toContain("프롬프트 투명성");
		expect(source).toContain("도구 결과");
		expect(source).toContain("selectedEvidenceIndex");
	});

	it("keeps the empty state aligned to the README product message", () => {
		const source = read("src/lib/components/EmptyState.svelte");

		expect(source).toContain("재무 수치와 서술 텍스트");
		expect(source).toContain("표준화된 계정");
		expect(source).toContain("40개 모듈");
		expect(source).toContain("원문 근거");
		expect(source).toContain("Evidence First");
	});

	it("preserves the stable streaming affordance in chat", () => {
		const source = read("src/lib/components/ChatArea.svelte");

		expect(source).toContain("followStream");
		expect(source).toContain("showJumpToLatest");
		expect(source).toContain("streamAnchor.scrollIntoView");
		expect(source).toContain("최신 응답으로 이동");
	});
});
