import type {
	UniverseKnowledgeContent,
	UniverseKnowledgeTreeNode,
	UniverseKnowledgeTreeValueKind
} from '@dartlab/ui-contracts';

export const CONTENT_BYTE_LIMIT = 64 * 1024;
export const CONTENT_TEXT_DISPLAY_LIMIT = 20 * 1024;
export const CONTENT_ROW_LIMIT = 12;
export const CONTENT_COLUMN_LIMIT = 16;
export const CONTENT_TREE_NODE_LIMIT = 96;
const CONTENT_TREE_DEPTH_LIMIT = 7;

export function universeContentKind(path: string): UniverseKnowledgeContent['kind'] {
	const lower = path.toLocaleLowerCase();
	if (/\.(png|webp|jpe?g|gif|svg|avif)$/.test(lower)) return 'image';
	if (/\.(mp4|webm|mov)$/.test(lower)) return 'video';
	if (/\.(m4a|mp3|wav|ogg|flac)$/.test(lower)) return 'audio';
	if (/\.(parquet|csv|tsv)$/.test(lower)) return 'table';
	if (/\.(json|jsonl|ndjson)$/.test(lower)) return 'json';
	if (/\.(md|mdx|txt|xml|html?|ya?ml|toml|ini|py|ts|js|css|sql)$/.test(lower)) return 'text';
	return 'binary';
}

export function universeContentMime(kind: UniverseKnowledgeContent['kind'], path: string): string {
	const extension = path.split('.').at(-1)?.toLocaleLowerCase() ?? '';
	if (kind === 'image') return extension === 'svg' ? 'image/svg+xml' : `image/${extension === 'jpg' ? 'jpeg' : extension}`;
	if (kind === 'video') return `video/${extension === 'mov' ? 'quicktime' : extension}`;
	if (kind === 'audio') return `audio/${extension === 'm4a' ? 'mp4' : extension}`;
	if (kind === 'json') return extension === 'json' ? 'application/json' : 'application/x-ndjson';
	if (extension === 'parquet') return 'application/vnd.apache.parquet';
	if (extension === 'csv') return 'text/csv';
	if (extension === 'tsv') return 'text/tab-separated-values';
	if (kind === 'text') return extension === 'html' || extension === 'htm' ? 'text/html' : 'text/plain';
	return 'application/octet-stream';
}

export function printableCell(value: unknown): string {
	if (value === null || value === undefined) return '';
	if (typeof value === 'bigint') return value.toString();
	if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
	try {
		return JSON.stringify(value, (_, item: unknown) => typeof item === 'bigint' ? item.toString() : item);
	} catch {
		return String(value);
	}
}

function uniqueColumns(header: readonly string[]): string[] {
	const seen = new Map<string, number>();
	return header.slice(0, CONTENT_COLUMN_LIMIT).map((raw, index) => {
		const base = raw.trim() || `column_${index + 1}`;
		const occurrence = (seen.get(base) ?? 0) + 1;
		seen.set(base, occurrence);
		return occurrence === 1 ? base : `${base}_${occurrence}`;
	});
}

function scanDelimited(text: string, delimiter: ',' | '\t', rowLimit: number): string[][] {
	const rows: string[][] = [];
	let row: string[] = [];
	let cell = '';
	let quoted = false;
	for (let index = 0; index < text.length && rows.length < rowLimit; index += 1) {
		const char = text[index];
		if (char === '"') {
			if (quoted && text[index + 1] === '"') {
				cell += '"';
				index += 1;
			} else {
				quoted = !quoted;
			}
			continue;
		}
		if (!quoted && char === delimiter) {
			row.push(cell);
			cell = '';
			continue;
		}
		if (!quoted && (char === '\n' || char === '\r')) {
			if (char === '\r' && text[index + 1] === '\n') index += 1;
			row.push(cell);
			if (row.some((value) => value.length > 0)) rows.push(row);
			row = [];
			cell = '';
			continue;
		}
		cell += char;
	}
	if (rows.length < rowLimit && (cell.length > 0 || row.length > 0)) {
		row.push(cell);
		if (row.some((value) => value.length > 0)) rows.push(row);
	}
	return rows;
}

