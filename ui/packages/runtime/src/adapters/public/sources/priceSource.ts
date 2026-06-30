// 일별 OHLCV 시계열 · gov/prices/date/{year}.parquet 을 hyparquet HTTP-range 로 직독.
// hyparquet 는 컬럼 projection (7 컬럼) + ISU_CD 필터 pushdown + 병렬 range → 첫 페인트 비차단·sub-second.
// 전체 이력(2010~현재) lazy 로딩: 초기 = 현재+직전 연도, 이후 차트 좌측 팬 시 연도 단위 추가 로드.
// 표시용 변환(수정주가·집계·하이킨아시)은 surface 의 candleMath · 본 모듈은 로드·캐시만.
import { KRX_MIN_YEAR, type Candle, type CompanyPrices } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const browser = typeof window !== 'undefined';

// 연도 parquet read 는 fetch 코어(데이터 워크벤치 SSOT)가 캐시·dedup · hfRange 직접 read 금지(가드 rule 6).
// publicPricePort 는 ui/web 레거시 무인자 경로도 있어 core 미주입 시 모듈 폴백(govPriceSource.govCore 동형, lazy).
const priceCore = moduleFallbackCore();

const OHLCV_COLUMNS = ['ISU_CD', 'BAS_DD', 'TDD_OPNPRC', 'TDD_HGPRC', 'TDD_LWPRC', 'TDD_CLSPRC', 'ACC_TRDVOL', 'FLUC_RT', 'ACC_TRDVAL'];

const cache = new Map<string, CompanyPrices | null>();
// 동시 보관 회사 수 상한 · 많은 회사 탐색 시 캔들 누수 방지(MAX 이력 = 회사당 수 MB). 초과 시 가장 오래된 항목 제거.
const CACHE_CAP = 16;
function setCache(code: string, rec: CompanyPrices | null): void {
	cache.set(code, rec);
	if (cache.size > CACHE_CAP) {
		const oldest = cache.keys().next().value;
		if (oldest !== undefined && oldest !== code) cache.delete(oldest);
	}
}

interface KrxRow extends Record<string, unknown> {
	ISU_CD?: string | null;
	BAS_DD?: string | number | null;
	TDD_OPNPRC?: string | number | null;
	TDD_HGPRC?: string | number | null;
	TDD_LWPRC?: string | number | null;
	TDD_CLSPRC?: string | number | null;
	ACC_TRDVOL?: string | number | null;
	FLUC_RT?: string | number | null;
	ACC_TRDVAL?: string | number | null;
}

function num(v: unknown): number | null {
	if (typeof v === 'number') return Number.isFinite(v) ? v : null;
	if (typeof v === 'bigint') {
		const n = Number(v);
		return Number.isFinite(n) ? n : null;
	}
	if (typeof v === 'string' && v.trim()) {
		const n = Number(v.replace(/,/g, ''));
		return Number.isFinite(n) ? n : null;
	}
	return null;
}

function toCandle(r: KrxRow): Candle | null {
	const c = num(r.TDD_CLSPRC);
	if (c == null || c <= 0) return null;
	const t = r.BAS_DD == null ? '' : String(r.BAS_DD);
	if (!t) return null;
	return { t, o: num(r.TDD_OPNPRC) ?? c, h: num(r.TDD_HGPRC) ?? c, l: num(r.TDD_LWPRC) ?? c, c, v: num(r.ACC_TRDVOL) ?? 0, r: num(r.FLUC_RT), tv: num(r.ACC_TRDVAL) };
}

// ISU_CD 는 KRX 주식 = 'A' + 6 자리 (예: A005930). 드물게 prefix 없는 경우 대비 $in.
async function readYearCandles(year: number, isuA: string, isuPlain: string, core?: DataCore): Promise<Candle[]> {
	try {
		const rows = await priceCore(core).requestParquetRows<KrxRow>({
			origin: 'hfRange',
			path: `gov/prices/date/${year}.parquet`,
			columns: OHLCV_COLUMNS,
			filter: { ISU_CD: { $in: [isuA, isuPlain] } },
			cacheKey: `gov.prices.year:${year}:${isuPlain}`,
			cache: { scope: 'memory', ttlMs: 60 * 60_000, maxEntries: 64 }
		});
		return rows.map(toCandle).filter((x): x is Candle => x != null);
	} catch {
		return [];
	}
}

/** 오름차순 병합 + 일자 dedup (연도 경계 안전). 어댑터 조립(회사파일+recent tail 병합)에서도 사용. */
export function mergeDedup(...lists: Candle[][]): Candle[] {
	const merged = ([] as Candle[]).concat(...lists);
	merged.sort((a, b) => a.t.localeCompare(b.t));
	const out: Candle[] = [];
	let lastT = '';
	for (const k of merged) {
		if (k.t === lastT) continue;
		out.push(k);
		lastT = k.t;
	}
	return out;
}

/** 초기 로드 · 현재+직전 연도 (빠른 첫 페인트). null = 데이터 없음/실패. 동시 호출의 무거운 연도
 *  스캔 dedup 은 fetch 코어(연도 parquet read 키 공유)가 담당 · 자체 in-flight Map 폐기. */
export function loadInitialOHLCV(stockCode: string, year: number, core?: DataCore): Promise<CompanyPrices | null> {
	if (!browser) return Promise.resolve(null);
	const code = stockCode.trim();
	if (cache.has(code)) return Promise.resolve(cache.get(code) ?? null);
	return (async () => {
		const c = code.replace(/[^0-9A-Za-z]/g, '');
		const isuA = `A${c}`;
		const [curr, prev] = await Promise.all([readYearCandles(year, isuA, c, core), readYearCandles(year - 1, isuA, c, core)]);
		const candles = mergeDedup(prev, curr);
		if (candles.length === 0) {
			setCache(code, null);
			return null;
		}
		const rec: CompanyPrices = { candles, oldestYear: year - 1 };
		setCache(code, rec);
		return rec;
	})();
}

/** 현재까지 캐시된 전체 캔들(오름차순). 백필 후 차트 재적용·기간 윈도잉에 사용. */
export function loadedCandles(stockCode: string): Candle[] {
	return cache.get(stockCode.trim())?.candles ?? [];
}

/** 외부 소스(gov 회사별 parquet 전체이력)를 차트 캐시에 심는다 · loadedCandles/loadOlderYear 일관 보장. */
export function seedCandles(stockCode: string, candles: Candle[]): CompanyPrices | null {
	const first = candles[0];
	if (!first) return null;
	const rec: CompanyPrices = { candles, oldestYear: +first.t.slice(0, 4) };
	setCache(stockCode.trim(), rec);
	return rec;
}

/** 좌측 팬 시 더 오래된 연도 1 개 로드 (prepend 용). 캐시에도 병합. 빈 배열 = 데이터 없음. */
export async function loadOlderYear(stockCode: string, targetYear: number, core?: DataCore): Promise<Candle[]> {
	if (!browser || targetYear < KRX_MIN_YEAR) return [];
	const code = stockCode.trim();
	const c = code.replace(/[^0-9A-Za-z]/g, '');
	const rows = await readYearCandles(targetYear, `A${c}`, c, core);
	const rec = cache.get(code);
	if (rec) {
		rec.candles = mergeDedup(rows, rec.candles);
		rec.oldestYear = Math.min(rec.oldestYear, targetYear);
	}
	return rows;
}
