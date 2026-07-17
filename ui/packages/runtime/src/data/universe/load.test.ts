import { describe, expect, it, vi } from 'vitest';
import { createDataCore } from '../fetch/request';
import { loadObservationSeries, loadUniverseRouteSeed } from './load';

const meta = {
	schemaVersion: 1,
	buildId: 'fixture-build',
	buildTime: '2026-07-15T00:00:00Z',
	commitSha: 'abc1234',
	dataAsOf: { dart: null, finance: '2026-07-15T00:00:00Z', reviews: null, taxonomy: null },
	sizes: {},
	counts: {}
};
const atlas = {
	version: 'fixture',
	industries: [
		{ id: 'upstream', name: '상류', revenue: 0, nodeCount: 1, stagedCount: 1, stageMix: {}, stages: [{ key: 'a', name: 'A', role: '제조', stream: 'upstream' }] },
		{ id: 'downstream', name: '하류', revenue: 10, nodeCount: 1, stagedCount: 1, stageMix: {}, stages: [{ key: 'b', name: 'B', role: '서비스', stream: 'downstream' }] }
	],
	flows: [{ fromIndustry: 'upstream', toIndustry: 'downstream', edgeCount: 1, amount: 5 }]
};
const company = {
	ego: { stockCode: '005930', corpName: '삼성전자' },
	financials5y: [
		{ year: '2024', sales: 0 },
		{ year: '2025', sales: 12 }
	]
};

function response(value: unknown): Response {
	return new Response(JSON.stringify(value), {
		status: 200,
		headers: { 'content-type': 'application/json', etag: 'f'.repeat(64), 'x-repo-commit': 'fixture-commit' }
	});
}

describe('Universe loaders', () => {
	it('loads only meta and atlas for the route seed', async () => {
		const fetchFn = vi.fn(async (input: RequestInfo | URL) => {
			const url = String(input);
			if (url.endsWith('/landing/map/meta.json')) return response(meta);
			if (url.endsWith('/landing/map/atlas.json')) return response(atlas);
			throw new Error(`unexpected request: ${url}`);
		});
		const seed = await loadUniverseRouteSeed(createDataCore({ fetchFn: fetchFn as typeof fetch }));
		expect(fetchFn).toHaveBeenCalledTimes(2);
		expect(fetchFn.mock.calls.every(([input]) => !String(input).includes('ecosystem'))).toBe(true);
		expect(seed.scene.nodes).toHaveLength(2);
		expect(seed.scene.edges).toHaveLength(1);
		expect(seed.snapshot.exactReplayReady).toBe(false);
		expect(seed.releaseState).toBe('ga');
		expect(seed.product.routeReady).toBe(true);
		expect(seed.product.capabilities.find((item) => item.capabilityId === 'atlas')?.status).toBe('ready');
		expect(seed.product.capabilities.find((item) => item.capabilityId === 'factRelations')?.status).toBe('guarded');
	});

	it('loads observations lazily, preserves zero, and deduplicates an in-flight company request', async () => {
		const fetchFn = vi.fn(async () => response(company));
		const core = createDataCore({ fetchFn: fetchFn as typeof fetch });
		const [first, second] = await Promise.all([
			loadObservationSeries(core, '005930', 'sales'),
			loadObservationSeries(core, '005930', 'sales')
		]);
		expect(fetchFn).toHaveBeenCalledTimes(1);
		expect(first.map((point) => point.value)).toEqual([0, 12]);
		expect(second).toEqual(first);
	});

	it('opens the disabled incident surface without touching a source', async () => {
		const fetchFn = vi.fn(async () => { throw new Error('source must stay untouched'); });
		const seed = await loadUniverseRouteSeed(createDataCore({ fetchFn: fetchFn as typeof fetch }), 'disabled');
		expect(fetchFn).not.toHaveBeenCalled();
		expect(seed.releaseState).toBe('disabled');
		expect(seed.product.routeReady).toBe(false);
	});
});
