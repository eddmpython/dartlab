import type { PageLoad } from './$types';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const [movers, meta] = await Promise.all([
		loadJson<any>('map/movers.json', { fetchFn: fetch }),
		loadJson<any>('map/meta.json', { fetchFn: fetch })
	]);
	return { movers: movers ?? { categories: {}, disclaimer: '' }, meta };
};
