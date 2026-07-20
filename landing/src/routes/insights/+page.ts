import type { PageLoad } from './$types';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const data = await loadJson<any>('map/insights.json', { fetchFn: fetch, required: true });
	return { data };
};
