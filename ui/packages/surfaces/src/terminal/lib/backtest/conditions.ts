// 조건 빌더 · "프리셋 고르기"가 아니라 *사용자가 규칙을 조립*하는 전문가급 커스텀 패널의 엔진.
// 좌변 지표 + 연산자 + 우변(상수 또는 다른 지표)을 조건 1개로, 여러 조건을 AND/OR 합성 → 진입/청산.
// terminal-strategy-lab 01 §2.4. 봉별 조건 만족(satisfied)도 산출 → 조건 레인 시각화(02 §1.5).
// look-ahead 0: 전 series 는 t 이전 데이터로만(지표 내부 보장), 체결은 엔진의 t+1 shift 가 상속.
import { atr, bollinger, ema, macd, realizedVol, rsi, sma, stochastic, volSma } from '../indicators';
import type { BtParamDef, Candle, PresetFamily } from './types';

const closesOf = (cs: Candle[]) => cs.map((c) => c.c);

// 조건 빌더가 노출하는 좌변/우변 지표 카탈로그 · 이게 "조작패널"이 보여주는 building block 목록.
export type SeriesKey =
	| 'price' | 'ma' | 'ema' | 'rsi' | 'stochK' | 'macdHist' | 'bbPctB'
	| 'volRatio' | 'atrPct' | 'realizedVol' | 'momRet' | 'high20Prox'
	| 'fundGate'; // ★펀더게이트 · 캔들 파생 아닌 *외부 PIT 시계열*(Piotroski 등) 주입. SERIES_CATALOG 비포함(별도 게이트 UI). W2

export interface SeriesDef {
	key: SeriesKey;
	kr: string;
	en: string;
	unit: '원' | '%' | '비율' | 'idx';
	params: BtParamDef[];
	calc: (cs: Candle[], p: Record<string, number>) => (number | null)[];
}

// 고저종/거래량을 쓰는 지표 · 종가만 쓰던 6프리셋의 약점(거래량·변동성 무시)을 조건 단위로 해소.
export const SERIES_CATALOG: SeriesDef[] = [
	{ key: 'price', kr: '종가', en: 'price', unit: '원', params: [], calc: (cs) => closesOf(cs) },
	{ key: 'ma', kr: '이동평균(SMA)', en: 'SMA', unit: '원', params: [{ name: 'period', kr: '기간', en: 'period', min: 5, max: 200, step: 5, def: 20 }], calc: (cs, p) => sma(closesOf(cs), p.period) },
	{ key: 'ema', kr: '지수이평(EMA)', en: 'EMA', unit: '원', params: [{ name: 'period', kr: '기간', en: 'period', min: 5, max: 200, step: 5, def: 20 }], calc: (cs, p) => ema(closesOf(cs), p.period) },
	{ key: 'rsi', kr: 'RSI', en: 'RSI', unit: 'idx', params: [{ name: 'period', kr: '기간', en: 'period', min: 2, max: 28, step: 1, def: 14 }], calc: (cs, p) => rsi(closesOf(cs), p.period) },
	{ key: 'stochK', kr: '스토캐스틱 %K', en: 'Stoch %K', unit: 'idx', params: [{ name: 'k', kr: 'K', en: 'k', min: 5, max: 21, step: 2, def: 14 }], calc: (cs, p) => stochastic(cs.map((c) => c.h), cs.map((c) => c.l), closesOf(cs), p.k, 3).k },
	{ key: 'macdHist', kr: 'MACD 히스토그램', en: 'MACD hist', unit: 'idx', params: [], calc: (cs) => macd(closesOf(cs), 12, 26, 9).hist },
	{ key: 'bbPctB', kr: '볼린저 %B', en: 'BB %B', unit: '비율', params: [{ name: 'period', kr: '기간', en: 'period', min: 10, max: 60, step: 5, def: 20 }, { name: 'mult', kr: '승수', en: 'mult', min: 1, max: 4, step: 0.5, def: 2 }], calc: (cs, p) => { const bb = bollinger(closesOf(cs), p.period, p.mult); return bb.upper.map((u, i) => (u != null && bb.lower[i] != null && u !== bb.lower[i] ? (cs[i].c - (bb.lower[i] as number)) / (u - (bb.lower[i] as number)) : null)); } },
	{ key: 'volRatio', kr: '거래량 비율(vs 평균)', en: 'vol ratio', unit: '비율', params: [{ name: 'period', kr: '기간', en: 'period', min: 5, max: 60, step: 5, def: 20 }], calc: (cs, p) => { const vs = volSma(cs.map((c) => c.v), p.period); return vs.map((m, i) => (m != null && m > 0 ? cs[i].v / m : null)); } },
	{ key: 'atrPct', kr: 'ATR(%종가)', en: 'ATR %', unit: '%', params: [{ name: 'period', kr: '기간', en: 'period', min: 7, max: 28, step: 7, def: 14 }], calc: (cs, p) => { const a = atr(cs.map((c) => c.h), cs.map((c) => c.l), closesOf(cs), p.period); return a.map((v, i) => (v != null && cs[i].c > 0 ? (v / cs[i].c) * 100 : null)); } },
	{ key: 'realizedVol', kr: '실현변동성(연%)', en: 'realized vol', unit: '%', params: [{ name: 'period', kr: '기간', en: 'period', min: 10, max: 120, step: 10, def: 20 }], calc: (cs, p) => realizedVol(closesOf(cs), p.period) },
	{ key: 'momRet', kr: '모멘텀 수익률(%)', en: 'momentum %', unit: '%', params: [{ name: 'lookback', kr: '관측N', en: 'lookback', min: 20, max: 252, step: 10, def: 120 }], calc: (cs, p) => { const c = closesOf(cs); return c.map((v, i) => (i >= p.lookback && c[i - p.lookback] > 0 ? (v / c[i - p.lookback] - 1) * 100 : null)); } },
	{ key: 'high20Prox', kr: 'N일 신고가 근접(%)', en: 'high proximity', unit: '%', params: [{ name: 'period', kr: '기간', en: 'period', min: 20, max: 252, step: 10, def: 60 }], calc: (cs, p) => { const c = closesOf(cs); return c.map((v, i) => { if (i < p.period - 1) return null; let hh = -Infinity; for (let j = i - p.period + 1; j <= i; j++) if (c[j] > hh) hh = c[j]; return hh > 0 ? (v / hh) * 100 : null; }); } }
];
const SERIES_BY_KEY = new Map(SERIES_CATALOG.map((s) => [s.key, s]));

