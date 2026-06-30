// 백테스트 프리셋 레지스트리 · 신호 함수 정의. 변경 이유: 전략 추가/수정(엔진 체결 의미와 분리, 03 §0.5.3).
// 프리셋은 교육·탐색용 (추천 아님, 03 §9.1·§14). 각 preset 은 param schema·warmup 보유.
import { sma, rsi, macd, bollinger } from '../indicators';
import type { BtPresetDef } from './types';

export const BT_PRESETS: BtPresetDef[] = [
	{
		key: 'maCross',
		family: 'trend',
		kr: '골든크로스',
		en: 'MA Cross',
		descKr: '단기 이평 > 장기 이평이면 보유',
		descEn: 'hold while fast SMA > slow SMA',
		params: [
			{ name: 'fast', kr: '단기', en: 'fast', min: 5, max: 50, step: 5, def: 20 },
			{ name: 'slow', kr: '장기', en: 'slow', min: 20, max: 200, step: 10, def: 60 }
		],
		warmup: (p) => p.slow,
		signal: (c, p) => {
			const f = sma(c, p.fast);
			const s = sma(c, p.slow);
			const t = new Int8Array(c.length);
			for (let i = 0; i < c.length; i++) t[i] = f[i] != null && s[i] != null && (f[i] as number) > (s[i] as number) ? 1 : 0;
			return t;
		}
	},
	{
		key: 'rsiRevert',
		family: 'meanRevert',
		kr: 'RSI 과매도 반등',
		en: 'RSI Revert',
		descKr: 'RSI < 매수선 진입, > 매도선 청산',
		descEn: 'enter RSI < buy, exit > sell',
		params: [
			{ name: 'period', kr: '기간', en: 'period', min: 7, max: 28, step: 7, def: 14 },
			{ name: 'buyTh', kr: '매수선', en: 'buy', min: 10, max: 40, step: 5, def: 30 },
			{ name: 'sellTh', kr: '매도선', en: 'sell', min: 55, max: 80, step: 5, def: 70 }
		],
		warmup: (p) => p.period + 1,
		signal: (c, p) => {
			const r = rsi(c, p.period);
			const t = new Int8Array(c.length);
			let state = 0;
			for (let i = 0; i < c.length; i++) {
				const v = r[i];
				if (v != null) state = state === 0 ? (v < p.buyTh ? 1 : 0) : v > p.sellTh ? 0 : 1;
				t[i] = state;
			}
			return t;
		}
	},
	{
		key: 'bbRevert',
		family: 'meanRevert',
		kr: '볼린저 하단회귀',
		en: 'BB Revert',
		descKr: '종가 < 하단밴드 진입, ≥ 중심선 청산',
		descEn: 'enter below lower band, exit at mid',
		params: [
			{ name: 'period', kr: '기간', en: 'period', min: 10, max: 60, step: 5, def: 20 },
			{ name: 'mult', kr: '승수', en: 'mult', min: 1, max: 4, step: 0.5, def: 2 }
		],
		warmup: (p) => p.period,
		signal: (c, p) => {
			const bb = bollinger(c, p.period, p.mult);
			const t = new Int8Array(c.length);
			let state = 0;
			for (let i = 0; i < c.length; i++) {
				const lo = bb.lower[i];
				const mid = bb.mid[i];
				if (lo != null && mid != null) state = state === 0 ? (c[i] < lo ? 1 : 0) : c[i] >= mid ? 0 : 1;
				t[i] = state;
			}
			return t;
		}
	},
	{
		key: 'macdCross',
		family: 'trend',
		kr: 'MACD 시그널',
		en: 'MACD Cross',
		descKr: 'MACD선 > 시그널선이면 보유',
		descEn: 'hold while MACD > signal',
		params: [
			{ name: 'fast', kr: '단기', en: 'fast', min: 5, max: 20, step: 1, def: 12 },
			{ name: 'slow', kr: '장기', en: 'slow', min: 20, max: 60, step: 1, def: 26 },
			{ name: 'sig', kr: '시그널', en: 'sig', min: 5, max: 15, step: 1, def: 9 }
		],
		warmup: (p) => p.slow + p.sig,
		signal: (c, p) => {
			const m = macd(c, p.fast, p.slow, p.sig);
			const t = new Int8Array(c.length);
			const start = p.slow + p.sig;
			for (let i = start; i < c.length; i++) t[i] = m.line[i] > m.signal[i] ? 1 : 0;
			return t;
		}
	},
	{
		key: 'donchian',
		family: 'trend',
		kr: '채널 돌파 (터틀)',
		en: 'Donchian Break',
		descKr: 'N일 최고가 돌파 진입, M일 최저가 이탈 청산',
		descEn: 'enter on N-day high break, exit on M-day low',
		params: [
			{ name: 'entry', kr: '진입N', en: 'entry', min: 10, max: 100, step: 5, def: 20 },
			{ name: 'exit', kr: '청산M', en: 'exit', min: 5, max: 50, step: 5, def: 10 }
		],
		warmup: (p) => Math.max(p.entry, p.exit) + 1,
		// 종가 기준 채널 · 당일 종가가 직전 N일(당일 제외) 최고 종가 초과 시 진입 (look-ahead 0)
		signal: (c, p) => {
			const t = new Int8Array(c.length);
			let state = 0;
			for (let i = 1; i < c.length; i++) {
				let hh = -Infinity;
				let ll = Infinity;
				const eFrom = Math.max(0, i - p.entry);
				const xFrom = Math.max(0, i - p.exit);
				for (let j = eFrom; j < i; j++) if (c[j] > hh) hh = c[j];
				for (let j = xFrom; j < i; j++) if (c[j] < ll) ll = c[j];
				if (i < p.entry) { t[i] = 0; continue; }
				state = state === 0 ? (c[i] > hh ? 1 : 0) : c[i] < ll ? 0 : 1;
				t[i] = state;
			}
			return t;
		}
	},
	{
		key: 'momentum',
		family: 'momentum',
		kr: '절대 모멘텀',
		en: 'Momentum',
		descKr: 'N일 수익률 > 0 이면 보유 (듀얼모멘텀의 절대축)',
		descEn: 'hold while N-day return > 0',
		params: [{ name: 'lookback', kr: '관측N', en: 'lookback', min: 60, max: 252, step: 21, def: 126 }],
		warmup: (p) => p.lookback + 1,
		signal: (c, p) => {
			const t = new Int8Array(c.length);
			for (let i = p.lookback; i < c.length; i++) t[i] = c[i - p.lookback] > 0 && c[i] > c[i - p.lookback] ? 1 : 0;
			return t;
		}
	}
];
