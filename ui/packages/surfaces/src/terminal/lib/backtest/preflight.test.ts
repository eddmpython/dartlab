// 대기 프리플라이트 계산 회귀 · B&H 기준선·MDD·거래가능봉·왕복비용을 결정론 합성 캔들로 못박는다.
import { describe, expect, it } from 'vitest';
import { backtestPreflight } from './preflight';
import type { Candle } from './types';

// closes 로 캔들 생성(o=h=l=c). v 기본 1000.
const mk = (closes: number[], halts: number[] = []): Candle[] =>
	closes.map((c, i) => ({ t: `2021${String(i + 1).padStart(4, '0')}`, o: c, h: c, l: c, c, v: halts.includes(i) ? 0 : 1000 }));

describe('backtestPreflight · 실행 전 진실(B&H·데이터품질·비용)', () => {
	it('B&H 수익·MDD = 보유 실현치(종가만)', () => {
		// 100 → 120(피크) → 90(저점) → 108(끝): B&H +8%, MDD −25%(120→90).
		const pf = backtestPreflight(mk([100, 120, 90, 108]), 4, { commissionBp: 1.5, sellTaxBp: 15, slippageBp: 10 });
		expect(pf).not.toBeNull();
		expect(pf!.bhRetPct).toBeCloseTo(8, 5);
		expect(pf!.bhMddPct).toBeCloseTo(-25, 5);
		expect(pf!.bars).toBe(4);
		expect(pf!.fromT).toBe('20210001');
		expect(pf!.toT).toBe('20210004');
		expect(pf!.windowShort).toBe(true); // 4 < 60
		expect(pf!.annVolPct).toBeNull(); // 표본<20 → null(거짓 변동성 차단)
		expect(pf!.bhSharpe).toBeNull(); // 표본<60 → null(소표본 Sharpe 거짓말 차단)
	});

	it('거래가능 봉 = v>0 && o>0, 정지봉 분리', () => {
		// 봉2 거래정지(v=0) → 거래가능 3, 정지 1.
		const pf = backtestPreflight(mk([100, 110, 90, 108], [2]), 4, { commissionBp: 1.5, sellTaxBp: 15, slippageBp: 10 });
		expect(pf).not.toBeNull();
		expect(pf!.tradeableBars).toBe(3);
		expect(pf!.haltBars).toBe(1);
		expect(pf!.splitSuspect).toBeNull();
	});

	it('왕복 비용 % = 수수료×2 + 거래세 + 슬리피지×2 (bp→%)', () => {
		const pf = backtestPreflight(mk([100, 101, 102]), 3, { commissionBp: 1.5, sellTaxBp: 15, slippageBp: 10 });
		expect(pf).not.toBeNull();
		expect(pf!.roundTripPct).toBeCloseTo(0.38, 5); // (3 + 15 + 20)/100
	});

	it('창이 candles 보다 길면 전체로 클램프 · 봉<2 면 null', () => {
		expect(backtestPreflight(mk([100, 110]), 999, { commissionBp: 0, sellTaxBp: 0, slippageBp: 0 })!.bars).toBe(2);
		expect(backtestPreflight(mk([100]), 4, { commissionBp: 0, sellTaxBp: 0, slippageBp: 0 })).toBeNull();
	});
});
