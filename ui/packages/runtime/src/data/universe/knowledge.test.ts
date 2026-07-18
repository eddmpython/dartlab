import { describe, expect, it } from 'vitest';
import type { DataCore, RequestSpec } from '../fetch/request';
import { compileKnowledgeContentScene } from './contentProjection';
import { classifyKnowledgePath, createUniverseKnowledgeRuntime } from './knowledge';

const siblings = [
	{ rfilename: 'README.md' },
	{ rfilename: 'dart/companyProfile.parquet' },
	...Array.from({ length: 120 }, (_, index) => ({ rfilename: `dart/finance/${String(index).padStart(6, '0')}.parquet` })),
	{ rfilename: 'dart/panel/005930.parquet' },
	{ rfilename: 'edgar/prices/company/AAPL.parquet' },
	{ rfilename: 'macro/fred/GDP.parquet' },
	{ rfilename: 'news/public/20260717.parquet' },
	{ rfilename: 'catalog/companies.json' },
	{ rfilename: 'catalog/companies.csv' },
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
	skills: graph.nodes.map((node) => ({
		...node,
		whenToUse: [node.purpose],
		apiRefs: [],
		datasetRefs: node.id === 'engines.analysis' ? ['dart.finance', 'dart.docs'] : [],
		knowledgeRefs: [],
		sourceRefs: [`dartlab://skills/${node.id}`]
	}))
};

interface ContentCallLog {
	parquetRevision?: string;
	byteOrigin?: string;
	bytePath?: string;
	metadataPath?: string;
	metadataMethod?: string;
	metadataBody?: string;
}

