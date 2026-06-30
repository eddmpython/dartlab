// 정기보고서 자기이력 helper 골든 · 데모 게이트(03 §7): 다년 커버리지 / 무배당 소형주 / 첫배당 / 단일기간 엣지.
// self-vs-self 사실만, prior non-null 가드, window 넘는 연속 주장 금지를 회귀로 박는다.
import { describe, it, expect } from 'vitest';
import type { ShareholderReturnYear, WorkforceYear } from '@dartlab/ui-contracts';
import { returnTrend, workforceTrend } from './reportSelfHistory';

const wfY = (year: string, total: number | null, regular: number | null, contract: number | null): WorkforceYear => ({
	year, total, male: null, female: null, regular, contract, avgSalary: null, totalSalary: null, tenure: null
});
const srY = (year: string, dps: number | null, payoutPct: number | null, buybackCancel: number | null = null): ShareholderReturnYear => ({
	year, dps, eps: null, totalDividend: null, payoutPct, yieldPct: null, buybackQty: null, disposalQty: null, buybackCancel, treasuryEnd: null
});

describe('workforceTrend · 총원 궤적 + 계약직 비중 이동', () => {
	it('다년 커버리지 · 총원 +20%·계약직 비중 이동', () => {
		const t = workforceTrend([wfY('2021', 1000, 800, 200), wfY('2022', 1100, 850, 250), wfY('2023', 1200, 900, 300)]);
		expect(t).not.toBeNull();
		expect(t!.fromYear).toBe('2021');
		expect(t!.toYear).toBe('2023');
		expect(t!.headPct).toBeCloseTo(20, 5);
		expect(t!.contractFromPct).toBeCloseTo(20, 5); // 200/1000
		expect(t!.contractToPct).toBeCloseTo(25, 5); // 300/1200
	});
	it('단일 기간 · 궤적 미정의(null)', () => {
		expect(workforceTrend([wfY('2023', 1200, 900, 300)])).toBeNull();
	});
	it('total 결측 다수 · 유효 ≥2 아니면 null', () => {
		expect(workforceTrend([wfY('2022', null, 850, 250), wfY('2023', 1200, 900, 300)])).toBeNull();
	});
	it('계약직 결측 · headPct 만, 계약직 토큰 null', () => {
		const t = workforceTrend([wfY('2021', 1000, null, null), wfY('2023', 1100, null, null)]);
		expect(t!.headPct).toBeCloseTo(10, 5);
		expect(t!.contractFromPct).toBeNull();
		expect(t!.contractToPct).toBeNull();
	});
});

describe('returnTrend · 연속배당·배당성향·소각', () => {
	it('다년 연속배당 + 배당성향 span', () => {
		const t = returnTrend([srY('2021', 500, 22), srY('2022', 550, 25), srY('2023', 600, 28)]);
		expect(t!.streak).toBe(3);
		expect(t!.streakToYear).toBe('2023');
		expect(t!.payoutFromPct).toBe(22);
		expect(t!.payoutToPct).toBe(28);
		expect(t!.payoutFromYear).toBe('2021');
		expect(t!.payoutToYear).toBe('2023');
		expect(t!.cancelQty).toBeNull();
	});
	it('무배당 소형주 · dps 전부 0/null → streak 0·payout 없음 → null', () => {
		expect(returnTrend([srY('2022', null, null), srY('2023', 0, null)])).toBeNull();
	});
	it('중간 배당 중단 · trailing 연속만 계수(gap 이전 무시)', () => {
		const t = returnTrend([srY('2020', 500, 20), srY('2021', null, null), srY('2022', 300, 18), srY('2023', 350, 19)]);
		expect(t!.streak).toBe(2); // 2022·2023 만 (2021 gap)
		expect(t!.streakToYear).toBe('2023');
	});
	it('첫배당 · 최신해만 dps>0 → streak 1(<2 라 문장 미발현, payout span 없으면 null)', () => {
		expect(returnTrend([srY('2022', null, null), srY('2023', 400, 15)])).toBeNull(); // streak 1·payout 단일 → 토큰 없음
	});
	it('당해 미발표 꼬리 null · 가장 최근 배당연도부터 계수(실측 005010: 2021-2024 배당·2025 null)', () => {
		const t = returnTrend([srY('2021', 800, 30), srY('2022', 350, 28), srY('2023', 250, 25), srY('2024', 150, 22), srY('2025', null, null)]);
		expect(t!.streak).toBe(4); // 2025 미발표는 건너뛰고 2021-2024 연속
		expect(t!.streakToYear).toBe('2024');
	});
	it('소각 appears-when-clean · 최신해 buybackCancel>0 일 때만', () => {
		const t = returnTrend([srY('2022', 500, 20), srY('2023', 550, 22, 1_200_000)]);
		expect(t!.cancelQty).toBe(1_200_000);
		expect(t!.cancelYear).toBe('2023');
	});
	it('빈 배열 · null', () => {
		expect(returnTrend([])).toBeNull();
	});
});
