// 공공데이터포털 금융위원회_주식시세정보(공공누리/KOGL, 비상업+출처표시 재배포 가능) 기반 주가 캐시.
// KRX OpenAPI(제3자 제공 금지)와 달리 dartlab(비상업)은 출처표시 조건으로 공개 재배포·표시 합법.
//
// 파이프라인 (프리빌드 아님 · 런타임 온디맨드):
//   1. 읽기 · HF `gov/prices/company/{code}.parquet` (공개·토큰 0, origin.ts HF_RESOLVE 경유).
//   2. 미스 & 로컬 dev · Vite dev 미들웨어 `/__gov` 가 data.go.kr 라이브 호출 → 정규화 → HF 업로드 → 반환.
//   3. 프로덕션 · 캐시 읽기 전용(미스 시 호출측이 KRX 폴백). 운영자가 로컬에서 열며 공유 HF 캐시를 채운다.
// 출처표시 의무(공공누리): gov 데이터 표시 시 contracts 의 GOV_ATTRIBUTION 노출.
import type { Candle } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';
import { originConfigured } from '../../../data/origins/registry';

const browser = typeof window !== 'undefined';

export interface GovCandleFile {
	source: string;
	code: string;
	asOf: string;
	candles: Candle[];
}

// publicPricePort 는 ui/web 레거시·로컬 어댑터 양쪽이 호출하므로 core 미주입 경로 전용 모듈 폴백 코어를 lazy
// 생성한다(financeSource.financeRowsCore 동형). 어댑터는 자신의 createDataCore() 를 주입한다.
// 옛 cache·inflight·recentPromise Map(결과/in-flight 수기 관리)은 폐기 · 코어가 read 레벨에서 캐시·dedup.
const govCore = moduleFallbackCore();

// HF 캐시 = 회사별 parquet (gov/prices/company 동일 schema). 필요한 OHLCV+등락률 컬럼만 projection.
// fluctuationRate = 기준가 대비 등락률 · 수정주가(adjustCandles) 체이닝 입력.
const GOV_PARQUET_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume', 'fluctuationRate', 'tradedValue'];
interface GovRow extends Record<string, unknown> {
	date?: string | null;
	open?: number | null;
	high?: number | null;
	low?: number | null;
	close?: number | null;
	volume?: number | null;
	fluctuationRate?: number | null;
	tradedValue?: number | null;
}
function rowToCandle(r: GovRow): Candle | null {
	const c = Number(r.close);
	const t = r.date == null ? '' : String(r.date);
	if (!t || !Number.isFinite(c) || c <= 0) return null;
	const fr = Number(r.fluctuationRate);
	const tv = Number(r.tradedValue);
	return { t, o: Number(r.open) || c, h: Number(r.high) || c, l: Number(r.low) || c, c, v: Number(r.volume) || 0, r: Number.isFinite(fr) ? fr : null, tv: Number.isFinite(tv) ? tv : null };
}
function pick(j: unknown): Candle[] | null {
	const f = j as GovCandleFile | null;
	return f && Array.isArray(f.candles) && f.candles.length ? f.candles : null;
}

async function readHf(core: DataCore, code: string): Promise<Candle[] | null> {
	try {
		// 회사별 파일은 작다(~100KB) · HEAD probe 없이 GET 1 회 통파일 (핫패스 RTT 최소화). 코어가 read 캐시·dedup.
		const rows = await core.requestParquetWholeFile<GovRow>({
			origin: 'hf',
			path: `gov/prices/company/${code}.parquet`,
			columns: GOV_PARQUET_COLUMNS,
			cacheKey: `gov.prices.company:${code}`,
			cache: { scope: 'memory', ttlMs: 20 * 60_000, maxEntries: 128 } // 주가 신선도 · 짧은 TTL(20분), 회사 파일 주간 파생
		});
		if (!rows) return null;
		const candles = rows.map(rowToCandle).filter((x): x is Candle => x != null);
		return candles.length ? candles : null;
	} catch {
		return null;
	}
}

async function fillViaDev(core: DataCore, code: string): Promise<Candle[] | null> {
	if (!originConfigured('govDev')) return null; // 프로덕션: 미들웨어 없음 → 읽기 전용
	try {
		// 작업대 경유(코어 request) · origin 'govDev' = Vite /__gov 미들웨어. dev fill 무캐시(즉시 HF 반영),
		// 코어가 동일 코드 동시호출 dedup(중복 data.go.kr 호출 차단). 옛 raw fetch 폐기(data-wiring SSOT).
		const j = await core.request<unknown>({
			origin: 'govDev',
			path: code,
			parse: (res) => (res.ok ? res.json() : Promise.resolve(null)),
			cacheKey: `gov.dev:${code}`
		});
		return pick(j);
	} catch {
		return null;
	}
}

// 최근 30거래일 전종목 슬림 1파일 · 회사 파일(주간 파생)과 병합하는 신선 tail.
// 전 종목이 한 파일을 공유 → 첫 다운로드 후 회사 전환 시 tail 비용 0(코어 read 캐시 공유).
const RECENT_COLUMNS = ['stockCode', 'date', 'open', 'high', 'low', 'close', 'volume', 'fluctuationRate', 'tradedValue'];

/** 최근 거래일 tail (code → 캔들 오름차순, JSON-safe Record). null = recent 파일 미존재. 코어가 캐시·dedup. */
export function loadGovRecent(core?: DataCore): Promise<Record<string, Candle[]> | null> {
	if (!browser) return Promise.resolve(null);
	return (async () => {
		try {
			const rows = await govCore(core).requestParquetWholeFile<GovRow & { stockCode?: string | null }>({
				origin: 'hf',
				path: 'gov/prices/recent.parquet',
				columns: RECENT_COLUMNS,
				cacheKey: 'gov.prices.recent',
				cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 2 } // 최근 거래일 슬림 파일 · 신선도 우선 10분 TTL
			});
			if (!rows) return null;
			const map: Record<string, Candle[]> = {};
			for (const r of rows) {
				const codeKey = r.stockCode == null ? '' : String(r.stockCode);
				const c = rowToCandle(r);
				if (!codeKey || !c) continue;
				(map[codeKey] ??= []).push(c);
			}
			return map;
		} catch {
			return null;
		}
	})();
}

/** gov 캐시 주가(전체 이력, 오름차순). null = 미캐시·미지원. read 캐시·dedup 은 코어(옛 cache/inflight Map 폐기). */
export function loadGovCandles(code: string, core?: DataCore): Promise<Candle[] | null> {
	if (!browser) return Promise.resolve(null);
	const c = code.trim();
	const dc = govCore(core);
	return (async () => {
		const candles = await readHf(dc, c);
		return candles ?? (await fillViaDev(dc, c));
	})();
}