export type Op = '>' | '<' | '>=' | '<=' | 'crossUp' | 'crossDown';
export const OP_LABEL: Record<Op, string> = { '>': '>', '<': '<', '>=': '≥', '<=': '≤', crossUp: '상향돌파', crossDown: '하향돌파' };

export interface Condition {
	left: SeriesKey;
	leftParams: Record<string, number>;
	op: Op;
	right: { kind: 'const'; value: number } | { kind: 'series'; key: SeriesKey; params: Record<string, number> };
}
export interface StrategyRule {
	entry: Condition[];
	entryCombine: 'AND' | 'OR';
	exit: Condition[];
	exitCombine: 'AND' | 'OR';
}

function seriesOf(cs: Candle[], key: SeriesKey, params: Record<string, number>): (number | null)[] {
	const def = SERIES_BY_KEY.get(key);
	if (!def) return cs.map(() => null);
	const p = { ...Object.fromEntries(def.params.map((d) => [d.name, d.def])), ...params };
	return def.calc(cs, p);
}

/** 조건 1개 → 봉별 만족 0/1 (좌·우 결측 봉 = 0, cross 는 직전봉 필요).
 *  gate = 펀더게이트 PIT 시계열(공시일 이후 봉부터 값, 그 전 null). left/right='fundGate' 일 때 주입. */
export function evalCondition(cs: Candle[], cond: Condition, gate: (number | null)[] | null = null): Uint8Array {
	const sel = (key: SeriesKey, params: Record<string, number>): (number | null)[] =>
		key === 'fundGate' ? gate ?? cs.map(() => null) : seriesOf(cs, key, params);
	const L = sel(cond.left, cond.leftParams);
	let R: (number | null)[];
	if (cond.right.kind === 'const') { const v = cond.right.value; R = cs.map(() => v); }
	else R = sel(cond.right.key, cond.right.params);
	const out = new Uint8Array(cs.length);
	for (let i = 0; i < cs.length; i++) {
		const l = L[i];
		const r = R[i];
		if (l == null || r == null) continue;
		if (cond.op === '>') out[i] = l > r ? 1 : 0;
		else if (cond.op === '<') out[i] = l < r ? 1 : 0;
		else if (cond.op === '>=') out[i] = l >= r ? 1 : 0;
		else if (cond.op === '<=') out[i] = l <= r ? 1 : 0;
		else {
			const lp = L[i - 1];
			const rp = R[i - 1];
			if (lp == null || rp == null) continue;
			if (cond.op === 'crossUp') out[i] = lp <= rp && l > r ? 1 : 0;
			else out[i] = lp >= rp && l < r ? 1 : 0; // crossDown
		}
	}
	return out;
}

