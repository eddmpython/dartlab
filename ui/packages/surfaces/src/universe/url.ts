import type { UniverseUrlState } from '@dartlab/ui-contracts';

export const DEFAULT_UNIVERSE_URL_STATE: UniverseUrlState = Object.freeze({
	version: 1,
	snapshotSetId: null,
	buildId: null,
	workflowId: 'atlas',
	beatIndex: 0,
	flightId: null,
	seedIds: [],
	validAt: null,
	knownAt: null,
	predicates: [],
	statuses: [],
	lens: null,
	grouping: 'industry',
	colorBy: null,
	sizeBy: null,
	selectedId: null
});

function optional(params: URLSearchParams, key: string): string | null {
	const value = params.get(key)?.trim();
	return value || null;
}

export function parseUniverseUrl(url: URL): UniverseUrlState {
	const version = Number(url.searchParams.get('uv') ?? 1);
	if (version !== 1) return DEFAULT_UNIVERSE_URL_STATE;
	const grouping = optional(url.searchParams, 'group');
	const validGrouping = grouping === 'stage' || grouping === 'market' || grouping === 'industry' ? grouping : 'industry';
	const beat = Number(url.searchParams.get('beat') ?? 0);
	return {
		version: 1,
		snapshotSetId: optional(url.searchParams, 'snapshot'),
		buildId: optional(url.searchParams, 'build'),
		workflowId: optional(url.searchParams, 'workflow') ?? 'atlas',
		beatIndex: Number.isInteger(beat) && beat >= 0 ? beat : 0,
		flightId: optional(url.searchParams, 'flight'),
		seedIds: [...new Set(url.searchParams.getAll('seed').filter(Boolean))].sort(),
		validAt: optional(url.searchParams, 'validAt'),
		knownAt: optional(url.searchParams, 'knownAt'),
		predicates: [...new Set(url.searchParams.getAll('predicate').filter(Boolean))].sort(),
		statuses: url.searchParams.getAll('status').filter((status): status is UniverseUrlState['statuses'][number] =>
			status === 'observed' || status === 'corroborated' || status === 'disputed' || status === 'retracted'),
		lens: optional(url.searchParams, 'lens'),
		grouping: validGrouping,
		colorBy: optional(url.searchParams, 'color'),
		sizeBy: optional(url.searchParams, 'size'),
		selectedId: optional(url.searchParams, 'selected')
	};
}

export function universeUrl(state: UniverseUrlState, current: URL): URL {
	const next = new URL(current);
	next.search = '';
	next.searchParams.set('uv', '1');
	if (state.snapshotSetId) next.searchParams.set('snapshot', state.snapshotSetId);
	if (state.buildId) next.searchParams.set('build', state.buildId);
	if (state.workflowId !== 'atlas') next.searchParams.set('workflow', state.workflowId);
	if (state.beatIndex > 0) next.searchParams.set('beat', String(state.beatIndex));
	if (state.flightId) next.searchParams.set('flight', state.flightId);
	for (const seed of [...state.seedIds].sort()) next.searchParams.append('seed', seed);
	if (state.validAt) next.searchParams.set('validAt', state.validAt);
	if (state.knownAt) next.searchParams.set('knownAt', state.knownAt);
	for (const predicate of [...state.predicates].sort()) next.searchParams.append('predicate', predicate);
	for (const status of [...state.statuses].sort()) next.searchParams.append('status', status);
	if (state.lens) next.searchParams.set('lens', state.lens);
	if (state.grouping !== 'industry') next.searchParams.set('group', state.grouping);
	if (state.colorBy) next.searchParams.set('color', state.colorBy);
	if (state.sizeBy) next.searchParams.set('size', state.sizeBy);
	if (state.selectedId) next.searchParams.set('selected', state.selectedId);
	return next;
}
