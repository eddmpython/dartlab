import { describe, expect, it } from 'vitest';
import { DEFAULT_UNIVERSE_URL_STATE, parseUniverseUrl, universeUrl } from './url';

describe('Universe URL state', () => {
	it('round trips selection and canonical seed ordering', () => {
		const next = universeUrl({
			...DEFAULT_UNIVERSE_URL_STATE,
			snapshotSetId: `sha256:${'a'.repeat(64)}`,
			buildId: 'fixture',
			seedIds: ['z', 'a'],
			selectedId: 'semiconductor'
		}, new URL('https://dartlab.test/universe?ignored=1'));
		const parsed = parseUniverseUrl(next);
		expect(parsed.seedIds).toEqual(['a', 'z']);
		expect(parsed.selectedId).toBe('semiconductor');
		expect(next.searchParams.has('ignored')).toBe(false);
	});

	it('fails closed for an unknown schema version', () => {
		expect(parseUniverseUrl(new URL('https://dartlab.test/universe?uv=9&selected=x'))).toEqual(DEFAULT_UNIVERSE_URL_STATE);
	});
});
