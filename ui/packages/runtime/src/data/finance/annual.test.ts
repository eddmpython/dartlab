import { describe, it, expect } from 'vitest';
import { buildAnnualFromRows } from './annual';
import type { RawRow } from './accounts';

// 합성 픽스처 · GS건설형(연결 매출 124,503억). 네트워크 없는 헤르메틱 단위테스트.
// 검증: ① CFS 우선(OFS 무시) ② 부분분기(2026 q1) 제외 ③ id·kw 매칭 ④ 파생(매출총이익·비유동)
// ⑤ 회계항등식(자산=부채+자본·매총=매출−원가).
function row(p: Partial<RawRow>): RawRow {
	return { account_detail: '-', ord: 1, ...p } as RawRow;
}
const won = (eok: number) => String(eok * 1e8); // 억원 → 원 문자열

function fixture(): RawRow[] {
	const rows: RawRow[] = [];
	const add = (fs: string, year: number, reprt: string, sj: string, id: string, nm: string, eok: number) =>
		rows.push(row({ fs_div: fs, bsns_year: year, reprt_code: reprt, sj_div: sj, account_id: id, account_nm: nm, thstrm_amount: won(eok) }));

	// 2025 연결(CFS) 연간(11011)
	add('CFS', 2025, '11011', 'IS', 'ifrs-full_Revenue', '매출액', 124503);
	add('CFS', 2025, '11011', 'IS', 'ifrs-full_CostOfSales', '매출원가', 111053);
	// grossProfit 행 없음 → 파생(124503-111053=13450)
	add('CFS', 2025, '11011', 'IS', 'dart_OperatingIncomeLoss', '영업이익', 4378);
	add('CFS', 2025, '11011', 'IS', 'ifrs-full_ProfitLoss', '당기순이익', 934);
	add('CFS', 2025, '11011', 'BS', 'ifrs-full_Assets', '자산총계', 184598);
	add('CFS', 2025, '11011', 'BS', 'ifrs-full_CurrentAssets', '유동자산', 90742);
	add('CFS', 2025, '11011', 'BS', 'ifrs-full_Liabilities', '부채총계', 129363);
	add('CFS', 2025, '11011', 'BS', 'ifrs-full_CurrentLiabilities', '유동부채', 78321);
	add('CFS', 2025, '11011', 'BS', 'ifrs-full_Equity', '자본총계', 55235); // 129363+55235=184598
	add('CFS', 2025, '11011', 'CF', 'ifrs-full_CashFlowsFromUsedInOperatingActivities', '영업활동현금흐름', 5915);
	add('CFS', 2025, '11011', 'CF', 'ifrs-full_CashFlowsFromUsedInInvestingActivities', '투자활동현금흐름', -2470);
	add('CFS', 2025, '11011', 'CF', 'ifrs-full_CashFlowsFromUsedInFinancingActivities', '재무활동현금흐름', 5737);

	// 2024 연결 · costOfSales 는 id 비우고 nm 키워드 fallback 경로 검증
	add('CFS', 2024, '11011', 'IS', 'ifrs-full_Revenue', '매출액', 128638);
	add('CFS', 2024, '11011', 'IS', '', '매출원가', 117496);
	add('CFS', 2024, '11011', 'IS', 'dart_OperatingIncomeLoss', '영업이익', 2860);
	add('CFS', 2024, '11011', 'IS', 'ifrs-full_ProfitLoss', '당기순이익', 2639);
	add('CFS', 2024, '11011', 'BS', 'ifrs-full_Assets', '자산총계', 178033);
	add('CFS', 2024, '11011', 'BS', 'ifrs-full_Equity', '자본총계', 50871);

	// OFS(별도) 2025 · CFS 우선 검증용 다른 매출(무시돼야 함)
	add('OFS', 2025, '11011', 'IS', 'ifrs-full_Revenue', '매출액', 50000);

	// 2026 q1(11013) 부분분기 · 표/연도에서 제외돼야 함
	add('CFS', 2026, '11013', 'IS', 'ifrs-full_Revenue', '매출액', 24005);
	return rows;
}

describe('buildAnnualFromRows', () => {
	const r = buildAnnualFromRows('006360', fixture(), 5);

	it('연결(CFS) scope 채택', () => {
		expect(r).not.toBeNull();
		expect(r!.scope).toBe('CFS');
	});

	it('연간만·최신우선, 부분분기(2026) 제외', () => {
		expect(r!.years).toEqual(['2025', '2024']);
	});

	it('IS · CFS 매출 채택(OFS 50000 무시)·id/kw 매칭', () => {
		const get = (k: string) => r!.is.find((x) => x.key === k)!.values;
		expect(get('revenue')).toEqual([124503, 128638]);
		expect(get('costOfSales')).toEqual([111053, 117496]); // 2024 는 kw fallback
		expect(get('operatingIncome')).toEqual([4378, 2860]);
		expect(get('netIncome')).toEqual([934, 2639]);
	});

	it('매출총이익 파생 = 매출 − 원가', () => {
		const gp = r!.is.find((x) => x.key === 'grossProfit')!.values;
		expect(gp).toEqual([124503 - 111053, 128638 - 117496]);
	});

	it('BS 항등식 · 자산 = 부채 + 자본 · 비유동 파생', () => {
		const assets = r!.bs.find((x) => x.key === 'assets')!.values[0]!;
		const liab = r!.bs.find((x) => x.key === 'liabilities')!.values[0]!;
		const eq = r!.bs.find((x) => x.key === 'equity')!.values[0]!;
		expect(assets).toBe(184598);
		expect(liab + eq).toBe(assets);
		const nonCurAssets = r!.bs.find((x) => x.key === 'nonCurrentAssets')!.values[0]!;
		expect(nonCurAssets).toBe(184598 - 90742);
	});

	it('차트 프리셋 · IS 최신우선', () => {
		expect(r!.charts.is[0]).toEqual({ year: '2025', 매출액: 124503, 영업이익: 4378, 당기순이익: 934 });
		expect(r!.charts.bs[0]).toEqual({ year: '2025', 부채: 129363, 자본: 55235 });
		expect(r!.charts.cf[0]).toEqual({ year: '2025', 영업CF: 5915, 투자CF: -2470, 재무CF: 5737 });
	});

	it('데이터 없으면 null', () => {
		expect(buildAnnualFromRows('000000', [])).toBeNull();
	});
});
