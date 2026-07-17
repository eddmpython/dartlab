import type { PageLoad } from './$types';
import { createUniverseBrowser } from '$lib/browser/universeBrowser';
import type { UniverseReleaseState } from '@dartlab/ui-contracts';

export const prerender = true;
export const ssr = true;

function universeReleaseState(): UniverseReleaseState {
	const configured = (import.meta.env as Record<string, string | undefined>).VITE_DARTLAB_UNIVERSE_RELEASE_STATE;
	return configured === 'disabled' ? 'disabled' : 'ga';
}

export const load: PageLoad = async ({ fetch }) => {
	return await createUniverseBrowser({ fetchFn: fetch, universeReleaseState: universeReleaseState() }).seed();
};
