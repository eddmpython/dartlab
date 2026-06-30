// US FRED 지수 = macro/fred/observations.parquet 직독(종가 value 1컬럼) → degenerate Candle.
// macroSource 의 srcCache(loadSource('fred')) 재사용 · fred 파일 1 회 로드 공유(중복 다운로드 0).
// FRED /series/observations 는 (date, value) 2컬럼이라 OHLC 부재 → o=h=l=c=value, v=0(거래량 부재 정직).
// 화이트리스트 게이팅: US_INDEX_PRESETS 의 seriesId 4종만 · 임의 FRED 시리즈 fetch 차단(raw dump 방지).
import type { Candle, IndexRef } from '@dartlab/ui-contracts';
import { US_INDEX_PRESETS } from '@dartlab/ui-contracts';
import { loadFredSeriesPoints } from './macroSource';
import type { DataCore } from '../../../data/fetch/request';

const US_BY_SERIES = new Map(US_INDEX_PRESETS.map((r) => [r.seriesId as string, r]));

/** FRED 종가 시리즈 → degenerate Candle[](o=h=l=c=value, v=0). null = 미존재/미화이트리스트. */
export async function loadFredIndexCandles(ref: IndexRef, core?: DataCore): Promise<Candle[] | null> {
	const sid = ref.seriesId;
	if (!sid || !US_BY_SERIES.has(sid)) return null; // 화이트리스트 게이팅(임의 fetch 차단)
	const pts = await loadFredSeriesPoints(sid, core); // [{d:'YYYYMMDD', v}] 오름차순 or null
	if (!pts || !pts.length) return null;
	return pts.map((p) => ({ t: p.d, o: p.v, h: p.v, l: p.v, c: p.v, v: 0, r: null, tv: null }));
}

/** US preset 라벨/seriesId 부분일치 검색(FRED universe 확장 0 · 큐레이트 4종만). */
export function searchUsIndexPresets(query: string): IndexRef[] {
	const q = query.trim();
	if (!q) return [];
	const up = q.toUpperCase();
	return US_INDEX_PRESETS.filter((r) => r.name.includes(q) || (r.seriesId ?? '').toUpperCase().includes(up));
}
