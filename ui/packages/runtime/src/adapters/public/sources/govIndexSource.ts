// KR gov 지수 = gov/indices (공공누리/KOGL, 출처표시 의무 GOV_ATTRIBUTION). KRX-raw 지수 schema 직독.
// 읽기 전략(데이터 실측 기반):
//   1순위 · gov/indices/index/{key}.parquet : 지수 1개 전체 이력(작음). 빠르나 *온디맨드 생성*이라 미존재 가능.
//   폴백  · gov/indices/date/{year}.parquet : 전지수 횡단(연 1.1MB). 최근 N년만 읽어 IDX_NM 필터 → 최근 구간.
// date/ 전이력(17년×1.1MB=18MB)은 브라우저 비현실적이라, 폴백은 최근 N년으로 *bounded*. 전이력은 per-index seed 후.
// key = `{MARKET_GROUP}-{IDX_NM 안전화}` · buildGovData.indexKey 와 1:1 (예약문자/공백 '_' 치환·한글 유지).
import type { Candle, IndexRef } from '@dartlab/ui-contracts';
import { KR_INDEX_PRESETS } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';
import { mergeDedup } from './priceSource';

const browser = typeof window !== 'undefined';

// KRX-raw 지수 컬럼 (gather/gov/govApi.py normalizeGovIndexFrame 정본 · date/ 와 index/ 동일 schema).
const IDX_COLUMNS = ['BAS_DD', 'MARKET_GROUP', 'IDX_NM', 'OPNPRC_IDX', 'HGPRC_IDX', 'LWPRC_IDX', 'CLSPRC_IDX', 'ACC_TRDVOL', 'FLUC_RT', 'ACC_TRDVAL'];
interface IdxRow extends Record<string, unknown> {
	BAS_DD?: string | null;
	MARKET_GROUP?: string | null;
	IDX_NM?: string | null;
	OPNPRC_IDX?: number | null;
	HGPRC_IDX?: number | null;
	LWPRC_IDX?: number | null;
	CLSPRC_IDX?: number | null;
	ACC_TRDVOL?: number | null;
	FLUC_RT?: number | null;
	ACC_TRDVAL?: number | null;
}

