import { describe, it, expect } from 'vitest';
import { decodeAcontext, detectUnit, xbrlCellsFromContent } from './xbrlCells';
import { costCells, segmentCells, segName, buildSeries, type PeriodComposition } from './noteSeries';

describe('decodeAcontext · 정부 ACONTEXT 기간/축 토큰 분해', () => {
	it('당기 누적(FQA=1분기 누적)', () => {
		const d = decodeAcontext('CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember');
		expect(d).toEqual({ ctxYear: 2026, ctxFlow: 'd', ctxQuarter: 1, ctxMode: 'A', axisPath: 'ConsolidatedMember' });
	});
	it('연간(FY=4분기 Y)', () => {
		expect(decodeAcontext('CFY2025dFY_ifrs-full_X_ifrs-full_ConsolidatedMember')?.ctxMode).toBe('Y');
		expect(decodeAcontext('CFY2025dFY_ifrs-full_X_ifrs-full_ConsolidatedMember')?.ctxQuarter).toBe(4);
	});
	it('전기(BP)·시점(e)', () => {
		const d = decodeAcontext('BPFY2024eFY_ifrs-full_X_ifrs-full_ConsolidatedMember');
		expect(d?.ctxYear).toBe(2024);
		expect(d?.ctxFlow).toBe('e');
	});
	it('세그먼트 축 멤버 추출(entity 보존, ifrs-full prefix strip)', () => {
		const d = decodeAcontext('CFY2026dFQA_ifrs-full_OperatingSegmentsAxis_ifrs-full_ConsolidatedMember_dart_OperatingSegmentsMember_entity00126380_DsSegmentsMemberOfReportableSegmentsMember');
		expect(d?.axisPath).toContain('entity00126380_DsSegmentsMemberOfReportableSegmentsMember');
		expect(d?.axisPath).toContain('ConsolidatedMember');
	});
	it('비매칭 = null', () => expect(decodeAcontext('garbage')).toBeNull());
});

describe('detectUnit', () => {
	it('백만원', () => expect(detectUnit('(단위 : 백만원)')).toBe(1e6));
	it('천원', () => expect(detectUnit('단위 : 천원')).toBe(1e3));
	it('미발견 기본 백만원', () => expect(detectUnit('<TD>원재료</TD>')).toBe(1e6));
});

// 실측형 비용 표 · TR 별 첫 ACODE-없는 TE=라벨, ACODE+ACONTEXT TE=값
const COST_XML =
	'<TABLE><TBODY>' +
	'<TR><TE>성격별 비용</TE><TE ACODE="ifrs-full_ExpenseByNature" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember">76,640,647</TE></TR>' +
	'<TR><TE>제품과 재공품의 변동</TE><TE ACODE="ifrs-full_ChangesInInventoriesOfFinishedGoods" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember">(2,633,697)</TE></TR>' +
	'<TR><TE>원재료 등의 사용액 및 상품 매입액 등</TE><TE ACODE="ifrs-full_RawMaterialsAndConsumablesUsed" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember">27,555,867</TE></TR>' +
	'<TR><TE>급여</TE><TE ACODE="ifrs-full_EmployeeBenefitsExpense" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember">10,527,843</TE></TR>' +
	'<TR><TE>감가상각비</TE><TE ACODE="ifrs-full_DepreciationExpense" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember">11,480,235</TE></TR>' +
	'</TBODY></TABLE>';

describe('xbrlCellsFromContent + costCells · 비용 acode 직독', () => {
	it('TE 셀 추출(acode·label·value·기간)', () => {
		const cells = xbrlCellsFromContent(COST_XML, 1e6);
		const m = new Map(cells.map((c) => [c.acode, c]));
		expect(m.get('ifrs-full_RawMaterialsAndConsumablesUsed')?.value).toBe(27555867 * 1e6);
		expect(m.get('ifrs-full_RawMaterialsAndConsumablesUsed')?.label).toBe('원재료 등의 사용액 및 상품 매입액 등');
		expect(m.get('ifrs-full_ChangesInInventoriesOfFinishedGoods')?.value).toBe(-2633697 * 1e6); // 괄호 음수
	});
	it('costCells · 총계(ExpenseByNature)·재고변동·음수 제외, acode 그룹', () => {
		const c = costCells(xbrlCellsFromContent(COST_XML, 1e6), 2026);
		expect(c.has('ifrs-full_ExpenseByNature')).toBe(false);
		expect(c.has('ifrs-full_ChangesInInventoriesOfFinishedGoods')).toBe(false);
		expect(c.get('ifrs-full_RawMaterialsAndConsumablesUsed')?.value).toBe(27555867 * 1e6);
		expect(c.size).toBe(3); // 원재료·급여·감가상각
	});
	it('ACONTEXT 없으면(옛 양식) 빈 배열', () => {
		expect(xbrlCellsFromContent('<TABLE><TR><TD>원재료</TD><TD>123</TD></TR></TABLE>', 1e6)).toEqual([]);
	});
});

