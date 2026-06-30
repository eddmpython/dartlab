// 타입 정본 = contracts (ProductIndexItem 승격 완료 · 중복 정의 금지).
import type { ProductIndexItem } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const PRODUCT_INDEX_PATH = 'metadata/corpList.parquet';

// loadHfProductIndexMap 은 companySource(local)·createPublicRuntime 가 core 없이 호출하므로(시그니처 불변)
// 모듈 폴백 코어를 lazy 생성한다(financeSource.financeRowsCore 동형). 어댑터가 core 를 주면 그것을 쓴다.
// 옛 productIndexPromise 싱글턴(결과 메모이즈)은 폐기 · 코어가 read 레벨에서 캐시·dedup 한다.
const productCore = moduleFallbackCore();

interface ProductIndexRow extends Record<string, unknown> {
	stockCode?: unknown;
	product?: unknown;
	latestPeriod?: unknown;
	종목코드?: unknown;
	주요제품?: unknown;
	홈페이지?: unknown;
	업종?: unknown;
	대표자명?: unknown;
	결산월?: unknown;
	상장일?: unknown;
	지역?: unknown;
}

export async function loadHfProductIndexMap(core?: DataCore): Promise<Map<string, ProductIndexItem>> {
	const rows = await productCore(core).requestParquetRows<ProductIndexRow>({
		origin: 'hfRange',
		path: PRODUCT_INDEX_PATH,
		columns: ['종목코드', '주요제품', '홈페이지', '업종', '대표자명', '결산월', '상장일', '지역'],
		cacheKey: 'metadata.corpList',
		cache: { scope: 'memory', ttlMs: 60 * 60_000, maxEntries: 2 } // 분기 단위 메타 · 60분 TTL
	});
	const map = new Map<string, ProductIndexItem>();
	const opt = (v: unknown): string | undefined => String(v ?? '').trim() || undefined;
	for (const row of rows) {
		const stockCode = String(row.종목코드 ?? row.stockCode ?? '').trim();
		if (!stockCode) continue;
		const productRaw = cleanProduct(row.주요제품 ?? row.product);
		const product = summarizeProduct(productRaw);
		const homepage = normalizeHomepage(row.홈페이지);
		map.set(stockCode, {
			product,
			productRaw,
			latestPeriod: String(row.latestPeriod ?? '').trim(),
			homepage,
			industry: opt(row.업종),
			ceo: opt(row.대표자명),
			fiscalMonth: opt(row.결산월),
			listedDate: opt(row.상장일),
			region: opt(row.지역)
		});
	}
	return map;
}

function normalizeHomepage(value: unknown): string | undefined {
	const s = String(value ?? '').trim();
	if (!s || s === '-') return undefined;
	if (/^https?:\/\//i.test(s)) return s;
	return 'https://' + s.replace(/^\/+/, '');
}

function cleanProduct(value: unknown): string {
	return String(value ?? '')
		.replace(/&cr;/g, ' ')
		.replace(/\s+/g, ' ')
		.trim();
}

function summarizeProduct(value: string): string {
	return value
		.split(/[,;/·ㆍ]| 및 | 등 |와 |과 | 제조| 판매| 도매| 서비스/g)
		.map((part) =>
			part
				.replace(/\([^)]*\)/g, '')
				.replace(/\s+/g, ' ')
				.trim()
		)
		.filter((part) => part.length >= 2 && !/^(제품|상품|기타|수출입)$/.test(part))
		.filter(unique)
		.slice(0, 4)
		.join(', ');
}

function unique(value: string, index: number, array: string[]): boolean {
	return array.indexOf(value) === index;
}
