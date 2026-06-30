import { describe, expect, it } from 'vitest';
import { runUniverse } from './engine';
import type { UniverseRow, UniverseSpec, DelistReason } from './types';

// 합성 패널 빌더 · ym 리스트 × 종목, 명시 momMonthly·retFwd1m·delistReason.
function row(
	ym: string,
	code: string,
	mom: number | null,
	retFwd1m: number | null,
	delistReason: DelistReason = 'none'
): UniverseRow {
	return {
		ym,
		stockCode: code,
		close: 1000,
		mktcap: 1e9,
		turnover: 1e8,
		momMonthly: mom,
		volMonthly6m: 0.2,
		high52wProx: 0.9,
		retFwd1m: retFwd1m,
		retFwd3m: retFwd1m,
		delistReason
	};
}

const YMS = ['202001', '202002', '202003', '202004', '202005'];
const SPEC: UniverseSpec = {
	rebalance: 'M',
	rankSignal: 'mom12_1',
	buckets: 2,
	liquidityPctile: 0,
	windowFrom: '202001',
	windowTo: '202005'
};

describe('runUniverse · holdings 회계 + U-G1 이중밴드', () => {
	it('NAV 시작 100 · decisionYm<fillYm · 상위 모멘텀=분위1', () => {
		// A=고모멘텀(분위1), B=저모멘텀(분위2). 둘 다 매월 +10% forward.
		const rows: UniverseRow[] = [];
		for (const ym of YMS) {
			rows.push(row(ym, 'A', 0.5, 0.1));
			rows.push(row(ym, 'B', -0.5, 0.1));
		}
		const res = runUniverse(rows, SPEC);
		expect(res.status).toBe('ok');
		expect(res.optimistic.navByBucket[1][0]).toBe(100); // 시작 100
		expect(res.optimistic.navByBucket[2][0]).toBe(100);
		// 4 리밸 기간(202001~04) × +10% → 100·1.1^4 ≈ 146.41
		expect(res.optimistic.navByBucket[1].at(-1)!).toBeCloseTo(146.41, 1);
		// decisionYm < fillYm 불변
		for (const r of res.rebalances) expect(r.decisionYm < r.fillYm).toBe(true);
		// A 가 분위1(상위) 멤버
		expect(res.rebalances[0].byBucket[0].codes).toContain('A');
		expect(res.rebalances[0].byBucket[1].codes).toContain('B');
	});

	it('unknown 폐지 = 밴드(보수<낙관) · 합병 폐지 = last-close(밴드 0)', () => {
		// 분위1에 정상주 N + 폐지주 1. 202003 에서 폐지(retFwd1m null at 202003).
		const mk = (reason: DelistReason): UniverseRow[] => {
			const rows: UniverseRow[] = [];
			for (const ym of YMS) {
				// 고모멘텀 정상주 2개(분위1), 저모멘텀 1개(분위2)
				rows.push(row(ym, 'N1', 0.6, 0.1));
				rows.push(row(ym, 'N2', 0.5, 0.1));
				rows.push(row(ym, 'LOW', -0.9, 0.05));
				// 폐지주 X: 202003 까지 존재, 그 달 forward null(=exit)
				if (ym <= '202003') {
					const fwd = ym === '202003' ? null : 0.1;
					rows.push(row(ym, 'X', 0.55, fwd, reason));
				}
			}
			return rows;
		};
		const unk = runUniverse(mk('unknown'), SPEC);
		const mer = runUniverse(mk('merger'), SPEC);

		// unknown: 보수(−100%) 종착 < 낙관(0손실) 종착 → 밴드 폭>0
		const optEnd = unk.optimistic.navByBucket[1].at(-1)!;
		const consEnd = unk.conservative.navByBucket[1].at(-1)!;
		expect(consEnd).toBeLessThan(optEnd);
		expect(unk.unknownDependence).toBeGreaterThan(0);
		expect(unk.nUnknownExits).toBe(1);

		// merger: 양 모드 동일(last-close=0) → 밴드 0
		expect(mer.conservative.navByBucket[1].at(-1)!).toBeCloseTo(mer.optimistic.navByBucket[1].at(-1)!, 6);
		expect(mer.unknownDependence).toBeCloseTo(0, 6);
		expect(mer.nMergerExits).toBe(1);
	});

	it('표본 부족(리밸<4) = invalid', () => {
		const rows = [row('202001', 'A', 0.5, 0.1), row('202002', 'A', 0.5, 0.1)];
		const res = runUniverse(rows, { ...SPEC, windowTo: '202002' });
		expect(res.status).toBe('invalid');
	});
});
