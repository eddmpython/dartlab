import type { PageLoad } from './$types';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export const prerender = true;
export const ssr = false;

export const load: PageLoad = async ({ fetch }) => {
	const [ecosystem, atlas, movers, insights, industryStats, timeline] = await Promise.all([
		loadJson<any>('map/ecosystem.json', { fetchFn: fetch }),
		loadJson<any>('map/atlas.json', { fetchFn: fetch }),
		loadJson<any>('map/movers.json', { fetchFn: fetch }),
		loadJson<any>('map/insights.json', { fetchFn: fetch }),
		loadJson<any>('map/industryStats.json', { fetchFn: fetch }),
		loadJson<any>('map/timeline.json', { fetchFn: fetch })
	]);
	return {
		ecosystem: ecosystem ?? { nodes: [], links: [], industries: [] },
		atlas: atlas ?? { industries: [], flows: [] },
		movers,
		insights,
		industryStats,
		timeline
	};
};
