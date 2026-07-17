import { describe, expect, it } from 'vitest';
import type { DataCore, RequestSpec } from '../fetch/request';
import { classifyKnowledgePath, createUniverseKnowledgeRuntime } from './knowledge';

const siblings = [
	{ rfilename: 'README.md' },
	{ rfilename: 'dart/companyProfile.parquet' },
	...Array.from({ length: 120 }, (_, index) => ({ rfilename: `dart/finance/${String(index).padStart(6, '0')}.parquet` })),
	{ rfilename: 'dart/panel/005930.parquet' },
	{ rfilename: 'edgar/prices/company/AAPL.parquet' },
	{ rfilename: 'macro/fred/GDP.parquet' },
	{ rfilename: 'news/public/20260717.parquet' },
	{ rfilename: 'assets/avatar.png' },
	{ rfilename: 'pyodide/dartlab.whl' }
];

const graph = {
	nodes: [
		{ id: 'engines.analysis', title: 'Analysis', category: 'engines', purpose: '재무 분석 엔진', inDegree: 3, outDegree: 2, cluster: 'analysis' },
		{ id: 'engines.analysis.profitability', title: '수익성', category: 'engines', purpose: 'profitability 분석', inDegree: 1, outDegree: 0, cluster: 'analysis' },
		{ id: 'recipes.fundamental', title: '기업 분석 레시피', category: 'recipes', purpose: '근거 기반 분석 절차', inDegree: 1, outDegree: 1, cluster: 'recipes' }
	],
	edges: [
		{ src: 'engines.analysis', dst: 'engines.analysis.profitability', kind: 'successor' },
		{ src: 'recipes.fundamental', dst: 'engines.analysis', kind: 'linkedRecipe' }
	]
};

const catalog = {
	meta: { skillCount: 3 },
	skills: graph.nodes.map((node) => ({ ...node, whenToUse: [node.purpose], apiRefs: [], sourceRefs: [`dartlab://skills/${node.id}`] }))
};

interface ContentCallLog {
	parquetRevision?: string;
	byteOrigin?: string;
	bytePath?: string;
}

function fakeCore(contentCalls?: ContentCallLog): DataCore {
	return {
		async request<T>(spec: RequestSpec<T>): Promise<T> {
			if (spec.path.startsWith('tree/main')) {
				return [{ type: 'directory', path: 'dart' }, { type: 'directory', path: 'edgar' }] as T;
			}
			return {
				sha: 'revision-1',
				lastModified: '2026-07-17T10:13:00.000Z',
				mainSize: 280_987_765_346,
				usedStorage: 357_622_165_328,
				...(spec.path.includes('siblings') ? { siblings } : {})
			} as T;
		},
		async requestParquetRows<T extends Record<string, unknown>>(spec: { path: string; revision?: string }) {
			if (contentCalls) contentCalls.parquetRevision = spec.revision;
			return (spec.path === 'dart/companyProfile.parquet'
				? [{ stockCode: '005930', corpName: '삼성전자', listed: true }]
				: []) as unknown as T[];
		},
		async requestParquetWholeFile() { return []; },
		async requestBytes(spec: { origin?: string; path: string }) {
			if (contentCalls) {
				contentCalls.byteOrigin = spec.origin;
				contentCalls.bytePath = spec.path;
			}
			return new TextEncoder().encode('# DartLab\n통합 지식 원문').buffer as ArrayBuffer;
		},
		clear() {}
	};
}

function runtime(contentCalls?: ContentCallLog) {
	return createUniverseKnowledgeRuntime(fakeCore(contentCalls), {
		loadSkillGraph: async () => graph,
		loadSkillCatalog: async () => catalog
	});
}

describe('Universe knowledge runtime', () => {
	it('assigns every source path to one stable knowledge domain', () => {
		expect(classifyKnowledgePath('dart/finance/005930.parquet')).toBe('observations');
		expect(classifyKnowledgePath('dart/panel/005930.parquet')).toBe('filings');
		expect(classifyKnowledgePath('edgar/prices/company/AAPL.parquet')).toBe('marketData');
		expect(classifyKnowledgePath('news/public/20260717.parquet')).toBe('intelligence');
		expect(classifyKnowledgePath('assets/avatar.png')).toBe('timeMedia');
	});

	it('opens a fast twelve-galaxy overview before the full file index', async () => {
		const overview = await runtime().overview();
		expect(overview.domains).toHaveLength(12);
		expect(overview.repository.fileCount).toBeNull();
		expect(overview.scene.nodes).toHaveLength(13);
		expect(overview.scene.edges).toHaveLength(12);
		expect(overview.skillCount).toBe(3);
	});

	it('accounts for every HF file and Skill OS item exactly once', async () => {
		const coverage = await runtime().coverage();
		const domainTotal = Object.values(coverage.domainCounts).reduce((total, value) => total + value, 0);
		expect(coverage.hfFileCount).toBe(siblings.length);
		expect(coverage.skillCount).toBe(3);
		expect(coverage.addressableItemCount).toBe(siblings.length + 3);
		expect(domainTotal).toBe(coverage.addressableItemCount);
	});

	it('searches files and skills together and keeps scenes bounded', async () => {
		const search = await runtime().search({ query: 'profitability' });
		expect(search.hits[0]?.targetId).toBe('skill:engines.analysis.profitability');
		expect(search.scene.nodes.length).toBeLessThanOrEqual(80);

		const directory = await runtime().open('hfdir:dart/finance');
		expect(directory.receipt.indexedItemCount).toBe(120);
		expect(directory.nodes).toHaveLength(80);
		expect(directory.receipt.omittedNodeCount).toBe(41);
	});

	it('keeps an exact two-segment source as a file in its domain scene', async () => {
		const entities = await runtime().open('domain:entities');
		expect(entities.nodes.some((node) => node.nodeId === 'hf:dart/companyProfile.parquet' && node.kind === 'entity')).toBe(true);
	});

	it('resolves text, parquet and media content at the catalog revision', async () => {
		const contentCalls: ContentCallLog = {};
		const contentRuntime = runtime(contentCalls);
		const textContent = await contentRuntime.content('hf:README.md');
		expect(textContent.kind).toBe('text');
		expect(textContent.text).toContain('통합 지식 원문');
		expect(textContent.receipt.mode).toBe('byteRange');
		expect(contentCalls.byteOrigin).toBe('hfRevisionRange');
		expect(contentCalls.bytePath).toBe('revision-1/README.md');

		const tableContent = await contentRuntime.content('hf:dart/companyProfile.parquet');
		expect(tableContent.kind).toBe('table');
		expect(tableContent.columns).toEqual(['stockCode', 'corpName', 'listed']);
		expect(tableContent.rows[0]?.corpName).toBe('삼성전자');
		expect(contentCalls.parquetRevision).toBe('revision-1');

		const imageContent = await contentRuntime.content('hf:assets/avatar.png');
		expect(imageContent.kind).toBe('image');
		expect(imageContent.contentRef).toContain('/resolve/revision-1/assets/avatar.png');
		expect(imageContent.receipt.mode).toBe('mediaReference');
	});
});
