import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

export const prerender = true;

export const load: PageLoad = async ({ params, fetch }) => {
	const { id } = params;
	const [data, industryStats, allMovers, meta] = await Promise.all([
		loadJson<any>(`map/industries/${id}.json`, { fetchFn: fetch }),
		loadJson<any>('map/industryStats.json', { fetchFn: fetch }),
		loadJson<any>('map/movers.json', { fetchFn: fetch }),
		loadJson<any>('map/meta.json', { fetchFn: fetch })
	]);
	if (!data) {
		throw error(404, `산업 데이터 없음: ${id}`);
	}

	// 이 산업 소속 회사의 movers만 필터
	const indMovers: Record<string, any[]> = {};
	if (allMovers?.categories) {
		for (const [catKey, cat] of Object.entries(allMovers.categories) as [string, any][]) {
			indMovers[catKey] = (cat.entries || []).filter((e: any) => e.industry === id);
		}
	}

	return {
		id,
		data,
		stats: industryStats?.[id] || null,
		movers: indMovers,
		moversDisclaimer: allMovers?.disclaimer || '',
		meta
	};
};
