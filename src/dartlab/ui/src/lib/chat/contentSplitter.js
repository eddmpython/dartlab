/**
 * 스트리밍 콘텐츠 분리 — 완료된 부분과 진행 중인 부분을 나눈다.
 *
 * 테이블이나 코드 펜스가 아직 닫히지 않았으면 draft로 분류해서
 * 깨진 마크다운 렌더링을 방지한다.
 */

const TABLE_LINE_RE = /^\s*\|.+\|\s*$/;

export function splitStreamingContent(text, loading) {
	if (!text) return { committed: "", draft: "", draftType: "none" };
	if (!loading) return { committed: text, draft: "", draftType: "none" };

	const lines = text.split("\n");
	let safeIndex = lines.length;

	if (!text.endsWith("\n")) safeIndex = Math.min(safeIndex, lines.length - 1);

	// 열린 코드 펜스 감지
	let codeFenceCount = 0;
	let lastFenceLine = -1;
	for (let i = 0; i < lines.length; i++) {
		if (lines[i].trim().startsWith("```")) {
			codeFenceCount += 1;
			lastFenceLine = i;
		}
	}
	if (codeFenceCount % 2 === 1 && lastFenceLine >= 0) {
		safeIndex = Math.min(safeIndex, lastFenceLine);
	}

	// 열린 테이블 감지
	let trailingTableStart = -1;
	for (let i = lines.length - 1; i >= 0; i--) {
		const line = lines[i];
		if (!line.trim()) break;
		if (TABLE_LINE_RE.test(line)) trailingTableStart = i;
		else {
			trailingTableStart = -1;
			break;
		}
	}
	if (trailingTableStart >= 0) {
		safeIndex = Math.min(safeIndex, trailingTableStart);
	}

	if (safeIndex <= 0) {
		return {
			committed: "",
			draft: text,
			draftType: trailingTableStart === 0 ? "table" : codeFenceCount % 2 === 1 ? "code" : "text",
		};
	}

	const committed = lines.slice(0, safeIndex).join("\n");
	const draft = lines.slice(safeIndex).join("\n");
	let draftType = "text";
	if (draft && trailingTableStart >= safeIndex) draftType = "table";
	else if (draft && codeFenceCount % 2 === 1) draftType = "code";
	return { committed, draft, draftType };
}
