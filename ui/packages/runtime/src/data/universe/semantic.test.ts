import { describe, expect, it } from 'vitest';
import { compileKnowledgeFileSemantics } from './semantic';

const revision = '9906570fca6783f1f79173a0b699ca0c6aeb90a8';

function sourceRef(path: string): string {
	return `https://huggingface.co/datasets/eddmpython/dartlab-data/blob/${revision}/${path}`;
}

describe('Universe semantic compiler', () => {
	it('connects a DART section file to its dataset, security and evidence lanes', () => {
		const path = 'dart/sections/005930/2026Q1.parquet';
		const graph = compileKnowledgeFileSemantics({ path, revision, domainId: 'filings', sourceRef: sourceRef(path) });

		expect(graph.nodes.map((node) => node.nodeId)).toEqual([
			'repository:hf:eddmpython/dartlab-data',
			'dataset:hf:dart/sections',
			'security:dart:005930',
			'section:file:dart/sections/005930/2026Q1.parquet'
		]);
		expect(graph.nodes.find((node) => node.nodeId === 'security:dart:005930')).toMatchObject({
			kind: 'security', lane: 'derived', domainId: 'securities'
		});
		expect(graph.edges).toEqual(expect.arrayContaining([
			expect.objectContaining({
				sourceId: 'repository:hf:eddmpython/dartlab-data',
				targetId: 'dataset:hf:dart/sections',
				relation: 'contains',
				lane: 'fact'
			}),
			expect.objectContaining({
				sourceId: 'security:dart:005930',
				targetId: 'section:file:dart/sections/005930/2026Q1.parquet',
				relation: 'available',
				lane: 'derived',
				ruleId: 'knowledge.pathSubject.v1'
			})
		]));
		expect(graph.edges.every((edge) => edge.evidenceRefs.length > 0)).toBe(true);
	});

	it('uses a SEC CIK identity for EDGAR finance and keeps the observation derived', () => {
		const path = 'edgar/finance/0001045810.parquet';
		const graph = compileKnowledgeFileSemantics({ path, revision, domainId: 'observations', sourceRef: sourceRef(path) });

		expect(graph.nodes).toEqual(expect.arrayContaining([
			expect.objectContaining({ nodeId: 'entity:sec:cik:0001045810', kind: 'entity', lane: 'derived' }),
			expect.objectContaining({ nodeId: `observation:file:${path}`, kind: 'observation', lane: 'derived' })
		]));
		expect(graph.edges).toEqual(expect.arrayContaining([
			expect.objectContaining({
				sourceId: 'entity:sec:cik:0001045810',
				targetId: `observation:file:${path}`,
				relation: 'observed',
				lane: 'derived'
			})
		]));
	});

	it('does not invent an individual issuer for the complete EDGAR registry', () => {
		const path = 'edgar/tickers/tickers.parquet';
		const graph = compileKnowledgeFileSemantics({ path, revision, domainId: 'entities', sourceRef: sourceRef(path) });

		expect(graph.nodes.map((node) => node.nodeId)).toEqual([
			'repository:hf:eddmpython/dartlab-data',
			'dataset:hf:edgar/tickers'
		]);
		expect(graph.edges).toHaveLength(2);
		expect(graph.edges.every((edge) => edge.lane === 'fact')).toBe(true);
	});
});
