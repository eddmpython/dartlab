import { describe, expect, it } from 'vitest';
import {
	CONTENT_ROW_LIMIT,
	CONTENT_TREE_NODE_LIMIT,
	parseDelimitedPreview,
	parseJsonTreePreview,
	universeContentKind,
	universeContentMime
} from './contentAdapters';

describe('Universe content adapters', () => {
	it('classifies structured and media formats without treating them as generic binary', () => {
		expect(universeContentKind('facts/company.csv')).toBe('table');
		expect(universeContentKind('facts/company.tsv')).toBe('table');
		expect(universeContentKind('docs/index.json')).toBe('json');
		expect(universeContentKind('assets/guide.mp4')).toBe('video');
		expect(universeContentMime('table', 'facts/company.csv')).toBe('text/csv');
	});

	it('parses bounded CSV rows with quotes, embedded newlines and stable duplicate headers', () => {
		const source = 'name,name,note\n"DartLab","DL","line 1\nline 2"\n"SEC","US","quoted ""value"""\n';
		const preview = parseDelimitedPreview(source, ',');
		expect(preview.columns).toEqual(['name', 'name_2', 'note']);
		expect(preview.rows).toHaveLength(2);
		expect(preview.rows[0]?.note).toBe('line 1\nline 2');
		expect(preview.rows[1]?.note).toBe('quoted "value"');

		const partial = parseDelimitedPreview('id,name\n1,DartLab\n2,part', ',', true);
		expect(partial.rows).toEqual([{ id: '1', name: 'DartLab' }]);
		expect(partial.truncated).toBe(true);
	});

	it('bounds delimited and JSON projections while keeping their hierarchy explicit', () => {
		const csv = ['id,value', ...Array.from({ length: CONTENT_ROW_LIMIT + 3 }, (_, index) => `${index},${index * 2}`)].join('\n');
		const table = parseDelimitedPreview(csv, ',');
		expect(table.rows).toHaveLength(CONTENT_ROW_LIMIT);
		expect(table.truncated).toBe(true);

		const json = JSON.stringify({ companies: Array.from({ length: 120 }, (_, index) => ({ id: index, active: index % 2 === 0 })) });
		const tree = parseJsonTreePreview(json, 'companies.json');
		expect(tree).not.toBeNull();
		expect(tree?.tree[0]).toMatchObject({ key: '$', valueKind: 'object', childCount: 1, pointer: '' });
		expect(tree?.tree.length).toBeLessThanOrEqual(CONTENT_TREE_NODE_LIMIT);
		expect(tree?.truncated).toBe(true);
	});

	it('keeps complete JSONL records when a byte range ends inside a line', () => {
		const preview = parseJsonTreePreview('{"id":1}\n{"id":2}\n{"id":', 'events.jsonl', true);
		expect(preview?.tree.filter((node) => node.key === 'id').map((node) => node.value)).toEqual(['1', '2']);
		expect(preview?.tree.find((node) => node.key === 'id')?.pointer).toBe('/0/id');
		expect(preview?.truncated).toBe(true);
	});

	it('pages wide delimited columns without changing row identity', () => {
		const header = Array.from({ length: 20 }, (_, index) => `c${index + 1}`).join(',');
		const row = Array.from({ length: 20 }, (_, index) => `v${index + 1}`).join(',');
		const preview = parseDelimitedPreview(`${header}\n${row}\n`, ',', false, 16);
		expect(preview.totalColumns).toBe(20);
		expect(preview.columnStart).toBe(16);
		expect(preview.columns).toEqual(['c17', 'c18', 'c19', 'c20']);
		expect(preview.rows[0]?.c20).toBe('v20');
	});
});