const SEG_XML =
	'<TABLE><TBODY>' +
	'<TR><TE>매출액</TE>' +
	'<TE ACODE="ifrs-full_Revenue" ACONTEXT="CFY2026dFQA_dart_OperatingSegmentsAxis_entity1_DxSegmentsMemberOfReportableSegmentsMember">52,654,686</TE>' +
	'<TE ACODE="ifrs-full_Revenue" ACONTEXT="CFY2026dFQA_dart_OperatingSegmentsAxis_entity1_DsSegmentsMemberOfReportableSegmentsMember">81,715,643</TE>' +
	'<TE ACODE="ifrs-full_Revenue" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_MaterialReconcilingItemsMember">(11,016,691)</TE>' +
	'<TE ACODE="ifrs-full_Revenue" ACONTEXT="CFY2026dFQA_ifrs-full_GeographicalAreasAxis_entity1_CnMember">21,000,000</TE>' +
	'<TE ACODE="ifrs-full_Revenue" ACONTEXT="CFY2026dFQA_ifrs-full_X_ifrs-full_ConsolidatedMember">133,873,444</TE>' +
	'</TR></TBODY></TABLE>';

describe('segmentCells · 부문 axisPath 직독(지역·조정·집계 배제)', () => {
	it('영업부문만 · 지역(Cn)·조정(Reconciling)·합계(Consolidated) 제외', () => {
		const s = segmentCells(xbrlCellsFromContent(SEG_XML, 1e6), 2026);
		const names = [...s.keys()];
		expect(names).toContain('Dx');
		expect(names).toContain('Ds');
		expect(names).not.toContain('Cn'); // 지역 배제
		expect(s.size).toBe(2);
		expect(s.get('Ds')?.value).toBe(81715643 * 1e6);
	});
});

describe('segName · 택소노미 꼬리 strip', () => {
	it('Samsung Dx', () => expect(segName('ConsolidatedMember|entity1_DxSegmentsMemberOfReportableSegmentsMember')).toBe('Dx'));
	it('passthrough 꼬리 제거', () => expect(segName('PharmaceuticalSectorOfEntitysTotalForSegmentConsolidationItems')).toBe('Pharmaceutical'));
});

describe('buildSeries · 기간별 → 시계열(상위 K + 기타 롤업)', () => {
	const mk = (period: string, items: [string, number][]): PeriodComposition => ({
		period,
		year: period.slice(0, 4),
		quarter: period.slice(5) + '분기',
		items: new Map(items.map(([k, v]) => [k, { name: k, value: v }]))
	});
	it('비용 · topK + 기타, shares 합 100', () => {
		const s = buildSeries([mk('2025Q4', [['원재료', 50], ['급여', 30], ['감가', 20]]), mk('2026Q1', [['원재료', 60], ['급여', 25], ['감가', 15]])], { topK: 6, rollupOther: true });
		expect(s).not.toBeNull();
		expect(s!.points.length).toBe(2);
		const last = s!.points[1]!;
		expect(last.shares.reduce((a, b) => a + b, 0)).toBeCloseTo(100, 1);
		expect(s!.categories).toContain('기타');
	});
	// 회귀 · 서로 다른 acode 가 같은 표시명('급여')이면 categories 중복 → 다이얼로그/패널 keyed {#each (name)} 가
	// each_key_duplicate 로 렌더 throw·마운트 실패(상세보기 안 뜸). 표시명 병합으로 유일·값 합산 보장.
	it('표시명 중복 acode 병합 → categories 유일·값 합산(each_key_duplicate 방지)', () => {
		const items = new Map([
			['ifrs-full_EmployeeBenefitsExpense', { name: '급여', value: 30 }],
			['dart_EmployeeBenefitsExpense', { name: '급여', value: 20 }],
			['ifrs-full_RawMaterialsAndConsumablesUsed', { name: '원재료', value: 50 }]
		]);
		const s = buildSeries([{ period: '2026Q1', year: '2026', quarter: '1분기', items }], { topK: 6, rollupOther: true });
		expect(s).not.toBeNull();
		expect(s!.categories.filter((c) => c === '급여').length).toBe(1); // 중복 0
		const gi = s!.categories.indexOf('급여');
		expect(s!.points[0]!.shares[gi]).toBeCloseTo(50, 1); // 30+20=50 / 100
	});
});
