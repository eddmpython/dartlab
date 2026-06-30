import { describe, expect, it } from 'vitest';
import { niceTicks, yearTicks, nearestIdx, monthlyReturns } from './chartFrame';

describe('niceTicks · 1/2/5 배수 y 그리드', () => {
	it('수익률 범위를 보기좋은 눈금으로 스냅', () => {
		const t = niceTicks(85, 130, 5);
		expect(t.length).toBeGreaterThanOrEqual(3);
		// 모든 눈금은 [lo,hi] 안 + step 일정
		expect(t[0]).toBeGreaterThanOrEqual(85);
		expect(t[t.length - 1]).toBeLessThanOrEqual(130);
		const step = +(t[1] - t[0]).toFixed(6);
		for (let i = 2; i < t.length; i++) expect(+(t[i] - t[i - 1]).toFixed(6)).toBe(step);
	});
	it('역전·빈 범위는 빈 배열(그리드 생략)', () => {
		expect(niceTicks(100, 100)).toEqual([]);
		expect(niceTicks(120, 80)).toEqual([]);
		expect(niceTicks(NaN, 10)).toEqual([]);
	});
	it('100 기준선이 범위 안이면 눈금에 포함될 수 있음', () => {
		const t = niceTicks(90, 140, 5);
		expect(t).toContain(100);
	});
});

describe('yearTicks · 연 경계 x 그리드', () => {
	it('YYYY 바뀌는 인덱스만 추출', () => {
		const ts = ['20200102', '20200601', '20210104', '20210701', '20220103'];
		const yt = yearTicks(ts);
		expect(yt.map((y) => y.label)).toEqual(['2020', '2021', '2022']);
		expect(yt.map((y) => y.idx)).toEqual([0, 2, 4]);
	});
	it('라벨이 max 초과면 균등 솎음', () => {
		const ts: string[] = [];
		for (let y = 2000; y < 2020; y++) ts.push(`${y}0101`, `${y}0601`);
		const yt = yearTicks(ts, 8);
		expect(yt.length).toBeLessThanOrEqual(8);
	});
});

describe('nearestIdx · 크로스헤어 역산', () => {
	it('플롯 양끝/중앙 매핑 + 범위 clamp', () => {
		// padL=40, plotW=200, n=11 → 인덱스 0..10
		expect(nearestIdx(40, 40, 200, 11)).toBe(0);
		expect(nearestIdx(240, 40, 200, 11)).toBe(10);
		expect(nearestIdx(140, 40, 200, 11)).toBe(5);
		expect(nearestIdx(-100, 40, 200, 11)).toBe(0); // 왼쪽 밖 clamp
		expect(nearestIdx(9999, 40, 200, 11)).toBe(10); // 오른쪽 밖 clamp
	});
});

describe('monthlyReturns · 월말 equity 비율 행렬', () => {
	it('월말 수익률·연간 누적·결측 null', () => {
		// 2개월: 1월 100→110(+10%), 2월 110→121(+10%) → YTD ≈ +21%
		const eq = [100, 105, 110, 115, 121];
		const ts = ['20210104', '20210115', '20210129', '20210215', '20210226'];
		const mr = monthlyReturns(eq, ts);
		expect(mr.years).toEqual([2021]);
		expect(mr.cell(2021, 1)).toBeCloseTo(10, 5); // 1월말 110 / 시작 100
		expect(mr.cell(2021, 2)).toBeCloseTo(10, 5); // 2월말 121 / 1월말 110
		expect(mr.ytd(2021)).toBeCloseTo(21, 5);
		expect(mr.cell(2021, 3)).toBeNull(); // 결측 월
	});
	it('빈/단일 데이터는 빈 행렬', () => {
		expect(monthlyReturns([100], ['20210101']).years).toEqual([]);
		expect(monthlyReturns([], []).years).toEqual([]);
	});
});
