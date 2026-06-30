import { describe, expect, it } from 'vitest';
import { buildGateSeries, ruleUsesGate } from './gate';
import { evalCondition, evalRule } from './conditions';
import { runBacktestRule } from './engine';
import type { Candle } from './types';
import type { Condition, StrategyRule } from './conditions';

describe('buildGateSeries · PIT 계단(look-ahead 0)', () => {
	it('공시일 이후 봉부터 값, 그 전 null · 계단 유지', () => {
		const dates = ['20210101', '20210301', '20210401', '20220301', '20220401'];
		const rows = [
			{ rceptDt: '20210315', piotroski: 4 }, // 2020 사업보고서
			{ rceptDt: '20220318', piotroski: 8 } // 2021 사업보고서
		];
		const g = buildGateSeries(dates, rows);
		// 20210101·20210301 = 첫 공시(0315) 전 → null
		expect(g[0]).toBeNull();
		expect(g[1]).toBeNull();
		// 20210401 = 0315 이후 → 4 (계단)
		expect(g[2]).toBe(4);
		// 20220301 = 아직 0318 전 → 여전히 4
		expect(g[3]).toBe(4);
		// 20220401 = 0318 이후 → 8
		expect(g[4]).toBe(8);
	});
});

describe('fundGate 조건 · 재무 게이트 진입 차단', () => {
	const mkCandles = (n: number): Candle[] =>
		Array.from({ length: n }, (_, i) => ({ t: `2021${String(i + 1).padStart(4, '0')}`, o: 100, h: 101, l: 99, c: 100, v: 1000 }));

	it('evalCondition: fundGate≥6 · gate null/저점=0, 충족=1', () => {
		const cs = mkCandles(4);
		const gate = [null, 4, 7, 8]; // 봉별 Piotroski
		const cond: Condition = { left: 'fundGate', leftParams: {}, op: '>=', right: { kind: 'const', value: 6 } };
		const sat = evalCondition(cs, cond, gate);
		expect(Array.from(sat)).toEqual([0, 0, 1, 1]); // null·4=차단, 7·8=통과
	});

	it('evalRule + 게이트: 공시 전엔 진입 0 (gate=null 봉)', () => {
		const cs = mkCandles(4);
		const gate = [null, null, 7, 7];
		const rule: StrategyRule = {
			entry: [{ left: 'fundGate', leftParams: {}, op: '>=', right: { kind: 'const', value: 6 } }],
			entryCombine: 'AND',
			exit: [],
			exitCombine: 'OR'
		};
		const ev = evalRule(cs, rule, gate);
		expect(Array.from(ev.entryCombined)).toEqual([0, 0, 1, 1]);
		expect(ruleUsesGate(rule)).toBe(true);
	});

	it('MAE/MFE: 보유 중 최대역행·최대순행 추적(S2 거래분석)', () => {
		// 8봉, 비용 0. 항상-진입 룰(price>0) → 봉1 진입 후 보유. 봉4 저가 80(역행), 봉5 고가 130(순행).
		const cs: Candle[] = Array.from({ length: 8 }, (_, i) => ({ t: `2021${String(i + 1).padStart(4, '0')}`, o: 100, h: 100, l: 100, c: 100, v: 1000 }));
		cs[4] = { ...cs[4], l: 80 }; // 역행 -20%
		cs[5] = { ...cs[5], h: 130 }; // 순행 +30%
		const rule: StrategyRule = {
			entry: [{ left: 'price', leftParams: {}, op: '>', right: { kind: 'const', value: 0 } }],
			entryCombine: 'AND',
			exit: [],
			exitCombine: 'OR'
		};
		const res = runBacktestRule(cs, rule, { windowBars: 8, withCosts: false, costsBp: { commissionBp: 0, sellTaxBp: 0, slippageBp: 0 } });
		expect(res).not.toBeNull();
		const tr = res!.trades[0];
		expect(tr).toBeTruthy();
		expect(tr.maePct).toBeCloseTo(-20, 5); // 저가 80 / 진입 100 − 1
		expect(tr.mfePct).toBeCloseTo(30, 5); // 고가 130 / 진입 100 − 1
	});

	it('손절: 인트라바 stopPx 트리거 → exitReason stop · retPct=−손절% (S2)', () => {
		const cs: Candle[] = Array.from({ length: 8 }, (_, i) => ({ t: `2021${String(i + 1).padStart(4, '0')}`, o: 100, h: 100, l: 100, c: 100, v: 1000 }));
		cs[3] = { ...cs[3], l: 85 }; // 봉3 저가 85 → 손절 10%(stopPx 90) 인트라바 트리거
		const rule: StrategyRule = {
			entry: [{ left: 'price', leftParams: {}, op: '>', right: { kind: 'const', value: 0 } }],
			entryCombine: 'AND',
			exit: [],
			exitCombine: 'OR'
		};
		const res = runBacktestRule(cs, rule, { windowBars: 8, withCosts: false, costsBp: { commissionBp: 0, sellTaxBp: 0, slippageBp: 0 }, stop: { lossPct: 10 } });
		expect(res).not.toBeNull();
		const stopTrade = res!.trades.find((t) => t.exitReason === 'stop');
		expect(stopTrade).toBeTruthy();
		expect(stopTrade!.retPct).toBeCloseTo(-10, 5); // stopPx 90 / 진입 100 − 1
	});

	it('runBacktestRule: gate 없으면 fundGate 조건=항상 0(진입 0, 회귀 안전)', () => {
		const cs = mkCandles(40);
		const rule: StrategyRule = {
			entry: [{ left: 'fundGate', leftParams: {}, op: '>=', right: { kind: 'const', value: 6 } }],
			entryCombine: 'AND',
			exit: [],
			exitCombine: 'OR'
		};
		const res = runBacktestRule(cs, rule, { windowBars: 40, withCosts: false, costsBp: { commissionBp: 0, sellTaxBp: 0, slippageBp: 0 } });
		// gate 미주입 → fundGate 항상 null → 진입 0 → 거래 0(엔진 정상 반환)
		expect(res).not.toBeNull();
		expect(res!.trades.length).toBe(0);
	});
});