function fakeCore(contentCalls?: ContentCallLog): DataCore {
	return {
		async request<T>(spec: RequestSpec<T>): Promise<T> {
			if (spec.path.startsWith('tree/main')) {
				return [{ type: 'directory', path: 'dart' }, { type: 'directory', path: 'edgar' }] as T;
			}
			if (spec.path.startsWith('paths-info/')) {
				if (contentCalls) {
					contentCalls.metadataPath = spec.path;
					contentCalls.metadataMethod = spec.init?.method;
					contentCalls.metadataBody = String(spec.init?.body ?? '');
				}
				const path = new URLSearchParams(String(spec.init?.body ?? '')).get('paths') ?? '';
				const payload = [{
					type: 'file', path, oid: 'blob-123', size: path.endsWith('.parquet') ? 1_024 : 81,
					lfs: path.endsWith('.parquet') ? { oid: 'lfs-456', size: 1_024 } : null,
					xetHash: 'xet-789',
					lastCommit: { id: 'commit-abc', title: '데이터 갱신', date: '2026-07-16T03:00:00.000Z' },
					securityFileStatus: { status: 'queued', avScan: { status: 'queued' } }
				}];
				return spec.parse(new Response(JSON.stringify(payload), { status: 200 })) as Promise<T>;
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
			return (spec.path === 'dart/companyProfile.parquet'
				? [{ stockCode: '005930', corpName: '삼성전자', listed: true }]
				: []) as unknown as T[];
		},
		async requestParquetPreview<T extends Record<string, unknown>>(spec: { path: string; revision?: string; rowStart?: number; rowEnd?: number }) {
			if (contentCalls) contentCalls.parquetRevision = spec.revision;
			const allRows = spec.path === 'dart/companyProfile.parquet'
				? Array.from({ length: 30 }, (_, index) => ({ stockCode: String(index).padStart(6, '0'), corpName: index === 0 ? '삼성전자' : `기업 ${index}`, listed: true }))
				: [];
			const rows = allRows.slice(spec.rowStart ?? 0, spec.rowEnd ?? 12);
			const requests = [{ url: 'https://example.test/file.parquet', range: 'bytes=0-99', status: 206, bytes: 100, durationMs: 1 }];
			return {
				metadata: {
					path: spec.path, size: 1_024, rows: allRows.length, rowGroups: 3,
					columns: ['stockCode', 'corpName', 'listed'],
					schema: [
						{ name: 'stockCode', physicalType: 'BYTE_ARRAY', logicalType: 'STRING' },
						{ name: 'corpName', physicalType: 'BYTE_ARRAY', logicalType: 'STRING' },
						{ name: 'listed', physicalType: 'BOOLEAN', logicalType: '' }
					],
					requests
				},
				rows,
				requests
			} as never;
		},
		async requestParquetWholeFile() { return []; },
		async requestBytes(spec: { origin?: string; path: string }) {
			if (contentCalls) {
				contentCalls.byteOrigin = spec.origin;
				contentCalls.bytePath = spec.path;
			}
			const value = spec.path.endsWith('catalog/companies.json')
				? JSON.stringify({ companies: [{ code: '005930', name: '삼성전자' }] })
				: spec.path.endsWith('catalog/wide.csv')
					? `${Array.from({ length: 20 }, (_, index) => `c${index + 1}`).join(',')}\n${Array.from({ length: 20 }, (_, index) => `v${index + 1}`).join(',')}\n`
				: spec.path.endsWith('catalog/companies.csv')
					? 'code,name\n005930,삼성전자\n000660,SK하이닉스\n'
					: '# DartLab\n통합 지식 원문';
			return new TextEncoder().encode(value).buffer as ArrayBuffer;
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
		expect(classifyKnowledgePath('dart/docs/005930.parquet')).toBe('filings');
		expect(classifyKnowledgePath('dart/sections/005930/2026Q1.parquet')).toBe('filings');
		expect(classifyKnowledgePath('edgar/docs/AAPL.parquet')).toBe('filings');
		expect(classifyKnowledgePath('edgar/allFilingsContent/20260717.parquet')).toBe('filings');
		expect(classifyKnowledgePath('metadata/dartList.parquet')).toBe('entities');
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
		expect(search.receipt).toMatchObject({ execution: 'mainThreadFallback', sourceRevision: 'revision-1', workerElapsedMs: null });
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

	it('opens a file as an evidence-laned semantic graph instead of only a folder chain', async () => {
		const scene = await runtime().open('hf:dart/panel/005930.parquet');
		expect(scene.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({ nodeId: 'repository:hf:eddmpython/dartlab-data', kind: 'repository', lane: 'fact' }),
			expect.objectContaining({ nodeId: 'dataset:hf:dart/panel', kind: 'dataset', lane: 'fact' }),
			expect.objectContaining({ nodeId: 'security:dart:005930', kind: 'security', lane: 'derived' }),
			expect.objectContaining({ nodeId: 'document:file:dart/panel/005930.parquet', kind: 'document', lane: 'derived' })
		]));
		expect(scene.edges).toEqual(expect.arrayContaining([
			expect.objectContaining({ sourceId: 'security:dart:005930', relation: 'available', lane: 'derived' }),
			expect.objectContaining({ targetId: 'hf:dart/panel/005930.parquet', relation: 'supported', lane: 'derived' })
		]));
		expect(scene.edges.every((edge) => edge.ruleId && edge.evidenceRefs.length > 0)).toBe(true);
	});

	it('roundtrips twenty representative HF addresses through exact file scenes', async () => {
		const samples = siblings.slice(0, 20).map((entry) => entry.rfilename);
		expect(samples).toHaveLength(20);
		for (const path of samples) {
			const scene = await runtime().open(`hf:${path}`);
			const target = scene.nodes.find((node) => node.nodeId === `hf:${path}`);
			expect(scene.targetId).toBe(`hf:${path}`);
			expect(target?.sourceRef).toContain(`/blob/revision-1/${path}`);
			expect(target?.evidenceRefs).toContain(target?.sourceRef);
		}
	});

	it('preserves Skill OS relation kinds and declared dataset references as facts', async () => {
		const scene = await runtime().open('skill:engines.analysis');
		expect(scene.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({ nodeId: 'datasetref:dart.finance', kind: 'dataset', lane: 'fact' }),
			expect.objectContaining({ nodeId: 'datasetref:dart.docs', kind: 'dataset', lane: 'fact' })
		]));
		expect(scene.edges).toEqual(expect.arrayContaining([
			expect.objectContaining({ targetId: 'skill:engines.analysis.profitability', relation: 'revised', ruleId: 'skillGraph.successor.v1' }),
			expect.objectContaining({ targetId: 'datasetref:dart.finance', relation: 'used', ruleId: 'skillDataset.v1' })
		]));
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
		expect(contentCalls.metadataPath).toBe('paths-info/revision-1');
		expect(contentCalls.metadataMethod).toBe('POST');
		expect(contentCalls.metadataBody).toContain('paths=README.md');
		expect(contentCalls.metadataBody).toContain('expand=true');
		expect(textContent.fileMeta).toMatchObject({
			sizeBytes: 81,
			blobId: 'blob-123',
			xetHash: 'xet-789',
			lastCommitId: 'commit-abc',
			securityStatus: 'queued',
			antivirusStatus: 'queued'
		});
		expect(textContent.fileMeta.historyRef).toBe('https://huggingface.co/datasets/eddmpython/dartlab-data/commits/revision-1/README.md');

		const tableContent = await contentRuntime.content('hf:dart/companyProfile.parquet');
		expect(tableContent.kind).toBe('table');
		expect(tableContent.columns).toEqual(['stockCode', 'corpName', 'listed']);
		expect(tableContent.rows[0]?.corpName).toBe('삼성전자');
		expect(contentCalls.parquetRevision).toBe('revision-1');
		expect(tableContent.tableMeta).toMatchObject({ fileSizeBytes: 1_024, totalRows: 30, rowGroupCount: 3, rangeRequestCount: 1, rowStart: 0, rowEnd: 12 });
		expect(tableContent.schema[2]).toMatchObject({ name: 'listed', physicalType: 'BOOLEAN' });
		expect(tableContent.fileMeta).toMatchObject({ sizeBytes: 1_024, lfsOid: 'lfs-456', lfsSizeBytes: 1_024 });

		const nextTableContent = await contentRuntime.content('hf:dart/companyProfile.parquet', 12);
		expect(nextTableContent.tableMeta).toMatchObject({ rowStart: 12, rowEnd: 24, totalRows: 30 });
		expect(nextTableContent.rows[0]?.corpName).toBe('기업 12');

		const imageContent = await contentRuntime.content('hf:assets/avatar.png');
		expect(imageContent.kind).toBe('image');
		expect(imageContent.contentRef).toContain('/resolve/revision-1/assets/avatar.png');
		expect(imageContent.receipt.mode).toBe('mediaReference');

		const jsonContent = await contentRuntime.content('hf:catalog/companies.json');
		expect(jsonContent.receipt.mode).toBe('jsonTree');
		expect(jsonContent.tree.some((node) => node.key === 'name' && node.value === '삼성전자')).toBe(true);

		const csvContent = await contentRuntime.content('hf:catalog/companies.csv');
		expect(csvContent.receipt.mode).toBe('delimitedRows');
		expect(csvContent.columns).toEqual(['code', 'name']);
		expect(csvContent.rows[1]?.name).toBe('SK하이닉스');

		const wideContent = await contentRuntime.content('hf:catalog/wide.csv', 0, 16);
		expect(wideContent.columns).toEqual(['c17', 'c18', 'c19', 'c20']);
		expect(wideContent.rows[0]?.c20).toBe('v20');
		expect(wideContent.tableMeta).toMatchObject({ totalColumns: 20, columnStart: 16, columnEnd: 20 });
	});

	it('projects exact rows, fields, JSON pointers, line spans and revision history into bounded scenes', async () => {
		const contentRuntime = runtime();
		const tableScene = await contentRuntime.open('hf:dart/companyProfile.parquet');
		const tableContent = await contentRuntime.content('hf:dart/companyProfile.parquet');
		const tableProjection = compileKnowledgeContentScene(tableScene, tableContent, tableScene.targetId);
		const secondRow = tableProjection.nodes.find((node) => node.kind === 'record' && node.attributes.rowIndex === 1);
		expect(tableProjection.nodes.length).toBeLessThanOrEqual(80);
		expect(tableProjection.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({ kind: 'revision', sourceRef: tableContent.fileMeta.historyRef }),
			expect.objectContaining({ kind: 'record', sourceRef: expect.stringContaining('#row=1') })
		]));
		expect(tableProjection.nodes.some((node) => node.kind === 'field')).toBe(false);
		expect(tableProjection.receipt.outputNodeCount).toBe(tableProjection.nodes.length);
		expect(tableProjection.receipt.outputEdgeCount).toBe(tableProjection.edges.length);
		expect(tableProjection.receipt.omittedNodeCount).toBeGreaterThan(0);
		expect(secondRow).toBeTruthy();

		const focusedProjection = compileKnowledgeContentScene(tableScene, tableContent, secondRow?.nodeId ?? null);
		expect(focusedProjection.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({ kind: 'field', sourceRef: expect.stringContaining('#row=2&column=corpName') })
		]));
		const focusedFields = focusedProjection.nodes.filter((node) => node.kind === 'field');
		expect(focusedFields).toHaveLength(tableContent.columns.length);
		for (let left = 0; left < focusedFields.length; left += 1) {
			for (let right = left + 1; right < focusedFields.length; right += 1) {
				const deltaX = Math.abs((focusedFields[left]?.x ?? 0) - (focusedFields[right]?.x ?? 0));
				const deltaY = Math.abs((focusedFields[left]?.y ?? 0) - (focusedFields[right]?.y ?? 0));
				expect(Math.max(deltaX, deltaY)).toBeGreaterThanOrEqual(0.35);
			}
		}

		const jsonScene = await contentRuntime.open('hf:catalog/companies.json');
		const jsonContent = await contentRuntime.content('hf:catalog/companies.json');
		const jsonProjection = compileKnowledgeContentScene(jsonScene, jsonContent);
		expect(jsonProjection.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({
				kind: 'field',
				attributes: expect.objectContaining({ pointer: '/companies/0/name' }),
				sourceRef: expect.stringContaining('json-pointer=%2Fcompanies%2F0%2Fname')
			})
		]));

		const textScene = await contentRuntime.open('hf:README.md');
		const textContent = await contentRuntime.content('hf:README.md');
		const textProjection = compileKnowledgeContentScene(textScene, textContent);
		expect(textProjection.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({ kind: 'section', sourceRef: expect.stringContaining('#L1-L1') })
		]));
		expect(textProjection.film).toEqual(compileKnowledgeContentScene(textScene, textContent).film);
	});
});
