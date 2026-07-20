import type { PageLoad } from './$types';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export const prerender = false;
export const ssr = false;

export const load: PageLoad = async ({ fetch }) => {
	// ecosystem + industryStats + meta 필요 (회사 lookup + 업종 정규화)
	const [ecosystem, industryStats, meta] = await Promise.all([
		loadJson<any>('map/ecosystem.json', { fetchFn: fetch }),
		loadJson<any>('map/industryStats.json', { fetchFn: fetch }),
		loadJson<any>('map/meta.json', { fetchFn: fetch })
	]);
	return {
		ecosystem: ecosystem ?? { nodes: [] },
		industryStats: industryStats ?? {},
		meta
	};
};
