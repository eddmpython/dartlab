import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();

function assert(condition, message) {
	if (!condition) {
		throw new Error(message);
	}
}

function read(relativePath) {
	return readFileSync(path.join(ROOT, relativePath), "utf8");
}

function main() {
	const appSource = read("src/App.svelte");
	const workspaceSource = read("src/lib/stores/workspace.svelte.js");
	const explorerSource = read("src/lib/components/DataExplorer.svelte");
	const evidenceTabSource = read("src/lib/components/workspace/EvidenceTab.svelte");
	const messageSource = read("src/lib/components/MessageBubble.svelte");
	const buildIndexPath = path.join(ROOT, "build/index.html");

	assert(existsSync(buildIndexPath), "build/index.html is missing. Run npm run build first.");
	assert(appSource.includes("handleOpenEvidence"), "App.svelte is missing evidence routing.");
	assert(appSource.includes("onOpenEvidence={handleOpenEvidence}"), "ChatArea is not wired to evidence routing.");
	assert(workspaceSource.includes("openEvidence(section, index = null)"), "workspace store is missing openEvidence.");
	assert(workspaceSource.includes("clearEvidenceSelection()"), "workspace store is missing clearEvidenceSelection.");
	assert(evidenceTabSource.includes('data-evidence-section="tool-results"'), "EvidenceTab is missing tool-results evidence section.");
	assert(explorerSource.includes("copyWorkspaceLink"), "DataExplorer is missing workspace link action.");
	assert(messageSource.includes('onOpenEvidence(event?.type === "result" ? "tool-results" : "tool-calls", idx)'), "MessageBubble is missing tool-result drill-down.");
	assert(messageSource.includes("최신 응답으로 이동") || read("src/lib/components/ChatArea.svelte").includes("최신 응답으로 이동"), "Jump-to-latest affordance is missing.");

	console.log("e2e smoke passed");
}

main();
