import type { PageLoad } from './$types';

export const prerender = true;
export const ssr = false;

/**
 * Scan Studio · 횡단조회 판떼기.
 *
 * 첫 paint 는 ecosystem.json 만으로 가능하게 단순화. industryStats / quarters /
 * movers 는 후속 PR 이 필요로 할 때 fetch.
 *
 * - ecosystem.json: 회사 노드 41 필드 (scan 20 축 + 정량·등급·변화)
 * - meta.json: dataAsOf 신선도
 *
 * 가격·valuation·공시변경 등 parquet 데이터는 +page.svelte 가 DuckDB-WASM 으로
 * HF parquet 을 직접 query 하여 progressive populate (PR-B 이후 활성).
 */
export const load: PageLoad = async ({ fetch }) => {
	return {
		ecosystem: { nodes: [], industries: [] },
		meta: null,
		markets: {}
	};
};