function combine(sats: Uint8Array[], mode: 'AND' | 'OR', n: number): Uint8Array {
	const out = new Uint8Array(n);
	if (!sats.length) return out;
	for (let i = 0; i < n; i++) {
		let acc = mode === 'AND' ? 1 : 0;
		for (const s of sats) acc = mode === 'AND' ? (acc && s[i] ? 1 : 0) : (acc || s[i] ? 1 : 0);
		out[i] = acc;
	}
	return out;
}

export interface RuleEval {
	target: Int8Array; // long/flat (엔진 체결 입력 · 기존 preset.signal 과 동일 계약)
	entrySat: Uint8Array[]; // 진입 조건별 만족 (조건 레인)
	exitSat: Uint8Array[]; // 청산 조건별 만족
	entryCombined: Uint8Array; // AND/OR 합성 진입 신호
	exitCombined: Uint8Array;
}

/** 룰 → target(long/flat 상태기계) + 조건 레인. 진입조건 충족시 진입, 보유중 청산조건 충족시 청산.
 *  gate = 펀더게이트 PIT 시계열(있으면 fundGate 조건이 이를 소비 · 공시 전 봉 null=진입차단, look-ahead 0). */
export function evalRule(cs: Candle[], rule: StrategyRule, gate: (number | null)[] | null = null): RuleEval {
	const n = cs.length;
	const entrySat = rule.entry.map((c) => evalCondition(cs, c, gate));
	const exitSat = rule.exit.map((c) => evalCondition(cs, c, gate));
	const entryCombined = combine(entrySat, rule.entryCombine, n);
	const exitCombined = combine(exitSat, rule.exitCombine, n);
	const target = new Int8Array(n);
	let state = 0;
	for (let i = 0; i < n; i++) {
		if (state === 0) state = entryCombined[i] ? 1 : 0;
		else state = exitCombined.length && exitCombined[i] ? 0 : 1;
		// 청산 조건이 비어있으면(exit 0개) 진입신호가 꺼질 때 청산(보유=진입조건 유지) · signal-following.
		if (state === 1 && !rule.exit.length) state = entryCombined[i] ? 1 : 0;
		target[i] = state;
	}
	return { target, entrySat, exitSat, entryCombined, exitCombined };
}

// ── rule 프리셋 · 종가만 쓰던 6프리셋 너머. 전부 편집 가능(빌더에서 불러와 조건 수정). OHLCV 활용. ──
const cond = (left: SeriesKey, leftParams: Record<string, number>, op: Op, right: Condition['right']): Condition => ({ left, leftParams, op, right });
const k = (value: number): Condition['right'] => ({ kind: 'const', value });
const ser = (key: SeriesKey, params: Record<string, number>): Condition['right'] => ({ kind: 'series', key, params });

export type { PresetFamily };
export const FAMILY_LABEL: Record<PresetFamily, { kr: string; en: string }> = {
	trend: { kr: '추세', en: 'Trend' }, momentum: { kr: '모멘텀', en: 'Momentum' }, meanRevert: { kr: '평균회귀', en: 'Mean-Revert' }, volatility: { kr: '변동성', en: 'Volatility' }
};
export const FAMILY_ORDER: PresetFamily[] = ['trend', 'momentum', 'meanRevert', 'volatility'];
export interface RulePreset { key: string; kr: string; en: string; descKr: string; descEn: string; family: PresetFamily; make: () => StrategyRule; }

