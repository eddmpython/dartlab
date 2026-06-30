import type { PageLoad } from './$types';
import { base } from '$app/paths';

// 임베드는 prerender 불필요 · 다양한 code 파라미터 x URL 파라미터
export const prerender = false;
export const ssr = false;

export const load: PageLoad = async ({ params, fetch }) => {
	const { code } = params;

	// ecosystem 에서 해당 노드 lookup
	const [ecoRes, statsRes, metaRes, detailRes] = await Promise.all([
		fetch(`${base}/map/ecosystem.json`),
		fetch(`${base}/map/industryStats.json`),
		fetch(`${base}/map/meta.json`),
		fetch(`${base}/map/companies/${code}.json`)
	]);
	const ecosystem = ecoRes.ok ? await ecoRes.json() : { nodes: [] };
	const industryStats = statsRes.ok ? await statsRes.json() : {};
	const meta = metaRes.ok ? await metaRes.json() : null;
	const detail = detailRes.ok ? await detailRes.json() : null;

	const node = (ecosystem.nodes || []).find((n: any) => n.id === code) || null;

	return { code, node, detail, industryStats, meta };
};
