import { describe, expect, it } from 'vitest';
import type { EvidencePointer, UniverseEvidenceQuery } from '@dartlab/ui-contracts';
import { resolveUniverseEvidence } from './evidence';

const query: UniverseEvidenceQuery = {
	claimId: 'claim:1', text: '공급 계약', subjectId: '005930', predicate: 'suppliesTo', objectId: 'AAPL',
	direction: 'subjectToObject', validAt: '2025-01-01', knownAt: '2025-03-01'
};

const pointer: EvidencePointer = {
	evidenceId: `evidence:${'1'.repeat(64)}`, documentId: '20250101000001', sectionPath: '사업의 내용/주요 계약', sectionOrder: 3,
	sourceRef: 'https://example.com/filing', sourcePath: 'dart/content/20250101000001', sourceVersion: 'commit:abc',
	subjectId: '005930', predicate: 'suppliesTo', objectId: 'AAPL', direction: 'subjectToObject', sourcePublishedAt: '2025-01-01',
	availableAt: '2025-01-02', contentHash: `sha256:${'2'.repeat(64)}`, locatorKind: 'text',
	textLocator: { charStart: 10, charEnd: 40, snippetHash: `sha256:${'3'.repeat(64)}` }, tableLocator: null
};

describe('Universe evidence resolver', () => {
	it('admits only a complete exact pointer', async () => {
		const result = await resolveUniverseEvidence({ ...query, pointer }, {
			queryFilings: async () => { throw new Error('must not search'); }, indexBuiltAt: async () => null
		});
		expect(result.receipt.status).toBe('supported');
		expect(result.pointer?.evidenceId).toBe(pointer.evidenceId);
		expect(result.gaps).toHaveLength(0);
	});

	it('keeps filing search hits as candidates without fact promotion', async () => {
		const result = await resolveUniverseEvidence(query, {
			queryFilings: async () => [{ rceptNo: '1', corpName: '회사', stockCode: '005930', reportNm: '보고서', rceptDt: '20250101', snippet: '후보', source: 'dart', sourceRef: 'ref', score: 4 }],
			indexBuiltAt: async () => '2025-02-01'
		});
		expect(result.receipt.status).toBe('missing');
		expect(result.pointer).toBeNull();
		expect(result.candidates).toHaveLength(1);
		expect(result.gaps[0]?.reasonCode).toBe('candidateOnly');
	});
});
