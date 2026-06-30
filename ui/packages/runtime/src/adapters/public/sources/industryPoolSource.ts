// 산업 profit-pool 원자료 · map/industries/{id}.json (브라우저 fetch, DuckDB 불필요).
// stages[].nodes[].revenue/opMargin 원자료만 반환 · rollup(매출가중 영업이익률·coverageRatio)은
// 소비 surface(@dartlab/ui-surfaces/map rollupProfitPool) 책임 (계층: runtime ← surface 단방향).
// 로컬 어댑터도 이 loader 를 그대로 재사용 · 정적 자산이라 백엔드 0("깃헙페이지 자산 공유", price·finance 동일).
import type { ProfitPoolStageRaw } from '@dartlab/ui-contracts';
import { loadJson } from '../../../data/dartlabData';

const browser = typeof window !== 'undefined';

interface RawIndustryFile {
	stages?: ProfitPoolStageRaw[];
}

const cache = new Map<string, ProfitPoolStageRaw[] | null>();

export async function loadIndustryProfitPool(industryId: string): Promise<ProfitPoolStageRaw[] | null> {
	if (!browser) return null;
	const id = industryId.trim();
	if (!id) return null;
	if (cache.has(id)) return cache.get(id) ?? null;
	const d = await loadJson<RawIndustryFile>(`map/industries/${id}.json`, { fetchFn: fetch });
	const stages = d?.stages ?? null;
	cache.set(id, stages);
	return stages;
}
