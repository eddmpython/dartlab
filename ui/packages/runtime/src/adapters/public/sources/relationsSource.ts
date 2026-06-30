// 공급망/관계 · map/companies/{code}.json (per-company, 브라우저 fetch, DuckDB 불필요).
// dartlab 고유: 공급사·고객사(제품·매출비중), ego, blogPosts(강점/약점/verdict).
import type { BlogVerdict, CompanyRelations, RelEdge } from '@dartlab/ui-contracts';
import { loadJson } from '../../../data/dartlabData';

const browser = typeof window !== 'undefined';

interface RawCompanyFile {
	suppliers?: RelEdge[];
	customers?: RelEdge[];
	peers?: RelEdge[];
	neighbors?: unknown[];
	blogPosts?: BlogVerdict[];
}

const cache = new Map<string, CompanyRelations | null>();

export async function loadCompanyRelations(stockCode: string): Promise<CompanyRelations | null> {
	if (!browser) return null;
	const code = stockCode.trim();
	if (cache.has(code)) return cache.get(code) ?? null;
	const d = await loadJson<RawCompanyFile>(`map/companies/${code}.json`, { fetchFn: fetch });
	if (!d) {
		cache.set(code, null);
		return null;
	}
	const rel: CompanyRelations = {
		suppliers: (d.suppliers || []).slice(0, 8),
		customers: (d.customers || []).slice(0, 8),
		peers: (d.peers || []).slice(0, 6),
		neighborCount: Array.isArray(d.neighbors) ? d.neighbors.length : 0,
		blog: d.blogPosts && d.blogPosts.length ? (d.blogPosts[0] ?? null) : null
	};
	cache.set(code, rel);
	return rel;
}
