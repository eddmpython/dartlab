import { expandQuery, plainText, type SearchHit } from './searchIndex';

export interface DeepSearchRow {
	sectionKey: string;
	rowIndex: number;
	chapter: string;
	section: string;
	block: string;
	scope: string;
	cells: Record<string, string>;
}

export interface DeepSearchResult {
	ms: number;
	rows: number;
	hits: SearchHit[];
	added: string[];
}

export interface DeepSearchOpts {
	topK?: number;
	expand?: boolean;
	cellCap?: number;
	chunkRows?: number;
}

function surfaceNeedles(query: string, added: string[]): string[] {
	const needles = new Set<string>();
	for (const source of [query, ...added]) {
		for (const m of source.matchAll(/[가-힣A-Za-z0-9]{2,}/g)) needles.add(m[0].toLowerCase());
	}
	return [...needles].sort((a, b) => b.length - a.length);
}

function snippetAround(text: string, at: number): string {
	const start = Math.max(0, at - 34);
	const end = Math.min(text.length, at + 96);
	return text.slice(start, end);
}

function matchNeedles(text: string, needles: string[]): { matchedTerms: string[]; bestAt: number } {
	const matchedTerms: string[] = [];
	let bestAt = Number.POSITIVE_INFINITY;
	for (const needle of needles) {
		const at = text.indexOf(needle);
		if (at >= 0) {
			bestAt = Math.min(bestAt, at);
			matchedTerms.push(needle);
		}
	}
	return { matchedTerms, bestAt };
}

function plainCellText(raw: string): string {
	return plainText(raw)
		.replace(/<[^>]*$/g, ' ')
		.replace(/\s+/g, ' ')
		.trim();
}

function yieldToMain(): Promise<void> {
	return new Promise((resolve) => {
		const ch = new MessageChannel();
		ch.port1.onmessage = () => {
			ch.port1.close();
			ch.port2.close();
			resolve();
		};
		ch.port2.postMessage(null);
	});
}

function scanRow(row: DeepSearchRow, weights: Map<string, number>, needles: string[], cellCap: number): SearchHit | null {
	const label = `${row.chapter} ${row.section} ${row.block}`.toLowerCase();
	let labelScore = 0;
	for (const term of weights.keys()) {
		if (label.includes(term)) labelScore += 0.7;
	}
	let best: SearchHit | null = null;
	const periodsDesc = Object.keys(row.cells).sort().reverse();
	for (const period of periodsDesc) {
		const raw = row.cells[period];
		if (!raw) continue;
		const capped = raw.length > cellCap ? raw.slice(0, cellCap) : raw;
		const rawMatch = matchNeedles(capped.toLowerCase(), needles);
		if (labelScore <= 0 && rawMatch.matchedTerms.length === 0) continue;
		let score = labelScore;
		for (const needle of rawMatch.matchedTerms) {
			score += needle.length >= 4 ? 3 : 2;
		}
		if (score <= 0) continue;
		const text = plainCellText(capped);
		const textMatch = rawMatch.matchedTerms.length ? matchNeedles(text.toLowerCase(), rawMatch.matchedTerms) : rawMatch;
		const hit: SearchHit = {
			sectionKey: row.sectionKey,
			rowIndex: row.rowIndex,
			chapter: row.chapter,
			section: row.section,
			block: row.block,
			scope: row.scope,
			period,
			score,
			snippet: Number.isFinite(textMatch.bestAt) ? snippetAround(text, textMatch.bestAt) : text.slice(0, 96),
			matchKind: 'table',
			matchedTerms: rawMatch.matchedTerms.slice(0, 8),
			stale: false // deepSearch 는 특정 period 셀의 직접 매칭 · 행-최신 비교 없음(해당 셀 자체가 근거)
		};
		if (!best || hit.score > best.score) best = hit;
	}
	return best;
}

export async function scanDeepRowsChunked(rows: DeepSearchRow[], query: string, opts: DeepSearchOpts = {}): Promise<DeepSearchResult> {
	const started = performance.now();
	const { weights, added } = expandQuery(query, opts.expand ?? true);
	const needles = surfaceNeedles(query, added);
	const scored: SearchHit[] = [];
	const cellCap = opts.cellCap ?? 1000;
	const chunkRows = opts.chunkRows ?? 64;
	let since = 0;
	for (const row of rows) {
		const hit = scanRow(row, weights, needles, cellCap);
		if (hit) scored.push(hit);
		if (++since >= chunkRows) {
			since = 0;
			await yieldToMain();
		}
	}
	scored.sort((a, b) => b.score - a.score);
	return {
		ms: performance.now() - started,
		rows: rows.length,
		hits: scored.slice(0, opts.topK ?? 20),
		added
	};
}
