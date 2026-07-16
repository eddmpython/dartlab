import { describe, expect, it } from 'vitest';
import type { UniverseConformanceObservation, UniverseLegalEntityIdentity } from '@dartlab/ui-contracts';
import { compilePairedConformance, UNIVERSE_PAIRED_QUESTIONS } from './conformance';

const kr: UniverseLegalEntityIdentity = { market: 'KR', legalEntityId: '00126380', securityId: '005930', ticker: '005930', validFrom: '1975-06-11', validTo: null, sourceRef: 'dart:corpCode:00126380' };
const us: UniverseLegalEntityIdentity = { market: 'US', legalEntityId: '0000320193', securityId: 'US0378331005', ticker: 'AAPL', validFrom: '1980-12-12', validTo: null, sourceRef: 'sec:cik:0000320193' };

function rows(entity: UniverseLegalEntityIdentity): UniverseConformanceObservation[] {
	return UNIVERSE_PAIRED_QUESTIONS.map((question, index) => ({ entity, metricId: question.metricId, value: index + 1, unit: 'USD', dataAsOf: '2025-12-31', sourceRef: `${entity.sourceRef}#${question.metricId}` }));
}

describe('Universe cross-market conformance', () => {
	it('compiles all fixed 20 questions only with exact identity and source fields', async () => {
		const ready = await compilePairedConformance(rows(kr), rows(us));
		expect(ready).toHaveLength(20);
		expect(ready.every((result) => result.status === 'ready')).toBe(true);
		const blocked = await compilePairedConformance([], []);
		expect(blocked).toHaveLength(20);
		expect(blocked.every((result) => result.status === 'blocked' && result.gaps.length === 2)).toBe(true);
	});
});
