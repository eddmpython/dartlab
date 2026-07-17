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

function fakeCore(): DataCore {
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
		async requestParquetRows() { return []; },
		async requestParquetWholeFile() { return []; },
		async requestBytes() { return new ArrayBuffer(0); },
		clear() {}
	};
}

function runtime() {
	return createUniverseKnowledgeRuntime(fakeCore(), {
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
});
