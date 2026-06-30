// US(EDGAR 유니버스) 일별 OHLCV · edgar/prices/company/{ticker}.parquet 통파일 직독.
// KR govPriceSource 와 동형: 회사별 전체 OHLCV(Yahoo v8 ~10년 bake)를 read-only 로 읽는다.
//
// 원천 = gather US history(yahooChart.fetchHistory, Yahoo v8 period1/period2·interval=1d·adjclose)를
// 오프라인 bake 한 산출(edgar/prices/company). 런타임 라이브 호출 0 · Yahoo 는 429(per-IP)·CORS 라
// 브라우저 직호출 불가(KR 이 gov 에 굽는 이유와 동일). close 는 수정주가(adjclose)라 KR 의 등락률 체이닝
// 불필요 → r/tv = null. 표시 변환(집계·하이킨아시)은 surface 의 candleMath, 본 모듈은 로드·정규화만.
import type { Candle } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const browser = typeof window !== 'undefined';

// publicPricePort 는 어댑터가 createDataCore() 를 주입하지만, core 미주입 경로(레거시)도 안전하게 폴백한다
// (govPriceSource.govCore 동형, lazy 생성). 결과 캐시·in-flight dedup 은 코어가 read 레벨에서 담당.
const edgarCore = moduleFallbackCore();

// bake schema = KR gov company 와 동형(date/o/h/l/c/v). close = 수정주가(Yahoo adjclose).
const EDGAR_PRICE_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume'];

interface EdgarPriceRow extends Record<string, unknown> {
	date?: string | number | null;
	open?: number | null;
	high?: number | null;
	low?: number | null;
	close?: number | null;
	volume?: number | null;
}

// date → Candle.t 규약(YYYYMMDD). bake 가 'YYYY-MM-DD'(gather 출력) 든 'YYYYMMDD' 든 대시 제거로 흡수.
function toYmd(v: string | number | null | undefined): string {
	if (v == null) return '';
	return String(v).replace(/-/g, '').slice(0, 8);
}

function rowToCandle(r: EdgarPriceRow): Candle | null {
	const c = Number(r.close);
	const t = toYmd(r.date);
	if (!/^\d{8}$/.test(t) || !Number.isFinite(c) || c <= 0) return null;
	return { t, o: Number(r.open) || c, h: Number(r.high) || c, l: Number(r.low) || c, c, v: Number(r.volume) || 0, r: null, tv: null };
}

/** parquet 행 묶음 → 정규화 캔들(오름차순·일자 dedup). 순수 함수 · 단위 테스트 진입점(네트워크 무관). */
export function parseEdgarPriceRows(rows: EdgarPriceRow[]): Candle[] {
	const out: Candle[] = [];
	for (const r of rows) {
		const k = rowToCandle(r);
		if (k) out.push(k);
	}
	out.sort((a, b) => a.t.localeCompare(b.t));
	const dedup: Candle[] = [];
	let lastT = '';
	for (const k of out) {
		if (k.t === lastT) continue;
		dedup.push(k);
		lastT = k.t;
	}
	return dedup;
}

// 최근 거래일 tail · 일증분(Polygon by-day)이 매일 갱신하는 edgar/prices/recent.parquet(전 종목 1파일).
// 회사 base(company/{ticker})와 머지해 마지막 봉까지 신선. KR gov/prices/recent 와 동형(ticker 컬럼 추가).
const EDGAR_RECENT_COLUMNS = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume'];
interface EdgarRecentRow extends EdgarPriceRow {
	ticker?: string | null;
}

/** recent parquet 행 묶음 → {ticker: 캔들 오름차순}. 순수 함수 · 단위 테스트 진입점(네트워크 무관). */
export function parseEdgarRecent(rows: EdgarRecentRow[]): Record<string, Candle[]> {
	const map: Record<string, Candle[]> = {};
	for (const r of rows) {
		const tk = r.ticker == null ? '' : String(r.ticker).trim().toUpperCase();
		const k = rowToCandle(r);
		if (!tk || !k) continue;
		(map[tk] ??= []).push(k);
	}
	for (const arr of Object.values(map)) arr.sort((a, b) => a.t.localeCompare(b.t));
	return map;
}

/** 전 종목 최근 tail (ticker → 캔들 오름차순, JSON-safe Record). null = 미발행. 코어가 read 캐시·dedup. */
export function loadEdgarRecent(core?: DataCore): Promise<Record<string, Candle[]> | null> {
	if (!browser) return Promise.resolve(null);
	const dc = edgarCore(core);
	return (async () => {
		try {
			const rows = await dc.requestParquetWholeFile<EdgarRecentRow>({
				origin: 'hf',
				path: 'edgar/prices/recent.parquet',
				columns: EDGAR_RECENT_COLUMNS,
				cacheKey: 'edgar.prices.recent',
				cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 2 } // 일증분 · 신선도 우선 10분 TTL
			});
			if (!rows) return null;
			return parseEdgarRecent(rows);
		} catch {
			return null;
		}
	})();
}

/** US 회사 주가(전체 이력, 오름차순). null = 미캐시·미발행. ticker 키(대문자). read 캐시·dedup 은 코어. */
export function loadEdgarCandles(ticker: string, core?: DataCore): Promise<Candle[] | null> {
	if (!browser) return Promise.resolve(null);
	const t = ticker.trim().toUpperCase();
	if (!t) return Promise.resolve(null);
	const dc = edgarCore(core);
	return (async () => {
		try {
			// 회사별 파일은 작다(~수백 KB) · HEAD probe 없이 GET 1 회 통파일(핫패스 RTT 최소화). 코어가 read 캐시·dedup.
			const rows = await dc.requestParquetWholeFile<EdgarPriceRow>({
				origin: 'hf',
				path: `edgar/prices/company/${t}.parquet`,
				columns: EDGAR_PRICE_COLUMNS,
				cacheKey: `edgar.prices.company:${t}`,
				cache: { scope: 'memory', ttlMs: 20 * 60_000, maxEntries: 128 } // 주가 신선도 · 짧은 TTL(20분), 회사 파일 주기 파생
			});
			if (!rows) return null;
			const candles = parseEdgarPriceRows(rows);
			return candles.length ? candles : null;
		} catch {
			return null;
		}
	})();
}
