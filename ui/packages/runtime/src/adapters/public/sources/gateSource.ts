// 펀더게이트 소스 · gov/fundamental-gate.parquet(전종목 단일파일, 실측 0.031MB) 통파일 로드 후 종목 필터.
// terminal-strategy-lab W2 (간판②). 데이터 워크벤치 SSOT: data/fetch 코어가 read 레벨 캐시·dedup(통파일 1회 다운로드 공유).
// 게이트 = (stockCode·bsnsYear·rceptDt 공시일·piotroski). 소비부(PriceChart)가 buildGateSeries 로 봉별 PIT 계단화.

import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const browser = typeof window !== 'undefined';

interface GateRowRaw {
	stockCode: string;
	bsnsYear: string;
	rceptDt: string;
	piotroski: number;
	[key: string]: unknown; // requestParquetWholeFile<T extends Record<string, unknown>> 제약 충족
}
const GATE_COLUMNS = ['stockCode', 'bsnsYear', 'rceptDt', 'piotroski'];

/** 펀더게이트 한 행(소비 계약 · gate.ts GateRow 와 동형). */
export interface FundamentalGateRow {
	rceptDt: string; // YYYYMMDD 공시일(PIT 앵커)
	piotroski: number; // 0~9
}

async function readGate(core: DataCore): Promise<GateRowRaw[] | null> {
	try {
		// 통파일(0.031MB) · HEAD probe 없이 GET 1회. 코어가 read 캐시(cacheKey 공유)·dedup → 종목마다 재다운로드 0.
		const rows = await core.requestParquetWholeFile<GateRowRaw>({
			origin: 'hf',
			path: 'gov/fundamental-gate.parquet',
			columns: GATE_COLUMNS,
			cacheKey: 'fundamental.gate.all',
			cache: { scope: 'memory', ttlMs: 60 * 60_000, maxEntries: 2 } // 펀더는 분기 갱신 · 긴 TTL(60분)
		});
		return rows ?? null;
	} catch {
		return null;
	}
}

const gateCore = moduleFallbackCore();

/** 한 종목의 펀더게이트 행(rceptDt·piotroski) · 전체파일 1회 로드(캐시 공유) 후 stockCode 필터.
 *  미존재/실패/커버리지밖(2020 이전) = null 또는 빈배열(정직 폴백 · 게이트 미평가). */
export async function loadGateRows(stockCode: string): Promise<FundamentalGateRow[] | null> {
	if (!browser) return null;
	const all = await readGate(gateCore());
	if (!all) return null;
	const code = stockCode.trim();
	return all
		.filter((r) => String(r.stockCode) === code)
		.map((r) => ({ rceptDt: String(r.rceptDt), piotroski: Number(r.piotroski) }))
		.filter((r) => r.rceptDt.length === 8 && Number.isFinite(r.piotroski));
}