export const RULE_PRESETS: RulePreset[] = [
	{
		key: 'volConfirmTrend', family: 'trend', kr: '거래량 확인 추세', en: 'Volume-Confirmed Trend',
		descKr: '가격 > 60일선 그리고 거래량 평균 1.5배 초과(fake breakout 제거)', descEn: 'price>MA60 AND volume>1.5× avg',
		make: () => ({ entry: [cond('price', {}, '>', ser('ma', { period: 60 })), cond('volRatio', { period: 20 }, '>', k(1.5))], entryCombine: 'AND', exit: [cond('price', {}, '<', ser('ma', { period: 60 }))], exitCombine: 'OR' })
	},
	{
		key: 'lowVolMomentum', family: 'momentum', kr: '저변동 모멘텀', en: 'Low-Vol Momentum',
		descKr: '120일 수익률 > 0 그리고 실현변동성 < 30%(추세 + 낮은 변동)', descEn: '120d return>0 AND realized vol<30%',
		make: () => ({ entry: [cond('momRet', { lookback: 120 }, '>', k(0)), cond('realizedVol', { period: 60 }, '<', k(30))], entryCombine: 'AND', exit: [cond('momRet', { lookback: 120 }, '<', k(0))], exitCombine: 'OR' })
	},
	{
		key: 'breakoutVolume', family: 'volatility', kr: '거래량 신고가 돌파', en: 'Volume Breakout',
		descKr: '60일 신고가 99% 근접 그리고 거래량 2배 급증', descEn: 'near 60d high AND volume>2× avg',
		make: () => ({ entry: [cond('high20Prox', { period: 60 }, '>=', k(99)), cond('volRatio', { period: 20 }, '>', k(2))], entryCombine: 'AND', exit: [cond('high20Prox', { period: 60 }, '<', k(90))], exitCombine: 'OR' })
	},
	{
		key: 'stochRevert', family: 'meanRevert', kr: '스토캐스틱 반전', en: 'Stochastic Revert',
		descKr: '%K < 20 진입, > 80 청산(과매도 반등)', descEn: 'enter %K<20, exit %K>80',
		make: () => ({ entry: [cond('stochK', { k: 14 }, '<', k(20))], entryCombine: 'AND', exit: [cond('stochK', { k: 14 }, '>', k(80))], exitCombine: 'OR' })
	},
	{
		key: 'bbMeanRevert', family: 'meanRevert', kr: '볼린저 %B 평균회귀', en: 'BB %B Mean-Revert',
		descKr: '%B < 0.05(하단 이탈) 진입, > 0.5(중심) 청산', descEn: 'enter %B<0.05, exit %B>0.5',
		make: () => ({ entry: [cond('bbPctB', { period: 20, mult: 2 }, '<', k(0.05))], entryCombine: 'AND', exit: [cond('bbPctB', { period: 20, mult: 2 }, '>', k(0.5))], exitCombine: 'OR' })
	},
	{
		key: 'maCrossVol', family: 'trend', kr: '저변동 골든크로스', en: 'Low-Vol MA Cross',
		descKr: '20일선 상향돌파 60일선 그리고 ATR < 4%(변동성 스파이크 회피)', descEn: 'MA20 crossUp MA60 AND ATR<4%',
		make: () => ({ entry: [cond('ma', { period: 20 }, 'crossUp', ser('ma', { period: 60 })), cond('atrPct', { period: 14 }, '<', k(4))], entryCombine: 'AND', exit: [cond('ma', { period: 20 }, 'crossDown', ser('ma', { period: 60 }))], exitCombine: 'OR' })
	},
	{
		key: 'ma200Trend', family: 'trend', kr: '200일선 추세필터', en: '200MA Trend Filter',
		descKr: '50일선이 200일선 상향돌파 & 가격>200일선(하락장 휩쏘 차단)', descEn: 'MA50 crosses up MA200 while price>MA200',
		make: () => ({ entry: [cond('ma', { period: 50 }, 'crossUp', ser('ma', { period: 200 })), cond('price', {}, '>', ser('ma', { period: 200 }))], entryCombine: 'AND', exit: [cond('ma', { period: 50 }, 'crossDown', ser('ma', { period: 200 }))], exitCombine: 'OR' })
	},
	{
		key: 'dualMomentum', family: 'momentum', kr: '듀얼 모멘텀', en: 'Dual Momentum',
		descKr: '12개월 수익률>0 & 가격>200일선(절대+추세)', descEn: '12m return>0 AND price>MA200',
		make: () => ({ entry: [cond('momRet', { lookback: 252 }, '>', k(0)), cond('price', {}, '>', ser('ma', { period: 200 }))], entryCombine: 'AND', exit: [cond('momRet', { lookback: 252 }, '<', k(0)), cond('price', {}, '<', ser('ma', { period: 200 }))], exitCombine: 'OR' })
	},
	{
		key: 'trendPullback', family: 'meanRevert', kr: '추세 눌림목', en: 'Trend Pullback',
		descKr: '상승추세(>200일선)에서 RSI(7)<15 눌림 매수, RSI>70/5일선 이탈 청산', descEn: 'buy dips (RSI7<15) in an uptrend (>MA200)',
		make: () => ({ entry: [cond('price', {}, '>', ser('ma', { period: 200 })), cond('rsi', { period: 7 }, '<', k(15))], entryCombine: 'AND', exit: [cond('rsi', { period: 7 }, '>', k(70)), cond('price', {}, '<', ser('ma', { period: 5 }))], exitCombine: 'OR' })
	},
	{
		key: 'connorsRsi2', family: 'meanRevert', kr: 'RSI(2) 단기반전', en: 'Connors RSI-2',
		descKr: '상승추세에서 RSI(2)<10 급락 매수(단기·노이즈 높음), RSI>70/5일선 회복 청산', descEn: 'RSI(2)<10 dip in uptrend (short-term, noisy)',
		make: () => ({ entry: [cond('price', {}, '>', ser('ma', { period: 200 })), cond('rsi', { period: 2 }, '<', k(10))], entryCombine: 'AND', exit: [cond('rsi', { period: 2 }, '>', k(70)), cond('price', {}, '>', ser('ma', { period: 5 }))], exitCombine: 'OR' })
	},
	{
		key: 'high52wTrend', family: 'momentum', kr: '52주 신고가 추세', en: '52W High Trend',
		descKr: '52주 신고가 98% 근접 & 가격>50일선(신고가 추세추종)', descEn: 'near 52w high AND price>MA50',
		make: () => ({ entry: [cond('high20Prox', { period: 252 }, '>=', k(98)), cond('price', {}, '>', ser('ma', { period: 50 }))], entryCombine: 'AND', exit: [cond('price', {}, '<', ser('ma', { period: 50 }))], exitCombine: 'OR' })
	},
	{
		key: 'squeezeBreakout', family: 'volatility', kr: '변동성 수축 돌파', en: 'Squeeze Breakout',
		descKr: 'ATR<3%(조용) & 60일 신고가 & 거래량 2배(터짐), 20일선 이탈/ATR>7% 청산', descEn: 'low ATR squeeze + breakout on 2x volume',
		make: () => ({ entry: [cond('atrPct', { period: 14 }, '<', k(3)), cond('high20Prox', { period: 60 }, '>=', k(99)), cond('volRatio', { period: 20 }, '>', k(2))], entryCombine: 'AND', exit: [cond('price', {}, '<', ser('ma', { period: 20 })), cond('atrPct', { period: 14 }, '>', k(7))], exitCombine: 'OR' })
	},
	{
		key: 'lowVolTrend', family: 'volatility', kr: '저변동 추세추종', en: 'Low-Vol Trend',
		descKr: '가격>200일선 & 실현변동성<30% & 120일 수익률>0(저변동 우위)', descEn: 'uptrend with low realized vol',
		make: () => ({ entry: [cond('price', {}, '>', ser('ma', { period: 200 })), cond('realizedVol', { period: 60 }, '<', k(30)), cond('momRet', { lookback: 120 }, '>', k(0))], entryCombine: 'AND', exit: [cond('price', {}, '<', ser('ma', { period: 200 })), cond('realizedVol', { period: 60 }, '>', k(50))], exitCombine: 'OR' })
	},
	{
		key: 'emaDualTrend', family: 'trend', kr: 'EMA 듀얼 추세', en: 'EMA 8-21 Trend',
		descKr: 'EMA8이 EMA21 상향돌파 & 가격>100일선(빠른 스윙 추세)', descEn: 'EMA8 crosses up EMA21 above MA100',
		make: () => ({ entry: [cond('ema', { period: 8 }, 'crossUp', ser('ema', { period: 21 })), cond('price', {}, '>', ser('ma', { period: 100 }))], entryCombine: 'AND', exit: [cond('ema', { period: 8 }, 'crossDown', ser('ema', { period: 21 }))], exitCombine: 'OR' })
	},
	{
		key: 'bbFullRevert', family: 'meanRevert', kr: '볼린저 2시그마 반대편', en: 'BB Full Revert',
		descKr: '하단밴드 이탈(%B<0)에서 상승추세만 매수, 상단밴드(%B>1) 청산', descEn: 'enter below lower band in uptrend, exit above upper',
		make: () => ({ entry: [cond('bbPctB', { period: 20, mult: 2 }, '<', k(0)), cond('price', {}, '>', ser('ma', { period: 200 }))], entryCombine: 'AND', exit: [cond('bbPctB', { period: 20, mult: 2 }, '>', k(1))], exitCombine: 'OR' })
	}
];

/** 워밍업 · 룰 내 모든 series 의 최대 기간(보수적으로 period/lookback 최대값). */
export function ruleWarmup(rule: StrategyRule): number {
	let w = 1;
	const scan = (c: Condition) => {
		for (const v of Object.values(c.leftParams)) w = Math.max(w, v);
		if (c.right.kind === 'series') for (const v of Object.values(c.right.params)) w = Math.max(w, v);
	};
	rule.entry.forEach(scan);
	rule.exit.forEach(scan);
	return Math.ceil(w) + 1;
}
