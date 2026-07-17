import { describe, expect, it } from 'vitest';
import type { KnowledgeSearchIndex } from './knowledgeSearch';
import { searchKnowledgeIndex } from './knowledgeSearch';

const index: KnowledgeSearchIndex = {
	revision: 'revision-1',
	filePaths: [
		'dart/panel/005930.parquet',
		'dart/finance/005930.parquet',
		'edgar/tickers/tickers.parquet',
		'edgar/docs/NVDA.parquet',
		'news/public/20260717.parquet'
	],
	skills: [{
		id: 'engines.analysis',
		title: 'Analysis',
		category: 'engines',
		purpose: '재무 분석 엔진',
		whenToUse: ['profitability 분석'],
		datasetRefs: ['dart.finance'],
		sourceRefs: ['dartlab://skills/engines.analysis']
	}]
};

describe('Universe knowledge search index', () => {
	it('produces the same exact file and Skill OS hits in an isolated pure search', () => {
		const fileHits = searchKnowledgeIndex(index, { query: 'edgar/tickers/tickers.parquet' });
		expect(fileHits[0]).toMatchObject({ targetId: 'hf:edgar/tickers/tickers.parquet', domainId: 'entities', score: 120 });

		const skillHits = searchKnowledgeIndex(index, { query: 'profitability' });
		expect(skillHits[0]).toMatchObject({ targetId: 'skill:engines.analysis', kind: 'capability' });
	});

	it('applies domain and scene limits before returning structured clone safe hits', () => {
		const hits = searchKnowledgeIndex(index, { query: '005930', domainId: 'filings', limit: 12 });
		expect(hits).toHaveLength(1);
		expect(hits[0]).toMatchObject({ targetId: 'hf:dart/panel/005930.parquet', domainId: 'filings' });
		expect(() => structuredClone(hits)).not.toThrow();
	});
});