// 폴백 최근 윈도우 · date/{currentYear}+{-1} 2 파일(≤2.2MB)로 최근 ~2년. 전이력은 per-index seed 후.
const FALLBACK_YEARS = 2;
const GOV_MIN_YEAR = 2010;
// _RESERVED = '/\:*?"<>|' (buildGovData.py 와 동일 9 예약문자) + 공백 → '_'.
const RESERVED = /[/\\:*?"<>|]/g;

/** (market, idxNm) → 파일시스템 안전 키. buildGovData.indexKey 와 1:1. */
function indexKey(market: string, idxNm: string): string {
	let s = idxNm.normalize('NFC').trim().replace(RESERVED, '_').replace(/\s+/g, '_').replace(/_+/g, '_');
	s = s.replace(/^_+|_+$/g, '');
	return `${market}-${s}`;
}

function rowToCandle(r: IdxRow): Candle | null {
	const c = Number(r.CLSPRC_IDX);
	const t = r.BAS_DD == null ? '' : String(r.BAS_DD);
	if (!t || !Number.isFinite(c) || c <= 0) return null;
	const fr = Number(r.FLUC_RT);
	const tv = Number(r.ACC_TRDVAL);
	return {
		t,
		o: Number(r.OPNPRC_IDX) || c,
		h: Number(r.HGPRC_IDX) || c,
		l: Number(r.LWPRC_IDX) || c,
		c,
		v: Number(r.ACC_TRDVOL) || 0,
		r: Number.isFinite(fr) ? fr : null,
		tv: Number.isFinite(tv) ? tv : null
	};
}

// createPublicIndexPort 는 ui/web 레거시·로컬 어댑터 양쪽이 core 없이 호출하므로 모듈 폴백 코어를 lazy
// 생성한다(financeSource.financeRowsCore 동형). 어댑터는 자신의 createDataCore() 를 주입한다.
// 옛 cache·inflight·nameScanCache Map(결과/in-flight/universe 수기 관리)은 폐기 · 코어가 read 레벨에서
// 캐시(per-parquet path)·dedup. universe 재빌드는 코어 캐시된 year 파일을 재그룹화(read 비용 0).
const idxCore = moduleFallbackCore();

// per-index/date year 파일 통파일 직독 · 코어 read 캐시·dedup 공유. 지수 신선도 = 일 단위라 30분 TTL.
function readIdxFile(core: DataCore, path: string, columns: string[], key: string): Promise<IdxRow[] | null> {
	return core.requestParquetWholeFile<IdxRow>({
		origin: 'hf',
		path,
		columns,
		cacheKey: key,
		cache: { scope: 'memory', ttlMs: 30 * 60_000, maxEntries: 64 }
	});
}

function currentYear(): number {
	// 실 어댑터(픽스처 아님)라 현재시각 허용 · 폴백이 읽을 최신 date/ 연도 판정용.
	return new Date().getUTCFullYear();
}

/** 최근 count 년(내림차순, GOV_MIN_YEAR 바닥). 폴백·검색 윈도우 공통(DRY). */
function recentYears(count: number): number[] {
	const yr = currentYear();
	const out: number[] = [];
	for (let y = yr; y > yr - count && y >= GOV_MIN_YEAR; y--) out.push(y);
	return out;
}

/** per-index 캐시 1순위 · gov/indices/index/{key}.parquet (작음·전이력). null=미존재. */
async function readPerIndex(core: DataCore, key: string): Promise<Candle[] | null> {
	try {
		const rows = await readIdxFile(core, `gov/indices/index/${key}.parquet`, IDX_COLUMNS, `gov.indices.index:${key}`);
		if (!rows) return null;
		const candles = rows.map(rowToCandle).filter((x): x is Candle => x != null);
		return candles.length ? candles : null;
	} catch {
		return null;
	}
}

/** date/ 최근 N년 폴백 · 연도 파일에서 MARKET_GROUP+IDX_NM 필터 → 최근 구간(bounded). */
async function readDateFallback(core: DataCore, market: string, idxNm: string): Promise<Candle[] | null> {
	const out: Candle[] = [];
	for (const y of recentYears(FALLBACK_YEARS)) {
		let rows: IdxRow[] | null = null;
		try {
			rows = await readIdxFile(core, `gov/indices/date/${y}.parquet`, IDX_COLUMNS, `gov.indices.date:${y}`);
		} catch {
			rows = null;
		}
		if (!rows) continue;
		for (const r of rows) {
			if (String(r.MARKET_GROUP) !== market || String(r.IDX_NM) !== idxNm) continue;
			const c = rowToCandle(r);
			if (c) out.push(c);
		}
	}
	if (!out.length) return null;
	out.sort((a, b) => a.t.localeCompare(b.t));
	return out;
}

/**
 * KR gov 지수 캔들(오름차순). govPriceSource 동형 병합 패턴:
 *   per-index/{key}(전이력, 가끔 seed) ∪ date/ 최근 N년(daily-fresh tail) → mergeDedup.
 * v1(per-index 미seed): date/ 최근 N년만 → live. seed 후: 전이력 + 최신 거래일까지 fresh.
 * date/ 최근이 per-index seed 이후 갭을 메워 stale tail 0. null=둘 다 미존재. 동시호출 dedup.
 */
export function loadGovIndexCandles(ref: IndexRef, core?: DataCore): Promise<Candle[] | null> {
	if (!browser) return Promise.resolve(null);
	const dc = idxCore(core);
	const key = indexKey(ref.market, ref.name);
	return (async () => {
		const [perIdx, recent] = await Promise.all([readPerIndex(dc, key), readDateFallback(dc, ref.market, ref.name)]);
		const merged = mergeDedup(perIdx ?? [], recent ?? []); // 겹치는 날 per-index 우선(동일 출처라 값 동일)
		return merged.length ? merged : null;
	})();
}

/** gov 지수 전체 universe · 최신 date/ 파일의 distinct (MARKET_GROUP, IDX_NM). 회사 무관·세션 1회 캐시.
 *  카탈로그 select(전체 브라우징)·검색이 공유. 빈 결과는 캐시 안 함(일시 404 poisoning 방지). */
export async function loadGovIndexUniverse(core?: DataCore): Promise<IndexRef[]> {
	if (!browser) return [];
	const dc = idxCore(core);
	const universe: IndexRef[] = [];
	for (const y of recentYears(2)) {
		let rows: IdxRow[] | null = null;
		try {
			// universe 는 2컬럼만 projection · date/ 캔들 읽기(IDX_COLUMNS)와 컬럼셋이 달라 cacheKey 를 분리한다
			// (코어는 cacheKey 로 캐시하므로 같은 키면 선행 호출의 컬럼셋이 고정돼 컬럼 누락 버그가 난다).
			rows = await readIdxFile(dc, `gov/indices/date/${y}.parquet`, ['MARKET_GROUP', 'IDX_NM'], `gov.indices.date.names:${y}`);
		} catch {
			rows = null;
		}
		if (!rows) continue;
		const seen = new Set<string>();
		for (const r of rows) {
			const m = String(r.MARKET_GROUP ?? '');
			const nm = String(r.IDX_NM ?? '');
			if (!m || !nm) continue;
			const k = `${m}/${nm}`;
			if (seen.has(k)) continue;
			seen.add(k);
			universe.push({ market: m as IndexRef['market'], name: nm, code: `idx:${m}/${nm}`, ohlc: 'candle' });
		}
		if (universe.length) break; // 최신 연도에서 채웠으면 끝
	}
	return universe; // 빈 결과 비캐시 가드는 코어 read 레벨에 위임 · 실제 404 year 파일만 null 캐시(transient 403/429 는 fetchResilient 재시도)
}

/** gov 지수 이름 부분일치 검색 · universe 스캔(큐레이트 우선). */
export async function scanGovIndexNames(query: string, limit = 12, core?: DataCore): Promise<IndexRef[]> {
	if (!browser) return [];
	const q = query.trim();
	if (!q) return [];
	const universe = await loadGovIndexUniverse(core);
	// 큐레이트 우선 노출(부분일치) → 나머지.
	const matches = universe.filter((r) => r.name.includes(q));
	const curatedFirst = [
		...matches.filter((r) => KR_INDEX_PRESETS.some((p) => p.name === r.name && p.market === r.market)),
		...matches.filter((r) => !KR_INDEX_PRESETS.some((p) => p.name === r.name && p.market === r.market))
	];
	return curatedFirst.slice(0, limit);
}