export interface DelimitedPreview {
	columns: readonly string[];
	rows: readonly Readonly<Record<string, string>>[];
	truncated: boolean;
}

export function parseDelimitedPreview(text: string, delimiter: ',' | '\t', sourceTruncated = false): DelimitedPreview {
	const scanned = scanDelimited(text, delimiter, CONTENT_ROW_LIMIT + 2);
	if (sourceTruncated && !/[\r\n]$/.test(text)) scanned.pop();
	const columns = Object.freeze(uniqueColumns(scanned[0] ?? []));
	const body = scanned.slice(1, CONTENT_ROW_LIMIT + 1);
	const rows = Object.freeze(body.map((values) => Object.freeze(Object.fromEntries(columns.map((column, index) => [column, values[index] ?? ''])))));
	return Object.freeze({ columns, rows, truncated: sourceTruncated || scanned.length > CONTENT_ROW_LIMIT + 1 });
}

function treeValueKind(value: unknown): UniverseKnowledgeTreeValueKind {
	if (value === null) return 'null';
	if (Array.isArray(value)) return 'array';
	if (typeof value === 'object') return 'object';
	if (typeof value === 'number') return 'number';
	if (typeof value === 'boolean') return 'boolean';
	return 'string';
}

function treeChildren(value: unknown): readonly [string, unknown][] {
	if (Array.isArray(value)) return value.map((item, index) => [String(index), item]);
	if (value && typeof value === 'object') return Object.entries(value as Record<string, unknown>);
	return [];
}

function treeScalar(value: unknown): string {
	if (value === null) return 'null';
	if (typeof value === 'string') return value;
	if (typeof value === 'number' || typeof value === 'boolean') return String(value);
	return '';
}

export interface JsonTreePreview {
	formattedText: string;
	tree: readonly UniverseKnowledgeTreeNode[];
	truncated: boolean;
}

export function parseJsonTreePreview(text: string, path: string): JsonTreePreview | null {
	let root: unknown;
	let projectionTruncated = false;
	try {
		if (/\.(jsonl|ndjson)$/i.test(path)) {
			const lines = text.split(/\r?\n/).filter((line) => line.trim());
			projectionTruncated = lines.length > CONTENT_ROW_LIMIT;
			root = lines.slice(0, CONTENT_ROW_LIMIT).map((line) => JSON.parse(line));
		} else {
			root = JSON.parse(text);
		}
	} catch {
		return null;
	}
	const nodes: UniverseKnowledgeTreeNode[] = [];
	const visit = (key: string, value: unknown, depth: number, lineage: string): void => {
		if (nodes.length >= CONTENT_TREE_NODE_LIMIT) {
			projectionTruncated = true;
			return;
		}
		const children = treeChildren(value);
		nodes.push(Object.freeze({
			nodeId: `${lineage}:${nodes.length}`,
			key,
			value: treeScalar(value),
			valueKind: treeValueKind(value),
			depth,
			childCount: children.length
		}));
		if (depth >= CONTENT_TREE_DEPTH_LIMIT) {
			if (children.length > 0) projectionTruncated = true;
			return;
		}
		for (const [childKey, childValue] of children) {
			if (nodes.length >= CONTENT_TREE_NODE_LIMIT) break;
			visit(childKey, childValue, depth + 1, `${lineage}/${childKey}`);
		}
	};
	visit('$', root, 0, '$');
	const formattedText = JSON.stringify(root, null, 2);
	return Object.freeze({
		formattedText,
		tree: Object.freeze(nodes),
		truncated: projectionTruncated || nodes.length >= CONTENT_TREE_NODE_LIMIT || formattedText.length > CONTENT_TEXT_DISPLAY_LIMIT
	});
}
