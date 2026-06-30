// 체결 커널 회귀 · 전문 토론(2026-06-19)이 찾은 3 결함의 결정론 가드.
// 합성 캔들(전 봉 100, 비용 0)로 look-ahead·갭체결·미청산 오염을 못박는다.
import { describe, expect, it } from 'vitest';
import { runBacktestRule } from './engine';
import type { Candle } from './types';
import type { StrategyRule } from './conditions';

// 항상-진입 룰(price>0) · 첫 가능 봉(startIdx+1) 진입 후 보유(exit 없음 → target≡1).
const ALWAYS_ENTER: StrategyRule = {
	entry: [{ left: 'price', leftParams: {}, op: '>', right: { kind: 'const', value: 0 } }],
	entryCombine: 'AND',
	exit: [],
	exitCombine: 'OR'
};
const FLAT = (n: number): Candle[] =>
	Array.from({ length: n }, (_, i) => ({ t: `2021${String(i + 1).padStart(4, '0')}`, o: 100, h: 100, l: 100, c: 100, v: 1000 }));
const OPTS = { windowBars: 8, withCosts: false, costsBp: { commissionBp: 0, sellTaxBp: 0, slippageBp: 0 } };

describe('체결 커널 · look-ahead·갭·미청산 (전문 토론 P0)', () => {
	it('look-ahead 가드: 손절선이 진입 봉에서만 깨지면 손절 미발동(i>entryIdx)', () => {
		// 진입은 봉1 시가 100. 봉1 저가 85(stopPx 90 돌파)지만 = 진입 봉 → 같은 봉 인트라바 순서 미지로 무시.
		// 이후 봉 저가 100(미돌파) → 손절 거래 0, 포지션은 끝까지 보유(미청산).
		const cs = FLAT(8);
		cs[1] = { ...cs[1], l: 85 };
		const res = runBacktestRule(cs, ALWAYS_ENTER, { ...OPTS, stop: { lossPct: 10 } });
		expect(res).not.toBeNull();
		expect(res!.trades.filter((t) => t.exitReason === 'stop').length).toBe(0);
		// 유일 거래 = 미청산 finalMark, 진입 봉(1) 다음부터 보유 → holdDays = 마지막(7) − 진입(1) = 6
		expect(res!.trades.length).toBe(1);
		expect(res!.trades[0].open).toBe(true);
		expect(res!.trades[0].holdDays).toBe(6);
	});

	it('갭 관통: 손절선 아래로 갭하면 stopPx 아닌 그 봉 시가로 체결(낙관 차단)', () => {
		// 봉3 갭다운: 시가 80(stopPx 90 아래). 손절 체결 = min(90, 80) = 80 → retPct −20 (−10 아님).
		const cs = FLAT(8);
		cs[3] = { ...cs[3], o: 80, h: 80, l: 75, c: 80 };
		const res = runBacktestRule(cs, ALWAYS_ENTER, { ...OPTS, stop: { lossPct: 10 } });
		expect(res).not.toBeNull();
		const stopTrade = res!.trades.find((t) => t.exitReason === 'stop');
		expect(stopTrade).toBeTruthy();
		expect(stopTrade!.retPct).toBeCloseTo(-20, 5); // 갭 시가 80 체결 · stopPx 90 이었으면 −10
		expect(stopTrade!.holdDays).toBe(2); // 진입 봉1 → 봉3
	});

	it('미청산 거래는 승률 분모에서 제외(closed 만)', () => {
		// 봉2 익절(+10%, closed 승) → 봉3 재진입 → 끝(봉7 종가 90) 미청산 손실(−10%).
		// 승률 = 청산 1건 중 1승 = 100% (미청산 손실 포함이면 50%로 오염).
		const cs = FLAT(8);
		cs[2] = { ...cs[2], h: 115 }; // 익절 110 인트라바 트리거
		cs[7] = { ...cs[7], c: 90 }; // 종료 시 미청산 −10%
		const res = runBacktestRule(cs, ALWAYS_ENTER, { ...OPTS, stop: { gainPct: 10 } });
		expect(res).not.toBeNull();
		const closed = res!.trades.filter((t) => !t.open);
		const open = res!.trades.filter((t) => t.open);
		expect(closed.length).toBe(1); // 익절 1
		expect(open.length).toBe(1); // 미청산 손실 1
		expect(res!.metrics.winRatePct).toBe(100); // 청산 1/1 · 미청산 손실 제외(포함이면 50)
		expect(res!.metrics.tradeCount).toBe(2); // 거래표엔 미청산 행 유지
	});
});
