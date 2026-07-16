import { describe, expect, it } from 'vitest';
import type { DataCore } from '../fetch/request';
import type { SourceSnapshotSet, UniverseAssertion, UniverseAtlas } from '@dartlab/ui-contracts';
import { compileExactChangeUniverse, loadCurrentChangeUniverse } from './change';

const snapshot: SourceSnapshotSet = {
	schemaVersion: 'sourceSnapshotSet.v1', snapshotSetId: `sha256:${'a'.repeat(64)}`, createdAt: '2026-07-16',
	sources: [], mapBuildId: 'build', capabilityCatalogVersion: null, recipeCatalogVersion: null,
	exactReplayReady: false, unreplayableSourceIds: ['timeline'], missingDataAsOfSourceIds: [], missingRedistributionReceiptSourceIds: []
};

const atlas: UniverseAtlas = {
	version: '1',
	industries: [{ id: 'semiconductor', name: '반도체', revenue: 100, nodeCount: 2, stagedCount: 2, stageMix: {}, stages: [] }],
	flows: []
};

function fakeCore(): DataCore {
	return {
		request: async ({ path }: { path: string }) => path.endsWith('timeline.json')
			? { periods: ['2024', '2025'], data: { '2025': { '005930': { revenue: 90 } } }, industryTotals: { '2025': { semiconductor: { count: 1 } } } }
			: { asOf: '2026-07-16', categories: { revenueSpike: { entries: [{ stockCode: '005930', corpName: '삼성전자', industry: 'semiconductor', revenue: 100, asOfYear: 2026, signal: '매출 신호' }] } } }
	} as unknown as DataCore;
}

function assertion(id: string, availableAt: string): UniverseAssertion {
	return {
		relationId: 'relation:1', assertionId: `assertion:${id.repeat(64)}`, subjectId: '005930', predicate: 'suppliesTo', objectId: 'AAPL',
		direction: 'subjectToObject', status: 'observed', sourceSnapshotSetId: `sha256:${'b'.repeat(64)}`,
		sourcePublishedAt: '2024-01-01', availableAt, validFrom: '2024-01-01', validTo: '', eventAt: '2024-01-01',
		supersedesAssertionId: '', evidenceRefs: [], evidenceBindingHash: `sha256:${id.repeat(64)}`
	};
}

describe('Universe change compiler', () => {
	it('labels mover data as a current demo and emits exact-history gaps', async () => {
		const first = await loadCurrentChangeUniverse(fakeCore(), atlas, snapshot);
		const second = await loadCurrentChangeUniverse(fakeCore(), atlas, snapshot);
		expect(first.mode).toBe('currentDemo');
		expect(first.marks[0]?.kind).toBe('newlyKnown');
		expect(first.marks[0]?.evidence.before.status).toBe('missing');
		expect(first.aggregates[0]).toMatchObject({ coveredCount: 1, unknownCount: 1, changeCount: 1 });
		expect(first.diffHash).toBe(second.diffHash);
	});

	it('excludes assertions beyond knownAt in exact replay', async () => {
		const exactBefore = { ...snapshot, snapshotSetId: `sha256:${'c'.repeat(64)}`, exactReplayReady: true, unreplayableSourceIds: [] };
		const exactAfter = { ...snapshot, snapshotSetId: `sha256:${'d'.repeat(64)}`, exactReplayReady: true, unreplayableSourceIds: [] };
		const result = await compileExactChangeUniverse({
			beforeSnapshot: exactBefore, afterSnapshot: exactAfter, beforeAssertions: [],
			afterAssertions: [assertion('e', '2025-01-01'), assertion('f', '2027-01-01')],
			beforeKnownAt: '2023-12-31', afterKnownAt: '2026-01-01'
		});
		expect(result.mode).toBe('exactReplay');
		expect(result.marks).toHaveLength(1);
		expect(result.marks[0]?.kind).toBe('created');
	});
});
