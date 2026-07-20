import type { PageLoad } from './$types';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export const prerender = true;
export const ssr = false;

export const load: PageLoad = async ({ fetch }) => {
	const ecosystem = await loadJson<any>('map/ecosystem.json', { fetchFn: fetch });
	return { ecosystem: ecosystem ?? { nodes: [], industries: [] } };
};
