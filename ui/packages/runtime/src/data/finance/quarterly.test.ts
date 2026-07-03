import { describe, it, expect } from 'vitest';
import { buildQuarterlyFromRows } from './annual';
import type { RawRow } from './accounts';

// 합성 픽스처 · 분기 뷰(단일분기 환산) 헤르메틱 단위테스트. 네트워크 없음.
// 검증: ① CFS 우선 ② 기간 오래된→최신 ③ flow YTD 누적 자동판정→차분 ④ BS 시점 스냅샷 ⑤ 차트 프리셋.
function row(p: Partial<RawRow>): RawRow {
	return { account_detail: '-', ord: 1, ...p } as RawRow;
}
const won = (eok: number) => String(eok * 1e8); // 억원 → 원 문자열

// 2024 연결 4분기 · IS/CF 는 YTD 누적(Q1..Q3 합 > 연간), BS 는 분기말 시점.
function fixture(): RawRow[] {
	const rows: RawRow[] = [];
	const add = (year: number, reprt: string, sj: string, id: string, nm: string, eok: number, fs = 'CFS') =>
		rows.push(row({ fs_div: fs, bsns_year: year, reprt_code: reprt, sj_div: sj, account_id: id, account_nm: nm, thstrm_amount: won(eok) }));

	// revenue YTD: Q1=100, H1=250, 9M=420, FY=600 → 단일분기 [100,150,170,180]
	const rev: [string, number][] = [
		['11013', 100],
		['11012', 250],
		['11014', 420],
		['11011', 600]
	];
	for (const [reprt, v] of rev) add(2024, reprt, 'IS', 'ifrs-full_Revenue', '매출액', v);

	// operatingIncome YTD: Q1=10, H1=25, 9M=42, FY=60 → [10,15,17,18]
	const op: [string, number][] = [
		['11013', 10],
		['11012', 25],
		['11014', 42],
		['11011', 60]
	];
	for (const [reprt, v] of op) add(2024, reprt, 'IS', 'dart_OperatingIncomeLoss', '영업이익', v);

	// netIncome YTD: Q1=5, H1=12, 9M=20, FY=30 → [5,7,8,10]
	const ni: [string, number][] = [
		['11013', 5],
		['11012', 12],
		['11014', 20],
		['11011', 30]
	];
	for (const [reprt, v] of ni) add(2024, reprt, 'IS', 'ifrs-full_ProfitLoss', '당기순이익', v);

	// BS assets · 분기말 시점(누적 아님) → 그대로 [1000,1100,1150,1200]
	const assets: [string, number][] = [
		['11013', 1000],
		['11012', 1100],
		['11014', 1150],
		['11011', 1200]
	];
	for (const [reprt, v] of assets) add(2024, reprt, 'BS', 'ifrs-full_Assets', '자산총계', v);
	// 부채·자본 시점(최신 분기만 있어도 됨) · 자산=부채+자본
	add(2024, '11011', 'BS', 'ifrs-full_Liabilities', '부채총계', 700);
	add(2024, '11011', 'BS', 'ifrs-full_Equity', '자본총계', 500);

	// CF operating YTD: Q1=8, H1=20, 9M=33, FY=48 → [8,12,13,15]
	const cfo: [string, number][] = [
		['11013', 8],
		['11012', 20],
		['11014', 33],
		['11011', 48]
	];
	for (const [reprt, v] of cfo) add(2024, reprt, 'CF', 'ifrs-full_CashFlowsFromUsedInOperatingActivities', '영업활동현금흐름', v);

	return rows;
}

describe('buildQuarterlyFromRows', () => {
	const r = buildQuarterlyFromRows('006360', fixture(), 8);

	it('연결(CFS) scope 채택', () => {
		expect(r).not.toBeNull();
		expect(r!.scope).toBe('CFS');
	});

	it('기간 오래된→최신 · 최신 분기 asOf', () => {
		expect(r!.periods).toEqual(['24Q1', '24Q2', '24Q3', '24Q4']);
		expect(r!.asOf).toBe('24Q4');
	});

	it('flow(IS) YTD 누적 → 단일분기 차분', () => {
		const get = (k: string) => r!.is.find((x) => x.key === k)!.values;
		expect(get('revenue')).toEqual([100, 150, 170, 180]);
		expect(get('operatingIncome')).toEqual([10, 15, 17, 18]);
		expect(get('netIncome')).toEqual([5, 7, 8, 10]);
	});

	it('BS 시점 스냅샷 · 누적 차분 안 함', () => {
		expect(r!.bs.find((x) => x.key === 'assets')!.values).toEqual([1000, 1100, 1150, 1200]);
	});

	it('CF 단일분기 차분', () => {
		expect(r!.cf.find((x) => x.key === 'cfOperating')!.values).toEqual([8, 12, 13, 15]);
	});

	it('차트 프리셋 · 최신 분기 마지막', () => {
		expect(r!.charts.is[r!.charts.is.length - 1]).toEqual({ year: '24Q4', 매출액: 180, 영업이익: 18, 당기순이익: 10 });
	});

	it('데이터 없으면 null', () => {
		expect(buildQuarterlyFromRows('000000', [])).toBeNull();
	});
});
