/**
 * 스트리밍 콘텐츠 분리 — 완료된 부분과 진행 중인 부분을 나눈다.
 *
 * 테이블이나 코드 펜스가 아직 닫히지 않았으면 draft로 분류해서
 * 깨진 마크다운 렌더링을 방지한다.
 */

const TABLE_LINE_RE = /^\s*\|.+\|\s*$/;
const CODE_FENCE_RE = /^```[\w-]*$/;

function computeSplit(text) {
	const lines = text.split("\n");
	let safeIndex = lines.length;

	if (!text.endsWith("\n")) safeIndex = Math.min(safeIndex, lines.length - 1);

	// 열린 코드 펜스 감지 (언어 지정도 인식)
	let codeFenceCount = 0;
	let lastFenceLine = -1;
	for (let i = 0; i < lines.length; i++) {
		if (CODE_FENCE_RE.test(lines[i].trim())) {
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

	let draftType = "text";
	if (trailingTableStart >= 0 && trailingTableStart <= safeIndex) draftType = "table";
	else if (codeFenceCount % 2 === 1) draftType = "code";

	return { lines, safeIndex, draftType };
}

export function splitStreamingContent(text, loading) {
	if (!text) return { committed: "", draft: "", draftType: "none" };
	if (!loading) return { committed: text, draft: "", draftType: "none" };

	const { lines, safeIndex, draftType } = computeSplit(text);

	if (safeIndex <= 0) {
		return { committed: "", draft: text, draftType };
	}

	const committed = lines.slice(0, safeIndex).join("\n");
	const draft = lines.slice(safeIndex).join("\n");
	return { committed, draft, draftType: draft ? draftType : "none" };
}

/**
 * Monotonic 스트림 분리기 — committed 영역이 줄어드는 것을 방지.
 * 메시지별로 인스턴스를 생성해서 사용.
 */
export function createStreamSplitter() {
	let maxSafeIndex = 0;
	let prevLineCount = 0;
	let fenceCount = 0;
	let lastFenceLine = -1;
	let prevLastLineFence = false;

	return {
		split(text, loading) {
			if (!text) return { committed: "", draft: "", draftType: "none" };
			if (!loading) { this.reset(); return { committed: text, draft: "", draftType: "none" }; }

			const lines = text.split("\n");
			let safeIndex = lines.length;
			if (!text.endsWith("\n")) safeIndex = Math.min(safeIndex, lines.length - 1);

			// 증분 코드펜스 카운트: 새로 추가된 라인만 검사
			const scanStart = Math.max(0, prevLineCount - 1);
			// 이전 마지막 라인이 펜스였으면 재검사 시 중복 방지
			if (prevLastLineFence && scanStart < lines.length && scanStart === prevLineCount - 1) {
				// 이전에 카운트한 마지막 라인을 빼고 재검사
				fenceCount -= 1;
				if (lastFenceLine === scanStart) lastFenceLine = -1;
			}
			let lastLineFence = false;
			for (let i = scanStart; i < lines.length; i++) {
				if (CODE_FENCE_RE.test(lines[i].trim())) {
					fenceCount += 1;
					lastFenceLine = i;
					if (i === lines.length - 1) lastLineFence = true;
				}
			}
			prevLineCount = lines.length;
			prevLastLineFence = lastLineFence;

			if (fenceCount % 2 === 1 && lastFenceLine >= 0) {
				safeIndex = Math.min(safeIndex, lastFenceLine);
			}

			// trailing table 감지 (뒤에서만 역순 — O(trailing))
			let trailingTableStart = -1;
			for (let i = lines.length - 1; i >= 0; i--) {
				const line = lines[i];
				if (!line.trim()) break;
				if (TABLE_LINE_RE.test(line)) trailingTableStart = i;
				else { trailingTableStart = -1; break; }
			}
			if (trailingTableStart >= 0) {
				safeIndex = Math.min(safeIndex, trailingTableStart);
			}

			let draftType = "text";
			if (trailingTableStart >= 0 && trailingTableStart <= safeIndex) draftType = "table";
			else if (fenceCount % 2 === 1) draftType = "code";

			// monotonic: committed 영역은 줄어들지 않음
			const effectiveIndex = Math.max(safeIndex, maxSafeIndex);
			const clamped = Math.min(effectiveIndex, lines.length);
			maxSafeIndex = clamped;

			if (clamped <= 0) {
				return { committed: "", draft: text, draftType };
			}

			const committed = lines.slice(0, clamped).join("\n");
			const draft = lines.slice(clamped).join("\n");
			return { committed, draft, draftType: draft ? draftType : "none" };
		},
		reset() {
			maxSafeIndex = 0;
			prevLineCount = 0;
			fenceCount = 0;
			lastFenceLine = -1;
			prevLastLineFence = false;
		},
	};
}
