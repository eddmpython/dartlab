// 국내 시장지수 동행(베타) · "이 종목이 시장(코스피·코스닥)과 얼마나 같이 움직였나".
// ⚠ 시장 베타일 뿐 인과 아님. 거시 driver 와 *별도 행*으로 분리 · 대형주는 지수 상관이 거의 항상 최상위라
//   같은 랭킹에 섞으면 거시를 밀어낸다(발견성 훼손). US 지수(SP500·나스닥·VIX 등)는 이미 MACRO_SERIES 라 여기 없음.
// 회사 무관 시리즈라 모듈 캐시 1회 로드 (macro srcCache 와 동일 사상).
import type { Candle, IndexRef, MacroPoint, MacroSeriesDef } from '@dartlab/ui-contracts';
import { KR_INDEX_PRESETS } from '@dartlab/ui-contracts';

// 코스피·코스닥 광의 2종만 · 200/150/KRX300 은 광의와 강상관(중복)이라 제외(다중공선성 clutter 회피).
export const MARKET_INDEX_REFS: IndexRef[] = KR_INDEX_PRESETS.filter((r) => r.name === '코스피' || r.name === '코스닥');

// econOverlay 폴백(gray)과 구분되는 시장 톤(amber/orange) · "시장 맥락" 식별.
export const MARKET_INDEX_COLORS: Record<string, string> = {
	'idx:KOSPI/코스피': '#fbbf24',
	'idx:KOSDAQ/코스닥': '#fb923c'
};

/** IndexRef → 오버레이용 합성 def. econOverlay 는 def 의 id/kr/en/unit/digits 만 사용(src 무관). */
export function marketIndexDef(ref: IndexRef): MacroSeriesDef {
	return { id: ref.code, src: 'ecos', kr: ref.name, en: ref.name, unit: 'pt', digits: 0 };
}

const candleClose = (cs: Candle[]): MacroPoint[] =>
	cs.filter((k) => k.t && Number.isFinite(k.c)).map((k) => ({ d: k.t, v: k.c }));

let cache: Promise<{ ref: IndexRef; points: MacroPoint[] }[]> | null = null;
/** 시장지수 종가 시계열(MacroPoint) · 모듈 캐시 1회. rt.index.series 로 로드(회사 무관). */
export function loadMarketIndexSeries(
	index: { series: (ref: IndexRef) => Promise<Candle[] | null> }
): Promise<{ ref: IndexRef; points: MacroPoint[] }[]> {
	if (cache) return cache;
	cache = Promise.all(MARKET_INDEX_REFS.map(async (ref) => ({ ref, points: candleClose((await index.series(ref)) ?? []) })));
	return cache;
}
