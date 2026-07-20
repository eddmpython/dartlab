import type { PageLoad } from './$types';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

// 임베드는 prerender 불필요 · 다양한 code 파라미터 x URL 파라미터
export const prerender = false;
export const ssr = false;

export const load: PageLoad = async ({ params, fetch }) => {
	const { code } = params;

	// ecosystem 에서 해당 노드 lookup
	const [ecosystem, industryStats, meta, detail] = await Promise.all([
		loadJson<any>('map/ecosystem.json', { fetchFn: fetch }),
		loadJson<any>('map/industryStats.json', { fetchFn: fetch }),
		loadJson<any>('map/meta.json', { fetchFn: fetch }),
		loadJson<any>(`map/companies/${code}.json`, { fetchFn: fetch })
	]);
	const node = (ecosystem?.nodes || []).find((n: any) => n.id === code) || null;

	return { code, node, detail, industryStats: industryStats ?? {}, meta };
};
