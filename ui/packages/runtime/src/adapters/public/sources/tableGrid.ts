// panel contentRaw 의 HTML 표(서술 II.사업의내용: 생산능력·가동률·원재료·주요제품·매출수주)를
// rowspan/colspan 격자전개로 직사각 정규화. providers/dart/panel/text.py::parsePanelXmlTables 동형
// (런타임 TS 포팅, 정규식 기반. 브라우저 DOMParser 비의존, xbrlCells.ts 와 동일 관례).
// 기존 파서가 ROWSPAN/COLSPAN 을 버려 후속 행이 헤더보다 짧아지던 셀 밀림(ragged)을 제거해 헤더 정렬 복원.

const TABLE_RE = /<TABLE\b[^>]*>([\s\S]*?)<\/TABLE>/gi;
const TR_RE = /<TR\b[^>]*>([\s\S]*?)<\/TR>/gi;
const CELL_RE = /<(TD|TH|TE|TU)\b([^>]*)>([\s\S]*?)<\/\1>/gi;

const stripTags = (s: string): string => (s || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

interface SpanCell {
	text: string;
	rspan: number;
	cspan: number;
}

function spanOf(attrs: string, name: string): number {
	const m = new RegExp(name + '\\s*=\\s*"?(\\d+)', 'i').exec(attrs);
	const v = m ? parseInt(m[1]!, 10) : 1;
	return Number.isFinite(v) && v >= 1 ? v : 1;
}

function parseTableCells(tableInner: string): SpanCell[][] {
	const rows: SpanCell[][] = [];
	const trs = tableInner.match(TR_RE);
	if (!trs) return rows;
	for (const tr of trs) {
		const cells: SpanCell[] = [];
		let m: RegExpExecArray | null;
		CELL_RE.lastIndex = 0;
		while ((m = CELL_RE.exec(tr)) !== null) {
			cells.push({ text: stripTags(m[3]!), rspan: spanOf(m[2]!, 'ROWSPAN'), cspan: spanOf(m[2]!, 'COLSPAN') });
		}
		if (cells.length) rows.push(cells);
	}
	return rows;
}

/** span 보존 셀 → 직사각 격자(rowspan 아래 forward-fill·colspan 오른쪽 채움). 표준 HTML 표 격자 알고리즘. */
export function expandGrid(rowCells: SpanCell[][]): string[][] {
	const active = new Map<number, { rem: number; text: string }>();
	const out: string[][] = [];
	const maxActive = (): number => {
		let mx = -1;
		for (const k of active.keys()) if (k > mx) mx = k;
		return mx;
	};
	for (const cells of rowCells) {
		const rowArr: string[] = [];
		let col = 0;
		for (const { text, rspan, cspan } of cells) {
			while (active.has(col)) {
				const a = active.get(col)!;
				rowArr.push(a.text);
				if (--a.rem <= 0) active.delete(col);
				col += 1;
			}
			for (let k = 0; k < cspan; k++) {
				rowArr.push(text);
				if (rspan > 1) active.set(col, { rem: rspan - 1, text });
				col += 1;
			}
		}
		while (active.size && maxActive() >= col) {
			const a = active.get(col);
			if (a) {
				rowArr.push(a.text);
				if (--a.rem <= 0) active.delete(col);
			} else {
				rowArr.push('');
			}
			col += 1;
		}
		out.push(rowArr);
	}
	const width = out.reduce((w, r) => Math.max(w, r.length), 0);
	return out.map((r) => (r.length < width ? r.concat(Array(width - r.length).fill('')) : r));
}

/** colspan 으로 생긴 완전 중복 인접 열을 1개로 합침 (모든 행 값 동일 열만). */
export function collapseColspanDupes(grid: string[][]): string[][] {
	if (!grid.length || !grid[0]!.length) return grid;
	const ncol = grid[0]!.length;
	const keep = [0];
	for (let c = 1; c < ncol; c++) {
		if (!grid.every((row) => row[c] === row[c - 1])) keep.push(c);
	}
	return grid.map((row) => keep.map((c) => row[c]!));
}

/** DART XML 조각(0+ TABLE) → span-aware 직사각 격자 리스트. 헤더+1행 이상만. */
export function expandTables(content: string): string[][][] {
	const out: string[][][] = [];
	if (!content) return out;
	let m: RegExpExecArray | null;
	TABLE_RE.lastIndex = 0;
	while ((m = TABLE_RE.exec(content)) !== null) {
		const rowCells = parseTableCells(m[1]!);
		if (rowCells.length >= 2) out.push(expandGrid(rowCells));
	}
	return out;
}

/** 직사각 격자(headerRow=헤더) → row dict 리스트. colspan 중복열 합침 + 헤더 중복키 suffix. */
export function gridToRowDicts(grid: string[][], headerRow = 0): Record<string, string>[] {
	const g = collapseColspanDupes(grid.slice(headerRow));
	if (g.length < 2) return [];
	const seen = new Map<string, number>();
	const keys = g[0]!.map((h, i) => {
		const name = h || `col${i}`;
		if (seen.has(name)) {
			const n = seen.get(name)! + 1;
			seen.set(name, n);
			return `${name}.${n}`;
		}
		seen.set(name, 0);
		return name;
	});
	return g.slice(1).map((row) => {
		const o: Record<string, string> = {};
		keys.forEach((k, i) => (o[k] = row[i] ?? ''));
		return o;
	});
}
